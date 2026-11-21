import asyncio
import json
import uuid
import shutil
from pathlib import Path
import pymupdf
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.pdf_reader import extract_clean_page
from src.emotion_parser import analyze_page_emotions
from src.voice_engine import render_page_audio
from src.author_detector import detect_author_info
from src.database import init_db, add_book, list_books, get_book, update_progress, delete_book

app = FastAPI(title="AI Emotional Audiobook Reader")

BOOKS_DIR = Path("data/books")
AUDIO_DIR = Path("output/books")
BOOKS_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

init_db()
app.mount("/static", StaticFiles(directory="static"), name="static")


class ProgressPayload(BaseModel):
    page_num: int
    position: float = 0.0
    voice: str | None = None


def get_audio_path(book_id: str, page_num: int, voice: str) -> Path:
    safe_voice = voice.replace("/", "_")
    return AUDIO_DIR / book_id / safe_voice / f"page_{page_num + 1}.mp3"


_PAGE_LOCKS: dict[tuple[str, int, str], asyncio.Lock] = {}


async def generate_if_missing(book_id: str, pdf_path: Path, page_num: int, voice: str) -> tuple[Path | None, list[dict]]:
    lock_key = (book_id, page_num, voice)
    lock = _PAGE_LOCKS.setdefault(lock_key, asyncio.Lock())
    async with lock:
        return await _generate_if_missing_locked(book_id, pdf_path, page_num, voice)


async def _generate_if_missing_locked(book_id: str, pdf_path: Path, page_num: int, voice: str) -> tuple[Path | None, list[dict]]:
    audio_path = get_audio_path(book_id, page_num, voice)
    meta_path = audio_path.with_suffix(".json")

    if audio_path.exists() and audio_path.stat().st_size > 0 and meta_path.exists():
        timeline = json.loads(meta_path.read_text(encoding="utf-8"))
        return audio_path, timeline

    text = extract_clean_page(pdf_path, page_num)
    if not text.strip():
        return None, []

    segments = analyze_page_emotions(text, narrator_voice=voice)
    if not segments:
        return None, []

    timeline = await render_page_audio(segments, audio_path)
    return audio_path, timeline


@app.get("/", response_class=HTMLResponse)
async def serve_home():
    html = Path("static/index.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html, headers={"Cache-Control": "no-store"})


@app.get("/api/library")
async def fetch_library():
    return {"books": list_books()}


@app.post("/api/upload")
async def upload_book(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    book_id = uuid.uuid4().hex[:8]
    pdf_path = BOOKS_DIR / f"{book_id}.pdf"
    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    with pymupdf.open(pdf_path) as doc:
        total_pages = len(doc)

    author_info = detect_author_info(pdf_path, file.filename)
    clean_title = Path(file.filename).stem.replace("_", " ")

    add_book(
        book_id=book_id,
        title=clean_title,
        author=author_info["author"],
        gender=author_info["gender"],
        total_pages=total_pages,
        voice=author_info["recommended_voice"],
    )

    return get_book(book_id)


@app.post("/api/books/{book_id}/progress")
async def save_book_progress(book_id: str, payload: ProgressPayload):
    if not get_book(book_id):
        raise HTTPException(status_code=404, detail="Book not found.")
    update_progress(book_id, payload.page_num, payload.position, payload.voice)
    return {"status": "saved"}


@app.delete("/api/books/{book_id}")
async def remove_book(book_id: str):
    delete_book(book_id)
    pdf_path = BOOKS_DIR / f"{book_id}.pdf"
    if pdf_path.exists():
        pdf_path.unlink()
    audio_folder = AUDIO_DIR / book_id
    if audio_folder.exists():
        shutil.rmtree(audio_folder)
    return {"status": "deleted"}


@app.get("/api/books/{book_id}/page/{page_num}")
async def get_page_data(
    book_id: str,
    page_num: int,
    background_tasks: BackgroundTasks,
    voice: str | None = Query(None),
):
    pdf_path = BOOKS_DIR / f"{book_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Book not found.")

    book_record = get_book(book_id)
    active_voice = voice or (book_record["voice"] if book_record else "en-GB-RyanNeural")

    with pymupdf.open(pdf_path) as doc:
        total_pages = len(doc)
        if page_num < 0 or page_num >= total_pages:
            raise HTTPException(status_code=400, detail="Page out of range.")

    text = extract_clean_page(pdf_path, page_num)
    if any("\u0900" <= ch <= "\u097F" for ch in text) and not active_voice.startswith(("mr-", "hi-")):
        is_fem = book_record and book_record.get("gender") == "female"
        active_voice = "mr-IN-AarohiNeural" if is_fem else "mr-IN-ManoharNeural"
    audio_path, timeline = await generate_if_missing(book_id, pdf_path, page_num, active_voice)

    for offset in (1, 2):
        if page_num + offset < total_pages:
            background_tasks.add_task(generate_if_missing, book_id, pdf_path, page_num + offset, active_voice)

    return {
        "page_num": page_num,
        "total_pages": total_pages,
        "voice_used": active_voice,
        "text": text,
        "has_audio": audio_path is not None,
        "audio_url": f"/api/books/{book_id}/page/{page_num}/audio?voice={active_voice}" if audio_path else None,
        "segments": timeline,
    }


@app.get("/api/books/{book_id}/page/{page_num}/audio")
async def stream_page_audio(book_id: str, page_num: int, voice: str = Query("en-GB-RyanNeural")):
    audio_path = get_audio_path(book_id, page_num, voice)
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio not ready yet.")
    return FileResponse(audio_path, media_type="audio/mpeg", headers={"Cache-Control": "no-store"})
