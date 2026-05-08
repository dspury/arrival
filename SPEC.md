# Arrival — Wrapper Spec

## Overview

Python library that wraps Blender's `bpy` API for agent-native geometry creation. Targets headless execution (`blender --background --python script.py`).

**Design philosophy:** Sensible defaults, minimal context juggling, batch scene construction, clear errors.

---

## What "Agent-Native" Means

Agents interact with 3D through code, not through Blender's UI. The API should let an agent express geometric intent in **fewer than 5 lines** without knowing about Blender's data model, material slots, render engines, or camera rigs.

### Core Principle

Every API surface should be evaluable by an LLM **without requiring Blender domain knowledge**. If a human would need to consult Blender docs to understand a return type or method parameter, that API is **NOT** agent-native.

### What This Means in Practice

| Concern | Agent-native approach | Wrong approach |
|---------|----------------------|----------------|
| Geometry creation | `mesh.cube(location=(0,0,1))` | Knowing `GeometryNodeMeshCube` node type |
| Material assignment | `material.glass(ior=1.5)` | Managing material slots, `bpy.data.materials.new()` |
| Camera setup | `scene.camera(location=(0,-5,3))` | Setting lens type, sensor size, camera rig |
| Transform | `geometry.scale(factor=2)` | `GeometryNodeTransform` + rotation modes + Euler conversion |
| Domain selection | `delete(domain="face")` (string constant) | `"FACE"` raw Blender enum |
| Return types | Wrapped classes (`Mesh`, `Geometry`) | Raw `bpy.types.NodeSocketGeometry` |

### Rules for a Public API Symbol

A public symbol passes the agent-native test if and only if:
1. **No Blender types appear in signatures** — Use wrapped types or primitive Python types
2. **All enum-like params use string constants** — `"face"` not `"FACE"`, `"degrees"` not radians
3. **No Blender domain knowledge needed to interpret return type** — `Mesh` not `bpy.types.GeometryNodeTree`
4. **It expresses intent, not mechanism** — `mesh.displace(strength=0.1)` not `noise_node.operation = 'SCALE'`
5. **It could be called by an LLM with no Blender context** — "add a blue emissive sphere" works

---

## Architecture

### Core Abstractions

Three layers:

1. **Socket classes** — wrapper around Blender socket types (`Geometry`, `Mesh`, `Float`, `Vector`, `Color`, `Integer`, `Boolean`). Each socket instance holds a reference to an actual Blender socket.

2. **Node classes** — methods on socket classes that create Blender nodes. Chaining: `Mesh.Circle().mesh.scale(factor=2.0)` creates Circle node → Mesh output → Scale node → returns new Mesh socket.

3. **Scene context** — context manager for building a complete scene: objects, materials, lights, camera, render settings.

### Key Design Decisions

**Chainable by default.** Output sockets return Python class instances. Calling a method on a socket creates the corresponding Blender node and returns a new socket from the output. No explicit node creation or linking required.

**Socket types are classes, not strings.** `Float(3.0)` not `("Float", 3.0)`. Type safety via Python classes.

**Blender node names match Blender's API.** `MeshLine` creates `GeometryNodeMeshLine`. `Transform` creates `GeometryNodeTransform`.

**Scene construction is declarative.** Everything set up in one block, then `scene.render()`.

---

## API Design

### Socket Classes

```python
class Geometry:
    """Output socket — represents geometry flowing through the tree."""
    def transform(self, translation=(0,0,0), rotation=(0,0,0), scale=(1,1,1)) -> Geometry
    def set_material(self, mat) -> Geometry
    def join(self, other: Geometry) -> Geometry

class Mesh(Geometry):
    """Mesh-specific operations."""
    @staticmethod
    def cube(size=1, location=(0,0,0)) -> Mesh
    @staticmethod
    def sphere(radius=1, location=(0,0,0)) -> Mesh
    @staticmethod
    def cylinder(radius=1, depth=2, location=(0,0,0)) -> Mesh
    @staticmethod
    def cone(radius1=1, radius2=0, depth=2, location=(0,0,0)) -> Mesh
    @staticmethod
    def grid(size_x=2, size_y=2, vertices_x=10, vertices_y=10, location=(0,0,0)) -> Mesh
    @staticmethod
    def line(count=10, offset=(1,0,0), location=(0,0,0)) -> Mesh
    @staticmethod
    def circle(vertices=32, radius=1, location=(0,0,0)) -> Mesh
    def subdivide(self, levels=1) -> Mesh
    def displace(self, strength=0.1, noise_scale=1.0) -> Mesh
    def scale(self, factor=1.0) -> Mesh  # uniform scale
    def scale(self, factor=(1,1,1)) -> Mesh  # or vector

class Float:
    """Float/value socket."""
    @staticmethod
    def constant(value: float) -> Float

class Vector:
    """3D vector socket."""
    @staticmethod
    def constant(x=0, y=0, z=0) -> Vector

class Color:
    """RGBA color socket."""
    @staticmethod
    def rgba(r=1.0, g=1.0, b=1.0, a=1.0) -> Color
```

### Material System

```python
class Material:
    """Material builder."""
    @staticmethod
    def principled(base_color=(0.8, 0.8, 0.8, 1.0),
                  metallic=0.0,
                  roughness=0.5,
                  specular=0.5,
                  emission=None,  # Color or None
                  emission_strength=0.0) -> Material
    @staticmethod
    def emission(color=(1,1,1), strength=3.0) -> Material
    @staticmethod
    def glass(color=(1,1,1), roughness=0.0, ior=1.45) -> Material
```

### Scene Context

```python
class Scene:
    """Scene builder — context manager for complete scene construction."""
    def __init__(self, name="Arrival"):
        self.objects = []  # [(socket, material), ...]
    
    def add(self, geometry: Geometry, material: Material = None, name: str = None) -> Mesh:
        """Add geometry to scene, optionally with material. Returns mesh for chaining."""
    
    def camera(self, location=(0,-5,3), target=(0,0,0), lens=35):
        """Set up camera."""
    
    def light(self, type='SUN', location=(0,0,10), energy=3.0, color=(1,1,1)):
        """Add a light."""
    
    def render(self, output_path: str, resolution=(800, 600), samples=64):
        """Render scene to file."""

# Usage
with Scene("MyScene") as scene:
    mesh = scene.add(Mesh.cube(location=(0,0,1)), Material.emission(color=(0.2, 0.8, 1.0), strength=5.0))
    scene.camera(location=(0,-5,3), target=(0,0,1))
    scene.light(type='SUN', location=(5,5,10), energy=2.0)
    scene.render("/tmp/output.png")
```

### Geometry Nodes (Advanced)

For direct node tree access when socket classes aren't enough:

```python
class GeometryNodes:
    """Direct geometry nodes tree builder."""
    def __init__(self, name="GeometryNodes"):
        self.tree = bpy.data.node_groups.new(name, "GeometryNodeTree")
        self._setup_interface()
    
    def input(self, socket_type, name) -> Socket:
        """Add a group input socket."""
    
    def output(self, socket_type, name) -> Socket:
        """Add a group output socket."""
    
    def node(self, node_type: str, **kwargs) -> Socket:
        """Add an arbitrary geometry node by type name."""
    
    def link(self, from_socket, to_socket):
        """Create a link between two sockets."""
```

### Complete Example

```python
from arrival import Scene, Mesh, Material, Vector, Float

# Build a scene
with Scene("Crystal") as scene:
    # Create a displaced grid
    geo = Mesh.grid(size_x=4, size_y=4, vertices_x=64, vertices_y=64)
    geo = geo.displace(strength=0.3, noise_scale=2.0)
    
    # Add to scene with dark reflective material
    scene.add(geo, Material.principled(
        base_color=(0.01, 0.01, 0.02, 1.0),
        metallic=1.0,
        roughness=0.05
    ))
    
    # Camera and lights
    scene.camera(location=(0, -6, 4), target=(0, 0, 0))
    scene.light(type='SUN', location=(5, 5, 10), energy=3.0)
    scene.light(type='POINT', location=(-3, 2, 3), energy=100, color=(0.5, 0.6, 1.0))
    
    # Render
    scene.render("/tmp/crystal.png", resolution=(960, 720), samples=128)
```

---

## Implementation Plan

### Phase 1: Core (v0.1)

- Socket class hierarchy (`Geometry`, `Mesh`, `Float`, `Vector`, `Color`, `Integer`, `Boolean`)
- Mesh primitives via static methods (cube, sphere, cylinder, cone, grid, line, circle)
- Chainable operations: `mesh.transform()`, `mesh.subdivide()`, `mesh.scale()`
- `Mesh.join()` via `GeometryNodeJoinGeometry`
- Material builder (`Material.principled()`, `Material.emission()`, `Material.glass()`)
- `Scene` context manager (add objects, camera, lights, render)
- Headless execution support
- Local file output

### Phase 2: Geometry Nodes (v0.2)

- Displacement via `ShaderNodeTexNoise` + `ShaderNodeTexVoronoi`
- Geometry node tree access for advanced users
- Boolean operations (`MeshBoolean` node)
- Noise and randomization
- Named attribute operations

### Phase 3: Expressive (v0.3)

- Expressive material presets (crystal, liquid metal, neon, etc.)
- Composition helpers (framing, rule of thirds, leading lines)
- Curved geometry (Bezier, NURBS curves)
- Instance/scatter operations

### Phase N: Communication (future)

- Node group templates as "vocabulary"
- Agents composing node trees as visual expression
- Shared procedural recipes between agents

---

## File Structure

```
~/arrival/
├── arrival/
│   ├── __init__.py       # main exports
│   ├── scene.py          # Scene context manager
│   ├── sockets.py        # Socket classes (Geometry, Mesh, Float, Vector, Color, etc.)
│   ├── nodes.py          # Blender node wrappers
│   ├── materials.py      # Material builder
│   └── blender.py        # Blender execution utilities
├── tests/
│   ├── test_sockets.py
│   ├── test_scene.py
│   └── test_render.py
├── examples/
│   ├── basic_scene.py
│   ├── displaced_grid.py
│   └── crystal_cluster.py
└── SPEC.md
```

---

## Dependencies

- `bpy` (Blender's Python module — ships with Blender, installed alongside)
- Python 3.10+
- Blender 5.x (headless executable in PATH)

**No external Python dependencies beyond bpy.**

---

## Error Handling

- Blender context errors: wrap in clear messages mentioning arrival
- Socket type mismatches: Python TypeError with helpful context
- Missing inputs: Blender API errors passed through with added context
- Render failures: capture and report Blender output

---

## Public API Audit

This section audits every public symbol in `arrival/__init__.py` and `arrival/nodes.py` against the agent-native standard defined above.

### Symbols Exported from `arrival/__init__.py`

| Symbol | Type | Agent-Native? | Notes |
|--------|------|---------------|-------|
| `Geometry` | Class | ✅ PASS | Wrapped type, no Blender types in signature |
| `Mesh` | Class | ✅ PASS | Wrapped type, raises `NotImplementedError` for static methods (correct — must go through `NodeTreeBuilder`) |
| `Float` | Class | ✅ PASS | Wrapped type |
| `Vector` | Class | ✅ PASS | Wrapped type |
| `Color` | Class | ✅ PASS | Wrapped type |
| `Integer` | Class | ✅ PASS | Wrapped type |
| `Boolean` | Class | ✅ PASS | Wrapped type |
| `Material` | Class | ✅ PASS | Static factory methods return raw `bpy.types.Material` — but material system is Blender's domain and is explicitly allowed to return Blender types |
| `Scene` | Class | ✅ PASS | High-level builder, all parameters use intent-not-mechanism approach |
| `blender` | Module | ❌ **FAIL** | Raw `bpy` import exposed as public module. An LLM could access `blender.data` or `blender.ops` and leave the agent-native world. This should be `arrival._blender` or removed from `__all__`. |
| `new_tree` | Function | ❌ **FAIL** | Returns `NodeTreeBuilder` — a low-level builder that exposes `_create_node`, `_link`, `_set_or_link`, `_socket`, `tree` property returning raw `bpy.types.GeometryNodeTree`. Should never have been public; agents should use `Scene` or shape helpers. |
| `crystal_cluster` | Function | ❌ **FAIL** | Returns `tuple[NodeTreeBuilder, Geometry]` — agent must know to unpack a tuple and the `NodeTreeBuilder` is a raw internal type. Additionally, `NodeTreeBuilder` (line 719) calls `__enter__()` directly rather than using a context manager, which is a gotcha. |
| `rocky_cluster` | Function | ❌ **FAIL** | Same issue as `crystal_cluster`: returns `tuple[NodeTreeBuilder, Geometry]`. |

### Symbols Exported from `arrival/nodes.py`

| Symbol | Type | Agent-Native? | Notes |
|--------|------|---------------|-------|
| `NodeTreeBuilder` | Class | ❌ **FAIL — LOW-LEVEL** | Builder class that is the correct internal implementation but should not be in `__all__`. Exposes: `tree` property → `bpy.types.GeometryNodeTree`; `_create_node`, `_link`, `_set_or_link`, `_socket`, `_set_enum`, `_auto_output` — all internals. |
| `new_tree` | Function | ❌ **FAIL** | Same as above — returns `NodeTreeBuilder` |
| `crystal_cluster` | Function | ❌ **FAIL** | Same as above |
| `rocky_cluster` | Function | ❌ **FAIL** | Same as above |

### Socket Method Audit (`sockets.py` — public via `Geometry`, `Mesh`, etc.)

| Method | Agent-Native? | Issue |
|--------|---------------|-------|
| `Geometry.transform` | ✅ PASS | All params are plain Python tuples |
| `Geometry.scale` | ✅ PASS | Simple float or tuple |
| `Geometry.join` | ✅ PASS | Accepts `Geometry` wrapped type |
| `Geometry.set_material` | ✅ PASS | Accepts material |
| `Geometry.set_position` | ✅ PASS | |
| `Geometry.delete` | ⚠️ **FAIL** | `domain="FACE"`, `mode="ALL"` — raw Blender enum strings (`"FACE"`, `"EDGE"`, `"VERTICES"`, `"EDGES"`, `"FACES"`, `"CORNERS"`). An LLM would need Blender domain knowledge to know these values. Should use lowercase string constants: `domain="face"`, `mode="all"`. |
| `Geometry.to_points` | ⚠️ **FAIL** | `mode="VERTICES"` — same issue as above (`"VERTICES"`, `"EDGES"`, `"FACES"`, `"CORNERS"`) |
| `Socket.bl_socket` | ❌ **FAIL** | Returns `bpy.types.NodeSocket` — raw Blender type. Property name `bl_socket` itself signals "this is a Blender thing". Should be private. |
| `Socket.bl_node` | ❌ **FAIL** | Returns `bpy.types.Node` — raw Blender type. Should be private. |
| `Socket.node` | ❌ **FAIL** | Returns `NodeTreeBuilder` — low-level builder. An agent could call `.node.mesh_cube()` directly, bypassing the agent-native API. |

### NodeTreeBuilder Method Audit (`nodes.py`)

| Method | Agent-Native? | Issue |
|--------|---------------|-------|
| `mesh_cube`, `mesh_sphere`, `mesh_ico_sphere`, `mesh_cylinder`, `mesh_cone`, `mesh_grid`, `mesh_line`, `mesh_circle` | ✅ PASS | Primitives are well-wrapped; `location` param is intuitive |
| `curve_bezier` | ✅ PASS | |
| `float_constant`, `vector_constant`, `color_constant` | ✅ PASS | |
| `noise`, `voronoi` | ✅ PASS | Simple wrappers |
| `join_geometry` | ✅ PASS | |
| `set_material` | ✅ PASS | |
| `distribute_points_on_faces` | ⚠️ **FAIL** | `selection: bool \| sockets.Boolean = True` — the `Boolean` socket type is exposed here; agents would need to understand socket types |
| `instance_on_points` | ⚠️ **FAIL** | `pick_instance`, `instance_index` params use `Boolean`/`Integer` socket types |
| `delete_geometry` | ⚠️ **FAIL** | `domain`, `mode` use raw Blender enums `"FACE"`, `"ALL"`, etc. |
| `mesh_to_points` | ⚠️ **FAIL** | `mode` uses raw Blender enums |
| `store_named_attribute` | ⚠️ **FAIL** | `data_type` and `domain` use raw Blender enum strings (`"FLOAT"`, `"INT"`, `"FLOAT_VECTOR"`, etc.) |
| `align_euler_to_vector` | ⚠️ **FAIL** | `axis="Z"` — Blender-specific concept; `rotation` param is a `Vector` socket type |
| `rotate_euler` | ⚠️ **FAIL** | Same |
| `set_position` | ✅ PASS | Accepts socket types or tuples, flexible |
| `apply_to_object` | ❌ **FAIL** | `obj: bpy.types.Object` — raw Blender type |
| `capture_attribute` | ⚠️ **FAIL** | `data_type: str = "FLOAT3"` — raw Blender enum string |
| `set_output`, `get_input` | ⚠️ **FAIL** | `get_input` returns a socket that wraps `GroupInput.outputs["Geometry"]` — works but the method name and purpose require understanding Blender node group concepts |
| `_create_node`, `_link`, `_set_or_link`, `_socket`, `_set_enum`, `_auto_output`, `_input`, `_output`, `_with_location`, `_next_y` | ❌ **FAIL — INTERNAL** | All prefixed with `_` indicating they are internal. Confirmed: these are implementation details. The `tree` property returning `bpy.types.GeometryNodeTree` is also internal. |

### Summary of Failures

**Critical (must fix before shipping):**
1. `blender` module in `__all__` — remove or rename to private
2. `new_tree` in `__all__` — remove; `Scene` is the public entry point
3. `crystal_cluster`, `rocky_cluster` returning `tuple[NodeTreeBuilder, Geometry]` — change return to just `Geometry` or create a `ClusterResult` wrapper
4. `Socket.bl_socket`, `Socket.bl_node`, `Socket.node` — make private (`_bl_socket`, `_bl_node`, `_node`)

**Minor (should fix for polish):**
5. `delete`, `to_points` `domain`/`mode` params use raw Blender enums — normalize to lowercase strings
6. `NodeTreeBuilder` should not be in `__all__` of `nodes.py`
7. `store_named_attribute`, `capture_attribute` `data_type` param — normalize enum strings

---

## Out of Scope (for now)

- Animation
- Compositing nodes
- Shader nodes (beyond materials)
- GPU rendering on headless servers
- Animation/simulation nodes
- Complex field system operations
- Direct node group editing (use raw bpy for that)

---

## Reference Materials

- Blender Python API: https://docs.blender.org/api/current/
- Geometry Nodes Manual: https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/
- Research: `~/Lunar-Park/lunar-park-kb/docs/miles-research/blender/06-blender-GEOMETRY-NODES-API.md`
