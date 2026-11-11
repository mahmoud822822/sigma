import pathlib
p=pathlib.Path('index.html')
h=p.read_text()
search='<input id="sBox" placeholder="Search 573 teams..." oninput="doFilter()" style="width:100%;padding:10px;margin:8px 0;border-radius:10px"><select id="sLeague" onchange="doFilter()"><option>All Leagues</option><option>Italy</option><option>Netherlands</option><option>Spain La Liga</option><option>England</option></select><script>function doFilter(){let q=document.getElementById("sBox").value.toLowerCase();document.querySelectorAll(".card").forEach(c=>{c.style.display=c.innerText.toLowerCase().includes(q)?"block":"none"})}function toValue(prob){document.getElementById("prob").value=prob;document.getElementById("edgeRes").innerText="Prob set: "+prob+"% - Now enter odds and Calculate"}</script>'
if 'sBox' not in h:
 h=h.replace('<div class="phone">','<div class="phone">'+search,1)
 p.write_text(h)
 print('UI added')
else:
 print('already have search')
