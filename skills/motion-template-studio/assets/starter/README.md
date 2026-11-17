# Instructions for AI

Read motion.json, guide.json and params.schema.json first. This is an author project, not a signed personal download. It is a diagnostic scaffold, not a completed recreation.

Local author preview/export (execution-capable host):

`node tools/render.mjs --project . --inputs presets/demo.json --out /absolute/new-output.mp4 --silent`

The explicit silent option is for this soundless diagnostic. For a reference with sound, preserve and bind actual sound with an audio plan. Read tools/render.mjs's contract before execution. Node 22+, Python jsonschema, Playwright and a launchable Chromium, FFmpeg and ffprobe are required; not bundled. MOTION_PLAYWRIGHT_MODULE and CHROME_PATH can name already installed tools. No global MotionGit login or account key is used by this local author runner.

The canvas reference API is window.renderFrame(integerFrame, inputs). The local runner checks repeat/fresh seeking at one representative frame, then renders all output frames. Static checks, seek checks and full decode do not establish visual similarity or full listening. Keep those statuses separate.

This runner intentionally rejects HTML video/audio and Web Audio. To reconstruct media-bearing templates, use a verified media-capable original runtime/adapter with an explicit audio contract, preserve that adapter inside the author project and update motion.json and these instructions. Do not remove media or silently flatten it to claim this route supports it.
