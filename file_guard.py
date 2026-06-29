import os
import cv2
import pickle
import time
import threading
import win32gui
import pygetwindow as gw
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

PROTECTED_FILES = ["resume"]

_user_profile = os.environ.get("USERPROFILE", "C:/Users/YourUsername")
_project_dir   = os.environ.get("JARVIS_PROJECT_DIR", os.path.dirname(os.path.abspath(__file__)))

FACE_DATA_PATH = os.environ.get("JARVIS_FACE_DATA", os.path.join(_project_dir, "face_data.pkl"))
SCAN_SECONDS = 4
WATCH_FOLDERS = [
    os.environ.get("JARVIS_WATCH_1", os.path.join(_user_profile, "Downloads")),
    os.environ.get("JARVIS_WATCH_2", os.path.join(_user_profile, "Desktop")),
    os.environ.get("JARVIS_WATCH_3", os.path.join(_user_profile, "Documents")),
    os.environ.get("JARVIS_WATCH_4", os.path.join(_user_profile, "OneDrive")),
]
ALLOWED_EXTENSIONS = [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".txt", ".pptx"]

# tracks if protected file is CURRENTLY open in a window
# cleared as soon as window closes → forces rescan on every new open
currently_open = set()

def lock_pc():
    os.system("rundll32.exe user32.dll,LockWorkStation")

def recognize_face():
    try:
        with open(FACE_DATA_PATH, "rb") as f:
            known_face = pickle.load(f)
    except:
        print("❌ Face data not found")
        return False

    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)

    if face_cascade.empty():
        print("❌ Failed to load cascade")
        return False


    cam = cv2.VideoCapture(0)
    time.sleep(1)

    for _ in range(5):
        cam.read()

    recognized = False
    start_time = time.time()
    print(f"📸 Scanning face for {SCAN_SECONDS} seconds...")

    while (time.time() - start_time) < SCAN_SECONDS:
        ret, frame = cam.read()
        if not ret:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            face_img = gray[y:y+h, x:x+w]
            face_img = cv2.resize(face_img, (200, 200))
            result = cv2.matchTemplate(face_img, known_face, cv2.TM_CCOEFF_NORMED)
            score = result[0][0]
            print(f"Match score: {score:.2f}")
            if score > 0.5:
                recognized = True
                break
        if recognized:
            break

    cam.release()
    cv2.destroyAllWindows()
    return recognized


def trigger_scan(key):
    """Called when a protected file is newly opened"""
    if key in currently_open:
        return  # already open in this session, don't rescan while same window is open

    print(f"\n🚨 Protected file opened: {key}")
    print("🔒 Initiating face scan...")
    currently_open.add(key)  # mark as open

    verified = recognize_face()

    if verified:
        print("✅ Identity confirmed — access granted")
        # stays in currently_open until window closes
    else:
        print("❌ Face not recognised — locking PC")
        currently_open.discard(key)  # remove so it scans again after unlock
        lock_pc()


def get_all_window_title():
    titles=set()
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title=win32gui.GetWindowText(hwnd)
            if title:
                titles.add(title.lower())
    win32gui.EnumWindows(callback,None)
    return titles

# ── Window watcher — detects open AND close ──────────────────────────
def watch_active_window():
    print("👁  Window watcher started (win32gui)")
    # prev_titles = set()

    while True:
        try:
            # get ALL open window titles (not just active)
            all_titles = {w.title.lower() for w in gw.getAllWindows() if w.title}

            for protected in PROTECTED_FILES:
                key = f"window_{protected}"
                is_visible = any(protected.lower() in t for t in all_titles)

                if is_visible and key not in currently_open:
                    # file just opened → trigger scan
                    threading.Thread(target=trigger_scan, args=(key,), daemon=True).start()

                elif not is_visible and key in currently_open:
                    # window closed → clear from set so NEXT open triggers scan again
                    print(f"📂 '{protected}' window closed — will rescan on next open")
                    currently_open.discard(key)

        except Exception as e:
            print(f"WIndow watcher error: {e}")

        time.sleep(1)


# ── Watchdog for file system events (renames, new files) ─────────────
class FileGuardHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        if event.is_directory:
            return
        filepath = event.src_path.lower()
        _, ext = os.path.splitext(filepath)
        if ext not in ALLOWED_EXTENSIONS:
            return
        basename = os.path.basename(filepath)
        for protected in PROTECTED_FILES:
            if protected.lower() in basename:
                threading.Thread(
                    target=trigger_scan,
                    args=(filepath,),
                    daemon=True
                ).start()


# ── Start everything ─────────────────────────────────────────────────
handler = FileGuardHandler()
observer = Observer()
for folder in WATCH_FOLDERS:
    if os.path.exists(folder):
        observer.schedule(handler, folder, recursive=True)
        print(f"👁  Watching: {folder}")
observer.start()

window_thread = threading.Thread(target=watch_active_window, daemon=True)
window_thread.start()

print("\n🛡️  File Guard running")
print(f"   Protected: {PROTECTED_FILES}")
print("   Press Ctrl+C to stop\n")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
    print("\n🛑 File Guard stopped")

observer.join()