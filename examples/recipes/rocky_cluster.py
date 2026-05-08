# These are reference implementations showing how to compose Arrival primitives.
# Import directly from this module, not from arrival itself.

import sys
from pathlib import Path

# Ensure arrival is importable when running examples from this directory
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from arrival.nodes import NodeTreeBuilder
from arrival import sockets
from arrival import Scene
from arrival.materials import Material


def rocky_cluster(
    radius: float = 2.0,
    subdivisions: int = 2,
    density: float = 10.0,
    seed: int = 42,
    displacement_strength: float = 0.15,
    displacement_scale: float = 2.5,
    material=None,
) -> sockets.Geometry:
    """Create a rocky cluster: displaced ico sphere with no crystal instances.
    
    Good for asteroids, ore deposits, or organic rock formations.
    
    Args:
        radius: Size of the base ico sphere
        subdivisions: Detail level
        density: Point density for surface detail
        seed: Random seed
        displacement_strength: Surface roughness
        displacement_scale: Scale of displacement noise
        material: Optional material
    
    Returns:
        Geometry socket
    """
    tree = NodeTreeBuilder("RockyCluster")
    tree.__enter__()
    
    base = tree.mesh_ico_sphere(radius=radius, subdivisions=subdivisions)
    base = base.displace_noise(strength=displacement_strength, noise_scale=displacement_scale)
    points = tree.points_on_faces(base, density=density, seed=seed)
    realized = points.realize_instances()
    
    if material is not None:
        realized = realized.set_material(material)
    
    return realized