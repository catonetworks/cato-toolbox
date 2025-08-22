#!/usr/bin/env python3
import json
import csv
import subprocess
import argparse
import re
from datetime import datetime
from collections import defaultdict


def main():
    parser = argparse.ArgumentParser(description='Get WAN app stats from Cato and generate CSV reports')
    parser.add_argument('--account-id', required=True, help='Cato account ID')
    parser.add_argument('--days', type=int, default=14, help='Number of days to look back (default: 14)')
    parser.add_argument('--buckets', type=int, default=336, help='Number of time buckets (default: 336)')
    parser.add_argument('--granularity', type=int, default=3600, help='Granularity of the data in seconds (default: 3600)')
    parser.add_argument('--output-prefix', default='wan_app_stats', help='Output file prefix (default: wan_app_stats)')
    
    args = parser.parse_args()
    
    print(f"Fetching WAN app stats for last {args.days} days")
    print(f"Account ID: {args.account_id}")
    print(f"Buckets: {args.buckets}")
    
    # Get data from catocli
    data = get_wan_app_stats(args.account_id, args.days, args.buckets)
    
    if not data:
        print("Failed to get app stats data")
        return
    
    # Save raw JSON
    raw_filename = f"{args.output_prefix}_raw.json"
    with open(raw_filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved raw data to {raw_filename}")
    
    # Process data
    hourly_records = process_data_to_csv(data)
    
    if hourly_records:
        # Save hourly CSV
        hourly_filename = f"{args.output_prefix}_hourly.csv"
        save_hourly_csv(hourly_records, hourly_filename)
        
        # Create pivot summary
        summary_filename = f"{args.output_prefix}_summary.csv"
        create_pivot_summary(hourly_records, summary_filename)
        
        # Print statistics
        total_records = len(hourly_records)
        total_bandwidth = sum(record['bandwidth_mb'] for record in hourly_records)
        
        # Calculate upstream and downstream totals
        upstream_total = sum(record['bandwidth_mb'] for record in hourly_records if record['measure_type'] == 'upstream')
        downstream_total = sum(record['bandwidth_mb'] for record in hourly_records if record['measure_type'] == 'downstream')
        
        print(f"\nStatistics:")
        print(f"  - Total records: {total_records}")
        print(f"  - Total bandwidth: {total_bandwidth:.2f} MB")
        print(f"  - Total upstream: {upstream_total:.2f} MB")
        print(f"  - Total downstream: {downstream_total:.2f} MB")
        
        # Top applications
        app_totals = defaultdict(float)
        for record in hourly_records:
            app_totals[record['application']] += record['bandwidth_mb']
        
        top_apps = sorted(app_totals.items(), key=lambda x: x[1], reverse=True)[:10]
        print(f"\nTop 10 Applications by Bandwidth:")
        for app, bandwidth in top_apps:
            print(f"  - {app}: {bandwidth:.2f} MB")
        
        # Usage by user
        user_totals = defaultdict(float)
        for record in hourly_records:
            user_totals[record['user_name']] += record['bandwidth_mb']
        
        print(f"\nBandwidth by User:")
        for user, bandwidth in sorted(user_totals.items(), key=lambda x: x[1], reverse=True):
            user_display = user if user else "(Unknown)"
            print(f"  - {user_display}: {bandwidth:.2f} MB")
    else:
        print("No data processed")


def exec_cli(command):
    """Execute catocli command and return parsed JSON response"""
    try:
        print(f"Executing: {command}")
        response = subprocess.run(command, shell=True, text=True, capture_output=True)
        if response.returncode != 0:
            print(f"Command failed with return code {response.returncode}")
            print(f"Error: {response.stderr}")
            return None
        result = json.loads(response.stdout)
        return result
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response: {e}")
        print(f"Raw response: {response.stdout}")
        return None
    except Exception as e:
        print(f"Failed to execute command: {e}")
        return None

def get_wan_app_stats(account_id, days=14, buckets=336):
    """Get WAN app stats using the exact catocli command structure"""
    query = {
        "appStatsFilter": [
            {
                "fieldName": "traffic_direction",
                "operator": "is",
                "values": ["WANBOUND"]
            }
        ],
        "buckets": buckets,
        "dimension": [
            {"fieldName": "user_name"},
            {"fieldName": "application_name"}
        ],
        "measure": [
            {"aggType": "sum", "fieldName": "upstream"},
            {"aggType": "sum", "fieldName": "downstream"}
        ],
        "timeFrame": f"last.P{days}D"
    }
    
    command = f"catocli query appStatsTimeSeries -accountID={account_id} '{json.dumps(query)}'"
    return exec_cli(command)

def process_data_to_csv(data):
    """Process the JSON timeseries data into hourly records"""
    if not data or 'data' not in data or 'appStatsTimeSeries' not in data['data']:
        print("No valid app stats data found")
        return []
    
    app_stats = data['data']['appStatsTimeSeries']
    if 'timeseries' not in app_stats:
        print("No timeseries found in app stats data")
        return []
    
    hourly_records = []
    
    # Parse each timeseries
    for series in app_stats['timeseries']:
        label = series.get('label', '')
        data_points = series.get('data', [])
        
        # Extract application and user from the label using regex
        # Example: "sum(downstream) for application_name='Company APP', user_name='PM Analyst'"
        app_match = re.search(r"application_name='([^']+)'", label)
        user_match = re.search(r"user_name='([^']+)'", label)
        measure_match = re.search(r"sum\(([^)]+)\)", label)
        
        application_name = app_match.group(1) if app_match else 'Unknown'
        user_name = user_match.group(1) if user_match else 'Unknown'
        measure_type = measure_match.group(1) if measure_match else 'unknown'
        
        # Process each data point in the timeseries
        for timestamp_ms, value in data_points:
            if value > 0:  # Only include non-zero values
                # Convert timestamp from milliseconds to datetime
                timestamp_sec = timestamp_ms / 1000
                dt = datetime.fromtimestamp(timestamp_sec)
                hour_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                
                # Data is already in MB
                bandwidth_mb = round(value, 3)
                
                hourly_records.append({
                    'hour': hour_str,
                    'application': application_name,
                    'user_name': user_name,
                    'measure_type': measure_type,
                    'bandwidth_mb': bandwidth_mb
                })
    
    # Sort by hour, then application, then user
    hourly_records.sort(key=lambda x: (x['hour'], x['application'], x['user_name'], x['measure_type']))
    
    return hourly_records

def save_hourly_csv(hourly_records, filename):
    """Save hourly timeseries data to CSV in the format: hour,application,user_name,measure_type,bandwidth_mb"""
    if not hourly_records:
        print("No hourly records to save")
        return
    
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['hour', 'application', 'user_name', 'measure_type', 'bandwidth_mb']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(hourly_records)
    
    print(f"Created {filename} with {len(hourly_records)} hourly records")

def create_pivot_summary(hourly_records, filename):
    """Create a pivot table summary by application and user from hourly records"""
    if not hourly_records:
        print("No data to create pivot summary")
        return
    
    # Aggregate data by application and user
    app_user_data = defaultdict(float)
    applications = set()
    users = set()
    
    for record in hourly_records:
        app = record['application']
        user = record['user_name']
        bandwidth = record['bandwidth_mb']
        
        applications.add(app)
        users.add(user)
        app_user_data[(app, user)] += bandwidth
    
    # Create pivot table
    pivot_rows = []
    for app in sorted(applications):
        row_data = {'application': app}
        app_total = 0
        
        for user in sorted(users):
            user_display = user if user else "Unknown"
            bandwidth = app_user_data.get((app, user), 0)
            row_data[f"{user_display}_mb"] = round(bandwidth, 3) if bandwidth > 0 else 0
            app_total += bandwidth
        
        row_data['total_mb'] = round(app_total, 3)
        pivot_rows.append(row_data)
    
    # Sort by total bandwidth descending
    pivot_rows.sort(key=lambda x: x['total_mb'], reverse=True)
    
    # Write to CSV
    if pivot_rows:
        fieldnames = ['application']
        for user in sorted(users):
            user_display = user if user else "Unknown"
            fieldnames.append(f"{user_display}_mb")
        fieldnames.append('total_mb')
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(pivot_rows)
        
        print(f"Created {filename} with {len(pivot_rows)} applications")


if __name__ == "__main__":
    main()
