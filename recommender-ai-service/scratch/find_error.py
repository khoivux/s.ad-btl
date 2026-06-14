import subprocess

print("Finding LSTM or Graph error in logs...")
try:
    res = subprocess.run(
        ["docker", "compose", "logs", "--tail", "2000", "recommender-ai-service"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )
    logs = res.stdout
    for line in logs.splitlines():
        if "Failed LSTM or Graph" in line:
            print("FOUND ERROR LOG:", line)
except Exception as e:
    print("Error:", e)
