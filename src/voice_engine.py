import asyncio
import json
import re
import shutil
import tempfile
from pathlib import Path
import edge_tts
from edge_tts.exceptions import NoAudioReceived
from mutagen.mp3 import MP3
from src.emotion_parser import SpeechSegment


async def _synthesize_with_retry(text: str, voice: str, rate: str, pitch: str, out_file: Path) -> bool:
    attempts = [
        (rate, pitch),
        (rate, pitch),
        ("+0%", "+0Hz"),
    ]
    for i, (r, p) in enumerate(attempts):
        try:
            communicate = edge_tts.Communicate(text=text, voice=voice, rate=r, pitch=p)
            await communicate.save(str(out_file))
            if out_file.exists() and out_file.stat().st_size > 0:
                return True
        except NoAudioReceived:
            if i == len(attempts) - 1:
                return False
        except Exception:
            if i == len(attempts) - 1:
                raise
        await asyncio.sleep(0.6 * (i + 1))
    return False


async def render_page_audio(segments: list[SpeechSegment], output_path: Path) -> list[dict]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    timeline: list[dict] = []
    current_sec = 0.0

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        merged_tmp = tmp_path / "merged.mp3"
        with open(merged_tmp, "wb") as out_f:
            for idx, seg in enumerate(segments):
                clean_spoken = seg.text.strip("\"\u201c\u201d'\u2018\u2019 ")
                if not clean_spoken or not re.search(r"[^\W_]", clean_spoken, re.UNICODE):
                    continue

                part_file = tmp_path / f"part_{idx}.mp3"
                ok = await _synthesize_with_retry(clean_spoken, seg.voice, seg.rate, seg.pitch, part_file)
                if not ok:
                    continue

                duration = MP3(str(part_file)).info.length
                out_f.write(part_file.read_bytes())

                timeline.append({
                    "id": len(timeline),
                    "text": seg.text,
                    "role": seg.role,
                    "start": round(current_sec, 3),
                    "end": round(current_sec + duration, 3),
                })
                current_sec += duration

        if not timeline:
            return []

        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(merged_tmp), str(output_path))

    meta_path = output_path.with_suffix(".json")
    meta_path.write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")
    return timeline
