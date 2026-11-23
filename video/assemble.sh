#!/usr/bin/env bash
# Assemble the final video for post-x-the-agent-builds-a-game-from-20261122-1709.
# Layout (1920x1080, 30fps, silent, 32.0s total):
#   0.0-5.0s  Scene A — the one prompt, typed (PIL frames, 15fps)
#   5.0-13.0s Scene B — the agent working (PIL frames, 15fps)
#   13.0-29.5s Gameplay — real deterministic frames, win at ~24.3s
#   27.5-29.5s CTA text over the win screen
#   29.5-32.0s make.fun 16:9 referral end card (transparent webm) over a
#              background blurred + desaturated with a 0.8s ease-in;
#              referral code nq116kx7 typed letter by letter at 30.93s
#              (card comes to rest at 29.5 + 1.43 = 30.93).
set -euo pipefail
cd "$(dirname "$0")"

FONT=/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf
CODE="nq116kx7"

# Letter-by-letter typing: one drawtext per char, 0.05s apart, monospace
# advance 62px * 0.602 ~= 37.3px per char, starting at x=432.
# Full code is on screen from 31.28s to the 32.0s end.
TYPE_FILTERS=""
for i in $(seq 0 7); do
  ch="${CODE:$i:1}"
  t=$(python3 -c "print(f'{30.93 + $i * 0.05:.2f}')")
  x=$(python3 -c "print(f'{432 + $i * 37.3:.0f}')")
  TYPE_FILTERS="${TYPE_FILTERS}drawtext=text='${ch}':fontfile=${FONT}:fontsize=62:fontcolor=#191419:x=${x}:y=694:enable='gte(t,${t})',"
done

ffmpeg -y -v error \
  -framerate 15 -i frames-a/a-%04d.png \
  -framerate 15 -i frames-b/b-%04d.png \
  -framerate 30 -i frames-game/frame-%04d.png \
  -i endcard-16x9.webm \
  -filter_complex "\
[0:v]fps=30,format=yuv420p,settb=AVTB[a]; \
[1:v]fps=30,format=yuv420p,settb=AVTB[b]; \
[2:v]fps=30,format=yuv420p,settb=AVTB[c]; \
[a][b][c]concat=n=3:v=1:a=0,format=yuv420p[base]; \
[base]tpad=stop_mode=clone:stop_duration=2.5[base32]; \
[base32]split=2[pre][blur]; \
[blur]trim=29.5:32,boxblur=luma_radius=28:luma_power=1,eq=saturation=0.35,setpts=PTS-STARTPTS[blurred]; \
[pre]trim=0:30.3,setpts=PTS-STARTPTS[pre30]; \
[pre30][blurred]xfade=transition=fade:duration=0.8:offset=29.5[xf]; \
[xf]drawtext=text='YOUR TURN — COME BUILD ON make.fun':fontfile=${FONT}:fontsize=64:fontcolor=#ffd319:borderw=2:bordercolor=black:x=(w-text_w)/2:y=920:enable='between(t,27.5,29.5)'[cta]; \
[cta][3:v]overlay=0:0:enable='gte(t,29.5)'[card]; \
[card]drawbox=x=430:y=692:w=9:h=81:color=white:thickness=fill:enable='between(t,30.93,31.35)'[caret]; \
[caret]${TYPE_FILTERS}format=yuv420p[out]" \
  -map "[out]" -c:v libx264 -preset medium -crf 20 -r 30 \
  -movflags +faststart -an post-x-the-agent-builds-a-game.mp4

ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_name,width,height,r_frame_rate,codec_type -of default=noprint_wrappers=1 post-x-the-agent-builds-a-game.mp4
