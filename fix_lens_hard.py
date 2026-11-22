import pathlib, re
p = pathlib.Path("index.html")
s = p.read_text()
print("before 93.4 count:", s.count("93.4"))
print("before Lens 77 count:", s.count("Lens: 77"))
# 1 - fix the numbers themselves in the file
s = s.replace("93.4%", "86%")
s = s.replace("93.4", "86")
s = s.replace("Lens: 77%", "Lens: 75%")
s = s.replace("Lens: 77", "Lens: 75")
# 2 - force fab to right with JS that runs every 400ms
js = """<script>
function sigmaForceFab(){
try{
var els=document.querySelectorAll("button, div, a");
for(var i=0;i<els.length;i++){
var e=els[i];
if((e.textContent||"").trim()==="\\u2191" || e.className.toString().indexOf("fab")>=0){
e.style.setProperty("right","12px","important");
e.style.setProperty("left","auto","important");
}
}
}catch(e){}
}
setInterval(sigmaForceFab,400);
</script>"""
if "sigmaForceFab" not in s:
    s = s.replace("</body>", js+"</body>") if "</body>" in s else s+js
p.write_text(s)
print("after 93.4 count:", s.count("93.4"))
print("after Lens 77 count:", s.count("Lens: 77"))
print("done hard fix")
