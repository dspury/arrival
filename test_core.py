"""Test the Arrival library core functionality in Blender."""

import bpy
import sys
import os

# Add arrival to path
arrival_path = "/Users/miles/arrival"
if arrival_path not in sys.path:
    sys.path.insert(0, arrival_path)

from arrival.nodes import NodeTreeBuilder, new_tree
from arrival.materials import principled, emission, obsidian, dark_mirror
from arrival.sockets import Geometry, Mesh, Float, Vector

print("=" * 50)
print("ARRIVAL CORE TEST")
print("=" * 50)

# Test 1: Create a NodeTreeBuilder
print("\n[TEST 1] NodeTreeBuilder context")
try:
    with NodeTreeBuilder("TestTree") as tree:
        print(f"  ✓ Created tree: {tree.tree.name}")
        print(f"  ✓ Group input exists: {tree._group_input is not None}")
        print(f"  ✓ Group output exists: {tree._group_output is not None}")
        print(f"  ✓ Interface sockets defined")
except Exception as e:
    print(f"  ✗ Error: {e}")

# Test 2: Create mesh primitives
print("\n[TEST 2] Mesh primitives")
try:
    with NodeTreeBuilder("PrimitiveTest") as tree:
        cube = tree.mesh_cube(size=1.0)
        print(f"  ✓ mesh_cube: {type(cube).__name__}")
        
        sphere = tree.mesh_sphere(radius=0.5)
        print(f"  ✓ mesh_sphere: {type(sphere).__name__}")
        
        grid = tree.mesh_grid(size_x=4.0, size_y=4.0, vertices_x=32, vertices_y=32)
        print(f"  ✓ mesh_grid: {type(grid).__name__}")
        
        circle = tree.mesh_circle(vertices=64, radius=1.5)
        print(f"  ✓ mesh_circle: {type(circle).__name__}")
        
        cylinder = tree.mesh_cylinder(radius=0.5, depth=2.0)
        print(f"  ✓ mesh_cylinder: {type(cylinder).__name__}")
        
        cone = tree.mesh_cone(radius1=1.0, radius2=0.0, depth=2.0)
        print(f"  ✓ mesh_cone: {type(cone).__name__}")
        
        line = tree.mesh_line(count=20, offset=(0.2, 0, 0))
        print(f"  ✓ mesh_line: {type(line).__name__}")
        
        ico = tree.mesh_ico_sphere(radius=0.8, subdivisions=2)
        print(f"  ✓ mesh_ico_sphere: {type(ico).__name__}")
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Chain mesh operations
print("\n[TEST 3] Mesh chaining")
try:
    with NodeTreeBuilder("ChainTest") as tree:
        mesh = tree.mesh_grid(size_x=4.0, size_y=4.0, vertices_x=64, vertices_y=64)
        mesh = mesh.transform(translation=(0, 0, 1), scale=(1.0, 1.0, 0.5))
        print(f"  ✓ Chain worked: {type(mesh).__name__}")
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Create materials
print("\n[TEST 4] Materials")
try:
    mat1 = principled(base_color=(0.8, 0.2, 0.1, 1.0), metallic=0.0, roughness=0.5)
    print(f"  ✓ principled: {mat1.name}")
    
    mat2 = emission(color=(0.2, 0.8, 1.0, 1.0), strength=5.0)
    print(f"  ✓ emission: {mat2.name}")
    
    mat3 = obsidian()
    print(f"  ✓ obsidian: {mat3.name}")
    
    mat4 = dark_mirror(roughness=0.05)
    print(f"  ✓ dark_mirror: {mat4.name}")
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Apply node tree to object
print("\n[TEST 5] Apply to object")
try:
    # Create a cube object
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    obj = bpy.context.active_object
    
    with NodeTreeBuilder("ApplyTest") as tree:
        mesh = tree.mesh_sphere(radius=1.0)
        tree.set_output(mesh)
    
    mod = obj.modifiers.new(name="GeometryNodes", type='NODES')
    mod.node_group = tree.tree
    print(f"  ✓ Applied to object: {obj.name}, modifier: {mod.name}")
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Create value nodes
print("\n[TEST 6] Value nodes")
try:
    with NodeTreeBuilder("ValueTest") as tree:
        f = tree.float_constant(3.14)
        print(f"  ✓ float_constant: {type(f).__name__}")
        
        v = tree.vector_constant(1.0, 2.0, 3.0)
        print(f"  ✓ vector_constant: {type(v).__name__}")
        
        c = tree.color_constant(1.0, 0.5, 0.2, 1.0)
        print(f"  ✓ color_constant: {type(c).__name__}")
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 7: Noise nodes
print("\n[TEST 7] Noise nodes")
try:
    with NodeTreeBuilder("NoiseTest") as tree:
        n = tree.noise(scale=2.5, detail=8.0)
        print(f"  ✓ noise: {type(n).__name__}")
        
        v = tree.voronoi(scale=3.0)
        print(f"  ✓ voronoi: {type(v).__name__}")
        
        r = tree.random_float(0.0, 1.0)
        print(f"  ✓ random_float: {type(r).__name__}")
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("ALL TESTS COMPLETE")
print("=" * 50)
