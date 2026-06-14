import requests

url = "http://localhost:8010/chat/consultant/3/"
headers = {"Content-Type": "application/json"}

queries = [
    "xin chào",
    "gợi ý cho mình 2 cuốn sách hay và 1 món đồ gia dụng tiện ích xem sao"
]

for q in queries:
    print(f"\n========================================\nQuery: {q}\n========================================")
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
