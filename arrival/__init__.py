"""Arrival — agent-native 3D geometry library wrapping Blender's bpy."""

from .sockets import Geometry, Mesh, Float, Vector, Color, Integer, Boolean
from .materials import Material
from .scene import Scene, describe, show
from . import blender
from .nodes import new_tree

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
    "blender",
    "new_tree",
]

__version__ = "0.1.0"
