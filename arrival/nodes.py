"""Node tree builder for Arrival.

The NodeTreeBuilder manages the geometry node tree context, creating nodes,
wiring them together, and tracking the current position for node layout.
"""

import bpy
from typing import Tuple, Optional
from . import sockets


class NodeTreeBuilder:
    """Builds geometry node trees in Blender.
    
    This class manages the active node tree, tracks node positions for
    automatic layout, and provides methods for creating primitives and
    wiring nodes.
    
    Usage:
        with NodeTreeBuilder("MyTree") as tree:
            mesh = tree.mesh_cube(location=(0, 0, 0))
            mesh = mesh.transform(translation=(0, 0, 1))
    """
    
    def __init__(self, name: str = "ArrivalNodes"):
        self.name = name
        self._tree: Optional[bpy.types.GeometryNodeTree] = None
        self._group_input: Optional[bpy.types.Node] = None
        self._group_output: Optional[bpy.types.Node] = None
        self._current_x: float = 0
        self._current_y: float = 0
        
    def __enter__(self):
        """Create the node tree and enter context."""
        # Create the node group
        self._tree = bpy.data.node_groups.new(self.name, "GeometryNodeTree")
        
        # CRITICAL: Define interface sockets FIRST
        # This creates the actual sockets on GroupInput/GroupOutput
        self._tree.interface.new_socket(
            "Geometry", in_out='INPUT', socket_type='NodeSocketGeometry'
        )
        self._tree.interface.new_socket(
            "Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry'
        )
        
        # Now add GroupInput and GroupOutput nodes
        # Their sockets now exist because we defined the interface
        self._group_input = self._tree.nodes.new("NodeGroupInput")
        self._group_input.location = (-600, 0)
        
        self._group_output = self._tree.nodes.new("NodeGroupOutput")
        self._group_output.location = (600, 0)
        
        # Initialize layout position
        self._current_x = -300
        self._current_y = 0
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and wire group input/output."""
        if exc_type is None:
            # Wire group input to first node, last node to group output
            # This is done by the user via tree.links or by the final socket
            pass
        return False
    
    @property
    def tree(self) -> bpy.types.GeometryNodeTree:
        """The underlying Blender node tree."""
        if self._tree is None:
            raise RuntimeError("NodeTreeBuilder must be used as context manager")
        return self._tree
    
    def _create_node(self, node_type: str, location: Tuple[float, float] = None) -> bpy.types.Node:
        """Create a geometry node of the given type."""
        bl_node = self._tree.nodes.new(node_type)
        if location:
            bl_node.location = location
        else:
            bl_node.location = (self._current_x, self._current_y)
            self._current_x += 300
        return bl_node

    def _link(self, source: sockets.Socket, target: bpy.types.NodeSocket) -> None:
        """Link an Arrival socket to a Blender input socket."""
        self._tree.links.new(source.output_socket, target)

    def _set_or_link(self, target: bpy.types.NodeSocket, value) -> None:
        """Assign a literal default value or link an Arrival socket."""
        if isinstance(value, sockets.Socket):
            self._link(value, target)
        else:
            try:
                target.default_value = value
            except TypeError:
                if target.bl_socket_idname == "NodeSocketRotation":
                    from mathutils import Euler
                    target.default_value = Euler(value, 'XYZ')
                else:
                    raise

    def _socket(self, cls, bl_node: bpy.types.Node, output_name: str):
        """Wrap a Blender node output in an Arrival socket class."""
        return cls(self, bl_node.outputs[output_name], bl_node)

    def _input(self, bl_node: bpy.types.Node, *names: str):
        """Return the first available input by name."""
        for name in names:
            if name in bl_node.inputs:
                return bl_node.inputs[name]
        raise KeyError(f"None of the inputs exist on {bl_node.bl_idname}: {names}")

    def _output(self, bl_node: bpy.types.Node, *names: str):
        """Return the first available output by name."""
        for name in names:
            if name in bl_node.outputs:
                return bl_node.outputs[name]
        raise KeyError(f"None of the outputs exist on {bl_node.bl_idname}: {names}")

    def _set_enum(self, bl_node: bpy.types.Node, attr: str, value: str, allowed: set[str]) -> None:
        """Validate and set an enum-like node attribute when available."""
        if value not in allowed:
            raise ValueError(f"{attr} must be one of {sorted(allowed)}, got {value!r}")
        if hasattr(bl_node, attr):
            try:
                setattr(bl_node, attr, value)
            except TypeError as exc:
                raise ValueError(f"{value!r} is not valid for {bl_node.bl_idname}.{attr}") from exc

    def _with_location(self, mesh: sockets.Mesh, location: Tuple[float, float, float]) -> sockets.Mesh:
        """Apply primitive location using a Transform node when non-zero."""
        if tuple(location) == (0, 0, 0):
            return mesh
        return mesh.transform(translation=location)
    
    def _next_y(self):
        """Move to next row for layout."""
        self._current_y -= 100
        self._current_x = -300
    
    # ─────────────────────────────────────────────────────────────────
    # Mesh Primitives
    # ─────────────────────────────────────────────────────────────────
    
    def mesh_cube(self, size: float = 1.0,
                  location: Tuple[float, float, float] = (0, 0, 0)) -> sockets.Mesh:
        """Create a cube mesh primitive."""
        bl_node = self._create_node("GeometryNodeMeshCube")
        bl_node.inputs["Size"].default_value = (size, size, size)
        return self._with_location(self._socket(sockets.Mesh, bl_node, "Mesh"), location)
    
    def mesh_sphere(self, radius: float = 1.0,
                    location: Tuple[float, float, float] = (0, 0, 0)) -> sockets.Mesh:
        """Create a UV sphere mesh primitive."""
        bl_node = self._create_node("GeometryNodeMeshUVSphere")
        bl_node.inputs["Radius"].default_value = radius
        return self._with_location(self._socket(sockets.Mesh, bl_node, "Mesh"), location)
    
    def mesh_ico_sphere(self, radius: float = 1.0, subdivisions: int = 2,
                         location: Tuple[float, float, float] = (0, 0, 0)) -> sockets.Mesh:
        """Create an ico sphere mesh primitive."""
        bl_node = self._create_node("GeometryNodeMeshIcoSphere")
        bl_node.inputs["Radius"].default_value = radius
        bl_node.inputs["Subdivisions"].default_value = subdivisions
        return self._with_location(self._socket(sockets.Mesh, bl_node, "Mesh"), location)
    
    def mesh_cylinder(self, radius: float = 1.0, depth: float = 2.0,
                       location: Tuple[float, float, float] = (0, 0, 0)) -> sockets.Mesh:
        """Create a cylinder mesh primitive."""
        bl_node = self._create_node("GeometryNodeMeshCylinder")
        bl_node.inputs["Radius"].default_value = radius
        bl_node.inputs["Depth"].default_value = depth
        return self._with_location(self._socket(sockets.Mesh, bl_node, "Mesh"), location)
    
    def mesh_cone(self, radius1: float = 1.0, radius2: float = 0.0, depth: float = 2.0,
                   location: Tuple[float, float, float] = (0, 0, 0)) -> sockets.Mesh:
        """Create a cone mesh primitive."""
        bl_node = self._create_node("GeometryNodeMeshCone")
        bl_node.inputs["Radius Top"].default_value = radius2
        bl_node.inputs["Radius Bottom"].default_value = radius1
        bl_node.inputs["Depth"].default_value = depth
        return self._with_location(self._socket(sockets.Mesh, bl_node, "Mesh"), location)
    
    def mesh_grid(self, size_x: float = 2.0, size_y: float = 2.0,
                   vertices_x: int = 10, vertices_y: int = 10,
                   location: Tuple[float, float, float] = (0, 0, 0)) -> sockets.Mesh:
        """Create a grid mesh primitive."""
        bl_node = self._create_node("GeometryNodeMeshGrid")
        bl_node.inputs["Size X"].default_value = size_x
        bl_node.inputs["Size Y"].default_value = size_y
        bl_node.inputs["Vertices X"].default_value = vertices_x
        bl_node.inputs["Vertices Y"].default_value = vertices_y
        return self._with_location(self._socket(sockets.Mesh, bl_node, "Mesh"), location)
    
    def mesh_line(self, count: int = 10,
                   offset: Tuple[float, float, float] = (1, 0, 0),
                   location: Tuple[float, float, float] = (0, 0, 0)) -> sockets.Mesh:
        """Create a line mesh primitive."""
        bl_node = self._create_node("GeometryNodeMeshLine")
        bl_node.inputs["Count"].default_value = count
        bl_node.inputs["Offset"].default_value = offset
        return self._with_location(self._socket(sockets.Mesh, bl_node, "Mesh"), location)
    
    def mesh_circle(self, vertices: int = 32, radius: float = 1.0,
                     location: Tuple[float, float, float] = (0, 0, 0)) -> sockets.Mesh:
        """Create a circle mesh primitive."""
        bl_node = self._create_node("GeometryNodeMeshCircle")
        bl_node.inputs["Vertices"].default_value = vertices
        bl_node.inputs["Radius"].default_value = radius
        return self._with_location(self._socket(sockets.Mesh, bl_node, "Mesh"), location)
    
    # ─────────────────────────────────────────────────────────────────
    # Curve Primitives
    # ─────────────────────────────────────────────────────────────────
    
    def curve_bezier(self, resolution: int = 12) -> sockets.Geometry:
        """Create a bezier curve primitive."""
        bl_node = self._create_node("GeometryNodeCurvePrimitiveBezierSegment")
        bl_node.inputs["Resolution"].default_value = resolution
        return sockets.Geometry(self, bl_node.outputs["Curve"], bl_node)
    
    # ─────────────────────────────────────────────────────────────────
    # Constants
    # ─────────────────────────────────────────────────────────────────
    
    def float_constant(self, value: float) -> sockets.Float:
        """Create a constant float value node."""
        bl_node = self._create_node("ShaderNodeValue")
        bl_node.outputs[0].default_value = value
        return sockets.Float(self, bl_node.outputs[0], bl_node)
    
    def vector_constant(self, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> sockets.Vector:
        """Create a constant vector value node using VectorMath."""
        bl_node = self._create_node("ShaderNodeVectorMath")
        bl_node.operation = 'ADD'
        bl_node.inputs[0].default_value = (x, y, z)
        bl_node.inputs[1].default_value = (0, 0, 0)
        return sockets.Vector(self, bl_node.outputs["Vector"], bl_node)
    
    def color_constant(self, r: float = 1.0, g: float = 1.0, b: float = 1.0, a: float = 1.0) -> sockets.Color:
        """Create a constant color value node."""
        bl_node = self._create_node("FunctionNodeInputColor")
        bl_node.outputs[0].default_value = (r, g, b, a)
        return sockets.Color(self, bl_node.outputs[0], bl_node)
    
    # ─────────────────────────────────────────────────────────────────
    # Noise & Random
    # ─────────────────────────────────────────────────────────────────
    
    def noise(self, scale: float = 1.0, detail: float = 1.0) -> sockets.Float:
        """Create a noise texture node."""
        bl_node = self._create_node("ShaderNodeTexNoise")
        bl_node.inputs["Scale"].default_value = scale
        bl_node.inputs["Detail"].default_value = detail
        return sockets.Float(self, bl_node.outputs["Fac"], bl_node)
    
    def voronoi(self, scale: float = 1.0) -> sockets.Float:
        """Create a voronoi texture node."""
        bl_node = self._create_node("ShaderNodeTexVoronoi")
        bl_node.inputs["Scale"].default_value = scale
        return sockets.Float(self, bl_node.outputs["Distance"], bl_node)
    
    def random_float(self, min_val: float = 0.0, max_val: float = 1.0) -> sockets.Float:
        """Create a random value node."""
        bl_node = self._create_node("FunctionNodeRandomValue")
        bl_node.inputs["Min"].default_value = min_val
        bl_node.inputs["Max"].default_value = max_val
        return sockets.Float(self, bl_node.outputs[1], bl_node)
    
    # ─────────────────────────────────────────────────────────────────
    # Operations
    # ─────────────────────────────────────────────────────────────────
    
    def join_geometry(self, *geometries: sockets.Geometry) -> sockets.Geometry:
        """Join multiple geometry streams into one."""
        bl_node = self._create_node("GeometryNodeJoinGeometry")
        for geo in geometries:
            self._link(geo, bl_node.inputs["Geometry"])
        return self._socket(sockets.Geometry, bl_node, "Geometry")
    
    def set_material(self, geometry: sockets.Geometry, material) -> sockets.Geometry:
        """Set material on geometry."""
        bl_node = self._create_node("GeometryNodeSetMaterial")
        bl_node.inputs["Material"].default_value = material
        self._link(geometry, bl_node.inputs["Geometry"])
        return self._socket(sockets.Geometry, bl_node, "Geometry")

    def distribute_points_on_faces(
        self,
        geometry: sockets.Geometry,
        density: float | sockets.Float = 1.0,
        seed: int = 0,
        selection: bool | sockets.Boolean = True,
    ) -> sockets.Geometry:
        """Distribute points across mesh faces."""
        bl_node = self._create_node("GeometryNodeDistributePointsOnFaces")
        self._link(geometry, self._input(bl_node, "Mesh", "Geometry"))
        self._set_or_link(self._input(bl_node, "Density"), density)
        if "Selection" in bl_node.inputs:
            self._set_or_link(bl_node.inputs["Selection"], selection)
        if "Seed" in bl_node.inputs:
            bl_node.inputs["Seed"].default_value = seed
        return sockets.Geometry(self, self._output(bl_node, "Points"), bl_node)

    def points_on_faces(self, geometry, density=1.0, seed=0, selection=True) -> sockets.Geometry:
        """Alias for distribute_points_on_faces."""
        return self.distribute_points_on_faces(geometry, density=density, seed=seed, selection=selection)

    def instance_on_points(
        self,
        points: sockets.Geometry,
        instance: sockets.Geometry,
        rotation: tuple[float, float, float] | sockets.Vector | None = None,
        scale: float | tuple[float, float, float] | sockets.Vector = 1.0,
        pick_instance: bool | sockets.Boolean = False,
        instance_index: int | sockets.Integer = 0,
    ) -> sockets.Geometry:
        """Instance geometry on point geometry."""
        bl_node = self._create_node("GeometryNodeInstanceOnPoints")
        self._link(points, self._input(bl_node, "Points"))
        self._link(instance, self._input(bl_node, "Instance"))
        if isinstance(scale, (int, float)):
            scale = (scale, scale, scale)
        self._set_or_link(self._input(bl_node, "Scale"), scale)
        if rotation is not None and "Rotation" in bl_node.inputs:
            self._set_or_link(bl_node.inputs["Rotation"], rotation)
        if "Pick Instance" in bl_node.inputs:
            self._set_or_link(bl_node.inputs["Pick Instance"], pick_instance)
        if "Instance Index" in bl_node.inputs:
            self._set_or_link(bl_node.inputs["Instance Index"], instance_index)
        return sockets.Geometry(self, self._output(bl_node, "Instances"), bl_node)

    def realize_instances(self, geometry: sockets.Geometry) -> sockets.Geometry:
        """Realize instances into concrete geometry."""
        bl_node = self._create_node("GeometryNodeRealizeInstances")
        self._link(geometry, self._input(bl_node, "Geometry"))
        return self._socket(sockets.Geometry, bl_node, "Geometry")

    def position(self) -> sockets.Vector:
        """Current point position field."""
        bl_node = self._create_node("GeometryNodeInputPosition")
        return self._socket(sockets.Vector, bl_node, "Position")

    def normal(self) -> sockets.Vector:
        """Current surface normal field."""
        bl_node = self._create_node("GeometryNodeInputNormal")
        return self._socket(sockets.Vector, bl_node, "Normal")

    def index(self) -> sockets.Integer:
        """Current element index field."""
        bl_node = self._create_node("GeometryNodeInputIndex")
        return self._socket(sockets.Integer, bl_node, "Index")

    def vector_add(self, a: sockets.Vector | tuple, b: sockets.Vector | tuple) -> sockets.Vector:
        """Add two vectors."""
        bl_node = self._create_node("ShaderNodeVectorMath")
        bl_node.operation = 'ADD'
        self._set_or_link(bl_node.inputs[0], a)
        self._set_or_link(bl_node.inputs[1], b)
        return self._socket(sockets.Vector, bl_node, "Vector")

    def vector_subtract(self, a: sockets.Vector | tuple, b: sockets.Vector | tuple) -> sockets.Vector:
        """Subtract vector b from vector a."""
        bl_node = self._create_node("ShaderNodeVectorMath")
        bl_node.operation = 'SUBTRACT'
        self._set_or_link(bl_node.inputs[0], a)
        self._set_or_link(bl_node.inputs[1], b)
        return self._socket(sockets.Vector, bl_node, "Vector")

    def vector_scale(self, vector: sockets.Vector | tuple, scale: sockets.Float | float) -> sockets.Vector:
        """Scale a vector by a scalar."""
        bl_node = self._create_node("ShaderNodeVectorMath")
        bl_node.operation = 'SCALE'
        self._set_or_link(bl_node.inputs[0], vector)
        target = bl_node.inputs["Scale"] if "Scale" in bl_node.inputs else bl_node.inputs[3]
        self._set_or_link(target, scale)
        return self._socket(sockets.Vector, bl_node, "Vector")

    def float_add(self, a: sockets.Float | float, b: sockets.Float | float) -> sockets.Float:
        """Add two float values."""
        bl_node = self._create_node("ShaderNodeMath")
        bl_node.operation = 'ADD'
        self._set_or_link(bl_node.inputs[0], a)
        self._set_or_link(bl_node.inputs[1], b)
        return self._socket(sockets.Float, bl_node, "Value")

    def float_multiply(self, a: sockets.Float | float, b: sockets.Float | float) -> sockets.Float:
        """Multiply two float values."""
        bl_node = self._create_node("ShaderNodeMath")
        bl_node.operation = 'MULTIPLY'
        self._set_or_link(bl_node.inputs[0], a)
        self._set_or_link(bl_node.inputs[1], b)
        return self._socket(sockets.Float, bl_node, "Value")

    def map_range(
        self,
        value: sockets.Float | float,
        from_min: float = 0.0,
        from_max: float = 1.0,
        to_min: float = 0.0,
        to_max: float = 1.0,
        clamp: bool = True,
    ) -> sockets.Float:
        """Remap a float value from one range to another."""
        bl_node = self._create_node("ShaderNodeMapRange")
        if hasattr(bl_node, "clamp"):
            bl_node.clamp = clamp
        self._set_or_link(self._input(bl_node, "Value"), value)
        self._set_or_link(self._input(bl_node, "From Min"), from_min)
        self._set_or_link(self._input(bl_node, "From Max"), from_max)
        self._set_or_link(self._input(bl_node, "To Min"), to_min)
        self._set_or_link(self._input(bl_node, "To Max"), to_max)
        return self._socket(sockets.Float, bl_node, "Result")

    def random_vector(
        self,
        min_val: tuple[float, float, float] = (0.0, 0.0, 0.0),
        max_val: tuple[float, float, float] = (1.0, 1.0, 1.0),
        seed: int = 0,
    ) -> sockets.Vector:
        """Create a random vector field."""
        bl_node = self._create_node("FunctionNodeRandomValue")
        if hasattr(bl_node, "data_type"):
            try:
                bl_node.data_type = 'FLOAT_VECTOR'
            except TypeError:
                pass
        self._set_or_link(self._input(bl_node, "Min"), min_val)
        self._set_or_link(self._input(bl_node, "Max"), max_val)
        if "Seed" in bl_node.inputs:
            bl_node.inputs["Seed"].default_value = seed
        return sockets.Vector(self, self._output(bl_node, "Vector", "Value"), bl_node)

    def set_position(
        self,
        geometry: sockets.Geometry,
        position: sockets.Vector | tuple | None = None,
        offset: sockets.Vector | tuple | None = None,
        selection: sockets.Boolean | bool = True,
    ) -> sockets.Geometry:
        """Set geometry positions by absolute position and/or offset field."""
        bl_node = self._create_node("GeometryNodeSetPosition")
        self._link(geometry, self._input(bl_node, "Geometry"))
        self._set_or_link(self._input(bl_node, "Selection"), selection)
        if position is not None:
            self._set_or_link(self._input(bl_node, "Position"), position)
        if offset is not None:
            self._set_or_link(self._input(bl_node, "Offset"), offset)
        return self._socket(sockets.Geometry, bl_node, "Geometry")

    def displace_noise(
        self,
        geometry: sockets.Geometry,
        strength: float | sockets.Float = 0.1,
        noise_scale: float = 1.0,
        detail: float = 8.0,
        along_normal: bool = True,
    ) -> sockets.Geometry:
        """Displace geometry with a noise field."""
        noise = self.noise(scale=noise_scale, detail=detail)
        min_strength = self.float_multiply(strength, -1.0) if isinstance(strength, sockets.Socket) else -strength
        remapped = self.map_range(noise, from_min=0.0, from_max=1.0, to_min=min_strength, to_max=strength)
        if along_normal:
            offset = self.vector_scale(self.normal(), remapped)
        else:
            offset = self.vector_scale((0.0, 0.0, 1.0), remapped)
        return self.set_position(geometry, offset=offset)

    def delete_geometry(
        self,
        geometry: sockets.Geometry,
        selection: sockets.Boolean | bool = True,
        domain: str = "FACE",
        mode: str = "ALL",
    ) -> sockets.Geometry:
        """Delete selected geometry elements."""
        bl_node = self._create_node("GeometryNodeDeleteGeometry")
        self._link(geometry, self._input(bl_node, "Geometry"))
        self._set_or_link(self._input(bl_node, "Selection"), selection)
        self._set_enum(bl_node, "domain", domain, {"POINT", "EDGE", "FACE", "CURVE", "INSTANCE"})
        self._set_enum(bl_node, "mode", mode, {"ALL", "EDGE_FACE", "ONLY_FACE"})
        return self._socket(sockets.Geometry, bl_node, "Geometry")

    def mesh_to_points(
        self,
        mesh: sockets.Geometry,
        mode: str = "VERTICES",
        radius: float | sockets.Float = 0.05,
    ) -> sockets.Geometry:
        """Convert mesh elements to point geometry."""
        bl_node = self._create_node("GeometryNodeMeshToPoints")
        self._set_enum(bl_node, "mode", mode, {"VERTICES", "EDGES", "FACES", "CORNERS"})
        self._link(mesh, self._input(bl_node, "Mesh"))
        self._set_or_link(self._input(bl_node, "Radius"), radius)
        return sockets.Geometry(self, self._output(bl_node, "Points"), bl_node)

    def store_named_attribute(
        self,
        geometry: sockets.Geometry,
        name: str,
        value: sockets.Float | sockets.Vector | sockets.Color | bool | float | tuple,
        data_type: str,
        domain: str = "POINT",
        selection: sockets.Boolean | bool = True,
    ) -> sockets.Geometry:
        """Store a field as a named attribute."""
        bl_node = self._create_node("GeometryNodeStoreNamedAttribute")
        self._link(geometry, self._input(bl_node, "Geometry"))
        self._set_or_link(self._input(bl_node, "Selection"), selection)
        self._set_or_link(self._input(bl_node, "Name"), name)
        self._set_enum(bl_node, "data_type", data_type, {"FLOAT", "INT", "FLOAT_VECTOR", "FLOAT_COLOR", "BOOLEAN", "QUATERNION", "FLOAT4X4"})
        self._set_enum(bl_node, "domain", domain, {"POINT", "EDGE", "FACE", "CORNER", "CURVE", "INSTANCE"})
        value_input = self._input(bl_node, "Value")
        self._set_or_link(value_input, value)
        return self._socket(sockets.Geometry, bl_node, "Geometry")

    def uv_map(self, name: str = "UVMap") -> sockets.Vector:
        """Read a named UV map as a vector field."""
        try:
            bl_node = self._create_node("GeometryNodeInputUVMap")
            if "UV Map" in bl_node.inputs:
                self._set_or_link(bl_node.inputs["UV Map"], name)
            elif "Name" in bl_node.inputs:
                self._set_or_link(bl_node.inputs["Name"], name)
            return sockets.Vector(self, self._output(bl_node, "UV", "Vector", "Attribute"), bl_node)
        except (RuntimeError, TypeError, ValueError):
            bl_node = self._create_node("GeometryNodeInputNamedAttribute")
            if hasattr(bl_node, "data_type"):
                try:
                    bl_node.data_type = 'FLOAT_VECTOR'
                except TypeError:
                    pass
            self._set_or_link(self._input(bl_node, "Name"), name)
            return sockets.Vector(self, self._output(bl_node, "Attribute", "Vector"), bl_node)
    
    # ─────────────────────────────────────────────────────────────────
    # Group I/O
    # ─────────────────────────────────────────────────────────────────
    
    def set_output(self, geometry: sockets.Geometry):
        """Wire geometry to the group output."""
        self._tree.links.new(geometry.output_socket, self._group_output.inputs["Geometry"])
    
    def get_input(self) -> sockets.Geometry:
        """Get the group input geometry socket."""
        return sockets.Geometry(self, self._group_input.outputs["Geometry"], self._group_input)
    
    # ─────────────────────────────────────────────────────────────────
    # Apply to object
    # ─────────────────────────────────────────────────────────────────
    
    def apply_to_object(self, obj: bpy.types.Object):
        """Apply this node tree to an object via modifier."""
        if obj.type not in ('MESH', 'CURVE', 'SURFACE', 'FONT', 'VOLUME', 'POINTCLOUD'):
            raise ValueError(f"Cannot apply geometry nodes to object type: {obj.type}")
        
        mod = obj.modifiers.new(name="GeometryNodes", type='NODES')
        mod.node_group = self._tree
        return mod


def new_tree(name: str = "ArrivalNodes") -> NodeTreeBuilder:
    """Create a new geometry node tree builder."""
    return NodeTreeBuilder(name)
