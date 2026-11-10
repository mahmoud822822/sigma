# Fix email domain - Mahmoud Emad
import pathlib
p = pathlib.Path("index.html")
html = p.read_text(encoding="utf-8")
# sigma.app is rejected by Supabase, use gmail which is valid
html = html.replace("@sigma.app", ".sigma@gmail.com")
p.write_text(html, encoding="utf-8")
print("Fixed - Now uses mahmoud.sigma@gmail.com")
