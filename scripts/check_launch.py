"""Start an isolated local Streamlit process, check health, then stop it. No API calls."""

from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request


def main():
    root = Path(__file__).resolve().parents[1]
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(root / "app.py"),
         "--server.address", "127.0.0.1", "--server.port", str(port),
         "--server.headless", "true", "--browser.gatherUsageStats", "false"],
        cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline and process.poll() is None:
            try:
                with opener.open(f"http://127.0.0.1:{port}/_stcore/health", timeout=1) as response:
                    if response.status == 200:
                        print("PASS: isolated Streamlit server health HTTP 200")
                        print("NOT TESTED: browser rendering or live model response")
                        return 0
            except (urllib.error.URLError, TimeoutError):
                pass
            time.sleep(0.2)
        print("FAIL: Streamlit server did not become healthy")
        return 1
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
