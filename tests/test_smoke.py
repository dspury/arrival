"""Smoke tests for arrival module."""

import pytest


def test_import_arrival():
    """Verify the arrival module imports successfully."""
    import arrival
    assert hasattr(arrival, "NodeTreeBuilder")


def test_import_nodes_module():
    """Verify nodes module exposes NodeTreeBuilder."""
    from arrival.nodes import NodeTreeBuilder
    assert NodeTreeBuilder is not None


def test_import_scene_module():
    """Verify scene module exposes Scene."""
    from arrival.scene import Scene
    assert Scene is not None


def test_smoke_node_tree_builder():
    """Smoke test: NodeTreeBuilder context, mesh_cube, builder.nodes, context manager protocol."""
    import bpy
    from arrival.nodes import NodeTreeBuilder

    # Can be used as a context manager
    with NodeTreeBuilder("SmokeTest") as builder:
        # Creates a mesh cube
        mesh = builder.mesh_cube(size=1.0, location=(0, 0, 0))
        
        # Verifies builder.nodes has content (the underlying node tree nodes)
        assert len(builder.tree.nodes) > 0
        
        # Verify mesh socket is returned
        assert mesh is not None

    # Context manager __exit__ ran without error (no exception re-raised)
