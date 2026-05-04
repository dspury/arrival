# Arrival — Agent-native 3D Geometry Library

## Overview

Python library wrapping Blender's `bpy` API for agent-native geometry creation. Headless execution (`blender --background --python script.py`).

## Design Philosophy

- Sensible defaults, minimal context juggling
- Batch scene construction
- Chainable API (geonodes-inspired)
- Clear error messages

## Key Patterns

- **Socket classes** — `Geometry`, `Mesh`, `Float`, `Vector`, `Color`, etc. hold references to Blender sockets
- **Nodes as methods** — `mesh.scale(factor=2.0)` creates a Scale node, returns new Mesh socket
- **Chainable** — `Mesh.Circle().mesh.scale(2.0).subdivide(3)`
- **Scene context** — `with Scene("Name"):` block for full scene construction

## Critical API Sequence (Blender 5.1.1)

1. Create node group: `bpy.data.node_groups.new(name, "GeometryNodeTree")`
2. **Define interface sockets FIRST** (creates actual sockets on GroupInput/GroupOutput)
3. Add GroupInput and GroupOutput nodes
4. Add primitive/generator nodes
5. Wire: GroupInput → [generators] → [operators] → GroupOutput

**IMPORTANT:** GroupInput/GroupOutput sockets don't exist until interface is defined. This is the #1 gotcha.

## Key Node Types

- `GeometryNodeMeshLine` / `GeometryNodeMeshCube` / `GeometryNodeMeshUVSphere` — primitives
- `GeometryNodeTransform` — geometry transform
- `GeometryNodeJoinGeometry` — merge geometry streams
- `ShaderNodeTexNoise` / `ShaderNodeTexVoronoi` — displacement

## Socket Types

- `NodeSocketGeometry` — geometry (mesh, curve, points)
- `NodeSocketFloat` — float values
- `NodeSocketVector` — 3D vectors
- `NodeSocketInt` — integers
- `NodeSocketBool` — booleans
- `NodeSocketColor` — RGBA colors

## References

- SPEC.md — full API specification
- ~/Lunar-Park/lunar-park-kb/docs/miles-research/blender/06-blender-GEOMETRY-NODES-API.md — validated API research
