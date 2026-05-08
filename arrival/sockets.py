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
    def _node(self) -> 'NodeTreeBuilder':
        """The node tree builder this socket belongs to (internal)."""
        return self._node
    
    @property
    def _bl_socket(self) -> bpy.types.NodeSocket:
        """The underlying Blender socket (internal)."""
        return self._socket
    
    @property
    def _bl_node(self) -> bpy.types.Node:
        """The underlying Blender node (internal)."""
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
        bl_node = node._create_node("GeometryNodeTransform")
        
        # Set transform inputs (Translation/Rotation/Scale are VECTOR = 3 floats)
        node._set_or_link(bl_node.inputs["Translation"], translation)
        if "Rotation" in bl_node.inputs:
            node._set_or_link(bl_node.inputs["Rotation"], rotation)
        node._set_or_link(bl_node.inputs["Scale"], scale)
        
        # Link input geometry
        node._link(self, bl_node.inputs["Geometry"])
        
        # Return new socket on output
        new_socket = bl_node.outputs["Geometry"]
        return self.__class__(node, new_socket, bl_node)
    
    def scale(self, factor: float = 1.0) -> 'Geometry':
        """Uniform scale. Pass a single float or (x, y, z) tuple for non-uniform."""
        if isinstance(factor, (int, float)):
            return self.transform(scale=(factor, factor, factor))
        return self.transform(scale=factor)
    
    def join(self, *others: 'Geometry') -> 'Geometry':
        """Join this geometry with other geometry inputs."""
        node = self._node
        return node.join_geometry(self, *others)
    
    def set_material(self, material) -> 'Geometry':
        """Set material on geometry."""
        node = self._node
        return node.set_material(self, material)

    def points_on_faces(self, density=1.0, seed=0, selection=True) -> 'Geometry':
        """Distribute points on this geometry's faces."""
        return self._node.points_on_faces(self, density=density, seed=seed, selection=selection)

    def instance_on_points(self, instance, rotation=None, scale=1.0,
                           pick_instance=False, instance_index=0) -> 'Geometry':
        """Instance geometry on this point geometry."""
        return self._node.instance_on_points(
            self,
            instance,
            rotation=rotation,
            scale=scale,
            pick_instance=pick_instance,
            instance_index=instance_index,
        )

    def realize_instances(self) -> 'Geometry':
        """Realize this instance geometry."""
        return self._node.realize_instances(self)

    def set_position(self, position=None, offset=None, selection=True) -> 'Geometry':
        """Set positions on this geometry."""
        return self._node.set_position(self, position=position, offset=offset, selection=selection)

    def displace_noise(self, strength=0.1, noise_scale=1.0, detail=8.0,
                       along_normal=True) -> 'Geometry':
        """Displace this geometry with a noise field."""
        return self._node.displace_noise(
            self,
            strength=strength,
            noise_scale=noise_scale,
            detail=detail,
            along_normal=along_normal,
        )

    def delete(self, selection=True, domain="FACE", mode="ALL") -> 'Geometry':
        """Delete selected geometry elements."""
        return self._node.delete_geometry(self, selection=selection, domain=domain, mode=mode)

    def to_points(self, mode="VERTICES", radius=0.05) -> 'Geometry':
        """Convert this mesh geometry to points."""
        return self._node.mesh_to_points(self, mode=mode, radius=radius)

    def to_usd(self, output_path: str) -> str:
        """Export this geometry to USD format.
        
        Args:
            output_path: Path to save the USD file (.usda, .usdc, or .usdz)
        
        Returns:
            Path to the exported USD file
        
        Raises:
            RuntimeError: If USD export fails
        
        Example:
            >>> with NodeTreeBuilder("ExportTest") as tree:
            ...     cube = tree.mesh_cube(size=2.0)
            ...     path = cube.to_usd("/tmp/my_cube.usda")
            >>> print(f"Exported to: {path}")
        """
        return self._node.export_usd(self, output_path)


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
        bl_node = node._create_node("GeometryNodeSubdivideMesh")
        
        node._set_or_link(bl_node.inputs["Level"], levels)
        node._link(self, bl_node.inputs["Mesh"])
        
        new_socket = bl_node.outputs["Mesh"]
        return Mesh(node, new_socket, bl_node)
    
    def displace(self, strength: float = 0.1, noise_scale: float = 1.0) -> 'Mesh':
        """Displace mesh using noise. Requires subdivision for smooth results."""
        return self.displace_noise(strength=strength, noise_scale=noise_scale)


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
