OsmGT
====

![CI](https://github.com/wiralyki/osmgt/workflows/CI/badge.svg?branch=master)
[![codecov](https://codecov.io/gh/wiralyki/osmgt/branch/master/graph/badge.svg)](https://codecov.io/gh/wiralyki/osmgt)


OpenStreetMap based on graph-tools


# Features

* __Find data processing:__
  * ☑ Find all roads network  from a location area
  * ☑ Find all points of interest (POIs) from a location area

* __Topology processing:__
  * ☑ Clean roads network topology
  * ☑ Build topology between roads network and POIs

* __Export processing:__
  * ☑ Create a geodataframe from network and POIs
  * ☑ Create a graph from the clean network topology ; All graph-tool are available on the output graph
  * ☑ Easy matching between graph and geodataframe features
  * ☐  Export data to a binary file 

* __Data viz feature:__
  * ☑ Easy graph plotting
  * ☐ Easy geodataframe plotting

# How to test it 
```
docker build -t osmgt . && docker run -p 8888:8888 osmgt:latest
```

# How to play 
__(TODO)__

check example.ipynb notebook and the svg output


from shapely.geometry import Point

print(len(roads_gdf_split))

columns_without_geometry = roads_gdf_split.columns.tolist()
columns_without_geometry.remove("geometry")

roads_gdf_split["geometry"] = roads_gdf_split["geometry"].apply(lambda x: [Point(f) for f in x.coords])
# print(roads_gdf_split)
roads_gdf_split.set_index(columns_without_geometry, inplace=True)
output = roads_gdf_split["geometry"].explode().reset_index()