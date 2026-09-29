"""Build a narrated slide video and a silent copy from a scenes file.

  python3 build.py                  # scenes.json     -> plc_pitch.mp4 / plc_pitch_silent.mp4
  python3 build.py --short          # scenes_30s.json -> plc_pitch_30s.mp4 / plc_pitch_30s_silent.mp4

Narration: pyopenjtalk. Slides: render.js (Playwright). Joined with ffmpeg.
"""
import json, subprocess, sys, wave
from pathlib import Path
import numpy as np
import pyopenjtalk
import imageio_ffmpeg

ROOT = Path(__file__).parent
BUILD = ROOT / "build"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
FADE = 0.4

if "--short" in sys.argv:
    SCENES, OUT, LEAD, TAIL, SPEED = "scenes_30s.json", "plc_pitch_30s", 0.3, 0.5, 1.1
else:
    SCENES, OUT, LEAD, TAIL, SPEED = "scenes.json", "plc_pitch", 0.6, 0.9, 1.05

scenes = json.loads((ROOT / SCENES).read_text())
subprocess.run(["node", str(ROOT / "render.js"), str(ROOT / SCENES)], check=True)

segments = []
for s in scenes:
    x, sr = pyopenjtalk.tts(s["narration"], speed=SPEED)
    pad = lambda sec: np.zeros(int(sr * sec))
    x = np.concatenate([pad(LEAD), x, pad(TAIL)])
    x = np.clip(x, -32768, 32767).astype(np.int16)
    wav = BUILD / f"{s['id']}.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(x.tobytes())
    dur = len(x) / sr
    seg = BUILD / f"{s['id']}.mp4"
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-loop", "1", "-framerate", "30",
        "-i", str(BUILD / f"{s['id']}.png"), "-i", str(wav), "-t", f"{dur:.3f}",
        "-vf", f"fade=in:st=0:d={FADE},fade=out:st={dur - FADE:.3f}:d={FADE},format=yuv420p",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "160k", "-ar", "48000", str(seg)], check=True)
    segments.append(seg)
    print(f"{s['id']}: {dur:.1f}s")

lst = BUILD / f"{OUT}_concat.txt"
lst.write_text("".join(f"file '{p}'\n" for p in segments))
subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
    "-c", "copy", "-movflags", "+faststart", str(ROOT / f"{OUT}.mp4")], check=True)
# Same slides and timing without narration, e.g. for autoplaying social feeds.
subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(ROOT / f"{OUT}.mp4"),
    "-an", "-c:v", "copy", "-movflags", "+faststart", str(ROOT / f"{OUT}_silent.mp4")], check=True)
print("done")
