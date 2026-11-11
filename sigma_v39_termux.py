import base64, pathlib
p=pathlib.Path('index.html')
h=p.read_text()
if 'my_photo.jpg' in str(pathlib.Path('.').glob('my_photo.jpg')):
  b=base64.b64encode(open('my_photo.jpg','rb').read()).decode()
  img=f'<img src="data:image/jpeg;base64,{b}" style="width:62px;height:62px;border-radius:50%;border:2px solid #FFC107;object-fit:cover">'
else:
  img='<div style="width:62px;height:62px;border-radius:50%;background:#FFC107;color:#111;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:28px">M</div>'
hdr=f'<div style="display:flex;gap:12px;align-items:center;padding:12px;background:#0f172a;border-bottom:2px solid #FFC107">{img}<div><div style="color:#FFC107;font-size:11px;font-weight:700">Signature Prediction and Forecast: Sigma</div><div style="font-size:19px;font-weight:800;color:#fff">Mahmoud Emad</div></div><span style="margin-left:auto;background:#FFC107;color:#111;padding:4px 8px;border-radius:999px;font-size:11px;font-weight:800">V39</span></div>'
if 'Signature Prediction and Forecast: Sigma' not in h:
  h=h.replace('<body>', '<body>'+hdr, 1)
else:
  print('already have signature')
  h=h.replace('V35','V39').replace('V36','V39')
p.write_text(h)
print('V39 header done')
