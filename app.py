import streamlit as st
import subprocess
import asyncio
import edge_tts
from groq import Groq
import assemblyai as aai
import base64
import os

st.set_page_config(page_title="AI Movie Recap Studio", page_icon="🎬", layout="wide")

# Image to Base64 function
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

bg_base64 = get_base64_image("bg.jpg")
kyaw_gyi_b64 = get_base64_image("kyaw_gyi.png")
shwe_ein_b64 = get_base64_image("shwe_ein.png")

# CSS Styling - 3D Bubble Effect & Custom Background
bg_style = f"""
    background: linear-gradient(rgba(15, 23, 42, 0.85), rgba(15, 23, 42, 0.85)), url("data:image/jpeg;base64,{bg_base64}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
""" if bg_base64 else "background-color: #0f172a;"

st.markdown(f"""
<style>
    .stApp {{
        {bg_style}
        color: #f8fafc;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}
    
    /* 3D Glass Bubble Container */
    .avatar-container {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 15px;
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.18);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: all 0.3s ease-in-out;
    }}
    .avatar-container:hover {{
        transform: translateY(-5px);
        box-shadow: 0 12px 40px 0 rgba(56, 189, 248, 0.35);
        border: 1px solid rgba(56, 189, 248, 0.5);
    }}
    
    /* 3D Bubble Avatar */
    .bubble-avatar {{
        width: 110px;
        height: 110px;
        border-radius: 50%;
        object-fit: cover;
        box-shadow: 
            inset 0 0 20px rgba(255, 255, 255, 0.6),
            inset 10px 10px 20px rgba(255, 255, 255, 0.3),
            0 10px 25px rgba(0, 0, 0, 0.5),
            0 0 15px rgba(56, 189, 248, 0.5);
        border: 3px solid rgba(255, 255, 255, 0.85);
        background: radial-gradient(circle at 30% 30%, rgba(255,255,255,0.4), rgba(0,0,0,0.2));
        margin-bottom: 12px;
    }}
    
    .avatar-title {{
        font-size: 1.15rem;
        font-weight: bold;
        color: #e2e8f0;
        margin-bottom: 4px;
    }}
    .avatar-desc {{
        font-size: 0.85rem;
        color: #94a3b8;
    }}
</style>
""", unsafe_allow_html=True)

st.title("🎬 AI Movie Recap Studio")
st.caption("One-Click Auto Recap: Myanmar & English Dubbing + Time-Synced CapCut SRT")

# Sidebar for Keys
st.sidebar.header("🔑 API Keys ချိန်ညှိချက်")
groq_key = st.sidebar.text_input("Groq API Key:", type="password", placeholder="gsk_...")
assembly_key = st.sidebar.text_input("AssemblyAI API Key:", type="password")

# Language Selection
st.subheader("🌐 ဘာသာစကား ရွေးချယ်ပါ (Language Mode)")
target_lang = st.radio(
    "Recap ပြုလုပ်မည့် ဘာသာစကား:",
    ["မြန်မာဘာသာ (Myanmar Dubbing)", "အင်္ဂလိပ်ဘာသာ (English Dubbing)"],
    horizontal=True
)

st.divider()

# 3D Avatar Voice Selection
st.subheader("🎙️ အသံရွေးချယ်ပါ (Voice Selection)")
col_v1, col_v2 = st.columns(2)

with col_v1:
    img_tag_1 = f'<img src="data:image/png;base64,{kyaw_gyi_b64}" class="bubble-avatar"/>' if kyaw_gyi_b64 else '<div class="bubble-avatar" style="background:#38bdf8; display:flex; align-items:center; justify-content:center; font-size:40px;">👨</div>'
    st.markdown(f"""
    <div class="avatar-container">
        {img_tag_1}
        <div class="avatar-title">ကျော်ကြီး (Kyaw Gyi)</div>
        <div class="avatar-desc">Male • ဇာတ်လမ်းပြော ခပ်နက်နက်အသံ</div>
    </div>
    """, unsafe_allow_html=True)

with col_v2:
    img_tag_2 = f'<img src="data:image/png;base64,{shwe_ein_b64}" class="bubble-avatar"/>' if shwe_ein_b64 else '<div class="bubble-avatar" style="background:#f472b6; display:flex; align-items:center; justify-content:center; font-size:40px;">👩</div>'
    st.markdown(f"""
    <div class="avatar-container">
        {img_tag_2}
        <div class="avatar-title">ရွှေအိမ် (Shwe Ein)</div>
        <div class="avatar-desc">Female • ကြည်လင်ပြတ်သား သဘာဝအသံ</div>
    </div>
    """, unsafe_allow_html=True)

voice_selected = st.radio("အသုံးပြုမည့် Persona ကို ရွေးချယ်ပါ:", ["ကျော်ကြီး (Male)", "ရွှေအိမ် (Female)"], horizontal=True)

st.divider()

# File Uploader
uploaded_file = st.file_uploader("📥 မူရင်း ဗီဒီယိုဖိုင် တင်ပါ (MP4, MKV, MOV)", type=["mp4", "mkv", "mov"])

def format_srt_time(ms):
    seconds = int(ms / 1000)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    millis = int(ms % 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{millis:03d}"

async def text_to_speech(text, output_file, voice_code):
    communicate = edge_tts.Communicate(text, voice_code)
    await communicate.save(output_file)

if st.button("🚀 Start Auto Recap (စတင်ပြုလုပ်မည်)", type="primary"):
    if not groq_key or not assembly_key:
        st.error("ကျေးဇူးပြု၍ ဘယ်ဘက် Sidebar တွင် Groq နှင့် AssemblyAI API Keys များကို အရင်ထည့်သွင်းပေးပါ။")
    elif not uploaded_file:
        st.error("ဗီဒီယိုဖိုင် အရင် တင်ပေးပါ။")
    else:
        video_input = "temp_input.mp4"
        with open(video_input, "wb") as f:
            f.write(uploaded_file.read())
        
        status_box = st.status("AI အဆင့်ဆင့် စတင်ဆောင်ရွက်နေပါသည်...", expanded=True)

        try:
            status_box.write("⏳ ၁/၅ - ဗီဒီယိုမှ စကားပြောအသံကို ခွဲထုတ်နေပါသည်...")
            orig_audio = "temp_audio.wav"
            subprocess.run(["ffmpeg", "-y", "-i", video_input, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", orig_audio], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            status_box.write("⏳ ၂/၅ - မူရင်း စကားပြောများကို အချိန်မှတ်နှင့်အတူ ထုတ်ယူနေပါသည်...")
            aai.settings.api_key = assembly_key
            config = aai.TranscriptionConfig(language_code="zh")
            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(orig_audio, config=config)

            if not transcript.sentences:
                st.error("ဗီဒီယိုထဲတွင် စကားပြောသံ မတွေ့ရှိပါ သို့မဟုတ် Error ဖြစ်ပေါ်နေပါသည်။")
            else:
                status_box.write("⏳ ၃/၅ - AI က Recap ဇာတ်လမ်းပြော ပုံစံဖြင့် ဘာသာပြန်နေပါသည်...")
                client = Groq(api_key=groq_key)
                chinese_lines = "\n".join([f"{idx+1}. {s.text}" for idx, s in enumerate(transcript.sentences)])

                if "မြန်မာဘာသာ" in target_lang:
                    prompt = f"""အောက်ပါ တရုတ်စကားပြောစာကြောင်းများကို မြန်မာဇာတ်ကား Movie Recap ပြောသလို သဘာဝကျပြီး ဆွဲဆောင်မှုရှိသော မြန်မာစကားပြောဖြင့် ဘာသာပြန်ပေးပါ။ မူရင်းစာကြောင်းအရေအတွက်နှင့် အစဉ်အတိုင်း အတိအကျ နံပါတ်စဉ်တပ်ပြီး ပြန်ပေးပါ:
{chinese_lines}"""
                else:
                    prompt = f"""Translate the following transcribed lines into engaging and natural English movie recap narration style. Keep the exact same line count and numbering:
{chinese_lines}"""

                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                )
                
                translated_content = chat_completion.choices[0].message.content
                trans_lines = [line.strip() for line in translated_content.split("\n") if line.strip()]

                srt_content = ""
                full_script = []

                for idx, sentence in enumerate(transcript.sentences):
                    text_line = sentence.text
                    if idx < len(trans_lines):
                        clean_line = trans_lines[idx]
                        if "." in clean_line[:4]:
                            clean_line = clean_line.split(".", 1)[-1].strip()
                        text_line = clean_line
                    
                    full_script.append(text_line)
                    start_t = format_srt_time(sentence.start)
                    end_t = format_srt_time(sentence.end)
                    srt_content += f"{idx+1}\n{start_t} --> {end_t}\n{text_line}\n\n"

                srt_filename = "Myanmar_Subtitles.srt" if "မြန်မာဘာသာ" in target_lang else "English_Subtitles.srt"
                with open(srt_filename, "w", encoding="utf-8") as f:
                    f.write(srt_content)

                status_box.write("⏳ ၄/၅ - ရွေးချယ်ထားသော အသံဖြင့် Dubbing အသံသွင်းနေပါသည်...")
                if "မြန်မာဘာသာ" in target_lang:
                    tts_voice = "my-MM-ThihaNeural" if "ကျော်ကြီး" in voice_selected else "my-MM-NilarNeural"
                else:
                    tts_voice = "en-US-GuyNeural" if "ကျော်ကြီး" in voice_selected else "en-US-JennyNeural"

                dubbed_audio = "dubbed_audio.mp3"
                asyncio.run(text_to_speech(" ... ".join(full_script), dubbed_audio, tts_voice))

                status_box.write("⏳ ၅/၅ - မူရင်းအသံဖျောက်၍ အသံအသစ်နှင့် ဗီဒီယို ပေါင်းစပ်နေပါသည်...")
                final_video = "final_recap_video.mp4"
                subprocess.run([
                    "ffmpeg", "-y", "-i", video_input, "-i", dubbed_audio,
                    "-map", "0:v:0", "-map", "1:a:0",
                    "-c:v", "copy", "-c:a", "aac",
                    "-shortest", final_video
                ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                status_box.update(label="🎉 အားလုံး အောင်မြင်စွာ ပြုလုပ်ပြီးပါပြီ!", state="complete", expanded=False)
                st.success("ဗီဒီယိုနှင့် CapCut စာတန်းထိုးဖိုင် အသင့်ဖြစ်ပါပြီ!")

                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    with open(final_video, "rb") as vf:
                        st.download_button("📥 Download Recap Video (.mp4)", vf, file_name="Recap_Video.mp4", mime="video/mp4")
                with col_d2:
                    with open(srt_filename, "rb") as sf:
                        st.download_button(f"📥 Download CapCut {srt_filename}", sf, file_name=srt_filename, mime="text/plain")

        except Exception as e:
            status_box.update(label="Error ဖြစ်ပေါ်ခဲ့ပါသည်", state="error")
            st.error(f"အမှားဖြစ်ရသည့်အကြောင်းအရင်း: {str(e)}")
