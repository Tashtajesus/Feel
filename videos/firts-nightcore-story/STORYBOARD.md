---
compositionId: bgm
duration_s: 90.802
canvas: {"w": 1080, "h": 1920, "fps": 30}
style:
  font: "Unbounded / Space Mono"
  palette: ["#0B0617", "#2A0F4A", "#FF4FB4", "#4DF3FF", "#B9A3FF", "#FFF3FB"]
assets: false
build_notes:
  - "one paused timeline per frame"
  - "no remote assets; fonts in assets/fonts"
  - "persistent world layer (compositions/world.html: sky, starfield, audio-reactive neon ring) under every frame; fx layer (grain, scanlines, vignette) on top — frames are transparent"
  - "audio reactivity from assets/audio-data.json (30fps, 16 bands), sampled per frame"
avoid: ["light backgrounds", "text in IG UI zones", "tiny unreadable hero text"]
---

Track read: 81 BPM trap (hi-hat rolls everywhere), soft intro 0–7s, wall of energy 7–66s with
small breaths at 18, 31–34 and 42, hard stop at 66, decay 73–78, near-silent tail 78–90.8.

## Frame 1 — f1

- src: compositions/frames/01-f1.html
- duration: 6.827s
- span_sec: [0.0, 6.827]
- pacing: phrase_flow
- mood: [dreamy, tense]
- feel: sparse intro, a few soft hits, an accelerating perc roll (4.92–6.04) leading into the surge

### Groups

- **g1** — free_design
  - span_sec: [0.0, 6.827]
  - free_design: { dominant_system: "now-playing chip + title assembling out of blur", primitives: ["typewriter-reveal", "blur-resolve", "neon-flicker"], density_topology: "accumulate" }
  - anchors: [1.115, 1.579, 2.67, 4.133, 4.574, 4.923, 6.037, 6.618]
  - copy: ["now playing", "tashta x sickboyrostic", "firts"]

## Frame 2 — f2

- src: compositions/frames/02-f2.html
- duration: 11.238s
- span_sec: [6.827, 18.065]
- pacing: beat_cut
- mood: [hype, glitch]
- feel: first surge — heavy sub, snare roll 9.57–11.63, hi-hat rolls, dense

### Groups

- **g1** — free_design
  - span_sec: [6.827, 18.065]
  - free_design: { dominant_system: "giant 'firts' punch-in with pink/cyan chromatic ghosts on every snare, artist names on an orbiting ring", primitives: ["crash-zoom-in", "chromatic-split", "kinetic-letter-in"], density_topology: "pulse" }
  - anchors: [7.546, 7.593, 9.567, 10.495, 10.588, 11.262, 13.096, 13.56, 15.0, 16.579, 17.252, 17.995]
  - copy: ["firts", "tashta", "sickboyrostic"]

## Frame 3 — f3

- src: compositions/frames/03-f3.html
- duration: 23.986s
- span_sec: [18.065, 42.051]
- pacing: beat_cut
- mood: [hype, playful]
- feel: long driving section, one per bar downbeat, breath at 31–34, snare roll 39.57–41.24 into a drop

### Groups

- **g1** — free_design
  - span_sec: [18.065, 42.051]
  - free_design: { dominant_system: "manga speed lines + word slot on each downbeat, lilac dream dip 31–34", primitives: ["radial-burst-lines", "slot-machine-reveal", "palette-flip"], density_topology: "pulse" }
  - anchors: [19.574, 22.57, 25.588, 28.561, 31.579, 34.551, 37.547, 40.565, 39.567, 41.239]
  - copy: ["tashta", "x", "sickboyrostic", "firts", "night", "core", "firts"]

## Frame 4 — f4

- src: compositions/frames/04-f4.html
- duration: 24.01s
- span_sec: [42.051, 66.061]
- pacing: beat_cut
- mood: [glitch, aggressive]
- feel: peak — breath at 42 then surge at 43, dense snares through 66

### Groups

- **g1** — free_design
  - span_sec: [42.051, 66.061]
  - free_design: { dominant_system: "title tile mosaic wall that flips pink/cyan per bar, RGB glitch slices and shake on snares", primitives: ["tile-mosaic", "screen-shake", "datamosh-smear"], density_topology: "accumulate" }
  - anchors: [43.561, 46.579, 49.575, 52.57, 55.565, 58.561, 61.556, 64.575]
  - copy: ["firts", "tashta x sickboyrostic"]

## Frame 5 — f5

- src: compositions/frames/05-f5.html
- duration: 12.004s
- span_sec: [66.061, 78.065]
- pacing: beat_cut
- mood: [cinematic, dreamy]
- feel: hard stop at 66, surge back at 67, then energy decays 73→78

### Groups

- **g1** — free_design
  - span_sec: [66.061, 78.065]
  - free_design: { dominant_system: "blackout flash, crash-zoom title back in, then staggered dissolve as the track fades", primitives: ["flash-cut", "crash-zoom-in", "staggered-exit"], density_topology: "decay" }
  - anchors: [66.061, 67.57, 70.589, 73.584, 76.579]
  - copy: ["firts"]

## Frame 6 — f6

- src: compositions/frames/06-f6.html
- duration: 12.737s
- span_sec: [78.065, 90.802]
- pacing: phrase_flow
- mood: [dreamy, elegant]
- feel: near-silent tail, faint perc only — hold an end card

### Groups

- **g1** — free_design
  - span_sec: [78.065, 90.802]
  - free_design: { dominant_system: "calm end card lockup floating in the starfield", primitives: ["blur-resolve", "neon-flicker"], density_topology: "hold" }
  - anchors: [78.065, 79.575, 82.57, 85.589]
  - copy: ["tashta x sickboyrostic", "firts"]
