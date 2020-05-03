import pytest

from osmgt.network.gt_helper import GraphHelpers
from osmgt.network.gt_helper import ExistingVertex


def create_undirected_graph(point_a, point_b, point_c):
    graph = GraphHelpers()
    edge_1 = graph.add_edge(point_a.wkt, point_b.wkt, "edge_1")
    edge_2 = graph.add_edge(point_b.wkt, point_c.wkt, "edge_2")
    edge_3 = graph.add_edge(point_b.wkt, point_c.wkt, 'edge_2')

    return graph, edge_1, edge_2, edge_3


def create_weighted_undirected_graph(point_a, point_b, point_c):
    graph = GraphHelpers()
    edge_1 = graph.add_edge(point_a.wkt, point_b.wkt, "edge_1", 10.2)
    edge_2 = graph.add_edge(point_b.wkt, point_c.wkt, "edge_2", 15.9)
    edge_3 = graph.add_edge(point_b.wkt, point_c.wkt, 'edge_2', 25)

    return graph, edge_1, edge_2, edge_3


def test_create_vertices(point_a, point_b):
    graph = GraphHelpers()

    vertex_a = graph.add_vertex(point_a.wkt)
    vertex_b = graph.add_vertex(point_b.wkt)

    assert vertex_a is not None
    assert vertex_b is not None

    with pytest.raises(ExistingVertex):
        _ = graph.add_vertex(point_b.wkt)

    assert vertex_b == graph.find_vertex_from_name(point_b.wkt)
    assert graph.vertex_exists_from_name(point_b.wkt)
    assert not graph.vertex_exists_from_name('Hello ?')


def test_create_edges_with_an_undirected_graph(point_a, point_b, point_c):
    graph, edge_1, edge_2, edge_3 = create_undirected_graph(point_a, point_b, point_c)

    assert edge_1 is not None

    assert edge_3 is None

    assert edge_2 == graph.find_edge_from_name('edge_2')
    assert graph.edge_exists_from_name('edge_2')

    assert edge_2 == graph.find_edge_from_vertices_name(point_b.wkt, point_c.wkt)
    assert graph.edge_exists_from_vertices_name(point_b.wkt, point_c.wkt)
    assert not graph.edge_exists_from_vertices_name(point_a.wkt, point_c.wkt)


def test_edges_with_a_weighted_undirected_graph(point_a, point_b, point_c):
    graph, edge_1, edge_2, edge_3 = create_weighted_undirected_graph(point_a, point_b, point_c)

    assert edge_1 is not None
    assert edge_3 is None

    assert edge_2 == graph.find_edge_from_name('edge_2')
    assert graph.edge_exists_from_name('edge_2')

    assert edge_2 == graph.find_edge_from_vertices_name(point_b.wkt, point_c.wkt)
    assert graph.edge_exists_from_vertices_name(point_b.wkt, point_c.wkt)
    assert not graph.edge_exists_from_vertices_name(point_a.wkt, point_c.wkt)

    assert sum([
        graph.edge_weights[edge]
        for edge in graph.edges()
    ]) == 26.1


def test_find_vertices_from_edge(point_a, point_b, point_c):
    graph, _, _, _ = create_weighted_undirected_graph(point_a, point_b, point_c)

    vertices = graph.find_vertex_names_from_edge_name("edge_1")
    assert vertices[0] == point_a.wkt
    assert vertices[-1] == point_b.wkt

    vertices = graph.find_vertex_names_from_edge_name("edge_2")
    assert vertices[0] == point_b.wkt
    assert vertices[-1] == point_c.wkt

    vertices = graph.find_vertex_names_from_edge_name("edge_3")
    assert vertices is None


def test_find_edges_from_vertex(point_a, point_b, point_c):
    graph, _, _, _ = create_undirected_graph(point_a, point_b, point_c)

    edges_found = graph.find_edges_from_vertex(point_b.wkt)
    assert set(edges_found) == {"edge_1", "edge_2"}