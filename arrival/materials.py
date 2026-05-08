"""Material builder for Arrival.

Provides simple material creation functions that wrap Blender's shader node system.
Materials are created in bpy.data.materials and configured with node-based shaders.
"""

import bpy
from typing import Tuple, Optional


def _ensure_nodes(material: bpy.types.Material) -> Tuple[bpy.types.NodeTree, bpy.types.Node, bpy.types.Node]:
    """Ensure material has node tree setup, return (nodes, bsdf, output)."""
    if not material.use_nodes:
        material.use_nodes = True
    
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create output and bsdf
    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (300, 0)
    
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    
    return material.node_tree, bsdf, output


def principled(base_color: Tuple[float, float, float, float] = (0.8, 0.8, 0.8, 1.0),
               metallic: float = 0.0,
               roughness: float = 0.5,
               specular: float = 0.5,
               emission: Optional[Tuple[float, float, float, float]] = None,
               emission_strength: float = 0.0,
               ior: float = 1.45,
               transmission: float = 0.0,
               name: str = "PrincipledMaterial") -> bpy.types.Material:
    """Create a Principled BSDF material.
    
    Args:
        base_color: RGBA base color (0-1 range)
        metallic: Metallic value (0-1)
        roughness: Roughness value (0-1)
        specular: Specular value (0-1)
        emission: RGBA emission color, or None
        emission_strength: Emission strength
        ior: Index of refraction
        transmission: Transmission weight (for glass-like materials)
        name: Material name
    
    Returns:
        Blender material
    """
    mat = bpy.data.materials.new(name=name)
    tree, bsdf, output = _ensure_nodes(mat)
    
    # Set Principled BSDF properties
    bsdf.inputs["Base Color"].default_value = base_color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Specular IOR Level"].default_value = specular
    bsdf.inputs["IOR"].default_value = ior
    bsdf.inputs["Transmission Weight"].default_value = transmission
    
    # Emission
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = emission
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    
    # Link
    tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    
    return mat


def emission(color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
             strength: float = 3.0,
             name: str = "EmissionMaterial") -> bpy.types.Material:
    """Create a pure emission material (no shading, just glow).
    
    Args:
        color: RGBA emission color
        strength: Emission strength (higher = brighter)
        name: Material name
    
    Returns:
        Blender material
    """
    mat = bpy.data.materials.new(name=name)
    
    if not mat.use_nodes:
        mat.use_nodes = True
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (300, 0)
    
    emission = nodes.new(type="ShaderNodeEmission")
    emission.location = (0, 0)
    emission.inputs["Color"].default_value = color
    emission.inputs["Strength"].default_value = strength
    
    mat.node_tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])
    
    return mat


def glass(color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
          roughness: float = 0.0,
          ior: float = 1.45,
          name: str = "GlassMaterial") -> bpy.types.Material:
    """Create a glass-like material using Principled BSDF with transmission.
    
    Args:
        color: RGBA color
        roughness: Surface roughness (0 = perfectly smooth)
        ior: Index of refraction (1.45 = glass)
        name: Material name
    
    Returns:
        Blender material
    """
    return principled(
        base_color=color,
        roughness=roughness,
        ior=ior,
        transmission=0.95,
        name=name
    )


def dark_mirror(roughness: float = 0.05,
                name: str = "DarkMirror") -> bpy.types.Material:
    """Create a dark, mirror-like metallic material.
    
    Good for reflective surfaces like in the crystal cluster examples.
    
    Args:
        roughness: Surface roughness
        name: Material name
    
    Returns:
        Blender material
    """
    # Base color lifted from 0.01 → 0.04 so the surface still reads as "dark mirror"
    # but isn't a near-perfect light sink under typical lighting rigs.
    return principled(
        base_color=(0.04, 0.04, 0.06, 1.0),
        metallic=1.0,
        roughness=roughness,
        specular=1.5,
        name=name
    )


def obsidian(name: str = "Obsidian") -> bpy.types.Material:
    """Create an obsidian (volcanic glass) material.
    
    Dark, slightly reflective, with high specularity.
    
    Args:
        name: Material name
    
    Returns:
        Blender material
    """
    mat = bpy.data.materials.new(name=name)
    tree, bsdf, output = _ensure_nodes(mat)
    
    # Obsidian is a deep, glassy black — but Principled BSDF with base_color near 0
    # absorbs almost all light and renders pitch-black under typical lighting. Lift the
    # base slightly and drop transmission so reflections (the actual visual signature
    # of obsidian) carry the look.
    bsdf.inputs["Base Color"].default_value = (0.05, 0.05, 0.07, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 0.05
    bsdf.inputs["IOR"].default_value = 2.1
    bsdf.inputs["Specular IOR Level"].default_value = 1.2
    bsdf.inputs["Coat Weight"].default_value = 1.0
    bsdf.inputs["Coat IOR"].default_value = 1.6
    bsdf.inputs["Coat Roughness"].default_value = 0.0
    bsdf.inputs["Transmission Weight"].default_value = 0.0
    
    tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    
    return mat


class Material:
    """Material builder class for fluent API.
    
    Usage:
        mat = Material().principled(base_color=(0.8, 0.2, 0.1), metallic=1.0).build()
        # or
        mat = Material.emission(color=(0.2, 0.8, 1.0), strength=5.0)
    """
    
    @staticmethod
    def principled(base_color: Tuple[float, float, float, float] = (0.8, 0.8, 0.8, 1.0),
                  metallic: float = 0.0,
                  roughness: float = 0.5,
                  specular: float = 0.5,
                  emission: Optional[Tuple[float, float, float, float]] = None,
                  emission_strength: float = 0.0) -> bpy.types.Material:
        """Create a Principled BSDF material."""
        return principled(
            base_color=base_color,
            metallic=metallic,
            roughness=roughness,
            specular=specular,
            emission=emission,
            emission_strength=emission_strength
        )
    
    @staticmethod
    def emission(color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
                strength: float = 3.0) -> bpy.types.Material:
        """Create a pure emission material."""
        return emission(color=color, strength=strength)
    
    @staticmethod
    def glass(color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
              roughness: float = 0.0,
              ior: float = 1.45) -> bpy.types.Material:
        """Create a glass material."""
        return glass(color=color, roughness=roughness, ior=ior)
    
    @staticmethod
    def dark_mirror(roughness: float = 0.05) -> bpy.types.Material:
        """Create a dark mirror material."""
        return dark_mirror(roughness=roughness)
    
    @staticmethod
    def obsidian() -> bpy.types.Material:
        """Create an obsidian material."""
        return obsidian()
