import streamlit as st
import os
import subprocess
import tempfile
import base64
import requests
import asyncio
import edge_tts
from groq import Groq

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="AI Movie Recap Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- BACKGROUND & CSS STYLING -----------------
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

bg_base64 = get_base64_image("bg.jpg")
kyaw_gyi_base64 = get_base64_image("kyaw_gyi.png")
shwe_ein_base64 = get_base64_image("shwe_ein.png")

custom_css = f"""
<style>
/* Background Image */
.stApp {{
    background: {'linear-gradient(rgba(14, 17, 23, 0.85), rgba(14, 17, 23, 0.85)), url("data:image/jpeg;base64,' + bg_base64 + '")' if bg_base64 else '#0e1117'};
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    color: #ffffff;
}}

/* Header Typography */
.main-title {{
    font-size: 2.2rem;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 0px;
    display: flex;
    align-items: center;
    gap: 12px;
}}
.sub-title {{
    font-size: 0.95rem;
    color: #8b949e;
    margin-bottom: 25px;
}}

/* 3D Bubble Voice Card Styling */
.voice-container {{
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 20px;
    margin-top: 15px;
    margin-bottom: 25px;
}}
.voice-card {{
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(12px);
    border: 2px solid rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    padding: 20px;
    width: 260px;
    text-align: center;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
}}
.voice-card.selected {{
    border-color: #3b82f6;
    background: rgba(59, 130, 246, 0.15);
    box-shadow: 0 0 25px rgba(59, 130, 246, 0.4);
    transform: translateY(-5px);
}}
.avatar-bubble {{
    width: 90px;
    height: 90px;
    border-radius: 50%;
    margin: 0 auto 12px auto;
    background-size: cover;
    background-position: center;
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.4), inset 0 -3px 6px rgba(0,0,0,0.4), inset 0 3px 6px rgba(255,255,255,0.4);
    border: 3px solid rgba(255, 255, 255, 0.8);
}}
.voice-name {{
    font-size: 1.15rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 4px;
}}
.voice-desc {{
    font-size: 0.8rem;
    color: #94a3b8;
}}

/* Sidebar Link Button */
.key-link-btn {{
    background-color: #1f2937;
    color: #60a5fa !important;
    padding: 3px 10px;
    border-radius: 6px;
    text-decoration: none;
    font-size: 11px;
    border: 1px solid #374151;
    font-weight: 600;
    transition: 0.2s;
}}
.key-link-btn:hover {{
    background-color: #374151;
    color: #93c5fd !important;
}}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ----------------- SIDEBAR: API KEYS & EXTERNAL LINKS -----------------
with st.sidebar:
    st.markdown("### 🔑 API Keys ချိန်ညှိချက်")
    st.write("")
    
    # 1. Groq API Key Setup
    st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
            <span style="font-weight: 600; font-size: 13.5px; color: #e5e7eb;">Groq API Key (ဇာတ်ညွှန်း/ဘာသာပြန်):</span>
            <a href="https://console.groq.com/keys" target="_blank" class="key-link-btn">Get Free Key ↗</a>
        </div>
    """, unsafe_allow_html=True)
    groq_api_key = st.text_input("Groq API Key", placeholder="gsk_...", type="password", label_visibility="collapsed")
    st.caption("Groq Cloud (Llama-3) ဖြင့် ဗီဒီယိုဇာတ်လမ်းကို အချိန်ကိုက် မြန်မာပြန်ပေးပါသည်။")
    
    st.markdown("<hr style='margin: 18px 0; border: 0.5px solid #374151;'>", unsafe_allow_html=True)
    
    # 2. AssemblyAI API Key Setup
    st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
            <span style="font-weight: 600; font-size: 13.5px; color: #e5e7eb;">AssemblyAI Key (အသံဖိုင် စာသားပြောင်းရန်):</span>
            <a href="https://www.assemblyai.com/dashboard/signup" target="_blank" class="key-link-btn">Get Free Key ↗</a>
        </div>
    """, unsafe_allow_html=True)
    assemblyai_key = st.text_input("AssemblyAI Key", placeholder="Paste your AssemblyAI API Key", type="password", label_visibility="collapsed")
    st.caption("ဗီဒီယိုထဲမှ မူရင်းအသံကို တိကျသော Timestamp စာတန်းထိုးအဖြစ် ထုတ်ယူပေးပါသည်။")

    st.markdown("<hr style='margin: 18px 0; border: 0.5px solid #374151;'>", unsafe_allow_html=True)
    st.info("💡 API Keys များသည် မိမိ Browser တွင်သာ ခေတ္တအသုံးပြုပြီး လုံခြုံစွာ ရှိနေပါမည်။")

# ----------------- MAIN UI -----------------
st.markdown('<div class="main-title">🎬 AI Movie Recap Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">One-Click Auto Recap: Myanmar & English Dubbing + Time-Synced CapCut SRT</div>', unsafe_allow_html=True)

# 1. Language Mode Selection
st.markdown("#### 🌐 ဘာသာစကား ရွေးချယ်ပါ (Language Mode)")
lang_mode = st.radio(
    "ဘာသာစကား ရွေးချယ်ပါ",
    options=["မြန်မာဘာသာ (Myanmar Dubbing)", "အင်္ဂလိပ်ဘာသာ (English Dubbing)"],
    index=0,
    horizontal=True,
    label_visibility="collapsed"
)

st.write("")

# 2. Voice Selection (Kyaw Gyi & Shwe Ein)
st.markdown("#### 🎙️ အသံရွေးချယ်ပါ (Voice Selection)")
col1, col2 = st.columns(2)

with col1:
    voice_choice = st.radio(
        "Voice Selector",
        options=["ကျော်ကြီး (Kyaw Gyi)", "ရွှေအိမ် (Shwe Ein)"],
        index=0,
        horizontal=True
    )

selected_voice = "kyaw_gyi" if "ကျော်ကြီး" in voice_choice else "shwe_ein"

# 3D Avatar Display Cards
st.markdown(f"""
<div class="voice-container">
    <div class="voice-card {'selected' if selected_voice == 'kyaw_gyi' else ''}">
        <div class="avatar-bubble" style="{'background-image: url(data:image/png;base64,' + kyaw_gyi_base64 + ');' if kyaw_gyi_base64 else 'background-color: #3b82f6;'}"></div>
        <div class="voice-name">ကျော်ကြီး (Kyaw Gyi)</div>
        <div class="voice-desc">Male • ဇာတ်လမ်းပြော ခပ်နက်နက်အသံ</div>
    </div>
    <div class="voice-card {'selected' if selected_voice == 'shwe_ein' else ''}">
        <div class="avatar-bubble" style="{'background-image: url(data:image/png;base64,' + shwe_ein_base64 + ');' if shwe_ein_base64 else 'background-color: #ec4899;'}"></div>
        <div class="voice-name">ရွှေအိမ် (Shwe Ein)</div>
        <div class="voice-desc">Female • ကြည်လင်ပြတ်သား သဘာဝအသံ</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 3. Video File Uploader
uploaded_video = st.file_uploader("📂 Recap လုပ်မည့် ဗီဒီယိုဖိုင်ကို တင်ပါ (MP4, MKV, MOV)", type=["mp4", "mkv", "mov"])

# ----------------- HELPER FUNCTIONS -----------------
def extract_audio(video_path, audio_path):
    cmd = ["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "libmp3lame", "-q:a", "4", audio_path]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

def transcribe_audio_assemblyai(audio_path, api_key):
    headers = {"authorization": api_key}
    with open(audio_path, "rb") as f:
        upload_response = requests.post("https://api.assemblyai.com/v2/upload", headers=headers, data=f)
    audio_url = upload_response.json()["upload_url"]

    transcript_req = requests.post(
        "https://api.assemblyai.com/v2/transcript",
        headers=headers,
        json={"audio_url": audio_url}
    )
    transcript_id = transcript_req.json()["id"]

    while True:
        polling_res = requests.get(f"https://api.assemblyai.com/v2/transcript/{transcript_id}", headers=headers).json()
        if polling_res["status"] == "completed":
            return polling_res["text"]
        elif polling_res["status"] == "error":
            raise Exception(f"Transcription failed: {polling_res['error']}")
        asyncio.run(asyncio.sleep(2))

def generate_recap_script(original_transcript, groq_key, lang):
    client = Groq(api_key=groq_key)
    target_lang = "Burmese (မြန်မာဘာသာ)" if "မြန်မာ" in lang else "English"
    prompt = f"""
You are a master movie recap narrator for TikTok and Facebook Reels.
Here is the raw speech transcript from a video:
"{original_transcript}"

Please write a dramatic, concise, engaging, and fast-paced movie recap script based on this transcript.
Target Language: {target_lang}
Keep the narration synchronized, natural, and compelling without unnecessary greetings.
"""
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile"
    )
    return chat_completion.choices[0].message.content

async def create_edge_tts_audio(text, output_audio, voice_type, lang):
    if "မြန်မာ" in lang:
        voice = "my-MM-ThihaNeural" if voice_type == "kyaw_gyi" else "my-MM-NilarNeural"
    else:
        voice = "en-US-ChristopherNeural" if voice_type == "kyaw_gyi" else "en-US-JennyNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_audio)

def create_srt_file(text, output_srt):
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    srt_content = ""
    start_sec = 0
    duration_per_line = 3.5

    for idx, line in enumerate(lines, 1):
        end_sec = start_sec + duration_per_line
        s_h, s_m, s_s = int(start_sec // 3600), int((start_sec % 3600) // 60), int(start_sec % 60)
        e_h, e_m, e_s = int(end_sec // 3600), int((end_sec % 3600) // 60), int(end_sec % 60)
        
        srt_content += f"{idx}\n"
        srt_content += f"{s_h:02d}:{s_m:02d}:{s_s:02d},000 --> {e_h:02d}:{e_m:02d}:{e_s:02d},000\n"
        srt_content += f"{line}\n\n"
        start_sec = end_sec

    with open(output_srt, "w", encoding="utf-8") as f:
        f.write(srt_content)
    return output_srt

# ----------------- EXECUTION -----------------
if st.button("🚀 Start Auto Recap (စတင်ပြုလုပ်မည်)", type="primary"):
    if not groq_api_key or not assemblyai_key:
        st.error("⚠️ ဘယ်ဘက် Sidebar တွင် Groq API Key နှင့် AssemblyAI Key တို့ကို အရင်ဖြည့်သွင်းပေးပါခင်ဗျာ။")
    elif not uploaded_video:
        st.warning("⚠️ ကျေးဇူးပြု၍ ဗီဒီယိုဖိုင်တစ်ခု အရင်တင်သွင်းပေးပါခင်ဗျာ။")
    else:
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_video_path = os.path.join(tmp_dir, "input_video.mp4")
            temp_audio_path = os.path.join(tmp_dir, "extracted_audio.mp3")
            dubbed_audio_path = os.path.join(tmp_dir, "dubbed_audio.mp3")
            srt_path = os.path.join(tmp_dir, "capcut_subtitles.srt")

            with open(temp_video_path, "wb") as f:
                f.write(uploaded_video.read())

            status_box = st.status("🎬 AI Movie Recap စတင်လည်ပတ်နေပါပြီ...", expanded=True)
            try:
                status_box.write("1️⃣ ဗီဒီယိုထဲမှ အသံဖိုင်ကို သီးသန့်ထုတ်ယူနေပါသည်...")
                extract_audio(temp_video_path, temp_audio_path)

                status_box.write("2️⃣ AssemblyAI ဖြင့် ဗီဒီယိုထဲမှ စကားသံများကို စာသားပြောင်းနေပါသည်...")
                raw_text = transcribe_audio_assemblyai(temp_audio_path, assemblyai_key)

                status_box.write("3️⃣ Groq AI ဖြင့် စိတ်ဝင်စားဖွယ် ဇာတ်လမ်းအကျဉ်းနှင့် ဘာသာပြန် ရေးဖွဲ့နေပါသည်...")
                recap_script = generate_recap_script(raw_text, groq_api_key, lang_mode)

                status_box.write(f"4️⃣ {voice_choice} အသံဖြင့် အသံဒပ်ဘင်းဖိုင် ထုတ်လုပ်နေပါသည်...")
                asyncio.run(create_edge_tts_audio(recap_script, dubbed_audio_path, selected_voice, lang_mode))

                status_box.write("5️⃣ CapCut အချိန်ကိုက် SRT စာတန်းထိုးဖိုင် တည်ဆောက်နေပါသည်...")
                create_srt_file(recap_script, srt_path)

                status_box.update(label="🎉 AI Movie Recap အောင်မြင်စွာ ပြီးဆုံးပါပြီ!", state="complete")

                st.success("✅ အသံဒပ်ဘင်းနှင့် CapCut စာတန်းထိုးဖိုင် အသင့်ဖြစ်ပါပြီ!")

                st.markdown("### 📝 ထွက်ရှိလာသော ဇာတ်လမ်းအကျဉ်း (Recap Script)")
                st.text_area("Script", recap_script, height=180)

                st.markdown("### 🎧 အသံဒပ်ဘင်း နားဆင်ရန်နှင့် ရယူရန်")
                with open(dubbed_audio_path, "rb") as af:
                    audio_bytes = af.read()
                    st.audio(audio_bytes, format="audio/mp3")
                    st.download_button(
                        label="⬇️ အသံဖိုင်ဒေါင်းလုဒ်ရယူရန် (Download Dubbed Audio)",
                        data=audio_bytes,
                        file_name="recap_dubbed_audio.mp3",
                        mime="audio/mp3"
                    )

                st.markdown("### 💬 CapCut စာတန်းထိုး SRT ဖိုင် ရယူရန်")
                with open(srt_path, "rb") as sf:
                    st.download_button(
                        label="⬇️ CapCut SRT ဖိုင် ဒေါင်းလုဒ်ရယူရန် (Download SRT)",
                        data=sf.read(),
                        file_name="capcut_subtitles.srt",
                        mime="text/plain"
                    )

            except Exception as e:
                status_box.update(label="❌ လုပ်ဆောင်မှု မအောင်မြင်ပါ", state="error")
                st.error(f"အမှားဖြစ်ပေါ်ရသည့်အကြောင်းရင်း: {e}")
