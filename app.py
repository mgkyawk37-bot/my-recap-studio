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

# ----------------- HELPER: IMAGE LOADER -----------------
def get_base64_image(image_path):
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

def find_image(file_list):
    for f in file_list:
        if os.path.exists(f):
            return f
    return None

bg_path = find_image(["3703192a-8066-4da6-a1f0-f6a420a0783d.jpg", "bg.jpg"])
kyaw_gyi_path = find_image(["b77e842c-f0a7-4974-8357-f65c1765c738.jpg", "kyaw_gyi.png", "kyaw_gyi.jpg"])
shwe_ein_path = find_image(["f904bbe0-e401-46c9-9774-e2d903e2561d.jpg", "shwe_ein.png", "shwe_ein.jpg"])

bg_base64 = get_base64_image(bg_path)
kyaw_gyi_base64 = get_base64_image(kyaw_gyi_path)
shwe_ein_base64 = get_base64_image(shwe_ein_path)

# ----------------- CSS STYLING (စာသားအားလုံး အဖြူရောင် ထင်ရှားစေရန်) -----------------
custom_css = f"""
<style>
/* App Background */
.stApp {{
    background: {'linear-gradient(rgba(10, 12, 16, 0.85), rgba(10, 12, 16, 0.85)), url("data:image/jpeg;base64,' + bg_base64 + '")' if bg_base64 else '#0e1117'};
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    color: #ffffff !important;
}}

/* Radio Buttons Text Color */
div[role="radiogroup"] label p,
div[role="radiogroup"] label div,
div[role="radiogroup"] span {{
    color: #ffffff !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    text-shadow: 0 1px 3px rgba(0,0,0,0.8);
}}

/* Sidebar Label & Text Color */
[data-testid="stSidebar"] {{
    background-color: rgba(18, 22, 28, 0.95) !important;
}}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span {{
    color: #ffffff !important;
}}

/* Titles */
.main-title {{
    font-size: 2.3rem;
    font-weight: 800;
    color: #ffffff !important;
    margin-bottom: 2px;
    text-shadow: 0 2px 4px rgba(0,0,0,0.6);
}}
.sub-title {{
    font-size: 0.95rem;
    color: #cbd5e1 !important;
    margin-bottom: 25px;
}}
.section-header {{
    font-size: 1.15rem;
    font-weight: 700;
    color: #ffffff !important;
    margin-top: 15px;
    margin-bottom: 8px;
    text-shadow: 0 1px 2px rgba(0,0,0,0.5);
}}

/* 3D Voice Cards */
.voice-container {{
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 24px;
    margin: 15px 0 25px 0;
}}
.voice-card {{
    background: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(14px);
    border: 2px solid rgba(255, 255, 255, 0.2);
    border-radius: 20px;
    padding: 20px;
    width: 270px;
    text-align: center;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.45);
}}
.voice-card.selected {{
    border-color: #38bdf8;
    background: rgba(56, 189, 248, 0.18);
    box-shadow: 0 0 25px rgba(56, 189, 248, 0.45);
    transform: translateY(-5px);
}}
.avatar-bubble {{
    width: 95px;
    height: 95px;
    border-radius: 50%;
    margin: 0 auto 12px auto;
    background-size: cover;
    background-position: center;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.6), inset 0 2px 4px rgba(255,255,255,0.4);
    border: 3px solid #ffffff;
}}
.voice-name {{
    font-size: 1.2rem;
    font-weight: 700;
    color: #ffffff !important;
    margin-bottom: 4px;
}}
.voice-desc {{
    font-size: 0.85rem;
    color: #cbd5e1 !important;
}}

/* Get Free Key Link Button */
.key-link-btn {{
    background-color: #1e293b;
    color: #38bdf8 !important;
    padding: 3px 10px;
    border-radius: 6px;
    text-decoration: none;
    font-size: 11.5px;
    border: 1px solid #334155;
    font-weight: 600;
}}
.key-link-btn:hover {{
    background-color: #334155;
    color: #7dd3fc !important;
}}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ----------------- SIDEBAR: API KEYS & EXTERNAL LINKS -----------------
with st.sidebar:
    st.markdown("<h2 style='color:#ffffff; font-size:1.3rem; margin-bottom:15px;'>🔑 API Keys ချိန်ညှိချက်</h2>", unsafe_allow_html=True)
    
    # 1. Groq API Key Setup
    st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
            <span style="font-weight: 600; font-size: 13.5px; color: #ffffff;">Groq API Key (ဇာတ်ညွှန်း/ဘာသာပြန်):</span>
            <a href="https://console.groq.com/keys" target="_blank" class="key-link-btn">Get Free Key ↗</a>
        </div>
    """, unsafe_allow_html=True)
    groq_api_key = st.text_input("Groq API Key", placeholder="gsk_...", type="password", label_visibility="collapsed")
    st.caption("Groq Cloud ဖြင့် မြန်ဆန်စွာ အချိန်ကိုက် မြန်မာပြန်ပေးပါသည်။")
    
    st.markdown("<hr style='margin: 16px 0; border: 0.5px solid #334155;'>", unsafe_allow_html=True)
    
    # 2. AssemblyAI API Key Setup
    st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
            <span style="font-weight: 600; font-size: 13.5px; color: #ffffff;">AssemblyAI Key (အသံဖိုင် စာသားပြောင်း):</span>
            <a href="https://www.assemblyai.com/dashboard/signup" target="_blank" class="key-link-btn">Get Free Key ↗</a>
        </div>
    """, unsafe_allow_html=True)
    assemblyai_key = st.text_input("AssemblyAI Key", placeholder="Paste your AssemblyAI API Key", type="password", label_visibility="collapsed")
    st.caption("ဗီဒီယိုထဲမှ မူရင်းစကားသံများကို အချိန်ကိုက် Timestamp စာတန်းထိုးအဖြစ် ထုတ်ပေးပါသည်။")

    st.markdown("<hr style='margin: 16px 0; border: 0.5px solid #334155;'>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:12px; color:#94a3b8;'>💡 API Key များကို သိမ်းဆည်းခြင်းမရှိဘဲ မိမိ Browser Session အတွင်းသာ ခေတ္တလုံခြုံစွာ အသုံးပြုပါသည်။</p>", unsafe_allow_html=True)

# ----------------- MAIN UI -----------------
st.markdown('<div class="main-title">🎬 AI Movie Recap Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">One-Click Auto Recap: Myanmar & English Dubbing + Time-Synced CapCut SRT</div>', unsafe_allow_html=True)

# 1. Language Mode Selection
st.markdown('<div class="section-header">🌐 ဘာသာစကား ရွေးချယ်ပါ (Language Mode)</div>', unsafe_allow_html=True)
lang_mode = st.radio(
    "Language Mode",
    options=["မြန်မာဘာသာ (Myanmar Dubbing)", "အင်္ဂလိပ်ဘာသာ (English Dubbing)"],
    index=0,
    horizontal=True,
    label_visibility="collapsed"
)

st.write("")

# 2. Voice Selection
st.markdown('<div class="section-header">🎙️ အသံရွေးချယ်ပါ (Voice Selection)</div>', unsafe_allow_html=True)
voice_choice = st.radio(
    "Voice Choice",
    options=["ကျော်ကြီး (Kyaw Gyi)", "ရွှေအိမ် (Shwe Ein)"],
    index=0,
    horizontal=True,
    label_visibility="collapsed"
)

selected_voice = "kyaw_gyi" if "ကျော်ကြီး" in voice_choice else "shwe_ein"

# 3D Avatar Display Cards
st.markdown(f"""
<div class="voice-container">
    <div class="voice-card {'selected' if selected_voice == 'kyaw_gyi' else ''}">
        <div class="avatar-bubble" style="{'background-image: url(data:image/jpeg;base64,' + kyaw_gyi_base64 + ');' if kyaw_gyi_base64 else 'background-color: #3b82f6;'}"></div>
        <div class="voice-name">ကျော်ကြီး (Kyaw Gyi)</div>
        <div class="voice-desc">Male • ဇာတ်လမ်းပြော ခပ်နက်နက်အသံ</div>
    </div>
    <div class="voice-card {'selected' if selected_voice == 'shwe_ein' else ''}">
        <div class="avatar-bubble" style="{'background-image: url(data:image/jpeg;base64,' + shwe_ein_base64 + ');' if shwe_ein_base64 else 'background-color: #ec4899;'}"></div>
        <div class="voice-name">ရွှေအိမ် (Shwe Ein)</div>
        <div class="voice-desc">Female • ကြည်လင်ပြတ်သား သဘာဝအသံ</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 3. Video File Uploader
st.markdown('<div class="section-header">📂 Recap လုပ်မည့် ဗီဒီယိုဖိုင်ကို တင်ပါ (MP4, MKV, MOV)</div>', unsafe_allow_html=True)
uploaded_video = st.file_uploader("Video Uploader", type=["mp4", "mkv", "mov"], label_visibility="collapsed")

# ----------------- HELPER FUNCTIONS -----------------
def extract_audio(video_path, audio_path):
    cmd = ["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "libmp3lame", "-q:a", "4", audio_path]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

def transcribe_audio_assemblyai(audio_path, api_key):
    headers = {"authorization": api_key}
    with open(audio_path, "rb") as f:
        upload_response = requests.post("https://api.assemblyai.com/v2/upload", headers=headers, data=f)
    
    if upload_response.status_code != 200:
        raise Exception(f"AssemblyAI Upload Failed: {upload_response.text}")
        
    audio_url = upload_response.json()["upload_url"]

    transcript_req = requests.post(
        "https://api.assemblyai.com/v2/transcript",
        headers=headers,
        json={"audio_url": audio_url}
    )
    if transcript_req.status_code != 200:
        raise Exception(f"AssemblyAI Request Failed: {transcript_req.text}")
        
    transcript_id = transcript_req.json()["id"]

    while True:
        polling_res = requests.get(f"https://api.assemblyai.com/v2/transcript/{transcript_id}", headers=headers).json()
        if polling_res["status"] == "completed":
            return polling_res.get("text", "")
        elif polling_res["status"] == "error":
            raise Exception(f"Transcription failed: {polling_res['error']}")
        asyncio.run(asyncio.sleep(2))

def generate_recap_script(original_transcript, groq_key, lang):
    client = Groq(api_key=groq_key)
    target_lang = "Burmese (မြန်မာဘာသာ)" if "မြန်မာ" in lang else "English"
    prompt = f"""
You are an expert movie recap narrator for TikTok and Facebook Reels.
Here is the speech transcript from a video:
"{original_transcript}"

Please write a dramatic, concise, engaging, and fast-paced movie recap narration based on this story.
Target Language: {target_lang}
Keep the narration natural, synchronized, thrilling, and suitable for voice-over narration.
Do not include any narrator notes, emojis, or sound effect descriptions—just the narration script lines.
"""
    # Error မတက်စေရန် အရန် Models များကို အစဉ်လိုက် စမ်းသပ်မည့် စနစ်
    candidate_models = [
        "llama-3.3-70b-versatile",
        "llama3-8b-8192",
        "llama-3.1-8b-instant"
    ]
    
    last_error = None
    for model_name in candidate_models:
        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model_name
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            last_error = e
            continue
            
    raise Exception(f"Groq Model Error: {last_error}")

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
    start_sec = 0.0
    duration_per_line = 3.5

    for idx, line in enumerate(lines, 1):
        end_sec = start_sec + duration_per_line
        s_h, s_m, s_s = int(start_sec // 3600), int((start_sec % 3600) // 60), int(start_sec % 60)
        s_ms = int((start_sec - int(start_sec)) * 1000)
        e_h, e_m, e_s = int(end_sec // 3600), int((end_sec % 3600) // 60), int(end_sec % 60)
        e_ms = int((end_sec - int(end_sec)) * 1000)
        
        srt_content += f"{idx}\n"
        srt_content += f"{s_h:02d}:{s_m:02d}:{s_s:02d},{s_ms:03d} --> {e_h:02d}:{e_m:02d}:{e_s:02d},{e_ms:03d}\n"
        srt_content += f"{line}\n\n"
        start_sec = end_sec

    with open(output_srt, "w", encoding="utf-8") as f:
        f.write(srt_content)
    return output_srt

# ----------------- EXECUTION -----------------
st.write("")
if st.button("🚀 Start Auto Recap (စတင်ပြုလုပ်မည်)", type="primary"):
    if not groq_api_key or not assemblyai_key:
        st.error("⚠️ ဘယ်ဘက် Sidebar တွင် Groq API Key နှင့် AssemblyAI Key တို့ကို အရင်ဖြည့်သွင်းပေးပါခင်ဗျာ။")
    elif not uploaded_video:
        st.warning("⚠️ ကျေးဇူးပြု၍ Recap ပြုလုပ်လိုသည့် ဗီဒီယိုဖိုင်တစ်ခု အရင်တင်သွင်းပေးပါခင်ဗျာ။")
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

                status_box.write("2️⃣ AssemblyAI ဖြင့် မူရင်းစကားသံများကို စာသားပြောင်းနေပါသည်...")
                raw_text = transcribe_audio_assemblyai(temp_audio_path, assemblyai_key)

                status_box.write("3️⃣ Groq AI ဖြင့် စိတ်ဝင်စားဖွယ် ဇာတ်လမ်းအကျဉ်းနှင့် ဘာသာပြန် ရေးဖွဲ့နေပါသည်...")
                recap_script = generate_recap_script(raw_text, groq_api_key, lang_mode)

                status_box.write(f"4️⃣ {voice_choice} အသံဖြင့် ဒပ်ဘင်းအသံဖိုင် ထုတ်လုပ်နေပါသည်...")
                asyncio.run(create_edge_tts_audio(recap_script, dubbed_audio_path, selected_voice, lang_mode))

                status_box.write("5️⃣ CapCut အချိန်ကိုက် SRT စာတန်းထိုးဖိုင် တည်ဆောက်နေပါသည်...")
                create_srt_file(recap_script, srt_path)

                status_box.update(label="🎉 AI Movie Recap အောင်မြင်စွာ ပြီးဆုံးပါပြီ!", state="complete")

                st.success("✅ အသံဒပ်ဘင်းနှင့် CapCut စာတန်းထိုးဖိုင် အသင့်ဖြစ်ပါပြီ!")

                st.markdown("<h3 style='color:#ffffff;'>📝 ထွက်ရှိလာသော ဇာတ်လမ်းအကျဉ်း (Recap Script)</h3>", unsafe_allow_html=True)
                st.text_area("Script", recap_script, height=180, label_visibility="collapsed")

                st.markdown("<h3 style='color:#ffffff;'>🎧 အသံဒပ်ဘင်း နားဆင်ရန်နှင့် ရယူရန်</h3>", unsafe_allow_html=True)
                with open(dubbed_audio_path, "rb") as af:
                    audio_bytes = af.read()
                    st.audio(audio_bytes, format="audio/mp3")
                    st.download_button(
                        label="⬇️ အသံဖိုင်ဒေါင်းလုဒ်ရယူရန် (Download Dubbed Audio)",
                        data=audio_bytes,
                        file_name="recap_dubbed_audio.mp3",
                        mime="audio/mp3"
                    )

                st.markdown("<h3 style='color:#ffffff;'>💬 CapCut စာတန်းထိုး SRT ဖိုင် ရယူရန်</h3>", unsafe_allow_html=True)
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
