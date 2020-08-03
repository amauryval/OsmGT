import geopandas

from osmgt import OsmGt

def test_from_web():
    location = "lyon"
    poi_output_name = f"{location}_poi"
    network_output_name = f"{location}_network"
    bbox = (40.718087, -74.018433, 40.733356, -73.982749)

    # get POI
    poi_from_web_found = OsmGt.poi_from_location(location)
    # poi_from_web_found = OsmGt.poi_from_bbox(bbox)
    # poi_from_web_found.export_to_osmgt_file(poi_output_name)

    # poi_from_osmgt_file_found = OsmGt.roads_from_osmgt_file(f"{poi_output_name}.osmgt")
    poi_gdf = poi_from_web_found.get_gdf()[["topo_uuid", "id", "name", "amenity", "geometry", "bounds"]]
    poi_gdf.to_file(f"{poi_output_name}.shp", driver="ESRI Shapefile")

    # get NETWORK
    network_from_web_found = OsmGt.roads_from_location(location, poi_gdf)
    # network_from_web_found = OsmGt.roads_from_bbox(bbox, poi_gdf)

    # network_from_web_found.export_to_osmgt_file(network_output_name)

    # network_from_osmgt_file_found = OsmGt.roads_from_osmgt_file(
    #     f"{network_output_name}.osmgt"
    # )

    network_from_osmgt_file_found = network_from_web_found.get_gdf()[["topo_uuid", "id", "name", "highway", "geometry", "topology"]]
    print("ok")
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
