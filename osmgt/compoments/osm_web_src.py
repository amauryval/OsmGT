from osmgt.apis.nominatim import NominatimApi
from osmgt.apis.overpass import OverpassApi

from osmgt.compoments.osmgt_core import OsmGtCore

from osmgt.geometry.reprojection import ogr_reproject
from osmgt.geometry.geom_network_cleaner import GeomNetworkCleaner

from shapely.geometry import LineString


class OsmGtWebSource(OsmGtCore):

    def __init__(self, location_name, additionnal_points=None):
        super().__init__()

        self._location_name = location_name
        self._additionnal_points = additionnal_points

    def get_data_from_osm(self):
        # TODO check variables

        self.logger.info(f"Working location: {self._location_name}")
        self.logger.info("Loading Data...")

        self._format_output_file_name(self._location_name.lower())

        location_id = NominatimApi(self.logger, q=self._location_name, limit=1).data()[0]["osm_id"]
        location_id += self.location_osm_default_id
        raw_data = OverpassApi(self.logger, location_osm_id=location_id).data()["elements"]
        raw_data_restructured = self.__prepare_network_to_be_cleaned(raw_data)
        self._output_data = GeomNetworkCleaner(self.logger, raw_data_restructured, self._additionnal_points).run()

        return self

    def __prepare_network_to_be_cleaned(self, raw_data):
        self.logger.info("Formating data")

        raw_data = filter(lambda x: x["type"] == "way", raw_data)
        raw_data_reprojected = []
        for feature in raw_data:
            try:
                feature["geometry"] = ogr_reproject(
                    LineString([(coords["lon"], coords["lat"]) for coords in feature["geometry"]]),
                    self.epsg_4236, self.epsg_3857
                )

            except:
                feature["geometry"] = LineString([(coords["lon"], coords["lat"]) for coords in feature["geometry"]])

            feature["bounds"] = feature["geometry"].bounds
            feature["geometry"] = feature["geometry"].coords[:]

            raw_data_reprojected.append(feature)

        return raw_data_reprojected
