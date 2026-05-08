# These are reference implementations showing how to compose Arrival primitives.
# Import directly from this module, not from arrival itself.

import sys
from pathlib import Path

# Ensure arrival is importable when running examples from this directory
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from arrival.nodes import NodeTreeBuilder
from arrival import sockets
from arrival import Scene
from arrival.materials import Material

# Re-export for backward compatibility
from .crystal_cluster import crystal_cluster
from .rocky_cluster import rocky_cluster

__all__ = ['crystal_cluster', 'rocky_cluster']