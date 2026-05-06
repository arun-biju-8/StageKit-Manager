import json
import urllib.request
import os

os.makedirs('stitch_html', exist_ok=True)
with open(r'C:\Users\musix\.gemini\antigravity\brain\c0ef7cf0-0ccb-45f6-bf68-947cf398b00a\.system_generated\steps\410\output.txt', encoding='utf-8') as f:
    d = json.load(f)

for s in d['screens']:
    title = s['title'].replace(' ', '_')
    url = s['htmlCode']['downloadUrl']
    try:
        html = urllib.request.urlopen(url).read().decode('utf-8')
        with open(f'stitch_html/{title}.html', 'w', encoding='utf-8') as out:
            out.write(html)
        print(f"Downloaded {title}.html")
    except Exception as e:
        print(f"Failed {title}: {e}")
