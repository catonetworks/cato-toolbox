# auditFeed Incremental Retrieval Specification

## Purpose

This specification defines the required behavior for a Cato `auditFeed` incremental retrieval script. It is intended for spec-driven development so an agent can re-create the feature or safely update an existing implementation.

The implementation must retrieve audit records from Cato `auditFeed`, page through results using the API marker, persist state between runs, and emit each audit record exactly once even when the API re-returns records at the marker boundary.

## Scope

In scope:

- Cato GraphQL `auditFeed` query execution.
- Required CLI parameters for API key, account ID, and time frame.
- Optional filtering by audit field.
- Marker persistence and reuse.
- Time-frame-scoped marker reset.
- Record-level deduplication across process restarts.
- Output to stdout, TCP stream, and Microsoft Sentinel.
- Retry behavior for transient errors and rate limits.

Out of scope:

- Automatic time-window scheduling or generation.
- Durable database storage.
- Multi-process state locking.
- Guaranteeing global exactly-once delivery across multiple concurrently running copies of the script using the same state file.

## API Contract

### Endpoint

The default Cato endpoint is:

```text
https://api.catonetworks.com/api/v1/graphql2
```

The request method is `POST`.

### Authentication

The Cato API key must be supplied in the `x-api-key` HTTP header.

Security requirements:

- The API key must never be hardcoded in source code.
- The API key must not be written to the state file.
- The API key must not be logged, printed, or included in error messages.

### GraphQL Query

The implementation must use a parameterized GraphQL request body with variables, not string interpolation for user-controlled values.

```graphql
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
```

Example request body:

```json
{
  "query": "query auditFeed(...) { ... }",
  "operationName": "auditFeed",
  "variables": {
    "accountIDs": ["12345"],
    "timeFrame": "last.P1D",
    "marker": "",
    "filters": [
      {
        "fieldNameInput": {
          "AuditFieldName": "change_type"
        },
        "operator": "is",
        "values": ["CREATED"]
      }
    ]
  }
}
```

### API Parameters

Required:

- `accountIDs`: list of Cato account IDs. The script CLI may accept a single `-I` account ID and send it as a one-item array.
- `timeFrame`: Cato `TimeFrame`, for example `last.P1D` or `utc.2026-06-{16/00:00:00--16/23:59:59}`.

Optional:

- `marker`: pagination marker returned from the previous response. Use `""` or omit/null for the first request in a time frame.
- `filters`: list of `AuditFieldFilterInput` objects.

Not supported:

- `limit`, `pageSize`, or explicit batch size. `auditFeed` does not expose a limit/page-size parameter. Pagination is controlled by `marker` and `hasMore`.

## CLI Contract

The script must expose these parameters:

- `-K API_KEY`: Cato API key. Required.
- `-I ID`: Cato account ID. Required.
- `-T TIME_FRAME`: Cato `TimeFrame`. Required.
- `-P`: pretty-print JSON output.
- `-p`: print audit records to stdout.
- `-n STREAM_EVENTS`: send records over TCP to `host:port`.
- `-z SENTINEL`: send records to Microsoft Sentinel as `customerid:sharedkey`.
- `-m MARKER`: initial marker override. Default behavior is to load marker from state.
- `-c CONFIG_FILE`: state/config file path. Default `./config.txt`.
- `-F FILTERS`: comma-separated `field=value` filters.
- `-f FETCH_LIMIT`: stop if a fetch returns fewer than this many records. Default `1`.
- `-r RUNTIME_LIMIT`: stop after this many seconds. Default infinite.
- `-v`: debug logging.
- `-V`: detailed debug logging.

Example commands:

```bash
python3 auditFeed.py -K "$CATO_API_KEY" -I 12345 -T last.P1D -p
python3 auditFeed.py -K "$CATO_API_KEY" -I 12345 -T last.P1D -pP -F change_type=CREATED
python3 auditFeed.py -K "$CATO_API_KEY" -I 12345 -T "utc.2026-06-{16/00:00:00--16/23:59:59}" -c ./config.txt -p
```

## Filter Contract

`-F` must parse comma-separated `field=value` pairs into `AuditFieldFilterInput` objects:

```json
{
  "fieldNameInput": {
    "AuditFieldName": "change_type"
  },
  "operator": "is",
  "values": ["CREATED"]
}
```

Rules:

- Empty field names or empty values must be rejected.
- Pairs without `=` must be rejected.
- Multiple values for the same field should be grouped into one filter object's `values` array.
- User input must be serialized through GraphQL variables, not interpolated directly into query text.

## State File Contract

The state file must be JSON when written by the script.

Required state schema:

```json
{
  "accountID": "12345",
  "timeFrame": "last.P1D",
  "marker": "1781883741985_",
  "seenHashes": [
    "sha256-record-hash"
  ]
}
```

Backward compatibility:

- A legacy plain-text marker file containing only a marker string may be read.
- If a legacy state file is read, `timeFrame` is unknown and `seenHashes` starts empty.

Security requirements:

- The state file must not contain API keys, Sentinel shared keys, or other secrets.
- The state file may contain audit record hashes, but not raw audit records.

## Marker Semantics

Observed `auditFeed` behavior:

- The marker is scoped to the `timeFrame`.
- A marker from one `timeFrame` must not be reused with a different `timeFrame`.
- The marker boundary is inclusive: after a drained query returns `hasMore: false`, a subsequent call with the returned marker may return the last record again.
- The marker may remain unchanged when the API re-returns a boundary record.

Required behavior:

- On first run for a time frame, use marker `""` unless `-m` is supplied.
- After each successful batch is fully processed, persist the response marker.
- If the stored state `timeFrame` differs from the requested `-T`, reset marker to `""` and reset deduplication state.
- If `-m` is supplied, use it as the starting marker and reset deduplication state, because this is manual repositioning.
- Do not attempt to manually calculate or mutate Cato markers.
- If the response marker equals the marker that was just sent while `hasMore` is true, treat the feed as stuck and stop, because continuing would refetch the same records (all deduplicated to nothing) forever. See Termination Guarantees.

## Polling Sequence

For a single run:

1. Load state from `-c CONFIG_FILE` if no explicit `-m` is supplied.
2. If the stored `timeFrame` differs from `-T`, reset marker and dedup state.
3. Build GraphQL variables using current marker, account ID, time frame, and filters.
4. Call `auditFeed`.
5. Normalize response records into output records.
6. Deduplicate records against persisted `seenHashes`.
7. Emit only new records to configured outputs.
8. Persist state with the response marker and updated `seenHashes`.
9. If `hasMore` is true, repeat from step 3 using the newly persisted marker.
10. Stop when `hasMore` is false, when the marker did not advance, or when a configured fetch/runtime stop condition is reached. See Termination Guarantees.

Important invariant:

- State must be persisted only after the current batch has been processed and emitted successfully. This prevents marker advancement from skipping records after an output failure.

## Record Normalization

Each Cato audit record must be transformed into a flat JSON object suitable for stdout, TCP streaming, and Sentinel.

Rules:

- Prefer `fieldsMap` when it is present and is a JSON object.
- If `fieldsMap` is unavailable, fall back to `flatFields` where possible.
- Add `audit_timestamp` from `record.time`.
- Add `event_timestamp` from `record.time` for downstream compatibility.
- Add `account_id` from the account container if not already present.
- Order timestamp keys first in the emitted JSON object when possible.

## Exactly-Once Deduplication

Problem:

- `auditFeed` may re-return the boundary record when the previous response marker is used in a later call.
- This can happen across process restarts and can happen even when `hasMore` is false.
- Future API behavior may change, so the implementation must not rely only on `hasMore` or marker equality.

Required solution:

- Compute a stable identity hash for each normalized audit record.
- Keep a persisted, bounded list of recently emitted hashes in `seenHashes`.
- Before any output, drop records whose identity hash is already in the seen set.
- Add newly emitted records to the seen set.
- Persist the updated seen set with the marker after output succeeds.
- Bound `seenHashes` to `MAX_SEEN_HASHES` recent entries. The canonical value is `5000`.

Canonical identity:

```python
serialized = json.dumps(audit_record, sort_keys=True, ensure_ascii=False)
record_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
```

For implementations that hash raw `flatFields` arrays, normalize/sort `flatFields` before hashing so ordering differences do not produce false new records.

Caveat:

- If Cato returns two genuinely distinct records with byte-identical normalized content and timestamp, content-hash deduplication will suppress the second record. If Cato exposes a stable unique audit record ID in the future, prefer that ID as the primary dedup key.

## Output Contract

Stdout:

- Emit one JSON object per audit record unless `-P` is set.
- With `-P`, emit indented JSON.
- Emit only deduplicated new records.

TCP stream:

- Validate `host:port` format before running.
- Send only deduplicated new records.
- Do not include API keys or Sentinel keys in payloads.

Microsoft Sentinel:

- Validate `customerid:sharedkey` format before running.
- Use `Log-Type: CatoAudit`.
- Use `Time-generated-field: audit_timestamp`.
- Send only deduplicated new records.

## Retry and Error Handling

Required retry behavior:

- Retry transient HTTP errors, including `429`, `500`, `502`, `503`, and `504`.
- Honor `Retry-After` when present.
- Use exponential backoff when `Retry-After` is absent.
- Cap backoff at 30 seconds.
- Treat in-body rate-limit responses (HTTP 200 whose payload is a rate-limit error) as retryable, and count every such retry against the same bounded retry budget as transport errors. A retry path that sleeps and continues without incrementing the retry counter is a defect, because the bound can never be reached and the script spins forever.
- Stop after a bounded retry count and exit with a nonzero status.

Required failure behavior:

- If the Cato API returns GraphQL `errors`, do not advance the marker.
- If output to a configured destination fails, do not advance the marker.
- Error messages must not expose secrets.

## Termination Guarantees

The script must always make progress or stop. Every retry or polling loop must have a bound that is guaranteed to be reached.

Required behavior:

- Every retry loop must increment a retry counter on every retry path (transport errors, HTTP error status, and in-body rate-limit responses) and must exit once the bound is exceeded.
- The pagination loop must stop when the response marker equals the marker just sent while `hasMore` is true (no-progress guard), so a stuck or misbehaving feed cannot loop forever.
- The pagination loop must also stop on the existing conditions: `hasMore` is false, fetched count below the fetch threshold, or runtime limit exceeded.
- Any network output (TCP stream, Sentinel) must use a bounded socket or request timeout so a hung receiver cannot block the run indefinitely. The canonical timeout is 30 seconds, matching the GraphQL request timeout.

Rationale:

- A retry path that does not increment the counter, or a pagination loop with no no-progress guard, can run forever and is treated as a defect.

## Logging

Debug logging may include:

- Iteration number.
- API fetch count.
- New record count.
- Duplicate record count.
- Total emitted count.
- Marker value.
- `hasMore`.
- First and last emitted audit timestamps.

Debug logging must not include:

- Cato API key.
- Sentinel shared key.
- Full raw API responses unless explicitly requested for local debugging and scrubbed for secrets.

## Acceptance Criteria

### API request

- Given `-K KEY -I 12345 -T last.P1D`, the request body uses GraphQL variables with `accountIDs: ["12345"]`, `timeFrame: "last.P1D"`, and a marker value.
- No `limit` or `pageSize` field is sent.

### Marker reset

- Given a state file with `timeFrame: "last.P1D"` and the script runs with `-T last.PT1H`, the script sends marker `""` and clears `seenHashes`.

### Boundary duplicate

- Given run 1 receives records `[A, B]`, marker `M`, and `hasMore: false`.
- And run 2 sends marker `M` and receives `[B]`.
- Then run 2 emits no records and persists marker `M`.

### Mixed duplicate and new record

- Given the state already contains hash for record `B`.
- And the next response contains `[B, C]`.
- Then the script emits only `C`, records one duplicate, and persists hashes for `B` and `C`.

### API behavior change

- Given the API stops re-returning the boundary record.
- And the next response contains only new records.
- Then the dedup layer emits all returned records and does not alter correct behavior.

### Restart persistence

- Given the script emitted record `B` and persisted its hash.
- And the process exits.
- When the script starts again with the same state file and the API returns `B`.
- Then `B` is dropped as a duplicate.

### Output safety

- Given `-p`, `-n`, or `-z` are configured.
- Then each output receives only deduplicated new records.
- If any configured output fails, the marker is not advanced.

### Bounded in-body rate-limit retries

- Given the API repeatedly returns an HTTP 200 in-body rate-limit error.
- Then each retry increments the retry counter.
- And the script exits with a nonzero status once the retry bound is exceeded, rather than looping forever.

### No-progress pagination stop

- Given a response with `hasMore: true` and a marker equal to the marker just sent.
- Then the script stops the pagination loop instead of issuing another identical request.

### Bounded network output

- Given `-n` is configured and the receiver accepts the connection but never reads.
- Then the send is bounded by a socket timeout and the run does not block indefinitely.

## Implementation Checklist

- [ ] Use parameterized GraphQL query and variables.
- [ ] Validate required CLI inputs.
- [ ] Validate `-n host:port` and `-z customerid:sharedkey`.
- [ ] Parse `-F field=value` filters into `AuditFieldFilterInput`.
- [ ] Load marker, time frame, and `seenHashes` from state.
- [ ] Reset marker and dedup state when `timeFrame` changes.
- [ ] Reset dedup state when explicit `-m` is supplied.
- [ ] Normalize records from `fieldsMap` or `flatFields`.
- [ ] Compute record identity hashes before output.
- [ ] Drop records already present in `seenHashes`.
- [ ] Emit only new records.
- [ ] Persist marker and updated `seenHashes` only after output succeeds.
- [ ] Bound `seenHashes` to `MAX_SEEN_HASHES`.
- [ ] Retry transient API errors with `Retry-After` or exponential backoff.
- [ ] Increment the retry counter on every retry path, including in-body rate-limit responses, so the retry bound is always reachable.
- [ ] Stop pagination when the marker does not advance while `hasMore` is true.
- [ ] Set a bounded socket/request timeout on all network output.
- [ ] Keep secrets out of code, logs, and state.
- [ ] Add tests or simulation for boundary duplicate and mixed duplicate/new pages.

