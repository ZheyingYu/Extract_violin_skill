# Violin Only v2 — Pop / Band Transcription (Windows)

A new prototype inspired by the **workflow concept** of [kiri603/To-Sheet-Music-Skill](https://github.com/kiri603/To-Sheet-Music-Skill). This is **not a verified fork** and does not include that repository's source code.

## What works and what does not

- Converts an authorized local video/audio file to WAV and optionally selects a 30-second test clip.
- **Demucs mode** reduces vocals/drums/bass and outputs `other_instruments_candidate.wav`. This is **NOT** isolated violin; it can still contain piano, guitar and other instruments.
- **Stem mode** accepts a genuinely isolated violin audio stem from an external violin-capable separator, and writes `violin_only.wav` (isolation quality not independently verified).
- Uses **Basic Pitch** to produce candidate MIDI; uses **music21** to produce candidate MusicXML; optional **MuseScore** export to PDF.
- **Not implemented:** automatic violin-targeted separation, melody-to-violin identification, high-fidelity polyphonic transcription, reliable rhythm/bowing/dynamics, Bilibili downloading.

## Windows setup — no winget needed

Install Python 3.11 from python.org and FFmpeg from ffmpeg.org (add the `bin` folder to PATH). In **64-bit PowerShell** from the extracted folder:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Installation of Basic Pitch / Demucs may require compatible Python, TensorFlow, PyTorch and other packages. If installation fails, share the **full error**; don't mix this environment with your existing Conda projects. First model execution may download weights. A CPU run can be slow.

Check FFmpeg:

```powershell
ffmpeg -version
```

## Run: pop or band recording

Use a local MP4/MP3/WAV you have rights to process:

```powershell
.\.venv\Scripts\python.exe violin_pipeline.py --input "C:\Music\song.mp4" --mode demucs --start 60 --duration 30 --out output
```

Outputs include `output/original_clip.wav`, `output/other_instruments_candidate.wav`, `output/violin_candidate.mid`, `output/violin_candidate.musicxml`, and `output/manifest.json`. The score may contain **other instruments' notes**.

To test separation alone (without Basic Pitch):

```powershell
.\.venv\Scripts\python.exe violin_pipeline.py --input "C:\Music\song.mp4" --mode demucs --skip-transcription
```

If you already have an actually isolated violin stem from another tool, use:

```powershell
.\.venv\Scripts\python.exe violin_pipeline.py --input "C:\Music\song.mp4" --mode stem --violin-stem "C:\Music\violin.wav" --start 60 --duration 30
```

**Important:** `--start` applies to BOTH the original and the supplied violin stem, assuming they start at the same time. If your stem was already cropped, use `--start 0` with a similarly cropped original.

To transcribe the unseparated mix (baseline):

```powershell
.\.venv\Scripts\python.exe violin_pipeline.py --input "C:\Music\song.mp4" --mode mix --start 60 --duration 30
```

For PDF export, open `violin_candidate.musicxml` in MuseScore Studio and export PDF. Or add `--musescore "C:\Path\To\MuseScore4.exe"` to a command.

## Suggested evaluation

Listen to original vs candidate audio. Compare melody pitches and onsets to a 10–20 note manually transcribed violin reference; check octave errors, vibrato fragmentation, and notes from guitar/keyboard. Only call the track isolated violin after listening confirms adequate isolation.

## Licensing / rights

Use files you have permission to download and process; respect rights in the recording and composition. Do not redistribute unauthorized audio or score copies.
