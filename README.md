OsmGT
====

![CI](https://github.com/wiralyki/osmgt/workflows/CI/badge.svg?branch=master)
[![codecov](https://codecov.io/gh/wiralyki/osmgt/branch/master/graph/badge.svg)](https://codecov.io/gh/wiralyki/osmgt)


OpenStreetMap based on graph-tools

# How to install it 
```
conda install -c amauryval osmgt
```


# How to test it 
```
docker build -t osmgt . && docker run -p 8888:8888 osmgt:latest
```

check example.html example (doc is coming)
