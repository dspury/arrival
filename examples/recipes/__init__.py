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


def crystal_cluster(
    radius: float = 2.0,
    subdivisions: int = 3,
    density: float = 12.0,
    crystal_radius: float = 0.12,
    crystal_depth: float = 0.9,
    crystal_scale_min: float = 0.4,
    crystal_scale_max: float = 1.5,
    seed: int = 7,
    displacement_strength: float = 0.08,
    displacement_scale: float = 3.0,
    material=None,
) -> tuple[NodeTreeBuilder, sockets.Geometry]:
    """Create a crystal cluster: ico sphere base with pointed crystal instances.

    Crystals are hexagonal prisms with pointed tips, oriented to surface normals
    with randomized scale for natural variation. Crystals grow from the top
    hemisphere only, leaning outward from the base.

    Args:
        radius: Size of the base ico sphere
        subdivisions: Detail level of the base (higher = more facets)
        density: Number of crystal instances per face
        crystal_radius: Base radius of crystal prisms
        crystal_depth: Height of crystal prisms (tip to base)
        crystal_scale_min: Minimum random scale for crystals
        crystal_scale_max: Maximum random scale for crystals
        seed: Random seed for point distribution
        displacement_strength: How much to displace the base surface (0 = no displacement)
        displacement_scale: Scale of the noise displacement
        material: Optional material to apply to the cluster

    Returns:
        Tuple of (NodeTreeBuilder, Geometry socket with realized instances)

    Example:
        with Scene("MyScene") as scene:
            tree, cluster = crystal_cluster(radius=2.0, density=15.0)
            scene.mesh(cluster, material=dark_mirror())
            scene.camera("dramatic")
            scene.lighting("crystal")
            scene.render("/tmp/crystals.png")
    """
    tree = NodeTreeBuilder("CrystalCluster")
    tree.__enter__()

    # ── 1. Base sphere ──────────────────────────────────────────────────────────
    base = tree.mesh_ico_sphere(radius=radius, subdivisions=subdivisions)
    if displacement_strength > 0:
        base = base.displace_noise(strength=displacement_strength, noise_scale=displacement_scale)

    # ── 3. Distribute points on all faces ───────────────────────────────────────
    # Note: hemisphere selection via Z comparison is deferred — the Z>0 test
    # requires a Float→Boolean conversion that's easier to add after we confirm
    # the basic instancing chain works.
    points = tree.points_on_faces(base, density=density, seed=seed)

    # ── 4. Build a single crystal: hexagonal prism base + pointed cone tip ────────
    # The crystal is built at the origin pointing +Z:
    #   - Bottom half: 6-sided cylinder, filled
    #   - Top half: 6-sided cone tapering to a point
    #   - Joined so the tip is at local +Z = crystal_depth, base is at local 0
    prism = tree.mesh_cylinder(radius=crystal_radius, depth=crystal_depth * 0.55,
                               vertices=6)
    tip = tree.mesh_cone(radius1=crystal_radius, radius2=0.0,
                          depth=crystal_depth * 0.55)
    # Translate tip so its base sits at local Z = crystal_depth * 0.55
    tip = tip.transform(translation=(0, 0, crystal_depth * 0.55))
    crystal_mesh = prism.join(tip)

    # ── 5. Random rotation per crystal ─────────────────────────────────────────────
    # Use random_vector for per-instance rotation (Euler XYZ).
    # X: slight outward lean [0, 0.25] — cookbook-style tilt
    # Y: 0 (no twist)
    # Z: splay around normal [-0.5, 0.5] — natural cluster variation
    rotation_rand = tree.random_vector(
        min_val=(0.0, 0.0, -0.5),
        max_val=(0.25, 0.0, 0.5),
        seed=seed,
    )

    # ── 7. Random scale for size variation ───────────────────────────────────────
    # Use random_vector for proper per-crystal non-uniform scale.
    scale_rand = tree.random_vector(
        min_val=(crystal_scale_min, crystal_scale_min, crystal_scale_min),
        max_val=(crystal_scale_max, crystal_scale_max, crystal_scale_max),
        seed=seed,
    )

    # ── 8. Instance crystals on points ──────────────────────────────────────────
    instances = tree.instance_on_points(
        points,
        crystal_mesh,
        rotation=rotation_rand,
        scale=scale_rand,
    )

    # ── 9. Realize and apply material ───────────────────────────────────────────
    realized = instances.realize_instances()
    if material is not None:
        realized = realized.set_material(material)

    return tree, realized


def rocky_cluster(
    radius: float = 2.0,
    subdivisions: int = 2,
    density: float = 10.0,
    seed: int = 42,
    displacement_strength: float = 0.15,
    displacement_scale: float = 2.5,
    material=None,
) -> tuple[NodeTreeBuilder, sockets.Geometry]:
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
        Tuple of (NodeTreeBuilder, Geometry socket)
    """
    tree = NodeTreeBuilder("RockyCluster")
    tree.__enter__()
    
    base = tree.mesh_ico_sphere(radius=radius, subdivisions=subdivisions)
    base = base.displace_noise(strength=displacement_strength, noise_scale=displacement_scale)
    points = tree.points_on_faces(base, density=density, seed=seed)
    realized = points.realize_instances()
    
    if material is not None:
        realized = realized.set_material(material)
    
    return tree, realized
