# CatoCLI User Guide

This comprehensive user guide provides detailed information on using the Cato Networks CLI (`catocli`) for various query operations and reporting tasks.

## Overview

CatoCLI is a command-line interface that provides access to the Cato Networks GraphQL API, enabling you to:
- Generate detailed network and security reports
- Analyze user and application activity
- Monitor network performance and events
- Export data in multiple formats (JSON, CSV)
- Automate reporting and monitoring tasks

## Prerequisites

- Python 3.6 or higher
- CatoCLI installed (`pip3 install catocli`)
- Valid Cato Networks API token and Account ID
- Proper authentication configuration (see [Authentication Setup](#authentication-setup))

## Authentication Setup

Configure your CatoCLI profile before using any query operations:

```bash
# Interactive configuration
catocli configure set

# Non-interactive configuration
catocli configure set --cato-token "your-api-token" --account-id "12345"

# List configured profiles
catocli configure list

# Show current profile
catocli configure show
```

## Query Operations

### Core Analytics Queries

| Operation | Description | Guide |
|-----------|-------------|--------|
| [Account Metrics](./account-metrics.md) | Network performance metrics by site, user, or interface | 📊 |
| [Application Statistics](./app-stats.md) | User activity and application usage analysis | 📱 |
| [Application Time Series](./app-stats-timeseries.md) | Traffic analysis over time with hourly/daily breakdowns | 📈 |
| [Events Time Series](./events-timeseries.md) | Security events, connectivity, and threat analysis | 🔒 |
| [Socket Port Metrics](./socket-port-metrics.md) | Socket interface performance and traffic analysis | 🔌 |
| [Socket Port Time Series](./socket-port-timeseries.md) | Socket performance metrics over time | ⏱️ |

### Advanced Topics

- [Common Patterns & Best Practices](./common-patterns.md) - Output formats, time frames, filtering patterns
- [Python Integration - Windows](./python-integration-windows.md) - Windows-specific Python automation examples
- [Python Integration - Unix/Linux/macOS](./python-integration-unix.md) - Unix-based Python integration guide
- [SIEM Integration Guide](./siem-integration.md) - Real-time security event streaming to SIEM platforms

## Quick Start Examples

### Basic Network Health Check
```bash
# Get last hour account metrics
catocli query accountMetrics '{"timeFrame":"last.PT1H"}'
```

### User Activity Report (csv format)
```bash
# Export user activity for the last month to CSV
catocli query appStats '{
    "dimension": [{"fieldName": "user_name"}],
    "measure": [{"aggType": "sum", "fieldName": "flows_created"}],
    "timeFrame": "last.P1M"
}' -f csv --csv-filename user_activity_report.csv
```

### Security Events Analysis
```bash
# Weekly security events breakdown
catocli query eventsTimeSeries '{
    "buckets": 7,
    "eventsFilter": [{"fieldName": "event_type", "operator": "is", "values": ["Security"]}],
    "eventsMeasure": [{"aggType": "sum", "fieldName": "event_count"}],
    "timeFrame": "last.P7D"
}'
```

## Output Formats

CatoCLI supports multiple output formats:

- **Enhanced JSON** (default): Formatted with granularity adjustments
- **Raw JSON**: Original API response with `-raw` flag
- **CSV**: Structured data export with `-f csv`
- **Custom CSV**: Named files with `--csv-filename` and `--append-timestamp`

## Time Frame Options

Common time frame patterns:
- `last.PT1H` - Last hour
- `last.P1D` - Last day  
- `last.P7D` - Last week
- `last.P1M` - Last month
- `utc.2023-02-{28/00:00:00--28/23:59:59}` - Custom UTC range

## Getting Help

- Use `-h` or `--help` with any command for detailed usage
- Check the [Cato API Documentation](https://api.catonetworks.com/documentation/)
- Review individual operation guides linked above

## Support and Contributions

For issues, enhancements, or contributions to this user guide, please refer to the main Cato Toolbox repository.

---

*This user guide is part of the Cato Toolbox project and is continuously updated with new examples and use cases.*