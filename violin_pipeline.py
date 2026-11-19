"""Pop/band violin transcription prototype. No false claims of violin isolation."""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def execute(command):
    print('> ' + ' '.join(map(str, command)), flush=True)
    subprocess.run([str(x) for x in command], check=True)


def ffmpeg_convert(ffmpeg, src, dst, start=None, duration=None, mono=False):
    cmd = [ffmpeg, '-hide_banner', '-loglevel', 'error', '-y']
    if start is not None:
        cmd += ['-ss', str(start)]
    cmd += ['-i', src, '-vn']
    if duration is not None:
        cmd += ['-t', str(duration)]
    cmd += ['-ar', '44100', '-ac', '1' if mono else '2', '-c:a', 'pcm_s16le', dst]
    execute(cmd)


def main():
    ap = argparse.ArgumentParser(description='Violin-only score prototype for pop and band music')
    ap.add_argument('--input', required=True, help='Local audio/video file')
    ap.add_argument('--out', default='output')
    ap.add_argument('--mode', choices=['demucs', 'mix', 'stem'], default='demucs',
                    help='demucs removes vocals/drums/bass; stem uses supplied isolated violin; mix transcribes original')
    ap.add_argument('--violin-stem', help='External genuinely isolated violin stem (required for mode=stem)')
    ap.add_argument('--start', type=float, default=0, help='Clip start in seconds')
    ap.add_argument('--duration', type=float, default=30, help='Clip duration in seconds; 0 means full file')
    ap.add_argument('--musescore', help='Optional MuseScore executable for PDF export')
    ap.add_argument('--skip-transcription', action='store_true', help='Only prepare candidate audio')
    args = ap.parse_args()
    inp = Path(args.input).expanduser().resolve()
    if not inp.is_file():
        ap.error('Input file does not exist: ' + str(inp))
    if args.start < 0 or args.duration < 0:
        ap.error('--start and --duration must be nonnegative')
    if args.mode == 'stem' and not args.violin_stem:
        ap.error('--mode stem requires --violin-stem')
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        ap.error('FFmpeg not found. Install FFmpeg and add ffmpeg.exe to PATH.')
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    original = out / 'original_clip.wav'
    ffmpeg_convert(ffmpeg, str(inp), str(original), args.start,
                   args.duration if args.duration > 0 else None)
    isolated = False
    notes = []
    if args.mode == 'stem':
        stem = Path(args.violin_stem).expanduser().resolve()
        if not stem.is_file():
            ap.error('Violin stem file does not exist: ' + str(stem))
        source = out / 'violin_only.wav'
        # External stem is expected to be aligned to original; clip same interval.
        ffmpeg_convert(ffmpeg, str(stem), str(source), args.start,
                       args.duration if args.duration > 0 else None)
        isolated = True  # User-supplied isolation, NOT verified by this script.
        notes.append('User-supplied violin stem: isolation quality not independently verified.')
    elif args.mode == 'demucs':
        try:
            import demucs  # noqa: F401
        except ImportError:
            ap.error('Demucs not installed. Run: python -m pip install demucs')
        sep_dir = out / 'demucs'
        execute([sys.executable, '-m', 'demucs', '-n', 'htdemucs', '-o', sep_dir, original])
        other = sep_dir / 'htdemucs' / original.stem / 'other.wav'
        if not other.exists():
            raise FileNotFoundError('Demucs other.wav not found: ' + str(other))
        source = out / 'other_instruments_candidate.wav'
        ffmpeg_convert(ffmpeg, str(other), str(source))
        notes.append('Demucs other includes violin AND potentially guitar, keys, and other instruments. NOT violin-only.')
    else:
        source = original
        notes.append('Original mixed audio; transcription may contain non-violin notes.')

    midi_path = None
    xml_path = None
    pdf_path = None
    if not args.skip_transcription:
        try:
            from basic_pitch.inference import predict
            from basic_pitch import ICASSP_2022_MODEL_PATH
        except ImportError:
            ap.error('Basic Pitch not installed. Run: python -m pip install basic-pitch')
        mono = out / 'transcription_input_mono.wav'
        ffmpeg_convert(ffmpeg, str(source), str(mono), mono=True)
        _, midi, _ = predict(str(mono), ICASSP_2022_MODEL_PATH)
        midi_path = out / 'violin_candidate.mid'
        midi.write(str(midi_path))
        try:
            import music21
        except ImportError:
            notes.append('music21 not installed: MusicXML skipped.')
        else:
            score = music21.converter.parse(str(midi_path))
            score.metadata = music21.metadata.Metadata()
            score.metadata.title = 'Violin candidate - human review required'
            xml_path = out / 'violin_candidate.musicxml'
            score.write('musicxml', fp=str(xml_path))
            if args.musescore:
                musescore = Path(args.musescore).expanduser().resolve()
                if not musescore.is_file():
                    ap.error('MuseScore executable not found: ' + str(musescore))
                pdf_path = out / 'violin_candidate.pdf'
                execute([str(musescore), '-o', str(pdf_path), str(xml_path)])
    manifest = {
        'input': str(inp), 'mode': args.mode, 'start_seconds': args.start,
        'duration_seconds': args.duration, 'original_clip': str(original),
        'transcription_source': str(source),
        'is_violin_only_claim': isolated,
        'isolation_verified': False,
        'midi': str(midi_path) if midi_path else None,
        'musicxml': str(xml_path) if xml_path else None,
        'pdf': str(pdf_path) if pdf_path else None,
        'notes': notes + ['Automatic pitch and rhythm estimates require listening and score correction.']
    }
    (out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Finished. Review manifest.json and audio:', out)


if __name__ == '__main__':
    main()
