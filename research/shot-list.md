# "Number One" — Playgroup (2001, dir. Trevor Jackson) — Shot List & Build Analysis

Source: `reference/video.mp4` — 3:16.65, 1280x720, 29.97fps, h264/AAC.
Sparse frames: `reference/extracted/frames/frame_NNNN.jpg` (t = (N-1) × 2s).
Contact sheets (dense, far more useful): `shots/contacts/`.
Full-res single grabs for detail: `shots/key/`.

## Corrections log

Things this document previously got wrong, recorded so they don't creep back:

1. **The machine is a CUBE** — roughly 1:1:1, square front face, sitting on a mirror
   floor. It was previously modelled as a 2.2:1 tall tower. Wrong.
2. **The big white disc on the front panel is a CD being inserted by hand**, not a
   circular dish that is part of the machine. The CD is a transient prop. There is
   no permanent circular feature on the front face.
3. **The debossed front-panel text reads `PLAYGROUP`** — the artist. It was previously
   written as "TREVOR JACKSON" (the director), which was invented from a blurry crop
   and should never have been presented as observed.
4. **The "abstract cityscape" is an equaliser** — bar-graph columns rising from the
   brushed metal floor, representing the track's spectrum. Not architecture.
5. The Wikipedia summary ("tower PC transforms into humanoid robot") undersells the
   video badly. The PC disassembles, opens, and becomes a *landscape* long before any
   robot appears. Treat it as a 4-act piece.
6. **The CD slot IS the seam.** The machine splits along the slot line — there is only
   ONE line on the front face, not a drawn slot plus a separate seam. The camera pitches
   down and zooms in until the slot fills the frame, then the two halves separate.
   This is why the earlier build's separate "seam groove" was wrong, and why the slot
   must sit at exactly 50% height and run the full width.
7. **The opening is NOT a clamshell hinge.** Detailed in contact sheet C (6.5–11.7s at
   3fps): the halves separate, then the top section tilts and is carried on an
   **articulated chrome two-link arm** at the rear — the mechanism is clearly visible as
   a chrome linkage, standing in an inverted V. By ~10.2s the arm **folds flat** onto the
   top of the box and the machine is closed again. A plain box lid rotating about its
   rear edge is wrong, and the arm is almost certainly the ancestor of the robot's arm
   in Act 3.
8. **Camera staging & timing** (see `tools/compare.py` output). The video is a WIDE shot
   only from 0–2s, then it is a **macro on the front panel from ~2.2s** — a cut, not a
   slow move. It holds that macro through the CD insert and the LED change, tightens to
   the slot itself around 6.0–7.0s, and only then opens. An earlier build held a wide
   3/4 shot until 4s and moved continuously, which is a different edit entirely.

---

## ACT 1 — AWAKENING (0:00–0:45) — "the object"

| t | Content |
|---|---|
| 0:00–2:00 | The cube fades up out of a white void — near-white-on-white, almost invisible at first. It sits on a **mirror floor**: a strong reflection hangs below it. Soft rounded edges, brushed aluminium, cream/white. |
| 2:00–2:20 | **CUT to macro on the front panel.** From here on it is a tight product shot of the panel surface. |
| 2:00–4:00 | A woman's hand (orange/red nail polish) **inserts a CD** into the slot — the disc is the big white semicircle hanging below the slot line. The **power LED is RED**. |
| 4:00 | **LED turns GREEN** — power on. Panel cream, brushed, `POWER` + slot legible. |
| 4:00–6:00 | The macro panel shot, holding. Almost nothing happens. |
| 6:00–7:00 | The camera tightens onto the **slot itself** until the slot's ends leave frame. |
| 7:00–7:50 | **The two halves separate along the slot** — the slot IS the slit. |
| 7:50–9:30 | The top section **tilts and is carried on an articulated chrome two-link arm**, clearly visible as a chrome linkage standing in an inverted V. |
| 9:30–10:20 | The **arm folds flat** onto the top of the box; the machine closes again. |
| 10:20–14:00 | Transition: the floor horizon, then **EQ bars rise out of the brushed metal floor**, forming a bar-graph "skyline". |
| 14:00–19:00 | The bars grow. Camera **flies down between them** — they read as tall reflective slabs either side. At ~19:00 the machine **opens in a V**, two panels hinging apart to reveal a glossy recessed rectangular frame. |
| 19:00–28:00 | **A speaker driver** — a large woofer with concentric black rings and a polished dust cap, face-on, then at an angle. The **EQ bars dance on the speaker's dark curved cone**. |
| 28:00–45:00 | EQ bars keep dancing across the speaker surface. Shallow DOF, blurred foreground elements framing shots. |

**Palette:** high-key. White `#f2f0ea`, cream `#e8e3d8`, warm grey, silver, and exactly
two saturated colours in the whole act: the **red LED** and the **green LED**.
**Style:** macro lens, shallow DOF, heavy specular.

### Front panel spec (also the robot's front in Act 3)

```
shape      : cube, ~1:1:1, square front face. Sits on a true planar mirror floor.
panel      : FULL-FACE panel, not a smaller inset one
POWER      : small engraved caps, left side, upper half
LED        : ~8mm dot, upper-left, ABOVE the POWER label
             red 0xd8382a (off)  →  green 0x2bff5a (on)
slot       : THE seam. Runs the full width at exactly 50% height, hairline.
             The machine separates along it, so there is only ONE line here --
             do not draw a slot AND a separate split.
deboss     : "PLAYGROUP", tracked out, centred, lower half (below the slot)
```

---

## ACT 2 — TRANSFORMATION (0:45–1:15) — "disassembly → assembly"

Contact sheet `shots/contacts/E_robot_58-82s.png` (58–82s at 2fps) resolves the
assembly order and the limb construction. Verified:

**The torso IS the cube.** At 62.0–63.5s a silver cube is unmistakable, sitting above a
mirrored floor with the chrome waist below it. Parts carry over between acts.

**Assembly order:**

| t | Beat |
|---|---|
| 58 | chrome pelvis dome on its cradle |
| 59–60 | **waist ball joint seated in a polished chrome cup** under the cube |
| 62–63 | the cube torso, low, on a mirror floor |
| 64–66 | legs unfold downward; **orange/red cables visible inside the open leg panels** |
| 67–70 | legs extend; flat white feet on the floor; "0:00" decals on the shins |
| 71–75 | body rotates upright; cube face with deboss |
| 76–79 | **arms extend** — articulated white segments, red "0:00" decals, chrome elbows |
| 80–82 | robot standing |

**Limb construction** (more detailed than the earlier "~20 primitives" estimate):

```
limb      : long FLAT WHITE PANELS, not chunky boxes
markings  : red "0:00" decals on shins, forearms, thighs
joints    : chrome BALL joints, plus multi-link articulated clusters at the elbows
cables    : orange/red cables run INSIDE the opened panels
feet      : flat white plates lying on the floor
```

**New detail:** at 81.5s the cube is shown from the other side with a **circular
fan/vent** on its face. The front face has `PLAYGROUP`; the back has a fan.

---

## ACT 2 (original table, superseded by the above)

| t | Frame | Content |
|---|---|---|
| 0:48 | 25 | Torso section suspended on a **polished chrome cylinder/pedestal**. Chrome collar at the bottom of the box, antenna/eject rod angled left. |
| 0:58 | 30 | **Chrome hemispherical pelvis dome** in a dark cradle, beam elements either side. |
| 1:08 | 35 | **ROBOT ASSEMBLED**, single top spotlight in a dark navy void. Torso = the cube housing. Legs are chunky flat boxes with red **"0:00"** decals. Feet are flat plates. |
| 1:18 | 40 | **Macro on shoulder/arm**: chrome ball joints, black cylinder upper arm, articulated linkage. Deep shadow. |

**Style shift:** high-key white → **hard single-source spotlight on black**.

---

## ACT 3 — DANCE (1:15–2:50)

| t | Frame | Content |
|---|---|---|
| 1:28 | 45 | Close 3/4 on the torso. Chrome **shoulder ball joint** + white articulated forearm extending right. Red "0:00" decal on the lower torso. |
| 1:38 | 50 | Wide arena. Robot small on a **dark reflective domed stage**. Background = wall of **glowing red dots** in a grid. |
| 1:48 | 55 | Low angle *up* the legs. **Magenta/pink dot grid** on black. Blue rim light. |
| 1:58 | 60 | Full body, blue-white spotlight, **chalky matte white** limbs (flat light, not metallic). Arms raised, elbows out. |
| 2:08 | 65 | Wide arena: **yellow glowing grid floor tiles**, red star-flare lights around the perimeter. |
| 2:18 | 70 | Low angle on the legs — **red floodlight**. Chunky decals on thighs. Feet = flat plates with visible actuator rods. |
| 2:28 | 75 | **DUCKWALK / Angus Young lean**: body pitched forward almost horizontal, one arm flung straight back, knees deep. Behind: **glowing multicolour floor tiles**. |
| 2:38 | 80 | Extreme wide, tiny robot in a vast dark red space, dramatic diagonal rig pose. |
| 2:48 | 85 | **Aerial tumble**, seen from above/behind, single flare point. |
| 2:58 | 90 | **MOONWALK**: low angle, one foot **glowing brightly**, casting light streaks across a black floor of small point-lights. Warm tungsten. Billie Jean homage. |
| 3:08 | 95 | **Hero close-up**: torso and leg, low angle, warm bloom, yellow light streaks, star flares. |

---

## ACT 4 — POWER DOWN (3:08–3:16)

| t | Frame | Content |
|---|---|---|
| 3:14 | 98 | The machine is a **plain closed box** again, floating in pure black with a soft mirror reflection below. No floor, no context. Cyclical ending. |

---

## Palette

| Act | Key colours |
|---|---|
| 1 | White `#f2f0ea`, silver, warm grey, red LED `#d8382a`, green LED `#2bff5a` |
| 2 | Steel/silver + pure black, one white spotlight |
| 3 | Navy `#0a1220`, crimson `#e01010`, magenta `#ff10a0`, amber `#ffb000`, multicolour tiles, tungsten `#ffd080` |
| 4 | Black `#000000` + a single silver box |

## Materials

- **Brushed/satin aluminium** — the hero surface. `metalness ≈ 0.45`, roughness ≈ 0.5.
  Note: `anisotropy` was tried and removed — it is UV-scale dependent, so parts sharing
  a 0–1 UV at different sizes render at visibly different roughness.
- **Polished chrome** — all joints, pelvis dome, pedestal. Low roughness, strong env.
- **Matte white** — limbs under flat light (Act 3 first half), chalky.
- **Black** — arm cylinders, seams, void backgrounds.
- **Red decals** — "0:00" on thighs/torso.

## Robot anatomy (all primitives — no sculpting needed)

```
torso      : the cube housing, with seams + slot + red decal
waist      : short polished chrome cylinder strut
pelvis     : chrome hemisphere/dome, prominent
shoulders  : small chrome ball joints, upper sides of the torso
upper arm  : rectangular block w/ red "0:00" decal + black cylinder core
elbow      : cluster of chrome cylinders/balls (heavy, visible)
forearm    : slimmer white block
hand       : small flat chrome claw/plate
thigh      : LARGE flat white box, red "DG" decal
knee       : chrome cylinder joint
shin       : slimmer white box
foot       : flat chrome plate/ski + visible actuator rods (very distinctive)
```

≈20 primitives total. Fully buildable in Three.js with no imported assets.

## Dance vocabulary to hand-key

1. Arm-extended poses, elbows out, robot-tronic (throughout)
2. Hip sway + knee bend groove (~2:20)
3. **Moonwalk** with self-illuminating foot + floor light streaks (~2:58)
4. **Duckwalk** forward lean (~2:28)
5. Aerial tumble / spin (~2:48)
6. Hip-led strut, weight shift (~2:38)

## Camera language

Hyper-cut (most shots 1–2s). Mix of: extreme macro on joints · low worm's-eye ·
top-down · wide arena establishing · dutch tilt · shallow DOF throughout.
Every shot names a light source visible in frame (spot flare, star flare, dot wall).

---

## Technical notes for the build

- **No build step.** Single `index.html` + importmap → Three.js from CDN. Add Vite only
  if it ever gets painful.
- Robot = a `THREE.Group` hierarchy matching the anatomy table. Every joint is a Group
  with its pivot at the joint centre; child meshes offset from it. Getting pivot
  placement right once is what makes the hand-keyed choreography tractable.
- Arena = reflective floor, dot-wall backdrop as an instanced/emissive grid,
  spotlights with visibly volumetric cones.
- Post: bloom/glare does most of the aesthetic work. Real depth-of-field still needed
  (a `BokehPass`) — bloom + fog only approximates the macro shots.

## Not yet done

- BPM/downbeat extraction from `reference/audio/audio.wav`
- Act 1's animated beats: CD insert, lid lifting, EQ bars rising
- Exact "0:00" / "DG" decal artwork on the robot
- The speaker driver model (Act 1, 19s–28s) — this is a significant asset
- Removed: `reference/extracted/thumbnails/` (scene threshold 0.15 → 5806 junk files)
