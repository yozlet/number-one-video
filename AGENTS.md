# Working notes for agents

## Keep this file current — update it AS YOU WORK

This is a living document, not a report. Update it during the work, not at the end and
not when asked. Its whole value is being current; a note added three turns later is a
note that was missing for three turns.

**Also run `tools/session-log.py` — ideally EARLY in a session.** It converts pi's
session JSONL into a readable Markdown transcript in `log/sessions/`: the raw file is
~24MB of base64 frames, the transcript is ~850KB of greppable text. It is idempotent,
so re-running costs nothing.

Run it early rather than at the end, because pi writes the JSONL incrementally — a
session started now can archive everything up to this point, whereas "at the end" is
exactly the instruction that gets forgotten when the end arrives mid-task. A fresh
session can then read the reasoning behind decisions that the summary docs only record
the outcome of.

Add an entry when:

- **A bug cost more than a few minutes.** Record the rule *and* the evidence. A rule
  with a cost attached is credible; a bare rule reads as opinion and gets ignored.
- **A tool gave a plausible but WRONG answer** — especially if it failed *silently*.
  Those are the expensive ones, because nothing prompts you to distrust them.
- **An assumption was falsified.** "I assumed X was needed" is worth writing down even
  when the fix is obvious.
- **You caught yourself doing something the hard way** when the answer was already
  known. That is usually a missing rule, not a one-off slip.

Keep entries short and evidence-first: the rule, one concrete example, what to do
instead. **Delete entries that stop being true** — a stale rule is worse than no rule,
because it is followed. Do not duplicate what is already here; extend or correct it.

## Fidelity beats plausibility

**The reference is CGI from 2001 made by animators taking liberties. Match the video,
not physics.** Do not spend effort making a mechanism mechanically valid, or refuse a
pose because a real linkage could not reach it. If the video shows a chrome wedge
carrying a lid in a way that would need three joints, build the chrome wedge that
looks right. Being "correct" and looking different is a worse outcome than being
slightly impossible and matching the frame.

This has already cost time: a two-link scissor was constrained by what it could
physically reach, which fought directly against making it look like the reference.

## Derive, don't detect

**If a value is derivable from something you already know, derive it. Do not measure it
from pixels.** Detection is for when the value is genuinely not present in anything you
control.

Three times on this project, detection was reached for and was the wrong tool:

| Wanted | Detected (wrong) | Derived instead |
|---|---|---|
| our own render's silhouette | thresholded it with computer vision | a `scene.overrideMaterial` white-on-black mask pass — exact, free, and it drops the floor reflection for free too |
| the robot's bbox, to align a landmark overlay | luminance threshold (missed the shadowed legs); then background-difference (caught the whole crop AND clipped our own feet) | the extents are known: the reference robot is y 10–690, ours is y 20–700 from the camera maths |
| which scene objects are the subject | — | a `maskExclude` list on the scene graph |

Detection's real failure mode is not inaccuracy. It is that a threshold always returns
*something* plausible-looking, so a wrong answer arrives wearing the same clothes as a
right one. Derivation cannot fail that way: it is either exact, or it throws.

Ask first: *do I already control this?* For our own render the answer is always yes —
we authored the scene, the camera and the timeline.

## Camera framing is measurable — do not eyeball it

Eyeballing camera distance drifts and takes many render cycles to converge. Use
`tools/framing.py`: it high-passes both frames, isolates the object, and reports its
bounding box as a fraction of the frame for the reference vs our render, plus the
vertical centre.

```sh
tools/compare.py 7.3 7.9 8.5      # renders + builds the side-by-side
tools/framing.py 7.3 7.9 8.5      # -> coverage %, zoom ratio, centre offset
```

`zoom` below 1 means we are too small: DIVIDE the camera distance by it. Two or three
iterations converges to within 5%.

**Watch the crop.** If the object runs off the frame edge its measured height is
clipped, so the numbers lie. Fix the crop before trusting the ratio.

**Coverage matching is not angle matching.** Two cameras can put the same number of
pixels on the object at very different elevations. Check the side-by-side too: the
reference lift shots are only ~12deg above and ~28deg round, so the front and side
faces dominate and the top face stays a thin sliver.

## Measuring the render, not eyeballing it

Three tools, all cheap. The loop is:

```sh
tools/diff.py 1.0 2.8 6.9 7.3 8.5     # bake + measure, ~8s for 8 frames
tools/diff.py 7.3 7.9 --reuse          # re-measure, no re-bake
tools/diff.py 1.0 2.8 --selftest       # verify the instrument
```

**`--selftest` is not optional before trusting a reading.** It compares each frame
against itself; every score must be 1.00. An instrument that cannot score a perfect
match on identical input will hand you confident nonsense about everything else, and
two earlier versions of this one did exactly that.

### Bake first

`?bakeTs=1.0,2.8,6.9&cols=4&w=384&h=216` renders a LIST of timeline positions into
one canvas, so a sweep costs one browser launch instead of one per frame. That launch
cost (8–20s each) was the real bottleneck in this loop, more than tokens. Needs
`preserveDrawingBuffer: true` or the readback is blank.

### Our own silhouette needs no computer vision at all

Bake mode emits TWO bands: beauty on top, and an exact **silhouette pass** below
(`scene.overrideMaterial` flat white, black background, no composer, mirror and
shadow-catcher excluded). We authored the scene — we already know what is visible —
so inferring our own silhouette from pixels was self-inflicted difficulty. It also
excludes the floor reflection for free, which no threshold can do.

Only the REFERENCE now has to be segmented. That halves the problem, and gives us
something to disambiguate against: our coverage is exact, so `segment_reference()`
picks whichever reference segmentation lands closest to it.

### Segmenting the reference: there is no single right answer

Both of these were tried and each is right for a different part of the video:

| method | correct for | fails on |
|---|---|---|
| **otsu** — luminance threshold, smaller class = subject | a subject on a contrasting field: the robot in the dark arena, which is all of Act 3 | Act 1, where the machine is white on white and Otsu just splits noise |
| **edge** — high-pass, closed, hole-filled | Act 1's studio shots, where the structure is entirely in edges | frames where it silently INVERTS and returns the dark background instead of the lit subject |

Do not build this on edge detection plus topological fill alone. Hole-filling an edge
map has no reliable notion of which side is the subject, and it fails *silently*.

**Known weakness:** on dance frames the otsu mask captures the robot *and* the
spotlight pool on the floor. Fine for ref-vs-render comparison (both will have a
pool), useless if you need a robot-only silhouette for limb tracking. A learned
segmenter is the real fix for that — see below.

### When to reach for a segmentation model

Classical CV is adequate where the subject contrasts with its field, which is most of
Act 3. Add SAM (or SAM 2) only when a real frame defeats it:

- **Act 1's white-on-white** — no threshold can work; a learned objectness prior could
- **robot vs spotlight pool** — needs semantic knowledge, not a threshold
- **SAM 2's video propagation** — keeps ONE object identity across frames, so motion
  curves do not flicker between independently-segmented frames. This is the real
  argument for it, and it matters for choreography extraction.
- **limb-level prompting** — point prompts on joints, beyond any global threshold

Cost: PyTorch (~2.5GB) plus a checkpoint. It is a DEV-ONLY dependency — the thing we
ship stays a single HTML file with no build step. Do not add it speculatively: Act 1 is
judged by eye against contact sheets anyway, and the tooling is already deep enough to
be a rabbit hole of its own.

### What the numbers mean

```
iou    raw mask overlap in frame space      (position + scale + shape together)
shape  overlap after normalising position and scale   -> isolated shape error
size   object size ratio, ref/render        (<1 means we are too big)
dx dy  bbox centre offset, as % of frame
mask%  coverage for each, WITH the mode used — if these disagree wildly,
       the frame is not measurable and the other columns are noise
```

A bad `shape` with good `size`/`dx`/`dy` means geometry is wrong. A good `shape` with
bad `dx` means only camera placement is wrong.

## Reference analysis

**When in doubt about a movement or shape, grab more frames between the two that are
confusing you.** Do not reason harder from the frames you already have, and do not
guess. Extract denser frames around the ambiguity and look.

This is not a fallback for when analysis fails — it is the *first* move. Every wrong
turn on this project so far was resolved this way within one or two looks:

| Mistake | What fixed it |
|---|---|
| Modelled the machine as a 2.2:1 tower | One 4×6 contact sheet of 0–12s: it's a cube |
| Invented a "circular dish" on the front panel | Denser frames: it's a CD being inserted by hand |
| Read the deboss as "TREVOR JACKSON" | Full-res grab at t=3.0s: it reads `PLAYGROUP` |
| Called the EQ an "abstract cityscape" | Contact sheet of 12–30s: it's a spectrum analyser |
| Thought the panel pulled back before splitting | The user described it: the slot IS the seam |

Two tools, both cheap:

```sh
# Contact sheet: N frames in ONE image. Best first look at any time range.
ffmpeg -y -ss 0 -t 12 -i reference/video.mp4 \
  -vf "fps=2,scale=320:-1,tile=4x6" -frames:v 1 shots/contacts/out.png

# Full-res single grab, for READING text or measuring a detail.
ffmpeg -y -ss 3.0 -i reference/video.mp4 -frames:v 1 shots/key/t3.0.png

# Reference vs our render, same timestamps, side by side (video on top).
# Do this BEFORE claiming a beat is right — differences in proportion, staging
# and mechanism only become obvious when the two frames are adjacent.
tools/compare.py 1.0 2.8 6.6 9.0 --out shots/cmp/compare.png
```

Read the video with contact sheets, not the sparse `reference/extracted/frames/`
(those are 2s apart and miss most beats).

**Flag uncertainty explicitly.** Say "I can't read this at this resolution" rather than
writing a guess into code with a soft caveat in a comment. The invented "TREVOR JACKSON"
deboss was in the build for several rounds because it was labelled "unverified" instead
of "unreadable".

## Hierarchies: a local offset is a DIFFERENCE

In a joint hierarchy, every child offset is `absolute(child) − absolute(parent)`. Using
an absolute height fraction as a parent-relative offset silently places the part far too
high: it put a 2.2m robot's head at 3.15m, and the result just looked *a bit off* rather
than obviously broken. With ~13 joints and more coming, this will recur.

Same class of bug, same shape: **`Number('')` is `0`, not `NaN`**, so an absent
`?bakeTs=` produced `[0]` and put the page into bake mode instead of playback, showing a
384×216 tile in the corner of the window. When adding a query parameter, filter empty
fields *before* coercing.

Both failed quietly. Prefer an assertion or a visible wrongness over silence.

## Rendering

Use `tools/shoot.sh` — it wraps `chrome-headless-shell`, not the "Google Chrome for
Testing" app bundle. The full bundle can wedge under machine load and never exit.

If a render hangs, suspect machine load first. The same command has taken 8s and 90s.

**When measuring proportions off a render, find the floor line first.** The mirror
reflection doubles the apparent height of the object; the cube read as 1.5:1 tall until
the floor line was identified.

## Shots are gitignored — record the recipe, not the pixels

The repo is public, so no image derived from the source video is committed: they
are copyrighted stills, and they are regenerable anyway. What is NOT regenerable
is the recipe. `tools/prov.py` appends a JSON line to `shots/provenance.jsonl` as
each tool writes an image; `tools/manifest.py` renders that into
`shots/MANIFEST.md`.

Why at generation time rather than later: **the commit SHA cannot be recovered
afterwards.** `tools/manifest.py` can infer a rebuild command from a filename and
does for the 163 pre-git images, but it labels them `inferred (pre-git)` in the
manifest, because a filename records only what the caller happened to type. Two
grades, and the manifest says which is which, is the whole point.

If you add a tool that writes an image, call `prov.record(out, tool=..., argv=...,
params=..., note=...)` (or `tools/prov.py record ...` from shell). Regenerate the
manifest before committing; `tools/manifest.py --check` exits non-zero if it is
stale. Beware `parse_known_args`-style sloppiness here: `--param` after
`--argv` in the CLI is rejected explicitly, because silently dropping that data
would produce a confident, wrong rebuild command.

## Commits

Don't commit `reference/video.mp4` or `reference/audio/audio.wav` (75MB of copyrighted
material). Derivatives — frames, contact sheets, renders — are fine for local work, but
they're gitignored here and described by `shots/MANIFEST.md` instead.
