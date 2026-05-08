"""Tests for arrival.show() — one-call render with smart defaults."""

import pytest
import os


def test_show_returns_path_ending_in_png():
    """Verify show() returns a path string that ends with .png."""
    import bpy
    import arrival
    
    # Create a simple mesh cube
    with arrival.nodes.NodeTreeBuilder("ShowTest") as builder:
        cube = builder.mesh_cube(size=1.0, location=(0, 0, 0))
    
    # Call show and verify it returns a string
    result = arrival.show(cube)
    assert isinstance(result, str)
    assert result.endswith(".png"), f"Expected .png ending, got: {result}"


def test_show_returns_valid_file_path():
    """Verify show() returns a valid file path string."""
    import bpy
    import arrival
    
    with arrival.nodes.NodeTreeBuilder("ShowTest2") as builder:
        cube = builder.mesh_cube(size=1.0, location=(0, 0, 0))
    
    result = arrival.show(cube)
    # Should be a proper absolute path
    assert os.path.isabs(result), f"Expected absolute path, got: {result}"


def test_show_file_actually_exists():
    """Verify the rendered PNG file actually exists on disk."""
    import bpy
    import arrival
    
    with arrival.nodes.NodeTreeBuilder("ShowTest3") as builder:
        cube = builder.mesh_cube(size=1.0, location=(0, 0, 0))
    
    result = arrival.show(cube)
    assert os.path.exists(result), f"Expected file to exist at: {result}"
    # Verify it's not empty
    assert os.path.getsize(result) > 0, f"File at {result} is empty"