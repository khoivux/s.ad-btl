import os
import subprocess

print("Dumping recommender-ai-service docker logs...")
try:
    res = subprocess.run(
        ["docker", "compose", "logs", "--tail", "2000", "recommender-ai-service"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )
    logs = res.stdout
    start_idx = logs.find("--- [AI-DEBUG] FULL PROMPT SENT TO GEMINI ---")
    end_idx = logs.find("--- [AI-DEBUG] END FULL PROMPT ---")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    if start_idx != -1 and end_idx != -1:
        prompt_content = logs[start_idx:end_idx + len("--- [AI-DEBUG] END FULL PROMPT ---")]
        out_path = os.path.join(current_dir, "prompt_debug.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(prompt_content)
        print(f"Prompt successfully extracted to {out_path}")
    else:
        print("Could not find start/end markers in logs.")
        out_path = os.path.join(current_dir, "all_logs.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(logs)
        print(f"All logs written to {out_path}")
except Exception as e:
    print("Error:", e)
