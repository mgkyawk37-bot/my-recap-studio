import streamlit as st
import os
import re
import time
import base64
import subprocess
import tempfile
import asyncio
import requests
import edge_tts
from groq import Groq

# =========================================================
# AI MOVIE RECAP STUDIO
# Clean Burmese/English recap + natural TTS + real SRT timing
# =========================================================

st.set_page_config(
    page_title="AI Movie Recap Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- IMAGE HELPERS --------------------
def get_base64_image(path):
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""

def find_image(file_names):
    for name in file_names:
        if os.path.exists(name):
            return name
    return None

bg_path = find_image([
    "3703192a-8066-4da6-a1f0-f6a420a0783d.jpg",
    "bg.jpg",
])
kyaw_gyi_path = find_image([
    "b77e842c-f0a7-4974-8357-f65c1765c738.jpg",
    "kyaw_gyi.png",
    "kyaw_gyi.jpg",
])
shwe_ein_path = find_image([
    "f904bbe0-e401-46c9-9774-e2d903e2561d.jpg",
    "shwe_ein.png",
    "shwe_ein.jpg",
])

bg_base64 = get_base64_image(bg_path)
kyaw_gyi_base64 = get_base64_image(kyaw_gyi_path)
shwe_ein_base64 = get_base64_image(shwe_ein_path)

# -------------------- CSS --------------------
if bg_base64:
    app_background = (
        "linear-gradient(rgba(5,8,12,0.84), rgba(5,8,12,0.90)), "
        f"url('data:image/jpeg;base64,{bg_base64}')"
    )
else:
    app_background = "#0b0f14"

custom_css = f"""
<style>
.stApp {{
    background: {app_background};
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    color: #f8fafc !important;
}}

[data-testid="stAppViewContainer"] {{
    color: #f8fafc !important;
}}

[data-testid="stSidebar"] {{
    background: rgba(11, 15, 20, 0.98) !important;
    border-right: 1px solid rgba(255,255,255,0.08);
}}

[data-testid="stSidebar"] * {{
    color: #f8fafc !important;
}}

.main-title {{
    font-size: 2.35rem;
    font-weight: 800;
    color: #ffffff !important;
    margin-bottom: 2px;
    text-shadow: 0 2px 10px rgba(0,0,0,0.7);
}}

.sub-title {{
    color: #cbd5e1 !important;
    font-size: 0.96rem;
    margin-bottom: 24px;
}}

.section-header {{
    color: #ffffff !important;
    font-size: 1.13rem;
    font-weight: 800;
    margin-top: 16px;
    margin-bottom: 9px;
    text-shadow: 0 1px 5px rgba(0,0,0,0.7);
}}

div[role="radiogroup"] {{
    gap: 10px;
}}

div[role="radiogroup"] label {{
    color: #ffffff !important;
    background: rgba(15,23,42,0.78);
    border: 1px solid rgba(255,255,255,0.13);
    border-radius: 10px;
    padding: 7px 13px;
}}

div[role="radiogroup"] label p,
div[role="radiogroup"] label span {{
    color: #ffffff !important;
    font-weight: 700 !important;
}}

.voice-container {{
    display: flex;
    justify-content: center;
    align-items: stretch;
    gap: 22px;
    margin: 14px 0 24px 0;
}}

.voice-card {{
    width: 270px;
    padding: 18px;
    text-align: center;
    border-radius: 20px;
    background: rgba(15,23,42,0.74);
    border: 2px solid rgba(255,255,255,0.14);
    box-shadow: 0 12px 30px rgba(0,0,0,0.35);
}}

.voice-card.selected {{
    border-color: #38bdf8;
    background: rgba(14,116,144,0.25);
    box-shadow: 0 0 25px rgba(56,189,248,0.30);
}}

.avatar-bubble {{
    width: 92px;
    height: 92px;
    margin: 0 auto 12px auto;
    border-radius: 50%;
    background-size: cover;
    background-position: center;
    border: 3px solid #ffffff;
    box-shadow: 0 8px 20px rgba(0,0,0,0.55);
}}

.voice-name {{
    color: #ffffff !important;
    font-size: 1.18rem;
    font-weight: 800;
}}

.voice-desc {{
    color: #cbd5e1 !important;
    font-size: 0.84rem;
    margin-top: 4px;
}}

.key-link-btn {{
    display: inline-block;
    background: #172033;
    color: #7dd3fc !important;
    padding: 4px 10px;
    border-radius: 7px;
    text-decoration: none !important;
    font-size: 11px;
    border: 1px solid #334155;
    font-weight: 700;
}}

.key-link-btn:hover {{
    background: #263449;
}}

[data-testid="stTextArea"] textarea,
textarea {{
    background-color: #111827 !important;
    color: #f8fafc !important;
    -webkit-text-fill-color: #f8fafc !important;
    caret-color: #ffffff !important;
    border: 1px solid #475569 !important;
    border-radius: 12px !important;
    font-size: 15px !important;
    line-height: 1.65 !important;
}}

[data-testid="stTextInput"] input {{
    background-color: #111827 !important;
    color: #f8fafc !important;
    -webkit-text-fill-color: #f8fafc !important;
}}

[data-testid="stFileUploader"] section {{
    background: rgba(15,23,42,0.82) !important;
    border: 1px dashed #64748b !important;
}}

[data-testid="stFileUploader"] section * {{
    color: #f8fafc !important;
}}

.stDownloadButton button {{
    width: 100%;
}}

div[data-testid="stAlert"] {{
    border-radius: 12px;
}}

.small-note {{
    color: #94a3b8 !important;
    font-size: 0.78rem;
}}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# -------------------- SIDEBAR --------------------
with st.sidebar:
    st.markdown(
        "<h2 style='color:#fff;margin-bottom:15px;'>🔑 API Keys ချိန်ညှိချက်</h2>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
            <span style="font-weight:700;font-size:13px;color:#fff;">Groq API Key</span>
            <a href="https://console.groq.com/keys" target="_blank" class="key-link-btn">Get Free Key ↗</a>
        </div>
        """,
        unsafe_allow_html=True,
    )
    groq_api_key = st.text_input(
        "Groq API Key",
        placeholder="gsk_...",
        type="password",
        label_visibility="collapsed",
    )
    st.caption("ဇာတ်လမ်းနားလည်ခြင်း၊ ပြန်ရေးခြင်းနှင့် ဘာသာပြန်ခြင်းအတွက် အသုံးပြုပါသည်။")

    st.markdown("<hr style='border:0;border-top:1px solid #334155;'>", unsafe_allow_html=True)

    st.markdown(
        """
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
            <span style="font-weight:700;font-size:13px;color:#fff;">AssemblyAI API Key</span>
            <a href="https://www.assemblyai.com/dashboard/signup" target="_blank" class="key-link-btn">Get Free Key ↗</a>
        </div>
        """,
        unsafe_allow_html=True,
    )
    assemblyai_key = st.text_input(
        "AssemblyAI Key",
        placeholder="Paste your AssemblyAI API Key",
        type="password",
        label_visibility="collapsed",
    )
    st.caption("ဗီဒီယိုထဲက မူရင်းအသံကို စာသားအဖြစ် ပြောင်းရန် အသုံးပြုပါသည်။")

    st.markdown("<hr style='border:0;border-top:1px solid #334155;'>", unsafe_allow_html=True)
    st.markdown(
        "<div class='small-note'>💡 API Key များကို ဒီ app က database ထဲ မသိမ်းပါ။ Session အတွင်းသာ အသုံးပြုပါသည်။</div>",
        unsafe_allow_html=True,
    )

# -------------------- MAIN UI --------------------
st.markdown('<div class="main-title">🎬 AI Movie Recap Studio</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">One-Click Movie Recap • Natural Myanmar/English Narration • Real-Timing CapCut SRT</div>',
    unsafe_allow_html=True,
)

st.markdown('<div class="section-header">🌐 ဘာသာစကား ရွေးချယ်ပါ</div>', unsafe_allow_html=True)
lang_mode = st.radio(
    "Language Mode",
    ["မြန်မာဘာသာ (Myanmar Dubbing)", "အင်္ဂလိပ်ဘာသာ (English Dubbing)"],
    index=0,
    horizontal=True,
    label_visibility="collapsed",
)

st.markdown('<div class="section-header">🎙️ အသံရွေးချယ်ပါ</div>', unsafe_allow_html=True)
voice_choice = st.radio(
    "Voice Choice",
    ["ကျော်ကြီး (Kyaw Gyi)", "ရွှေအိမ် (Shwe Ein)"],
    index=0,
    horizontal=True,
    label_visibility="collapsed",
)

selected_voice = "kyaw_gyi" if "ကျော်ကြီး" in voice_choice else "shwe_ein"

kyaw_style = (
    f"background-image:url('data:image/jpeg;base64,{kyaw_gyi_base64}');"
    if kyaw_gyi_base64
    else "background:#2563eb;"
)
shwe_style = (
    f"background-image:url('data:image/jpeg;base64,{shwe_ein_base64}');"
    if shwe_ein_base64
    else "background:#db2777;"
)

st.markdown(
    f"""
    <div class="voice-container">
        <div class="voice-card {'selected' if selected_voice == 'kyaw_gyi' else ''}">
            <div class="avatar-bubble" style="{kyaw_style}"></div>
            <div class="voice-name">ကျော်ကြီး (Kyaw Gyi)</div>
            <div class="voice-desc">Male • နက်ရှိုင်းပြီး ဇာတ်လမ်းပြောသံ</div>
        </div>
        <div class="voice-card {'selected' if selected_voice == 'shwe_ein' else ''}">
            <div class="avatar-bubble" style="{shwe_style}"></div>
            <div class="voice-name">ရွှေအိမ် (Shwe Ein)</div>
            <div class="voice-desc">Female • ကြည်လင်ပြီး သဘာဝကျသောအသံ</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-header">📂 Recap လုပ်မည့် ဗီဒီယိုဖိုင် တင်ပါ (MP4, MKV, MOV)</div>',
    unsafe_allow_html=True,
)
uploaded_video = st.file_uploader(
    "Video Uploader",
    type=["mp4", "mkv", "mov"],
    label_visibility="collapsed",
)

# =========================================================
# HELPER FUNCTIONS
# =========================================================

def run_ffmpeg(command):
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-3000:])
    return result

def extract_audio(video_path, audio_path):
    run_ffmpeg([
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",
        "-ac", "1",
        "-ar", "44100",
        "-codec:a", "libmp3lame",
        "-q:a", "3",
        audio_path,
    ])

def get_media_duration(path):
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            path,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        return 0.0
    try:
        return float(result.stdout.strip())
    except Exception:
        return 0.0

def transcribe_audio_assemblyai(audio_path, api_key):
    headers = {"authorization": api_key}

    with open(audio_path, "rb") as audio_file:
        upload = requests.post(
            "https://api.assemblyai.com/v2/upload",
            headers=headers,
            data=audio_file,
            timeout=120,
        )

    if upload.status_code != 200:
        raise RuntimeError(f"AssemblyAI upload failed: {upload.text}")

    audio_url = upload.json()["upload_url"]

    payload = {
        "audio_url": audio_url,
        "language_detection": True,
    }

    transcript_request = requests.post(
        "https://api.assemblyai.com/v2/transcript",
        headers=headers,
        json=payload,
        timeout=60,
    )

    if transcript_request.status_code not in (200, 201):
        raise RuntimeError(
            f"AssemblyAI transcript request failed: {transcript_request.text}"
        )

    transcript_id = transcript_request.json()["id"]

    for _ in range(180):
        polling = requests.get(
            f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
            headers=headers,
            timeout=30,
        )

        if polling.status_code != 200:
            raise RuntimeError(f"AssemblyAI polling failed: {polling.text}")

        data = polling.json()
        status = data.get("status")

        if status == "completed":
            return data.get("text", "").strip()

        if status == "error":
            raise RuntimeError(
                f"AssemblyAI transcription failed: {data.get('error', 'Unknown error')}"
            )

        time.sleep(2)

    raise TimeoutError("AssemblyAI transcription timed out after 6 minutes.")

def choose_groq_model(client):
    preferred = [
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "llama-3.3-70b-versatile",
        "qwen/qwen3-32b",
        "llama-4-scout-17b-16e-instruct",
    ]

    try:
        available = [m.id for m in client.models.list().data]
    except Exception:
        available = []

    for model in preferred:
        if model in available:
            return model

    for model in available:
        low = model.lower()
        if not any(x in low for x in ["whisper", "guard", "safety"]):
            return model

    return "openai/gpt-oss-20b"

def clean_model_text(text):
    text = text.replace("```text", "").replace("```", "").strip()

    text = re.sub(
        r"^(Narrator|Voice-over|ဇာတ်လမ်းပြောသူ|ဇာတ်ကြောင်း|Script)\s*:\s*",
        "",
        text,
        flags=re.I,
    )

    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def generate_recap_script(original_transcript, groq_key, lang):
    client = Groq(api_key=groq_key)
    model = choose_groq_model(client)

    if "မြန်မာ" in lang:
        target = "Myanmar Burmese"
        rules = """
မြန်မာစကားကို စာအုပ်ထဲက ဘာသာပြန်သလို မရေးပါနဲ့။
မြန်မာလူတစ်ယောက် TikTok/Facebook movie recap ကို တကယ်ပြောနေသလို ရေးပါ။

အထူးလိုက်နာရန် -
1. မူရင်း transcript ကို စကားလုံးချင်း မပြန်ပါနဲ့။ အဓိပ္ပာယ်ကို အရင်နားလည်ပြီး သဘာဝကျအောင် ပြန်ရေးပါ။
2. စကားလုံးထပ်ခြင်း၊ ဝါကျထပ်ခြင်း၊ အဓိပ္ပာယ်တူတာကို နှစ်ခါပြောခြင်း မလုပ်ပါနဲ့။
3. "သူက... သူက... သူက..." လို ပုံစံတစ်မျိုးတည်း ထပ်ခါထပ်ခါ မသုံးပါနဲ့။
4. "ဒါပေမယ့်", "အဲဒီအချိန်မှာ", "မကြာခင်မှာ", "နောက်ဆုံးတော့" စတဲ့ ဆက်စပ်စကားတွေကို လိုအပ်တဲ့နေရာမှာပဲ သုံးပါ။
5. စကားပြောသလို တိုတိုရှင်းရှင်း ဝါကျတွေသုံးပါ။
6. အလွန်စာပေဆန်တဲ့ စကားလုံး၊ Google Translate ဆန်တဲ့ စာကြောင်းတွေ ရှောင်ပါ။
7. နာမည်ကို မလိုအပ်ဘဲ ဝါကျတိုင်းမှာ ထပ်မရေးပါနဲ့။
8. ဇာတ်လမ်းအချက်အလက် မရှိတာကို မတီထွင်ပါနဲ့။
9. Movie recap အတွက် စိတ်ဝင်စားစရာကောင်းပြီး အရှိန်မကျအောင် ရေးပါ။
10. အသံဖတ်ရလွယ်အောင် ဝါကျတစ်ကြောင်းကို အလွန်ရှည်မထားပါနဲ့။
11. Emoji, heading, bullet point, narrator note, sound effect မထည့်ပါနဲ့။
12. Output မှာ narration စာသားပဲ ထည့်ပါ။
13. မြန်မာဘာသာမှာ သဘာဝကျတဲ့ punctuation သုံးပါ။ ဝါကျအဆုံးမှာ "။" သုံးပါ။
"""
    else:
        target = "Natural spoken English"
        rules = """
Write like a real human movie-recap narrator speaking naturally.
Do not translate word-for-word.
Avoid repeated words, repeated sentence patterns, and unnecessary character-name repetition.
Use short, punchy sentences that are easy for TTS.
Do not invent facts that are not supported by the transcript.
Do not add headings, emojis, bullet points, narrator notes, or sound effects.
Output narration only.
"""

    prompt = f"""
You are a professional movie recap writer and spoken-language editor.

TARGET LANGUAGE: {target}

Your job:
First understand the full story in the transcript.
Then rewrite it as one coherent movie recap narration.

{rules}

Important quality check before answering:
- Remove duplicated ideas.
- Remove awkward literal translations.
- Make every sentence sound natural when spoken aloud.
- Keep the story logically connected from beginning to end.
- Do not make the script unnecessarily long.
- Do not repeat the same sentence opening again and again.

SOURCE TRANSCRIPT:
{original_transcript}
"""

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a natural spoken-language movie recap editor.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.55,
        max_tokens=6000,
    )

    result = completion.choices[0].message.content or ""
    result = clean_model_text(result)

    if not result:
        raise RuntimeError("Groq returned an empty recap script.")

    return result

def split_into_sentences(text):
    text = clean_model_text(text)
    text = re.sub(r"[ \t]+", " ", text)

    parts = re.split(r"(?<=[။!?…])\s+|\n+", text)

    sentences = []
    for part in parts:
        part = part.strip()
        if not part:
            continue

        if len(part) > 260:
            subparts = re.split(r"(?<=[၊,;])\s+", part)
            for sub in subparts:
                sub = sub.strip()
                if sub:
                    sentences.append(sub)
        else:
            sentences.append(part)

    merged = []
    for sentence in sentences:
        if merged and len(sentence) < 18:
            merged[-1] = merged[-1] + " " + sentence
        else:
            merged.append(sentence)

    return merged

async def synthesize_one(text, output_path, voice_type, lang):
    if "မြန်မာ" in lang:
        voice = (
            "my-MM-ThihaNeural"
            if voice_type == "kyaw_gyi"
            else "my-MM-NilarNeural"
        )
        rate = "-4%"
        pitch = "-1Hz"
    else:
        voice = (
            "en-US-ChristopherNeural"
            if voice_type == "kyaw_gyi"
            else "en-US-JennyNeural"
        )
        rate = "-3%"
        pitch = "0Hz"

    communicate = edge_tts.Communicate(
        text,
        voice,
        rate=rate,
        pitch=pitch,
    )
    await communicate.save(output_path)

def concatenate_audio(audio_files, output_audio):
    if len(audio_files) == 1:
        run_ffmpeg([
            "ffmpeg", "-y",
            "-i", audio_files[0],
            "-codec:a", "libmp3lame",
            "-q:a", "2",
            output_audio,
        ])
        return

    concat_file = output_audio + ".txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for path in audio_files:
            safe_path = os.path.abspath(path).replace("'", "'\\''")
            f.write(f"file '{safe_path}'\n")

    try:
        run_ffmpeg([
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-codec:a", "libmp3lame",
            "-q:a", "2",
            output_audio,
        ])
    finally:
        if os.path.exists(concat_file):
            os.remove(concat_file)

def create_timed_dub_and_srt(script, output_audio, output_srt, voice_type, lang, work_dir):
    sentences = split_into_sentences(script)

    if not sentences:
        raise RuntimeError("No usable sentences were found in the recap script.")

    audio_parts = []
    timings = []
    current_time = 0.0

    for index, sentence in enumerate(sentences, start=1):
        part_path = os.path.join(work_dir, f"part_{index:04d}.mp3")

        asyncio.run(
            synthesize_one(
                sentence,
                part_path,
                voice_type,
                lang,
            )
        )

        duration = get_media_duration(part_path)

        if duration <= 0:
            duration = max(1.0, len(sentence) / 12.0)

        start = current_time
        end = current_time + duration

        timings.append((start, end, sentence))
        audio_parts.append(part_path)
        current_time = end

    concatenate_audio(audio_parts, output_audio)

    def fmt(seconds):
        total_ms = max(0, int(round(seconds * 1000)))
        hours = total_ms // 3600000
        minutes = (total_ms % 3600000) // 60000
        secs = (total_ms % 60000) // 1000
        ms = total_ms % 1000
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"

    with open(output_srt, "w", encoding="utf-8") as f:
        for idx, (start, end, sentence) in enumerate(timings, start=1):
            f.write(f"{idx}\n")
            f.write(f"{fmt(start)} --> {fmt(end)}\n")
            f.write(f"{sentence}\n\n")

    return output_audio, output_srt, timings

# =========================================================
# EXECUTION
# =========================================================

st.write("")

if st.button("🚀 Start Auto Recap", type="primary", use_container_width=True):
    if not groq_api_key.strip():
        st.error("⚠️ Sidebar ထဲမှာ Groq API Key ထည့်ပါ။")
    elif not assemblyai_key.strip():
        st.error("⚠️ Sidebar ထဲမှာ AssemblyAI API Key ထည့်ပါ။")
    elif uploaded_video is None:
        st.warning("⚠️ Recap လုပ်မယ့် video file ကို အရင်တင်ပါ။")
    else:
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_name = uploaded_video.name
            extension = os.path.splitext(original_name)[1].lower() or ".mp4"

            temp_video_path = os.path.join(tmp_dir, f"input{extension}")
            temp_audio_path = os.path.join(tmp_dir, "source_audio.mp3")
            dubbed_audio_path = os.path.join(tmp_dir, "recap_dubbed.mp3")
            srt_path = os.path.join(tmp_dir, "capcut_subtitles.srt")

            with open(temp_video_path, "wb") as f:
                f.write(uploaded_video.getbuffer())

            status_box = st.status(
                "🎬 AI Movie Recap စတင်နေပါပြီ...",
                expanded=True,
            )

            try:
                status_box.write("1️⃣ Video ထဲက original audio ကို ထုတ်နေပါတယ်...")
                extract_audio(temp_video_path, temp_audio_path)

                status_box.write("2️⃣ AssemblyAI နဲ့ speech ကို စာသားပြောင်းနေပါတယ်...")
                raw_text = transcribe_audio_assemblyai(
                    temp_audio_path,
                    assemblyai_key.strip(),
                )

                if len(raw_text.strip()) < 10:
                    raise RuntimeError(
                        "မူရင်းအသံထဲက စာသားမရပါ။ Audio quality သို့မဟုတ် API setting ကို စစ်ပါ။"
                    )

                status_box.write("3️⃣ Groq AI က ဇာတ်လမ်းကို နားလည်ပြီး လူပြောသလို ပြန်ရေးနေပါတယ်...")
                recap_script = generate_recap_script(
                    raw_text,
                    groq_api_key.strip(),
                    lang_mode,
                )

                status_box.write("4️⃣ Natural TTS voice နဲ့ narration audio ထုတ်နေပါတယ်...")
                create_timed_dub_and_srt(
                    recap_script,
                    dubbed_audio_path,
                    srt_path,
                    selected_voice,
                    lang_mode,
                    tmp_dir,
                )

                status_box.update(
                    label="🎉 AI Movie Recap အောင်မြင်စွာ ပြီးဆုံးပါပြီ!",
                    state="complete",
                )

                st.success(
                    "✅ Recap Script + Natural Dubbing + အချိန်ကိုက် CapCut SRT အသင့်ဖြစ်ပါပြီ။"
                )

                st.markdown(
                    '<h3 style="color:#fff;">📝 Recap Script</h3>',
                    unsafe_allow_html=True,
                )
                st.text_area(
                    "Generated Script",
                    recap_script,
                    height=260,
                    label_visibility="collapsed",
                )

                st.markdown(
                    '<h3 style="color:#fff;">🎧 Dubbed Audio</h3>',
                    unsafe_allow_html=True,
                )
                with open(dubbed_audio_path, "rb") as f:
                    audio_bytes = f.read()

                st.audio(audio_bytes, format="audio/mp3")
                st.download_button(
                    "⬇️ Download Dubbed Audio",
                    data=audio_bytes,
                    file_name="recap_dubbed_audio.mp3",
                    mime="audio/mpeg",
                    use_container_width=True,
                )

                st.markdown(
                    '<h3 style="color:#fff;">💬 CapCut SRT</h3>',
                    unsafe_allow_html=True,
                )
                with open(srt_path, "rb") as f:
                    srt_bytes = f.read()

                st.download_button(
                    "⬇️ Download CapCut SRT",
                    data=srt_bytes,
                    file_name="capcut_subtitles.srt",
                    mime="application/x-subrip",
                    use_container_width=True,
                )

            except Exception as e:
                status_box.update(
                    label="❌ လုပ်ဆောင်မှု မအောင်မြင်ပါ",
                    state="error",
                )
                st.error(f"အမှား: {e}")
                st.code(str(e))
