with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

old_combo = '''  if(T==="combo"){
    pb.style.display="none";
    const top4=[...A].filter(m=>!m.trap&&(m.dc_prob||0)>82).sort((a,b)=>(b.dc_prob||0)-(a.dc_prob||0)).slice(0,4);
    const combProb=top4.length?Math.round(top4.reduce((a,c)=>a*((c.dc_prob||85)/100),1)*100):0;
    ls.innerHTML=`<div class="card gold"><h3 style="color:var(--gd);margin-bottom:6px">🧾 الورقة الذكية اليومية المجمعة (Smart Combo)</h3><p style="font-size:.76rem;color:#cbd5e1;margin-bottom:10px">اختيار آلي لأكثر 4 مباريات أماناً واستقراراً في أعلى اليوم • الاحتمال التراكمي للنجاح: <b style="color:var(--ac)">${combProb}%</b></p>`+
      top4.map((m,idx)=>`<div style="background:rgba(5,9,20,.65);padding:9px;border-radius:10px;margin-bottom:7px;border:1px solid var(--bd)"><div class="row" style="font-size:.7rem;color:var(--mt);margin-bottom:4px"><span>#${idx+1} • ${(m.league_name||m.league).slice(0,24)}</span><span>${m.date}</span></div><div class="row" style="font-size:.82rem;font-weight:800"><span>${m.home} vs ${m.away}</span><span style="color:var(--ac)">${m.dc_pick} (${m.dc_prob}%)</span></div></div>`).join("")+`</div>`;
    return;
  }'''

new_combo = '''  if(T==="combo"){
    pb.style.display="none";
    const favMatches = A.filter(m => FAV.includes(m.key));
    const safePool = [...A].filter(m=>!m.trap&&(m.dc_prob||0)>82).sort((a,b)=>(b.dc_prob||0)-(a.dc_prob||0)).slice(0,4);
    const useFav = (window._parlayMode === "fav" && favMatches.length > 0) || (window._parlayMode !== "safe" && favMatches.length > 0);
    const picks = useFav ? favMatches : safePool;
    
    const combProb = picks.length ? Math.round(picks.reduce((acc,c)=>acc*((c.dc_prob||85)/100),1)*100) : 0;
    const totalOdds = picks.length ? picks.reduce((acc,c)=>acc*(100/Math.max(50, (c.dc_prob||85))),1).toFixed(2) : "1.00";
    const stakeVal = parseFloat(document.getElementById("bk")?.value || 100) || 100;
    const parlayStake = window._parlayStake || Math.max(5, Math.round(stakeVal * 0.05));
    const totalReturn = (parlayStake * parseFloat(totalOdds)).toFixed(2);
    const netProfit = (totalReturn - parlayStake).toFixed(2);

    ls.innerHTML=`<div class="card gold">
      <div class="row" style="margin-bottom:8px">
        <h3 style="color:var(--gd);font-size:.95rem">🧮 حاسبة الأرباح التراكمية (Parlay Builder)</h3>
        <span style="font-size:.68rem;background:rgba(245,158,11,.15);color:var(--gd);padding:3px 7px;border-radius:6px">${picks.length} مباريات</span>
      </div>
      <div style="display:flex;gap:6px;margin-bottom:10px">
        <button onclick="window._parlayMode='fav';rn()" style="flex:1;padding:6px;border-radius:8px;border:1px solid ${useFav?'var(--gd)':'var(--bd)'};background:${useFav?'rgba(245,158,11,.2)':'rgba(5,9,20,.6)'};color:#fff;font-size:.72rem;font-weight:700;cursor:pointer">❤️ من مفضلتي (${favMatches.length})</button>
        <button onclick="window._parlayMode='safe';rn()" style="flex:1;padding:6px;border-radius:8px;border:1px solid ${!useFav?'var(--ac)':'var(--bd)'};background:${!useFav?'rgba(16,185,129,.2)':'rgba(5,9,20,.6)'};color:#fff;font-size:.72rem;font-weight:700;cursor:pointer">🛡️ الأعلى أماناً (Top 4)</button>
      </div>
      <div style="background:rgba(5,9,20,.75);border:1px solid var(--bd);border-radius:10px;padding:10px;margin-bottom:10px">
        <div class="row" style="margin-bottom:8px">
          <span style="font-size:.75rem;color:#cbd5e1">💵 مبلغ الدخول في الورقة:</span>
          <input type="number" value="${parlayStake}" min="1" onchange="window._parlayStake=Math.max(1,parseFloat(this.value)||10);rn()" style="width:85px;background:#0f172a;border:1px solid var(--gd);color:var(--gd);font-weight:800;border-radius:7px;padding:4px 8px;text-align:center;font-size:.82rem">
        </div>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:6px;text-align:center">
          <div style="background:rgba(15,23,42,.8);padding:6px;border-radius:8px">
            <div style="font-size:.62rem;color:var(--mt)">إجمالي المضاعف</div>
            <div style="font-size:.88rem;font-weight:900;color:var(--bl)">${totalOdds}x</div>
          </div>
          <div style="background:rgba(15,23,42,.8);padding:6px;border-radius:8px">
            <div style="font-size:.62rem;color:var(--mt)">احتمال النجاح</div>
            <div style="font-size:.88rem;font-weight:900;color:${combProb>=50?'var(--ac)':'var(--gd)'}">${combProb}%</div>
          </div>
          <div style="background:rgba(15,23,42,.8);padding:6px;border-radius:8px">
            <div style="font-size:.62rem;color:var(--mt)">صافي الربح</div>
            <div style="font-size:.88rem;font-weight:900;color:var(--ac)">+${netProfit}</div>
          </div>
        </div>
        <div style="margin-top:8px;padding-top:6px;border-top:1px dashed var(--bd);display:flex;justify-content:space-between;font-size:.76rem">
          <span style="color:var(--mt)">إجمالي العائد المتوقع:</span>
          <b style="color:#fff;font-size:.86rem">${totalReturn}</b>
        </div>
      </div>`+
      (picks.length ? picks.map((m,idx)=>{
        const fairOdd = (100/Math.max(50,(m.dc_prob||85))).toFixed(2);
        return `<div style="background:rgba(5,9,20,.65);padding:9px;border-radius:10px;margin-bottom:7px;border:1px solid var(--bd)">
          <div class="row" style="font-size:.7rem;color:var(--mt);margin-bottom:4px">
            <span>#${idx+1} • ${(m.league_name||m.league).slice(0,22)}</span>
            <div style="display:flex;align-items:center;gap:6px">
              <span style="color:var(--bl);font-weight:700">@${fairOdd}</span>
              ${useFav?`<button onclick="togFav('${m.key}')" style="background:rgba(239,68,68,.2);border:none;color:#f87171;border-radius:5px;padding:1px 6px;font-size:.7rem;cursor:pointer">✖</button>`:""}
            </div>
          </div>
          <div class="row" style="font-size:.8rem;font-weight:800">
            <span>${m.home} vs ${m.away}</span>
            <span style="color:var(--ac)">${m.dc_pick} (${m.dc_prob}%)</span>
          </div>
        </div>`;
      }).join("") : `<p style="text-align:center;color:var(--mt);font-size:.78rem;padding:12px">اضغط على القلب 🤍 بجانب أي مباراة لإضافتها لحاسبة الورقة</p>`) +
      `<div style="text-align:center;font-size:.65rem;color:var(--mt);margin-top:8px">SIGMA AI Parlay Engine • Mahmoud Emad</div>
    </div>`;
    return;
  }'''

if old_combo in html:
    html = html.replace(old_combo, new_combo)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("SUCCESS: Interactive Parlay Builder installed!")
else:
    print("WARNING: Could not match old_combo block exactly.")
