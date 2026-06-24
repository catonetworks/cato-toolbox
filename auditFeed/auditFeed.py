# auditFeed.py
#
# This script takes as input an API key, account ID, and time frame, and returns
# audit records in JSON format from the auditFeed API for that account. Optional
# parameters include a marker value to initialise with and the path to a file in
# which to store the marker between runs. Audit records can also be filtered by
# audit field values.
#
# The auditFeed marker is scoped to a specific timeFrame, so the config file
# stores the marker together with its timeFrame. When the requested time window
# changes, the stored marker is reset automatically to avoid reusing a marker
# across different time frames.
#
# The auditFeed API query returns records with fieldsMap and flatFields. This
# script normalizes records into a JSON key:value collection, adds audit and
# event timestamps from the record time, and keeps output behavior similar to
# eventsFeed.py.
#
# The script provides the -n option for sending audit records to a TCP socket,
# and the -z option for sending audit records directly into Microsoft Sentinel.
#
# Usage: auditFeed.py [options]
#
# Options:
#   -h, --help          show this help message and exit
#   -K API_KEY          API key
#   -I ID               Account ID
#   -T TIME_FRAME       Cato TimeFrame, for example last.P1D
#   -P                  Prettify output
#   -p                  Print audit records
#   -n STREAM_EVENTS    Send audit records over network to host:port TCP
#   -z SENTINEL         Send audit records to Sentinel customerid:sharedkey
#   -m MARKER           Initial marker value (default is "", which means start
#                       of the query window)
#   -c CONFIG_FILE      Config file location (default ./config.txt)
#   -F FILTERS          Comma-separated field=value audit filters
#   -f fetch_limit      Stop execution if a fetch returns less than this number
#                       of audit records (default=1)
#   -r RUNTIME_LIMIT    Stop execution if total runtime exceeds this many
#                       seconds (default=infinite)
#   -v                  Print debug info
#   -V                  Print detailed debug info
#
# Examples:
#
# To run the script with key=YOURAPIKEY for account ID 1714 for the previous day,
# pulling all audit records and storing the marker in the default location
# (./config.txt) without displaying records:
#   python3 auditFeed.py -K YOURAPIKEY -I 1714 -T last.P1D -m ""
#
# Running the script from the start with debug enabled so you can see the fetch logic:
#   python3 auditFeed.py -K YOURAPIKEY -I 1714 -T last.P1D -m "" -v
#
# To show audit records, use the -p parameter:
#   python3 auditFeed.py -K YOURAPIKEY -I 1714 -T last.P1D -p
#
# For more human readable audit records, use -pP:
#   python3 auditFeed.py -K YOURAPIKEY -I 1714 -T last.P1D -pP
#
# To print human readable audit records to screen and send raw records to TCP port
# 8000 on 192.168.1.1:
#   python3 auditFeed.py -K YOURAPIKEY -I 1714 -T last.P1D -pP -n 192.168.1.1:8000
#
# To only see audit records where change_type is CREATED:
#   python3 auditFeed.py -K YOURAPIKEY -I 1714 -T last.P1D -p -F change_type=CREATED
#
# This script is supplied as a demonstration of how to access the Cato API with
# Python. It is not an official Cato release and is provided with no guarantees
# of support. Error handling is restricted to the bare minimum required for the
# script to work with the API, and may not be sufficient for production
# environments.
#

import argparse
import base64
import datetime
import gzip
import hmac
import hashlib
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.request


# Maximum number of recently-seen record hashes to remember between runs.
# Only records near the time-window boundary can realistically reappear, so a
# few thousand is plenty while keeping the state file small.
MAX_SEEN_HASHES = 5000


########################################################################################
########################################################################################
########################################################################################
# Helper functions and globals

GRAPHQL_QUERY = """
query auditFeed(
  $accountIDs: [ID!]
  $timeFrame: TimeFrame!
  $filters: [AuditFieldFilterInput!]
  $marker: String
) {
  auditFeed(
    accountIDs: $accountIDs
    timeFrame: $timeFrame
    filters: $filters
    marker: $marker
  ) {
    from
    to
    marker
    fetchedCount
    hasMore
    accounts {
      id
      records {
        time
        fieldsMap
        flatFields
      }
    }
  }
}
""".strip()


# log debug output
def log(text):
    if args.verbose or args.veryverbose:
        print(f"LOG {datetime.datetime.now(datetime.UTC)}> {text}")


# log detailed debug output
def logd(text):
    if args.veryverbose:
        log(text)


# send GQL query string and variables to API, return JSON
# if we hit a network error, retry ten times with a 2 second sleep
def send(query, variables):
    global api_call_count
    global total_bytes_compressed
    global total_bytes_uncompressed
    retry_count = 0
    data = {
        'query': query,
        'variables': variables,
        'operationName': 'auditFeed'
    }
    headers = {
        'x-api-key': args.api_key,
        'Content-Type': 'application/json',
        'Accept-Encoding': 'gzip, deflate, br',
        'User-Agent': 'auditFeed.py'
    }
    while True:
        if retry_count > 10:
            print("FATAL ERROR retry count exceeded")
            sys.exit(1)
        try:
            request = urllib.request.Request(
                url='https://api.catonetworks.com/api/v1/graphql2',
                data=json.dumps(data).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            response = urllib.request.urlopen(request, timeout=30)
            api_call_count += 1
        except urllib.error.HTTPError as e:
            # honor Retry-After for rate limiting (HTTP 429), otherwise use
            # exponential backoff capped at 30 seconds
            retry_after = e.headers.get("Retry-After") if e.headers else None
            try:
                delay = float(retry_after) if retry_after is not None else min(2 ** retry_count, 30)
            except ValueError:
                delay = min(2 ** retry_count, 30)
            log(f"HTTP ERROR {e.code} (attempt {retry_count}), sleeping {delay} seconds then retrying")
            time.sleep(delay)
            retry_count += 1
            continue
        except Exception as e:
            delay = min(2 ** retry_count, 30)
            log(f"ERROR {retry_count}: {e}, sleeping {delay} seconds then retrying")
            time.sleep(delay)
            retry_count += 1
            continue

        response_data = response.read()
        total_bytes_compressed += len(response_data)
        if response.headers.get("Content-Encoding", "").lower() == "gzip" or response_data[:2] == b"\x1f\x8b":
            result_data = gzip.decompress(response_data)
        else:
            result_data = response_data
        total_bytes_uncompressed += len(result_data)
        if result_data[:48] == b'{"errors":[{"message":"rate limit for operation:':
            # in-body rate limit (HTTP 200 with an error payload): count it
            # against the retry budget so the retry_count guard can fire instead
            # of spinning forever if the server keeps returning this error
            log(f"RATE LIMIT (attempt {retry_count}) sleeping 5 seconds then retrying")
            time.sleep(5)
            retry_count += 1
            continue
        break
    result = json.loads(result_data.decode('utf-8', 'replace'))
    if "errors" in result:
        log(f"API error: {result_data}")
        return False, result
    return True, result


def build_variables(marker, audit_filters):
    variables = {
        "accountIDs": [args.ID],
        "timeFrame": args.time_frame,
        "marker": marker
    }
    if audit_filters:
        variables["filters"] = audit_filters
    return variables


def parse_filters(filters):
    filter_values = {}
    for filter_text in filters.split(','):
        if "=" not in filter_text:
            print("Error: -F values must be comma-separated field=value pairs")
            parser.print_help()
            sys.exit(1)
        field_name, value = filter_text.split("=", 1)
        field_name = field_name.strip()
        value = value.strip()
        if not field_name or not value:
            print("Error: -F values must include a non-empty field and value")
            parser.print_help()
            sys.exit(1)
        filter_values.setdefault(field_name, []).append(value)

    audit_filters = []
    for field_name, values in filter_values.items():
        audit_filters.append({
            "fieldNameInput": {
                "AuditFieldName": field_name
            },
            "operator": "is",
            "values": values
        })
    return audit_filters


def flat_fields_to_dict(flat_fields):
    flat_fields_dict = {}
    if isinstance(flat_fields, dict):
        return flat_fields
    if not isinstance(flat_fields, list):
        return flat_fields_dict

    for field in flat_fields:
        if isinstance(field, (list, tuple)) and len(field) >= 2:
            flat_fields_dict[str(field[0])] = field[1]
        elif isinstance(field, dict):
            field_name = field.get("name") or field.get("fieldName") or field.get("key")
            field_value = field.get("value")
            if field_name is not None:
                flat_fields_dict[str(field_name)] = field_value
    return flat_fields_dict


def normalize_audit_record(record, account_id):
    audit_data = {}
    fields_map = record.get("fieldsMap")
    flat_fields = record.get("flatFields")

    if isinstance(fields_map, dict):
        audit_data.update(fields_map)
    else:
        audit_data.update(flat_fields_to_dict(flat_fields))

    audit_time = record.get("time")
    if audit_time:
        audit_data["audit_timestamp"] = audit_time
        audit_data["event_timestamp"] = audit_time

    if account_id and "account_id" not in audit_data:
        audit_data["account_id"] = account_id

    return dict(sorted(
        audit_data.items(),
        key=lambda i: i[0] in {'audit_timestamp', 'event_timestamp'},
        reverse=True
    ))


def record_identity(audit_record):
    """Stable content hash of a normalized audit record, used for dedup."""
    serialized = json.dumps(audit_record, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


########################################################################################
########################################################################################
########################################################################################
# Azure Sentinel functions
# Taken from Microsoft sample here:
# https://docs.microsoft.com/en-gb/azure/azure-monitor/logs/data-collector-api
#
# Main change is to replace requests with urllib

# Build the API signature
def build_signature(customer_id, shared_key, date, content_length):
    x_headers = 'x-ms-date:' + date
    string_to_hash = f"POST\n{content_length}\napplication/json\n{x_headers}\n/api/logs"
    bytes_to_hash = bytes(string_to_hash, encoding="utf-8")
    decoded_key = base64.b64decode(shared_key)
    encoded_hash = base64.b64encode(hmac.new(decoded_key, bytes_to_hash, digestmod=hashlib.sha256).digest()).decode()
    authorization = "SharedKey {}:{}".format(customer_id, encoded_hash)
    return authorization


# Build and send a request to the POST API
def post_data(customer_id, shared_key, body):

    rfc1123date = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    content_length = len(body)
    signature = build_signature(customer_id, shared_key, rfc1123date, content_length)
    headers = {
        'content-type': 'application/json',
        'Authorization': signature,
        'Log-Type': 'CatoAudit',
        'Time-generated-field': 'audit_timestamp',
        'x-ms-date': rfc1123date
    }
    try:
        request = urllib.request.Request(
            url='https://' + customer_id + '.ods.opinsights.azure.com/api/logs?api-version=2016-04-01',
            data=body,
            headers=headers,
            method="POST"
        )
        response = urllib.request.urlopen(request, timeout=30)
    except urllib.error.URLError as e:
        print(f"Azure API ERROR:{e}")
        sys.exit(1)
    except OSError as e:
        print(f"Azure API ERROR: {e}")
        sys.exit(1)
    return response.code


########################################################################################
########################################################################################
########################################################################################
# start of the main program

api_call_count = 0
total_bytes_compressed = 0
total_bytes_uncompressed = 0
start = datetime.datetime.now()

# Process options
parser = argparse.ArgumentParser()
parser.add_argument("-K", dest="api_key", help="API key")
parser.add_argument("-I", dest="ID", help="Account ID")
parser.add_argument("-T", dest="time_frame", help="Cato TimeFrame, for example last.P1D")
parser.add_argument("-P", dest="prettify", action="store_true", help="Prettify output")
parser.add_argument("-p", dest="print_events", action="store_true", help="Print audit records")
parser.add_argument("-n", dest="stream_events", help="Send audit records over network to host:port TCP")
parser.add_argument("-z", dest="sentinel", help="Send audit records to Sentinel customerid:sharedkey")
parser.add_argument("-m", dest="marker", help="Initial marker value (default is \"\", which means start of the query window)")
parser.add_argument("-c", dest="config_file", help="Config file location (default ./config.txt)")
parser.add_argument("-F", dest="filters", help="Comma-separated field=value audit filters")
parser.add_argument("-f", dest="fetch_limit", help="Stop execution if a fetch returns less than this number of audit records (default=1)")
parser.add_argument("-r", dest="runtime_limit", help="Stop execution if total runtime exceeds this many seconds (default=infinite)")
parser.add_argument("-v", dest="verbose", action="store_true", help="Print debug info")
parser.add_argument("-V", dest="veryverbose", action="store_true", help="Print detailed debug info")
args = parser.parse_args()
if args.api_key is None or args.ID is None or args.time_frame is None:
    parser.print_help()
    sys.exit(1)


# The auditFeed marker is scoped to a specific timeFrame. The config file stores
# the marker together with the timeFrame it belongs to, so that a run against a
# different time window starts cleanly instead of reusing a stale marker.
def read_config(path):
    """Return (marker, time_frame, seen_hashes) from the config file.

    Supports the JSON format written by this script as well as a legacy
    plain-text marker file (a single line containing just the marker)."""
    try:
        with open(path, "r") as f:
            content = f.read().strip()
    except IOError as e:
        log(f"Couldn't read config file: {e}")
        return "", None, []
    if not content:
        return "", None, []
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            seen = data.get("seenHashes") or []
            if not isinstance(seen, list):
                seen = []
            return data.get("marker", "") or "", data.get("timeFrame"), seen
    except ValueError:
        pass
    # legacy plain-text marker (no associated timeFrame / dedup state)
    return content.splitlines()[0].strip(), None, []


# either use the default marker or load from config file
config_file = "./config.txt"
marker = ""
seen_hashes = []
if args.config_file is None:
    log(f"No config file specified, using default: {config_file}")
else:
    config_file = args.config_file
    log(f"Using config file from -c parameter: {config_file}")
if args.marker is None:
    log("No marker value supplied, attempting to load from config file")
    # does the config file exist, if so load the marker value
    if os.path.isfile(config_file):
        log(f"Found config file: {config_file}")
        stored_marker, stored_time_frame, stored_seen = read_config(config_file)
        if stored_time_frame is not None and stored_time_frame != args.time_frame:
            log(f"Stored timeFrame '{stored_time_frame}' differs from requested '{args.time_frame}', resetting marker and dedup state")
            marker = ""
            seen_hashes = []
        else:
            marker = stored_marker
            seen_hashes = stored_seen
            log(f"Read marker from config_file: {marker} ({len(seen_hashes)} seen hashes)")
    else:
        log("Config file does not exist, sticking with default marker")
else:
    # explicit marker override means manual repositioning, so drop dedup memory
    marker = args.marker
    seen_hashes = []
    log(f"Using marker value from -m parameter: {marker}")

seen_set = set(seen_hashes)

# process audit filters
if args.filters is not None:
    log(f"Audit filter parameter: {args.filters}")
    audit_filters = parse_filters(args.filters)
    log("Audit filters: " + json.dumps(audit_filters))
else:
    audit_filters = []


# process network options
if args.stream_events is not None:
    network_elements = args.stream_events.split(":")
    if len(network_elements) != 2:
        print("Error: -n value must be in the form of host:port")
        parser.print_help()
        sys.exit(1)
    try:
        int(network_elements[1])
    except ValueError:
        print("Error: -n port must be a valid integer")
        parser.print_help()
        sys.exit(1)

# process sentinel options
if args.sentinel is not None:
    sentinel_elements = args.sentinel.split(":")
    if len(sentinel_elements) != 2:
        print("Error: -z value must be in the form of customerid:sharedkey")
        parser.print_help()
        sys.exit(1)

# fetch count
if args.fetch_limit is None:
    FETCH_THRESHOLD = 1
else:
    FETCH_THRESHOLD = int(args.fetch_limit)

# runtime threshold
if args.runtime_limit is None:
    RUNTIME_LIMIT = sys.maxsize
else:
    RUNTIME_LIMIT = int(args.runtime_limit)

# API call loop
iteration = 1
total_count = 0
while True:
    sent_marker = marker
    variables = build_variables(marker, audit_filters)

    logd(GRAPHQL_QUERY)
    logd(json.dumps(variables))
    success, resp = send(GRAPHQL_QUERY, variables)
    if not success:
        print(resp)
        sys.exit(1)
    logd(resp)

    audit_feed = resp["data"]["auditFeed"]
    marker = audit_feed.get("marker") or ""
    fetched_count = int(audit_feed.get("fetchedCount", 0))
    has_more = bool(audit_feed.get("hasMore"))

    # Construct list of audit records, with added timestamps and reordering.
    audit_list = []
    for account in audit_feed.get("accounts", []) or []:
        account_id = account.get("id")
        for record in account.get("records", []) or []:
            audit_list.append(normalize_audit_record(record, account_id))

    # Deduplicate: the auditFeed marker boundary is inclusive, so the last
    # record(s) of a drained window are re-returned on the next poll. Drop any
    # record we have already emitted. Robust even if the API changes its
    # boundary/marker behavior in the future.
    new_records = []
    duplicate_count = 0
    for audit_record in audit_list:
        h = record_identity(audit_record)
        if h in seen_set:
            duplicate_count += 1
            continue
        seen_set.add(h)
        seen_hashes.append(h)
        new_records.append(audit_record)

    # bound the persisted dedup set to the most recent entries
    if len(seen_hashes) > MAX_SEEN_HASHES:
        drop = len(seen_hashes) - MAX_SEEN_HASHES
        for old in seen_hashes[:drop]:
            seen_set.discard(old)
        seen_hashes = seen_hashes[drop:]

    audit_list = new_records
    total_count += len(audit_list)
    line = f"iteration:{iteration} fetched:{fetched_count} new:{len(audit_list)} dup:{duplicate_count} total_count:{total_count} marker:{marker} hasMore:{has_more}"

    if len(audit_list) > 0:
        line += " " + audit_list[0].get("audit_timestamp", "")
        line += " " + audit_list[-1].get("audit_timestamp", "")
    log(line)

    # print output
    if args.print_events:
        for audit_record in audit_list:
            if args.prettify:
                print(json.dumps(audit_record, indent=2, ensure_ascii=False))
            else:
                try:
                    print(json.dumps(audit_record, ensure_ascii=False))
                except Exception:
                    print(json.dumps(audit_record))

    # network stream
    if args.stream_events is not None:
        logd(f"Sending audit records to {network_elements[0]}:{network_elements[1]}")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # bound connect/send so a hung receiver cannot block the run forever
            s.settimeout(30)
            s.connect((network_elements[0], int(network_elements[1])))
            for audit_record in audit_list:
                s.sendall(json.dumps(audit_record, ensure_ascii=False).encode("utf-8"))

    # send to Microsoft Sentinel
    if args.sentinel is not None:
        logd(f"Sending audit records to Azure workspace ID {sentinel_elements[0]}")
        response_status = post_data(
            sentinel_elements[0],
            sentinel_elements[1],
            json.dumps(audit_list, ensure_ascii=False).encode('utf-8')
        )
        if response_status < 200 or response_status > 299:
            print(f"Send to Azure returned {response_status}, exiting")
            sys.exit(1)
        logd(f"Send to Azure response code:{response_status}")

    # write marker back out after the current batch is processed successfully.
    # Persist the timeFrame alongside the marker so a future run against a
    # different time window resets the marker (the marker is timeFrame-scoped).
    logd("Writing marker to " + config_file)
    with open(config_file, "w") as File:
        json.dump({
            "accountID": args.ID,
            "timeFrame": args.time_frame,
            "marker": marker,
            "seenHashes": seen_hashes,
        }, File)

    # increment counter and check if we hit any limits for stopping
    iteration += 1
    if not has_more:
        log("No more audit records available, stopping")
        break
    # guard against a stuck feed: if the marker did not advance but the API
    # still reports hasMore, paginating again would just refetch the same
    # records (all deduplicated to nothing) forever, so stop here
    if marker == sent_marker:
        log(f"Marker did not advance ({marker!r}) while hasMore is true, stopping to avoid an infinite loop")
        break
    if fetched_count < FETCH_THRESHOLD:
        log(f"Fetched count {fetched_count} less than threshold {FETCH_THRESHOLD}, stopping")
        break
    elapsed = datetime.datetime.now() - start
    if elapsed.total_seconds() > RUNTIME_LIMIT:
        log(f"Elapsed time {elapsed.total_seconds()} exceeds runtime limit {RUNTIME_LIMIT}, stopping")
        break

end = datetime.datetime.now()
log(f"OK {total_count} audit records from {api_call_count} API calls with {total_bytes_uncompressed} bytes uncompressed, {total_bytes_compressed} bytes compressed in {end-start}")
