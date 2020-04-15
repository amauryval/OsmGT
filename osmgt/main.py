from osmgt.apis.nominatim import NominatimApi
from osmgt.apis.overpass import OverpassApi


class OsmGt:


    @staticmethod
    def get_graph_from_location(location_name):
        """
        get a graph tool graph from a location name

        :param location_name: the location name
        :type location_name: str
        :return:
        """
        location_osm_id = NominatimApi(q=location_name, limit=1).data()[0]["osm_id"]
        location_osm_id += 3600000000
        query = f'area({location_osm_id})->.searchArea;(way["highway"](area.searchArea););out geom;(._;>;);'
        return OverpassApi(query).to_graph()
