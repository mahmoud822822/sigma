import pathlib, re
p = pathlib.Path("index.html")
html = p.read_text(encoding="utf-8")
html = re.sub(r'<script id="admin-v23".*?</script>', '', html, flags=re.DOTALL)
admin = r'''
<script id="admin-v23">
async function supaRegister(){
 let u=document.getElementById('suName').value.trim().toLowerCase();
 let pw=document.getElementById('suPass').value;
 if(!u||!pw){document.getElementById('supaMsg').innerText='Enter username + password';return}
 if(!supa){document.getElementById('supaMsg').innerText='Supabase not connected';return}
 let r=await supa.from('sigma_users').insert({username:u,pass_hash:hashPass2(pw),status:'pending',role:'user'}).select();
 if(r.error){document.getElementById('supaMsg').innerText=r.error.message.includes('duplicate')?'Username exists - Press Login':r.error.message;return}
 document.getElementById('supaMsg').innerText='Registered - Waiting for Admin Approval';
 alert('Registered - Waiting for Admin Approval');
}
async function supaLogin(){
 let u=document.getElementById('suName').value.trim().toLowerCase();
 let pw=document.getElementById('suPass').value;
 if(!supa){document.getElementById('supaMsg').innerText='Supabase not connected';return}
 let r=await supa.from('sigma_users').select('*').eq('username',u).limit(1);
 if(!r.data||!r.data.length){document.getElementById('supaMsg').innerText='User not found - Press Register';return}
 let usr=r.data[0];
 if(usr.pass_hash!==hashPass2(pw)){document.getElementById('supaMsg').innerText='Wrong password';return}
 if(usr.status==='pending'){document.getElementById('supaMsg').innerText='Waiting for Admin Approval';alert('Waiting for Admin Approval');return}
 if(usr.status==='rejected'){document.getElementById('supaMsg').innerText='Rejected by Admin';return}
 if(usr.status==='banned'){document.getElementById('supaMsg').innerText='Banned by Admin';return}
 localStorage.setItem('sigma_current',u);
 localStorage.setItem('sigma_uid',String(usr.id));
 localStorage.setItem('sigma_role',usr.role||'user');
 supaUser={id:usr.id,username:u,role:usr.role};
 alert('Logged in Shared: '+u+' - Role: '+(usr.role||'user'));
 closeSupaAcc(); checkAdminBtn();
}
function checkAdminBtn(){
 let role=localStorage.getItem('sigma_role')||'';
 let u=localStorage.getItem('sigma_current')||'';
 let btn=document.getElementById('adminBtn');
 if(!btn){
  let bar=document.getElementById('supaBar');
  if(bar){
   btn=document.createElement('button');btn.id='adminBtn';btn.innerText='Admin Panel';btn.style.cssText='background:#dc2626;color:#fff;border:none;padding:6px 10px;border-radius:999px;cursor:pointer;display:none';btn.onclick=openAdmin;bar.appendChild(btn);
   let prof=document.createElement('button');prof.innerText='My Profile';prof.style.cssText='background:#2563eb;color:#fff;border:none;padding:6px 10px;border-radius:999px;cursor:pointer';prof.onclick=showMyProfile;bar.appendChild(prof);
  }
 }
 if(btn) btn.style.display=(role==='admin'||u==='mahmoud')?'inline-block':'none';
}
async function openAdmin(){
 let u=localStorage.getItem('sigma_current')||'';let role=localStorage.getItem('sigma_role')||'';
 if(role!=='admin'&&u!=='mahmoud'){alert('Admin only - Mahmoud');return}
 document.getElementById('adminModal').style.display='flex';loadAdminUsers();
}
function closeAdmin(){document.getElementById('adminModal').style.display='none'}
async function loadAdminUsers(){
 let r=await supa.from('sigma_users').select('*').order('created_at',{ascending:false});
 let rows=r.data||[];let pend=rows.filter(x=>x.status==='pending').length;
 let h='<p><b>Total:</b> '+rows.length+' - <b>Pending:</b> '+pend+'</p>';
 rows.forEach(x=>{h+='<div style="display:flex;justify-content:space-between;gap:6px;padding:8px 0;border-bottom:1px solid #eee;font-size:13px;flex-wrap:wrap"><span><b>'+x.username+'</b> - '+x.status+' - '+(x.role||'user')+'</span><span><button onclick="adminSet(\''+x.username+'\',\'approved\')">Approve</button> <button onclick="adminSet(\''+x.username+'\',\'rejected\')">Reject</button> <button onclick="adminSet(\''+x.username+'\',\'banned\')">Ban</button> <button onclick="adminRole(\''+x.username+'\',\'admin\')">Make Admin</button> <button onclick="delUser(\''+x.username+'\')">Delete</button></span></div>'});
 document.getElementById('adminList').innerHTML=h;
}
async function adminSet(u,s){await supa.from('sigma_users').update({status:s}).eq('username',u);alert(u+' -> '+s);loadAdminUsers();}
async function adminRole(u,ro){await supa.from('sigma_users').update({role:ro}).eq('username',u);alert(u+' role -> '+ro);loadAdminUsers();}
async function delUser(u){if(!confirm('Delete '+u+' ?'))return;await supa.from('sigma_users').delete().eq('username',u);loadAdminUsers();}
async function showMyProfile(){
 let u=localStorage.getItem('sigma_current')||'';if(!u){alert('Login first');return}
 let r=await supa.from('sigma_users').select('*').eq('username',u).limit(1);let usr=r.data[0]||{};
 let b=await supa.from('sigma_bets').select('*').eq('username',u);let bets=b.data||[];let won=bets.filter(x=>x.status==='won').length;let wr=bets.length?Math.round(won/bets.length*100):0;
 let np=prompt('My Profile - '+u+'\nStatus: '+usr.status+'\nRole: '+(usr.role||'user')+'\nBets: '+bets.length+' Won: '+won+' WinRate: '+wr+'%\n\nEnter NEW password to change, or Cancel:');
 if(np&&np.length>=4){await supa.from('sigma_users').update({pass_hash:hashPass2(np)}).eq('username',u);alert('Password changed');}
}
document.addEventListener('DOMContentLoaded',()=>{setTimeout(checkAdminBtn,1000);let m=document.createElement('div');m.id='adminModal';m.style.cssText='display:none;position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:2000;align-items:center;justify-content:center';m.innerHTML='<div style="background:#fff;width:94%;max-width:520px;border-radius:16px;padding:16px;max-height:85vh;overflow:auto;font-family:Arial"><h3 style="margin:0">Admin Panel - Mahmoud</h3><div id="adminList"></div><button onclick="closeAdmin()" style="width:100%;padding:10px;margin-top:10px;background:#eee;border:none;border-radius:10px">Close</button></div>';document.body.appendChild(m);});
</script>
'''
if "</body>" in html:
    html = html.replace("</body>", admin + "</body>", 1)
else:
    html = html + admin
p.write_text(html, encoding="utf-8")
print("V23 Admin installed")
