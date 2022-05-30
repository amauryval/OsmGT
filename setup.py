from setuptools import setup, find_packages

# used by meta.yaml, do not forget space
requirements = [
    "geopandas >=0.10.2",
    "requests >=2.26.0",
    "numpy >=1.21.3",
    "geojson >=2.5.0",
    "python-dateutil >=2.8.2",
    "graph-tool >=2.43",
    "cairo >=1.16.0",
    "scipy >=1.7.1",
    "more-itertools >=8.10.0",
    "numba >=0.53.1",
    "requests-futures >=1.0.0",
    "pygeos >=0.10.2"
]

setup_requirements = []

test_requirements = []

setup(
    author="amauryval",
    author_email='amauryval@gmail.com',
    url="https://github.com/amauryval/osmgt",
    version='0.9.0',
    description="A library to play with OSM roads (and POIs) data using graph tool network library",
    entry_points={},
    install_requires=requirements,
    license="GPL3",
    long_description="",
    include_package_data=True,
    keywords='network POIS roads shortest_path isochrone',
    name='osmgt',
    packages=find_packages(include=["osmgt", "osmgt.*"]),
    # setup_requires=setup_requirements,
    test_suite='tests',
    # tests_require=test_requirements,
    zip_safe=False,
    python_requires=">=3.9",
)
