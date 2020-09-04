from typing import List

osm_url = "https://www.openstreetmap.org"

epsg_4326: str = "4326"
epsg_3857: str = "3857"

km_hour_2_m_sec: float = 3.6
min_2_sec: float = 60
time_unit: str = "minutes"

# transport modes
transport_modes: List[str] = ["vehicle", "pedestrian"]

# direction tags
forward_tag: str = "forward"
backward_tag: str = "backward"

# topology
topology_fields: List[str] = ["topo_uuid", "id", "topology", "osm_url", "geometry"]

# POIs overpass query
poi_query: str = (
    'node[~"^(amenity)$"~"('
    "bar|biergarten|cafe|drinking_water|fast_food|ice_cream|food_court|pub|restaurant|college|driving_school"
    "|kindergarten|language_school|library|music_school|school|sport_school|toy_library|university|	"
    "bicycle_parking|bicycle_repair_station|bicycle_rental|boat_rental|boat_sharing|	"
    "bus_station|car_rental|car_sharing|car_wash|vehicle_inspection|charging_station|ferry_terminal|fuel|taxi|	"
    "atm|bank|bureau_de_change|baby_hatch|clinic|doctors|dentist|hospital|nursing_home|pharmacy|social_facility"
    "|veterinary|arts_centre|brothel|casino|cinema|community_centre|gambling|nightclub|planetarium|	"
    "public_bookcase|social_centre|stripclub|studio|bicycle_parking|bicycle_rental|swingerclub|theatre|animal_boarding"
    "|animal_shelter|conference_centre|courthouse|	"
    "crematorium|dive_centre|embassy|fire_station|give_box|internet_cafe|monastery|photo_booth|place_of_worship|police"
    "|post_box|post_depot|post_office|prison|public_bath|ranger_station|recycling|refugee_site|	"
    "sanitary_dump_station|shelter|shower|telephone|toilets|townhall|vending_machine|waste_basket|waste_disposal"
    "|waste_transfer_station|watering_place|water_point"
    ')"]({geo_filter});'
    'node[~"^(shop)$"~"."]({geo_filter});'
)

out_geom_query: str = "out geom;(._;>;)"

# network overpass queries
network_queries: dict = {
    "vehicle": {
        "query": 'way["highway"~"^('
        "motorway|"
        "trunk|"
        "primary|"
        "secondary|"
        "tertiary|"
        "unclassified|"
        "residential|"
        "pedestrian|"
        "motorway_link|"
        "trunk_link|"
        "primary_link|"
        "secondary_link|"
        "tertiary_link|"
        "living_street|"
        "service|"
        "track|"
        "bus_guideway|"
        "escape|"
        "raceway|"
        "road|"
        "bridleway|"
        "corridor|"
        "path"
        ')$"]["area"!~"."]({geo_filter});',
        "directed_graph": True,
    },
    "pedestrian": {
        "query": 'way["highway"~"^('
        "motorway|"
        "cycleway|"
        "primary|"
        "secondary|"
        "tertiary|"
        "unclassified|"
        "residential|"
        "pedestrian|"
        "motorway_link|"
        "primary_link|"
        "secondary_link|"
        "tertiary_link|"
        "living_street|"
        "service|"
        "track|"
        "bus_guideway|"
        "escape|"
        "road|"
        "footway|"
        "bridleway|"
        "steps|"
        "corridor|"
        "path"
        ')$"]["area"!~"."]({geo_filter});',
        "directed_graph": False,
    },
}
