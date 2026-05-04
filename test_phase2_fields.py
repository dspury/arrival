"""Phase 2 field, math, and minimal attribute smoke tests."""

import sys

arrival_path = "/Users/miles/arrival"
if arrival_path not in sys.path:
    sys.path.insert(0, arrival_path)

from arrival.nodes import NodeTreeBuilder
from arrival.sockets import Float, Geometry, Integer, Vector


def has_node(tree, bl_idname):
    return any(node.bl_idname == bl_idname for node in tree.tree.nodes)


def has_link_to(tree, socket_name):
    return any(link.to_socket.name == socket_name for link in tree.tree.links)


with NodeTreeBuilder("Phase2FieldsTest") as tree:
    mesh = tree.mesh_grid(vertices_x=8, vertices_y=8)
    position = tree.position()
    normal = tree.normal()
    index = tree.index()
    noise = tree.noise(scale=3.0, detail=4.0)
    remapped = tree.map_range(noise, from_min=0.0, from_max=1.0, to_min=-0.2, to_max=0.2)
    offset = tree.vector_scale(normal, remapped)
    moved_position = tree.vector_add(position, (0.0, 0.0, 0.1))
    delta = tree.vector_subtract(moved_position, position)
    summed = tree.float_add(remapped, 1.0)
    scaled = tree.float_multiply(summed, 0.5)
    random_vector = tree.random_vector(seed=12)
    uv = tree.uv_map("UVMap")
    stored = tree.store_named_attribute(mesh, "arrival_weight", scaled, data_type="FLOAT")
    deformed = tree.set_position(stored, offset=offset)
    tree.set_output(deformed)

    assert isinstance(position, Vector)
    assert isinstance(normal, Vector)
    assert isinstance(index, Integer)
    assert isinstance(noise, Float)
    assert isinstance(remapped, Float)
    assert isinstance(offset, Vector)
    assert isinstance(moved_position, Vector)
    assert isinstance(delta, Vector)
    assert isinstance(summed, Float)
    assert isinstance(scaled, Float)
    assert isinstance(random_vector, Vector)
    assert isinstance(uv, Vector)
    assert isinstance(stored, Geometry)
    assert isinstance(deformed, Geometry)

    assert has_node(tree, "GeometryNodeInputPosition")
    assert has_node(tree, "GeometryNodeInputNormal")
    assert has_node(tree, "GeometryNodeInputIndex")
    assert has_node(tree, "ShaderNodeTexNoise")
    assert has_node(tree, "ShaderNodeMapRange")
    assert has_node(tree, "ShaderNodeVectorMath")
    assert has_node(tree, "ShaderNodeMath")
    assert has_node(tree, "FunctionNodeRandomValue")
    assert has_node(tree, "GeometryNodeStoreNamedAttribute")
    assert has_node(tree, "GeometryNodeSetPosition")

    assert has_link_to(tree, "Value")
    assert has_link_to(tree, "Scale")
    assert has_link_to(tree, "Offset")
    assert has_link_to(tree, "Geometry")

print("test_phase2_fields: OK")
