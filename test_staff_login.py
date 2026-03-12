import requests, re

s = requests.Session()
r = s.get('http://localhost:8000/staff/login/')
csrf = s.cookies.get('csrftoken', '')
print('Got csrf:', bool(csrf), 'Status:', r.status_code)

res = s.post('http://localhost:8000/staff/login/', 
    data={'username':'admin','password':'admin123','csrfmiddlewaretoken':csrf},
    headers={'Referer':'http://localhost:8000/staff/login/'})

print('Status:', res.status_code, 'URL:', res.url)
# Find error block
m = re.search(r'class="bg-red[^"]*"[^>]*>\s*(.*?)\s*</div>', res.text, re.DOTALL)
print('Error msg:', m.group(1).strip()[:200] if m else 'NO ERROR MSG')
