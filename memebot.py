# ===============================================================
#                ULTRA VIRAL MEME BOT — FINAL CLEAN BUILD
# ===============================================================

import os
import random
import time
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
import textwrap

import requests
import pyautogui
from moviepy.editor import (
    VideoFileClip,
    CompositeVideoClip,
    ImageClip,
    AudioFileClip,
    ColorClip,
    afx,
)
from PIL import Image, ImageDraw, ImageFont
import numpy as np


# ===========================
# PUT YOUR API KEYS HERE
# ===========================
OPENAI_API = "your api keys"
GIPHY_API_KEY = "api keys"


# ===========================
# CONFIG
# ===========================
BASE_DIR = Path(r"C:\memebot")
SONG_FOLDER = BASE_DIR / "New folder"

TMP_GIF = BASE_DIR / "temp.gif"
OUTPUT_TEMPLATE = BASE_DIR / "MEME_{:04d}.mp4"

OUTPUT_W = 1080
OUTPUT_H = 1920
TARGET_DURATION = 5.5
BASE_HEADER = 420
FONT_NAME = "arialbd.ttf"
TEXT_WRAP = 22

NUM_UPLOADS_PER_DAY = 20

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

pyautogui.FAILSAFE = True
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")


# ===========================
# COORDINATES (FULLSCREEN)
# ===========================
RECORDED_LEFT_WIDTH = 1920
RECORDED_SCREEN_W = 1440
RECORDED_SCREEN_H = 900

RECORDED_COORDS = {
    "upload": (3218, 100),
    "select_files": (2640, 569),
    "title": (2223, 284),
    "description": (2226, 429),
    "not_for_kids": (2220, 584),
    "next": (3065, 817),
    "public": (2269, 470),
    "publish": (3066, 809),
}

SCREEN_W, SCREEN_H = pyautogui.size()

def _scale_coord(x, y):
    x_local = x - RECORDED_LEFT_WIDTH
    return int((x_local / RECORDED_SCREEN_W) * SCREEN_W), int((y / RECORDED_SCREEN_H) * SCREEN_H)

COORDS = {name: _scale_coord(*xy) for name, xy in RECORDED_COORDS.items()}


# ===========================
# GIF SOURCES
# ===========================
GIF_SOURCES = [
    "patrick star reaction",
    "patrick star shocked",
    "patrick star side eye",
    "spongebob confused",
    "spongebob goofy",
    "squidward reaction meme",
    "walter white reaction",
    "walter white staring",
    "jesse pinkman reaction",
    "saul goodman reaction",
    "gus fring reaction",
    "peter griffin reaction",
    "peter griffin shocked",
    "stewie reaction meme",
    "jim halpert reaction",
    "michael scott reaction meme",
    "dwight schrute reaction",
    "homer simpson reaction",
    "bart simpson reaction",
    "marge simpson reaction meme",
    "futurama fry reaction",
    "fry not sure if meme",
    "shrek reaction gif",
    "puss in boots reaction meme",
    "donkey shrek reaction meme",
    "luffy reaction meme",
    "zoro reaction meme",
    "eren yeager reaction",
    "gojo shocked meme",
    "cat reaction gif",
    "confused cat gif",
    "angry cat meme",
    "awkward monkey puppet",
]


# ===========================
# HELPERS
# ===========================
def retry(func, tries=3):
    last = None
    for _ in range(tries):
        try:
            return func()
        except Exception as e:
            last = e
            time.sleep(1)
    raise last

def click(coord, wait=0.7):
    pyautogui.moveTo(*coord, duration=0.15)
    pyautogui.click()
    time.sleep(wait)

def write(text):
    pyautogui.typewrite(text, interval=0.02)
    time.sleep(0.2)


# ===========================
# CHROME — RESTORE PAGE FIXED
# ===========================
def open_chrome():
    chrome_args = [
        CHROME_PATH,
        "--new-window",
        "--start-maximized",
        "--restore-last-session=false",
        "--disable-session-crashed-bubble",
        "--noerrdialogs",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-session-restore",
        "--hide-crash-restore-bubble",
        "--disable-popup-blocking",
        "--overscroll-history-navigation=0",
        "--disable-features=InfiniteSessionRestore",
        "--disable-features=SessionRestore",
        "https://studio.youtube.com",
    ]

    proc = subprocess.Popen(chrome_args)
    time.sleep(8)
    try:
        pyautogui.press("f11")
    except:
        pass
    return proc


# ===========================
# GIF FETCH
# ===========================
def fetch_gif():
    def _req():
        query = random.choice(GIF_SOURCES)
        url = "https://api.giphy.com/v1/gifs/search"
        params = {
            "api_key": GIPHY_API_KEY,
            "q": query,
            "limit": 25,
            "rating": "pg-13"
        }
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()

        data = r.json()["data"]
        good = []
        for d in data:
            try:
                img = d["images"]["original"]
                w = int(img["width"])
                h = int(img["height"])
                if w > 300 and h > 300:
                    good.append(img["url"])
            except:
                pass

        if not good:
            raise RuntimeError("No GIFs found")

        chosen = random.choice(good[:10])
        TMP_GIF.write_bytes(requests.get(chosen, timeout=15).content)
        return str(TMP_GIF)

    return retry(_req)


# ===========================
# CAPTION GENERATION
# ===========================

NIGHT_PROMPT = """
Generate 10 viral 3AM doomscrolling captions.
Tone: depressed, guilty, chronically-online, emotional, tired, overthinking.
Must feel like someone losing control of their life at 3AM.
10–15 words. No emojis. No quotes. No numbering.
Use hyper-specific times like 2:47AM, 3:11AM, 4:02AM.
One caption per line.
"""

DAY_PROMPT = """
Generate 10 captions.

RULES:
- Tone: dark, hyper-specific, relatable, exaggerated realism, MrUnknownXD style.
- No emojis.
- No hashtags.
- No numbers at the start.
- 10–17 words max.
- One situation per caption.
- Must feel like: hyper-specific moment I didn’t know was relatable.
- Must include absurdly exact times, weights, distances, or relationship trauma.
- Acceptable themes: dad forcing you to lift insane weights, gaming at 3AM, wife irritated, kids doing dangerous things, funerals, construction workers doing impossible things, unexpected sounds in the house, responsibility avoidance.

FORMAT:
One caption per line.
No numbering.
No quotes.
"""

def generate_captions():
    def ask(prompt):
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {OPENAI_API}"}
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 300,
            "temperature": 0.95,
        }
        r = requests.post(url, json=payload, headers=headers, timeout=20)
        r.raise_for_status()
        lines = r.json()["choices"][0]["message"]["content"].split("\n")
        clean = [l.strip() for l in lines if l.strip()]
        return clean

    night = ask(NIGHT_PROMPT)
    day = ask(DAY_PROMPT)

    combined = night + day
    random.shuffle(combined)
    return combined[:20]


# ===========================
# SONG
# ===========================
def get_song():
    for file in SONG_FOLDER.iterdir():
        if file.suffix.lower() in [".mp3", ".wav", ".m4a", ".aac", ".flac"]:
            return str(file)
    raise FileNotFoundError("No song found")

def song_clip(duration):
    audio = AudioFileClip(get_song())
    if audio.duration < duration:
        return afx.audio_loop(audio, duration=duration)
    return audio.subclip(0, duration)


# ===========================
# HEADER TEXT
# ===========================
def create_header(caption):
    img = Image.new("RGB", (OUTPUT_W, BASE_HEADER), "white")
    draw = ImageDraw.Draw(img)

    lines = textwrap.wrap(caption, width=TEXT_WRAP)
    font_size = 90

    while True:
        try:
            font = ImageFont.truetype(FONT_NAME, font_size)
        except:
            font = ImageFont.load_default()

        bbox = font.getbbox("A")
        line_h = (bbox[3] - bbox[1]) + 15
        total_h = len(lines) * line_h

        if total_h <= BASE_HEADER - 40:
            break

        font_size -= 5
        if font_size < 40:
            break

    y = (BASE_HEADER - total_h) // 2

    for line in lines:
        w = draw.textlength(line, font=font)
        x = (OUTPUT_W - w) // 2
        draw.text((x, y), line, fill="black", font=font)
        y += line_h

    return ImageClip(np.array(img))


# ===========================
# BUILD MEME
# ===========================
def build_meme(gif_path, caption, outpath):
    clip = VideoFileClip(gif_path)

    if clip.duration < TARGET_DURATION:
        loop = int(TARGET_DURATION / clip.duration) + 1
        clip = clip.loop(loop)
    clip = clip.subclip(0, TARGET_DURATION)

    header = create_header(caption).set_duration(TARGET_DURATION)

    gif_h = OUTPUT_H - BASE_HEADER
    gif_scale = min(OUTPUT_W / clip.w, gif_h / clip.h)
    resized = clip.resize(gif_scale)
    y_pos = BASE_HEADER + (gif_h - resized.h) // 2
    resized = resized.set_position((0, y_pos))

    bg = ColorClip((OUTPUT_W, OUTPUT_H), (255, 255, 255)).set_duration(TARGET_DURATION)

    final = CompositeVideoClip([bg, header, resized])
    final = final.set_audio(song_clip(TARGET_DURATION))
    final.write_videofile(str(outpath), fps=24, codec="libx264", audio_codec="aac", logger=None)

    clip.close()
    final.close()


# ===========================
# UPLOAD BOT
# ===========================
def upload(path):
    logging.info(f"Uploading: {path}")
    proc = open_chrome()

    click(COORDS["upload"])
    click(COORDS["select_files"])
    write(path)
    pyautogui.press("enter")
    time.sleep(6)

    click(COORDS["title"])
    pyautogui.hotkey("ctrl", "a")
    pyautogui.press("backspace")
    write("#shorts #memes")

    click(COORDS["description"])
    pyautogui.hotkey("ctrl", "a")
    pyautogui.press("backspace")
    write("#memes #shorts")

    for _ in range(5):
        pyautogui.scroll(-800)

    click(COORDS["not_for_kids"])
    click(COORDS["next"])
    click(COORDS["next"])
    click(COORDS["next"])
    click(COORDS["public"])
    click(COORDS["publish"])

    time.sleep(5)
    os.remove(path)
    proc.kill()


# ===========================
# FIXED UPLOAD SCHEDULE
# ===========================
def make_fixed_schedule():
    today = datetime.now().replace(second=0, microsecond=0)

    slots = []

    # Batch 1 — 10 strongest (01:40–02:00)
    t = today.replace(hour=1, minute=40)
    for _ in range(10):
        slots.append(t)
        t += timedelta(minutes=2)

    # Batch 2 — 5 medium (02:40–03:00)
    t = today.replace(hour=2, minute=40)
    for _ in range(5):
        slots.append(t)
        t += timedelta(minutes=4)

    # Batch 3 — 5 peak (03:20–03:40)
    t = today.replace(hour=3, minute=20)
    for _ in range(5):
        slots.append(t)
        t += timedelta(minutes=4)

    return slots


# ===========================
# ONE DAY LOOP
# ===========================
def generate_memes(n):
    captions = generate_captions()
    out = []

    for _ in range(n):
        gif = fetch_gif()
        cap = captions.pop(0)
        fp = OUTPUT_TEMPLATE.with_name(f"MEME_{random.randint(1000,9999)}.mp4")
        build_meme(gif, cap, fp)
        out.append(str(fp))

    return out


def run_one_day():
    logging.info("Generating memes for the day...")
    vids = generate_memes(NUM_UPLOADS_PER_DAY)
    schedule = make_fixed_schedule()

    print("\n=========== TODAY'S FIXED UPLOAD SCHEDULE ===========")
    for vid, t in zip(vids, schedule):
        print(f"{t.strftime('%Y-%m-%d %H:%M:%S')}  →  {vid}")
    print("======================================================\n")

    for vid, t in zip(vids, schedule):
        while datetime.now() < t:
            time.sleep(10)
        upload(vid)


# ===========================
# INFINITE LOOP
# ===========================
if __name__ == "__main__":
    while True:
        try:
            run_one_day()
        except Exception as e:
            logging.error(f"Error: {e}")
            time.sleep(60)

