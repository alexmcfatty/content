#!/usr/bin/env python3
"""Auto-cut for talking clips: transcribe, then cut silences and filler words.

Usage:
  python3 tools/autocut.py transcribe CLIP.MOV
      -> edits/CLIP.txt  (numbered lines with timestamps, for picking takes)
  python3 tools/autocut.py cut CLIP.MOV [--keep 1.2-8.4,10-15] [--gap 0.35] [--pad 0.08]
      -> edits/CLIP_cut.mp4 (+ CLIP_cut.srt captions and CLIP_cut.words.json on the new timeline)
  python3 tools/autocut.py frames FILE [--every 1]
      -> edits/frames/FILE/*.jpg stills, so Claude can see framing and what's in a clip
  python3 tools/autocut.py library
      -> lists broll/ with lengths, shape and tags (from the file names)
  python3 tools/autocut.py broll edits/CLIP_cut.mp4 PLAN.txt
      -> edits/CLIP_cut_broll.mp4, b-roll laid over the cut (lines: start length file [from])

--keep limits the cut to those time ranges (seconds), e.g. to drop a fluffed take.
Needs ffmpeg and whisper-cli (Homebrew) and a model in ~/.whisper-models.
"""
import json, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'edits')
MODEL = os.path.expanduser('~/.whisper-models/ggml-base.en.bin')
BIN = '/opt/homebrew/bin'
FILLERS = {'um', 'uh', 'umm', 'uhh', 'erm', 'ah', 'hmm'}


def run(cmd, capture=False):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit('Failed: ' + ' '.join(cmd[:3]) + '\n' + r.stderr[-1500:])
    return r.stdout + r.stderr if capture else None


def audio_stream(clip):
    """iPhones add a spatial-audio track ffmpeg can't decode; use the AAC one."""
    out = run([BIN + '/ffprobe', '-v', 'error', '-select_streams', 'a',
               '-show_entries', 'stream=index,codec_name', '-of', 'csv=p=0', clip], True)
    streams = [l.split(',') for l in out.strip().splitlines() if l]
    for idx, codec in streams:
        if codec == 'aac':
            return idx
    return streams[0][0]


def words(clip):
    """Word timestamps (seconds), cached next to the output."""
    os.makedirs(OUT, exist_ok=True)
    name = os.path.splitext(os.path.basename(clip))[0]
    cache = os.path.join(OUT, name + '.words.json')
    if os.path.exists(cache) and os.path.getmtime(cache) > os.path.getmtime(clip):
        return json.load(open(cache))
    tmp = tempfile.mkdtemp()
    wav = os.path.join(tmp, 'a.wav')
    run([BIN + '/ffmpeg', '-v', 'error', '-y', '-i', clip, '-map', '0:' + audio_stream(clip),
         '-vn', '-ac', '1', '-ar', '16000', wav])
    run([BIN + '/whisper-cli', '-m', MODEL, '-f', wav, '-ojf', '-of', os.path.join(tmp, 'a'),
         '-ml', '1', '-sow', '-np'])
    data = json.load(open(os.path.join(tmp, 'a.json')))
    ws = [{'w': s['text'].strip(), 'a': s['offsets']['from'] / 1000, 'b': s['offsets']['to'] / 1000}
          for s in data['transcription'] if s['text'].strip()]
    json.dump(ws, open(cache, 'w'))
    return ws


def silences(clip, noise='-32dB', min_len=0.3):
    out = run([BIN + '/ffmpeg', '-hide_banner', '-i', clip, '-map', '0:' + audio_stream(clip),
               '-af', f'silencedetect=noise={noise}:d={min_len}', '-f', 'null', '-'], True)
    starts = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', out)]
    ends = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', out)]
    return list(zip(starts, ends + [1e9] * (len(starts) - len(ends))))


def duration(clip):
    return float(run([BIN + '/ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                      '-of', 'csv=p=0', clip], True).strip())


def transcribe(clip):
    ws = words(clip)
    lines, cur = [], []
    for w in ws:
        cur.append(w)
        if re.search(r'[.?!]$', w['w']):
            lines.append(cur); cur = []
    if cur:
        lines.append(cur)
    name = os.path.splitext(os.path.basename(clip))[0]
    path = os.path.join(OUT, name + '.txt')
    with open(path, 'w') as f:
        for i, l in enumerate(lines, 1):
            f.write(f"{i:>3}  {l[0]['a']:6.2f}-{l[-1]['b']:6.2f}  {' '.join(w['w'] for w in l)}\n")
    print(open(path).read())
    print('Saved', path)


def keep_segments(clip, keep, gap, pad):
    total = duration(clip)
    ranges = keep or [(0, total)]
    # Start from the kept ranges, then remove silences longer than `gap` and filler words.
    cuts = [(s + pad, e - pad) for s, e in silences(clip, min_len=gap) if e - s > gap]
    cuts += [(w['a'], w['b']) for w in words(clip) if re.sub(r'\W', '', w['w'].lower()) in FILLERS]
    segs = []
    for a, b in ranges:
        pieces = [(a, b)]
        for ca, cb in sorted(cuts):
            nxt = []
            for pa, pb in pieces:
                if cb <= pa or ca >= pb:
                    nxt.append((pa, pb))
                else:
                    if ca > pa: nxt.append((pa, ca))
                    if cb < pb: nxt.append((cb, pb))
            pieces = nxt
        segs += [(round(pa, 3), round(pb, 3)) for pa, pb in pieces if pb - pa > 0.12]
    return segs


def srt_time(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'


def write_srt(clip, segs, path, per_line=4):
    # Map each kept word onto the new timeline, then group into short caption lines.
    offset, mapped = 0.0, []
    for a, b in segs:
        for w in words(clip):
            mid = (w['a'] + w['b']) / 2
            if a <= mid <= b and re.sub(r'\W', '', w['w'].lower()) not in FILLERS:
                mapped.append((max(w['a'], a) - a + offset, min(w['b'], b) - a + offset, w['w']))
        offset += b - a
    json.dump([{'w': w, 'a': round(a, 3), 'b': round(b, 3)} for a, b, w in mapped],
              open(path[:-4] + '.words.json', 'w'))
    with open(path, 'w') as f:
        for i in range(0, len(mapped), per_line):
            g = mapped[i:i + per_line]
            f.write(f"{i // per_line + 1}\n{srt_time(g[0][0])} --> {srt_time(g[-1][1])}\n"
                    f"{' '.join(x[2] for x in g)}\n\n")


def cut(clip, keep, gap, pad):
    segs = keep_segments(clip, keep, gap, pad)
    if not segs:
        sys.exit('Nothing left to keep.')
    sel = '+'.join(f'between(t,{a},{b})' for a, b in segs)
    name = os.path.splitext(os.path.basename(clip))[0]
    out = os.path.join(OUT, name + '_cut.mp4')
    run([BIN + '/ffmpeg', '-v', 'error', '-y', '-i', clip,
         '-vf', f"select='{sel}',setpts=N/FRAME_RATE/TB",
         '-af', f"aselect='{sel}',asetpts=N/SR/TB",
         '-map', '0:v:0', '-map', '0:' + audio_stream(clip),
         '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
         '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', out])
    write_srt(clip, segs, out[:-4] + '.srt')
    before, after = duration(clip), duration(out)
    print(f'{len(segs)} pieces kept, {before:.1f}s -> {after:.1f}s')
    print('Saved', out)


IMAGE_EXT = ('.jpg', '.jpeg', '.png', '.heic', '.webp')
BROLL = os.path.join(ROOT, 'broll')


def probe(path):
    out = run([BIN + '/ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
               'stream=width,height:stream_side_data=rotation:format=duration', '-of', 'json', path], True)
    d = json.loads(out[out.index('{'):])
    s = d['streams'][0]
    w, h = s['width'], s['height']
    rot = next((abs(int(x.get('rotation', 0))) for x in s.get('side_data_list', []) if 'rotation' in x), 0)
    if rot in (90, 270):
        w, h = h, w
    dur = float(d.get('format', {}).get('duration', 0) or 0)
    return w, h, dur


def frames(path, every):
    name = os.path.splitext(os.path.basename(path))[0]
    folder = os.path.join(OUT, 'frames', name)
    os.makedirs(folder, exist_ok=True)
    if path.lower().endswith(IMAGE_EXT):
        run([BIN + '/ffmpeg', '-v', 'error', '-y', '-i', path, '-vf', 'scale=540:-2', os.path.join(folder, '001.jpg')])
    else:
        run([BIN + '/ffmpeg', '-v', 'error', '-y', '-i', path, '-vf', f'fps=1/{every},scale=540:-2',
             '-q:v', '4', os.path.join(folder, '%03d.jpg')])
    shots = sorted(os.listdir(folder))
    for i, f in enumerate(shots):
        print(f'{os.path.join(folder, f)}  (~{i * every:.1f}s)')


def library():
    if not os.path.isdir(BROLL) or not os.listdir(BROLL):
        sys.exit('broll/ is empty. Add clips named by what they show, e.g. 180-rack.mov, ankle-bruise.jpg')
    for f in sorted(os.listdir(BROLL)):
        if f.startswith('.'):
            continue
        path = os.path.join(BROLL, f)
        w, h, dur = probe(path)
        kind = 'photo' if f.lower().endswith(IMAGE_EXT) else f'{dur:.1f}s'
        shape = 'vertical' if h >= w else 'horizontal'
        tags = os.path.splitext(f)[0].replace('_', '-').split('-')
        print(f'{f:<32} {kind:>7}  {shape:<10}  tags: {" ".join(tags)}')


def fill_9x16(label_in, label_out, horizontal):
    """Vertical: crop to fill. Horizontal: blurred copy behind, clip centred (no black bars)."""
    if not horizontal:
        return (f'[{label_in}]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,'
                f'setsar=1[{label_out}]')
    return (f'[{label_in}]split[{label_out}a][{label_out}b];'
            f'[{label_out}a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:3[{label_out}bg];'
            f'[{label_out}b]scale=1080:-2[{label_out}fg];'
            f'[{label_out}bg][{label_out}fg]overlay=(W-w)/2:(H-h)/2,setsar=1[{label_out}]')


def broll(video, plan_path):
    shots = []
    for line in open(plan_path):
        line = line.split('#')[0].strip()
        if not line or line.lower().startswith('start'):
            continue
        p = line.split()
        f = p[2] if os.path.isabs(p[2]) else os.path.join(ROOT, p[2])
        if not os.path.exists(f):
            sys.exit('Missing b-roll file: ' + p[2])
        shots.append((float(p[0]), float(p[1]), f, float(p[3]) if len(p) > 3 else 0.0))
    if not shots:
        sys.exit('The plan has no shots.')
    cmd = [BIN + '/ffmpeg', '-v', 'error', '-y', '-i', video]
    chain, prev = [], '0:v'
    for k, (start, length, f, frm) in enumerate(shots, 1):
        if f.lower().endswith(IMAGE_EXT):
            cmd += ['-loop', '1', '-framerate', '30', '-t', str(length), '-i', f]
        else:
            cmd += ['-ss', str(frm), '-t', str(length), '-i', f]
        w, h, _ = probe(f)
        chain.append(fill_9x16(f'{k}:v', f'f{k}', w > h))
        chain.append(f'[f{k}]fps=30,setpts=PTS-STARTPTS+{start}/TB[s{k}]')
        chain.append(f"[{prev}][s{k}]overlay=eof_action=pass:enable='between(t,{start},{start + length})'[v{k}]")
        prev = f'v{k}'
    out = video[:-4] + '_broll.mp4'
    cmd += ['-filter_complex', ';'.join(chain), '-map', f'[{prev}]', '-map', '0:a?',
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
            '-c:a', 'copy', '-movflags', '+faststart', out]
    run(cmd)
    print(f'{len(shots)} b-roll shots laid over. Saved {out}')


if __name__ == '__main__':
    args = sys.argv[1:]
    if args[:1] == ['library']:
        library(); sys.exit()
    if len(args) < 2 or args[0] not in ('transcribe', 'cut', 'frames', 'broll'):
        sys.exit(__doc__)
    cmd, clip = args[0], os.path.abspath(os.path.expanduser(args[1]))
    if cmd == 'broll':
        if len(args) < 3:
            sys.exit(__doc__)
        broll(clip, os.path.abspath(os.path.expanduser(args[2]))); sys.exit()
    opt = dict(zip(args[2::2], args[3::2]))
    if cmd == 'frames':
        frames(clip, float(opt.get('--every', 1))); sys.exit()
    keep = [tuple(float(x) for x in r.split('-')) for r in opt['--keep'].split(',')] if '--keep' in opt else None
    if cmd == 'transcribe':
        transcribe(clip)
    else:
        cut(clip, keep, float(opt.get('--gap', 0.35)), float(opt.get('--pad', 0.08)))
