import threading
import subprocess
import sys
import os

def run_flask():
    # Flask sunucusunu başlat
    subprocess.Popen([sys.executable, os.path.abspath(os.path.join('api', 'main.py'))])

if __name__ == "__main__":
    # Flask'ı thread ile başlat
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # PyQt5 arayüzünü ana threadde başlat
    pyqt_path = os.path.abspath(os.path.join('gui', 'gui_pyqt.py'))
    subprocess.call([sys.executable, pyqt_path])