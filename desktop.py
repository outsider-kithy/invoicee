import threading
import time
import requests
import webview
from app import create_app

PORT = 5000

def run_flask():
    app = create_app()
    app.run(port=PORT, debug=False, use_reloader=False, threaded=True)

def wait_for_server():
    while True:
        try:
            requests.get(f"http://127.0.0.1:{PORT}")
            break
        except:
            time.sleep(0.1)

if __name__ == '__main__':
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    wait_for_server()

    webview.create_window(
        "My App",
        f"http://127.0.0.1:{PORT}/login",
        width=1000,
        height=700
    )

    webview.start()