#!/usr/bin/env python
import sys
import signal
from server import create_app

def signal_handler(sig, frame):
        print('You pressed Ctrl+C!')
        sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    app = create_app()
    app.run(host="0.0.0.0", port=4040, threaded=True)
