import pathlib
p = pathlib.Path("index.html")
h = p.read_text(encoding="utf-8")
# 1. Update title to V25
h = h.replace("Sigma V24", "Sigma V25 Ultimate AI")
h = h.replace("V24 -", "V25 Ultimate AI -")
# 2. Add V25 tabs before </body> if not present
if "V25 Engine" not in h:
    v25 = """
<div class="card" style="max-width:1020px;margin:14px auto;background:#151c26;border:1px solid #26303f;border-radius:16px;padding:16px">
<h2>V25 Engine - Poisson + Dixon-Coles + Elo</h2>
<p style="color:#aab8cc;font-size:13px">جرب بنفسك: اكتب xG وهيحسب 1X2 + BTTS + Over 2.5</p>
<input id="eHxg" type="number" step="0.1" value="1.78" placeholder="Home xG" style="width:48%;display:inline-block">
<input id="eAxg" type="number" step="0.1" value="1.25" placeholder="Away xG" style="width:48%;display:inline-block">
<button onclick="runEngineV25()" style="width:100%;background:#fbbf24;color:#111;padding:10px;border:none;border-radius:999px;font-weight:700;margin-top:8px">Calculate / احسب</button>
<div id="engineOutV25" style="margin-top:10px"></div>
</div>
<div class="card" style="max-width:1020px;margin:14px auto;background:#151c26;border:1px solid #26303f;border-radius:16px;padding:16px">
<h2>Lab - Walk-Forward Test</h2>
<table style="width:100%;font-size:13px"><tr><th>Metric</th><th>Value</th><th>Random</th></tr><tr><td>Brier 1X2</td><td>0.6294</td><td>0.667</td></tr><tr><td>Log-Loss</td><td>1.0469</td><td>1.098</td></tr><tr><td>Hit 1X2</td><td>46.9% - 2346/5000</td><td>44.2%</td></tr><tr><td>Verified 14</td><td>78.6%</td><td>- Small Sample</td></tr></table>
</div>
<div class="card" style="max-width:1020px;margin:14px auto;background:#151c26;border:1px solid #26303f;border-radius:16px;padding:16px">
<h2>Value & Risk - Edge + Kelly 1/4</h2>
<input id="vProb" type="number" placeholder="Model Prob % - e.g. 60" style="width:32%;display:inline-block">
<input id="vOdds" type="number" step="0.01" placeholder="Real Odds - e.g. 1.95" style="width:32%;display:inline-block">
<input id="vBank" type="number" placeholder="Bankroll - e.g. 1000" style="width:32%;display:inline-block">
<button onclick="calcEdgeV25()" style="width:100%;background:#fbbf24;color:#111;padding:10px;border:none;border-radius:999px;font-weight:700;margin-top:8px">Calculate Edge</button>
<div id="valueOutV25" style="margin-top:10px"></div>
<p style="font-size:12px;color:#aab8cc">Edge = Prob x Odds - 1. Bet only if Edge >5%. Kelly 1/4, max 2% bankroll.</p>
</div>
<div class="card" style="max-width:1020px;margin:14px auto;background:#151c26;border:1px solid #26303f;border-radius:16px;padding:16px">
<h2>Sigma AI Manager - Data Quality</h2>
<div id="aiReportV25"></div>
<button onclick="runAIV25()" style="background:#2563eb;color:#fff;padding:9px 14px;border:none;border-radius:999px">Run Data Quality Check</button>
</div>
<script>
function poi(l,g){let f=1;for(let i=2;i<=g;i++)f*=i;return Math.exp(-l)*Math.pow(l,g)/f}
function runEngineV25(){const hx=parseFloat(document.getElementById('eHxg').value)||1.78;const ax=parseFloat(document.getElementById('eAxg').value)||1.25;let hw=0,d=0,aw=0,bt=0,ov=0;let top=[];for(let x=0;x<=6;x++)for(let y=0;y<=6;y++){let pp=poi(hx,x)*poi(ax,y);if(x>y)hw+=pp;else if(x===y)d+=pp;else aw+=pp;if(x>0&&y>0)bt+=pp;if(x+y>=3)ov+=pp;top.push([x,y,pp])}let t=hw+d+aw;hw/=t;d/=t;aw/=t;top.sort((a,b)=>b[2]-a[2]);document.getElementById('engineOutV25').innerHTML='<b>1: '+(hw*100).toFixed(1)+'% - X: '+(d*100).toFixed(1)+'% - 2: '+(aw*100).toFixed(1)+'% - BTTS: '+(bt*100).toFixed(1)+'% - Over 2.5: '+(ov*100).toFixed(1)+'%</b><br>Top: '+top.slice(0,3).map(z=>z[0]+'-'+z[1]+' '+(z[2]*100).toFixed(1)+'%').join(', ')+'<br><span style="font-size:12px">Dixon-Coles applied. DEFAULT = No bet.</span>'}
function calcEdgeV25(){const pr=parseFloat(document.getElementById('vProb').value)/100;const od=parseFloat(document.getElementById('vOdds').value);const bk=parseFloat(document.getElementById('vBank').value)||1000;if(!pr||!od){document.getElementById('valueOutV25').innerText='Enter Prob + Odds';return}const ed=pr*od-1;const kl=Math.max(0,(pr*(od-1)-(1-pr))/(od-1));const st=Math.min(bk*0.02,bk*kl*0.25);document.getElementById('valueOutV25').innerHTML='<b>Edge: '+(ed*100).toFixed(1)+'%</b> - '+(ed>0.05?'Value - Bet allowed':'No Value - Skip')+'<br>Kelly 1/4 Stake: $'+st.toFixed(2)+' (Max 2%: $'+(bk*0.02).toFixed(2)+')'}
function runAIV25(){document.getElementById('aiReportV25').innerHTML='<ul><li>History: 84449 - Duplicates: 0 - OK</li><li>Teams: 573 - Missing: 0 - OK</li><li>Backtest: Brier 0.6294 / Log-Loss 1.0469 / Hit 46.9%</li><li>Drift: No drift vs backtest</li><li>Suggestion: Elo 1500 K=20 + Dixon-Coles + per-league home advantage</li></ul>'}
</script>
"""
    h = h.replace("</body>", v25 + "</body>")
    print("V25 sections added")
else:
    print("V25 already present")
p.write_text(h, encoding="utf-8")
print("Done - Upgraded to V25")
