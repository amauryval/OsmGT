import pytest

from osmgt.network.graphtools_helper import GraphHelpers
from osmgt.network.graphtools_helper import ExistingVertex


def test_create_vertices(point_a, point_b):
    graph = GraphHelpers(directed=False)

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
    graph = GraphHelpers(directed=False)

    edge_1 = graph.add_edge(point_a.wkt, point_b.wkt, 'edge_1')
    assert edge_1 is not None

    edge_2 = graph.add_edge(point_b.wkt, point_c.wkt, 'edge_2')

    edge_3 = graph.add_edge(point_b.wkt, point_c.wkt, 'edge_2')
    assert edge_3 is None

    assert edge_2 == graph.find_edge_from_name('edge_2')
    assert graph.edge_exists_from_name('edge_2')

    assert edge_2 == graph.find_edge_from_vertices_name(point_b.wkt, point_c.wkt)
    assert graph.edge_exists_from_vertices_name(point_b.wkt, point_c.wkt)
    assert not graph.edge_exists_from_vertices_name(point_a.wkt, point_c.wkt)

    assert graph.edges_content().shape[0] == 2
    assert graph.vertices_content().shape[0] == 3

def test_edges_with_a_weighted_undirected_graph(point_a, point_b, point_c):
    graph = GraphHelpers(directed=False)

    edge_1 = graph.add_edge(point_a.wkt, point_b.wkt, 'edge_1', 10.2)
    assert edge_1 is not None

    edge_2 = graph.add_edge(point_b.wkt, point_c.wkt, 'edge_2', 15.9)

    edge_3 = graph.add_edge(point_b.wkt, point_c.wkt, 'edge_2', 25)
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

    assert graph.edges_content().shape[0] == 2
    assert graph.vertices_content().shape[0] == 3