# Music playlist (qa3d/audio/music/)

Tracks are CC0, picked by Jacob. Credits: ../CREDITS.txt. The list lives in `CFG.music.tracks` in qa3d/main.js (empty list = silent, nothing fetched).

- Each track is a Web Audio buffer loop (gapless: LAME-tagged mp3, so `decodeAudioData` trims the encoder delay and padding; checked in Chrome,
  decoded length = the trimmed PCM length to the sample). It plays for whole loops (about `dwellSec` 150 s), then crossfades (`xfadeSec` 4 s)
  into the next track. The list rotates and wraps; outer_space_loop plays first.
- Only the first track loads, on the first tap (browser audio unlock). Each next track loads while the current one plays.
- Volume `CFG.music.vol` 0.28, ducks under Eve line audio / SFX (`musicDuck`). Settings (gear under the Eve bubble) > Music on/off is saved;
  music pauses while the page is hidden.
- To add a track: encode 96 kbps MP3 with LAME (`ffmpeg -i in.wav -c:a libmp3lame -b:a 96k out.mp3`) from PCM trimmed exactly to the loop,
  drop it here, add it to `CFG.music.tracks` and to ../CREDITS.txt.

Optional Eve line audio (calls stay text-only, no TTS): list files under `CFG.eveVoice.lines` as `{ beatId: ['line0.mp3', null, ...] }`,
files in qa3d/audio/eve/. A line plays only if it is listed.
