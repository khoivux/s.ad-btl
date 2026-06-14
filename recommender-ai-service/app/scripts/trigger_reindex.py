import sys
import requests

def main():
    # Default is the internal container URL (useful when running inside docker exec)
    url = "http://recommender-ai-service:8000/api/index-kb/"
    if len(sys.argv) > 1:
        url = sys.argv[1]
    
    print(f"Triggering Vector DB re-indexing at: {url}...")
    try:
        # Long timeout because indexing uses a sleep duration to avoid rate limits
        r = requests.post(url, timeout=300)
        if r.status_code == 200:
            print("SUCCESS:")
            print(r.json().get('status', 'Completed.'))
        else:
            print(f"FAILED (HTTP {r.status_code}):")
            try:
                print(r.json().get('error', r.text))
            except:
                print(r.text)
    except Exception as e:
        print(f"Connection failed: {e}")
        # Try fallback via API Gateway on localhost (useful when running on the host machine)
        fallback_url = "http://localhost:8000/api/recommender/index-kb/"
        print(f"Attempting fallback to localhost API Gateway: {fallback_url}...")
        try:
            r = requests.post(fallback_url, timeout=300)
            if r.status_code == 200:
                print("SUCCESS (via localhost):")
                print(r.json().get('status', 'Completed.'))
            else:
                print(f"FAILED (HTTP {r.status_code}):")
                try:
                    print(r.json().get('error', r.text))
                except:
                    print(r.text)
        except Exception as ex:
            print(f"Fallback connection failed: {ex}")

if __name__ == "__main__":
    main()
