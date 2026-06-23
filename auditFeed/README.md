# auditFeed.py

An example of how to use the auditFeed() API to extract audit records from Cato.
The auditFeed Python script is an example of how to use the auditFeed() API to extract audit messages from the Cato SASE Cloud Platform, retrieves and processes audit data, and outputs it in multiple configurable formats. It supports marker persistence, time frame selection, customizable audit filters, and logging for error handling.

## Features include:
* Marker persistence, scoped to the requested time frame (the marker is reset automatically when `-T` changes, since auditFeed markers are time-frame specific).
* Exactly-once delivery: the auditFeed marker boundary is inclusive, so the last record of a drained window is re-returned on the next poll. The script remembers recently emitted records and drops these duplicates, so each audit entry is returned exactly once (robust even if the API boundary behavior changes).
* Time frame based audit retrieval.
* Marker pagination using the auditFeed `hasMore` response.
* Multiple stop conditions, including number of audit records fetched and total execution time.
* Multiple output options, including pretty print, Azure API and network stream.
* Error handling, compression, and exponential backoff with `Retry-After` support for rate limits.

## Usage

```bash
python auditFeed.py [options]

python auditFeed.py -K YOURAPIKEY -I YOURACCOUNTID -T last.P1D -p -F change_type=CREATED
```

## Example

```bash
python auditFeed.py -K abcde12345 -I 1234 -T last.P1D -p -F change_type=CREATED
```

## TimeFrame examples

```bash
python auditFeed.py -K YOURAPIKEY -I YOURACCOUNTID -T last.PT1H -p
python auditFeed.py -K YOURAPIKEY -I YOURACCOUNTID -T last.P1D -p
python auditFeed.py -K YOURAPIKEY -I YOURACCOUNTID -T "utc.2026-06-{16/00:00:00--16/23:59:59}" -p
```

### Config Options ####

| Flag                      | Description                                                                 |
|----------------------------|-----------------------------------------------------------------------------|
| `-h`, `--help`             | Show help message and exit                                                   |
| `-K API_KEY`               | API key for authenticating requests to the Cato API                          |
| `-I ID`                    | Account ID associated with your Cato account                                 |
| `-T TIME_FRAME`            | Cato TimeFrame, for example `last.P1D`                                       |
| `-P`                       | Prettify output for readability                                              |
| `-p`                       | Print audit records to the console                                           |
| `-n STREAM_EVENTS`         | Send audit records over network to a specified `host:port` via TCP           |
| `-z SENTINEL`              | Send audit records to Microsoft Sentinel in `customerid:sharedkey` format    |
| `-m MARKER`                | Specify the initial marker value (default: `""`, meaning start of the query window) |
| `-c CONFIG_FILE`           | Path to the config file (default: `./config.txt`)                            |
| `-F FILTERS`               | Comma-separated `field=value` audit filters, for example `change_type=CREATED` |
| `-f FETCH_LIMIT`           | Stop execution if a fetch returns fewer than this number of audit records (default: `1`) |
| `-r RUNTIME_LIMIT`         | Stop execution if total runtime exceeds this many seconds (default: infinite) |
| `-v`                       | Print debug information                                                     |
| `-V`                       | Print detailed debug information                                             |
