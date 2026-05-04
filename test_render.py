"""Full render test for Arrival."""

import bpy
import sys
import os
import tempfile

arrival_path = "/Users/miles/arrival"
if arrival_path not in sys.path:
    sys.path.insert(0, arrival_path)

from arrival.nodes import NodeTreeBuilder
from arrival.materials import principled, emission, obsidian

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

# Create node tree
with NodeTreeBuilder("RenderTest") as tree:
    # Create geometry
    mesh = tree.mesh_ico_sphere(radius=1.5, subdivisions=3)
    mesh = mesh.transform(translation=(0, 0, 0.5))
    
    # Set output
    tree.set_output(mesh)

# Create object and apply modifier
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
obj = bpy.context.active_object
obj.name = "TestRender"

mod = obj.modifiers.new(name="GeometryNodes", type='NODES')
mod.node_group = tree.tree

# Set material
mat = obsidian()
obj.data.materials.append(mat)

# Add camera
bpy.ops.object.camera_add(location=(0, -4, 2))
cam = bpy.context.active_object
cam.name = "TestCamera"
scene.camera = cam
cam.rotation_euler = (1.1, 0, 0)  # Look down and forward

# Add light
bpy.ops.object.light_add(type='SUN', location=(2, -2, 4))
light = bpy.context.active_object
light.data.energy = 3.0

# World
world = bpy.data.worlds.new("TestWorld")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Strength"].default_value = 0.5

# Render to temp file
output_path = "/tmp/arrival_render_test.png"
scene.render.filepath = output_path
bpy.ops.render.render(write_still=True)

print(f"✓ Rendered to {output_path}")
print(f"  Tree: {tree.tree.name}")
print(f"  Object: {obj.name}")
print(f"  Material: {mat.name}")
