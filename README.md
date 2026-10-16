# 🤖 J.A.R.V.I.S. – AI Desktop Assistant

J.A.R.V.I.S. is an AI-powered desktop assistant built with Python that combines voice control, desktop automation, computer vision, and LLM-powered tool calling into a single application.

It is designed to automate everyday desktop tasks while providing an intuitive and futuristic user experience.

---

## ✨ Features

* 🎙️ Voice-controlled desktop automation
* 💻 Open applications and websites using natural language
* 🎵 Spotify playback control(with spotify preminum only)
* 📸 Capture screenshots with voice commands
* 👨‍💻 AI-powered code analysis
* 👀 AI Vision screen reader
* 🔐 Face recognition authentication
* 🛡️ File Guard for protecting sensitive documents
* 📝 Smart notes management
* 📂 Search and open files instantly
* 📊 Live CPU, RAM, and Battery monitoring
* 🖥️ Custom futuristic J.A.R.V.I.S. interface

---

## 🛠️ Tech Stack

* Python
* OpenCV
* Tkinter
* SpeechRecognition
* Groq API
* Spotipy
* Watchdog
* Pillow
* PyAutoGUI
* PyCAW
* Pyperclip

---
## 🤖 AI Models

Jarvis uses Groq-hosted AI models for conversational assistance
and visual analysis.

| Function | Model |
|---|---|
| Conversational AI and tool calling | `openai/gpt-oss-120b` |
| Screenshot analysis | `qwen/qwen3.8-27b` |
| Code analysis | `qwen/qwen3.8-27b` |

Model availability and supported capabilities may change.
Check the Groq documentation for current model availability.

## 📂 Project Structure

```text
jarvis-ai-desktop-assistant/
│
├── main.py
├── jarvis_gui.py
├── file_guard.py
├── register_face.py
├── requirements.txt
├── .env.example
├── README.md
├── .gitignore
└── LICENSE
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/AnshulCodes3096/jarvis-ai-desktop-assistant.git
```

### 2. Navigate to the project directory

```bash
cd jarvis-ai-desktop-assistant
```

### 3. Install the required dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` and rename it to `.env`.

Add your own API keys:

```env
GROQ_API_KEY=your_groq_api_key
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
OPENWEATHER_API_KEY=your_openweather_api_key
```

### 5. Register your face

```bash
python register_face.py
```

### 6. Launch J.A.R.V.I.S.

```bash
python main.py
```

---

## 🔮 Future Improvements

* Wake-word detection
* Cross-platform support (Linux & macOS)
* Plugin-based architecture
* Enhanced desktop automation
* Improved GUI animations
* Local AI model support
* Smart reminders and scheduling

---

## 🤝 Contributing

Contributions, ideas, and feature requests are welcome.

If you'd like to contribute:

1. Fork the repository.
2. Create a new feature branch.
3. Commit your changes.
4. Open a Pull Request.

---

## 💻 Platform Support

Jarvis is currently designed for Windows.

Some features depend on Windows-specific APIs and may not
work on Linux or macOS.

## 📄 License

This project is licensed under the MIT License.

---

## 👨‍💻 Author

**Anshul Goyal**

GitHub: https://github.com/AnshulCodes3096
