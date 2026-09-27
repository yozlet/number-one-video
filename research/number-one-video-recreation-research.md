# Research: Recreating Playgroup "Number One" Music Video as Live Web Animation

## Source Video Analysis

**Song:** "Number One" by Playgroup (Trevor Jackson)  
**Released:** 2001 (UK), 2002 (US)  
**Original medium:** Pre-rendered computer animation (CGI)

### Visual Description (from Wikipedia and MusicBrainz data)
- A tower PC transforms into a humanoid dancing robot during the song
- The robot performs various dance moves spanning disco to breakdance
- Set in a "digital dance arena" with dynamic lighting effects
- Specific signature move recreations:
  - Michael Jackson's moonwalk + glowing floor tiles under each footstep (reference to "Billie Jean" video)
  - Angus Young's rocking duckwalk (AC/DC)
- Peaked at #66 on UK Singles Chart

### Aesthetic Characteristics
- Early 2000s CGI style: relatively low-poly models, simple shaders, basic materials
- Retro-futuristic "digital arena" environment
- Robot design based on late-90s/early-2000s desktop PC components (tower case, CRT monitor head, etc.)

---

## Technical Landscape for Browser Recreation

### Recommended Engine: Three.js

**Why Three.js over alternatives:**
- Maturest web 3D ecosystem with extensive examples and community
- Built-in GLTF/GLB support (standard format for animated 3D assets)
- Excellent skeletal animation system (AnimationMixer, skinned meshes)
- Post-processing pipeline including bloom (critical for glowing tiles effect)
- TSL (Three Shading Language) for modern WebGPU-ready materials
- Works on WebGL 2.0 (widely supported) with WebGPU as opt-in upgrade path

**Key relevant capabilities found in docs:**
- `AnimationMixer` with crossfading between clips (walk ↔ dance transitions)
- `SkeletonUtils.retargetClip()` for applying motion capture to custom robot rigs
- Morph targets for facial/structural deformation during PC→robot transformation
- `BloomNode` post-processing for glowing floor tiles and neon arena effects
- `THREE.Sprite` particle systems for lighting atmospherics
- Film grain/scanline post-effects for retro video aesthetic

### Alternative: Babylon.js
- Stronger built-in physics and animation state machines
- Excellent skeletal animation tools
- Slightly heavier API; good choice if complex dance-state choreography needed
- Either engine is fully capable

### Not Recommended
- **Raw WebGL/WebGPU** — too low-level for character animation, lighting, and scene graph needs
- **Unity WebGL export** — heavy builds, poor web-native integration
- **Unreal Engine (Web)** — overkill for this aesthetic, massive bundle sizes

---

## Asset Requirements

### 3D Models Needed
1. **Robot character** — low-poly PC-inspired humanoid (tower case torso, monitor head, keyboard/cable details)
2. **PC mode** — the pre-transformation desktop computer form
3. **Dance arena environment** — simple reflective floor, grid/neon structures, dark void background

### Animation Requirements
- Skeletal rig for the robot (humanoid biped with PC-specific constraints)
- Individual dance move clips (moonwalk, duckwalk, breakdance freezes, disco pointing)
- Transformation sequence: PC → robot morph/assembly
- Music-synchronized transitions between moves

**Animation sourcing options:**
- **Motion capture retargeting:** Use free Mixamo dance animations retargeted to custom robot skeleton via `SkeletonUtils`
- **Manual keyframing:** Viable for low-poly stylized robot; fewer joints than realistic human
- **Procedural hybrid:** Code some rhythmic movements (bouncing to beat), keyframe signature moves

---

## Technical Implementation Breakdown

| Component | Approach | Complexity |
|-----------|----------|------------|
| Scene setup & camera | Three.js scene with animated camera cuts matching video | Low |
| Robot model + rig | Custom GLB model with Mixamo-compatible skeleton | Medium |
| PC→Robot transformation | Morph targets or scripted part-assembly animation | Medium |
| Dance animation system | AnimationMixer with synced clip transitions | Medium |
| Glowing floor tiles | Emissive plane tiles + Bloom post-processing | Low |
| Arena lighting | Point/spot lights with animated color/intensity | Low |
| Music sync | Web Audio API beat detection or manual BPM-timed events | Medium |
| Retro video aesthetic | Post-processing: slight chromatic aberration + film grain | Low |

---

## Work Estimate

### Scenario A: Stylized Recreation (Faithful aesthetic, simplified scope)
- **Modeling:** Use existing free robot GLB models, modify to look PC-inspired (2–3 days)
- **Rigging + animation:** Retarget Mixamo dance clips, keyframe 3–4 signature moves (3–4 days)
- **Environment + effects:** Grid floor, bloom, basic lighting (1–2 days)
- **Music sync + sequencing:** Manual beat-mapped animation triggers (2 days)
- **Polish:** Camera work, retro post-FX, responsive layout (2 days)
- **Total: 2–3 weeks** (solo developer comfortable with Three.js)

### Scenario B: Pixel-Perfect Recreation
- **Custom modeling:** Sculpt exact 2001 video robot from reference frames (1–2 weeks)
- **Full animation suite:** Hand-keyframe every dance move to match original timing (2–3 weeks)
- **Transformation sequence:** Complex scripted assembly animation (3–5 days)
- **Environment recreation:** Exact digital arena with all lighting variations (3–4 days)
- **Camera editing:** Match every cut and camera move from original (2–3 days)
- **Total: 6–10 weeks** (solo developer)

### Critical Path Dependencies
1. Access to the original video for visual reference (needed for any detailed recreation)
2. The song audio file for beat sync
3. Three.js familiarity (learning curve ~1 week if new to the library)

---

## Risk Factors

- **Asset availability:** No pre-made "dancing PC robot" model exists; custom modeling required
- **Video reference:** Original video is obscure; finding high-quality reference may be difficult
- **Animation quality:** Dancing robots are inherently in the "uncanny valley" — stylized/cartoony approach is easier and arguably more charming
- **Music rights:** Syncing to the original track requires licensing for any public deployment

---

## Recommended Tech Stack

```
Frontend: Vanilla JS/TS + Vite
3D Engine: Three.js (WebGL 2.0 renderer)
Asset format: GLB/GLTF (models + animations)
Audio: Web Audio API (beat sync)
Post-processing: Three.js EffectComposer (BloomNode, FilmGrain, ChromaticAberration)
Build: Static SPA deployable to any host
```

---

## Summary

The original video's 2001 CGI aesthetic is actually an **advantage** for live web recreation — the low-poly models, simple materials, and stylized lighting are well within what modern WebGL handles effortlessly at 60fps. The core challenge is **asset creation** (modeling, rigging, animation) rather than rendering technology.

A skilled Three.js developer could ship a recognizable, charming recreation in **2–3 weeks** by leveraging free motion-capture dance data, off-the-shelf bloom/lighting effects, and deliberately embracing the retro-CGI style. A frame-perfect recreation would require significantly more animation polish and likely **2+ months** of focused work.
