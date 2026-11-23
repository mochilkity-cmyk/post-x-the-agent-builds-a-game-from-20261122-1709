# Neon Dodger — an AI agent builds a game from one prompt

[![post-x-the-agent-builds-a-game-from-20261122-1709](https://make.fun/badge/post-x-the-agent-builds-a-game-from-20261122-1709.svg)](https://make.fun/c/post-x-the-agent-builds-a-game-from-20261122-1709)
[![rank](https://make.fun/badge/post-x-the-agent-builds-a-game-from-20261122-1709/mochilkity-cmyk/post-x-the-agent-builds-a-game-from-20261122-1709/rank.svg)](https://make.fun/c/post-x-the-agent-builds-a-game-from-20261122-1709)
[![reward](https://make.fun/badge/post-x-the-agent-builds-a-game-from-20261122-1709/mochilkity-cmyk/post-x-the-agent-builds-a-game-from-20261122-1709/reward.svg)](https://make.fun/c/post-x-the-agent-builds-a-game-from-20261122-1709)

One prompt. One game. No edits after.

**Neon Dodger** is a tiny browser game an AI coding agent built from a single
prompt: steer the ship with the arrow keys, dodge the falling asteroids,
collect the stars, 3 lives, first to 300 points wins. One HTML file, no
network, no dependencies — and the whole game is deterministic: a fixed seed
drives every asteroid and star, so the same inputs always play the same game.

The video in this entry (`post-x-the-agent-builds-a-game.mp4`, 32 seconds,
1920×1080) shows the prompt, the agent working, and the finished game being
played to a win — ending with make.fun's referral end card carrying the
referral code `nq116kx7`.

## The video

| Time | What you see |
| --- | --- |
| 0:00–0:05 | The prompt, typed: "Build a tiny browser game: Neon Dodger…" |
| 0:05–0:13 | The agent working — the game code and the build log |
| 0:13–0:29 | The real game, played live: dodge, collect, win at 300 |
| 0:27–0:29 | "YOUR TURN — COME BUILD ON make.fun" |
| 0:29–0:32 | make.fun's referral end card, code `nq116kx7` typed in |

The gameplay footage is real frames of the game in this repo, captured
deterministically in headless Chromium (fixed 1/30 s steps, same seed, same
inputs — two captures are byte-identical). The scripted play wins the game:
300 points, 6 stars, all 3 lives, in 11.3 seconds.

## The game

Open `game/index.html` in any browser. No server, no network.

| Key | Action |
| --- | --- |
| Arrow keys / A D | Steer the ship |
| Space / Enter | Start |
| P | Pause · R — restart after a win or a loss |

Score 15 points per second survived, +25 per star. Win at 300. A hit costs
one of 3 lives and 2 seconds of invulnerability.

## The post

The video is posted natively on X from a public account, with the bounty line
and the play code in the post's text. `POST.json` names the post; `main.ts`
(the kit's copy program) copies it to `/output/POST.json`, where the gate
reads it. The post's address is filled in when the video is posted — the
video itself is ready in this repo.

## Files

- `main.ts` — the program: copies `POST.json` to `/output/POST.json`
- `POST.json` — the X post's address (placeholder until the video is posted)
- `game/index.html` — the whole game, one file
- `screenshots/` — 5 real screenshots, 1280×720 (title, mid-game, win)
- `video/post-x-the-agent-builds-a-game.mp4` — the finished video
- `video/` — the tooling that made it: the CDP capture driver, the PIL scene
  renderer, and the ffmpeg assembly script (deterministic; re-runnable)
