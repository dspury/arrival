"""Phase 2 delete geometry and mesh-to-points smoke tests."""

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


with NodeTreeBuilder("Phase2DeletePointsTest") as tree:
    mesh = tree.mesh_grid(size_x=2.0, size_y=2.0, vertices_x=8, vertices_y=8)
    points = tree.mesh_to_points(mesh, mode="VERTICES", radius=0.04)
    deleted = tree.delete_geometry(points, selection=False, domain="POINT")
    chain_points = mesh.to_points(mode="VERTICES", radius=0.02)
    chain_deleted = chain_points.delete(selection=False, domain="POINT")
    output = deleted.join(chain_deleted)
    tree.set_output(output)

    assert isinstance(mesh, Mesh)
    assert isinstance(points, Geometry)
    assert isinstance(deleted, Geometry)
    assert isinstance(chain_points, Geometry)
    assert isinstance(chain_deleted, Geometry)
    assert isinstance(output, Geometry)

    assert has_node(tree, "GeometryNodeMeshToPoints")
    assert has_node(tree, "GeometryNodeDeleteGeometry")
    assert has_node(tree, "GeometryNodeJoinGeometry")

    assert has_link_to(tree, "Mesh")
    # Radius uses default_value, not a link
    assert has_link_to(tree, "Geometry")

print("test_phase2_delete_points: OK")
