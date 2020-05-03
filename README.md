OsmGT
==
OpenStreetMap based on graph-tools


# Features

* __Find data processing:__
  * ✅ Find all roads network  from a location area (__(TODO)__ describe query)
  * ✅ Find all points of interest (POIs) from a location area (__(TODO)__ describe query)

* __Topology processing:__
  * ✅ Clean roads network topology
  * ✅ Build topology between roads network and POIs

* __Export processing:__
  * ✅ Create a geodataframe from network and POIs
  * ✅ Create a graph from the clean network topology ; All graph-tool are available on the output graph
  * ✅ Easy matching between graph and geodataframe features
  * ❌ __(TODO)__ Export data to a binary file 

* __Data viz feature:__
  * ✅ Easy graph plotting
  * ❌ Easy geodataframe plotting

# How to test it 
```
docker build -t osmgt . && docker run -p 8888:8888 osmgt:latest
```

# How to play 
__(TODO)__

check example.ipynb notebook and the svg output
