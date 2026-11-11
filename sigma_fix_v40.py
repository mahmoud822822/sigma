import base64, pathlib, re
p=pathlib.Path('index.html')
h=p.read_text()
# 1. photo
try:
  b=base64.b64encode(open('my_photo.jpg','rb').read()).decode()
  img=f'<img src="data:image/jpeg;base64,{b}" style="width:52px;height:52px;border-radius:50%;border:2px solid #FFC107;object-fit:cover">'
except:
  img='<div style="width:52px;height:52px;border-radius:50%;background:#FFC107;color:#111;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:24px">M</div>'
# 2. remove old plain signature line to avoid duplicate
h=re.sub(r'Signature Prediction and Forecast: Sigma -.*?Mahmoud Emad', '', h, count=1)
# 3. header + top nav + bottom nav
hdr=f'<div style="display:flex;gap:10px;align-items:center;padding:10px;background:#0f172a;border-bottom:2px solid #FFC107;position:sticky;top:0;z-index:99">{img}<div><div style="color:#FFC107;font-size:10px;font-weight:700">Signature Prediction and Forecast: Sigma</div><div style="font-size:17px;font-weight:800;color:#fff">Mahmoud Emad</div></div><span style="margin-left:auto;background:#FFC107;color:#111;padding:4px 8px;border-radius:999px;font-size:11px;font-weight:800">V40</span></div><div style="display:flex;gap:6px;overflow-x:auto;padding:8px;background:#020617;position:sticky;top:76px;z-index:98"><a href="#today" style="background:#16A34A;color:#fff;padding:8px 14px;border-radius:999px;text-decoration:none;font-size:13px;font-weight:700">Today</a><a href="#future" style="background:#1e293b;color:#fff;padding:8px 14px;border-radius:999px;text-decoration:none;font-size:13px">Future</a><a href="#lab" style="background:#1e293b;color:#fff;padding:8px 14px;border-radius:999px;text-decoration:none;font-size:13px">Lab</a><a href="#value" style="background:#1e293b;color:#fff;padding:8px 14px;border-radius:999px;text-decoration:none;font-size:13px">Value</a><a href="#profile" style="background:#1e293b;color:#fff;padding:8px 14px;border-radius:999px;text-decoration:none;font-size:13px">My Sigma</a></div>'
if 'V40' not in h:
  h=h.replace('<body>', '<body>'+hdr, 1)
# 4. add IDs to sections + bottom nav
h=h.replace('Real History','<div id="today"></div>Real History',1)
h=h.replace('418 REAL','<div id="future"></div>418 REAL',1)
h=h.replace('AI Lab','<div id="lab"></div>AI Lab',1)
h=h.replace('Value -','<div id="value"></div>Value -',1)
h=h.replace('Golden Bets','<div id="profile"></div>Golden Bets',1)
bot='<div style="position:fixed;bottom:0;left:0;right:0;background:#0f172a;border-top:1px solid #FFC107;display:flex;justify-content:space-around;padding:10px;max-width:430px;margin:0 auto;z-index:99"><a href="#today" style="color:#FFC107;text-decoration:none;font-size:12px;font-weight:700">🏠 Home</a><a href="#future" style="color:#fff;text-decoration:none;font-size:12px">🔮 Future</a><a href="#lab" style="color:#fff;text-decoration:none;font-size:12px">🧪 Lab</a><a href="#value" style="color:#fff;text-decoration:none;font-size:12px">💰 Value</a><a href="#profile" style="color:#fff;text-decoration:none;font-size:12px">👤 Me</a></div>'
if 'position:fixed;bottom:0' not in h:
  h=h.replace('</body>', bot+'</body>')
# 5. shrink Orb
h=h.replace('width:150px;height:150px','width:110px;height:110px')
p.write_text(h)
print('V40 fixed - header + nav + IDs')
