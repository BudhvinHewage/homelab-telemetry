from fastapi import FastAPI
from decimal import Decimal
import boto3
from datetime import datetime, timezone, timedelta
from boto3.dynamodb.conditions import Key
from fastapi.middleware.cors import CORSMiddleware

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('homelab-metrics')

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def convert_decimals(obj):
    if isinstance(obj,dict):
        return {k:convert_decimals(v) for k,v in obj.items()}
    elif isinstance(obj,Decimal):
        return float(obj)
    return obj

@app.get("/nodes/{node}/status")
def get_status(node: str):
    response = table.query(
        KeyConditionExpression=Key('node').eq(node),
        ScanIndexForward=False,
        Limit=1)
    items = response['Items']
    if not items:
        return {"error": "no data found"}

    return convert_decimals(items[0])

@app.get("/nodes/{node}/metrics")
def get_metrics(node: str, hours: int = 24):
    end = datetime.now(timezone.utc).isoformat()
    start = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    response = table.query(
        KeyConditionExpression=Key('node').eq(node) & Key('timestamp').between(start,end))
    items = response['Items']
    if not items:
        return {"error": "no data found"}
    return [convert_decimals(item) for item in items]

@app.get("/nodes/{node}/health")
def get_health(node : str):
    response = table.query(
        KeyConditionExpression=Key('node').eq(node),
        ScanIndexForward=False,
        Limit=1)
    items = response['Items']
    if not items:
        return {"error": "no data found"}
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(items[0]['timestamp'])).total_seconds()
    return {
        "node": node,
        "last_seen": items[0]['timestamp'],
        "seconds_since_last_snapshot": age,
        "status": "healthy" if age < 600 else "stale"
    }