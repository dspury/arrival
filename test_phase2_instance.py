"""Phase 2 instancing pipeline smoke tests."""

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


with NodeTreeBuilder("Phase2InstanceTest") as tree:
    base = tree.mesh_ico_sphere(radius=2.0, subdivisions=3)
    points = base.points_on_faces(density=8.0, seed=4)
    crystal = tree.mesh_cone(radius1=0.12, radius2=0.0, depth=0.8)
    instances = points.instance_on_points(crystal, scale=0.6)
    realized = instances.realize_instances()
    tree.set_output(realized)

    assert isinstance(base, Mesh)
    assert isinstance(points, Geometry)
    assert isinstance(crystal, Mesh)
    assert isinstance(instances, Geometry)
    assert isinstance(realized, Geometry)

    assert has_node(tree, "GeometryNodeDistributePointsOnFaces")
    assert has_node(tree, "GeometryNodeInstanceOnPoints")
    assert has_node(tree, "GeometryNodeRealizeInstances")

    assert has_link_to(tree, "Mesh")
    assert has_link_to(tree, "Points")
    assert has_link_to(tree, "Instance")
    # Scale uses default_value (0.6 -> (0.6, 0.6, 0.6)), not a link
    assert has_link_to(tree, "Geometry")

print("test_phase2_instance: OK")
