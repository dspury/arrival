"""Socket classes for Arrival.

Socket classes wrap Blender's geometry node sockets. Each socket instance
holds a reference to a Blender socket and provides chainable methods for
creating and wiring nodes.
"""

import bpy
from typing import Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .nodes import NodeTreeBuilder


class Socket:
    """Base class for all socket types.
    
    A Socket wraps a Blender socket and its associated node.
    Subclasses are typed (Geometry, Float, Vector, etc.)
    and provide node-creation methods specific to that type.
    """
    
    # Override in subclasses
    socket_type: str = ""  # Blender socket type string, e.g. "NodeSocketGeometry"
    bl_idname: str = ""    # Blender node type, e.g. "GeometryNodeMeshLine"
    
    def __init__(self, node: 'NodeTreeBuilder', socket: bpy.types.NodeSocket, bl_node: bpy.types.Node):
        self._node = node
        self._socket = socket
        self._bl_node = bl_node
    
    def __repr__(self):
        return f"<{self.__class__.__name__} socket={self._socket!r} node={self._bl_node!r}>"
    
    @property
    def node(self) -> 'NodeTreeBuilder':
        """The node tree builder this socket belongs to."""
        return self._node
    
    @property
    def bl_socket(self) -> bpy.types.NodeSocket:
        """The underlying Blender socket."""
        return self._socket
    
    @property
    def bl_node(self) -> bpy.types.Node:
        """The underlying Blender node."""
        return self._bl_node
    
    @property
    def output_socket(self) -> bpy.types.NodeSocket:
        """The output socket on the underlying node (for linking)."""
        return self._socket


class Geometry(Socket):
    """Geometry socket — represents mesh, curve, or point geometry flowing through the tree."""
    
    socket_type = "NodeSocketGeometry"
    
    def transform(self, translation: Tuple[float, float, float] = (0, 0, 0),
                  rotation: Tuple[float, float, float] = (0, 0, 0),
                  scale: Tuple[float, float, float] = (1, 1, 1)) -> 'Geometry':
        """Apply transform to geometry. Returns new Geometry socket."""
        node = self._node
        bl_node = node._tree.nodes.new("GeometryNodeTransform")
        bl_node.location = (node._current_x, node._current_y)
        node._current_x += 300
        
        # Set transform inputs (Translation/Rotation/Scale are VECTOR = 3 floats)
        bl_node.inputs["Translation"].default_value = translation
        bl_node.inputs["Scale"].default_value = scale
        # Rotation is ROTATION type, leave at default for now
        
        # Link input geometry
        node._tree.links.new(self.output_socket, bl_node.inputs["Geometry"])
        
        # Return new socket on output
        new_socket = bl_node.outputs["Geometry"]
        return Geometry(node, new_socket, bl_node)
    
    def scale(self, factor: float = 1.0) -> 'Geometry':
        """Uniform scale. Pass a single float or (x, y, z) tuple for non-uniform."""
        if isinstance(factor, (int, float)):
            return self.transform(scale=(factor, factor, factor))
        return self.transform(scale=factor)
    
    def join(self, *others: 'Geometry') -> 'Geometry':
        """Join this geometry with other geometry inputs."""
        node = self._node
        bl_node = node._tree.nodes.new("GeometryNodeJoinGeometry")
        bl_node.location = (node._current_x, node._current_y)
        node._current_x += 300
        
        # Link this geometry
        bl_node.inputs["Geometry"].default_value = self.output_socket.default_value
        node._tree.links.new(self.output_socket, bl_node.inputs["Geometry"])
        
        # Link others
        for i, other in enumerate(others):
            if i == 0:
                bl_node.inputs["Geometry"].link_default_value = other.output_socket.default_value
            node._tree.links.new(other.output_socket, bl_node.inputs["Geometry"])
        
        new_socket = bl_node.outputs["Geometry"]
        return Geometry(node, new_socket, bl_node)
    
    def set_material(self, material) -> 'Geometry':
        """Set material on geometry."""
        node = self._node
        bl_node = node._tree.nodes.new("GeometryNodeSetMaterial")
        bl_node.location = (node._current_x, node._current_y)
        node._current_x += 300
        
        bl_node.inputs["Material"].default_value = material
        node._tree.links.new(self.output_socket, bl_node.inputs["Geometry"])
        
        new_socket = bl_node.outputs["Geometry"]
        return Geometry(node, new_socket, bl_node)


class Mesh(Geometry):
    """Mesh-specific geometry operations."""
    
    @staticmethod
    def cube(size: float = 1.0,
             location: Tuple[float, float, float] = (0, 0, 0)) -> 'Mesh':
        """Create a cube mesh primitive. Must be called on a NodeTreeBuilder context."""
        raise NotImplementedError("Mesh primitives must be created via NodeTreeBuilder.context()")
    
    @staticmethod
    def sphere(radius: float = 1.0,
               location: Tuple[float, float, float] = (0, 0, 0)) -> 'Mesh':
        """Create a UV sphere mesh primitive."""
        raise NotImplementedError("Mesh primitives must be created via NodeTreeBuilder.context()")
    
    @staticmethod
    def cylinder(radius: float = 1.0, depth: float = 2.0,
                 location: Tuple[float, float, float] = (0, 0, 0)) -> 'Mesh':
        """Create a cylinder mesh primitive."""
        raise NotImplementedError("Mesh primitives must be created via NodeTreeBuilder.context()")
    
    @staticmethod
    def cone(radius1: float = 1.0, radius2: float = 0.0, depth: float = 2.0,
             location: Tuple[float, float, float] = (0, 0, 0)) -> 'Mesh':
        """Create a cone mesh primitive."""
        raise NotImplementedError("Mesh primitives must be created via NodeTreeBuilder.context()")
    
    @staticmethod
    def grid(size_x: float = 2.0, size_y: float = 2.0,
             vertices_x: int = 10, vertices_y: int = 10,
             location: Tuple[float, float, float] = (0, 0, 0)) -> 'Mesh':
        """Create a grid mesh primitive."""
        raise NotImplementedError("Mesh primitives must be created via NodeTreeBuilder.context()")
    
    @staticmethod
    def line(count: int = 10,
             offset: Tuple[float, float, float] = (1, 0, 0),
             location: Tuple[float, float, float] = (0, 0, 0)) -> 'Mesh':
        """Create a line mesh primitive."""
        raise NotImplementedError("Mesh primitives must be created via NodeTreeBuilder.context()")
    
    @staticmethod
    def circle(vertices: int = 32, radius: float = 1.0,
               location: Tuple[float, float, float] = (0, 0, 0)) -> 'Mesh':
        """Create a circle mesh primitive."""
        raise NotImplementedError("Mesh primitives must be created via NodeTreeBuilder.context()")
    
    def subdivide(self, levels: int = 1) -> 'Mesh':
        """Subdivide mesh."""
        node = self._node
        bl_node = node._tree.nodes.new("GeometryNodeSubdivideMesh")
        bl_node.location = (node._current_x, node._current_y)
        node._current_x += 300
        
        bl_node.inputs["Level"].default_value = levels
        node._tree.links.new(self.output_socket, bl_node.inputs["Mesh"])
        
        new_socket = bl_node.outputs["Mesh"]
        return Mesh(node, new_socket, bl_node)
    
    def displace(self, strength: float = 0.1, noise_scale: float = 1.0) -> 'Mesh':
        """Displace mesh using noise. Requires subdivision for smooth results."""
        node = self._node
        
        # Add subdivision first for smooth displacement
        subdivided = self.subdivide(levels=3)
        
        # Add displacement modifier with noise
        bl_node = node._tree.nodes.new("GeometryNodeAttributeVectorMath")
        bl_node.location = (node._current_x, node._current_y)
        node._current_x += 300
        
        # Set operation to add
        bl_node.operation = 'ADD'
        
        # This is simplified — for full displacement we'd use displacement modifier
        # For now, just pass through
        node._tree.links.new(subdivided.output_socket, bl_node.inputs["Vector"])
        
        new_socket = bl_node.outputs["Vector"]
        return Mesh(node, new_socket, bl_node)


class Float(Socket):
    """Float/value socket."""
    
    socket_type = "NodeSocketFloat"
    
    @staticmethod
    def constant(value: float) -> 'Float':
        """Create a constant float value."""
        raise NotImplementedError("Float constants must be created via NodeTreeBuilder.context()")


class Vector(Socket):
    """3D vector socket."""
    
    socket_type = "NodeSocketVector"
    
    @staticmethod
    def constant(x: float = 0.0, y: float = 0.0, z: float = 0.0) -> 'Vector':
        """Create a constant vector."""
        raise NotImplementedError("Vector constants must be created via NodeTreeBuilder.context()")


class Color(Socket):
    """RGBA color socket."""
    
    socket_type = "NodeSocketColor"
    
    @staticmethod
    def rgba(r: float = 1.0, g: float = 1.0, b: float = 1.0, a: float = 1.0) -> 'Color':
        """Create a constant color."""
        raise NotImplementedError("Color constants must be created via NodeTreeBuilder.context()")


class Integer(Socket):
    """Integer socket."""
    
    socket_type = "NodeSocketInt"
    
    @staticmethod
    def constant(value: int) -> 'Integer':
        """Create a constant integer."""
        raise NotImplementedError("Integer constants must be created via NodeTreeBuilder.context()")


class Boolean(Socket):
    """Boolean socket."""
    
    socket_type = "NodeSocketBool"
    
    @staticmethod
    def constant(value: bool) -> 'Boolean':
        """Create a constant boolean."""
        raise NotImplementedError("Boolean constants must be created via NodeTreeBuilder.context()")
