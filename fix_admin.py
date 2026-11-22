import pathlib
p = pathlib.Path("index.html")
s = p.read_text()
if "sigmaAdminLogin" not in s:
    btn = '<button class=tbtn onclick="sigmaAdminLogin()">Admin</button>'
    s = s.replace("</div>", btn+"</div>", 1)
    fix = """<script>
window.sigmaAdminLogin=function(){
var u=prompt("Admin user:");
var pw=prompt("Password:");
if(u==="admin"&&pw==="sigma123"){localStorage.setItem("sigma_role","admin");localStorage.setItem("sigma_admin","1");alert("Admin OK");location.reload()}
else if(u==="editor1"&&pw==="123456"){localStorage.setItem("sigma_role","editor");alert("Editor OK");location.reload()}
else if(u==="viewer1"&&pw==="123456"){localStorage.setItem("sigma_role","viewer");alert("Viewer OK");location.reload()}
else{alert("Wrong")}
};
try{
if(localStorage.getItem("sigma_role")==="admin"||localStorage.getItem("sigma_admin")==="1"){
document.body.classList.add("is-admin");
document.querySelectorAll(".admin-only").forEach(e=>e.style.display="");
}
}catch(e){}
</script>"""
    s = s.replace("</body>", fix+"</body>") if "</body>" in s else s+fix
    p.write_text(s)
    print("admin login added")
else:
    print("already there")
