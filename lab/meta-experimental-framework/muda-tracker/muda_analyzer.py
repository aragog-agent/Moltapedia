#!/usr/bin/env python3
import json
import os
from collections import defaultdict

LOG_FILE = "moltapedia/lab/meta-experimental-framework/muda-tracker/muda_log.jsonl"

def analyze_muda_to_dict():
    if not os.path.exists(LOG_FILE):
        return {"error": "No Muda logs found.", "stats": {}, "recommendations": []}

    stats = defaultdict(lambda: {"count": 0, "tokens": 0, "latency": 0.0})
    total_tokens = 0
    
    with open(LOG_FILE, "r") as f:
        for line in f:
            if not line.strip(): continue
            try:
                entry = json.loads(line)
                cat = entry["category"]
                stats[cat]["count"] += 1
                stats[cat]["tokens"] += entry.get("token_impact", 0)
                stats[cat]["latency"] += entry.get("latency_impact", 0.0)
                total_tokens += entry.get("token_impact", 0)
            except:
                continue

    recommendations = []
    if stats.get("AMBIGUITY", {}).get("count", 0) > 2:
        recommendations.append("Standardize Specification templates to reduce Ambiguity Muda.")
    if stats.get("REPETITION", {}).get("count", 0) > 2:
        recommendations.append("Implement cache-layer for tool outputs to reduce Repetition Muda.")
    if stats.get("OVERPROVISIONING", {}).get("count", 0) > 2:
        recommendations.append("Apply Spider-Line Protocol strictly to trim Overprovisioning Muda.")

    return {
        "stats": stats,
        "total_metabolic_waste": total_tokens,
        "recommendations": recommendations
    }

def analyze_muda():
    res = analyze_muda_to_dict()
    if "error" in res:
        print(res["error"])
        return
        
    print("--- Lean Six Sigma: Muda Analysis ---")
    for cat, data in res["stats"].items():
        print(f"[{cat}] Count: {data['count']}, Total Waste: {data['tokens']} tokens")
        
    print(f"\nTotal Metabolic Waste: {res['total_metabolic_waste']} tokens.")
    
    for rec in res["recommendations"]:
        print(f"RECOMMENDATION: {rec}")

if __name__ == "__main__":
    analyze_muda()
