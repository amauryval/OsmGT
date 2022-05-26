from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from graph_tool import Graph
from graph_tool.all import graph_draw
from graph_tool.draw import sfdp_layout

import collections

class ErrorGraphHelpers(ValueError):
    pass


class ExistingVertex(ValueError):
    pass


class GraphHelpers(Graph):
    """Graph with named edges and vertices (unique),
     can have multiple edges between 2 vertices

    - infos()
    - add_vertex()
    - find_vertex_from_name()
    - vertex_exists_from_name()
    - add_edge()
    - find_edge_from_name()
    - edge_exists_from_name()
    - find_edge_from_vertices_name()
    - edge_exists_from_vertices_name()
    - find_edges_from_vertex()
    - find_vertex_names_from_edge_name()
    """

    __slots__ = (
        "_logger",
        "vertex_names",
        "edge_names",
        "edge_weights",
        "vertices_content",
        "edges_content",
    )

    def __init__(self, logger, is_directed: bool = True) -> None:
        """
        :param logger: logger
        :type logger:
        :param is_directed: is directed or not
        :type is_directed: bool
        """
        super(GraphHelpers, self).__init__(directed=is_directed)

        self._logger = logger
        self.vertex_names = self.new_vertex_property("string")
        self.edge_names = self.new_edge_property("string")

        self.edge_weights = self.new_edge_property("double")

        self.vertices_content: Dict = collections.defaultdict(lambda: None)
        self.edges_content: Dict = collections.defaultdict(lambda: None)

    def find_edges_from_vertex(self, vertex_name: str) -> List[str]:
        vertex = self.find_vertex_from_name(vertex_name)
        if vertex is not None:
            all_edges_found = vertex.all_edges()
            edges_names = [self.edge_names[edge] for edge in all_edges_found]
            edges_exist = list(map(self.edge_exists_from_name, edges_names))
            if all(edges_exist):
                return edges_names
            else:
                raise ErrorGraphHelpers("Seems impossible ?")

    def find_vertex_names_from_edge_name(
        self, edge_name: str
    ) -> Optional[Tuple[str, str]]:
        edge = self.find_edge_from_name(edge_name)
        if edge is not None:

            vertex_source_name = self.vertex_names[edge.source()]
            vertex_target_name = self.vertex_names[edge.target()]

            if all(
                [
                    self.vertex_exists_from_name(vertex_source_name),
                    self.vertex_exists_from_name(vertex_source_name),
                ]
            ):
                return vertex_source_name, vertex_target_name
            else:
                # if an edge exists, it must have source and target nodes
                raise ErrorGraphHelpers("Seems impossible ?")

        return None

    def add_vertex(self, vertex_name: str):
        """
        Add a vertex

        :param vertex_name: vertex name
        :type vertex_name: str
        :return: vertex object
        :rtype: graph_tool.libgraph_tool_core.Vertex
        :raises ExistingVertex: if the vertex already exists
        """

        if self.vertex_exists_from_name(vertex_name):
            raise ExistingVertex(f"Vertex {vertex_name} already exists")

        vertex = super(GraphHelpers, self).add_vertex()
        self.vertex_names[vertex] = vertex_name
        self.vertices_content[vertex_name] = vertex

        return vertex

    def add_edge(
        self,
        source_vertex_name: str,
        target_vertex_name: str,
        edge_name: str,
        weight: Optional[float] = None,
    ):
        """
        Add an edge from 2 vertex name

        :param source_vertex_name: source vertex name
        :type source_vertex_name: str
        :param target_vertex_name: target vertex name
        :type target_vertex_name: str
        :param edge_name: edge name
        :type edge_name: str
        :param weight: weight value
        :type weight: float, default None
        :return: Edge object
        :rtype: graph_tool.libgraph_tool_core.Edge
        :raises ExistingEdge: if the vertex already exists
        """

        is_edge_exists = self.edge_exists_from_name(edge_name)
        if not is_edge_exists:

            source = self.find_vertex_from_name(source_vertex_name)
            if not source:
                source = self.add_vertex(source_vertex_name)

            target = self.find_vertex_from_name(target_vertex_name)
            if not target:
                target = self.add_vertex(target_vertex_name)

            edge = super(GraphHelpers, self).add_edge(source, target)
            self.edge_names[edge] = edge_name
            self.edges_content[edge_name] = edge

            if weight is not None:
                self.edge_weights[edge] = weight

            return edge

        else:
            print(f"Edge {edge_name} already exists")

            return None



    def find_edge_from_name(self, edge_name: str):
        """
        Find an edge

        :param edge_name: edge name
        :type edge_name: str
        :return: Edge object
        :rtype: graph_tool.libgraph_tool_core.Edge
        """
        return self.edges_content[str(edge_name)]


    def edge_exists_from_name(self, edge_name: str):
        """
        check if an edge exists

        :param edge_name: edge name
        :type edge_name: str
        :return: is edge name exists
        :rtype: bool
        """
        return self.find_edge_from_name(edge_name) is not None

    def find_edge_from_vertices_name(
        self, source_vertex_name: str, target_vertex_name: str
    ):
        """
        Find an edge with its vertices names

        :param source_vertex_name: source vertex name
        :type source_vertex_name: str
        :param target_vertex_name: target vertex name
        :type target_vertex_name: str
        :return: Edge object
        :rtype: graph_tool.libgraph_tool_core.Edge
        """
        source_vertex_found = self.find_vertex_from_name(source_vertex_name)
        target_vertex_found = self.find_vertex_from_name(target_vertex_name)

        if not all([source_vertex_found, target_vertex_found]):
            return None

        return self.edge(source_vertex_found, target_vertex_found)

    def edge_exists_from_vertices_name(
        self, source_vertex_name: str, target_vertex_name: str
    ):
        """
        Find if an edge with specific vertices names

        :param source_vertex_name: source vertex name
        :type source_vertex_name: str
        :param target_vertex_name: target vertex name
        :type target_vertex_name: str
        :return: if an edge exists between 2 specific vertices
        :rtype: bool
        """
        return (
            self.find_edge_from_vertices_name(source_vertex_name, target_vertex_name)
            is not None
        )

    def find_vertex_from_name(self, vertex_name: str):
        """
        find a vertex

        :param vertex_name: vertex name
        :type vertex_name: str
        :return: vertex object or none if not exists
        :rtype: graph_tool.libgraph_tool_core.Vertex or None
        """

        return self.vertices_content[vertex_name]


    def vertex_exists_from_name(self, vertex_name: str) -> bool:
        """
        check if a vertex exists

        :param vertex_name: vertex name
        :type vertex_name: str
        :return: is vertex exists
        :rtype: bool
        """

        return self.find_vertex_from_name(vertex_name) is not None

    def plot(self, output_file_with_extension: Optional[str] = None):
        """
        To return a graph image

        :param output_file_with_extension: the output file name with extension
        :return: str
        """
        self._logger.info("Graph to image")
        pos = sfdp_layout(self)
        graph_draw(
            self,
            pos=pos,
            vertex_shape="circle",
            vertex_size=3,
            vertex_anchor=0,
            vertex_color="white",
            vertex_fill_color=(0, 0, 0, 1),  # normalized values
            vertex_pen_width=1,
            edge_color=(1, 0, 0, 1),
            bg_color=(0, 0, 0, 1),
            output_size=[1024, 1024],
            output=output_file_with_extension,
        )
