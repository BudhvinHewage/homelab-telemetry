import requests
import os
import json
import boto3
from datetime import datetime, timezone

PROXMOX_HOST = "https://192.168.0.15:8006"
TOKEN_ID = os.environ.get("PROXMOX_TOKEN_ID")
TOKEN_SECRET = os.environ.get("PROXMOX_TOKEN_SECRET")

headers = {
    "Authorization": f"PVEAPIToken={TOKEN_ID}={TOKEN_SECRET}"
}

verify = "/etc/pve/pve-root-ca.pem" if os.path.exists("/etc/pve/pve-root-ca.pem") else False

# Proxmox API metrics
response = requests.get(
    f"{PROXMOX_HOST}/api2/json/nodes/capital/status",
    headers=headers,
    verify=verify
)

data = response.json()['data']

metrics = {
    'cpu': round(data['cpu'] * 100, 2),
    'memory_used': round(data['memory']['used'] / (1024 ** 3), 2),
    'memory_total': round(data['memory']['total'] / (1024 ** 3), 2),
    'uptime': data['uptime'],
    'rootfs_used': round(data['rootfs']['used'] / (1024 ** 3), 2),
    'swap_used': round(data['swap']['used'] / (1024 ** 3), 2),
    'loadaverage': float(data['loadavg'][0]),
}

# Temperature metrics
temp_response = requests.get("http://192.168.0.15:8765/temperature.json")
temperatures = temp_response.json()

# Combined snapshot
combined = {**metrics, **temperatures}

snapshot = {
    'node': 'capital',
    'timestamp': datetime.now(timezone.utc).isoformat(),
    **combined
}

# Push to DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('homelab-metrics')
table.put_item(Item=snapshot)

print(snapshot)