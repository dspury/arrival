# Phase 3 Plan — Arrival v0.3 "Expressive"

## Context

Phase 3 builds on the v0.2 "Geometry Nodes" release. The roast identified Arrival's core value:
> agents create and share 3D scenes programmatically

The highest-leverage additions are those that make Arrival more **shareable**, **expressive**, and **composable** as an agent visual language — not more complex geometry operations.

---

## Phase 3.1 — USD Export
**Priority: HIGH** | Estimated: 4–6 hours

USD (Universal Scene Description) is the standard interchange format for 3D content. Adding USD export lets agents:
- Save scenes for use in other DCC tools (Maya, Houdini, Cinema 4D, etc.)
- Share procedural scenes between agents
- Persist complex node trees without needing Blender runtime

### Deliverables
- `Scene.export_usd(path)` method on the Scene class
- Export geometry (mesh data), materials, and camera to `.usda` or `.usdc`
- Wrapper function `arrival.export_usd(geometry, path)` for one-shot use
- Test: render a scene, export to USD, verify file exists and contains expected content

### Implementation approach
- Use Blender's `bpy.ops.wm.usd_export` operator
- Package into a helper function that works with the Scene's existing node tree
- One-call convenience: `Mesh.to_usd(path)` and `Geometry.to_usd(path)` as methods

---

## Phase 3.2 — Expressive Material Presets
**Priority: MEDIUM** | Estimated: 3–4 hours

The current material system (principled, glass, emission, dark_mirror, obsidian) is solid but lacks the **expressiveness** that makes matplotlib seaborn popular. Agents should be able to say "make it look cinematic" or "give it a neon aesthetic" without knowing PBR values.

### Deliverables
- `Material.cinematic()` — filmic look with warm highlights, cool shadows
- `Material.neon(glow_color)` — emissive with halo effect
- `Material.metallic_gold()` — gold metallic with slight roughness variation
- `Material.holographic()` — iridescent/shimmer effect
- `Material.clay()` — matte, clay-like render for sculpt visualization

---

## Phase 3.3 — Composition Presets
**Priority: MEDIUM** | Estimated: 2–3 hours

Agents should be able to say "compose this as a product shot" or "cinematic wide" without manually positioning camera and lights.

### Deliverables
- `scene.compose(preset)` where preset options include:
  - `"product"` — centered, soft three-point lighting, neutral background
  - `"cinematic"` — shallow depth of field feel, dramatic lighting
  - `"wide"` — full object in frame with environmental context
  - `"macro"` — close-up, extreme detail capture

---

## Phase 3.4 — Better Error Messages & Debug Helpers
**Priority: LOW** | Estimated: 2–3 hours

Agent-native means errors that don't require Blender domain knowledge to fix.

### Deliverables
- Custom exception types with suggested fixes
- `Scene.debug()` method that outputs the node tree graph as ASCII art
- Validation that catches common mistakes before render (missing geometry, unlinked nodes)

---

## Testing Strategy

Each phase ships with:
1. Unit tests for the new API
2. An example script in `examples/`
3. Update to `SPEC.md` with the new public API symbols

---

## Out of Scope

- Animation (future phase)
- Physics
- Web viewer
- Direct shader node editing
- Animation/simulation nodes