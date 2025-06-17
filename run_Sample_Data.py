""" Scripted command line call to HyperCP. Set up the configuration file using the GUI first,
    or by editing ./Config/[yourconfig].cfg JSON file."""

import multiprocessing
import os
import glob
import time

from Main import Command

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
#       Multithreading for manually acquired TriOS (.mlb) raw files (e.g., multi-level) is now supported
# NOTE: This script cannot be run on the same repository simultaneously with alternate configurations.
# NOTE: By default this processes all files in the PROC_LEVEL -1 level directory to PROC_LEVEL directory.
#
# D. Aurin NASA/GSFC Aug 2024

################################################### CUSTOM SET UP ###################################################
# Block use of screen for QT if necessary
# NOTE: if you get the following error, read on...
#       qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in "" even though it was found
# NOTE: The following needs to be run in the parent shell, so cannot be spawned from here. Prior to running this script,
# run the following in the shell:
#       export QT_QPA_PLATFORM=offscreen

# Batch options
MULTI_TASK = True  # Multiple threads for HyperSAS (any level) or TriOS (only L1A and up)
MULTI_LEVEL = False  # Process raw (L0) to Level-2 (L2)
CLOBBER = True      # True overwrites existing files
PROC_LEVEL = "L1A"   # Process to this level: L1A, L1AQC, L1B, LBQC, L2 (ignored for MULTI_LEVEL)

# Dataset options
# PLATFORM = "pySAS"
PLATFORM = "Manual_TriOS"
# INST_TYPE = "SEABIRD"  # SEABIRD or TRIOS; defines raw file naming
INST_TYPE = "TRIOS"
CRUISE = "FICE22"
# L1B_REGIME: Optional. [Default, Class, Full]
#   Denote FRM processing regime and use appropriately named subdirectories.
#   This requires a custom Configuration file (e.g., "FICE22_pySAS_Class.cfg"). Set this up in the GUI.
L1B_REGIME = ""

# L2_VERSION: Optional. [M99NN, M99MA, M99SimSpec, Z17NN, etc.]
#   Denote a special output path for Level-2 processing alternatives.
L2_VERSION = ""

#################################
## PATH options
PATH_HCP = os.path.dirname(os.path.abspath(__file__))  # Path to HyperCP repository on host
# PATH_DATA = f"{PATH_OS}/Projects/HyperPACE/field_data/HyperSAS/{CRUISE}"  # Top level data directory containing RAW/ and ancillary file.
PATH_DATA = os.path.join(PATH_HCP,'Data','Sample_Data',PLATFORM)
##################################

if PLATFORM.lower() == "manual_trios":
    PATH_ANC = os.path.join(
        PATH_DATA, f"{CRUISE}_TriOS_Ancillary.sb",
    )
else:
    PATH_ANC = os.path.join(
        PATH_DATA, f"{CRUISE}_{PLATFORM}_Ancillary.sb",
    )

if MULTI_LEVEL or PROC_LEVEL == "L1A":
    PATH_INPUT = PATH_DATA
else:
    PATH_INPUT = os.path.join(PATH_DATA, L1B_REGIME)

# PATH_OUTPUT does not require folder names of data levels. HyperCP will automate that.
PATH_OUTPUT = os.path.join(PATH_DATA, L1B_REGIME)
# Add output directory if necessary (ignore data level directories)
if os.path.isdir(PATH_OUTPUT) is False:
    os.mkdir(PATH_OUTPUT)
    PATH_OUTPUT = os.path.join(PATH_DATA, L1B_REGIME, L2_VERSION)
    if os.path.isdir(PATH_OUTPUT) is False:
        os.mkdir(PATH_OUTPUT)

# Set these up in advance in the GUI. One config file for each REGIME, edited for each VERSION.
if PLATFORM.lower() == 'pysas':
    PATH_CFG = os.path.join(PATH_HCP, "Config", "sample_SEABIRD_pySAS.cfg")
elif PLATFORM.lower() == 'manual_trios':
    PATH_CFG = os.path.join(PATH_HCP, "Config", "sample_TriOS_NOTRACKER.cfg")
else:
    PATH_CFG = os.path.join(PATH_HCP, "Config", f"{CRUISE}.cfg")
################################################# END CUSTOM SET UP #################################################
os.environ["HYPERINSPACE_CMD"] = "true"

## Setup remaining globals ##
TO_LEVELS = ["L1A", "L1AQC", "L1B", "L1BQC", "L2"]
FROM_LEVELS = ["RAW", "L1A", "L1AQC", "L1B", "L1BQC"]
if INST_TYPE.lower() == "seabird":
    FILE_EXT = [".raw"]  # May need to use ".RAW" sometimes
else:
    FILE_EXT = [".mlb"]
FILE_EXT.extend(["_L1A.hdf", "_L1AQC.hdf", "_L1B.hdf", "_L1BQC.hdf"])

if not MULTI_LEVEL:
    iOutput = TO_LEVELS.index(PROC_LEVEL)
    TO_LEVELS = [TO_LEVELS[iOutput]]
    FROM_LEVELS = [FROM_LEVELS[iOutput]]
    FILE_EXT = [FILE_EXT[iOutput]]


def run_Command(fp_input_files):
    """Run either directly or using multiprocessor pool below."""
    #   fp_input_files is a string unless TriOS RAW, then list.

    # This will skip the file if either 1) the result exists and no CLOBBER, or
    #   2) the Level failed and produced a report.
    # Override with CLOBBER, above.
    to_skip = {level: [os.path.basename(fp).split("_" + level)[0]
            for fp in glob.glob(os.path.join(PATH_OUTPUT, level, "*"))]
        + [
            os.path.basename(fp).split("_" + level)[0]
            for fp in glob.glob(
                os.path.join(PATH_OUTPUT, "Reports", f"*_{level}_fail.pdf"))
        ]
        for level in TO_LEVELS}

    if MULTI_LEVEL:
        # One or more files. (fp_input_files is a list of one or more files)
        from_level = FROM_LEVELS[0]
        to_level = "L1A"
        # inputFileBase = fp_input_files  # Full-path file list of all in L1A
        test = [
            os.path.exists(fp_input_files[i])
            for i, x in enumerate(fp_input_files)
            if os.path.exists(x)
        ]
        if not test:
            print("***********************************")
            print(f"*** [{fp_input_files}] STOPPED PROCESSING ***")
            print(f"Bad input path: {fp_input_files}")
            print("***********************************")
            return
        inputFileBase = os.path.splitext(os.path.basename(fp_input_files[0]))[0]  # single file no path
        test = [v for v in to_skip[to_level] if v in inputFileBase]
        if (test and not CLOBBER):
            print("************************************************")
            print(f"*** [{inputFileBase}] ALREADY PROCESSED TO {to_level} ***")
            print("************************************************")
        else:
            print("************************************************")
            print(f"*** [{inputFileBase}] PROCESSING L0 - L2 ***")
            print("************************************************")

            Command(
                PATH_CFG,
                from_level,
                fp_input_files,
                PATH_OUTPUT,
                to_level,
                PATH_ANC,
                MULTI_LEVEL,
            )

    else:
        # One file at a time with or without multithread. (fp_input_files is a string of one file)
        for from_level, to_level, ext in zip(FROM_LEVELS, TO_LEVELS, FILE_EXT):
            if from_level == 'RAW' and INST_TYPE.lower() == 'trios':
                inputFileBase = os.path.splitext(os.path.basename(fp_input_files[0]))[0]  # single file no path
                test = [
                    os.path.exists(fp_input_files[i])
                    for i, x in enumerate(fp_input_files)
                    if os.path.exists(x)
                    ]
            else:
                inputFileBase = os.path.splitext(os.path.basename(fp_input_files))[0]
                test = os.path.exists(fp_input_files)
            if not test:
                print("***********************************")
                print(f"*** [{inputFileBase}] STOPPED PROCESSING ***")
                print(f"Bad input path: {fp_input_files}")
                print("***********************************")
                break
            test = [v for v in to_skip[to_level] if v in inputFileBase]
            if test and not CLOBBER:
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
                fp_input_files,
                PATH_OUTPUT,
                to_level,
                PATH_ANC,
                MULTI_LEVEL,
            )


def worker(fp_input_files):
    # fp_input_files is a list unless multitasking, in which case it's a string, unless it's TriOS RAW
    if isinstance(fp_input_files, list):
        if INST_TYPE.lower() == "trios" and (MULTI_LEVEL or 'RAW' in FROM_LEVELS):
            print(f"### Processing {fp_input_files} ...")
            run_Command(fp_input_files)
        else:
            for file in fp_input_files:
                print(f"### Processing {os.path.basename(file)} ...")
                run_Command(file)
            print(f"### Finished {os.path.basename(file)}")
    else:
        print(f"### Multithread Processing {os.path.basename(fp_input_files)} ...")
        run_Command(fp_input_files)
        print(f"### Finished {os.path.basename(fp_input_files)}")


if __name__ == "__main__":
    t0Single = time.time()

    # Input list of one or more elements:
    fpf_input = sorted(
        glob.glob(os.path.join(PATH_INPUT, FROM_LEVELS[0], f"*{FILE_EXT[0]}"))
    )

    if fpf_input:
        print(f"Processing {fpf_input}")
        print(f"Using configuration {PATH_CFG}")
        print(f"with ancillary data {PATH_ANC}")

        if MULTI_TASK:
            # If Z17 correction is enabled in L2, a significant amount of
            #   memory is used (~3GB) for each process so you may not be able to
            #   use all cores of the system with problems.
            with multiprocessing.Pool(4) as pool:
                if INST_TYPE.lower() == 'trios' and FROM_LEVELS[0] == 'RAW':
                    # Here we need a list of three files for each raw collection, or maybe a list of list triplets
                    fpf_input_triplets = []
                    for item in fpf_input:
                        inputFileBase = os.path.splitext(os.path.basename(item))[0]
                        timeStamp = inputFileBase[len(inputFileBase)-15:-1] # Subject to string error for non-compliant filenames
                        index = [i for i,x in enumerate(fpf_input) if timeStamp in x]
                        fpf_input_triplet = [fpf_input[x] for x in index]
                        fpf_input_triplets.append(fpf_input_triplet)

                    unique_fpf_input_triplets = [list(x) for x in set(tuple(x) for x in fpf_input_triplets)]
                    pool.map(worker, unique_fpf_input_triplets)
                else:
                    # One file (string) at a time to worker
                    pool.map(worker, fpf_input)
        else:
            # List of one or more files
            worker(fpf_input)

        t1Single = time.time()
        print(f"Overall time elapsed: {str(round((t1Single-t0Single)/60))} minutes")

    else:
        print("No input files found")
