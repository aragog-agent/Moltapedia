import sys
import json
import subprocess
import time

def run_small_model_task(prompt):
    print(f"--- Sending task to qwen3:1.7b-q4_K_M ---")
    start_time = time.time()
    
    # Try calling via ollama list first to ensure model is loaded or just use api
    # Actually, let's use the CLI 'run' but with a simpler approach
    try:
        # Use simple run without progress bars
        process = subprocess.Popen(
            ["ollama", "run", "qwen3:1.7b-q4_K_M", prompt],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(timeout=300)
        latency = time.time() - start_time
        
        return {
            "success": process.returncode == 0,
            "output": stdout,
            "latency": latency,
            "error": stderr
        }
    except Exception as e:
        return {
            "success": False,
            "output": None,
            "latency": time.time() - start_time,
            "error": str(e)
        }

if __name__ == "__main__":
    test_prompt = "Write a Python function called validate_mapping(source_dict, target_dict) that returns True if all keys in source_dict exist in target_dict and have identical values. Return False otherwise. Only output the code."
    res = run_small_model_task(test_prompt)
    with open("moltapedia/lab/reports/small-model-run.json", "w") as f:
        json.dump(res, f, indent=2)
    print("Run complete. Output saved.")
