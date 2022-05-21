OsmGT
====

![CI](https://github.com/amauryval/osmgt/workflows/CI/badge.svg?branch=master)
[![codecov](https://codecov.io/gh/amauryval/osmgt/branch/master/graph/badge.svg)](https://codecov.io/gh/amauryval/osmgt)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

[![Anaconda-Server Badge](https://anaconda.org/amauryval/osmgt/badges/version.svg)](https://anaconda.org/amauryval/osmgt)
[![Anaconda-Server Badge](https://anaconda.org/amauryval/osmgt/badges/latest_release_date.svg)](https://anaconda.org/amauryval/osmgt)

[![Anaconda-Server Badge](https://anaconda.org/amauryval/osmgt/badges/platforms.svg)](https://anaconda.org/amauryval/osmgt)

[![Anaconda-Server Badge](https://anaconda.org/amauryval/osmgt/badges/installer/conda.svg)](https://conda.anaconda.org/amauryval)


OpenStreetMap (OSM) network analysis based on [graph-tools](https://graph-tool.skewed.de/) (GT): 
* load data from a location name or a bounding box (roads and pois)
* graph creation (and topology processing)
* isochrone builder
* shortest path 


## Demo

To play with the notebook on binder: [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/amauryval/osmgt/master?filepath=example.ipynb)

If you do not want to wait (OsmGt docker building takes time here on myBinder), you can find the html version of the jupyter notebook : click [here](https://amauryval.github.io/osmgt/) to get the result


# Documentation

[Open the wiki](https://github.com/amauryval/osmgt/wiki/OsmGT-Wiki)

# Releases

- 0.8.12:

Code cleaning...


- 0.8.4:

First usable version


# How to install it 

Only on Linux

```
conda install -c amauryval osmgt
```

# How to run the dockerfile 
```
docker build -t osmgt . && docker run -p 8888:8888 osmgt:latest
```
