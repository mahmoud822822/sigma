# Sigma Fast Link - Mahmoud Emad - Connect Sigma + Supabase Fast
import pathlib
print("Sigma Fast Link - Paste once, works on all devices")
url = input("Paste Supabase URL: ").strip()
key = input("Paste anon key: ").strip()
if "supabase.co" not in url or not url.startswith("https://"):
    print("URL wrong - must be https://....supabase.co")
    raise SystemExit
if len(key) < 20:
    print("Key too short")
    raise SystemExit
p = pathlib.Path("index.html")
if not p.exists():
    print("No index.html - Run V22 first")
    raise SystemExit
html = p.read_text(encoding="utf-8")
# Remove old fast link if exists
import re
html = re.sub(r'<script>localStorage\.setItem\("sigma_supa_url".*?</script>', '', html, flags=re.DOTALL)
inject = f'<script>localStorage.setItem("sigma_supa_url","{url}");localStorage.setItem("sigma_supa_key","{key}");</script>'
if "<body>" in html:
    html = html.replace("<body>", "<body>" + inject, 1)
else:
    html = inject + html
p.write_text(html, encoding="utf-8")
print("Linked OK - Open site, must show Shared: ON")
