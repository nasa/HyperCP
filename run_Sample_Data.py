""" Scripted command line call to HyperCP. Set up the configuration file using the GUI first,
    or by editing ./Config/[yourconfig].cfg JSON file."""

import multiprocessing
from functools import partial
import os
import glob
import time

from Main import Command
from Source.ConfigFile import ConfigFile

# Run scripted call to single-level or multi-level (L0 - L2) command line calls to HyperCP
# from terminal. Recommend making a copy for your own purposes. This file is tracked with
# git and controlled by the HyperCP team (i.e., your changes will be lost on pull).
#
# Before running:
#   conda activate hypercp
# Usage:
#   python run_Sample_Data.py
#
# NOTE: Set up the HyperCP Configuration in the GUI before running this script. Sample configurations
#       have been provided in the HyperCP repository. The configuration file (./Config/[sample].cfg) can
#       also be edited by hand.
# NOTE: Multithreading is available to run multiple files simulataneously.
# NOTE: This script cannot be run on the same repository simultaneously with alternate configurations.
# NOTE: By default this processes all files in the PROC_LEVEL -1 level directory to PROC_LEVEL directory.
#
# D. Aurin NASA/GSFC Aug 2026
# 
#   BUG: Block use of screen for QT if necessary
#   If you get the following error, read on:
#
#       "qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in "" even though it was found"
#
#   The following needs to be run in the parent shell, so cannot be spawned from here. Prior to running this script,
#   run the following in the shell:
#       export QT_QPA_PLATFORM=offscreen

################################################### CUSTOM SET UP ###################################################

# Batch options #

MULTI_TASK = True  # Multiple threads for HyperSAS (any level) or TriOS (only L1A and up)
MULTI_LEVEL = True  # Process raw (L0) to Level-2 (L2)
CLOBBER = True      # True overwrites existing files
PROC_LEVEL = "L2"   # Process to this level: L1A, L1AQC, L1B, LBQC, L2 (ignored for MULTI_LEVEL)

# Dataset options #

# PLATFORM = "pySAS" # case-sensitive for ancillary file naming
# PLATFORM = "SolarTracker"
# PLATFORM = "Manual_TriOS"
# PLATFORM = "ES_Only"
PLATFORM = "DALEC"
# PLATFORM = "SoRad"

CRUISE = "FICE22" # Here mainly used for ancillary file name

# L1B_REGIME: Optional. [Factory, Class, Sensor]
#   Denote FRM processing regime and use appropriately named subdirectories.
#   This requires a custom Configuration file (e.g., "FICE22_pySAS_Class.cfg"). Set this up in the GUI.
L1B_REGIME = "" # Leave this blank unless you want to process in multiple regimes. Only changes folders, not the configuration file.

# L2_VERSION: Glint options [M99NN, M99MA, M99SS, Z17NN, etc.] One or more.
#   M99: Mobley 1999 glint
#   Z17: Zhang et al. 2017 glint
#   3C: 3C glint (e.g. Groetsch et al. 2017)
#   NN: No NIR residual correction
#   SS: Similarity Spectrum (Ruddick et al.) NIR correction
#   MA: Mueller and Austin 1995 NIR correction
#   Alters the configuration file and designates a special output path for Level-2 processing alternatives.
#
#   I tend to run this script once on multilevel M99NN L0-2C, then move L1A-L1BQC and related folders back up to PATH_DATA,
#       and run single level L2 for the rest of the options.
L2_VERSIONS = ['M99NN']
# L2_VERSIONS = ['M99MA','M99NN',"M99SS","Z17MA","Z17NN","Z17SS"] # NOTE: Configuration file is automatically updated based on this

# STATIONS: True to extract station data at L2 based on ancillary file
STATIONS = [False]
# STATIONS = [True,False]         # NOTE: Configuration file is automatically updated based on this

#################################
## PATH options. Edit this block for processing your own data outside the HyerCP repository
PATH_HCP = os.path.dirname(os.path.abspath(__file__))  # Path to HyperCP repository on host
# PATH_DATA = f"{PATH_OS}/My/Data/Directory/{CRUISE}"  # Top level data directory containing RAW/ and ancillary file.
PATH_DATA = os.path.join(PATH_HCP,'Data','Sample_Data',PLATFORM)
##################################

################################################# END CUSTOM SET UP #################################################


PATH_ANC = ""
if PLATFORM.lower() == "manual_trios":
    PATH_ANC = os.path.join(
        PATH_DATA, f"{CRUISE}_TriOS_Ancillary.sb")
    RAW_TYPE = "MSDA" # Defines the type of raw data expected. Not case-sensitive.
    CONFIG_NAME = "sample_TRIOS_NOTRACKER.cfg"
elif PLATFORM.lower() == "pysas" or PLATFORM.lower() == "solartracker":
    RAW_TYPE = "SeaBird"
    if PLATFORM.lower() == 'pysas':
        # Set these up in advance in the GUI.
        CONFIG_NAME = "sample_SEABIRD_pySAS.cfg"
    else:
        CONFIG_NAME = "sample_SEABIRD_SOLARTRACKER.cfg"
elif PLATFORM.lower() == "es_only":
    RAW_TYPE = "MSDA"
    CONFIG_NAME = "sample_TRIOS_ESONLY.cfg"
elif PLATFORM.lower() == "dalec":
    RAW_TYPE = "IMO"
    CONFIG_NAME = "sample_DALEC.cfg"
elif PLATFORM.lower() == "sorad":
    RAW_TYPE = "PML"
    CONFIG_NAME = "sample_TRIOS_SoRad.cfg"
else:
    RAW_TYPE = ""
    CONFIG_NAME = f"{CRUISE}.cfg"

PATH_CFG = os.path.join(PATH_HCP, "Config", CONFIG_NAME)

if PLATFORM.lower() != "manual_trios":
    PATH_ANC = os.path.join(
            PATH_DATA, f"{CRUISE}_{PLATFORM}_Ancillary.sb")

if MULTI_LEVEL or PROC_LEVEL == "L1A":
    PATH_INPUT = PATH_DATA
else:
    PATH_INPUT = os.path.join(PATH_DATA, L1B_REGIME)

# PATH_OUTPUT does not require folder names of data levels. HyperCP will automate that.
PATH_OUTPUT = os.path.join(PATH_DATA, L1B_REGIME)
# Add output directory if necessary (ignore data level directories)
if os.path.isdir(PATH_OUTPUT) is False:
    os.mkdir(PATH_OUTPUT)
    PATH_OUTPUT = os.path.join(PATH_DATA, L1B_REGIME, L2_VERSIONS)
    if os.path.isdir(PATH_OUTPUT) is False:
        os.mkdir(PATH_OUTPUT)

os.environ["HYPERINSPACE_CMD"] = "true"

## Setup remaining globals ##
TO_LEVELS = ["L1A", "L1AQC", "L1B", "L1BQC", "L2"]
FROM_LEVELS = ["RAW", "L1A", "L1AQC", "L1B", "L1BQC"]
if RAW_TYPE.lower() == "seabird":
    FILE_EXT = [".raw"]  # May need to use ".RAW" sometimes
elif RAW_TYPE.lower() == "msda":
    FILE_EXT = [".mlb"]
elif RAW_TYPE.lower() == "imo":
    FILE_EXT = [".TXT"]
elif RAW_TYPE.lower() == "pml":
    FILE_EXT = [".hdf"]
else:
    FILE_EXT = []

FILE_EXT.extend(["_L1A.hdf", "_L1AQC.hdf", "_L1B.hdf", "_L1BQC.hdf"])

if not MULTI_LEVEL:
    iOutput = TO_LEVELS.index(PROC_LEVEL)
    TO_LEVELS = [TO_LEVELS[iOutput]]
    FROM_LEVELS = [FROM_LEVELS[iOutput]]
    FILE_EXT = [FILE_EXT[iOutput]]

def adjust_config(config, version, stations):
    ConfigFile.loadConfig(config)

    if stations:
        ConfigFile.settings["bL2Stations"] = 1
    else:
        ConfigFile.settings["bL2Stations"] = 0

    if version.startswith('M99'):
        ConfigFile.settings["bL23CRho"] = 0
        ConfigFile.settings["bL2Z17Rho"] = 0
        ConfigFile.settings["bL2M99Rho"] = 1
    elif version.startswith('Z17'):
        ConfigFile.settings["bL23CRho"] = 0
        ConfigFile.settings["bL2Z17Rho"] = 1
        ConfigFile.settings["bL2M99Rho"] = 0
    elif version.startswith('3C'):
        ConfigFile.settings["bL23CRho"] = 1
        ConfigFile.settings["bL2Z17Rho"] = 0
        ConfigFile.settings["bL2M99Rho"] = 0

    if version.endswith('MA'):
        ConfigFile.settings["bL2PerformNIRCorrection"] = 1
        ConfigFile.settings["bL2SimpleNIRCorrection"] = 1 # Mobley 1999 adapted to minimum 700-800, not 750 nm
        ConfigFile.settings["bL2SimSpecNIRCorrection"] = 0 # Ruddick 2005, Ruddick 2006 similarity spectrum
    elif version.endswith('NN'):
        ConfigFile.settings["bL2PerformNIRCorrection"] = 0
        ConfigFile.settings["bL2SimpleNIRCorrection"] = 0
        ConfigFile.settings["bL2SimSpecNIRCorrection"] = 0
    elif version.endswith('SS'):
        ConfigFile.settings["bL2PerformNIRCorrection"] = 1
        ConfigFile.settings["bL2SimpleNIRCorrection"] = 0
        ConfigFile.settings["bL2SimSpecNIRCorrection"] = 1

    ConfigFile.saveConfig(config)


def run_Command(inputFiles,outPath):
    """Run either directly or using multiprocessor pool below."""
    #   inputFiles is a string unles TriOS RAW, then list.

    # This will skip the file if either 1) the result exists and no CLOBBER, or 2) the Level failed and produced a report.
    # Override with CLOBBER, above.
    to_skip = {
        level: [
            os.path.basename(fp).split("_" + level)[0]
            for fp in glob.glob(os.path.join(outPath, level, "*"))
        ]
        + [
            os.path.basename(fp).split("_" + level)[0]
            for fp in glob.glob(os.path.join(outPath, "Reports", f"*_{level}_fail.pdf"))
        ]
        for level in TO_LEVELS
    }

    if MULTI_LEVEL:
        # One or more files. (inputFiles is a list of one or more files)
        from_level = FROM_LEVELS[0]
        to_level = 'L1A'
        final_level = 'L2'
        inputFileBase = inputFiles        # Full-path file
        test = [os.path.exists(inputFileBase[i])
                for i, x in enumerate(inputFiles)
                if os.path.exists(x)]
        if not test:
            print("***********************************")
            print(f"*** [{inputFileBase}] STOPPED PROCESSING ***")
            print(f"Bad input path: {inputFiles}")
            print("***********************************")
            return
        inputFileBase = os.path.splitext(os.path.basename(inputFiles))[0]     # 'FRM4SOC2_FICE22_NASA_20220715_120000_L1BQC'
        if RAW_TYPE.lower() == 'seabird' and inputFileBase in to_skip[final_level] and not CLOBBER:
            print("************************************************")
            print(f"*** [{inputFileBase}] ALREADY PROCESSED TO {final_level} ***")
            print("************************************************")
        else:
            # NOTE: When running multi-level, it has to start over at raw, even if L1A exists.
            print("************************************************")
            print(f"*** [{inputFileBase}] PROCESSING L0 - L2 ***")
            print("************************************************")

            Command(
                PATH_CFG,
                from_level,
                inputFiles,
                outPath,
                to_level,
                PATH_ANC,
                MULTI_LEVEL)

    else:
        # One file at a time with or without multithread. (inputFiles is a string of one file)
        for from_level, to_level, _ in zip(FROM_LEVELS, TO_LEVELS, FILE_EXT):
            # inputFileBase = os.path.splitext(os.path.basename(inputFiles))[0]     # 'FRM4SOC2_FICE22_NASA_20220715_120000_L1BQC'
            inputFileBase = os.path.basename(inputFiles).split("_" + from_level)[0] # 'FRM4SOC2_FICE22_NASA_20220715_120000, 1614100, etc.
            test = os.path.exists(inputFiles)
            if not test:
                print("***********************************")
                print(f"*** [{inputFileBase}] STOPPED PROCESSING ***")
                print(f"Bad input path: {inputFiles}")
                print("***********************************")
                break
            if inputFileBase in to_skip[to_level] and not CLOBBER:
                print("************************************************")
                print(f"*** [{inputFileBase}] ALREADY PROCESSED TO {to_level} ***")
                print("************************************************")
                continue
            print("************************************************")
            print(f"*** [{inputFileBase}] PROCESSING TO {to_level} ***")
            print("************************************************")

            Command(
                PATH_CFG,
                from_level,
                inputFiles,
                outPath,
                to_level,
                PATH_ANC,
                MULTI_LEVEL
                )


def worker(fpf,pathOut):
    # fpf is a list unless multitasking, in which case it's a string, unless it's TriOS RAW
    if isinstance(fpf, list):
        if RAW_TYPE.lower() == "trios" and MULTI_LEVEL:
            print(f"### Processing {fpf} ...")
            run_Command(fpf,pathOut)
        else:
            file = None
            for file in fpf:
                print(f"### Processing {os.path.basename(file)} ...")
                run_Command(file,pathOut)
            print(f"### Finished {os.path.basename(file)}")
    else:
        print(f"### Multithread Processing {os.path.basename(fpf)} ...")
        run_Command(fpf,pathOut)
        print(f"### Finished {os.path.basename(fpf)}")


if __name__ == '__main__':
    t0Single = time.time()
    for STATION in STATIONS:
        for L2_VERSION in L2_VERSIONS:
            # PATH_OUTPUT does not require folder names of data levels. HyperCP will automate that.
            if PROC_LEVEL == 'L2':
                PATH_OUTPUT = os.path.join(PATH_DATA,L1B_REGIME,L2_VERSION)
            else:
                PATH_OUTPUT = os.path.join(PATH_DATA,L1B_REGIME)
            if os.path.isdir(PATH_OUTPUT) is False:
                os.mkdir(PATH_OUTPUT)

            # Adjust the configuration file to reflect the L2 variant and whether stations are being run.
            adjust_config(CONFIG_NAME, L2_VERSION,STATION)

            t1Single = time.time()

            # Input list of one or more elements:
            fp_input_files = sorted(
                glob.glob(os.path.join(PATH_INPUT, FROM_LEVELS[0], f"*{FILE_EXT[0]}")))
            if not fp_input_files:
                FILE_EXT = [".RAW"]
                fp_input_files = sorted(
                    glob.glob(os.path.join(PATH_INPUT, FROM_LEVELS[0], f"*{FILE_EXT[0]}")))


            # # NOTE: For debugging VVV
            # fp_input_files = [fp_input_files[0]]

            partial_worker = partial(worker,pathOut=PATH_OUTPUT)

            if fp_input_files:
                print(f"Processing {fp_input_files}")
                print(f"Using configuration {PATH_CFG}")
                print(f"with ancillary data {PATH_ANC}")

                if MULTI_TASK:
                    # If Z17 correction is enabled in L2, a significant amount of
                    #   memory is used (~3GB) for each process so you may not be able to
                    #   use all cores of the system without problems.
                    with multiprocessing.Pool(4) as pool:
                        # One file (string) at a time to worker
                        pool.map(
                            partial_worker, fp_input_files
                        )
                else:
                    # List of one or more files
                    worker(fp_input_files,PATH_OUTPUT)

                t2Single = time.time()
                print(f"Time elapsed: {str(round((t2Single-t1Single)/60))} minutes")

            else:
                print(f"No input files found {os.path.join(PATH_INPUT, FROM_LEVELS[0], FILE_EXT[0])}")
                t2Single = time.time()
        t3Single = time.time()

        mesg = f"Global batch time elapsed: {str(round((t2Single-t1Single)/60))} minutes"
        print(mesg)
        if STATION:
            with open(PATH_OUTPUT + 'batchlog_stations.txt', 'w', encoding="utf-8") as logFile:
                logFile.write(mesg + "\n")
        else:
            with open(PATH_OUTPUT + 'batchlog_no_stations.txt', 'w', encoding="utf-8") as logFile:
                logFile.write(mesg + "\n")

