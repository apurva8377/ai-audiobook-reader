import re
from dataclasses import dataclass


@dataclass
class SpeechSegment:
    text: str
    voice: str
    rate: str
    pitch: str
    role: str
    pause_ms: int = 160


SAD_CUES = re.compile(
    r"\b(cry|cried|tears|sob|sobbed|sad|sorrow|grief|lonely|alone|pain|hurt|sigh|sighed|weep|wept|sorry|broken|died|death)\b"
    r"|(दुःख|अश्रू|रडत|रडू|एकटे|वेदना|मृत्यू|हळहळ|खंत)",
    re.IGNORECASE,
)
ANGRY_CUES = re.compile(
    r"\b(shout|shouted|scream|screamed|yell|yelled|angry|furious|rage|hate|damn|shut up|stop it|snapped|roared)\b"
    r"|(राग|रागाने|ओरड|ओरडला|ओरडली|संताप|चिडून|थांब)",
    re.IGNORECASE,
)
WHISPER_CUES = re.compile(
    r"\b(whisper|whispered|murmur|murmured|softly|quietly|secret|afraid|scared|fear|trembled|shivered|hush)\b"
    r"|(हळूच|कुजबुज|घाबर|भीती|शांतपणे|गुपित)",
    re.IGNORECASE,
)
EXCITED_CUES = re.compile(
    r"\b(laugh|laughed|smile|smiled|joy|happy|wonderful|amazing|love|loved|excited|hurray|brilliant|delighted)\b"
    r"|(आनंद|हसला|हसली|खुश|वाह|सुंदर|प्रेम|अप्रतिम)",
    re.IGNORECASE,
)


def _detect_emotion(text: str, context: str, is_dialogue: bool) -> tuple[str, str, str, int]:
    combined = f"{text} {context}"

    if ANGRY_CUES.search(combined) or (text.isupper() and len(text) > 4):
        return "+7%", "+4Hz", "Intense", 200
    if WHISPER_CUES.search(combined) or "..." in text or "…" in text:
        return "-7%", "-4Hz", "Soft / Suspense", 240
    if SAD_CUES.search(combined):
        return "-6%", "-5Hz", "Emotional", 240
    if "!" in text or EXCITED_CUES.search(combined):
        return "+6%", "+5Hz", "Expressive", 180
    if "?" in text:
        return "+2%", "+4Hz", "Question", 180

    if is_dialogue:
        return "+2%", "+1Hz", "Dialogue", 160
    return "+0%", "+0Hz", "Narrator", 140


def analyze_page_emotions(page_text: str, narrator_voice: str = "en-GB-RyanNeural") -> list[SpeechSegment]:
    pattern = r"([\"\u201c].*?[\"\u201d]|(?<!\w)['\u2018].*?['\u2019](?!\w))"
    chunks = re.split(pattern, page_text)
    segments: list[SpeechSegment] = []

    for i, chunk in enumerate(chunks):
        clean_chunk = chunk.strip()
        if not clean_chunk:
            continue

        context = ""
        if i > 0:
            context += " " + chunks[i - 1][-90:]
        if i + 1 < len(chunks):
            context += " " + chunks[i + 1][:90]

        is_dialogue = (
            (clean_chunk[0] in "\"\u201c'\u2018")
            and (clean_chunk[-1] in "\"\u201d'\u2019")
            and len(clean_chunk) > 2
        )

        if is_dialogue:
            spoken = clean_chunk[1:-1].strip()
            if not spoken:
                continue
            rate, pitch, role, pause_ms = _detect_emotion(spoken, context, is_dialogue=True)
            segments.append(SpeechSegment(clean_chunk, narrator_voice, rate, pitch, role, pause_ms))
        else:
            sentences = re.split(r"(?<=[.!?।])\s+", clean_chunk)
            for sent in sentences:
                sent = sent.strip()
                if not sent:
                    continue
                rate, pitch, role, pause_ms = _detect_emotion(sent, "", is_dialogue=False)
                segments.append(SpeechSegment(sent, narrator_voice, rate, pitch, role, pause_ms))

    return segments
