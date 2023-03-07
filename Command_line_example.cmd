# Command for the community processor

---
## Guide

### Quick Start Overview
1. Identify the research cruise, relevant calibration files, and ancillary data files to be used in processing.
2. Setup configuration file with wanted instrument: Seabird or Trios (it is recommended to have 2 separated configuration files, one for each instrument)
3. Add and enable only *relevant* calibration and instrument files to the Configuration; there is no such thing as a standard instrument package.
4. Choose appropriate processing parameters for L1A-L2 (do not depend on software defaults; there is no such thing as a standard data collection)
5. HDF files will be produced at each level of processing, plus optional SeaBASS text files for radiometry at L1E and L2. Plots can be produced at L1D, L1E, and L2. Processing logs and plots are aggregated into PDF Reports at L2 (covering all processing from RAW to L2) written to a dedicated Reports directory in the selected Output directory.


## Processing command line for Seabird
python3 Main.py -cmd -c Seabird_example.cfg -i Data/Sample_Data/Seabird/L0/    -o Data/Sample_Data/Seabird/ -a Data/Sample_Data/FICE2_Ancillary_TrueRelAz.sb -l L1A 
python3 Main.py -cmd -c Seabird_example.cfg -i Data/Sample_Data/Seabird/L1A/   -o Data/Sample_Data/Seabird/ -a Data/Sample_Data/FICE2_Ancillary_TrueRelAz.sb -l L1AQC
python3 Main.py -cmd -c Seabird_example.cfg -i Data/Sample_Data/Seabird/L1AQC/ -o Data/Sample_Data/Seabird/ -l L1B
python3 Main.py -cmd -c Seabird_example.cfg -i Data/Sample_Data/Seabird/L1B/   -o Data/Sample_Data/Seabird/ -l L1BQC -u user -p password
python3 Main.py -cmd -c Seabird_example.cfg -i Data/Sample_Data/Seabird/L1BQC/ -o Data/Sample_Data/Seabird/ -l L2


## Processing command line for TRIOS
python3 Main.py -cmd -c Trios_example.cfg -i Data/Sample_Data/Trios/L0/    -o Data/Sample_Data/Trios/ -a Data/Sample_Data/FICE2_Ancillary_TrueRelAz.sb -l L1A
python3 Main.py -cmd -c Trios_example.cfg -i Data/Sample_Data/Trios/L1A/   -o Data/Sample_Data/Trios/ -a Data/Sample_Data/FICE2_Ancillary_TrueRelAz.sb -l L1AQC
python3 Main.py -cmd -c Trios_example.cfg -i Data/Sample_Data/Trios/L1AQC/ -o Data/Sample_Data/Trios/ -l L1B
python3 Main.py -cmd -c Trios_example.cfg -i Data/Sample_Data/Trios/L1B/   -o Data/Sample_Data/Trios/ -l L1BQC -u user -p password
python3 Main.py -cmd -c Trios_example.cfg -i Data/Sample_Data/Trios/L1BQC/ -o Data/Sample_Data/Trios/ -l L2 


