from osmgt import OsmGt
from shapely.geometry import Point


def test_from_web():
    location = "lyon"
    poi_output_name = f"{location}_poi"
    network_output_name = f"{location}_network"
    # bbox = (-74.018433, 40.718087, -73.982749, 40.733356)

    # get POI
    poi_from_web_found = OsmGt.poi_from_location(location)
    # poi_from_web_found = OsmGt.poi_from_bbox(bbox)

    # poi_from_osmgt_file_found = OsmGt.roads_from_osmgt_file(f"{poi_output_name}.osmgt")
    poi_gdf = poi_from_web_found.get_gdf()[
        ["topo_uuid", "id", "name", "amenity", "geometry", "osm_url"]
    ]
    poi_gdf.to_file(f"{poi_output_name}.shp", driver="ESRI Shapefile")

    # get NETWORK
    network_from_web_found = OsmGt.roads_from_location(
        location, additionnal_nodes=poi_gdf, mode="vehicle"
    )
    # network_from_web_found = OsmGt.roads_from_bbox(bbox, additionnal_nodes=poi_gdf, mode="vehicle")

    network_from_osmgt_file_found = network_from_web_found.get_gdf()[
        ["topo_uuid", "id", "name", "highway", "geometry", "topology", "osm_url"]
    ]
    print("ok")
    network_from_osmgt_file_found.to_file(
        f"{network_output_name}.shp", driver="ESRI Shapefile"
    )
    assert True


def test_from_file():
    poi_from_file_found = OsmGt.poi_from_file("Roanne_poi.shp", "id").get_gdf()
    network_from_file_found = OsmGt.network_from_file(
        "Roanne_network.shp", "id", poi_from_file_found
    )
    network_from_file_found
    assert False


# location_point = Point(4.0697088, 46.0410178)
# isochrones_from_location = OsmGt.isochrone_from_coordinates(
#     location_point, [2, 5, 10], 3, mode="pedestrian"
# )

test_from_web()
# test_from_file()
assert True
