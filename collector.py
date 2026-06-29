# Importing necessary libraries and modules
import requests
import os
import json
import boto3
import time

from datetime import datetime, timezone
from decimal import Decimal


# Declaring variables to be used in the program
PROXMOX_HOST = "https://192.168.0.15:8006"
TOKEN_ID = os.environ.get("PROXMOX_TOKEN_ID")
TOKEN_SECRET = os.environ.get("PROXMOX_TOKEN_SECRET")
snapshot = {}
home_assistant_trigger_url = "https://homeassistant.capital-labs.dev/api/webhook/-bx5tofcNJevp2m_KnWrNrlu9"

headers = {
    "Authorization": f"PVEAPIToken={TOKEN_ID}={TOKEN_SECRET}"
}

verify = "/etc/pve/pve-root-ca.pem" if os.path.exists("/etc/pve/pve-root-ca.pem") else False

def fetch_capital_metrics():
    response = requests.get(
        f"{PROXMOX_HOST}/api2/json/nodes/capital/status",
        headers=headers,
        verify=verify
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

    temp_response = requests.get("http://192.168.0.15:8765/temperature.json")
    temperatures = temp_response.json()

    combined = {**capital_metrics, **temperatures}

    snapshot_capital = {
        'node': 'capital',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        **combined
    }

    return snapshot_capital


def to_decimal(obj):
    if isinstance(obj, float):
        return Decimal(str(obj))
    return obj

def push_to_dynamodb(snapshot):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('homelab-metrics')
    table.put_item(Item=snapshot)

def push_to_s3(snapshot):
    s3 = boto3.client('s3', region_name='us-east-1')

    ts = datetime.fromisoformat(snapshot['timestamp'])
    key = f"capital/{ts.year}/{ts.month:02d}/{ts.day:02d}/{ts.strftime('%H-%M-%S')}.json"

    s3.put_object(
        Bucket='budhvin-diagnostics-capital-proxmox',
        Key=key,
        Body=json.dumps(snapshot, default=str),
        ContentType='application/json'
    )

def notify_error(message):
    try:
        requests.post(home_assistant_trigger_url, json={"message": message})
    except Exception as e:
        print(f"Failed to send HA notification: {e}")

def main():
    while True:
        try:
            snapshot = fetch_capital_metrics()
        except Exception as e:
            notify_error(f"Failed to fetch metrics from capital: {e}")
            time.sleep(300)
            continue

        try:
            snapshot_modified = {k: to_decimal(v) for k, v in snapshot.items()}
            push_to_dynamodb(snapshot_modified)
        except Exception as e:
            notify_error(f"Failed to push to DynamoDB: {e}")

        try:
            push_to_s3(snapshot)
        except Exception as e:
            notify_error(f"Failed to push to S3: {e}")

        notify_error("It works")

        time.sleep(300)

if __name__ == "__main__":
    main()