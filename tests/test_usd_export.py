"""Tests for USD export functionality in Arrival.

These tests are designed to run in Blender's Python environment (headless).
They do not require pytest - instead they use simple assertions.
"""

import os


def test_export_usd_returns_path():
    """Verify export_usd returns a path string."""
    import bpy
    import arrival
    
    from arrival.nodes import NodeTreeBuilder
    
    with NodeTreeBuilder("USDTest") as tree:
        cube = tree.mesh_cube(size=1.0, location=(0, 0, 0))
    
    path = arrival.export_usd(cube, "/tmp/arrival_usd_test.usda")
    assert isinstance(path, str), f"Expected str, got {type(path)}"
    assert path.endswith('.usda') or path.endswith('.usdc') or path.endswith('.usdz'), f"Expected USD extension, got: {path}"


def test_export_usd_file_exists():
    """Verify the exported USD file actually exists."""
    import bpy
    import arrival
    
    from arrival.nodes import NodeTreeBuilder
    
    output_path = "/tmp/arrival_usd_exists_test.usda"
    
    with NodeTreeBuilder("USDTest2") as tree:
        cube = tree.mesh_cube(size=1.5, location=(1, 0, 0))
    
    path = arrival.export_usd(cube, output_path)
    assert os.path.exists(path), f"Expected file to exist at: {path}"
    assert os.path.getsize(path) > 0, f"File at {path} is empty"


def test_geometry_to_usd_method():
    """Verify Geometry.to_usd() convenience method works."""
    import bpy
    
    from arrival.nodes import NodeTreeBuilder
    
    output_path = "/tmp/arrival_method_test.usda"
    
    with NodeTreeBuilder("USDMethodTest") as tree:
        sphere = tree.mesh_sphere(radius=1.0, location=(0, 0, 1))
    
    path = sphere.to_usd(output_path)
    assert os.path.exists(path), f"Expected file to exist at: {path}"


def test_export_usd_wrong_type_raises():
    """Verify export_usd raises TypeError for invalid input."""
    import arrival
    
    try:
        arrival.export_usd("not a geometry", "/tmp/fail.usda")
        assert False, "Expected TypeError but none was raised"
    except TypeError as e:
        assert "requires a Geometry or Mesh socket" in str(e), f"Unexpected error message: {e}"


def test_export_usd_adds_extension():
    """Verify export_usd adds .usda if extension is missing."""
    import bpy
    import arrival
    
    from arrival.nodes import NodeTreeBuilder
    
    output_path = "/tmp/arrival_no_ext_test"  # no extension
    
    with NodeTreeBuilder("USDTest3") as tree:
        cube = tree.mesh_cube(size=1.0, location=(0, 0, 0))
    
    path = arrival.export_usd(cube, output_path)
    # Should have .usda appended
    assert path.endswith('.usda'), f"Expected .usda extension, got: {path}"
    assert os.path.exists(path), f"Expected file to exist at: {path}"


def test_export_usd_with_displacement():
    """Verify USD export works with more complex geometry (displaced grid)."""
    import bpy
    import arrival
    
    from arrival.nodes import NodeTreeBuilder
    
    output_path = "/tmp/arrival_displaced.usda"
    
    with NodeTreeBuilder("USDDisplaced") as tree:
        grid = tree.mesh_grid(size_x=4, size_y=4, vertices_x=32, vertices_y=32)
        displaced = grid.displace_noise(strength=0.2, noise_scale=2.0)
    
    path = arrival.export_usd(displaced, output_path)
    assert os.path.exists(path), f"Expected file to exist at: {path}"
    # File should have reasonable content
    assert os.path.getsize(path) > 500, "USD file seems too small for displaced grid"


def test_node_tree_builder_export_usd():
    """Verify NodeTreeBuilder.export_usd() method works."""
    import bpy
    
    from arrival.nodes import NodeTreeBuilder
    
    output_path = "/tmp/arrival_tree_method.usda"
    
    with NodeTreeBuilder("USDTreetTest") as tree:
        cone = tree.mesh_cone(radius1=0.5, radius2=0.0, depth=2.0)
        tree.export_usd(cone, output_path)
    
    assert os.path.exists(output_path), f"Expected file to exist at: {output_path}"


def test_usd_contains_mesh_data():
    """Verify the USD file actually contains mesh data."""
    import bpy
    import arrival
    
    from arrival.nodes import NodeTreeBuilder
    
    output_path = "/tmp/arrival_mesh_content.usda"
    
    with NodeTreeBuilder("USDMeshContent") as tree:
        cube = tree.mesh_cube(size=2.0, location=(0, 0, 0))
    
    path = arrival.export_usd(cube, output_path)
    
    # Read the file and check it contains mesh definition
    with open(path, 'r') as f:
        content = f.read()
    
    # USD format should contain something like "def Mesh" or "mesh" 
    assert 'Mesh' in content or 'mesh' in content, f"Expected mesh data in USD file, got: {content[:200]}"