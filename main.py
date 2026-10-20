import pyttsx3
import speech_recognition as sr
import webbrowser
import datetime
import requests
from groq import Groq
import os
import threading
import tkinter as tk
# import pytesseract
from PIL import ImageGrab
import keyboard
import base64
import io
import spotipy
from spotipy.oauth2 import SpotifyOAuth
# import pywhatkit as kit
import subprocess
import psutil
import pyautogui
import json
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
import cv2
import pickle
import glob
import pyperclip
import time
from jarvis_gui import launch_gui, get_gui
from dotenv import load_dotenv

load_dotenv()

# Load API keys from environment variables (set these in a .env file or your system environment)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
# gemini_client=genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
# recognizer = sr.Recognizer()

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
    client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
    redirect_uri="http://127.0.0.1:9090/callback",
    scope="user-modify-playback-state user-read-playback-state"
))

conversation_history=[]
def speak(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 200)
    engine.setProperty('volume', 1)
    engine.say(text)
    engine.runAndWait()
    engine.stop()

def recognize_face():
    try:
        with open("face_data.pkl","rb") as f:
            known_face=pickle.load(f)
    except:
        speak("Face data not found")
        return False
    
    face_cascade=cv2.CascadeClassifier(cv2.data.haarcascades+'haarcascade_frontalface_default.xml')
    cam=cv2.VideoCapture(0)
    attempts=0
    print("📸 Scanning face...")

    while attempts<30:
        ret,frame=cam.read()
        if not ret:
            attempts+=1
            continue
        gray=cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces=face_cascade.detectMultiScale(gray,1.3,5)

        for (x,y,w,h) in faces:
            face_img=gray[y:y+h,x:x+w]
            face_img=cv2.resize(face_img,(200,200))
            result=cv2.matchTemplate(face_img,known_face,cv2.TM_CCOEFF_NORMED)
            score=result[0][0]
            print(f"Match Score: {score: .2f}")
            if score>0.6:
                cam.release()
                cv2.destroyAllWindows()
                return True
            
        attempts+=1
    cam.release()
    cv2.destroyAllWindows()
    return False

def face_watcher():
    global active
    print("📸 Face watcher active")
    while True:
        if active:
            import time
            time .sleep(2)
            continue

        recongized=recognize_face()
        if recongized and not active:
            active= True
            speak("Face recognised! Welcome back sir, jarvis activated")
            print("Activated by face")


def open_application(app_name):
    user_profile = os.environ.get("USERPROFILE", "C:/Users/YourUsername")
    apps = {
        "chrome": "C:/Program Files/Google/Chrome/Application/chrome.exe",
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "spotify": f"{user_profile}/AppData/Roaming/Spotify/Spotify.exe",
        "vscode": f"{user_profile}/AppData/Local/Programs/Microsoft VS Code/Code.exe",
        "explorer": "explorer.exe",
        "task manager": "taskmgr.exe",
        "whatsapp": f"{user_profile}/AppData/Local/WhatsApp/WhatsApp.exe",
        "word": "winword.exe",
        "excel": "excel.exe",
        "powerpoint": "powerpnt.exe",
        "cmd": "cmd.exe",
    }
    app=app_name.lower()
    if app in apps:
        subprocess.Popen(apps[app])
        return f"Opening {app_name}"
    else:
        try:
            subprocess.Popen(app_name)
            return f"Opening {app_name}"
        except:
            return f"Sorry, I couldn't find {app_name}"
def get_battery():
    battery=psutil.sensors_battery()
    if battery:
        percent=battery.percent
        charging="and charging" if battery.power_plugged else "and not charging"
        return f"battery is at {percent}% {charging}"
    return "Couldn'tget battery info"

def get_system_info():
    cpu=psutil.cpu_percent(interval=1)
    ram=psutil.virtual_memory()
    battery=psutil.sensors_battery()
    bat=f"{battery.percent}%" if battery else " N/A"
    return f"CPU usage is {cpu}%, RAM usage is {ram.percent}%, Battery is {bat}"

def set_volume(level):
    try:
        level = max(0, min(100, int(level)))
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        return f"Volume set to {level}%"
    except Exception as e:
        print(f"Volume error: {e}")
        return f"Couldn't set volume: {e}"

def take_screenshot(filename="Screenshots"):
    filename = filename.replace(".png", "")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    user_profile = os.environ.get("USERPROFILE", "C:/Users/YourUsername")
    screenshots_dir = os.environ.get("JARVIS_SCREENSHOTS_DIR", f"{user_profile}/Pictures/Screenshots")
    path = f"{screenshots_dir}/{filename}_{timestamp}.png"
    screenshot = ImageGrab.grab()
    screenshot.save(path)
    return f"screenshot saved to {filename}_{timestamp}.png"


def shutdown_pc(timer=0):
    if timer==0:
        os.system("shutdown /s /t 0")
        return "shutting down PC now"
    else: 
        os.system(f"shutdown /s /t {timer *60}")
        return f"PC will shutdown in {timer} minutes"

def restart_pc():
    os.system("shutdown /r /t 0")
    return "Restarting PC now"


def lock_pc():
    os.system("rundll32.exe user32.dll,LockWorkStation")
    return "PC locked"

def cancel_shutdown():
    os.system("shutdown /a")
    return "Shutdown cancelled"

def open_website(url):
    if not url.startswith("http"):
        url="https://"+url
    webbrowser.open(url)
    return f"Opening {url}"

def search_google(query):
    webbrowser.open(f"https://www.google.com/search?q={query}")
    return f"searching Google for {query}"

def search_youtube(query):
    webbrowser.open(f"https://youtube.com/results?search_query={query}")
    return f"searching YouTube for {query}"

def get_weather():
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    loc=requests.get("http://ip-api.com/json/").json()
    city=loc["city"]
    url=f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    data=requests.get(url).json()
    temp=data["main"]["temp"]
    desc=data["weather"][0]["description"]
    return f"Current temperature in {city} is {temp}°C with {desc}"

def get_time():
    return datetime.datetime.now().strftime("%I:%M %p")

def get_date():
    return datetime.datetime.now().strftime("%A,%B %d, %Y")

def type_text(text):
    pyautogui.typewrite(text,interval=0.05)
    return f"Typed: {text}"



def spotify_play(song_name):
    try:
        results=sp.search(q=song_name,limit=1,type="track")
        tracks=results["tracks"]["items"]
        if tracks:
            uri=tracks[0]["uri"]
            sp.start_playback(uris=[uri])
            return f"Playing {tracks[0]['name']} by {tracks[0]['artists'][0]['name']}"
        return "song not found on Spotify"
    except Exception as e:
        return f"Spotify error: {e}"
    

def spotify_pause():
    sp.pause_playback()
    return " Music paused"

def spotify_resume():
    sp.start_playback()
    return "Music resumed"

def spotify_next():
    sp.next_track()
    return "Playing next track"

def spotify_previous():
    sp.previous_track()
    return "Playing previous track"

def spotify_volume(level):
    sp.volume(level)
    return f"spotify volume set to {level}%"

def save_note(note):
    try:
        user_profile = os.environ.get("USERPROFILE", "C:/Users/YourUsername")
        notes_path = os.environ.get("JARVIS_NOTES_PATH", f"{user_profile}/Desktop/jarvis_notes.txt")
        timestamp=datetime.datetime.now().strftime("%d-%m-%y %I:%M %p")

        with open(notes_path,"a") as f:
            f.write (f"[{timestamp}]{note}\n")

        return f"Note saved: {note}"
    except Exception as e:
        return f"couldn't save note: {e}"
    
def read_notes():
    try:
        user_profile = os.environ.get("USERPROFILE", "C:/Users/YourUsername")
        notes_path = os.environ.get("JARVIS_NOTES_PATH", f"{user_profile}/Desktop/jarvis_notes.txt")

        if not os.path.exists(notes_path):
            return "No notes found"
        with open(notes_path,"r") as f:
            content=f.read()
            if not content:
                return "Notes file is empty"
            
            lines=[l for l in content.splitlines() if l.strip()]
            last_5=lines[-5:]
            return "your recent notes: "+"|". join(last_5)
    except Exception as e:
        return f"couldn't read notes: {e}"
    
def open_notes():
    try:
        user_profile = os.environ.get("USERPROFILE", "C:/Users/YourUsername")
        notes_path = os.environ.get("JARVIS_NOTES_PATH", f"{user_profile}/Desktop/jarvis_notes.txt")
        if not os.path.exists(notes_path):
            with open(notes_path,"w") as f:
                f.write("--- JARVIS NOTES---\n")
        os.startfile(notes_path)
        return "Opening notes file"
    except Exception as e:
        return f"coildn't open notes: {e}"
    
def clear_notes():
    try:
        user_profile = os.environ.get("USERPROFILE", "C:/Users/YourUsername")
        notes_path = os.environ.get("JARVIS_NOTES_PATH", f"{user_profile}/Desktop/jarvis_notes.txt")
        with open(notes_path,"w") as f:
            f.write("---jarivs notes---\n")
        return "Notes cleared"
    except Exception as e:
        return f" couldn't clear notes: {e}"


def list_files(path=None):
    if path is None:
        user_profile = os.environ.get("USERPROFILE", "C:/Users/YourUsername")
        path = f"{user_profile}/Downloads"
    try:
        files=os.listdir(path)
        return "Files: "+",".join(files[:10])
    except:
        return f"Couldn't access {path}"

protected_files=[
    
]

def find_and_open_file(filename):
    user_profile = os.environ.get("USERPROFILE", "C:/Users/YourUsername")
    project_dir = os.environ.get("JARVIS_PROJECT_DIR", "C:/jarvis")
    search_paths = [
        f"{user_profile}/Desktop",
        f"{user_profile}/Downloads",
        f"{user_profile}/Documents",
        f"{user_profile}/OneDrive",
        f"{user_profile}/Pictures",
        f"{user_profile}/Music",
        f"{user_profile}/Videos",
        project_dir,
    ]

    found_files=[]

    for path in search_paths:
        matches=glob.glob(f"{path}/**/*{filename}*",recursive=True)
        found_files.extend(matches)

    if found_files:
        os.startfile(found_files[0])
        return f"Opening{found_files[0]}"
    else:
        return f"No file named'{filename} found on your PC"
    

def shutdown_jarvis():
    speak("Shutting down completely. Goodbye Sir!")
    os._exit(0)

def sleep_jarvis():
    return "SLEEP"

"""TOOLS DEFINATION FOR GROQ"""
tools=[
    {
        "type":"function",
        "function":{
            "name":"open_application",
            "description": "Open any application on the PC like chrome, spotify, VS code, whatsapp, Word , Excel etc. ",
            "parameters":{
                "type": "object",
                "properties": {
                    "app_name":{"type": "string","description":"name of the app to open e.g. chrome, notepad, spotify"}   
                },
                "required": ["app_name"]

            }
        }
    },
    {
        "type":"function",
        "function":{
            "name": "get_battery",
            "description": "Get current battery percentage and charging status",
            "parameters": {"type": "object", "properties":{}}
        }
    },
    {
        "type":"function",
        "function":{
            "name":"get_system_info",
            "description":"get CPU, RAM and battery info",
            "parameters": {"type":"object","properties":{}}
        }
    },
    {
        "type":"function",
        "function":{
            "name":"set_volume",
            "description":"set the system volume to a speccific level ",
            "parameters": {
                "type": "object",
                "properties":{
                    "level": {"type":"integer","description":"Volume level from 0 to 100"}
                },
                "required":["level"]
            }
        }
    },
    {
        "type":"function",
        "function":{
            "name": "take_screenshot",
            "description":"take screenshot of the current screen and save it",
            "parameters":{
                "type":"object",
                "properties":{
                    "filename":{"type":"string","description":"name to save the screenshot as"}
                }
            }
        }
    },
    {
        "type":"function",
        "function":{
            "name":"shutdown_pc",
            "description":"Shutdown the PC immediattely or after a timer in minutes, if there's a work pc or laptop after or before the shutdown",
            "parameters":{
                "type":"object",
                "properties":{
                    "timer":{"type":"integer","description":"number of minutes before shutdown. must be a whole number like 0,1,5,10. default is 0 for immediate shutdown"}
                }
            }
        }
    },
    {
        "type": "function",
        "function":{
            "name": "restart_pc",
            "description":"Restart the PC",
            "parameters":{"type":"object","properties":{}}
        }
    },
    {
        "type":"function",
        "function":{
            "name":"lock_pc",
            "description":"lock the PC screen",
            "parameters":{"type":"object","properties":{}}
        }
    },
    {
        "type":"function",
        "function":{
            "name":"cancel_shutdown",
            "description":"Cancel a shutdown PC shutdown",
            "parameters": {"type": "object","properties":{}}
        }
    },
    {
        "type":"function",
        "function":{
            "name":"open_website",
            "description":"Open any website in the browser",
            "parameters":{
                "type": "object",
                "properties":{
                    "url":{"type":"string","description":"Website URL e.g. youtube.com"}
                },
                "required":["url"]
            }
        }
    },
    {
        "type":"function",
        "function":{
            "name":"search_google",
            "description": "Search something on Google",
            "parameters":{
                "type":"object",
                "properties":{
                    "query":{"type":"string","description":"The search query"}
                },
                "required":["query"]
            }
        }
    },
    {
        "type":"function",
        "function":{
            "name":"search_youtube",
            "description":"Search for video on youtube",
            "parameters":{
                "type":"object",
                "properties":{
                    "query":{"type":"string","description":"The search query"}
                },
                "required":["query"]
            }
        }
    },
    {
        "type":"function",
        "function":{
            "name":"get_time",
            "description":"Get the current time",
            "parameters":{"type":"object","properties":{}}
        }
    },
    {
        "type":"function",
        "function":{
            "name":"get_weather",
            "description":"Get current weather of user's location",
            "parameters":{"type":"object","properties":{}}
        }
    },
    {
        "type":"function",
        "function":{
            "name":"get_date",
            "description":"Get today's date",
            "parameters":{"type":"object","properties":{}}
        }
    },
    {
        "type":"function",
        "function":{
            "name":"type_text",
            "description":"Automatically type any text using the keyboard",
            "parameters":{
                "type":"object",
                "properties":{
                    "text":{"type":"string","description":"The text to type"}
                },
                "required":["text"]
            }
        }
    },

    {
        "type":"function",
        "function":{
            "name":"spotify_play",
            "description":"play a specific song on spotify",
            "parameters":{
                "type": "object",
                "properties":{
                    "song_name":{"type":"string","description":"Name of the song to play"}
                },
                "required":["song_name"]
            }
        }
    },
    {
        "type":"function",
        "function":{
            "name":"spotify_resume",
            "description":"Resume paused Spotify music",
            "parameters":{"type":"object","properties":{}}
        }
    },
    {
        "type":"function",
        "function":{
            "name":"spotify_pause",
            "description":"Pause Spotify music",
            "parameters":{"type":"object","properties":{}}
        }
    },
    {
        "type":"function",
        "function":{
            "name":"spotify_next",
            "description":"Skip to next track on Spotify",
            "parameters":{"type":"object","properties":{}}
        }
    },
    {
        "type":"function",
        "function":{
            "name":"spotify_previous",
            "description":"Go to previous track on Spotify",
            "parameters":{"type":"object","properties":{}}
        }
    },
    {
        "type":"function",
        "function":{
            "name":"spotify_volume",
            "description":"Set Spotify playback volume",
            "parameters":{
                "type":"object",
                "properties":{
                    "level":{"type":"integer","description":"Volume level from 0 to 100"}
                },
            "required":["level"]
            }
        }
    },
    {
        "type":"function",
        "function":{
            "name":"list_files",
            "description":"List files in a folder on the PC",
            "parameters":{
                "type":"object",
                "properties":{
                    "path":{"type":"string","description":"Folder path to list"}
                }
            }
        }
    },
    {
        "type":"function",
        "function":{
            "name":"shutdown_jarvis",
            "description":"Completely quit and exit Jarvis forever until manually restarted. User says or exit jarvis or quit jarvis",
            "parameters":{"type":"object","properties":{}}
        }
    },
    {
        "type":"function",
        "function":{
            "name":"sleep_jarvis",
            "description":"Put jarvis to sleep, stop listening until woke nup again by saying jarvis",
            "parameters":{"type":"object","properties":{}}
        }
    },
    {
        "type":"function",
        "function":{
            "name":"find_and_open_file",
            "description":"Search for any file by name on the PC and open it automatically. Use when user says open a file, find a file, or wants to access any document, image,video etc.",
            "parameters":{
                "type":"object",
                "properties":{
                    "filename":{
                        "type":"string",
                        "description":"Name or partial name of the file to search e.g. 'heart','resume','notes'"
                    }
                },
                "required":["filename"]
            }
        }
    },
    {
        "type":"function",
        "function":{
            "name":"save_note",
            "description":"Save a note or reminder ro the notes file. use whe nuser says write this down, note this , remember this , add to notes",
            "parameters":{
                "type":"object",
                "properties":{
                    "note":{
                        "type":"string",
                        "description":"The text content to save in the notes"
                    }
                },
                "required":["note"]
            }
        }
    },
    {
        "type":"function",
        "function":{
            "name":"read_notes",
            "description":"Read the last 5 saved notes. Use when user says read my notes, what are my notes , show notes",
            "parameters":{"type":"object","properties":{}}
        }
    },
    {
        "type":"function",
        "function":{
            "name":"open_notes",
            "description":"Open the notes file on screen. use when user says open notes, show me the notes file",
            "parameters":{"type":"object","properties":{}}
        }
    },
    {
        "type":"function",
        "function":{
            "name":"clear_notes",
            "description":"CLear all notes. Use we nuser says delete notes, clear notes, empty notes",
            "parameters":{"type":"object","properties":{}}
        }
    },
    {
    "type":"function",
    "function":{
        "name":"analyze_code",
        "description":"Analyze code from clipboard or screen. Use when user says: explain this code, fix this error, optimize this code, explain line by line, convert to C, check complexity.",
        "parameters":{
            "type":"object",
            "properties":{
                "intent":{
                    "type":"string",
                    "description":"What to do: explain / fix / optimize / line by line / convert / complexity"
                }
            },
            "required":["intent"]
        }
    }
},
]


"""FUNCTION MAP"""
function_map={
    "spotify_play":         lambda args: spotify_play(args["song_name"]),
    "open_application":     lambda args: open_application(args["app_name"]),
    "spotify_volume":       lambda args: spotify_volume(args["level"]),
    "set_volume":           lambda args: set_volume(args["level"]),
    "take_screenshot":      lambda args: take_screenshot(args.get("filename","screenshot")),
    "list_files":           lambda args: list_files(args.get("path", None)),
    "find_and_open_file":   lambda args: find_and_open_file(args["filename"]),
    "type_text":            lambda args: type_text(args["text"]),
    "analyze_code":         lambda args: analyze_code(args.get("intent","explain")),
    "shutdown_pc":          lambda args: shutdown_pc(int(args.get("timer",0))),
    "save_note":            lambda args: save_note(args["note"]),
    "open_website":         lambda args: open_website(args["url"]),
    "search_youtube":       lambda args: search_youtube(args["query"]),
    "search_google":        lambda args: search_google(args["query"]),
    "get_battery":          lambda args: get_battery(),
    "get_system_info":      lambda args: get_system_info(),
    "restart_pc":           lambda args: restart_pc(),
    "lock_pc":              lambda args: lock_pc(),
    "cancel_shutdown":      lambda args: cancel_shutdown(),
    "get_weather":          lambda args: get_weather(),
    "get_time":             lambda args: get_time(),
    "get_date":             lambda args: get_date(),
    "spotify_pause":        lambda args: spotify_pause(),
    "spotify_resume":       lambda args: spotify_resume(),
    "spotify_next":         lambda args: spotify_next(),
    "spotify_previous":     lambda args: spotify_previous(),
    "shutdown_jarvis":      lambda args: shutdown_jarvis(),
    "sleep_jarvis":         lambda args: sleep_jarvis(),
    "read_notes":           lambda args: read_notes(),
    "open_notes":           lambda args: open_notes(),
    "clear_notes":          lambda args: clear_notes(),

}


"""AI agent processor"""
def process_with_agent(command):
    conversation_history.append({"role":"user","content":command})

    response=client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role":"system",
                "content":(
                    "you are jarvis, a smart and witty AI assistant."
                    "Use tools whenever possible to perform actionson my PC."
                    "keep spoken responses short- 3to 4 lines max."
                )
            }
        ]+ conversation_history,
        tools=tools,
        tool_choice="auto",
        temperature=0.7,
    )

    message=response.choices[0].message

    if message.tool_calls:
        for tool_call in message.tool_calls:
            func_name=tool_call.function.name
            args=json.loads(tool_call.function.arguments)
            print(f"🔧 calling: {func_name} with {args}")

            # result=function_map[func_name](args)
            # print(f"✅ Result: {result}")

            if func_name=="shutdown_jarvis":
                shutdown_jarvis()

            if func_name=='sleep_jarvis':
                speak("Going to sleep sir, call me when nyou need me ")
                return "sleep"
            
            result=function_map[func_name](args)
            print(f"✅ Result: {result}")

            speak(result)
            gui=get_gui()
            if gui: gui.add_message("jarvis",result)
            if gui: gui.set_status("LISTENING")
            conversation_history.append({"role": "assistant","content": str(result)})
            return result
        conversation_history.append({"role":"assistant","content":str(result)})
        return result[0] if result else None
        
    else:
        reply=message.content.strip()
        conversation_history.append({"role":"assistant", "content":reply})
        speak(reply)
        return reply
        

"""---SCREEN OVERLAY---"""
def show_overlay(answer_text):
    overlay=tk.Tk()#creates a window with no title text
    overlay.title("")
    overlay.attributes("-topmost",True)#forces the window to always stay on top of every otgher app- so it shows even on your browswer or game
    overlay.attributes("-alpha", 0.5)#maintains opacity of the window
    overlay.overrideredirect(True)#removes the default windows tirle bar and border- makes it look like a clean floationg popup instead of a normal window
    overlay.configure(bg="#ffffff")#background colour(here- dark navy)

#gets your screen size, the ncalculates wherre to place the box so it appears centers horizontally and 60 pixels from the bottom of your screen
    screen_w =overlay.winfo_screenwidth()
    screen_h=overlay.winfo_screenheight()
    width,height=800,280
    x=(screen_w-width)//2
    y=screen_h-height-60
    overlay.geometry(f"{width}x{height}+{x}+{y}")


#adds the jarvis headerd text in blue ar the top left
    tk.Label(
        overlay, text="🤖 JARVIS",
        font=("Consolas",10,"bold"),
        bg="#ffffff", fg="#89b4fa"
    ).pack(anchor="w", padx=16,pady=(10,0))

#shows the actual answer (wraplength=760) means if the answer is long, it wraps onto the next line instead of going off screen.
    tk.Label(
        overlay, text=answer_text,
        font=("Consolas",13),
        bg="#FFF5F5", fg="#000206",
        wraplength=760, justify="left"
    ).pack(padx=16,pady=(4,10))


#adds a close button at the bottom right. (command=overaly.destroy) means clicking it cloases the window immediaterl
    tk.Button(
        overlay, text="✕  close",
        command=overlay.destroy,
        font=("Consolas",9),
        bg="#FFFFFF", fg="#e886a3",
        relief="flat", cursor="hand2"
    ).pack(anchor="e",padx=16,pady=(0,10))


    overlay.after(10000,overlay.destroy)#automatically closes the overlay after 15 seconds(15000 mili seconds) even if you don't click close
    overlay.mainloop()#keeps the window open and responsive until it's closed- without te window would flash and disappear instantaly



""""SCREEN READER"""

def read_screen_and_answer():
    print("📸 Taking screenshot...")
    screenshot = ImageGrab.grab()
    buffer = io.BytesIO()
    screenshot.save(buffer, format="PNG")
    image_data = base64.b64encode(buffer.getvalue()).decode("utf-8")

    response = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_data}"}
                },
                {
                    "type": "text",
                    "text": (
                        "You are an expert in electronics, computer science and coding. "
                        "Analyze this screenshot carefully and find ALL questions visible. "

                        "FOR MCQ QUESTIONS (most important): "
                        "- Read all options very carefully "
                        "- Think step by step which option is correct "
                        "- Give ONLY the correct option like: 'Q1: (B) NPN Transistor' "
                        "- Never explain why, just the answer "

                        "FOR THEORETICAL QUESTIONS: "
                        "- Give a crisp 2 line answer max "
                        "- Only key information, no fluff "

                        "FOR CODING QUESTIONS: "
                        "- Give the correct code or output directly "

                        "RULES: "
                        "- If multiple questions visible, answer each on new line "
                        "- Never repeat the question "
                        "- Never say 'The answer is' just give the answer directly "
                        "- Be confident, no maybe or probably "
                    )
                }
            ]
        }]
    )
    answer = response.choices[0].message.content.strip()
    print(f"✅ Answer: {answer}")
    threading.Thread(target=show_overlay, args=(f"Ans: {answer}",), daemon=True).start()


def analyze_code(intent="explain"):
    try:
        code=pyperclip.paste().strip()
    except:
        code=""
    if code and len(code)>10:
        source="clipboard"
        content=[{"type":"text","text":f"Code\n'''\n{code}\n'''"}]
    else:
        source="screenshot"
        screenshot=ImageGrab.grab()
        buffer=io.BytesIO()
        screenshot.save(buffer, format="PNG")
        image_data= base64.b64encode(buffer.getvalue()).decode("utf-8")
        content=[
            {
                "type":"image_url",
                "url": f"data:image/png;base64,{image_data}"
            }
        ]
    print(f" source:{source}")

    prompts={
        "explain":      "explain what this code clearly and concisely. Civer the logic and purpse",
        "fix":          "find all bugs and errors. Show the coorected e=with a brief explaination of what was wrong.",
        "optimize":     "suggest a faster or cleaner version of this code. Show the improved code.",
        "line by line": "Explain this code line by line. keep each explaination brief",
        "convert":      "convert this code to C. keep the same logic.",
        "complexity":   "analyze the time and spacee complexity of this code. GIve Big O notation",
    }
    prompt_text=prompts.get(intent, f"Analyse this codeand help with: {intent}")
    content.append({"type":"text","text":prompt_text})

    response=client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[{"role":"user","content":content}]
    )

    answer=response.choices[0].message.content.strip()
    threading.Thread(target=show_overlay,args=(answer,),daemon=True).start()
    speak(f"Done. Check the overlay for the {intent} analysis.")

    






"""---HOTKEY SETUP---"""

def setup_hotkey():
    print("⌨  Hotkey active: Press Ctrl+x to read screen")
    keyboard.add_hotkey("ctrl+x",read_screen_and_answer)#registerss the hotkey (ctrl+z       ) globally - meaning whwnever you press it, no matter what app you're in, it will  call (read_secreen_and_answer) automatically.
    keyboard.wait()





if __name__ == "__main__":
    speak("initializing jarvis..")
    gui_thread=threading.Thread(target=launch_gui,daemon=True)
    gui_thread.start()
    time.sleep(1.2)
    guard_path = os.environ.get("JARVIS_PROJECT_DIR", os.path.dirname(os.path.abspath(__file__)))
    guard_path = os.path.join(guard_path, "file_guard.py")
    subprocess.Popen(
        ["python",guard_path],
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    print("file guard started")

    

    hotkey_thread=threading.Thread(target=setup_hotkey, daemon=True)
    hotkey_thread.start()

    face_thread=threading.Thread(target=face_watcher,daemon=True)
    face_thread.start()


    active = False
    while True:
        r = sr.Recognizer()
        # print("recognizing..")
        try:
            with sr.Microphone() as source:
                print("listening...!")
                audio = r.listen(source, timeout=3)
            word = r.recognize_google(audio)
            gui=get_gui()
            if gui: gui.add_message("you",word)
            if gui: gui.set_status("ACTIVE")
            print(word)
            if word.lower() == "jarvis" and not active:
                active = True
                speak("yes sir")
            elif active:
                result = process_with_agent(word)
                if result and result.lower() == "sleep":
                    active = False

        except sr.WaitTimeoutError:
            continue

        except sr.UnknownValueError:
            continue

        except sr.RequestError as e:
            print(f"Speech recognition error: {e}")

        except Exception as e:
            print(f"Unexpected error: {e}")



"""working of pillow library: it bascially make the python so that it can take the image of the screen'

working of tessaract library: it's an OCR(Optical Character Recognition) engine used to read the text from the image. 
it bascicallt converts pixels to text. working with pillow both make a readable page

working of keyboard library: it detects hotkey to give command 
like currently if i press alt+space my gpt opens on the screen 


So the full flow is: Keyboard detects your hotkey → Pillow takes the screenshot → Tesseract reads the text → Groq answers the question → overlay shows the answer.

os._exit(0)   "I shut down successfully, no errors"
os._exit(1)   "I shut down because something went wrong"
"""
