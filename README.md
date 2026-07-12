# Homelab Telemetry Dashboard

A full-stack telemetry pipeline that collects live metrics from my self-hosted homelab infrastructure and displays them on a web dashboard — with a planned hardware display (LCD/LED panel) as a secondary output.

Built as a dual-purpose project: a genuinely useful monitoring tool for my own systems, and a hands-on way to develop end-to-end software engineering skills across embedded systems, cloud infrastructure, and web development.

---

## Architecture

```
Proxmox VE API  ──┐
                   ├──► Python Collector ──► AWS DynamoDB ──► FastAPI Backend ──► React Frontend
lm-sensors HTTP ──┘                     └──► AWS S3 (raw archive)
```

- **Collector** — Python container running on a 5-minute schedule, pulling metrics from two sources: the Proxmox REST API (CPU, memory, disk, uptime, load average) and a local HTTP endpoint serving lm-sensors hardware data (CPU package temp, NVMe temps, network adapter temp). Pushes snapshots to DynamoDB for live querying and S3 for long-term archival. Errors reported via Home Assistant webhook notifications.
- **Storage** — DynamoDB for fast, queryable recent data (24-hour TTL), S3 for raw JSON archival organized by node/year/month/day
- **Backend** — FastAPI server exposing a REST API with three endpoints: current node status, historical metrics with time range filtering, and node health checks
- **Frontend** — React dashboard with live-updating cards and mini graphs, served via Nginx and accessible at [capital-labs.dev](https://capital-labs.dev)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Metrics collection | Python, Proxmox REST API, lm-sensors |
| Host automation | systemd timers and services |
| Cloud storage | AWS DynamoDB (with TTL), AWS S3 |
| Backend | FastAPI, uvicorn |
| Frontend | React, Tailwind CSS, Recharts |
| Infrastructure | Proxmox VE, Portainer, Nginx Proxy Manager, Cloudflare |
| Containerization | Docker, Docker Hub |

---

## Data Sources

Currently collecting from:
- **Proxmox host (`capital`)** — CPU usage, memory used/total, disk usage, swap, load average, uptime
- **Hardware sensors** — CPU package temperature, NVMe drive temperatures, network adapter temperature

Planned:
- ESP32 room sensors (temperature, humidity) via ESPHome
- Unraid NAS API metrics

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/nodes/{node}/status` | Latest snapshot for a node |
| GET | `/nodes/{node}/metrics?hours=24` | Historical snapshots over a time range |
| GET | `/nodes/{node}/health` | Node health check based on last seen timestamp |

---

## Project Structure

```
homelab-telemetry/
├── collector/
│   ├── collector.py        # Metrics collector — fetches, merges, and pushes snapshots
│   ├── Dockerfile
│   └── requirements.txt
├── backend/
│   ├── main.py             # FastAPI backend with status, metrics, and health endpoints
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx         # Dashboard components and data fetching
│   │   └── api/
│   │       └── client.js   # Centralized API client
│   ├── Dockerfile
│   └── package.json
└── README.md
```

---

## Running Locally

### Collector

#### Prerequisites
- Python 3.x
- AWS credentials with DynamoDB and S3 write access
- Proxmox API token with PVEAuditor role

#### Install dependencies
```bash
pip install requests boto3
```

#### Set environment variables
```powershell
$env:PROXMOX_TOKEN_ID="collector@pve!your-token-name"
$env:PROXMOX_TOKEN_SECRET="your-token-secret"
$env:AWS_ACCESS_KEY_ID="your-access-key"
$env:AWS_SECRET_ACCESS_KEY="your-secret-key"
```

#### Run
```bash
python collector.py
```

### Backend

#### Install dependencies
```bash
pip install fastapi uvicorn boto3
```

#### Run
```bash
uvicorn main:app --reload
```

API available at `http://localhost:8000` — interactive docs at `http://localhost:8000/docs`

### Frontend

#### Install dependencies
```bash
npm install
```

#### Set environment variables
Create a `.env` file in the `frontend/` folder:
```
VITE_API_BASE_URL=http://localhost:8000
```

#### Run
```bash
npm run dev
```

---

## Infrastructure Notes

**Temperature collection** — temperature data is not available through the Proxmox API. Instead, a lightweight pipeline runs directly on the Proxmox host:

1. A systemd timer runs `sensors -j` every 30 seconds and writes output to `/run/pve-metrics/temperature.json`
2. A Python HTTP server serves that directory on port 8765
3. The collector fetches it remotely via a standard HTTP request

This keeps elevated (root) access isolated to the systemd timer and off the network-facing component.

**DynamoDB TTL** — items are automatically deleted after 24 hours using DynamoDB's built-in TTL feature, keeping storage costs minimal. S3 is used for long-term archival.

**Deployment** — all three services run as Docker containers managed by Portainer on a Proxmox LXC. Images are published to Docker Hub under `budhvinhewage/`.

---

## Roadmap

- [x] Proxmox API metrics collection
- [x] Hardware temperature collection via lm-sensors
- [x] AWS DynamoDB storage with TTL
- [x] AWS S3 archival
- [x] Containerize collector in Portainer
- [x] FastAPI backend with status, metrics, and health endpoints
- [x] React frontend with live-updating cards and graphs
- [x] Deployed at capital-labs.dev via Nginx Proxy Manager and Cloudflare
- [ ] ESP32 room sensor integration via ESPHome
- [ ] Unraid NAS metrics
- [ ] Hardware LCD/LED display output
- [ ] Mobile app