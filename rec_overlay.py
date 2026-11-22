# -*- coding: utf-8 -*-
"""
录制监视窗（置顶、半透明、鼠标穿透）。
屏幕角落显示：红点闪烁 + “正在录制” + 当前软件名 + 预计剩余倒计时。
随 ffmpeg gdigrab 录屏一起被采集进画面。

用法：
  python rec_overlay.py --name "M3E Canvas" --total 60 [--x 1520] [--y 24] [--stopfile stop.flag]
退出：按 Esc，或在 --stopfile 路径创建空文件后自动退出。
"""
import argparse, os, time, tkinter as tk, ctypes, threading

ap = argparse.ArgumentParser()
ap.add_argument("--name", default="未命名软件")
ap.add_argument("--name-file", default="", help="从 UTF-8 文本文件读取软件名（规避命令行中文编码问题）")
ap.add_argument("--total", type=int, default=60, help="预计总时长（秒）")
ap.add_argument("--x", type=int, default=1516)
ap.add_argument("--y", type=int, default=24)
ap.add_argument("--stopfile", default="")
args = ap.parse_args()

if args.name_file and os.path.exists(args.name_file):
    with open(args.name_file, encoding="utf-8") as f:
        args.name = f.read().strip() or args.name

W, H = 380, 74
remaining = args.total
stop_flag = {"quit": False}

root = tk.Tk()
root.title("rec-overlay")
root.geometry(f"{W}x{H}+{args.x}+{args.y}")
root.overrideredirect(True)
root.attributes("-topmost", True)
root.attributes("-alpha", 0.9)

# 鼠标穿透/分层样式会导致 gdigrab 抓不到窗口内容，故默认不启用。
# 如需鼠标穿透，另走 PostMessage/点击排除，不在此加 WS_EX_LAYERED。

canvas = tk.Canvas(root, width=W, height=H, bg="#0f1620", highlightthickness=0, bd=0)
canvas.pack(fill="both", expand=True)
# 圆角底
canvas.create_round_rect = None
def round_rect(x1, y1, x2, y2, r, **kw):
    pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y2-r, x2,y2,
           x2-r,y2, x1+r,y2, x1,y2, x1,y2-r, x1,y1+r, x1,y1]
    return canvas.create_polygon(pts, smooth=True, **kw)
round_rect(2, 2, W-2, H-2, 16, fill="#16222e", outline="#2b3b4a", width=1)

dot = canvas.create_oval(22, 26, 44, 48, fill="#e5484d", outline="")
label_rec = canvas.create_text(56, 30, text="正在录制", fill="#ffffff",
                               font=("Microsoft YaHei", 15, "bold"), anchor="w")
label_name = canvas.create_text(56, 54, text=args.name, fill="#9fb3c4",
                                font=("Microsoft YaHei", 11), anchor="w")
label_time = canvas.create_text(W-20, 37, text="", fill="#ffd166",
                                font=("Consolas", 18, "bold"), anchor="e")

def fmt(sec):
    sec = max(0, int(sec))
    return f"{sec//60:02d}:{sec%60:02d}"

def refresh_time():
    global remaining
    total = args.total
    canvas.itemconfigure(label_time, text=f"{fmt(remaining)} / {fmt(total)}")
    if remaining <= 0:
        canvas.itemconfigure(label_rec, text="录制结束")
        canvas.itemconfigure(dot, fill="#5fd39a")

def blink():
    cur = canvas.itemcget(dot, "fill")
    canvas.itemconfigure(dot, fill="#e5484d" if cur != "#e5484d" else "#3a2022")
    root.after(500, blink)

def tick():
    global remaining
    if stop_flag["quit"]:
        root.destroy(); return
    if args.stopfile and os.path.exists(args.stopfile):
        root.destroy(); return
    if remaining > 0:
        remaining -= 1
        refresh_time()
    root.after(1000, tick)

def on_esc(_):
    stop_flag["quit"] = True

root.bind("<Escape>", on_esc)
refresh_time(); blink(); tick()
root.mainloop()
