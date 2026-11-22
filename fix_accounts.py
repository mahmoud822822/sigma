import pathlib
p = pathlib.Path("index.html")
s = p.read_text()
if "sigma_accounts" not in s:
    js = """<script>
window.SIGMA_DEFAULT_ACCOUNTS=[
{u:"super",p:"Sigma2026!",r:"super"},
{u:"admin",p:"sigma123",r:"admin"},
{u:"editor1",p:"123456",r:"editor"},
{u:"viewer1",p:"123456",r:"viewer"}
];
function sigmaGetAccounts(){
try{
var a=JSON.parse(localStorage.getItem("sigma_accounts"));
if(a&&a.length>0){return a;}
}catch(e){}
localStorage.setItem("sigma_accounts",JSON.stringify(window.SIGMA_DEFAULT_ACCOUNTS));
return window.SIGMA_DEFAULT_ACCOUNTS;
}
window.sigmaAdminLogin=function(){
var u=prompt("Username:");
if(!u){return;}
var pw=prompt("Password:");
var accs=sigmaGetAccounts();
var f=null;
for(var i=0;i<accs.length;i++){if(accs[i].u===u&&accs[i].p===pw){f=accs[i];break;}}
if(f){
localStorage.setItem("sigma_role",f.r);
localStorage.setItem("sigma_user",f.u);
localStorage.setItem("sigma_admin",(f.r==="super"||f.r==="admin")?"1":"0");
alert("Welcome "+f.u+" Role "+f.r);
location.reload();
}else{alert("Wrong");}
};
window.sigmaLogout=function(){
localStorage.removeItem("sigma_role");
localStorage.removeItem("sigma_user");
localStorage.setItem("sigma_admin","0");
location.reload();
};
window.sigmaManageAccounts=function(){
var role=localStorage.getItem("sigma_role");
if(role!=="super"&&role!=="admin"){alert("No permission");return;}
var accs=sigmaGetAccounts();
var txt="";
for(var i=0;i<accs.length;i++){txt+=accs[i].u+" | "+accs[i].r+"\\n";}
var act=prompt("Accounts:\\n"+txt+"\\nType ADD to add, DEL to delete");
if(act==="ADD"){
var nu=prompt("New username:");
var npw=prompt("New password:");
var nr=prompt("Role: super, admin, editor, viewer");
if(nu&&npw&&(nr==="super"||nr==="admin"||nr==="editor"||nr==="viewer")){
accs.push({u:nu,p:npw,r:nr});
localStorage.setItem("sigma_accounts",JSON.stringify(accs));
alert("Account added "+nu);
}else{alert("Wrong role");}
}
if(act==="DEL"){
var du=prompt("Username to delete:");
if(du==="super"){alert("Cannot delete super");return;}
var out=[];
for(var j=0;j<accs.length;j++){if(accs[j].u!==du){out.push(accs[j]);}}
localStorage.setItem("sigma_accounts",JSON.stringify(out));
alert("Deleted "+du);
}
};
try{
var r=localStorage.getItem("sigma_role");
if(r==="super"||r==="admin"||r==="editor"){
document.body.classList.add("is-admin");
document.querySelectorAll(".admin-only").forEach(function(e){e.style.display="";});
}
}catch(e){}
</script>"""
    s = s.replace("</body>", js+"</body>") if "</body>" in s else s+js
    p.write_text(s)
    print("accounts added")
else:
    print("already there")
