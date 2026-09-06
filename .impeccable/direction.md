# Current direction: monochrome glass

User selected fog white (#f7f7f8), ink (#242428), and explicitly requested glassmorphism. Preserve existing navigation, content and library workflows. Use translucent white large surfaces, restrained silver light, clear glass edges and local backdrop blur; no green in site chrome. Reduce per-card GPU work. Catalogs use bilingual static specimen previews with near-viewport loading; detail pages keep live specimens. No new identity selection or comp approval is required for this explicit brief.

Performance objective: remove whole-library prefetch, eager catalog requests, and catalog animation scripts. First content and largest content must appear earlier under the same local 150ms / 200KB/s / 4x CPU test. Public GitHub Pages connection time is measured separately and remains a hosting constraint.

User correction, 2026-09-07: UI dictionary animations are mandatory. Replace its static-preview strategy with original live specimens in on-demand isolated frames; destroy offscreen frames and pause in background tabs. First three specimen sources are inline. Other catalog surfaces retain their current strategy. The correction overrides the earlier instruction to remove catalog animation scripts.
