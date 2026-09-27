# Starting a fresh session

The context in any one session eventually gets too deep to work well. Everything needed
to resume is on disk; this is the prompt that gets a new session up to speed.

**Paste this:**

```
Continuing work recreating the Playgroup "Number One" (2001) music video as a live
Three.js animation. Repo: /Users/yozgrahame/code/number1-video

Read these in order, before doing anything else:
  1. AGENTS.md  — working discipline. Follow it, and keep it updated as you learn.
  2. STATE.md   — where the work stands and what to do next.
  3. README.md  — project detail: timeline, build notes, known gaps.

Then tell me: (a) what you understand the current state to be, (b) what you think the
next action is, and (c) anything in those docs that contradicts itself or looks stale.
Wait for my confirmation before starting work.
```

That last part is deliberate — asking for a summary *and* a report of contradictions
catches a stale or self-inconsistent doc before it sends the session off in the wrong
direction, and it is cheap.

## What the new session gets

| File | Role |
|---|---|
| `AGENTS.md` | working discipline — measured rules, each with the cost that produced it |
| `STATE.md` | position: what's built, what's next, what's undecided |
| `README.md` | project detail, timeline, build notes, known gaps |
| `research/shot-list.md` | timecoded breakdown of all four acts + a corrections log |
| `log/sessions/*.md` | full transcripts, including the reasoning behind decisions |
| `tools/` | bake, diff, compare, framing, session-log, shoot |

## Before you end a session

```sh
tools/session-log.py     # archive the transcript; idempotent
```

Then update `STATE.md` — the position will have moved, and a stale position doc is
worse than none.

## Why the transcripts matter

The summary docs record *outcomes*: what was decided. They lose *why*, and they lose
the dead ends. The transcripts have both — including several approaches that were tried,
appeared to work, and turned out to be wrong in ways that were not obvious (edge-based
segmentation silently inverting; a camera distance that matched coverage but not angle).
A session that re-derives those from scratch will waste the same days.
