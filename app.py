# ============================================================
# 🎬 AI MOVIE RECAP STUDIO
# Myanmar + English Voice
# Original Audio + AI Narration
# MP4 + TXT Download
# ============================================================

import sys
import subprocess
import importlib.util
import os
import re
import asyncio
import tempfile
import shutil
from pathlib import Path


# ============================================================
# AUTO INSTALL PYTHON PACKAGES
# ============================================================

REQUIRED_PACKAGES = {
    "streamlit": "streamlit",
    "edge_tts": "edge-tts",
    "pydub": "pydub",
}

for module, package in REQUIRED_PACKAGES.items():

    if importlib.util.find_spec(module) is None:

        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "install",
            package
        ])


# ============================================================
# IMPORTS
# ============================================================

import streamlit as st
import edge_tts
from pydub import AudioSegment


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Movie Recap Studio",
    page_icon="🎬",
    layout="wide"
)


# ============================================================
# TITLE
# ============================================================

st.title("🎬 AI Movie Recap Studio")

st.markdown(
    """
    **Myanmar + English AI Narration**

    🎙️ AI Voice  
    🔊 Original Movie Audio  
    🎬 Final MP4  
    📝 Script TXT
    """
)


# ============================================================
# VOICES
# ============================================================

MYANMAR_VOICE = "my-MM-NilarNeural"
ENGLISH_VOICE = "en-US-JennyNeural"


# ============================================================
# CHECK FFMPEG
# ============================================================

def check_ffmpeg():

    return shutil.which("ffmpeg") is not None


FFMPEG_AVAILABLE = check_ffmpeg()


if not FFMPEG_AVAILABLE:

    st.warning(
        """
        ⚠️ FFmpeg မတွေ့သေးပါ။

        Video + Audio ကို MP4 အဖြစ် ပြန်ပေါင်းဖို့
        FFmpeg လိုအပ်ပါတယ်။
        """
    )


# ============================================================
# LANGUAGE DETECTION
# ============================================================

def is_myanmar(text):

    return bool(
        re.search(
            r"[\u1000-\u109F]",
            text
        )
    )


# ============================================================
# SPLIT SCRIPT
# ============================================================

def split_script(text):

    """
    Myanmar / English စာကြောင်းတွေကို ခွဲပေးမယ်။
    """

    sentences = re.split(
        r"(?<=[။.!?])\s+|\n+",
        text
    )

    result = []

    for sentence in sentences:

        sentence = sentence.strip()

        if sentence:

            result.append(sentence)

    return result


# ============================================================
# GENERATE ONE TTS
# ============================================================

async def generate_tts(
    text,
    voice,
    output_file
):

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate="+0%",
        volume="+0%"
    )

    await communicate.save(
        output_file
    )


# ============================================================
# CREATE AI VOICE
# ============================================================

def create_ai_voice(
    script,
    output_file
):

    sentences = split_script(
        script
    )

    if not sentences:

        raise ValueError(
            "Script မရှိပါ။"
        )

    combined_audio = AudioSegment.empty()

    temp_folder = tempfile.mkdtemp()

    try:

        for index, sentence in enumerate(
            sentences
        ):

            # ----------------------------------------
            # Detect Language
            # ----------------------------------------

            if is_myanmar(sentence):

                voice = MYANMAR_VOICE

            else:

                voice = ENGLISH_VOICE


            # ----------------------------------------
            # Temporary MP3
            # ----------------------------------------

            part_file = os.path.join(
                temp_folder,
                f"part_{index}.mp3"
            )


            # ----------------------------------------
            # Generate Voice
            # ----------------------------------------

            asyncio.run(
                generate_tts(
                    sentence,
                    voice,
                    part_file
                )
            )


            # ----------------------------------------
            # Load Audio
            # ----------------------------------------

            audio = AudioSegment.from_file(
                part_file
            )


            # ----------------------------------------
            # Add Small Pause
            # ----------------------------------------

            combined_audio += audio

            combined_audio += (
                AudioSegment.silent(
                    duration=250
                )
            )


        # ----------------------------------------
        # Export Final AI Voice
        # ----------------------------------------

        combined_audio.export(
            output_file,
            format="mp3"
        )

    finally:

        shutil.rmtree(
            temp_folder,
            ignore_errors=True
        )


# ============================================================
# GET VIDEO AUDIO
# ============================================================

def get_video_duration(video):

    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    try:

        return float(
            result.stdout.strip()
        )

    except:

        return 0


# ============================================================
# CREATE FINAL VIDEO
# ============================================================

def create_final_video(
    video_file,
    ai_voice_file,
    output_file,
    original_volume
):

    # --------------------------------------------------------
    # AI Voice + Original Video Audio
    # --------------------------------------------------------

    command = [
        "ffmpeg",
        "-y",

        "-i",
        video_file,

        "-i",
        ai_voice_file,

        "-filter_complex",

        (
            f"[0:a]volume={original_volume}[orig];"
            "[1:a]volume=1.0[voice];"
            "[orig][voice]"
            "amix=inputs=2:"
            "duration=first:"
            "dropout_transition=2"
            "[mixed]"
        ),

        "-map",
        "0:v:0",

        "-map",
        "[mixed]",

        "-c:v",
        "copy",

        "-c:a",
        "aac",

        "-b:a",
        "192k",

        "-shortest",

        output_file
    ]


    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )


    if result.returncode != 0:

        raise RuntimeError(
            result.stderr
        )


# ============================================================
# VIDEO UPLOAD
# ============================================================

st.subheader(
    "🎬 1. Upload Movie / Video"
)

uploaded_video = st.file_uploader(
    "Upload MP4 / MOV / MKV",
    type=[
        "mp4",
        "mov",
        "mkv",
        "avi",
        "webm"
    ]
)


# ============================================================
# SCRIPT
# ============================================================

st.subheader(
    "📝 2. Enter Recap Script"
)

script = st.text_area(
    "AI Voice Script",
    height=350,
    placeholder=
    """
ဥပမာ -

ဒီဇာတ်လမ်းရဲ့ အစမှာတော့
အဓိကဇာတ်ကောင်ဟာ မထင်မှတ်ထားတဲ့
ပြဿနာတစ်ခုနဲ့ ရင်ဆိုင်ခဲ့ရပါတယ်။

But he didn't know that
this moment would completely
change his life.

အဲ့ဒီနောက်မှာတော့ သူ့ဘဝဟာ
တဖြည်းဖြည်း ပြောင်းလဲလာခဲ့ပါတယ်။
"""
)


# ============================================================
# ORIGINAL AUDIO VOLUME
# ============================================================

st.subheader(
    "🔊 3. Original Movie Audio"
)

original_volume = st.slider(
    "မူရင်း Video အသံ",
    min_value=0.0,
    max_value=1.0,
    value=0.20,
    step=0.05
)

st.caption(
    "0.20 ဆိုရင် မူရင်းအသံကို 20% လောက်ပဲထားပြီး AI Voice ကို အဓိကထားမယ်။"
)


# ============================================================
# OUTPUT OPTIONS
# ============================================================

st.subheader(
    "📦 4. Output"
)

st.info(
    """
    Final output:

    🎬 MP4 Video
    🎙️ Myanmar / English AI Voice
    🔊 Original Video Audio
    📝 TXT Script
    """
)


# ============================================================
# GENERATE BUTTON
# ============================================================

generate = st.button(
    "🚀 Generate Final Movie Recap",
    type="primary",
    use_container_width=True
)


# ============================================================
# GENERATE
# ============================================================

if generate:

    if not uploaded_video:

        st.error(
            "❌ Video အရင် Upload လုပ်ပါ။"
        )

        st.stop()


    if not script.strip():

        st.error(
            "❌ Recap Script အရင်ထည့်ပါ။"
        )

        st.stop()


    if not FFMPEG_AVAILABLE:

        st.error(
            """
            ❌ FFmpeg မရှိသေးလို့
            Final MP4 မထုတ်နိုင်သေးပါ။
            """
        )

        st.stop()


    # ========================================================
    # TEMP DIRECTORY
    # ========================================================

    work_dir = tempfile.mkdtemp()


    try:

        # ----------------------------------------------------
        # Save Uploaded Video
        # ----------------------------------------------------

        input_video = os.path.join(
            work_dir,
            "input_video.mp4"
        )

        with open(
            input_video,
            "wb"
        ) as f:

            f.write(
                uploaded_video.getbuffer()
            )


        # ----------------------------------------------------
        # AI Voice
        # ----------------------------------------------------

        ai_voice = os.path.join(
            work_dir,
            "ai_narration.mp3"
        )


        # ----------------------------------------------------
        # Final Video
        # ----------------------------------------------------

        final_video = os.path.join(
            work_dir,
            "final_movie_recap.mp4"
        )


        # ----------------------------------------------------
        # TXT
        # ----------------------------------------------------

        txt_file = os.path.join(
            work_dir,
            "movie_recap_script.txt"
        )


        # ====================================================
        # STEP 1
        # ====================================================

        st.write(
            "🎙️ Step 1/3 — AI Voice ထုတ်နေပါတယ်..."
        )

        progress = st.progress(
            0
        )


        create_ai_voice(
            script,
            ai_voice
        )

        progress.progress(
            35
        )


        # ====================================================
        # STEP 2
        # ====================================================

        st.write(
            "🎬 Step 2/3 — Video + Voice ပေါင်းနေပါတယ်..."
        )


        create_final_video(
            input_video,
            ai_voice,
            final_video,
            original_volume
        )


        progress.progress(
            75
        )


        # ====================================================
        # STEP 3
        # ====================================================

        st.write(
            "📝 Step 3/3 — Script File ပြုလုပ်နေပါတယ်..."
        )


        with open(
            txt_file,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(
                script
            )


        progress.progress(
            100
        )


        st.success(
            "🎉 Movie Recap ပြီးပါပြီ!"
        )


        # ====================================================
        # VIDEO PREVIEW
        # ====================================================

        st.subheader(
            "🎬 Final Video"
        )

        st.video(
            final_video
        )


        # ====================================================
        # DOWNLOAD VIDEO
        # ====================================================

        with open(
            final_video,
            "rb"
        ) as f:

            video_bytes = f.read()


        st.download_button(
            label="⬇️ Download Final MP4",
            data=video_bytes,
            file_name="movie_recap.mp4",
            mime="video/mp4",
            use_container_width=True
        )


        # ====================================================
        # DOWNLOAD SCRIPT
        # ====================================================

        with open(
            txt_file,
            "rb"
        ) as f:

            txt_bytes = f.read()


        st.download_button(
            label="📝 Download Script TXT",
            data=txt_bytes,
            file_name="movie_recap_script.txt",
            mime="text/plain",
            use_container_width=True
        )


        # ====================================================
        # AI VOICE PREVIEW
        # ====================================================

        st.subheader(
            "🎙️ AI Voice Preview"
        )

        st.audio(
            ai_voice,
            format="audio/mp3"
        )


    except Exception as e:

        st.error(
            "❌ Error ဖြစ်သွားပါတယ်။"
        )

        st.code(
            str(e)
        )


    finally:

        # ----------------------------------------------------
        # Don't delete immediately because Streamlit needs
        # the files for download / playback.
        # ----------------------------------------------------

        pass
