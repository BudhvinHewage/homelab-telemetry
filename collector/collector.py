"""
Homelab Telemetry Collector

Collects system metrics from the Proxmox host (capital) and hardware
temperature sensors, then pushes the combined snapshot to AWS DynamoDB
(for querying) and S3 (for long-term archival). Runs continuously on a
5-minute interval. Errors are reported via a Home Assistant webhook.
"""

import requests
import os
import json
import boto3
import time
import urllib3

from datetime import datetime, timezone
from decimal import Decimal

# --- Configuration ---

PROXMOX_HOST = "https://192.168.0.15:8006"
TEMPERATURE_ENDPOINT = "http://192.168.0.15:8765/temperature.json"
HOME_ASSISTANT_WEBHOOK_URL = "https://homeassistant.capital-labs.dev/api/webhook/-bx5tofcNJevp2m_KnWrNrlu9"

TOKEN_ID = os.environ.get("PROXMOX_TOKEN_ID")
TOKEN_SECRET = os.environ.get("PROXMOX_TOKEN_SECRET")

HEADERS = {
    "Authorization": f"PVEAPIToken={TOKEN_ID}={TOKEN_SECRET}"
}

COLLECTION_INTERVAL_SECONDS_DB = 5
COLLECTION_INTERVAL_SECONDS_S3 = 300

# Proxmox uses a self-signed certificate on the local network.
# Verification is disabled since this traffic never leaves the LAN.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Error count tracker to avoid spamming Home Assistant with repeated errors.
retreival_error_count_Capital = 0
transmission_error_count_DynamoDB = 0
transmission_error_count_S3 = 0

# Error time threshold to avoid spamming Home Assistant with repeated errors.
ERROR_NOTIFICATION_THRESHOLD_SECONDS_RETRIEVAL = 300
ERROR_NOTIFICATION_THRESHOLD_SECONDS_TRANSMISSION_DB = 300
ERROR_NOTIFICATION_THRESHOLD_SECONDS_TRANSMISSION_S3 = 300

# --- Data Collection ---

def fetch_capital_metrics():
    """Fetch system and temperature metrics for the 'capital' node."""
    response = requests.get(
        f"{PROXMOX_HOST}/api2/json/nodes/capital/status",
        headers=HEADERS,
        verify=False,
        timeout=10
    )
    data = response.json()['data']

    capital_metrics = {
        'cpu': round(data['cpu'] * 100, 2),
        'memory_used': round(data['memory']['used'] / (1024 ** 3), 2),
        'memory_total': round(data['memory']['total'] / (1024 ** 3), 2),
        'uptime': data['uptime'],
        'rootfs_used': round(data['rootfs']['used'] / (1024 ** 3), 2),
        'swap_used': round(data['swap']['used'] / (1024 ** 3), 2),
        'loadaverage': float(data['loadavg'][0]),
    }

    temp_response = requests.get(TEMPERATURE_ENDPOINT, timeout=10)
    temperatures = temp_response.json()

    combined = {**capital_metrics, **temperatures}

    return {
        'node': 'capital',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'ttl': int(time.time())+(24 * 60 * 60),
        **combined
    }


# --- Helpers ---

def to_decimal(value):
    """DynamoDB requires Decimal instead of float for numeric types."""
    if isinstance(value, float):
        return Decimal(str(value))
    return value


# --- Storage ---

def push_to_dynamodb(snapshot):
    """Write a snapshot to DynamoDB for fast, recent-data queries."""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('homelab-metrics')
    table.put_item(Item=snapshot)


def push_to_s3(snapshot):
    """Archive a snapshot to S3, organized by node/year/month/day."""
    s3 = boto3.client('s3', region_name='us-east-1')

    ts = datetime.fromisoformat(snapshot['timestamp'])
    key = f"capital/{ts.year}/{ts.month:02d}/{ts.day:02d}/{ts.strftime('%H-%M-%S')}.json"

    s3.put_object(
        Bucket='budhvin-diagnostics-capital-proxmox',
        Key=key,
        Body=json.dumps(snapshot, default=str),
        ContentType='application/json'
    )


# --- Alerting ---

def notify_error(message):
    """Send an error notification to Home Assistant via webhook."""
    try:
        requests.post(HOME_ASSISTANT_WEBHOOK_URL, json={"message": message})
    except Exception as e:
        print(f"Failed to send HA notification: {e}")


# --- Main Loop ---

def main():
    last_s3_push_time = 0
    while True:
        print(f"Collecting metrics at {datetime.now(timezone.utc).isoformat()}...")
        try:
            print("Fetching metrics from capital...")
            snapshot = fetch_capital_metrics()
            print(f"Snapshot successfully collected: {snapshot['timestamp']}", flush=True)
        except Exception as e:
            retreival_error_count_Capital += 1
            if retrieval_error_count_Capital >= 5 and (time.time() - last_s3_push_time) < ERROR_NOTIFICATION_THRESHOLD_SECONDS_RETRIEVAL:
                notify_error(f"Failed to fetch metrics from capital: {e}")
                retreival_error_count_Capital = 0  # Reset after notification
            continue

        try:
            print("Pushing snapshot to DynamoDB...")
            snapshot_for_db = {k: to_decimal(v) for k, v in snapshot.items()}
            push_to_dynamodb(snapshot_for_db)
            print("Snapshot successfully pushed to DynamoDB.", flush=True)
        except Exception as e:
            transmission_error_count_DynamoDB += 1
            if transmission_error_count_DynamoDB >= 5 and (time.time() - last_s3_push_time) < ERROR_NOTIFICATION_THRESHOLD_SECONDS_TRANSMISSION_DB:
                notify_error(f"Failed to push to DynamoDB: {e}")
                transmission_error_count_DynamoDB = 0  # Reset after notification

        if (time.time() - last_s3_push_time) >= COLLECTION_INTERVAL_SECONDS_S3:
            try:
                print("Pushing snapshot to S3...")
                push_to_s3(snapshot)
                print("Snapshot successfully pushed to S3.", flush=True)
                last_s3_push_time = time.time()
            except Exception as e:
                transmission_error_count_S3 += 1
                if transmission_error_count_S3 >= 5 and (time.time() - last_s3_push_time) < ERROR_NOTIFICATION_THRESHOLD_SECONDS_TRANSMISSION_S3:
                    notify_error(f"Failed to push to S3: {e}")
                    transmission_error_count_S3 = 0  # Reset after notification

        time.sleep(COLLECTION_INTERVAL_SECONDS_DB)


if __name__ == "__main__":
    main()