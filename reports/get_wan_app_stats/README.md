# WAN App Stats Analyzer

A Python script for fetching and analyzing WAN-bound application statistics from Cato Networks using the Cato CLI, with support for timeseries data processing and CSV report generation.

## Features

- Fetch WAN application statistics from Cato Networks via `catocli`
- Process timeseries data into hourly breakdowns
- Generate detailed hourly CSV reports
- Create pivot table summaries by application and user
- Support for both upstream and downstream traffic analysis
- Configurable time ranges and granularity

## Requirements

- Python 3.6+
- `catocli` (Cato CLI tool)
- Access to Cato Networks account with appropriate permissions

## Installation

### 1. Install Cato CLI

First, install the Cato CLI tool:

```bash
pip3 install catocli
```

### 2. Configure Cato CLI

Configure catocli with your Cato credentials:

```bash
catocli configure set
```

This will prompt you to enter:
- Your Cato API token
- API base URL (typically the default is fine)
- Other authentication details

You can verify your configuration with:

```bash
catocli configure show
```

### 3. Download the Script

1. Clone or download the script to your local machine
2. Make sure you have the required Python modules (all standard library)
3. Ensure the script has execute permissions if needed

## Usage

### Basic Usage

```bash
python get_app_stats.py --account-id YOUR_ACCOUNT_ID
```

### Advanced Usage

```bash
python get_app_stats.py \
  --account-id YOUR_ACCOUNT_ID \
  --days 7 \
  --buckets 168 \
  --output-prefix wan_stats_weekly
```

### Command Line Options

- `--account-id` (required): Your Cato account ID
- `--days` (default: 14): Number of days to look back
- `--buckets` (default: 336): Number of time buckets for the analysis
- `--granularity` (default: 3600): Data granularity in seconds (3600 = hourly)
- `--output-prefix` (default: wan_app_stats): Prefix for output files

## Output Files

The script generates three types of output files:

### 1. Raw JSON Data (`*_raw.json`)
Contains the raw response from the Cato API for debugging and reprocessing.

### 2. Hourly CSV Report (`*_hourly.csv`)
Detailed breakdown of bandwidth usage by hour, application, user, and traffic direction.

**Format:**
```csv
hour,application,user_name,measure_type,bandwidth_mb
2025-08-14 14:00:00,Company APP,PM Analyst,downstream,36.0
2025-08-14 14:00:00,Company APP,PM Analyst,upstream,1.467
```

**Columns:**
- `hour`: Timestamp in YYYY-MM-DD HH:MM:SS format
- `application`: Application name
- `user_name`: User name
- `measure_type`: Either "upstream" or "downstream"
- `bandwidth_mb`: Bandwidth usage in megabytes

### 3. Summary CSV Report (`*_summary.csv`)
Pivot table showing total bandwidth usage by application and user.

**Format:**
```csv
application,User1_mb,User2_mb,total_mb
Company APP,1234.5,2345.6,3580.1
DNS,567.8,890.1,1457.9
```

### Data Processing

The script processes Cato's timeseries data format:
- Extracts application and user information from series labels using regex
- Converts Unix timestamps (milliseconds) to readable datetime strings
- Handles bandwidth values (already in MB from API)
- Filters out zero-value data points

## Example Output Statistics

When run, the script displays summary statistics:

```
Statistics:
  - Total records: 2176
  - Total bandwidth: 53612.89 MB
  - Total upstream: 31383.09 MB
  - Total downstream: 22229.80 MB

Top 10 Applications by Bandwidth:
  - Company APP: 31383.09 MB
  - DNS: 22229.80 MB
  - RDP: 13.06 MB

Bandwidth by User:
  - Another User: 33090.19 MB
  - Mary Berry: 20532.49 MB
  - Some User: 3.32 MB
```

## Data Structure

The script expects Cato API timeseries data with the following structure:
```json
{
  "data": {
    "appStatsTimeSeries": {
      "timeseries": [
        {
          "label": "sum(downstream) for application_name='App Name', user_name='User Name'",
          "data": [
            [timestamp_ms, bandwidth_mb],
            ...
          ]
        }
      ]
    }
  }
}
```

## Error Handling

The script includes error handling for:
- Failed catocli command execution
- JSON parsing errors
- Missing or invalid data structures
- File I/O operations

## Troubleshooting

### Common Issues

1. **catocli not found**: Ensure catocli is installed and in your PATH
2. **Authentication errors**: Verify catocli is configured with valid credentials
3. **Account ID errors**: Confirm you're using the correct Cato account ID
4. **No data returned**: Check the time range and ensure there's WAN traffic in the specified period

### Debug Steps

1. Check if the raw JSON file contains data
2. Verify the timeseries structure matches expected format
3. Run with shorter time ranges to isolate issues
4. Check catocli configuration: `catocli configure show`

## File Structure

```
.
├── get_app_stats.py          # Main script
├── README.md                 # This file
├── *_raw.json               # Raw API response (generated)
├── *_hourly.csv             # Hourly breakdown (generated)
└── *_summary.csv            # Summary pivot table (generated)
```

## License

This script is provided as-is for use with Cato Networks environments.
