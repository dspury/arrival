"""Crystal cluster render test — exercises Phase 2 + composition API."""

import bpy
import sys
import os

arrival_path = "/Users/miles/arrival"
if arrival_path not in sys.path:
    sys.path.insert(0, arrival_path)

from arrival import Scene
from arrival.materials import dark_mirror

# Crystal cluster using Scene composition API
with Scene("CrystalCluster") as scene:
    # Build geometry with node tree
    base = scene.nodes.mesh_ico_sphere(radius=2.0, subdivisions=3)
    base = base.displace_noise(strength=0.08, noise_scale=3.0)

    points = scene.nodes.points_on_faces(base, density=12.0, seed=7)
    crystal = scene.nodes.mesh_cone(radius1=0.12, radius2=0.0, depth=0.9)
    geo = scene.nodes.instance_on_points(points, crystal, scale=0.7)
    geo = geo.realize_instances().set_material(dark_mirror())

    scene.mesh(geo)

    # Composition
    scene.camera("dramatic")
    scene.lighting("crystal")

    # Render
    scene.render(
        "/tmp/arrival_crystal_cluster.png",
        quality="good",
        resolution=(960, 720)
    )

# Finalize
output = scene.render_and_save()
print(f"✓ Crystal cluster rendered to {output}")
