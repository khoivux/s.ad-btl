import sys
import requests

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

url = "http://127.0.0.1:8000/chat/consultant/3/"
headers = {"Content-Type": "application/json"}
q = "dựa vào lịch sử mua sắm của tôi cho tôi biết tôi thích gì"

print(f"Querying: {q}")
try:
    r = requests.post(url, json={"message": q}, headers=headers, stream=True)
    if r.status_code == 200:
        for chunk in r.iter_content(chunk_size=1024, decode_unicode=True):
            if chunk:
                print(chunk, end="", flush=True)
        print()
    else:
        print(f"Error {r.status_code}: {r.text}")
except Exception as e:
    print(f"Connection failed: {e}")
