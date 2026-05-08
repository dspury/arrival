"""Example: USD Export from Arrival.

This demonstrates exporting Arrival geometry to USD format,
which can be opened in other 3D applications (Maya, Houdini, Cinema 4D, etc.).

Run with: blender --background --python examples/usd_export.py
"""

import bpy
import sys
import os

# Ensure arrival is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from arrival.nodes import NodeTreeBuilder
from arrival import export_usd


def example_basic_export():
    """Export a simple cube to USD."""
    output_path = "/tmp/arrival_example_cube.usda"
    
    with NodeTreeBuilder("CubeExport") as tree:
        cube = tree.mesh_cube(size=2.0, location=(0, 0, 0))
        path = tree.export_usd(cube, output_path)
    
    print(f"Exported cube to: {path}")
    return path


def example_sphere_with_displacement():
    """Export a displaced sphere - shows complex geometry export."""
    output_path = "/tmp/arrival_example_displaced.usda"
    
    with NodeTreeBuilder("DisplacedExport") as tree:
        sphere = tree.mesh_ico_sphere(radius=1.5, subdivisions=3)
        displaced = sphere.displace_noise(strength=0.15, noise_scale=3.0)
        path = export_usd(displaced, output_path)
    
    print(f"Exported displaced sphere to: {path}")
    return path


def example_cluster_export():
    """Export a crystal cluster."""
    output_path = "/tmp/arrival_example_cluster.usda"
    
    with NodeTreeBuilder("ClusterExport") as tree:
        # Base ico sphere
        base = tree.mesh_ico_sphere(radius=1.0, subdivisions=2)
        base = base.displace_noise(strength=0.08, noise_scale=3.0)
        
        # Distribute points
        points = tree.points_on_faces(base, density=8.0, seed=42)
        
        # Create crystal shape (small cones)
        crystal = tree.mesh_cone(radius1=0.08, radius2=0.0, depth=0.5)
        
        # Instance crystals
        instances = tree.instance_on_points(points, crystal, scale=0.8)
        realized = instances.realize_instances()
        
        path = export_usd(realized, output_path)
    
    print(f"Exported crystal cluster to: {path}")
    return path


if __name__ == "__main__":
    print("=" * 60)
    print("Arrival USD Export Examples")
    print("=" * 60)
    
    # Run examples
    example_basic_export()
    print()
    example_sphere_with_displacement()
    print()
    example_cluster_export()
    
    print()
    print("All exports complete. Files are in /tmp/arrival_example_*.usda")