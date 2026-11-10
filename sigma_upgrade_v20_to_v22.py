# Upgrade V20 to V22 Supabase - Mahmoud Emad
import pathlib
p = pathlib.Path("index.html")
html = p.read_text(encoding="utf-8")
if "supabase" in html.lower():
    print("Already has supabase - skip")
else:
    supa_js = r'''
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<div id="supaBar" style="position:fixed;top:0;left:0;right:0;z-index:999;background:#111;color:#fff;padding:8px 12px;display:flex;justify-content:space-between;align-items:center;font-family:Arial;font-size:13px"><span id="supaStatus">Shared: OFF - Local</span><span><button onclick="openSupaAcc()" style="background:#fff;color:#111;border:none;padding:6px 10px;border-radius:999px;cursor:pointer">Account</button> <button onclick="showMyBets()" style="background:#16a34a;color:#fff;border:none;padding:6px 10px;border-radius:999px;cursor:pointer">My Bets</button></span></div>
<div id="supaModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:1000;align-items:center;justify-content:center"><div style="background:#fff;width:92%;max-width:380px;border-radius:16px;padding:18px;font-family:Arial"><h3 style="margin:0">Account - Sigma Live</h3><p style="font-size:12px;color:#666">Supabase = Shared on all devices</p><input id="suName" placeholder="Username" style="width:100%;padding:10px;margin:6px 0;border:1px solid #ddd;border-radius:10px"><input id="suPass" type="password" placeholder="Password" style="width:100%;padding:10px;margin:6px 0;border:1px solid #ddd;border-radius:10px"><button onclick="supaRegister()" style="width:100%;padding:10px;margin:4px 0;background:#111;color:#fff;border:none;border-radius:10px">Register</button><button onclick="supaLogin()" style="width:100%;padding:10px;margin:4px 0;background:#16a34a;color:#fff;border:none;border-radius:10px">Login</button><button onclick="supaLogout()" style="width:100%;padding:10px;margin:4px 0;background:#fee2e2;color:#dc2626;border:none;border-radius:10px">Logout</button><button onclick="closeSupaAcc()" style="width:100%;padding:10px;margin:4px 0;background:#eee;border:none;border-radius:10px">Close</button><p id="supaMsg" style="font-size:12px;color:red"></p></div></div>
<script>
let supa=null, supaUser=null;
function openSupaAcc(){document.getElementById('supaModal').style.display='flex'}
function closeSupaAcc(){document.getElementById('supaModal').style.display='none'}
function initSupa(){let url=localStorage.getItem('sigma_supa_url')||''; let key=localStorage.getItem('sigma_supa_key')||''; let st=document.getElementById('supaStatus'); if(url&&key&&url.includes('supabase.co')&&window.supabase){try{supa=window.supabase.createClient(url,key); st.innerText='Shared: ON - Supabase Live'; st.style.background='#16a34a'; supa.auth.getSession().then(r=>{if(r.data.session){supaUser=r.data.session.user;}})}catch(e){st.innerText='Shared: OFF - Local'}} else {st.innerText='Shared: OFF - Local'}}
async function supaRegister(){let u=document.getElementById('suName').value.trim().toLowerCase(); let p=document.getElementById('suPass').value; if(!u||!p){document.getElementById('supaMsg').innerText='Enter username + password';return} if(!supa){document.getElementById('supaMsg').innerText='Supabase not connected - Run Fast Link first';return} let r=await supa.auth.signUp({email:u+'@sigma.app',password:p}); if(r.error){document.getElementById('supaMsg').innerText=r.error.message;return} if(r.data.user){await supa.from('profiles').insert({id:r.data.user.id,username:u})} localStorage.setItem('sigma_current',u); alert('Registered Shared: '+u); closeSupaAcc()}
async function supaLogin(){let u=document.getElementById('suName').value.trim().toLowerCase(); let p=document.getElementById('suPass').value; if(!supa){document.getElementById('supaMsg').innerText='Supabase not connected';return} let r=await supa.auth.signInWithPassword({email:u+'@sigma.app',password:p}); if(r.error){document.getElementById('supaMsg').innerText=r.error.message;return} supaUser=r.data.user; localStorage.setItem('sigma_current',u); alert('Logged in Shared: '+u); closeSupaAcc()}
async function supaLogout(){if(supa) await supa.auth.signOut(); supaUser=null; localStorage.removeItem('sigma_current'); alert('Logged out')}
async function saveSharedBet(m,market){let u=localStorage.getItem('sigma_current')||''; if(!u){openSupaAcc(); alert('Login first'); return} if(!supa||!supaUser){alert('Supabase not connected'); return} let r=await supa.from('sigma_bets').insert({user_id:supaUser.id,username:u,match:m,market:market,stake:10,status:'pending'}); if(r.error) alert(r.error.message); else alert('Saved SHARED: '+m+' - '+market)}
async function showMyBets(){let u=localStorage.getItem('sigma_current')||''; if(!supa||!supaUser){alert('Login + Supabase first'); return} let r=await supa.from('sigma_bets').select('*').eq('username',u).order('created_at',{ascending:false}).limit(20); let txt=(r.data||[]).map(b=>b.match+' - '+b.market+' - '+b.status).join('\\n')||'No bets yet'; alert('My Shared Bets:\\n'+txt)}
document.addEventListener('DOMContentLoaded',()=>{initSupa(); document.body.style.paddingTop='38px'; document.querySelectorAll('.mcard').forEach(card=>{let bs=card.querySelectorAll('b'); if(bs.length>=2){let m=bs[0].innerText+' vs '+bs[1].innerText; let btn=document.createElement('button'); btn.innerText='+ Save Shared Bet'; btn.style.cssText='width:100%;padding:10px;background:#16a34a;color:#fff;border:none;cursor:pointer;font-weight:700'; btn.onclick=()=>saveSharedBet(m,'1X / Over 2.5'); card.appendChild(btn)}})});
</script>
'''
    if "</body>" in html:
        html = html.replace("</body>", supa_js + "</body>", 1)
    else:
        html = html + supa_js
    p.write_text(html, encoding="utf-8")
    print("Upgraded V20 to V22 Supabase")
