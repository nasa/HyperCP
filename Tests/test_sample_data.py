import os
import glob
import unittest


os.environ["HYPERINSPACE_CMD"] = "TRUE"
root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))


class TestManualTriOS(unittest.TestCase):
    def setUp(self):
        # Load files to process
        self.path_to_data = os.path.join(root, 'Data', 'Sample_Data', 'Manual_TriOS')
        self.anc_filename = os.path.join(self.path_to_data, f"FICE22_TriOS_Ancillary.sb")
        self.cfg_filename = os.path.join(root, "Config", "sample_TRIOS_NOTRACKER.cfg")
        self.files = sorted(glob.glob(os.path.join(self.path_to_data, 'RAW', f'*.mlb')))

    def test_manual_trios(self):
        from Main import Command
        os.chdir(root)  # Need to switch to root as path in Config files are relative
        Command(self.cfg_filename, 'RAW', self.files, self.path_to_data,'L1A',
                self.anc_filename, processMultiLevel=True)


class TestPySAS(unittest.TestCase):
    def setUp(self):
        # Load files to process
        self.path_to_data = os.path.join(root, 'Data', 'Sample_Data', 'pySAS')
        self.anc_filename = os.path.join(self.path_to_data, f"FICE22_pySAS_Ancillary.sb")
        self.cfg_filename = os.path.join(root, "Config", "sample_SEABIRD_pySAS.cfg")
        self.files = sorted(glob.glob(os.path.join(self.path_to_data, 'RAW', f'*.raw')))

    def test_pysas(self):
        from Main import Command
        os.chdir(root)  # Need to switch to root as path in Config files are relative
        for file in self.files:
            Command(self.cfg_filename, 'RAW', file, self.path_to_data,'L1A',
                    self.anc_filename, processMultiLevel=True)


class TestSeabirdSolarTracker(unittest.TestCase):
    def setUp(self):
        # Load files to process
        self.path_to_data = os.path.join(root, 'Data', 'Sample_Data', 'SolarTracker')
        self.anc_filename = os.path.join(self.path_to_data, f"KORUS_SOLARTRACKER_Ancillary.sb")
        self.cfg_filename = os.path.join(root, "Config", "sample_SEABIRD_SOLARTRACKER.cfg")
        self.files = sorted(glob.glob(os.path.join(self.path_to_data, 'RAW', f'*.RAW')))

    def test_pysas(self):
        from Main import Command
        os.chdir(root)  # Need to switch to root as path in Config files are relative
        for file in self.files:
            Command(self.cfg_filename, 'RAW', file, self.path_to_data,'L1A',
                    self.anc_filename, processMultiLevel=True)


if __name__ == '__main__':
    unittest.main()
