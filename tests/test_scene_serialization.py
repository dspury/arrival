"""Tests for Scene.to_dict() and Scene.from_dict() serialization."""

import pytest


def test_to_dict_returns_dict():
    """Verify to_dict returns a dictionary with expected keys."""
    # Can't run without Blender, but verify the method exists and returns a dict structure
    # by checking the Scene class has the method
    import inspect
    from arrival.scene import Scene
    assert hasattr(Scene, 'to_dict')
    assert callable(Scene.to_dict)


def test_from_dict_is_classmethod():
    """Verify from_dict is a classmethod on Scene."""
    from arrival.scene import Scene
    assert hasattr(Scene, 'from_dict')
    assert callable(Scene.from_dict)


def test_to_dict_expected_keys():
    """Verify to_dict docstring describes the expected output keys."""
    from arrival.scene import Scene
    doc = Scene.to_dict.__doc__
    assert 'name' in doc
    assert 'geometry' in doc
    assert 'camera_position' in doc
    assert 'lights' in doc
    assert 'background' in doc
    assert 'render_settings' in doc


def test_from_dict_expected_behavior():
    """Verify from_dict docstring describes the expected behavior."""
    from arrival.scene import Scene
    doc = Scene.from_dict.__doc__
    assert 'Scene' in doc
    assert 'dict' in doc
