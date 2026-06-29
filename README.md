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

- **Collector** — Python script running on a schedule, pulling metrics from two sources: the Proxmox REST API (CPU, memory, disk, uptime) and a local HTTP endpoint serving hardware sensor data (CPU package temp, NVMe temps, network adapter temp)
- **Storage** — snapshots written to DynamoDB for querying and S3 for long-term archival
- **Backend** — FastAPI server exposing a REST API for the frontend to query historical metrics
- **Frontend** — React dashboard hosted via Cloudflare on [capital-labs.dev](https://capital-labs.dev)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Metrics collection | Python, Proxmox REST API, lm-sensors |
| Host automation | systemd timers and services |
| Cloud storage | AWS DynamoDB, AWS S3 |
| Backend | FastAPI (Python) |
| Frontend | React |
| Infrastructure | Proxmox VE, Portainer, Nginx Proxy Manager, Cloudflare |
| Containerization | Docker |

---

## Data Sources

Currently collecting from:
- **Proxmox host (`capital`)** — CPU usage, memory, disk, swap, load average, uptime
- **Hardware sensors** — CPU package temperature, NVMe drive temperatures, network adapter temperature

Planned:
- ESP32 room sensors (temperature, humidity) via ESPHome
- Unraid NAS API metrics

---

## Project Structure

```
proxmox-collector/
├── collector.py        # Main metrics collector — fetches, merges, and pushes snapshots
├── README.md
└── .gitignore
```

---

## Running Locally

### Prerequisites
- Python 3.x
- AWS credentials configured with DynamoDB and S3 write access

### Install dependencies
```bash
pip install requests boto3
```

### Set environment variables
```powershell
$env:PROXMOX_TOKEN_ID="collector@pve!your-token-name"
$env:PROXMOX_TOKEN_SECRET="your-token-secret"
```

### Run
```bash
python collector.py
```

---

## Infrastructure Notes

Temperature data is not available through the Proxmox API. Instead, a lightweight pipeline runs directly on the Proxmox host:

1. A systemd timer runs `sensors -j` every 30 seconds and writes the output to `/run/pve-metrics/temperature.json`
2. A Python HTTP server serves that directory on port 8765
3. The collector fetches it remotely via a standard HTTP request

This keeps elevated (root) access isolated to the systemd timer and off the network-facing component.

---

## Roadmap

- [x] Proxmox API metrics collection
- [x] Hardware temperature collection via lm-sensors
- [x] AWS DynamoDB storage
- [ ] AWS S3 archival
- [ ] Containerize collector in Portainer
- [ ] FastAPI backend
- [ ] React frontend on capital-labs.dev
- [ ] ESP32 sensor integration
- [ ] Hardware LCD/LED display output
