import subprocess, sys

def ensure(pkg):
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg,
                               "--quiet", "--break-system-packages"])

ensure("yfinance")
ensure("pandas")
ensure("numpy")
ensure("ta")

print("Dependencies installed.")
