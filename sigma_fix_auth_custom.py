# Fix Auth to Username only - No Email - Mahmoud Emad
import pathlib, re
p = pathlib.Path("index.html")
html = p.read_text(encoding="utf-8")
html = re.sub(r'<script id="custom-auth".*?</script>', '', html, flags=re.DOTALL)
override = r'''
<script id="custom-auth">
function hashPass2(s){let h=0;for(let i=0;i<s.length;i++){h=(h*31+s.charCodeAt(i))>>>0}return h.toString(16)}
async function supaRegister(){let u=document.getElementById('suName').value.trim().toLowerCase(); let pw=document.getElementById('suPass').value; if(!u||!pw){document.getElementById('supaMsg').innerText='Enter username + password';return} if(!supa){document.getElementById('supaMsg').innerText='Supabase not connected';return} let r=await supa.from('sigma_users').insert({username:u,pass_hash:hashPass2(pw)}).select(); if(r.error){document.getElementById('supaMsg').innerText=r.error.message.includes('duplicate')?'Username exists - Press Login':r.error.message;return} localStorage.setItem('sigma_current',u); localStorage.setItem('sigma_uid',String(r.data[0].id)); supaUser={id:r.data[0].id,username:u}; alert('Registered Shared: '+u); closeSupaAcc();}
async function supaLogin(){let u=document.getElementById('suName').value.trim().toLowerCase(); let pw=document.getElementById('suPass').value; if(!supa){document.getElementById('supaMsg').innerText='Supabase not connected';return} let r=await supa.from('sigma_users').select('*').eq('username',u).limit(1); if(!r.data||!r.data.length){document.getElementById('supaMsg').innerText='User not found - Press Register';return} if(r.data[0].pass_hash!==hashPass2(pw)){document.getElementById('supaMsg').innerText='Wrong password';return} localStorage.setItem('sigma_current',u); localStorage.setItem('sigma_uid',String(r.data[0].id)); supaUser={id:r.data[0].id,username:u}; alert('Logged in Shared: '+u); closeSupaAcc();}
async function saveSharedBet(m,market){let u=localStorage.getItem('sigma_current')||''; if(!u){openSupaAcc(); alert('Login first'); return} if(!supa){alert('Supabase not connected'); return} let r=await supa.from('sigma_bets').insert({username:u,match:m,market:market,stake:10,status:'pending'}); if(r.error) alert(r.error.message); else alert('Saved SHARED: '+m+' - '+market)}
async function showMyBets(){let u=localStorage.getItem('sigma_current')||''; if(!supa||!u){alert('Login first'); return} let r=await supa.from('sigma_bets').select('*').eq('username',u).order('created_at',{ascending:false}).limit(20); let txt=(r.data||[]).map(b=>b.match+' - '+b.market+' - '+b.status).join('\n')||'No bets yet'; alert('My Shared Bets:\n'+txt)}
</script>
'''
if "</body>" in html:
    html = html.replace("</body>", override + "</body>", 1)
else:
    html = html + override
p.write_text(html, encoding="utf-8")
print("Fixed to Username-only Auth - No Email")
