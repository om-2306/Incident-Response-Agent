#!/usr/bin/env python3
"""
Seed script to populate Hindsight Episodic Memory with 5 realistic production incidents.
Run this script before launching the Streamlit app.
"""

import sys
import os
import time
from memory import HindsightMemory

# Ensure UTF-8 encoding for stdout on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

SYNTHETIC_INCIDENTS = [
    {
        "error": "Error 503: Database connection pool timeout on auth-service",
        "root_cause": "Memory leak in auth-service v2.1 during high traffic.",
        "resolution": "Restarted pod, increased max_connections pool limit to 150 in deployment.yaml.",
        "service": "auth-service",
        "severity": "critical",
        "tags": ["database", "auth-service", "503", "connection-pool"]
    },
    {
        "error": "Redis Cache Eviction Storm: OOM killed on redis-master-0",
        "root_cause": "A rogue cron job was writing unbounded telemetry data to Redis.",
        "resolution": "Killed cron job telemetry-dump, set maxmemory-policy allkeys-lru in redis.conf.",
        "service": "redis-cache",
        "severity": "high",
        "tags": ["redis", "oom", "eviction", "telemetry"]
    },
    {
        "error": "Kafka Consumer Lag Critical: payment-processor-group exceeding 10k messages",
        "root_cause": "Downstream PostgreSQL DB locked up due to a missing index on the transactions table.",
        "resolution": "Added index CREATE INDEX idx_txn_created_at ON transactions(created_at);, restarted consumer pods.",
        "service": "payment-processor",
        "severity": "critical",
        "tags": ["kafka", "postgres", "index", "consumer-lag"]
    },
    {
        "error": "AWS ALB 502 Bad Gateway: Target group health checks failing for api-gateway",
        "root_cause": "SSL certificate expired on the internal microservice, causing health check timeouts.",
        "resolution": "Renewed cert via cert-manager, updated secret api-gateway-tls.",
        "service": "api-gateway",
        "severity": "high",
        "tags": ["aws-alb", "502", "ssl-certificate", "api-gateway"]
    },
    {
        "error": "Elasticsearch Cluster Red: Unassigned shards on node es-data-03",
        "root_cause": "Disk watermark exceeded (90% full) on es-data-03 due to unmapped log indices.",
        "resolution": "Deleted old indices logs-2023.*, increased disk size, triggered shard reallocation.",
        "service": "elasticsearch",
        "severity": "critical",
        "tags": ["elasticsearch", "cluster-red", "shards", "disk-watermark"]
    }
]

def seed_database():
    print("=" * 65)
    print("HINDSIGHT EPISODIC MEMORY SEEDER (HackwithHyderabad 3.0)")
    print("=" * 65)
    
    mem = HindsightMemory()
    status_str = "Hindsight Cloud API Live" if mem.is_hindsight_live() else "Local Resilient Memory Store"
    print(f"Connection Status: {status_str}")
    print(f"Target Memory Bank: {mem.bank_id}")
    print("-" * 65)
    
    seeded_count = 0
    for i, inc in enumerate(SYNTHETIC_INCIDENTS, start=1):
        print(f"\n[Incident {i}/5] Seeding: {inc['error'][:50]}...")
        result = mem.save_incident(
            error_text=inc["error"],
            root_cause=inc["root_cause"],
            resolution=inc["resolution"],
            service=inc["service"],
            severity=inc["severity"],
            tags=inc["tags"]
        )
        print(f"   -> Service: {inc['service']} | Severity: {inc['severity']}")
        saved_status = "Hindsight Cloud + Local" if result['hindsight_saved'] else "Local Episodic Memory"
        print(f"   -> Saved Status: {saved_status}")
        seeded_count += 1
        time.sleep(0.1)
        
    print("\n" + "=" * 65)
    print(f"Successfully seeded {seeded_count} production incidents into Hindsight Memory!")
    print(f"Total Stored Episodic Memories: {mem.get_memory_count()}")
    print("=" * 65)

if __name__ == "__main__":
    seed_database()
