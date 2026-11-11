import pathlib
p=pathlib.Path('index.html')
h=p.read_text()
css='<style>.card{background:#0f172a;border:1px solid #1e293b;border-radius:16px;padding:16px;margin:12px 0}.card b{font-size:16px}button{background:#FFC107;border:0;padding:12px;border-radius:999px;font-weight:800;width:100%}</style>'
if '.card{' not in h:
  h=h.replace('</head>', css+'</head>')
  print('clean CSS added')
else:
  print('CSS already')
# shortcuts bar
short='<div style="display:flex;gap:6px;overflow-x:auto;padding:8px 0"><button style="width:auto;padding:8px 14px" onclick="doFilter()">All</button><button style="width:auto;padding:8px 14px" onclick="doFilter()">Today</button><button style="width:auto;padding:8px 14px">Golden</button><button style="width:auto;padding:8px 14px">Top Conf</button></div><input id="sBox" placeholder="Search 573 teams..." oninput="doFilter()" style="width:100%;padding:10px;border-radius:10px;margin:6px 0">'
if 'sBox' not in h:
  h=h.replace('<div class="phone">','<div class="phone">'+short,1)
  print('shortcuts added')
p.write_text(h)
print('clean done')
