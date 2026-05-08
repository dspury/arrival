# Arrival

> Agent-native 3D geometry via Blender geometry nodes.

## What

Arrival is a Python library that gives language models the ability to produce structured 3D geometry without needing to understand Blender's UI or manual node authoring. Write Python, get rendered geometry.

## Install

pip install -e .
# requires Blender 5.1.x installed on the system

## Quick Start

import arrival

# Build geometry with a fluent NodeTree API
with arrival.NodeTreeBuilder("MyScene") as tree:
    geometry = tree.mesh_ico_sphere(radius=2.0, subdivisions=3)
    geometry = geometry.displace_noise(strength=0.1, noise_scale=2.0)
    arrival.show(geometry)  # render and display

## Status

Actively developing. See SPEC.md for the full API surface.

## Requirements

- Python 3.10+
- Blender 5.1.x (installed separately — not bundled)