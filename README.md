# Flights Aggregation App with Redis Caching

This project computes aggregations (mean, max, std, etc.) on flight CSV data and caches results in Redis for faster subsequent queries. Logs are written both to console and a rotating log file with proper timezone handling (Europe/Brussels).

---

## Challenge: CSV Caching with Redis

This project demonstrates how to efficiently cache CSV data using Redis, exposing a simple API to query flight data.

## Project Structure

```
challenge-caching-csv-redis/
│
├─ app/
│  ├─ main.py           # FastAPI application entrypoint
│  ├─ cache.py          # Redis caching logic
│  └─ data/
│      └─ flights.csv   # Sample flight data
│
├─ logs/                # Log folder
├─ Dockerfile           # Dockerfile for the application
├─ docker-compose.yml   # Docker Compose for app + Redis
├─ requirements.txt     # Python dependencies
└─ .env                 # Environment variables (e.g., Redis URL)
```
## Table of Contents

- [Prerequisites](#prerequisites)  
- [Installing & Running Redis](#installing--running-redis)  
- [Running the App](#running-the-app)  
- [Example Logs](#example-logs)  
- [Performance Notes](#performance-notes)  

---

## Prerequisites

- Docker & Docker Compose installed
- Python 3.12+ (if running outside Docker)
- Flight CSV file located at `data/flights.csv`  (downloaded from: [click here](https://www.kaggle.com/datasets/usdot/flight-delays?select=flights.csv))

---

## Installing & Running Redis

**Option 1: Using Docker Compose (recommended)**

Redis is included in `docker-compose.yml`:
Running Redis locally:

```bash
docker compose up -d redis

```

**Option 2: Running Redis locally**

```bash
# Install Redis (Ubuntu)
sudo apt-get update
sudo apt-get install redis-server
```

```bash
# Start Redis

redis-server
```
Verify Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

## Running the App

**Option 1: Docker Compose (recommended)**

```bash
docker-compose build app  
docker-compose up app
```

Logs are streamed to console and also stored in:
```bash
logs/cache_history.log
```
**Option 2: Run Locally**
```bash
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
export TZ=Europe/Brussels

python main.py
```

## Example Logs

```pgsql
2025-08-21 12:45:46,679 [INFO] Computed 'max_CANCELLED_per_ORIGIN_AIRPORT' from CSV in 16040.89ms
2025-08-21 12:45:46,683 [INFO] Cached result for query 'max_CANCELLED_per_ORIGIN_AIRPORT' as HASH with TTL=900s
2025-08-21 12:45:46,763 [INFO] Cache HIT for query 'max_CANCELLED_per_ORIGIN_AIRPORT', field 'EWR' (elapsed=1.23ms, TTL=900s)
2025-08-21 12:45:46,764 [INFO] Cache MISS for query 'std_ARRIVAL_DELAY_per_AIRLINE' (checked in 0.26ms)
2025-08-21 12:46:02,043 [INFO] Computed 'std_ARRIVAL_DELAY_per_AIRLINE' from CSV in 15279.0ms
2025-08-21 12:46:02,045 [INFO] Cached result for query 'std_ARRIVAL_DELAY_per_AIRLINE' as HASH with TTL=900s
2025-08-21 12:46:02,123 [INFO] Cache HIT for query 'std_ARRIVAL_DELAY_per_AIRLINE', field 'UA' (elapsed=0.67ms, TTL=900s)
2025-08-21 12:46:41,041 [INFO] Connected to Redis at redis_cache:6379, db=0
2025-08-21 12:46:41,043 [INFO] Cache HIT for query 'mean_ARRIVAL_DELAY_per_AIRLINE' (elapsed=0.56ms, TTL=830s)
2025-08-21 12:46:41,044 [INFO] Cache HIT for query 'mean_ARRIVAL_DELAY_per_AIRLINE', field 'AA' (elapsed=0.46ms, TTL=830s)
2025-08-21 12:46:41,046 [INFO] Cache HIT for query 'max_CANCELLED_per_ORIGIN_AIRPORT' (elapsed=1.63ms, TTL=846s)
2025-08-21 12:46:41,047 [INFO] Cache HIT for query 'max_CANCELLED_per_ORIGIN_AIRPORT', field 'EWR' (elapsed=0.43ms, TTL=846s)
2025-08-21 12:46:41,048 [INFO] Cache HIT for query 'std_ARRIVAL_DELAY_per_AIRLINE' (elapsed=0.48ms, TTL=861s)
2025-08-21 12:46:41,048 [INFO] Cache HIT for query 'std_ARRIVAL_DELAY_per_AIRLINE', field 'UA' (elapsed=0.32ms, TTL=861s)
2025-08-21 12:46:41,049 [INFO] Invalidated cache for query 'mean_ARRIVAL_DELAY_per_AIRLINE'
2025-08-21 12:46:41,051 [INFO] Cleared 2 cached queries (prefix='cache:*')
```

*Cache MISS indicates CSV computation.

*Cache HIT indicates value retrieved from Redis.

*Second run activated invalidating and clearing full cache.

## Performance Notes
*First run: Reads CSV and computes aggregation → ~14.9s - 16s

*Second run: Retrieves aggregation from Redis → ~0.3ms - 1.6ms

*Cache TTL is configurable (default 15 minutes).
