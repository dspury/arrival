# Arrival Phase 2 Plan

## Context

Arrival is a Python library for agents to create procedural 3D geometry via Blender's geometry nodes API. Phase 1 delivered the foundation: socket wrapper classes, `NodeTreeBuilder`, mesh primitives, simple transforms, noise/random value nodes, and basic materials.

Phase 2 should add the smallest set of geometry-node operations that lets agents express repeated forms and organic surface variation without exposing raw `bpy` node wiring.

## Design Constraints From Current Code

- Keep the public API centered on `NodeTreeBuilder` methods plus chainable `Geometry`/`Mesh` methods in `sockets.py`.
- Do not add `deform.py`, `instance.py`, `attributes.py`, or `texture.py` in Phase 2. The package is still small, and new modules would create import/export churn before there is enough code to justify them.
- Match existing names: builder constructors use `mesh_cube`, `mesh_grid`, `noise`, `random_float`; socket methods use verbs like `transform`, `join`, `set_material`, `subdivide`.
- Return Arrival socket wrappers, not raw Blender sockets. Use `Geometry`, `Mesh`, `Float`, `Vector`, `Boolean`, and add `Rotation` only if a Blender rotation socket is actually needed.
- Accept plain Python defaults where possible, but allow socket inputs for field-driven behavior. Add internal helpers so every method can link a socket or assign a default consistently.

## Priority 0: API Cleanup Required First

Before adding Phase 2 nodes, fix the current rough edges that will otherwise make the new plan brittle.

### Shared internal helpers in `nodes.py`

Add these private helpers to `NodeTreeBuilder` and use them in both new code and opportunistically in touched existing methods:

```python
def _link(self, source: sockets.Socket, target: bpy.types.NodeSocket) -> None

def _set_or_link(self, target: bpy.types.NodeSocket, value) -> None
# If value is an Arrival Socket, link value.output_socket to target.
# Otherwise assign target.default_value = value.

def _socket(self, cls, bl_node: bpy.types.Node, output_name: str)
# Return cls(self, bl_node.outputs[output_name], bl_node).
```

This keeps Phase 2 method bodies short and avoids repeating fragile `default_value`/`links.new` logic.

### Fix existing inconsistent methods

- `Geometry.transform(...)`: either wire rotation correctly or document that rotation is deferred. Prefer supporting tuple rotation by assigning the `Rotation` input if the Blender API accepts Euler tuples in the active version; otherwise leave it out of Phase 2 examples.
- `Geometry.join(...)` and `NodeTreeBuilder.join_geometry(...)`: remove attempts to assign `default_value` or `link_default_value` on geometry sockets. Multi-input sockets only need links.
- `Mesh.displace(...)`: replace the current broken placeholder. It creates `GeometryNodeAttributeVectorMath`, links mesh geometry into a vector socket, and returns a `Mesh` wrapper around a vector output. Phase 2 should implement displacement with `GeometryNodeSetPosition` instead.
- Primitive `location` parameters are currently unused. Either apply a `transform(translation=location)` when non-zero, or remove `location` from examples until implemented. Prefer implementing location because the API already exposes it.

## Priority 1: Instancing Pipeline

This is the highest-impact missing feature. It enables clusters, scatter, repeated motifs, surface growth, and particle-like arrangements.

### Builder methods

```python
def distribute_points_on_faces(
    self,
    geometry: sockets.Geometry,
    density: float | sockets.Float = 1.0,
    seed: int = 0,
    selection: bool | sockets.Boolean = True,
) -> sockets.Geometry
```

Node: `GeometryNodeDistributePointsOnFaces`

Socket details:
- Link `geometry` to input `"Mesh"`.
- Set/link `density` to `"Density"`.
- Set/link `selection` to `"Selection"` if available.
- Set `"Seed"` to `seed`.
- Return output `"Points"` as `Geometry`.

Keep the method name explicit. A shorter alias can be added after the behavior is stable:

```python
def points_on_faces(self, geometry, density=1.0, seed=0, selection=True) -> sockets.Geometry
```

```python
def instance_on_points(
    self,
    points: sockets.Geometry,
    instance: sockets.Geometry,
    rotation: tuple[float, float, float] | sockets.Vector | None = None,
    scale: float | tuple[float, float, float] | sockets.Vector = 1.0,
    pick_instance: bool | sockets.Boolean = False,
    instance_index: int | sockets.Integer = 0,
) -> sockets.Geometry
```

Node: `GeometryNodeInstanceOnPoints`

Socket details:
- Link `points` to input `"Points"`.
- Link `instance` to input `"Instance"`.
- Set/link `"Scale"` from `scale`; convert a scalar to `(scale, scale, scale)`.
- Set/link `"Rotation"` only after verifying whether Blender expects a rotation socket or accepts Euler-compatible values. If it does not accept a `Vector`, keep `rotation` tuple-only for Phase 2 and avoid a `Vector` promise.
- Set/link `"Pick Instance"` and `"Instance Index"` when available.
- Return output `"Instances"` as `Geometry`.

```python
def realize_instances(self, geometry: sockets.Geometry) -> sockets.Geometry
```

Node: `GeometryNodeRealizeInstances`

Socket details:
- Link `geometry` to input `"Geometry"`.
- Return output `"Geometry"`.

`realize_instances` is not optional. Most downstream operations, including material assignment and deformation after instancing, become confusing without it.

### Chainable socket aliases

Add thin methods on `Geometry` that delegate to the builder:

```python
def points_on_faces(self, density=1.0, seed=0, selection=True) -> Geometry
def instance_on_points(self, instance, rotation=None, scale=1.0, pick_instance=False, instance_index=0) -> Geometry
def realize_instances(self) -> Geometry
```

Expected usage:

```python
base = tree.mesh_ico_sphere(radius=2.0, subdivisions=3)
points = base.points_on_faces(density=8.0, seed=4)
crystal = tree.mesh_cone(radius1=0.12, radius2=0.0, depth=0.8)
cluster = points.instance_on_points(crystal, scale=0.6).realize_instances()
tree.set_output(cluster)
```

## Priority 2: Field and Math Primitives

Instancing and deformation need field values. Add these before implementing higher-level deformation helpers.

### Input field nodes

```python
def position(self) -> sockets.Vector
```

Node: `GeometryNodeInputPosition`

Return output `"Position"` as `Vector`.

```python
def normal(self) -> sockets.Vector
```

Node: `GeometryNodeInputNormal`

Return output `"Normal"` as `Vector`.

```python
def index(self) -> sockets.Integer
```

Node: `GeometryNodeInputIndex`

Return output `"Index"` as `Integer`.

### Vector math

```python
def vector_add(self, a: sockets.Vector | tuple, b: sockets.Vector | tuple) -> sockets.Vector
def vector_subtract(self, a: sockets.Vector | tuple, b: sockets.Vector | tuple) -> sockets.Vector
def vector_scale(self, vector: sockets.Vector | tuple, scale: sockets.Float | float) -> sockets.Vector
```

Node: `ShaderNodeVectorMath`

Socket details:
- `vector_add`: operation `'ADD'`, inputs `0` and `1`, output `"Vector"`.
- `vector_subtract`: operation `'SUBTRACT'`, inputs `0` and `1`, output `"Vector"`.
- `vector_scale`: operation `'SCALE'`, vector input `0`, scale input `"Scale"` if available or the scalar input exposed by Blender for that operation.

Avoid a generic `add(...)` name in Phase 2. It will collide conceptually with float math and makes type errors harder for agents to understand.

### Float math

```python
def float_add(self, a: sockets.Float | float, b: sockets.Float | float) -> sockets.Float
def float_multiply(self, a: sockets.Float | float, b: sockets.Float | float) -> sockets.Float
def map_range(
    self,
    value: sockets.Float | float,
    from_min: float = 0.0,
    from_max: float = 1.0,
    to_min: float = 0.0,
    to_max: float = 1.0,
    clamp: bool = True,
) -> sockets.Float
```

Nodes:
- `ShaderNodeMath` with operations `'ADD'` and `'MULTIPLY'`.
- `ShaderNodeMapRange` for remapping noise/random fields.

### Random vector

```python
def random_vector(
    self,
    min_val: tuple[float, float, float] = (0.0, 0.0, 0.0),
    max_val: tuple[float, float, float] = (1.0, 1.0, 1.0),
    seed: int = 0,
) -> sockets.Vector
```

Node: `FunctionNodeRandomValue`

Implementation detail:
- Set `data_type = 'FLOAT_VECTOR'` if that enum is available in the active Blender version.
- Set `"Min"`, `"Max"`, and `"Seed"`.
- Return output `"Vector"`.

Use this for per-point scale variation before attempting per-point random rotation.

## Priority 3: Deformation With `Set Position`

Implement real vertex displacement using the field nodes above.

### Low-level set position

```python
def set_position(
    self,
    geometry: sockets.Geometry,
    position: sockets.Vector | tuple | None = None,
    offset: sockets.Vector | tuple | None = None,
    selection: sockets.Boolean | bool = True,
) -> sockets.Geometry
```

Node: `GeometryNodeSetPosition`

Socket details:
- Link `geometry` to input `"Geometry"`.
- Set/link `"Selection"` from `selection`.
- If `position` is not `None`, set/link input `"Position"`.
- If `offset` is not `None`, set/link input `"Offset"`.
- Return output `"Geometry"`.

Add a chainable alias:

```python
def set_position(self, position=None, offset=None, selection=True) -> Geometry
```

### Noise displacement convenience

```python
def displace_noise(
    self,
    geometry: sockets.Geometry,
    strength: float | sockets.Float = 0.1,
    noise_scale: float = 1.0,
    detail: float = 8.0,
    along_normal: bool = True,
) -> sockets.Geometry
```

Implementation:
1. Create `noise = self.noise(scale=noise_scale, detail=detail)`.
2. Remap noise from `[0, 1]` to `[-strength, strength]` using `map_range`.
3. If `along_normal` is true, compute `offset = vector_scale(self.normal(), remapped_noise)`.
4. Otherwise compute a simple Z offset vector. This requires either a `combine_xyz(x=0, y=0, z=remapped_noise)` helper or a documented limitation for Phase 2.
5. Return `set_position(geometry, offset=offset)`.

Socket aliases:

```python
def displace_noise(self, strength=0.1, noise_scale=1.0, detail=8.0, along_normal=True) -> Geometry
```

For `Mesh.displace(...)`, keep backward compatibility by delegating to `displace_noise(...)`:

```python
def displace(self, strength=0.1, noise_scale=1.0) -> Mesh | Geometry
```

Do not use `GeometryNodeOffsetInGeometry`; that is not a realistic implementation target for this API. `GeometryNodeSetPosition` is the correct Phase 2 primitive.

## Priority 4: Mesh Selection and Domain Operations

These are useful immediately after instancing/deformation and are less speculative than UV work.

```python
def delete_geometry(
    self,
    geometry: sockets.Geometry,
    selection: sockets.Boolean | bool = True,
    domain: str = "FACE",
    mode: str = "ALL",
) -> sockets.Geometry
```

Node: `GeometryNodeDeleteGeometry`

Socket details:
- Link `geometry` to `"Geometry"`.
- Set/link `"Selection"`.
- Set `domain` on the node using Blender's enum after validating allowed values.
- Set `mode` only if exposed by the active Blender version.
- Return `"Geometry"`.

```python
def mesh_to_points(
    self,
    mesh: sockets.Geometry,
    mode: str = "VERTICES",
    radius: float | sockets.Float = 0.05,
) -> sockets.Geometry
```

Node: `GeometryNodeMeshToPoints`

Socket details:
- Link `mesh` to input `"Mesh"`.
- Set `mode` on the node.
- Set/link `"Radius"`.
- Return output `"Points"`.

Chainable aliases:

```python
def delete(self, selection=True, domain="FACE", mode="ALL") -> Geometry
def to_points(self, mode="VERTICES", radius=0.05) -> Geometry
```

## Priority 5: Minimal Attribute and UV Flow

Keep this narrow. The original plan overreached by proposing `sample_attribute(...)` via `GeometryNodeAttributeStatistic`; that node computes statistics and is not a general attribute sampler.

### Store named attributes

```python
def store_named_attribute(
    self,
    geometry: sockets.Geometry,
    name: str,
    value: sockets.Float | sockets.Vector | sockets.Color | bool | float | tuple,
    data_type: str,
    domain: str = "POINT",
    selection: sockets.Boolean | bool = True,
) -> sockets.Geometry
```

Node: `GeometryNodeStoreNamedAttribute`

Socket details:
- Link `geometry` to `"Geometry"`.
- Set `"Name"` to `name`.
- Set/link `"Selection"`.
- Set node `data_type` and `domain` using Blender enums.
- Link or assign `value` to the matching value input for the chosen `data_type`.
- Return output `"Geometry"`.

Do not add `sample_attribute(...)` until there is a concrete use case and a verified Blender node path such as named attribute input, capture attribute, or sample nearest/surface.

### Capture attribute only if needed by tests

```python
def capture_attribute(
    self,
    geometry: sockets.Geometry,
    value: sockets.Float | sockets.Vector | sockets.Color,
    data_type: str,
    domain: str = "POINT",
) -> tuple[sockets.Geometry, sockets.Socket]
```

Node: `GeometryNodeCaptureAttribute`

This returns two outputs, so it does not fit the current single-socket wrapper pattern cleanly. Defer it unless `store_named_attribute` is insufficient for the Phase 2 examples.

### UV plan

Defer full UV projection. Phase 2 can include only:

```python
def uv_map(self, name: str = "UVMap") -> sockets.Vector
```

Node: `GeometryNodeInputNamedAttribute` or `GeometryNodeInputUVMap`, whichever is available in the target Blender version.

Implementation detail:
- Verify the active Blender 5.x node identifier and output names before committing the method.
- Return UV as a `Vector` only if the node exposes a vector output. Otherwise return the correct socket wrapper.

Do not add `Mesh.uv_project(...)` in Phase 2. UV unwrapping/projection is not a simple geometry-node wrapper and would be misleading as an API promise.

## Deferred From Phase 2

- Generic geometry "mix" operation. `ShaderNodeMix` does not mix geometry streams. Use `join_geometry`, selections, delete, boolean, or switch-style nodes later.
- Full shader graph and material-node sockets.
- General attribute sampling.
- NURBS/spline manipulation.
- Animation/time-based effects.
- Per-instance random rotation unless the rotation socket type is represented cleanly.
- New module split. Revisit after Phase 2 lands and the method count becomes painful.

## Optional Stretch: Boolean Mesh Operations

The spec lists booleans for v0.2, but they are less critical than instancing and displacement. Add only if the core priorities are complete.

```python
def mesh_boolean(
    self,
    mesh: sockets.Geometry,
    cutter: sockets.Geometry,
    operation: str = "DIFFERENCE",
    solver: str = "EXACT",
) -> sockets.Geometry
```

Node: `GeometryNodeMeshBoolean`

Socket details:
- Link `mesh` to input `"Mesh 1"` or the active version's first mesh input.
- Link `cutter` to `"Mesh 2"` or the multi-input cutter socket.
- Validate operation: `"DIFFERENCE"`, `"UNION"`, `"INTERSECT"`.
- Return output `"Mesh"` as `Mesh` if Blender exposes a mesh output, otherwise `Geometry`.

## Testing

Add tests that run under Blender like the current `test_core.py`.

- `test_phase2_instance.py`: grid or ico sphere -> `points_on_faces(density=...)` -> `instance_on_points(cone)` -> `realize_instances()` -> `set_output(...)`.
- `test_phase2_deform.py`: `mesh_grid(vertices_x=64, vertices_y=64).subdivide(...).displace_noise(strength=0.25, noise_scale=2.5)` and verify every created node exists with expected links.
- `test_phase2_fields.py`: create `position`, `normal`, `noise`, `map_range`, `vector_scale`, and `set_position` in one tree.
- `test_phase2_delete_points.py`: `mesh_to_points(...)`, `delete_geometry(...)`, and `set_output(...)`.
- Keep render testing optional but include one smoke render for the success scene if runtime is acceptable.

For each test, assert:
- The returned object is the expected Arrival socket wrapper.
- The Blender node tree contains the intended node identifiers.
- Critical links target the expected socket names (`"Geometry"`, `"Mesh"`, `"Points"`, `"Instance"`, `"Scale"`, `"Offset"`).

## Success Criteria

An agent can build a crystal-cluster scene with:

```python
with NodeTreeBuilder("CrystalCluster") as tree:
    base = tree.mesh_ico_sphere(radius=2.0, subdivisions=3)
    base = base.displace_noise(strength=0.08, noise_scale=3.0)

    points = base.points_on_faces(density=12.0, seed=7)
    crystal = tree.mesh_cone(radius1=0.12, radius2=0.0, depth=0.9)
    instances = points.instance_on_points(crystal, scale=0.7)
    cluster = instances.realize_instances().set_material(dark_mirror())

    tree.set_output(cluster)
```

This exercises the Phase 2 priorities in order: deformation fields, surface point distribution, instancing, realizing instances, and material assignment, while staying consistent with the current Arrival API.
