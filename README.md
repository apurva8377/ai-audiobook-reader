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
