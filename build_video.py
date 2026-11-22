# -*- coding: utf-8 -*-
"""
迅鸽传输打样成片合成框架（配置驱动）。
当前用已有截图占位；正式录屏片段放入 assets 后，替换 shots 里的 asset 路径即可。
输出 16:9 1920x1080，烧录中文字幕，混入旁白。
"""
import os, subprocess, json, sys

FF = r"D:\VideoUpscaler\ffmpeg.exe"
ASSETS = r"C:\Users\Administrator\WorkBuddy\video-project\assets"
OUT_DIR = r"C:\Users\Administrator\WorkBuddy\video-project\output"
os.makedirs(OUT_DIR, exist_ok=True)
os.chdir(ASSETS)

# 镜头时间线（秒），与 subtitles.srt 对齐
shots = [
    {"id": 1, "start": 0.000, "end": 3.694,  "asset": "cover.png",            "note": "痛点开场"},
    {"id": 2, "start": 4.337, "end": 7.827,  "asset": "dev-scene.png",        "note": "开发场景·对话流(复刻)"},
    {"id": 3, "start": 8.720, "end": 19.283, "asset": "dev-code.png",         "note": "开发场景·工程终端(复刻)"},
    {"id": 4, "start": 19.634,"end": 25.460, "asset": "desktop-online.png",   "note": "产品亮相"},
    {"id": 5, "start": 25.770,"end": 28.548, "asset": "android-chat.png",     "note": "拖拽传输(占位)"},
    {"id": 6, "start": 28.943,"end": 32.436, "asset": "desktop-received.png", "note": "离线排队(占位)"},
    {"id": 7, "start": 32.767,"end": 40.335, "asset": "android-msg-sent.png", "note": "直连图文(占位)"},
    {"id": 8, "start": 40.666,"end": 45.000, "asset": "cover.png",            "note": "版本收尾"},
]

W, H, FPS = 1920, 1080, 30
SEG_DIR = os.path.join(ASSETS, "segments")
os.makedirs(SEG_DIR, exist_ok=True)

def run(cmd):
    print("$", " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        print(r.stderr[-1500:])
        sys.exit(1)
    return r

# 1. 逐镜头生成片段
seg_files = []
TOTAL = 45.0
for idx, s in enumerate(shots):
    nxt = shots[idx+1]["start"] if idx+1 < len(shots) else TOTAL
    dur = round(nxt - s["start"], 3)
    src = os.path.join(ASSETS, s["asset"])
    seg = os.path.join(SEG_DIR, f"seg{s['id']}.mp4")
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
          f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x102028,fps={FPS}")
    run([FF, "-y", "-loop", "1", "-t", str(dur), "-i", src,
         "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), seg])
    seg_files.append(seg)

# 2. concat 列表
list_file = os.path.join(SEG_DIR, "list.txt")
with open(list_file, "w", encoding="utf-8") as f:
    for seg in seg_files:
        f.write(f"file '{seg}'\n")

silent = os.path.join(SEG_DIR, "silent.mp4")
run([FF, "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", silent])

# 3. 烧字幕 + 混旁白
final = os.path.join(OUT_DIR, "迅鸽传输打样样片.mp4")
style = ("FontName=Microsoft YaHei,FontSize=22,PrimaryColour=&H00FFFFFF,"
         "OutlineColour=&H00202020,BorderStyle=1,Outline=1.6,Shadow=0,Alignment=2,MarginV=42")
vf = f"subtitles=subtitles.srt:force_style='{style}'"
run([FF, "-y", "-i", silent, "-i", "voiceover.wav",
     "-vf", vf,
     "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
     "-c:a", "aac", "-b:a", "128k", "-shortest", final])

print("\nFINAL:", final, round(os.path.getsize(final)/1024, 1), "KB")
