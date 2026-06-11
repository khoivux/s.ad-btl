import requests

url = "http://localhost:8010/chat/consultant/1/"
headers = {"Content-Type": "application/json"}

queries = [
    "Silver được giảm bao nhiêu % và ship hỏa tốc bao nhiêu tiền?",
    "Mình muốn tìm mỹ phẩm cho da dầu",
    "Bạn có khỏe không?"
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
