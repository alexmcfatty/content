# Content Bank: rules for Claude

Personal short-form video setup (TikTok + Reels): the idea bank app, script rules, and a local editing pipeline.
This repo is public. Never commit video, audio, b-roll, edits, keys or personal details.
Personal context (goals, current numbers, dates) lives in `CLAUDE.local.md`, which is not committed:

@CLAUDE.local.md

## Files
- `index.html`, `sw.js`, `manifest.json`, `config.js`: the idea bank PWA (Supabase, live on GitHub Pages).
- `rules.txt`: the voice and script rules. Every script, hook and caption follows it.
- `editing-rules.md`: the editing rules. Every cut follows it. When the user sends an edit back, add a rule there.
- `tools/autocut.py`: the editing pipeline (below).
- `raw/` (clips to edit), `broll/` (the b-roll library) and `edits/` (outputs) are git-ignored.

## Writing (hooks, scripts, captions)
- Follow `rules.txt` exactly: dry, understated, self-deprecating Aussie; no preaching or advice to the viewer; flat endings; banned words; no gambling/betting/side-business specifics, only "a business I'm building on the side"; no money figures; no invented numbers (use [brackets]).
- Structure: the hook lands in the first second, and each open loop closes within 3–5 seconds while the next one opens. Only the last loop stays open.
- Engagement through the caption (an easy question, "send this to the mate who...") never through spoken "comment/share" asks.
- Offer options with a pick and a reason. When feedback is "boring", bring sharper ideas, not more explanation.

## Editing pipeline
Tools: ffmpeg and whisper-cli at /opt/homebrew/bin, model at `~/.whisper-models/ggml-base.en.bin`.
Claude cannot watch video. Work from transcripts (words + timestamps) and still frames (`frames`), and say so.

    python3 tools/autocut.py transcribe raw/CLIP.MOV          # numbered lines + timestamps -> pick takes
    python3 tools/autocut.py cut raw/CLIP.MOV --keep 0-5.9,7.6-17   # cut pauses/ums -> edits/CLIP_cut.mp4 + .srt + _cut.words.json
    python3 tools/autocut.py frames FILE [--every 1]          # stills to look at (framing, b-roll contents, cover frame)
    python3 tools/autocut.py library                          # list the b-roll library with tags and lengths
    python3 tools/autocut.py broll edits/CLIP_cut.mp4 PLAN.txt     # lay b-roll over the cut -> edits/CLIP_cut_broll.mp4

Typical job ("cut these clips"):
1. `transcribe` each clip. Match lines to the script, choose the best take of each line (fluffs, repeats, wrong numbers out), and tell the user which takes were picked and why.
2. `cut` with `--keep` ranges for the chosen takes.
3. Read `edits/CLIP_cut.words.json`, then write a b-roll plan: where the script mentions something with a matching library tag, cover those words with that clip. Talking-head moments that need a face (hook, turns of the story, the ending) stay uncovered.
4. Run `broll`, pull a few `frames` of the result to check it, then send the video with SendUserFile.
5. The user finishes music, sound effects and gags in CapCut.

B-roll plan format (`edits/PLAN.txt`), one line per shot, times in seconds on the cut's timeline:

    start  length  file                  [from]
    2.10   1.5     broll/180-rack.mov    0.4
    6.00   2.0     broll/ankle-bruise.jpg

## B-roll library
Files in `broll/` are named by what they show, with words split by dashes: `180-rack.mov`, `ankle-bruise.jpg`,
`run-away-road.mov`, `hyrox-sled.mov`. Those words are the tags. If a file has a vague name (IMG_1234), look at its `frames`,
then suggest a name and rename it only with the user's OK.

## Git
Ask before every commit and push. Show what changed first.
