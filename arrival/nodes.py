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
        return sockets.Mesh(self, bl_node.outputs["Mesh"], bl_node)
    
    def mesh_sphere(self, radius: float = 1.0,
                    location: Tuple[float, float, float] = (0, 0, 0)) -> sockets.Mesh:
        """Create a UV sphere mesh primitive."""
        bl_node = self._create_node("GeometryNodeMeshUVSphere")
        bl_node.inputs["Radius"].default_value = radius
        return sockets.Mesh(self, bl_node.outputs["Mesh"], bl_node)
    
    def mesh_ico_sphere(self, radius: float = 1.0, subdivisions: int = 2,
                         location: Tuple[float, float, float] = (0, 0, 0)) -> sockets.Mesh:
        """Create an ico sphere mesh primitive."""
        bl_node = self._create_node("GeometryNodeMeshIcoSphere")
        bl_node.inputs["Radius"].default_value = radius
        bl_node.inputs["Subdivisions"].default_value = subdivisions
        return sockets.Mesh(self, bl_node.outputs["Mesh"], bl_node)
    
    def mesh_cylinder(self, radius: float = 1.0, depth: float = 2.0,
                       location: Tuple[float, float, float] = (0, 0, 0)) -> sockets.Mesh:
        """Create a cylinder mesh primitive."""
        bl_node = self._create_node("GeometryNodeMeshCylinder")
        bl_node.inputs["Radius"].default_value = radius
        bl_node.inputs["Depth"].default_value = depth
        return sockets.Mesh(self, bl_node.outputs["Mesh"], bl_node)
    
    def mesh_cone(self, radius1: float = 1.0, radius2: float = 0.0, depth: float = 2.0,
                   location: Tuple[float, float, float] = (0, 0, 0)) -> sockets.Mesh:
        """Create a cone mesh primitive."""
        bl_node = self._create_node("GeometryNodeMeshCone")
        bl_node.inputs["Radius Top"].default_value = radius2
        bl_node.inputs["Radius Bottom"].default_value = radius1
        bl_node.inputs["Depth"].default_value = depth
        return sockets.Mesh(self, bl_node.outputs["Mesh"], bl_node)
    
    def mesh_grid(self, size_x: float = 2.0, size_y: float = 2.0,
                   vertices_x: int = 10, vertices_y: int = 10,
                   location: Tuple[float, float, float] = (0, 0, 0)) -> sockets.Mesh:
        """Create a grid mesh primitive."""
        bl_node = self._create_node("GeometryNodeMeshGrid")
        bl_node.inputs["Size X"].default_value = size_x
        bl_node.inputs["Size Y"].default_value = size_y
        bl_node.inputs["Vertices X"].default_value = vertices_x
        bl_node.inputs["Vertices Y"].default_value = vertices_y
        return sockets.Mesh(self, bl_node.outputs["Mesh"], bl_node)
    
    def mesh_line(self, count: int = 10,
                   offset: Tuple[float, float, float] = (1, 0, 0),
                   location: Tuple[float, float, float] = (0, 0, 0)) -> sockets.Mesh:
        """Create a line mesh primitive."""
        bl_node = self._create_node("GeometryNodeMeshLine")
        bl_node.inputs["Count"].default_value = count
        bl_node.inputs["Offset"].default_value = offset
        return sockets.Mesh(self, bl_node.outputs["Mesh"], bl_node)
    
    def mesh_circle(self, vertices: int = 32, radius: float = 1.0,
                     location: Tuple[float, float, float] = (0, 0, 0)) -> sockets.Mesh:
        """Create a circle mesh primitive."""
        bl_node = self._create_node("GeometryNodeMeshCircle")
        bl_node.inputs["Vertices"].default_value = vertices
        bl_node.inputs["Radius"].default_value = radius
        return sockets.Mesh(self, bl_node.outputs["Mesh"], bl_node)
    
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
        for i, geo in enumerate(geometries):
            if i == 0:
                bl_node.inputs["Geometry"].default_value = geo.output_socket.default_value
            self._tree.links.new(geo.output_socket, bl_node.inputs["Geometry"])
        return sockets.Geometry(self, bl_node.outputs["Geometry"], bl_node)
    
    def set_material(self, geometry: sockets.Geometry, material) -> sockets.Geometry:
        """Set material on geometry."""
        bl_node = self._create_node("GeometryNodeSetMaterial")
        bl_node.inputs["Material"].default_value = material
        self._tree.links.new(geometry.output_socket, bl_node.inputs["Geometry"])
        return sockets.Geometry(self, bl_node.outputs["Geometry"], bl_node)
    
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
