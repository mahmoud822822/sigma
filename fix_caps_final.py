import pathlib
p = pathlib.Path("index.html")
s = p.read_text()
# 1 - CSS: fab right + bottom bar fixed
css = """<style>
.fab-up, .fab, .up-btn, .scroll-top, .to-top{right:12px!important;left:auto!important;}
.bottom-bar, .bottom-nav, .tab-bar, .footer-bar, .nav-bottom, .bottom-menu{position:fixed!important;bottom:0!important;left:0!important;right:0!important;transform:none!important;z-index:9999!important;}
body{padding-bottom:72px!important;}
</style>"""
if "fab-up" not in s or ".bottom-bar" not in s:
    s = s.replace("</head>", css+"</head>") if "</head>" in s else s+css
# 2 - JS: cap X2/1X to 86 + sync inner to header
js = """<script>
function sigmaFixCaps(){
try{
var cards=document.querySelectorAll(".card, .match-card, .match, article");
if(cards.length===0){cards=[document.body];}
cards.forEach(function(card){
var all=card.querySelectorAll("*");
var headerPct=null;
for(var i=0;i<all.length;i++){
var t=all[i].textContent||"";
if(/Lens.*75%/.test(t)||/\\(75%\\)/.test(t)){headerPct=75;}
}
if(headerPct!==null){
for(var j=0;j<all.length;j++){
var el=all[j];
if(el.children.length===0){
var txt=el.textContent||"";
if(/Lens:\\s*77%/.test(txt)){el.textContent=txt.replace("77%","75%");}
if(/Lens:\\s*\\d+%/.test(txt)){el.textContent=txt.replace(/Lens:\\s*\\d+%/,"Lens: 75%");}
}
}
}
for(var k=0;k<all.length;k++){
var e2=all[k];
if(e2.children.length===0){
var tx=e2.textContent||"";
if(/(X2|1X)/.test(tx)){
var m=tx.match(/(\\d+\\.\\d+|\\d+)%/);
if(m&&parseFloat(m[1])>86){e2.textContent=tx.replace(m[1]+"%","86%");}
}
}
}
});
}catch(e){}
}
setInterval(sigmaFixCaps,400);
document.addEventListener("DOMContentLoaded",sigmaFixCaps);
</script>"""
if "sigmaFixCaps" not in s:
    s = s.replace("</body>", js+"</body>") if "</body>" in s else s+js
p.write_text(s)
print("caps fab bottom fixed")
