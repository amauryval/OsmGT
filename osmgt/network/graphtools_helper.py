from graph_tool import Graph
from graph_tool.all import graph_draw
from graph_tool.draw import sfdp_layout


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
    """

    def __init__(self, directed):
        """

        :param directed: is directed or not
        :type directed: bool
        """
        super(GraphHelpers, self).__init__(directed=directed)

        self.vertex_names = self.new_vertex_property('string')
        self.edge_names = self.new_edge_property('string')

        self.edge_weights = self.new_edge_property('double')

        self.vertices_content = {}
        self.edges_content = {}

    def add_vertex(self, vertex_name):
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

    def add_edge(self, source_vertex_name, target_vertex_name, edge_name, weight=None):
        """
        Add an edge from 2 vertex name

        :param source_vertex_name: source vertex name
        :type source_vertex_name: str
        :param target_vertex_name: target vertex name
        :type target_vertex_name: str
        :param edge_name: edge name
        :type edge_name: str
        :param weight: wieght value
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

    def find_edge_from_name(self, edge_name):
        """
        Find an edge

        :param edge_name: edge name
        :type edge_name: str
        :return: Edge object
        :rtype: graph_tool.libgraph_tool_core.Edge
        """
        try:
            return self.edges_content[str(edge_name)]
        except KeyError:
            return None

    def edge_exists_from_name(self, edge_name):
        """
        check if an edge exists

        :param edge_name: edge name
        :type edge_name: str
        :return: is edge name exists
        :rtype: bool
        """
        return self.find_edge_from_name(edge_name) is not None

    def find_edge_from_vertices_name(self, source_vertex_name, target_vertex_name):
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

    def edge_exists_from_vertices_name(self, source_vertex_name, target_vertex_name):
        """
        Find if an edge with specific vertices names

        :param source_vertex_name: source vertex name
        :type source_vertex_name: str
        :param target_vertex_name: target vertex name
        :type target_vertex_name: str
        :return: if an edge exists between 2 specific vertices
        :rtype: bool
        """
        return self.find_edge_from_vertices_name(
            source_vertex_name,
            target_vertex_name
        ) is not None

    def find_vertex_from_name(self, vertex_name):
        """
        find a vertex

        :param vertex_name: vertex name
        :type vertex_name: str
        :return: vertex object or none if not exists
        :rtype: graph_tool.libgraph_tool_core.Vertex or None
        """

        try:
            return self.vertices_content[vertex_name]
        except KeyError:
            return None

    def vertex_exists_from_name(self, vertex_name):
        """
        check if a vertex exists

        :param vertex_name: vertex name
        :type vertex_name: str
        :return: is vertex exists
        :rtype: bool
        """

        return self.find_vertex_from_name(vertex_name) is not None

    def plot(self, output_file_with_extension):
        pos = sfdp_layout(self)
        graph_draw(
            self,
            pos=pos,
            vertex_shape="circle",
            vertex_size=3,
            vertex_anchor=0,
            vertex_color="white",
            vertex_fill_color=(1, 0, 0, 1),  # normalized values
            vertex_pen_width=0.7,
            edge_color=(1, 0, 0, 1),
            bg_color=(0, 0, 0, 1),
            output_size=[1024,1024],
            output=output_file_with_extension
        )
