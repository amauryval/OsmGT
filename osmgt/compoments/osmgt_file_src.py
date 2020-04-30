import os

import pickle


from shapely.geometry import LineString

from osmgt.compoments.osmgt_core import OsmGtCore

from osmgt.geometry.reprojection import ogr_reproject


class OsmgtFileSource(OsmGtCore):

    def __init__(self, osmgt_input_file_path):
        super().__init__()

        self._osmgt_input_file_path = osmgt_input_file_path

    def get_data_from_osmgt_file(self):
        # TODO check variable

        input_file_name = os.path.splitext(os.path.basename(self._osmgt_input_file_path))[0]
        self._format_output_file_name(input_file_name)
        self._OUTPUT = self.__open_from_pikle_file(self._osmgt_input_file_path)

        return self

    def __open_from_pikle_file(self, pikle_file_path):
        self.logger.info("Opening from pikle file...")

        with open(pikle_file_path, "rb") as input:
            input_data = pickle.load(input)

        return input_data
