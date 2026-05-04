"""Full render test for Arrival using Scene composition API."""

import bpy
import sys
import os

arrival_path = "/Users/miles/arrival"
if arrival_path not in sys.path:
    sys.path.insert(0, arrival_path)

from arrival import Scene
from arrival.materials import obsidian

with Scene("RenderTest") as scene:
    nt = scene.nodes
    mesh = nt.mesh_ico_sphere(radius=1.5, subdivisions=3)
    mesh = mesh.transform(translation=(0, 0, 0.5))
    scene.mesh(mesh, material=obsidian())
    scene.camera("medium")
    scene.lighting("studio")
    scene.render("/tmp/arrival_render_test.png", quality="good", resolution=(640, 480))

output = scene.render_and_save()
print(f"✓ Rendered to {output}")
