import multiprocessing
import os
import glob
import sys
import time

from Main import Command
''' Scripted command line call to HyperCP. Set up the configuration file using the GUI first,
    or by editing ./Config/[yourconfig].cfg JSON file. 

    Run scripted call to single-level or multi-level (L0 - L2) command line calls to HyperCP 
    from terminal.
    
    Recommend making a copy for your own purposes. This file is tracked with git and controlled
    by the HyperCP team.

    D. Aurin NASA/GSFC Aug 2024
    '''

# Run scripted call to single-level or multi-level (L0 - L2) command line calls to HyperCP from terminal.
#
# Before running:
#   conda activate hypercp
# Usage:
#   python run_Sample_Data.py
#
# IMPORTANT: Set up the HyperCP Configuration in the GUI before running this script.
#           (Sample configurations have been provided in the HyperCP repository)
# Multithreading is available to run multiple files simulataneously
#   NOTE: Multithreading not yet available for manually acquired TriOS (.mlb) raw files (e.g., multi-level) 
#   NOTE: Cannot be run on the same machine simultaneously with alternate Configurations.

# By default processes all files in the PROC_LEVEL -1 level directory to PROC_LEVEL directory.

os.environ["HYPERINSPACE_CMD"] = "TRUE"
################################################### CUSTOM SET UP ###################################################
# Batch options
MULTI_TASK = True       # Multiple threads for HyperSAS (any level) or TriOS (only L1A and up)
MULTI_LEVEL = True      # Process raw (L0) to Level-2 (L2)
CLOBBER = True          # True overwrites existing files
PROC_LEVEL = "L2"       # Process to this level: L1A, L1AQC, L1B, LBQC, L2 (ignored for MULTI_LEVEL)

# Dataset options
PLATFORM = "pySAS"
# PLATFORM = "Manual_TriOS"
INST_TYPE = "SEABIRD"   # SEABIRD or TRIOS; defines raw file naming
# INST_TYPE = "TRIOS" 
CRUISE = "FICE22"
# L1B_REGIME: Optional. [Default, Class, Full]
#   Denote FRM processing regime and use appropriately named subdirectories.
#   This requires a custom Configuration file (e.g., "FICE22_pySAS_Class.cfg"). Set this up in the GUI.
L1B_REGIME = ""

# L2_VERSION: Optional. [M99NN, M99MA, M99SimSpec, Z17NN, etc.]
#   Denote a special output path for Level-2 processing alternatives.
L2_VERSION = "Z17SS"

#################################
## PATH options
PATH_OS = os.path.expanduser('~')
PATH_HCP = f"{PATH_OS}/GitRepos/HyperCP"                # Local path to HyperCP repository.
PATH_DATA = f'{PATH_OS}/Projects/HyperPACE/field_data/HyperSAS/{CRUISE}'   # Top level data directory containing RAW/ and ancillary file.
##################################

PATH_ANC = os.path.join(
    PATH_DATA, f"{CRUISE}_pySAS_Ancillary.sb"
    # PATH_DATA, f"{CRUISE}_TriOS_Ancillary.sb"
    # PATH_DATA, f"{CRUISE}_Ancillary.sb"
    )

if MULTI_LEVEL or PROC_LEVEL == "L1A":
    PATH_INPUT = PATH_DATA
else:
    PATH_INPUT = os.path.join(PATH_DATA,L1B_REGIME)
# PATH_OUTPUT does not require folder names of data levels. HyperCP will automate that.
PATH_OUTPUT = os.path.join(PATH_DATA,L1B_REGIME)

# Add output directory if necessary (ignore data level directories)
if os.path.isdir(PATH_OUTPUT) is False:
    os.mkdir(PATH_OUTPUT)
    PATH_OUTPUT = os.path.join(PATH_DATA,L1B_REGIME,L2_VERSION)
    if os.path.isdir(PATH_OUTPUT) is False:
        os.mkdir(PATH_OUTPUT)

# Set these up in advance in the GUI. One config file for each REGIME, edited for each VERSION.
if L1B_REGIME == "":
    PATH_CFG = os.path.join(    
        PATH_HCP, 'Config', f'{CRUISE}.cfg'    
        )   
else:
    PATH_CFG = os.path.join(    
        PATH_HCP, 'Config', f'{CRUISE}_{L1B_REGIME}.cfg'    
        )  
# Tip: When running multiple FRM-pathways, move the RAW directory to where the input data directory needs to be.
################################################# END CUSTOM SET UP #################################################

## Setup remaining globals ##
TO_LEVELS = ["L1A", "L1AQC", "L1B", "L1BQC", "L2"]
FROM_LEVELS = ["RAW", "L1A", "L1AQC", "L1B", "L1BQC"]
if INST_TYPE.lower() == "seabird":
    FILE_EXT = [".raw"]                 # May need to use ".RAW" sometimes
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
    to_skip = {
        level: [
            os.path.basename(fp).split("_" + level)[0]
            for fp in glob.glob(os.path.join(PATH_OUTPUT, level, "*"))
        ]
        + [
            os.path.basename(fp).split("_" + level)[0]
            for fp in glob.glob(os.path.join(PATH_OUTPUT, "Reports", f"*_{level}_fail.pdf"))
        ]
        for level in TO_LEVELS
    }

    if MULTI_LEVEL:
        # One or more files. (fp_input_files is a list of one or more files)
        from_level = FROM_LEVELS[0]
        to_level = 'L1A'
        inputFileBase = fp_input_files        # Full-path file
        test = [
                os.path.exists(inputFileBase[i])
                for i, x in enumerate(fp_input_files)
                if os.path.exists(x)
                ]            
        if not test:
            print("***********************************")
            print(f"*** [{inputFileBase}] STOPPED PROCESSING ***")
            print(f"Bad input path: {fp_input_files}")
            print("***********************************")
            return
        inputFileBase = os.path.splitext(os.path.basename(fp_input_files))[0]     # 'FRM4SOC2_FICE22_NASA_20220715_120000_L1BQC'  
        if INST_TYPE.lower() == 'seabird' and inputFileBase in to_skip[to_level] and not CLOBBER:
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
                MULTI_LEVEL
                )       
    
    else:
        # One file at a time with or without multithread. (fp_input_files is a string of one file)
        for from_level, to_level, ext in zip(FROM_LEVELS, TO_LEVELS, FILE_EXT):                        
            inputFileBase = os.path.splitext(os.path.basename(fp_input_files))[0]            
            test = os.path.exists(fp_input_files)            
            if not test:
                print("***********************************")
                print(f"*** [{inputFileBase}] STOPPED PROCESSING ***")
                print(f"Bad input path: {fp_input_files}")
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
                fp_input_files,
                PATH_OUTPUT,
                to_level,
                PATH_ANC,
                MULTI_LEVEL
                )        


def worker(fp_input_files):
    # fp_input_files is a list unless multitasking, in which case it's a string, unless it's TriOS RAW
    if type(fp_input_files) is list:
        if INST_TYPE.lower() == "trios" and MULTI_LEVEL: 
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
    fp_input_files = sorted(
        glob.glob(os.path.join(PATH_INPUT, FROM_LEVELS[0], f"*{FILE_EXT[0]}"))
    )

    if fp_input_files:
        print(f"Processing {fp_input_files}")
        print(f"Using configuration {PATH_CFG}")
        print(f"with ancillary data {PATH_ANC}")
        
        if MULTI_TASK:
            # If Z17 correction is enabled in L2, a significant amount of 
            #   memory is used (~3GB) for each process so you may not be able to 
            #   use all cores of the system with problems.
            with multiprocessing.Pool(4) as pool:
                # One file (string) at a time to worker
                pool.map(
                    worker, fp_input_files
                )  
        else:
            # List of one or more files  
            worker(fp_input_files)       

        t1Single = time.time()
        print(f"Overall time elapsed: {str(round((t1Single-t0Single)/60))} minutes")

    else:
        print("No input files found")