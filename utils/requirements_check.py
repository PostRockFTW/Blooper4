# Blooper4/utils/requirements_check.py
import subprocess
import sys
import os
import importlib.util

def check_requirements():
    print("--- Blooper 4.0 Dependency Check ---")
    req_path = os.path.join(os.path.dirname(__file__), "..", "requirements.txt")
    
    if not os.path.exists(req_path):
        with open(req_path, "w") as f:
            f.write("pygame==2.6.1\nnumpy>=1.26.0\nscipy>=1.11.0\n")

    with open(req_path, "r") as f:
        libs = [line.split('==')[0].split('>=')[0].strip().lower() for line in f if line.strip()]

    missing = False
    for lib in libs:
        if importlib.util.find_spec(lib) is None:
            print(f"! Library '{lib}' is missing.")
            missing = True

    if missing:
        print("Installing dependencies...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_path])
            print("[OK] Success.")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        print("[OK] Environment Ready.")