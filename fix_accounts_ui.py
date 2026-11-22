import pathlib
p = pathlib.Path("index.html")
s = p.read_text()
if "sigma-accounts-panel" not in s:
    js = """<script>
function sigmaRenderTop(){
try{
var tools=document.querySelector(".top-tools");
if(!tools){return;}
var role=localStorage.getItem("sigma_role")||"";
var user=localStorage.getItem("sigma_user")||"";
if(!document.getElementById("sigma-user-label")){
var lbl=document.createElement("span");
lbl.id="sigma-user-label";
lbl.style.cssText="font-size:.7rem;color:#fff;opacity:.9;margin:0 6px;";
tools.appendChild(lbl);
}
var lbl2=document.getElementById("sigma-user-label");
lbl2.textContent = role ? ("Logged: "+user+" - "+role) : "Not logged";
if(!document.getElementById("sigma-logout-btn")){
var b=document.createElement("button");
b.id="sigma-logout-btn"; b.className="tbtn"; b.textContent="Logout";
b.onclick=function(){window.sigmaLogout();};
tools.appendChild(b);
}
if(!document.getElementById("sigma-accounts-btn")){
var b2=document.createElement("button");
b2.id="sigma-accounts-btn"; b2.className="tbtn"; b2.textContent="Accounts";
b2.onclick=function(){window.sigmaToggleAccounts();};
tools.appendChild(b2);
}
var ab=document.getElementById("sigma-accounts-btn");
if(ab){ab.style.display=(role==="super"||role==="admin")?"":"none";}
}catch(e){}
}
window.sigmaToggleAccounts=function(){
var p=document.getElementById("sigma-accounts-panel");
if(!p){return;}
if(p.style.display==="none"||p.style.display===""){p.style.display="block";window.sigmaListAccounts();}else{p.style.display="none";}
};
window.sigmaListAccounts=function(){
try{
var accs=JSON.parse(localStorage.getItem("sigma_accounts")||"[]");
var box=document.getElementById("sigma-accounts-list");
if(!box){return;}
var h="";
for(var i=0;i<accs.length;i++){
h+="<div style='display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid #333;'><span>"+accs[i].u+" - "+accs[i].r+"</span>";
if(accs[i].u!=="super"){h+="<button onclick=\\"window.sigmaDeleteAccount('"+accs[i].u+"')\\" style='background:#7f1d1d;color:#fff;border:0;padding:4px 8px;border-radius:6px;'>Delete</button>";}else{h+="<span>Protected</span>";}
h+="</div>";
}
box.innerHTML=h;
}catch(e){}
};
window.sigmaDeleteAccount=function(u){
if(u==="super"){alert("Cannot delete super");return;}
var accs=JSON.parse(localStorage.getItem("sigma_accounts")||"[]");
var out=[];
for(var i=0;i<accs.length;i++){if(accs[i].u!==u){out.push(accs[i]);}}
localStorage.setItem("sigma_accounts",JSON.stringify(out));
window.sigmaListAccounts();
};
window.sigmaAddAccountUI=function(){
var nu=document.getElementById("sigma-new-user").value.trim();
var npw=document.getElementById("sigma-new-pass").value.trim();
var nr=document.getElementById("sigma-new-role").value;
if(!nu||!npw){alert("Fill user and pass");return;}
var accs=JSON.parse(localStorage.getItem("sigma_accounts")||"[]");
for(var i=0;i<accs.length;i++){if(accs[i].u===nu){alert("Exists");return;}}
accs.push({u:nu,p:npw,r:nr});
localStorage.setItem("sigma_accounts",JSON.stringify(accs));
document.getElementById("sigma-new-user").value="";
document.getElementById("sigma-new-pass").value="";
window.sigmaListAccounts();
alert("Added "+nu);
};
window.sigmaResetAccounts=function(){
localStorage.removeItem("sigma_accounts");
location.reload();
};
document.addEventListener("DOMContentLoaded",function(){
try{
var panel=document.createElement("div");
panel.id="sigma-accounts-panel";
panel.className="admin-only";
panel.style.cssText="display:none;background:#0f172a;border:1px solid #334155;border-radius:10px;padding:12px;margin:10px;";
panel.innerHTML="<div style='display:flex;justify-content:space-between;'><b>Accounts</b><button onclick=\\"window.sigmaToggleAccounts()\\" style='background:#334155;color:#fff;border:0;padding:4px 10px;border-radius:6px;'>Close</button></div><div id='sigma-accounts-list' style='margin:10px 0;'></div><div style='display:flex;gap:6px;flex-wrap:wrap;'><input id='sigma-new-user' placeholder='New username' style='flex:1;padding:8px;border-radius:6px;border:1px solid #334155;background:#020617;color:#fff;'><input id='sigma-new-pass' placeholder='New password' style='flex:1;padding:8px;border-radius:6px;border:1px solid #334155;background:#020617;color:#fff;'><select id='sigma-new-role' style='padding:8px;border-radius:6px;background:#020617;color:#fff;'><option value='viewer'>viewer</option><option value='editor'>editor</option><option value='admin'>admin</option><option value='super'>super</option></select><button onclick=\\"window.sigmaAddAccountUI()\\" style='background:#16a34a;color:#fff;border:0;padding:8px 12px;border-radius:6px;'>Add</button></div><div style='font-size:.7rem;opacity:.7;margin-top:8px;'>Super cannot be deleted. Accounts are saved in this browser.</div>";
var top=document.querySelector(".top-tools");
if(top&&top.parentNode){top.parentNode.insertBefore(panel,top.nextSibling);}else{document.body.insertBefore(panel,document.body.firstChild);}
}catch(e){}
sigmaRenderTop();
});
setTimeout(sigmaRenderTop,800);
</script>"""
    s = s.replace("</body>", js+"</body>") if "</body>" in s else s+js
    p.write_text(s)
    print("accounts ui added")
else:
    print("already there")
