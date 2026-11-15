#!/usr/bin/env python3
# Sigma CHECK TOKEN - SAFE, never prints token value
# Task 3 - Mahmoud Emad
# Two DIFFERENT tokens, never mix them:
#   ~/token.txt          = GitHub token, ghp_ + 39 chars, scopes repo + workflow. For git push ONLY.
#   ~/football_token.txt = football-data.org token, exactly 32 chars alnum. For Auto-Fetch ONLY.
#   FOOTBALL_DATA_TOKEN env must be the 32-char one, NEVER the GitHub one.
# Usage: python3 sigma_check_token.py
# No Arabic inside .py. Stdlib only.
import os, re
from pathlib import Path
def check_file(path, expect_len, expect_prefix=None, label=""):
    p = Path(path)
    if not p.exists():
        print(f"{label}: MISSING {path}")
        return None
    try:
        mode = oct(p.stat().st_mode)[-3:]
    except Exception:
        mode = "?"
    txt = p.read_text(encoding="utf-8").strip()
    print(f"{label}: EXISTS {path} | len={len(txt)} | chmod={mode} | prefix_ok={txt.startswith(expect_prefix) if expect_prefix else 'n/a'}")
    if len(txt) != expect_len:
        print(f"  -> WRONG LENGTH: got {len(txt)}, expected {expect_len}. Do NOT paste token in chat.")
    else:
        print(f"  -> LENGTH OK ({expect_len})")
    if expect_prefix and not txt.startswith(expect_prefix):
        print(f"  -> WARNING: does not start with {expect_prefix}")
    return txt
def main():
    print("Sigma CHECK TOKEN - safe (values never printed)")
    home = Path.home()
    gh = check_file(home / "token.txt", 39, "ghp_", "GitHub token ~/token.txt (for git push only)")
    ft_file = check_file(home / "football_token.txt", 32, None, "Football token ~/football_token.txt (for Auto-Fetch only)")
    env = os.environ.get("FOOTBALL_DATA_TOKEN", "").strip()
    if not env:
        print("Env FOOTBALL_DATA_TOKEN: MISSING - Auto-Fetch will SKIP")
    else:
        clean = "".join(c for c in env if c.isascii() and c.isalnum())
        print(f"Env FOOTBALL_DATA_TOKEN: EXISTS len={len(env)} clean_len={len(clean)}")
        if len(clean) != 32:
            print("  -> WRONG: env is NOT 32 chars. If len=39 and starts ghp_, you exported GitHub token by mistake!")
            print("  -> Fix: unset FOOTBALL_DATA_TOKEN, then export FOOTBALL_DATA_TOKEN=$(cat ~/football_token.txt)")
        elif gh and clean == "".join(c for c in gh if c.isascii() and c.isalnum()):
            print("  -> WRONG: env equals GitHub token! Never use GitHub token for football-data.")
        else:
            print("  -> LENGTH OK (32)")
    print("")
    if ft_file and len("".join(c for c in ft_file if c.isascii() and c.isalnum())) == 32:
        print("OK - Football token file looks good. Run:")
        print("  export FOOTBALL_DATA_TOKEN=$(cat ~/football_token.txt)")
        print("  python3 sigma_auto_fetch.py")
    else:
        print("FIX - Get REAL 32-char token:")
        print("  1. Open https://www.football-data.org/client/register in browser")
        print("  2. Register free, copy token from dashboard (32 chars, NOT ghp_)")
        print("  3. In Termux: cat > ~/football_token.txt  [paste, Enter, Ctrl+D]")
        print("     chmod 600 ~/football_token.txt")
        print("     export FOOTBALL_DATA_TOKEN=$(cat ~/football_token.txt)")
        print("  4. NEVER paste token in chat. NEVER put it in ~/token.txt (that is GitHub).")
        print("  5. Re-run: python3 sigma_check_token.py")
    print("")
    print("GitHub ~/token.txt must stay UNCHANGED for git push. Do NOT overwrite it with football token.")
if __name__ == "__main__":
    main()
