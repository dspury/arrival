# Arrival — Wrapper Spec

## Overview

Python library that wraps Blender's `bpy` API for agent-native geometry creation. Targets headless execution (`blender --background --python script.py`).

**Design philosophy:** Sensible defaults, minimal context juggling, batch scene construction, clear errors.

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
