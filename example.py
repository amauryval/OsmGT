import geopandas

from osmgt import OsmGt

roanne_new_points = [
    {"geometry": (4.0671, 46.0364), "tags": {"value": 5}},
    {"geometry": (4.0673379313728617, 46.03655443159822624), "tags": {"value": 10}},
    {"geometry": (4.06656361310282666, 46.03683579838379103), "tags": {"value": 1}},
    {"geometry": (4.06664460157913865, 46.03671836509313664), "tags": {"value": 2}},
]

lyon_new_points = [
    {"geometry": (4.83282848269435039, 45.75813237931674848), "tags": {"value": 10}},
    {"geometry": (4.83298239951893827, 45.75810561117334174), "tags": {"value": 1}},
    {"geometry": (4.83314077770076089, 45.75808107370855282), "tags": {"value": 2}},
]
def test_from_web():
    location = "lyon"
    poi_output_name = f"{location}_poi"
    network_output_name = f"{location}_network"

    # get POI
    poi_from_web_found = OsmGt.poi_from_location(location)
    # poi_from_web_found.export_to_osmgt_file(poi_output_name)

    # poi_from_osmgt_file_found = OsmGt.roads_from_osmgt_file(f"{poi_output_name}.osmgt")
    poi_gdf = poi_from_web_found.get_gdf()[["topo_uuid", "id", "name", "amenity", "geometry", "bounds"]]
    poi_gdf.to_file(f"{poi_output_name}.shp", driver="ESRI Shapefile")

    # get NETWORK
    network_from_web_found = OsmGt.roads_from_location(location, poi_gdf)
    # network_from_web_found.export_to_osmgt_file(network_output_name)

    # network_from_osmgt_file_found = OsmGt.roads_from_osmgt_file(
    #     f"{network_output_name}.osmgt"
    # )

    network_from_osmgt_file_found = network_from_web_found.get_gdf()[["topo_uuid", "id", "name", "highway", "geometry", "topology"]]

    network_from_osmgt_file_found.to_file(
        f"{network_output_name}.shp", driver="ESRI Shapefile"
    )

def test_from_file():
    poi_from_file_found = OsmGt.poi_from_file("Roanne_poi.shp", "id").get_gdf()
    network_from_file_found = OsmGt.network_from_file("Roanne_network.shp", "id", poi_from_file_found)
    assert False

test_from_web()
# test_from_file()
assert True
