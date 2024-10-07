# eventsFeed.py

An example of how to use the eventsFeed() API to extract events from Cato. 
The eventsFeed Python script is an example of how to use the eventsFeed() API to extract events from the Cato SASE Cloud Platform, retrieves and processes event data, and outputs it in multiple configurable formats. It supports customizable filters, real-time or scheduled processing, and offers logging for error handling.

## Features include:
* Marker persistence.
* Multiple stop conditions, including number of events fetched and total execution time.
* Multiple output options, including pretty print, Azure API and network stream.
* Error handling and compression.

## Usage

```bash
python eventsFeed.py [options]

python eventsFeed.py -K YOURAPIKEY -I YOURACCOUNTID -p -s "NG Anti Malware,Anti Malware"
```

## Example

```bash
python eventsFeed.py -K abcde12345 -I 1234 -p -s "NG Anti Malware,Anti Malware"
```

### Config Options ####

| Flag                      | Description                                                                 |
|----------------------------|-----------------------------------------------------------------------------|
| `-h`, `--help`             | Show help message and exit                                                   |
| `-K API_KEY`               | API key for authenticating requests to the Cato API                          |
| `-I ID`                    | Account ID associated with your Cato account                                 |
| `-P`                       | Prettify output for readability                                              |
| `-p`                       | Print event records to the console                                           |
| `-n STREAM_EVENTS`         | Send events over network to a specified `host:port` via TCP                  |
| `-z SENTINEL`              | Send events to Microsoft Sentinel in `customerid:sharedkey` format           |
| `-m MARKER`                | Specify the initial marker value (default: `""`, meaning start of the queue) |
| `-c CONFIG_FILE`           | Path to the config file (default: `./config.txt`)                            |
| `-t EVENT_TYPES`           | Comma-separated list of event types to filter on                             |
| `-s EVENT_SUB_TYPES`       | Comma-separated list of event sub-types to filter on                         |
| `-f FETCH_LIMIT`           | Stop execution if a fetch returns fewer than this number of events (default: `1`) |
| `-r RUNTIME_LIMIT`         | Stop execution if total runtime exceeds this many seconds (default: infinite) |
| `-v`                       | Print debug information                                                     |
| `-V`                       | Print detailed debug information                                             |
