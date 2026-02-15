import asyncio
import os
import json
from datetime import datetime

# Path relative to script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_FILE = os.path.join(os.path.dirname(BASE_DIR), "memory", "heartbeat-state.json")

async def run_audit():
    print(f"[{datetime.now()}] Starting Isomorphism Audit...")
    
    # 1. Check spec vs implementation
    spec_path = os.path.join(BASE_DIR, "docs", "specs", "ISOMORPHISM_SPEC.md")
    impl_path = os.path.join(BASE_DIR, "isomorphism.py")
    
    with open(spec_path, 'r') as f:
        spec = f.read()
    with open(impl_path, 'r') as f:
        impl = f.read()
        
    print("- Verifying IsomorphismEngine stubs...")
    checks = {
        "VectorParams(size=3072": "text-embedding-3-large size match",
        "score_threshold=threshold": "Candidate discovery threshold usage",
        "calculate_ged": "Graph Edit Distance stub exists",
        "propose_mapping": "Mapping table proposal stub exists"
    }
    
    results = []
    for key, desc in checks.items():
        if key in impl:
            results.append(f"  [PASS] {desc}")
        else:
            results.append(f"  [FAIL] {desc}")
            
    # 2. Update state
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        state["lastChecks"]["isomorphism_audit"] = int(datetime.now().timestamp())
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"Error updating state: {e}")

    print("\n".join(results))
    print(f"[{datetime.now()}] Audit Complete.")

if __name__ == "__main__":
    asyncio.run(run_audit())
