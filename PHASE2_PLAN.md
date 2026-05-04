# Arrival Phase 2 Plan

## Context

Arrival is a Python library for agents to create procedural 3D geometry via Blender's geometry nodes API. Phase 1 (v0.1) delivered the foundation: socket classes, NodeTreeBuilder context, mesh primitives, basic materials.

Phase 2 focuses on what agents need to express visual intent — instancing, deformation, and UV/texture flow.

## Priority 1: Instance on Points

The single most impactful missing feature. Enables:
- crystals/trees/structures growing from surfaces
- particle-like distributions
- repeated motifs with variation

### Implementation

Add to `nodes.py`:
```python
def instance_on_points(self, points: Geometry, instance: Geometry,
                       rotation: Geometry = None, scale: Geometry = None) -> Geometry
```

Node: `GeometryNodeInstanceOnPoints`
- Points geometry input → instances placed at point positions
- Instance input → what gets instanced
- Rotation/Scale inputs → optional per-instance variation via separate node trees

### Supporting methods

```python
# Distribute points on a surface
def distribute_points(self, geometry: Geometry, density: float = 1.0) -> Geometry
# Node: GeometryNodeDistributePointsOnFaces

# Get point positions from geometry (for chaining)
def capture_attribute(self, geometry: Geometry, name: str = "position") -> Geometry
# Node: GeometryNodeInputMeshVertexPositions + GeometryNodeStoreNamedAttribute
```

## Priority 2: Deformation Pipeline

Transform is rigid. Deformation is alive. Need:

### 2a. Vector Math Operations
```python
# Add these to NodeTreeBuilder:
def add(self, a: Vector, b: Vector) -> Vector
def multiply(self, v: Vector, scalar: Float) -> Vector
def mix(self, a: Geometry, b: Geometry, factor: Float) -> Geometry
```
Node: `ShaderNodeVectorMath` (operations: ADD, MULTIPLY, etc.)
Node: `ShaderNodeMix` (for geometry mix)

### 2b. Displacement via Noise
```python
# Displace geometry along normals using noise
def displace(self, geometry: Geometry,
             noise: Float,
             strength: float = 1.0) -> Geometry
```
Node chain: `GeometryNodeOffsetInGeometry` or manual approach via `Position → SeparateXYZ → Add → Offset`.

### 2c. Set Position (vertex displacement)
```python
def set_position(self, geometry: Geometry,
                 offset: Vector = None,
                 selection: Geometry = None) -> Geometry
```
Node: `GeometryNodeSetPosition`

## Priority 3: UV / Texture Coordinate Flow

Materials need more than flat colors. UV coordinates enable:
- procedural textures
- material variation
- surface detail via bump maps

### Implementation
```python
# In NodeTreeBuilder:
def uv_map(self, geometry: Geometry) -> Vector
# Node: GeometryNodeInputUVMap

def capture_uv(self, geometry: Geometry, name: str = "UVMap") -> Geometry
# Node: GeometryNodeStoreNamedAttribute (for UV attribute)

# In Socket classes:
class Mesh(Geometry):
    def uv_project(self, uv_map: Vector) -> Mesh
    # Capture and store UV for material use
```

### Alternative: Procedural UV via Texture Coordinate
```python
def texture_coord(self) -> Vector
# Node: GeometryNodeInputTextureCoordinate ( outputs["UV"] )
```

## Priority 4: Attribute System

Geometry nodes are data-flow graphs. Attributes carry per-point/per-face data:
- positions
- normals  
- custom attributes (e.g., a "density" float per vertex)

```python
def store_attribute(self, geometry: Geometry,
                    name: str, data: Float) -> Geometry
# Node: GeometryNodeStoreNamedAttribute

def sample_attribute(self, geometry: Geometry,
                      attribute: str) -> Float
# Node: GeometryNodeAttributeStatistic (or sample from nearest)
```

## Priority 5: Domain Operations

Work at different levels of the geometry hierarchy (point, edge, face, vertex):

```python
def delete_geometry(self, geometry: Geometry,
                   selection: Geometry = None,
                   domain: str = 'FACE') -> Geometry
# Node: GeometryNodeDeleteGeometry (domain: VERT, EDGE, FACE, CURVE)

def mesh_to_points(self, geometry: Geometry) -> Geometry
# Node: GeometryNodeMeshToPoints
```

## Non-Goals for Phase 2

- Full shader graph (beyond what's in materials.py)
- Animation/time-based effects
- Complex curves beyond basic bezier
- NURBS/spline manipulation

## File Structure (Phase 2 additions)

```
arrival/
  __init__.py          # exports
  sockets.py           # Geometry, Mesh, Float, Vector, Color
  nodes.py             # NodeTreeBuilder + new methods
  materials.py         # existing
  scene.py             # existing
  blender.py           # existing
  deform.py            # NEW: deformation operations
  instance.py          # NEW: instancing operations
  attributes.py        # NEW: attribute read/write
  texture.py           # NEW: UV and texture coordinate flow
```

## Testing

- `test_instance.py`: instancing cubes on sphere points
- `test_deform.py`: noise displacement on grid
- `test_uv.py`: procedural texture on deformed mesh

## Success Criteria

An agent can build something like "a crystal cluster" — multiple icosphere instances on a surface, each slightly rotated/scaled differently, with noise-based vertex displacement, rendered with a dark mirror material. This exercises instancing + deformation + materials.
