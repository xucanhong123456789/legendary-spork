# -*- coding: utf-8 -*-
"""
批量成片流水线（配置驱动，复用旧迅鸽打样链路）。
用法: python build_pipeline.py <config.json>

config.json 示例:
{
  "title": "记账助手",
  "out_name": "01-记账助手.mp4",
  "voiceover": "voiceover.wav",
  "subtitles": "subtitles.srt",
  "bg_color": "0x102028",
  "clips": [
    {"asset": "cover.png", "dur": 5.0, "note": "开场"},
    {"asset": "demo1.mp4", "note": "主界面演示"}
  ]
}

规则:
- 工作目录即 config.json 所在目录；asset/voiceover/subtitles 均为相对该目录。
- 图片 clip 必须给 dur（秒）；视频 clip 不给 dur 则用整条，给 dur 则截取前 dur 秒。
- 输出 16:9 1920x1080 30fps，烧录中文字幕，混入旁白，-shortest 收尾。
- 脱敏: 素材入镜前已清理；脚本不写入任何路径/账号信息。
"""
import os, json, subprocess, sys

FF = r"D:\VideoUpscaler\ffmpeg.exe"
W, H, FPS = 1920, 1080, 30
STYLE = ("FontName=Microsoft YaHei,FontSize=22,PrimaryColour=&H00FFFFFF,"
         "OutlineColour=&H00202020,BorderStyle=1,Outline=1.6,Shadow=0,Alignment=2,MarginV=42")


def run(cmd):
    print("$", " ".join(str(x) for x in cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        print(r.stderr[-1500:])
        sys.exit(1)
    return r


def main(cfg_path):
    work = os.path.dirname(os.path.abspath(cfg_path))
    cfg = json.load(open(cfg_path, encoding="utf-8"))
    os.chdir(work)

    bg = cfg.get("bg_color", "0x102028")
    seg_dir = os.path.join(work, "segments")
    os.makedirs(seg_dir, exist_ok=True)
    clips = cfg["clips"]
    seg_files = []

    for i, c in enumerate(clips):
        src = os.path.join(work, c["asset"])
        if not os.path.exists(src):
            print("MISS asset:", src); sys.exit(1)
        seg = os.path.join(seg_dir, f"seg{i+1}.mp4")
        is_img = os.path.splitext(src)[1].lower() in (".png", ".jpg", ".jpeg", ".webp", ".bmp")
        vf = (f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
              f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color={bg},fps={FPS}")
        if is_img:
            dur = float(c["dur"])
            run([FF, "-y", "-loop", "1", "-t", str(dur), "-i", src,
                 "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), seg])
        else:
            cmd = [FF, "-y", "-i", src]
            if c.get("dur"):
                cmd += ["-t", str(float(c["dur"]))]
            cmd += ["-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), seg]
            run(cmd)
        seg_files.append(seg)

    list_file = os.path.join(seg_dir, "list.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for seg in seg_files:
            f.write(f"file '{seg}'\n")

    silent = os.path.join(seg_dir, "silent.mp4")
    run([FF, "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", silent])

    out_dir = os.path.join(work, "..", "output")
    os.makedirs(out_dir, exist_ok=True)
    final = os.path.join(out_dir, cfg["out_name"])
    vf = f"subtitles={cfg['subtitles']}:force_style='{STYLE}'"
    run([FF, "-y", "-i", silent, "-i", cfg["voiceover"],
         "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
         "-c:a", "aac", "-b:a", "128k", "-shortest", final])
    print("\nFINAL:", final, round(os.path.getsize(final) / 1024, 1), "KB")


if __name__ == "__main__":
    main(sys.argv[1])
