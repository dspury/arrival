# Changelog

All notable changes to **Arrival** will be documented here.

## [0.2.0] — 2026-05-07

### Added
- **`arrival.show(geometry)`** — One-call render with smart camera framing and material defaults. The `plt.show()` moment.
- **`Scene.to_dict()`** — Serialize scene to JSON. Geometry, lights, camera, materials, render settings — everything an agent needs to reconstruct the scene.
- **`Scene.from_dict(data)`** — Reconstruct a scene from JSON. Full round-trip.
- **`arrival.describe(scene)`** — Text summary of a scene for LLM context. Object counts, geometry types, material names, light setup.
- **`examples/recipes/`** — Reference implementations moved here. `crystal_cluster.py`, `rocky_cluster.py`.
- **GitHub Actions CI** — Blender headless tests on every push and PR.

### Changed
- **`SPEC.md`** — Added formal "agent-native" definition. Public API surface audited and documented.
- **`README.md`** — Full rewrite with install instructions and hello-world example.
- **`pyproject.toml`** — Added `bpy` pin and editable install support.

### Fixed
- `scene.py` indentation bug in `render` and `render_and_save` methods.

---

## [0.1.0] — 2026-05-04

Initial release. Geometry nodes API, Icosphere, UV sphere, cylinder, cone, torus, plane, circle, UV editor primitives. Basic material support. Crystal cluster and rocky cluster example scenes.
