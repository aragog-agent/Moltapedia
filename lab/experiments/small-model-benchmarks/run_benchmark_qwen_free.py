import sys
import json
import time
import subprocess

GATEWAY_URL = "http://localhost:18789/v1/chat/completions"
GATEWAY_TOKEN = "eee6376ff8702b73eb46630be41b6c0a6023028171e6679a9fe4bf2099717c44"

def run_qwen_free_task(prompt):
    print(f"--- Sending task to qwen-free (OpenRouter) ---")
    start_time = time.time()
    
    data = {
        "model": "qwen-free",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0
    }
    
    try:
        # Use curl via subprocess
        process = subprocess.Popen(
            [
                "curl", "-s", "-X", "POST", GATEWAY_URL,
                "-H", f"Authorization: Bearer {GATEWAY_TOKEN}",
                "-H", "Content-Type: application/json",
                "-d", json.dumps(data)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(timeout=300)
        latency = time.time() - start_time
        
        if process.returncode == 0:
            try:
                result = json.loads(stdout)
                if 'choices' in result:
                    output = result['choices'][0]['message']['content']
                    return {
                        "success": True,
                        "output": output,
                        "latency": latency,
                        "error": None
                    }
                else:
                    return {
                        "success": False,
                        "output": None,
                        "latency": latency,
                        "error": f"API Error (No choices): {stdout}"
                    }
            except Exception as e:
                return {
                    "success": False,
                    "output": None,
                    "latency": latency,
                    "error": f"JSON Parse Error: {str(e)}\nSTDOUT: {stdout}"
                }
        else:
            return {
                "success": False,
                "output": None,
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
    res = run_qwen_free_task(test_prompt)
    output_path = "moltapedia/lab/reports/small-model-run-qwen-free.json"
    with open(output_path, "w") as f:
        json.dump(res, f, indent=2)
    print(f"Run complete. Output saved to {output_path}")
