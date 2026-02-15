#!/usr/bin/env python3
import json
import time
import sys
import os

LOG_FILE = "moltapedia/lab/meta-experimental-framework/muda-tracker/muda_log.jsonl"

def log_muda(category, description, token_impact=0, latency_impact=0.0):
    """
    Categories: 
    - REPETITION: Redundant tool calls or output.
    - OVERPROVISIONING: Too much context provided.
    - AMBIGUITY: Clarification needed due to poor spec.
    - WAITING: Latency without computation.
    """
    entry = {
        "timestamp": int(time.time()),
        "category": category,
        "description": description,
        "token_impact": token_impact,
        "latency_impact": latency_impact
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: muda-log <category> <description> [tokens] [latency]")
        sys.exit(1)
    
    cat = sys.argv[1]
    desc = sys.argv[2]
    tokens = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    latency = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
    
    log_muda(cat, desc, tokens, latency)
    print(f"Logged {cat}: {desc}")
