"""Tests for arrival.describe() — scene description for LLM context windows."""

import pytest
import os
import sys

# Add arrival to path for standalone test execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_describe_from_path_rejects_nonexistent():
    """describe() raises TypeError for a non-existent file path."""
    import arrival
    with pytest.raises(TypeError):
        arrival.describe("/nonexistent/path/to/image.png")


def test_describe_from_path_rejects_invalid_type():
    """describe() raises TypeError when passed something that is neither Scene nor str."""
    import arrival
    with pytest.raises(TypeError):
        arrival.describe(12345)
    with pytest.raises(TypeError):
        arrival.describe([1, 2, 3])


def test_describe_exported_in_init():
    """describe is exported from the arrival module."""
    import arrival
    assert hasattr(arrival, "describe"), "arrival.describe should be exported"
    assert callable(arrival.describe)


def test_describe_function_signature():
    """describe accepts a Scene or a path string."""
    from arrival.scene import describe
    import inspect
    sig = inspect.signature(describe)
    assert len(sig.parameters) == 1


@pytest.mark.blender
def test_describe_on_simple_scene():
    """Create a simple scene, render with arrival.show(), call describe(), verify output."""
    import bpy
    import arrival

    # Create a simple scene using the NodeTreeBuilder API (like the README example)
    from arrival.nodes import NodeTreeBuilder

    with NodeTreeBuilder("TestScene") as builder:
        sphere = builder.mesh_ico_sphere(radius=1.5, subdivisions=3)
        sphere = sphere.displace_noise(strength=0.08, noise_scale=2.5)
    
    # Render using arrival.show
    image_path = arrival.show(builder, output_path="/tmp/arrival_test_describe.png")
    
    # Verify the image was created
    assert os.path.exists(image_path), f"Rendered image not found: {image_path}"
    
    # Call describe on the image path
    description = arrival.describe(image_path)
    
    # Verify the description is non-empty
    assert isinstance(description, str), "describe() should return a string"
    assert len(description) > 0, "Description should not be empty"
    
    # Verify it contains recognizable content (geometry, lighting, or composition keywords)
    description_lower = description.lower()
    expected_keywords = ["geometry", "sphere", "light", "surface", "render", "scene", "form", "material"]
    found = any(kw in description_lower for kw in expected_keywords)
    assert found, (
        f"Description should contain recognizable content but got: {description[:200]}..."
    )

    print(f"\nGenerated description ({len(description)} chars):\n{description[:400]}...")


if __name__ == "__main__":
    # Run with: python tests/test_describe.py
    # Requires Blender context (run via: blender --background --python tests/test_describe.py)
    pytest.main([__file__, "-v"])