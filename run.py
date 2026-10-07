import os
import sys
import time
import subprocess
import webbrowser
import requests

def check_or_start_ollama():
    try:
        r = requests.get("http://127.0.0.1:11434/api/tags", timeout=2)
        if r.status_code == 200:
            print("[✓] Local Ollama server is running with active models.")
            return True
    except Exception:
        pass

    print("[i] Ollama not responding on port 11434. Attempting to start local Ollama server...")
    try:
        ollama_bin = os.path.expanduser(r"~\AppData\Local\Programs\Ollama\ollama.exe")
        if not os.path.exists(ollama_bin):
            ollama_bin = "ollama"
        subprocess.Popen([ollama_bin, "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)
        print("[✓] Ollama server launched.")
        return True
    except Exception as e:
        print(f"[!] Note: Ollama could not be auto-started ({e}). Falling back to embedded naturalist engine.")
        return False

def main():
    print("=" * 65)
    print("🌿 GROUNDED: TouchGrass AI — Zero-Signal Outdoor Companion")
    print("   Open-Source AI at its Core (Gemma 3:4b + Bioacoustics + GPX)")
    print("=" * 65)

    check_or_start_ollama()

    port = 8000
    host = "127.0.0.1"
    url = f"http://{host}:{port}"
    print(f"\n[✓] Launching Grounded Web Portal at: {url}")
    print("[✓] Press Ctrl+C in terminal to stop server.\n")

    # Try opening browser after slight delay
    def open_browser():
        time.sleep(1.5)
        try:
            webbrowser.open(url)
        except Exception:
            pass

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    import uvicorn
    # Import app
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from backend.app import app
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    main()
