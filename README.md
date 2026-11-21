cd ~/Desktop/ai-audiobook-reader && cat << 'EOF' > README.md
# 🎧 AI Emotional Audiobook Reader

> **🌐 Live Demo:** [https://ai-audiobook-reader.onrender.com](https://ai-audiobook-reader.onrender.com)  
> *(Note: Hosted on Render's free tier—initial load may take ~30–40 seconds if the server is waking from sleep.)*

An AI-powered full-stack web application that converts static PDF books into **expressive, emotion-aware audiobooks** with automatic narrator gender matching, multilingual neural voices, pre-fetched page streaming, and persistent reading progress.

---

## ✨ Key Features

- **🎭 Context-Aware Emotional Narration (`emotion_parser.py`):** Dynamically analyzes sentence sentiment, punctuation, and dialogue cues to adjust vocal pitch, speaking rate, and tone—eliminating flat robotic reading.
- **🎙️ Automatic Author & Narrator Voice Matching (`author_detector.py`):** Extracts author metadata from uploaded PDFs and automatically pairs female authors with natural female neural voices (e.g., `en-GB-SoniaNeural`) and male authors with male voices.
- **🌍 Multilingual Neural TTS Support (`voice_engine.py`):** Supports English alongside regional Indian languages including **Marathi** (`mr-IN-AarohiNeural`, `mr-IN-ManoharNeural`) and **Hindi** via Microsoft Edge Neural TTS (`edge-tts`).
- **⚡ Zero-Lag Page Pre-Fetching & Auto-Advance:** Synthesizes page `N+1` audio asynchronously in the background while page `N` plays, ensuring seamless, hands-free chapter transitions.
- **📚 Library Management & Auto-Resume (`database.py`):** Stores uploaded books, extracted page counts, and exact last-read page positions in **SQLite** so users can pick up right where they left off.
- **📱 Mobile-First Progressive Web Experience:** Configured with mobile web-app meta tags so users can add the live URL to their Android/iOS home screen and listen like a native mobile app.

---

## 🏗️ System Architecture & Pipeline

```text
[PDF Upload (Frontend)] 
        │
        ▼
[FastAPI Backend (app.py)]
        ├──► 1. PyMuPDF (pdf_reader.py)      ──► Extracts clean page-by-page text & metadata
        ├──► 2. Author Detector              ──► Infers author gender & selects default neural voice
        ├──► 3. Emotion Parser               ──► Segments text & maps mood tags (rate/pitch prosody)
        ├──► 4. Edge-TTS Engine              ──► Generates MP3 audio + pre-fetches next page
        └──► 5. SQLite Store (database.py)   ──► Persists book catalog & page bookmark state


**Explanation:**

1.Modular Backend Design: Separated concerns across dedicated modules (pdf_reader.py, emotion_parser.py, voice_engine.py, author_detector.py, database.py) so the TTS engine or PDF parser can be swapped independently without touching API routes.

2.Latency Optimization via Pre-Fetching: Because real-time neural TTS synthesis takes 1–3 seconds per page, the backend triggers background audio generation for current_page + 1 as soon as playback starts, making page turns instantaneous for the listener.

3.Resilient File & Process Handling: Implemented atomic cross-device safe file handling and clean Uvicorn port-binding lifecycle management for reliable deployment on containerized Linux environments (Ubuntu & Render).


## 🛠️ Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend Framework** | Python 3, FastAPI, Uvicorn |
| **PDF & Text Processing** | PyMuPDF (`fitz`), Regex / Heuristic NLP |
| **Speech Synthesis** | `edge-tts` (Microsoft Neural Text-to-Speech) |
| **Database** | SQLite3 |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript (HTML5 Audio API + PWA Meta Tags) |
| **Deployment** | GitHub CI/CD, Render Cloud (Singapore Region) |

**Project Structure**
ai-audiobook-reader/
├── app.py                  # FastAPI entry point, REST endpoints & static file serving
├── requirements.txt        # Python dependencies for production deployment
├── launch.sh               # Local Ubuntu startup helper script
├── src/
│   ├── pdf_reader.py       # Page-level text extraction using PyMuPDF
│   ├── author_detector.py  # Author metadata parsing & voice gender mapping
│   ├── emotion_parser.py   # Sentiment/dialogue prosody tagging
│   ├── voice_engine.py     # Async Edge-TTS audio synthesis & caching
│   └── database.py         # SQLite library & reading-progress persistence
└── static/
    └── index.html          # Responsive mobile-ready player UI

Run Locally (Ubuntu / Linux)
Clone the repository:

Bash
git clone [https://github.com/apurva8377/ai-audiobook-reader.git](https://github.com/apurva8377/ai-audiobook-reader.git)
cd ai-audiobook-reader
Create and activate a virtual environment:

Bash
python3 -m venv venv
source venv/bin/activate
Install dependencies:

Bash
pip install -r requirements.txt
Start the FastAPI server:

Bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
Open http://127.0.0.1:8000 in your browser.

## 👩‍💻 Author

**Apurva Vilas Shinde**
- **GitHub:** https://github.com/apurva8377
- **Repository:** https://github.com/apurva8377/ai-audiobook-reader
- **LinkedIn:** https://www.linkedin.com/in/apurva-shinde-149383384
