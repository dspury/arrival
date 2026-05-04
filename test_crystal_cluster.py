"""Crystal cluster render test — exercises Phase 2 priorities in order."""

import bpy
import sys
import os

arrival_path = "/Users/miles/arrival"
if arrival_path not in sys.path:
    sys.path.insert(0, arrival_path)

from arrival.nodes import NodeTreeBuilder
from arrival.materials import dark_mirror

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Set up Cycles render
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 64
scene.render.resolution_x = 480
scene.render.resolution_y = 360
scene.render.image_settings.file_format = 'PNG'

# Crystal cluster (Phase 2 success criteria)
with NodeTreeBuilder("CrystalCluster") as tree:
    base = tree.mesh_ico_sphere(radius=2.0, subdivisions=3)
    base = base.displace_noise(strength=0.08, noise_scale=3.0)

    points = base.points_on_faces(density=12.0, seed=7)
    crystal = tree.mesh_cone(radius1=0.12, radius2=0.0, depth=0.9)
    instances = points.instance_on_points(crystal, scale=0.7)
    cluster = instances.realize_instances().set_material(dark_mirror())

    tree.set_output(cluster)

# Create object and apply
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
obj = bpy.context.active_object
obj.name = "CrystalCluster"

mod = obj.modifiers.new(name="GeometryNodes", type='NODES')
mod.node_group = tree.tree

# Camera
bpy.ops.object.camera_add(location=(0, -6, 3))
cam = bpy.context.active_object
cam.name = "TestCamera"
scene.camera = cam
from mathutils import Vector
direction = Vector((0, 0, 0)) - Vector((0, -6, 3))
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

# Light
bpy.ops.object.light_add(type='SUN', location=(3, -3, 6))
light = bpy.context.active_object
light.data.energy = 3.0
light.data.color = (0.9, 0.95, 1.0)  # slightly blue-white

# World
world = bpy.data.worlds.new("CrystalWorld")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Strength"].default_value = 0.4

# Render
output_path = "/tmp/arrival_crystal_cluster.png"
scene.render.filepath = output_path
bpy.ops.render.render(write_still=True)

print(f"✓ Crystal cluster rendered to {output_path}")
print(f"  Tree: {tree.tree.name}")
print(f"  Nodes: {[n.bl_idname for n in tree.tree.nodes]}")
