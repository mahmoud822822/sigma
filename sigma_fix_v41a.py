import base64, pathlib, re
p=pathlib.Path('index.html'); h=p.read_text()
try:
  b=base64.b64encode(open('my_photo.jpg','rb').read()).decode()
  img=f'<img src="data:image/jpeg;base64,{b}" style="width:52px;height:52px;border-radius:50%;border:2px solid #FFC107;object-fit:cover">'
except:
  img='<div style="width:52px;height:52px;border-radius:50%;background:#FFC107;color:#111;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:24px">M</div>'
# شيل اي هيدر قديم
h=re.sub(r'<div style="display:flex;gap:10px;align-items:center;padding:10px;background:#0f172a.*?</div>', '', h, count=1, flags=re.DOTALL)
hdr=f'<div style="display:flex;gap:10px;align-items:center;padding:10px;background:#0f172a;border-bottom:2px solid #FFC107;position:sticky;top:0;z-index:99">{img}<div><div style="color:#FFC107;font-size:10px;font-weight:700">Signature Prediction and Forecast: Sigma</div><div style="font-size:17px;font-weight:800;color:#fff">Mahmoud Emad</div></div><span style="margin-left:auto;background:#FFC107;color:#111;padding:4px 8px;border-radius:999px;font-size:11px;font-weight:800">V41</span></div><div style="display:flex;gap:6px;overflow-x:auto;padding:8px;background:#020617;position:sticky;top:76px;z-index:98"><a href="#today" style="background:#16A34A;color:#fff;padding:8px 14px;border-radius:999px;text-decoration:none;font-size:13px;font-weight:700">Today</a><a href="#future" style="background:#1e293b;color:#fff;padding:8px 14px;border-radius:999px;text-decoration:none;font-size:13px">Future</a><a href="#lab" style="background:#1e293b;color:#fff;padding:8px 14px;border-radius:999px;text-decoration:none;font-size:13px">Lab</a><a href="#value" style="background:#1e293b;color:#fff;padding:8px 14px;border-radius:999px;text-decoration:none;font-size:13px">Value</a><a href="#golden" style="background:#1e293b;color:#fff;padding:8px 14px;border-radius:999px;text-decoration:none;font-size:13px">Golden</a></div>'
h=h.replace('<body>', '<body>'+hdr, 1)
# IDs
for k in ['Real History','418 REAL','AI Lab','Value -','Golden Bets']:
  h=h.replace(k, f'<div id="{k[:4].lower()}"></div>'+k, 1)
# Fix Value inputs: odds 1.95 prob 60
h=re.sub(r'id="odds" value="[^"]*"', 'id="odds" value="1.95"', h)
h=re.sub(r'id="prob" value="[^"]*"', 'id="prob" value="60"', h)
h=h.replace('value="1.25"','value="1.95"').replace('value="1"','value="60"')
# Fix calcEdge: correct formula + color
h=re.sub(r'function calcEdge\(\)\{.*?\}', 'function calcEdge(){let o=parseFloat(document.getElementById("odds").value);let pr=parseFloat(document.getElementById("prob").value)/100;let e=pr*o-1;let c=e>0.05?"#00FF88":"#FF4444";document.getElementById("edgeRes").innerHTML="<span style=color:"+c+">Edge: "+(e*100).toFixed(2)+"% - Kelly 1/4: "+(e*25).toFixed(2)+"% - "+(e>0.05?"BET":"NO BET")+"</span>"}', h, flags=re.DOTALL)
# Bottom nav
bot='<div style="position:fixed;bottom:0;left:0;right:0;background:#0f172a;border-top:1px solid #FFC107;display:flex;justify-content:space-around;padding:10px;max-width:430px;margin:0 auto;z-index:99"><a href="#today" style="color:#FFC107;text-decoration:none;font-size:12px;font-weight:700">Home</a><a href="#future" style="color:#fff;text-decoration:none;font-size:12px">Future</a><a href="#lab" style="color:#fff;text-decoration:none;font-size:12px">Lab</a><a href="#value" style="color:#fff;text-decoration:none;font-size:12px">Value</a><a href="#golden" style="color:#fff;text-decoration:none;font-size:12px">Golden</a></div><div style="height:60px"></div>'
if 'position:fixed;bottom:0' not in h:
  h=h.replace('</body>', bot+'</body>')
h=h.replace('width:150px;height:150px','width:110px;height:110px')
p.write_text(h); print('V41a done')
