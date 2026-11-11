# Add Profile Photo + English Signature to Sigma - Mahmoud Emad
import pathlib
p = pathlib.Path("index.html")
html = p.read_text(encoding="utf-8")
# Remove old profile if exists
import re
html = re.sub(r'<div id="sigma-profile".*?</div>', '', html, flags=re.DOTALL)
profile = '''<div id="sigma-profile" style="display:flex;align-items:center;gap:12px;padding:14px 16px 8px;background:#0f172a;color:#fff;border-radius:0 0 16px 16px"><img src="sigma_profile.jpg" alt="Mahmoud Emad" style="width:72px;height:72px;object-fit:cover;border-radius:50%;border:2px solid #fbbf24"><div><div style="font-size:15px;font-weight:700;color:#fbbf24">Signature Prediction and Forecast: Sigma</div><div style="font-size:18px;font-weight:800">Mahmoud Emad</div><div style="font-size:12px;opacity:.8">V23 - Full World 84449 - 239 Matches - 35 Days</div></div></div>'''
if "<body" in html:
    html = html.replace("<body", profile + "<body", 1) if "sigma-profile" not in html else html
    # Better: insert after <body ...>
    import re as _re
    html = _re.sub(r'(<body[^>]*>)', r'\1' + profile, html, count=1)
else:
    html = profile + html
p.write_text(html, encoding="utf-8")
print("Profile added - 50% size - English Signature")
