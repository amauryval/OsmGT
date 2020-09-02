OsmGT
====

![CI](https://github.com/amauryval/osmgt/workflows/CI/badge.svg?branch=master)
[![codecov](https://codecov.io/gh/amauryval/osmgt/branch/master/graph/badge.svg)](https://codecov.io/gh/wiralyki/osmgt)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

[![Anaconda-Server Badge](https://anaconda.org/amauryval/osmgt/badges/version.svg)](https://anaconda.org/amauryval/osmgt)
[![Anaconda-Server Badge](https://anaconda.org/amauryval/osmgt/badges/latest_release_date.svg)](https://anaconda.org/amauryval/osmgt)

[![Anaconda-Server Badge](https://anaconda.org/amauryval/osmgt/badges/platforms.svg)](https://anaconda.org/amauryval/osmgt)

[![Anaconda-Server Badge](https://anaconda.org/amauryval/osmgt/badges/installer/conda.svg)](https://conda.anaconda.org/amauryval)


OpenStreetMap (OSM) network analysis based on [graph-tools](https://graph-tool.skewed.de/) (GT): 
* Find data (roads and pois)
* graph creation (and topology processing)
* isochrone builder
* shortest path 

# Check the jupyter notebook output

[Open the example](https://amauryval.github.io/osmgt/)


# How to install it 

Only on Linux

```
conda install -c amauryval osmgt
```

# A (very) short documentation...

Check example.html example (doc is coming)

# How to run the dockerfile 
```
docker build -t osmgt . && docker run -p 8888:8888 osmgt:latest
```