# Brazil reel – "23 goals at 13"

Vertical 1080x1920 / 30 fps reel (54.3 s), styled after the Pirlo PlayStation reel: cartoon characters with thick outlines,
small white captions, a big title (year + place), shout words, a pill counter widget and quick cuts with punch-ins.

- `brazil_reel.mp4` – the finished video
- `instagram_caption.txt` – post text
- `render.html` – all scenes, drawn with Canvas 2D (`renderFrame(t)`)
- `render.js` – Playwright driver: `node render.js preview 3.2 10` for stills, `node render.js video out.mp4` to render
- `audio.py` – synthesised bossa-style music bed and sound effects
- `words.json` – word timings of the voiceover (ElevenLabs voice "Chris" via vidIQ), used for captions

Mux: voiceover (loudnorm -16 LUFS) + `audio.py` output, see the commit message for the ffmpeg command.
