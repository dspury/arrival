"""Phase 2 deformation smoke tests."""

import sys

arrival_path = "/Users/miles/arrival"
if arrival_path not in sys.path:
    sys.path.insert(0, arrival_path)

from arrival.nodes import NodeTreeBuilder
from arrival.sockets import Geometry, Mesh


def has_node(tree, bl_idname):
    return any(node.bl_idname == bl_idname for node in tree.tree.nodes)


def has_link_to(tree, socket_name):
    return any(link.to_socket.name == socket_name for link in tree.tree.links)


with NodeTreeBuilder("Phase2DeformTest") as tree:
    mesh = tree.mesh_grid(size_x=4.0, size_y=4.0, vertices_x=64, vertices_y=64)
    subdivided = mesh.subdivide(levels=2)
    displaced = subdivided.displace_noise(strength=0.25, noise_scale=2.5)
    tree.set_output(displaced)

    assert isinstance(mesh, Mesh)
    assert isinstance(subdivided, Mesh)
    assert isinstance(displaced, Geometry)

    assert has_node(tree, "GeometryNodeSubdivideMesh")
    assert has_node(tree, "ShaderNodeTexNoise")
    assert has_node(tree, "ShaderNodeMapRange")
    assert has_node(tree, "GeometryNodeInputNormal")
    assert has_node(tree, "ShaderNodeVectorMath")
    assert has_node(tree, "GeometryNodeSetPosition")

    assert has_link_to(tree, "Mesh")
    assert has_link_to(tree, "Value")
    assert has_link_to(tree, "Scale")
    assert has_link_to(tree, "Offset")
    assert has_link_to(tree, "Geometry")

print("test_phase2_deform: OK")
