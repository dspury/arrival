"""Arrival — agent-native 3D geometry library wrapping Blender's bpy."""

from .sockets import Geometry, Mesh, Float, Vector, Color, Integer, Boolean
from .materials import Material
from .scene import Scene, describe, show

__all__ = [
    "Geometry",
    "Mesh",
    "Float",
    "Vector",
    "Color",
    "Integer",
    "Boolean",
    "Material",
    "Scene",
    "describe",
    "show",
    "export_usd",
]

__version__ = "0.2.0"


def export_usd(geometry, output_path: str) -> str:
    """Export geometry to USD format.

    This is the module-level convenience function for USD export.
    Works with any Geometry or Mesh socket from NodeTreeBuilder.

    Args:
        geometry: A Geometry or Mesh socket wrapper
        output_path: Path to save the USD file (.usda, .usdc, or .usdz)

    Returns:
        Path to the exported USD file

    Raises:
        RuntimeError: If USD export fails
        TypeError: If geometry is not a valid Geometry/Mesh socket

    Example:
        >>> from arrival.nodes import NodeTreeBuilder
        >>> from arrival import export_usd
        >>> with NodeTreeBuilder("MyScene") as tree:
        ...     cube = tree.mesh_cube(size=2.0)
        ...     path = export_usd(cube, "/tmp/scene.usda")
        >>> print(f"Exported: {path}")
    """
    from .sockets import Geometry as GeoClass
    
    if not isinstance(geometry, GeoClass):
        raise TypeError(
            f"export_usd requires a Geometry or Mesh socket wrapper, "
            f"got: {type(geometry).__name__}. "
            f"Create geometry with NodeTreeBuilder (e.g., tree.mesh_cube())."
        )
    
    return geometry._node.export_usd(geometry, output_path)
