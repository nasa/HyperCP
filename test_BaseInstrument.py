import unittest
from unittest.mock import Mock, patch

import numpy as np

# Source.PIU
import sys
sys.path.append("..")  # Add the parent directory to the path
from Source.PIU.BaseInstrument import BaseInstrument
from Source.PIU.TriOS import TriOS, TriOSUtils
from Source.PIU.HyperOCR import HyperOCR


es_wavebands = [305, 320, 412, 455, 603, 751, 855, 910]
es_light     = [742, 1509, 17999, 30301, 24730, 14401, 5183, 2175]
es_dark      = [500, 500, 500, 500, 5000, 500, 500, 500]
li_wavebands = [307, 322, 413, 454, 606, 752, 851, 908]
li_light     = [1219, 3559, 10750, 13773, 4625, 1863, 1230, 1049]
li_dark      = [980, 980, 980, 980, 980, 980, 980, 980]
lt_wavebands = [308, 324, 415, 455, 604, 756, 849, 906]
lt_light     = [1379, 1685, 7411, 16520, 5980, 1633, 1410, 1343]
lt_dark      = [1300, 1300, 1300, 1300, 1300, 1300, 1300, 1300]
newWaveBands = [310, 325, 412, 460, 625, 750, 800, 855, 900]

from Source.ConfigFile import ConfigFile

mock_HDFGroup = Mock()
mock_xslice = Mock()

class test_baseInstrument(unittest.TestCase):
    # def test_generate_sensor_stats(self):
    #     rawData = {
    #         "ES": None, # mock the groups
    #         "LI": None, 
    #         "LT": None,
    #     }
    #     rawSlice = {
    #         "ES": {
    #             "datetime": [datetime.datetime(2022, 1, 1, 8, i, 0) for i in range(5)],
    #             "data": None,
    #         }, 
    #         "LI": {
    #             "datetime": [datetime.datetime(2022, 1, 1, 8, i, 0) for i in range(5)],
    #             "data": None,
    #         },
    #         "LT": {
    #             "datetime": [datetime.datetime(2022, 1, 1, 8, i, 0) for i in range(5)],
    #             "data": None,
    #         }, 
    #     }
    #     newWaveBands = [400, 500, 600]
    #     # mock lightdarkstats
    #     obj = BaseInstrument()
    #     trios = obj.generateSensorStats("TriOS", rawData, rawSlice, newWaveBands, y)
    #     dalec = obj.generateSensorStats("Dalec", rawData, rawSlice, newWaveBands, y)
    #     pysas = obj.generateSensorStats("SeaBird", rawData, rawSlice, newWaveBands, y)

    @patch('Source.PIU.TriOS.TriOSUtils.readParams')
    @patch.object(ConfigFile, "settings", {"SensorType": "TriOS"})
    def test_stats_trios(self, mock_readParams):
        obj = TriOS() # HDFGroup, XSlice, sensortype
        statsTriOS = {}

        mock_readParams.return_value = (
            0,
            np.array(
                [
                    [0.01440519, 0.02414321],
                    [0.01431442, 0.02393418],
                    [0.0143042 , 0.02411632],
                    [0.01441066, 0.0239055 ],
                    [0.01439108, 0.02414295],
                ]
            ),
            np.array(
                [
                    [1140., 1191., 1298., 689., 711.],
                    [1144., 1193., 1304., 710., 708.],
                    [1140., 1192., 1301., 700., 692.],
                    [1140., 1192., 1301., 698., 701.],
                ]
            ),
            np.array(['305.42', '308.75', '312.08', '315.41', '318.75']),
            np.array(
                [[16], [16], [16], [16], [16]],
            ),
            8192,
            4,
            5,
        )
        statsTriOS["ES"] = obj.lightDarkStats(mock_HDFGroup, mock_xslice, "ES")
        statsTriOS["LI"] = obj.lightDarkStats(mock_HDFGroup, mock_xslice, "LI")
        statsTriOS["LT"] = obj.lightDarkStats(mock_HDFGroup, mock_xslice, "LT")
    
    @patch.object(ConfigFile, "settings", {"SensorType": "TriOS"})
    def test_stats_hyperocr(self):
        obj = HyperOCR() # lightdata, darkdata, sensortype
        obj.cal_int  = {k: 1024 for k in ["ES", "LI", "LT"]}
        obj.int_time = {k: 64 for k in ["ES", "LI", "LT"]}

        statsOCR = {}
        lightData = {}
        darkData = {}
        for i, band in enumerate(es_wavebands):
            lightData[band] = [np.random.uniform(low=es_light[i]-20, high=es_light[i]+20) for _ in range(5)]
            darkData[band] = [np.random.uniform(low=es_dark[i]-2, high=es_dark[i]+2) for _ in range(5)]
        statsOCR["ES"] = obj.lightDarkStats(lightData, darkData, "ES")

        for band in li_wavebands:
            lightData[band] = [np.random.uniform(low=li_light[i]-20, high=li_light[i]+20) for _ in range(5)]
            darkData[band] = [np.random.uniform(low=li_dark[i]-2, high=li_dark[i]+2) for _ in range(5)]
        statsOCR["LI"] = obj.lightDarkStats(lightData, darkData, "LI")

        for band in lt_wavebands:
            lightData[band] = [np.random.uniform(low=lt_light[i]-20, high=lt_light[i]+20) for _ in range(5)]
            darkData[band] = [np.random.uniform(low=lt_dark[i]-2, high=lt_dark[i]+2) for _ in range(5)]
        statsOCR["LT"] = obj.lightDarkStats(lightData, darkData, "LT")

        # assert runs

    def test_FRML2(self):
        pass

    def test_band_conv(self):
        # CB case

        # SB case
        
        pass

    def test_interpolation(self):
        # interp_and_slice_raw_data
        # get_interp_data
        pass

if __name__ == "__main__":
    unittest.main()
