# Number One — Playgroup (2001) recreation

Live-rendered recreation of Trevor Jackson's video for Playgroup's "Number One",
built layer by layer in Three.js.

## Run it

Any static server — ES modules and the importmap need `http`, not `file://`:

```sh
python3 -m http.server 8000
open http://localhost:8000
```

No build step, no `npm install`. Three.js 0.186.1 loads from unpkg via importmap.

Renders are taken headlessly with `tools/shoot.sh <path> <out.png>` — see the
screenshot gotcha in the build notes below before changing how that's invoked.

## Status

| Act | Content | State |
|---|---|---|
| **1** | Awakening — cube, CD insert, slot zoom, lift on arm, close | **animated** (`index.html`) |
| 2 | Transformation — disassembly → assembly | not started |
| 3 | Dance — the arena, dot walls, moonwalk, duckwalk | not started |
| 4 | Power down — back to a closed box | not started |

**Controls:** space play/pause · ← → step (±0.05s, shift ±0.5s) · **O** toggle free orbit ·
scrub bar along the bottom.

`?t=6.2` jumps straight to a beat and holds it. `?ui=0` hides the HUD for clean
comparison renders. `?orbit=1` starts in free-orbit mode.

### How close is it?

`tools/compare.py T1 T2 ...` renders the reference frame and our frame at the same
timestamps side by side. As of the last pass, these beats line up well:

| t | Beat |
|---|---|
| 1.0 | cube blown out in a wide shot |
| 2.8 | macro: `POWER` + red LED, slot bar, CD as a white half-disc |
| 6.6 | tight on the slot, bright lower lip |
| 7.9 | halves separated, both boxes in frame |
| 8.5 | top section lifted, mechanism between the halves |
| 9.9 | machine closed again |

## Act 1 timeline

| t | Beat |
|---|---|
| 0.0–2.2 | wide shot, blown out, LED red |
| 2.2 | **hard cut** to macro on the panel |
| 2.2–3.3 | the CD slides into the slot |
| 4.0 | LED goes green |
| 5.8–6.4 | camera tightens onto the slot itself |
| 6.5–6.9 | **the halves part IN CLOSE-UP** — the gap opens on screen while the camera is still tight on the slot |
| 6.9–7.3 | camera eases back to a medium shot |
| 7.3–7.9 | medium shot of the two boxes |
| 7.9–9.2 | camera **pushes back in**; the top section tilts to ~40° and the mechanism shows |
| 9.2–9.9 | full-frame close-up; the machine folds closed |

Three things here are easy to get wrong and were all got wrong at first:

- **The split starts at 6.5, not at the cut.** The camera stays tight and the gap
  opens *in close-up*; it eases back only afterwards. Cutting to wide at the moment
  of the split throws away the whole beat.
- **The pull-back eases, it does not cut.** Only the two moments above are hard cuts.
- **The camera does not settle after the split.** Its coverage runs 60% → 60% → 69% →
  100% → 100%: it keeps pushing in to a full-frame shot of the mechanism. Pushing in
  is the shot, not decoration.

## Files

```
index.html                                  the whole scene, one file
research/number-one-video-recreation-research.md   prior art + engine choice
research/shot-list.md                       timecoded breakdown + corrections log
reference/video.mp4                         source, 3:16, 1280x720
reference/audio/audio.wav                   44.1kHz stereo PCM
reference/extracted/frames/                 98 frames @ 2s (sparse, gitignored)
tools/shoot.sh                              headless screenshot (chrome-headless-shell)
tools/compare.py                            reference vs render, side by side, labelled
tools/framing.py                            coverage / zoom ratio / centre offset
tools/diff.py                               bake + measure silhouettes; has --selftest
tools/prov.py                               record how each image was made (at render time)
tools/manifest.py                           render shots/MANIFEST.md from the ledger
shots/contacts/                             dense contact sheets — use these, not frames/
shots/key/                                  full-res single grabs for reading detail
shots/cmp/                                  comparison sheets + the raw pairs
shots/diff/                                 baked sheets and extracted masks
shots/rig/                                  reference poses, blockout renders, landmark overlays
shots/act1.png                              latest render
shots/MANIFEST.md                           every shot, its rebuild command, its commit
```

**The images are not in the repo; the recipe is.** Every frame, contact sheet and
render under `shots/` and `reference/extracted/` is gitignored: they are derived
from a copyrighted music video and are regenerable. `tools/prov.py` appends a
provenance line as our tools write each image (exact argv, timeline positions,
tile size, commit and dirty state), and `tools/manifest.py` renders that into
`shots/MANIFEST.md` — rebuild a shot by checking out the recorded commit and
running the recorded command, then compare its sha256. Shots made before the
ledger existed are listed as *inferred*; the manifest is explicit about which
entries are a record and which are a guess.

## Robot blockout rig

`?rig=1` shows the robot and hides Act 1. Proportions are measured off
`shots/rig/robot_120.5.png` (a full-body frame) and stored as fractions of total
height so absolute scale can change freely:

```
ankle 0.029 · knee 0.272 · hip 0.426 · waist 0.559 · torso bottom 0.596
shoulder 0.787 · torso top 0.875 · head top 1.000
arm: shoulder 0.787 -> elbow 0.625 -> hand 0.456
widths: shoulder span 0.272 · torso 0.128 · head 0.213 · shin 0.162
```

The reference robot is LANKY — shoulder span is only 0.27 of its height, the shins
are the widest limb element, and the arms hang to mid-thigh.

**Pose harness** — set a static pose and diff it against a reference frame:

```sh
?rig=1&pose=shoulderL.z=58,shoulderR.z=-58,elbowL.x=-28,hipL.x=-22,kneeL.x=42
?rig=1&angle=40                      # orbit the camera round the figure
```

This exists because **pivots are what break animation**, and finding out while the
pose is static is far cheaper than finding out after a dance is keyed. Surface detail
does not move a joint centre, so panels, cables and chrome can all come later.
`shots/rig/landmarks.png` overlays the measured landmark fractions on both the
reference and the blockout to check alignment.

## Build notes — things that are non-obvious

**Light intensities are ~3x what you'd guess.** three.js r155+ is physically
correct and the Lambert BRDF carries a 1/π. A directional light needs ~5, not ~1.5,
to light a bright surface. This cost several render cycles to find.

**Use `NeutralToneMapping`, not `ACESFilmicToneMapping`.** ACES is a film look that
crushes mid-tones and desaturates; it rendered this studio setup as muddy grey.
Neutral (Khronos PBR Neutral) is designed for bright, flat, colour-accurate work.

**Don't use `anisotropy` on a material shared by boxes of different sizes.** It is
UV-scale dependent, so two stacked boxes sharing a 0–1 UV rendered at visibly
different roughness and the seam read as two separate objects.

**A metal box's front face reflects the *horizon* band of its environment.** With
`RoomEnvironment` (a uniform white box) a `metalness: 1` body renders flat white with
no gradient at all. The scene uses a hand-built vertical gradient env instead —
bright at the top, falling off below — and keeps `metalness` at 0.45 so the key
light can still shape the form.

**Framing:** the video's Act 1 is near-white-on-white (frame 1 is almost pure blown
out). The scene is deliberately exposed to the much more readable frames 2–3 so the
model can actually be reviewed. `renderer.toneMappingExposure` at ~1.6 reproduces
the frame-1 look.

**Reflections are load-bearing.** The cube sits on a true planar mirror in every
Act 1 shot and again in the closing frame. A glossy floor material won't give you
this — it reflects the environment, not the object. Use `Reflector` plus a
`ShadowMaterial` plane just above it to keep the contact shadow.

**A thin liner slab becomes a large face the moment its parent rotates.** The dark
box filling the CD slot was fine while closed — then the lid hinged open and turned
its entire 275mm top surface to face the camera as a black rectangle. `BoxGeometry`
takes one material per face, so the fix was to keep the *edges* dark (what you see
through the slot) and give the broad faces the body material (what you see when it
opens). Alternatively: hang it off whatever rotates away.

**Parenting to an already-offset mesh silently adds that offset again.** `panelLower`
was added to a base mesh positioned at `baseH/2`, so its "local" y picked up an extra
70mm and `PLAYGROUP` sat crammed against the slot. Both halves are now origin-anchored
Groups, so a child's local position equals its world position.

**The lid pivot must be its own centre, not the rear edge.** With the natural "hinge"
at the rear, rotating merely swings the lid away from the lower box; the reference
holds the lid above it and tilts it in place.

**Screenshot with `chrome-headless-shell`, not "Google Chrome for Testing".**
The full app bundle spawns a crowd of helper processes, makes a macOS Keychain lookup
for its password store, and attempts GCM registration. On a loaded machine that wedges
it so it never exits — even `--dump-dom about:blank` hangs and writes nothing. The
headless shell is the purpose-built binary (no keychain, no profile prompts) and exits
cleanly. If a render hangs, suspect machine load before suspecting the page: the same
command has taken both 8s and 90s on this machine.

**Read the video with contact sheets, not sparse frames.** 2s-interval frames miss
most of Act 1's beats entirely. `ffmpeg -ss 0 -t 12 -i reference/video.mp4 -vf
"fps=2,scale=320:-1,tile=4x6" -frames:v 1 out.png` puts 24 frames in one image —
cheap to review and it made the CD insertion and the lid-lift obvious immediately.

**When measuring proportions off a render, the mirror reflection will fool you.**
The cube read as ~1.5:1 tall until the floor line was identified; the "extra height"
was its own reflection. Measure against the floor line, not the object's bbox.

## Known gaps

- **The arm's end state is unresolved.** The reference's closing shots (9.2–9.9) are
  full-frame close-ups of the mechanism, and at 9.9 the chrome wedge is still standing
  proud of a *closed* box. Ours hides the arm once closed, because a folded linkage
  interpenetrates the solid halves. The reference's exact linkage is still not clear —
  grab a tighter crop of 9.5–10.5s before rebuilding it.
- **The arm is a plain two-link scissor.** It reads as a mechanism and cannot detach,
  but it was sized around what it could physically reach, which fought against matching
  the reference. Per `AGENTS.md`, fidelity beats plausibility here — rebuild it to look
  right and ignore the geometry's opinions.
- **The slot's facing edges are rounded**, so the slot is thicker than the reference
  at extreme zoom. `RoundedBoxGeometry` rounds every edge including the two facing the
  split. Proper fix is flat facing edges, which belongs with the interior.
- **No interior.** When the machine opens you see the two halves' mating faces and
  nothing else; the reference shows internal panels.
- EQ bars rising from the floor, and the speaker-driver sequence (19s–28s) — a
  significant asset, not started
- No depth-of-field pass (bloom + fog only approximates it)
- Brushed grain isn't visible; needs a roughness map
- Panel edge (the faint outline where the full-face panel meets the cube) is not modelled
