"""Arrival — agent-native 3D geometry library wrapping Blender's bpy."""

from .sockets import Geometry, Mesh, Float, Vector, Color, Integer, Boolean
from .materials import Material
from .scene import Scene
from . import blender

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
    "blender",
]

__version__ = "0.1.0"
