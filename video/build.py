"""Build plc_pitch.mp4: narration (pyopenjtalk) + slides (render.js) -> ffmpeg."""
import json, subprocess, wave
from pathlib import Path
import numpy as np
import pyopenjtalk
import imageio_ffmpeg

ROOT = Path(__file__).parent
BUILD = ROOT / "build"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
LEAD, TAIL, FADE = 0.6, 0.9, 0.4

scenes = json.loads((ROOT / "scenes.json").read_text())
subprocess.run(["node", str(ROOT / "render.js")], check=True)

segments = []
for s in scenes:
    x, sr = pyopenjtalk.tts(s["narration"], speed=1.05)
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

lst = BUILD / "concat.txt"
lst.write_text("".join(f"file '{p}'\n" for p in segments))
subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
    "-c", "copy", "-movflags", "+faststart", str(ROOT / "plc_pitch.mp4")], check=True)
print("done")
