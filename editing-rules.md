# Editing rules

Claude follows these when cutting a video. Every edit sent back adds a rule.
The script rules (voice, banned words, hard rules) are in `rules.txt`; these are about the edit.

## Pace
1. The hook is said within the first second. No intro, no "hey guys", no breath before it.
2. The hook's question is answered within ~5 seconds. Never stack two open loops before closing one.
3. Cut every pause longer than ~0.35s and every "um"/"uh". Keep a pause only when it's the point (e.g. after "For 42.").
4. Fast sections change shot every 1–2 seconds. Slow sections (the turn of the story) can hold.
5. 30–45s for normal videos; 60–90s only for a storytime that earns it.

## Look
6. Captions: clean, plain, centred, one short line (about 4 words). No bouncing, no word-by-word pop, no emojis, no colour-per-word.
7. No zoom or punch-in on every cut. One slow push-in at most, saved for the low point.
8. Text stays in the top two-thirds and off the right edge (the app buttons cover the bottom and right).
9. On-screen numbers for anything that matters: weights, times, paces, dates.
10. Old horizontal clips: crop to 9:16 or blurred background fill, never black bars.

## Sound
11. Music low under talking, and cut dead for a lift or a big moment. Real sound (bar clank, breathing) beats sound effects.
12. Use the phone's stereo track, not the spatial audio track (sounds echoey outside Photos).

## Honesty
13. Lifts and runs are one unbroken shot. Never trim a rep to make it look better, and post misses the same as makes.
14. No reaction faces, fake laughs or added "shocked" moments. The real reaction or nothing.
15. Every number on screen is real. If unsure, leave it off.

## Talking-head opinion videos (from @richiesjournal, studied 2026-11-27)
For sit-down opinion videos (e.g. "Passion for men"), where it's mostly his face talking:
16. Keep his face full-screen the whole time. Illustrate with a picture-in-picture box in the top third instead of cutting away. The face carries trust; the box carries the point.
17. Swap the box every 2–4 seconds, matched to the line being said. It can be literal (a screenshot of his watch, the 180 lift, an old photo) or a plain illustrative image (e.g. a tangled maze for "confused"). One box at a time, never stacked over his face.
18. Show receipts in the first 5 seconds when he claims something: the screenshot, the clip or the note, on screen as he says it. Shown, never bragged about (no follower or view counts in his own videos).
19. Talking-head shots: a plain background, natural hand movement, and the phone at eye level. No B-roll needed to keep it moving when the boxes are changing.
20. The PiP boxes are done in CapCut. `autocut.py broll` only does full-screen b-roll, so for these videos Claude writes a box plan (time, what's in the box) instead of a b-roll plan.
