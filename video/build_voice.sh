#!/usr/bin/env bash
# 30s cut over the recorded narration (../audio/recording.mp4).
# Slide cuts sit in the pauses of the recording; run `python3 build.py --short` first for the PNGs.
set -e
cd "$(dirname "$0")"
F=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
ids=(s1_question s2_case_score s3_case_topics s4_trainer s5_trial)
cuts=(0 4.1 12.8 19.1 24.85 29.29)
: > build/voice_concat.txt
for i in 0 1 2 3 4; do
  d=$(python3 -c "print(round(${cuts[$((i+1))]}-${cuts[$i]},3))")
  o=$(python3 -c "print(round($d-0.3,3))")
  $F -y -loglevel error -loop 1 -framerate 30 -i "build/${ids[$i]}.png" -t "$d" \
    -vf "fade=in:st=0:d=0.3,fade=out:st=$o:d=0.3,format=yuv420p" \
    -c:v libx264 -preset medium -crf 20 -tune stillimage "build/v_${ids[$i]}.mp4"
  echo "file '$PWD/build/v_${ids[$i]}.mp4'" >> build/voice_concat.txt
done
$F -y -loglevel error -f concat -safe 0 -i build/voice_concat.txt -i ../audio/recording.mp4 \
  -map 0:v -map 1:a -c copy -movflags +faststart plc_pitch_30s_voice.mp4
