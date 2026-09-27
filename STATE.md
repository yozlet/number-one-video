# State of the work

Where things stand right now, and what to do next. **Read `AGENTS.md` first** — that
is working discipline; this is position. `README.md` has the project detail.

Last updated: end of session 1.

---

## The goal

Recreate Trevor Jackson's video for Playgroup "Number One" (2001) as a live-rendered
WebGL animation in Three.js. Single `index.html`, no build step, no runtime deps.

## Where it stands

| Piece | State |
|---|---|
| **Act 1** — cube, CD insert, slot zoom, split, lift on arm, close | **built and animated** |
| **Robot rig** | **blockout built** — proportions, pivots, pose harness |
| Act 2 — disassembly / assembly | not started |
| Act 3 — the dance | not started |
| Act 4 — back to a closed box | not started |
| EQ bars rising from the floor | not started |
| Speaker-driver sequence (19–28s) | not started, no model |

### Act 1 detail

Runs 0 → 11.6s. Timeline and the two hard cuts are in `README.md`; the verified
reference timings are in `research/shot-list.md`.

**Resolved by direct comparison against the reference:** camera staging, the exposure
ramp, the CD insertion, the slot close-up, and the lift framing (all within ~5% on the
`tools/diff.py` coverage measure).

**Still open in Act 1 — the mechanism, t=8.5–9.9.** The reference's closing shots are
full-frame close-ups where a chrome wedge ends up standing proud of a *closed* box. Ours
hides the arm once closed, because a folded linkage interpenetrates the solid halves.
The reference's actual linkage is still not legible at the resolutions grabbed so far —
**grab a tighter crop of 9.5–10.5s before rebuilding it.** What is known: it is NOT a
clamshell; the top section is carried on an articulated chrome two-link arm.

### Robot rig detail

`?rig=1` shows the robot and hides Act 1. Proportions measured from
`shots/rig/robot_120.5.png` and verified with a landmark overlay
(`shots/rig/landmarks.png`) — shoulders, waist, hips, knees and ankles land close to the
reference's fractions.

Known deviations, all **surface, not pivot**, so all safe to defer:
head box slightly oversized · shin panels slightly too wide · waist section simplified
(the reference has a longer articulated chrome column between torso and knees).

Pose harness works on every joint:
```sh
?rig=1&pose=shoulderL.z=58,shoulderR.z=-58,elbowL.x=-28,hipL.x=-22,kneeL.x=42
?rig=1&angle=40
```

## Next actions

1. **Pose-matching pass on the rig** (the gate before any choreography). Pick a real
   reference pose — duckwalk at t=75 or arms-raised at t=118 — pose the rig to match,
   and diff. If a *static* pose matches, the pivots are proven and choreography is safe
   to key. **This is the highest-value next step**: pivots are what break animation, and
   finding out now costs a pose instead of a dance.
2. Finish Act 1's mechanism (see above — needs a tighter frame grab first).
3. Act 2 assembly: pelvis dome → waist ball in its cup → cube torso → legs unfold →
   arms extend. Order and construction are in `research/shot-list.md`.
4. Then the EQ bars and the speaker driver.

## Open decisions

- **Whether to add SAM for reference segmentation.** Recommendation on record: not yet.
  Classical CV is adequate where it matters (bright robot, dark arena); add it when a
  real Act 3 frame defeats the current tool. See `AGENTS.md` → "When to reach for a
  segmentation model".
- Absolute scale of the robot is still arbitrary. `H = 2.2` currently, chosen so the
  torso lands at 0.28 wide to match the cube. The torso's exact relationship to the
  cube is **unresolved** — measured torso is 0.28 × 0.47, not cubic.

## How to verify the current state

```sh
python3 -m http.server 8000 && open http://localhost:8000   # Act 1
open 'http://localhost:8000/?rig=1'                         # robot blockout

python3 tools/diff.py 1.0 2.8 6.9 7.3 8.5    # bake + measure, ~8s
python3 tools/diff.py 1.0 2.8 --selftest     # must print INSTRUMENT OK
python3 tools/session-log.py                 # archive this session into log/
```

## Standing constraints

- No build step, no runtime dependencies. Dev-only tooling deps are acceptable.
- `AGENTS.md` is a living document — update it *as you work*, not at the end.
- Derive values from the scene rather than detecting them from pixels.
- Fidelity to the video beats mechanical plausibility.
