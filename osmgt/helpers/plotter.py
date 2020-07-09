from bokeh.plotting import output_notebook
from bokeh.plotting import show

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.tile_providers import get_provider
from bokeh.tile_providers import CARTODBPOSITRON
from bokeh.models import HoverTool

from osmgt.geometry.geom_to_bokeh import geometry_2_bokeh_format


class BokehCore:
    output_notebook()

    def __init__(self, title, width=800, height=600, background_map=CARTODBPOSITRON):
        super().__init__()

        self.plot = figure(
            title=title,
            output_backend="webgl",
            tools="box_select,pan,wheel_zoom,box_zoom,reset,save"
        )

        self.plot.plot_width = width
        self.plot.plot_height = height

        self._add_background_map(background_map)

    def _add_background_map(self, map_name_object):
        tile_provider = get_provider(map_name_object)
        self.plot.add_tile(tile_provider)

    def _bokeh_global_params(self, renderer, features):
        self.plot.legend.click_policy = "hide"

        column_tooltip = self.__build_column_tooltip(features)
        self.plot.add_tools(HoverTool(
            tooltips=column_tooltip,
            renderers=[renderer],
            mode="mouse"
        ))

    def _format_simple_feature(self, feature):
        return ColumnDataSource({
            **{
                "x": feature['geometry'].apply(lambda x: geometry_2_bokeh_format(x, 'x')).tolist(),
                "y": feature['geometry'].apply(lambda x: geometry_2_bokeh_format(x, 'y')).tolist(),

            },
            **{
                column: feature[column].to_list()
                for column in feature.columns
                if column != "geometry"
            }
        })

    def _format_multiple_feature(self, feature):
        return ColumnDataSource({
            **{
                "x": [*feature['geometry'].apply(lambda x: geometry_2_bokeh_format(x, 'x')).tolist()],
                "y": [*feature['geometry'].apply(lambda x: geometry_2_bokeh_format(x, 'y')).tolist()],

            },
            **{
                column: [*feature[column].to_list()]
                for column in feature.columns
                if column != "geometry"
            }
        })

    def add_multi_lines(self, feature, legend, color="blue", line_width=2):
        source_data = self._format_multiple_feature(feature)
        rendered = self.plot.multi_line(
            xs="x",
            ys="y",
            legend_label=legend,
            line_color=color,
            line_width=line_width,
            source=source_data,
        )
        self._bokeh_global_params(rendered, feature)

    def add_lines(self, features, legend, color="blue", line_width=2):
        source_data = self._format_simple_feature(features)
        rendered = self.plot.line(
            x="x",
            y="y",
            legend_label=legend,
            line_color=color,
            line_width=line_width,
            source=source_data,
        )
        self._bokeh_global_params(rendered, features)

    def add_points(self, features, legend, fill_color="red", size=4, style="circle"):
        assert style in self.expected_node_style
        rendered = getattr(self.plot, style)(
            x="x",
            y="y",
            color=fill_color,
            size=size,
            legend_label=legend,
            source=self._format_simple_feature(features)
        )
        self._bokeh_global_params(rendered, features)

    def add_polygons(self, feature, legend, fill_color="red"):
        rendered = self.plot.multi_polygons(
            xs="x",
            ys="y",
            legend_label=legend,
            fill_color=fill_color,
            source=self._format_multiple_feature(feature),
        )
        self._bokeh_global_params(rendered, feature)

    def __build_column_tooltip(self, features):
        columns_filtered = list(filter(lambda x: x != "geometry", features.columns))
        return list(zip(map(lambda x: str(x.upper()), columns_filtered), map(lambda x: f"@{x}", columns_filtered)))

    def show(self):
        show(self.plot)

    @property
    def expected_node_style(self):
        return [
            "asterisk",
            "circle",
            "circle_cross",
            "circle_x",
            "cross",
            "dash",
            "diamond",
            "diamond_cross",
            "hex",
            "inverted_triangle",
            "square",
            "square_cross",
            "square_x",
            "triangle",
            "x",
        ]
