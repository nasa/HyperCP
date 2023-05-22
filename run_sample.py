import multiprocessing
import os
import glob
import subprocess
import sys

from Main import Command, cmd

## Custom set up ##

clobber = False # True overwrites existing files
PATH_HCP = '/Users/daurin/GitRepos/HyperInSPACE'   # Adjust with full path on local computer
INST_TYPE = 'SEABIRD' #SEABIRD or TRIOS

# For use with sample data provided:
PLATFORM_TYPE = 'NOTRACKER' #pySAS, SOLARTRACKER, or NOTRACKER. Adjust to desired acquisition platform type
PATH_DATA = os.path.join('Data','Sample_Data')   # For use with provided samples
PATH_WK = os.path.join(PATH_HCP,PATH_DATA)  # For use with provided samples
PATH_ANC = os.path.join(PATH_WK,f'SAMPLE_{INST_TYPE}_{PLATFORM_TYPE}_Ancillary.sb') # For use with provided samples

# For batching collections, adjust to your local settings:
# PATH_DATA = '/Users/daurin/Projects/HyperPACE/field_data/HyperSAS/EXPORTSNP'   # Adjust with full path on local computer
# PATH_WK = os.path.join(PATH_DATA)  # Adjust with full path on local computer
# PATH_ANC = os.path.join(PATH_DATA,f'*_Ancillary.sb') # Adjust with full path on local computer

## End Custom set up ##

## Setup Globals ##
PATH_CFG = os.path.join(PATH_HCP, 'Config', f'sample_{INST_TYPE}_{PLATFORM_TYPE}.cfg')
TO_LEVELS = ['L1A', 'L1AQC', 'L1B', 'L1BQC', 'L2']
FROM_LEVELS = ['RAW', 'L1A', 'L1AQC', 'L1B', 'L1BQC']
if INST_TYPE == 'SEABIRD':
    FILE_EXT = ['.raw', '_L1A.hdf', '_L1AQC.hdf', '_L1B.hdf', '_L1BQC.hdf']
else:
    FILE_EXT = ['.mlb', '_L1A.hdf', '_L1AQC.hdf', '_L1B.hdf', '_L1BQC.hdf']

os.environ['HYPERINSPACE_CMD'] = 'TRUE'


def process_raw_to_l2(filename):
    ''' Run either directly or using multiprocessor pool below. '''
    if INST_TYPE == 'SEABIRD':
        # Path to raw files:
        rawFPs = os.path.splitext(os.path.basename(filename))[0]
    elif INST_TYPE == 'TRIOS':
        rawFPs = filename # os.path.splitext(os.path.basename(filename))[0]

    # This will skip the file if either 1) the result exists and no clobber, or 2) the Level failed and produced a report.
    # Override with clobber, above.
    to_skip = {level: [os.path.basename(f).split('_' + level)[0]
                       for f in glob.glob(os.path.join(PATH_WK, level, '*'))] +
                      [os.path.basename(f).split('_' + level)[0]
                       for f in glob.glob(os.path.join(PATH_WK, 'Reports', f'*_{level}_fail.pdf'))]
               for level in TO_LEVELS}
    # failed = {}
    for from_level, to_level, ext in zip(FROM_LEVELS, TO_LEVELS, FILE_EXT):
        '''Single level CLI deprecated. Multi-level used. Raw-L2 only'''
        if to_level != 'L1A':
            continue
        if INST_TYPE == 'SEABIRD':
            # One file at a time
            l1aFileBase = os.path.splitext(os.path.basename(filename))[0]
            f = os.path.join(PATH_WK, from_level, rawFPs + ext)
            test  = os.path.exists(f)
        elif INST_TYPE == 'TRIOS':
            # All L0 files
            l0FileBase = os.path.splitext(os.path.basename(filename[0]))[0]
            l1aFileBase = l0FileBase.split('SPECTRUM_')[1]
            if to_level =='L1A':
                f = filename # a list
                test = [os.path.exists(f[i]) for i, x in enumerate(f) if os.path.exists(x)]
            else:
                '''deprecated'''
                f = os.path.join(PATH_WK, from_level, l1aFileBase + ext) # a file
                test = os.path.exists(f)


        # if not os.path.exists(f):
        if not test:
            print('***********************************')
            print(f'*** [{rawFPs}] STOPPED PROCESSING ***')
            print('***********************************')
            break
        # if rawFPs in to_skip[to_level] and not clobber:
        if l1aFileBase in to_skip[to_level] and not clobber:
            print('************************************************')
            # print(f'*** [{rawFPs}] ALREADY PROCESSED TO {to_level} ***')
            print(f'*** [{l1aFileBase}] ALREADY PROCESSED TO {to_level} ***')
            print('************************************************')
            continue
        print('************************************************')
        print(f'*** [{rawFPs}] PROCESSING TO {to_level} ***')
        print('************************************************')
        if INST_TYPE == 'SEABIRD':
            # Command(PATH_CFG, os.path.join(PATH_WK, from_level, rawFPs + ext), PATH_WK, to_level, None)
            # One file
            Command(PATH_CFG, from_level, os.path.join(PATH_WK, from_level, rawFPs + ext), PATH_WK, to_level, PATH_ANC)
        elif INST_TYPE == 'TRIOS':
            # rawFPs: list to L0 .mlbs
            Command(PATH_CFG, from_level, rawFPs, PATH_WK, to_level, PATH_ANC)


# %% One thread
# raw_filenames = sorted(glob.glob(os.path.join(PATH_WK, 'L0B', 'EXPORTS-EXPORTSNA-JC214-Process-*.raw')))
# for raw in raw_filenames[:3]:
#     process_raw_to_l2(raw)

# %% Multithread
#   Can't pickle HyperInSPACE, so start sub-processed instead
if len(sys.argv) > 1:
    # Code executed in subprocesses only
    process_raw_to_l2(sys.argv[2])
    sys.exit(0)


def worker(raw_filename):
    if type(raw_filename) is list:
        for file in raw_filename:
            print(f'### Processing {os.path.basename(file)} ...')

    else:
        print(f'### Processing {os.path.basename(raw_filename)} ...')
        proc = subprocess.run([sys.executable, 'run_sample.py', '-i', raw_filename])

    print(f'### Finished {os.path.basename(raw_filename)}')
    # print('### STDOUT ##################################')
    # print(proc.stdout[-200:])
    # print('#############################################')

## Watch for raw suffix below
if __name__ == '__main__':
    if INST_TYPE == 'SEABIRD':
        raw_filenames = sorted(glob.glob(os.path.join(PATH_WK, 'RAW', f'*{INST_TYPE}_{PLATFORM_TYPE}.raw'))) # For use with sample data
        # raw_filenames = sorted(glob.glob(os.path.join(PATH_WK, 'RAW', f'*.raw')))
        if not raw_filenames:
            raw_filenames = sorted(glob.glob(os.path.join(PATH_WK, 'RAW', f'*.RAW')))
    elif INST_TYPE == 'TRIOS':
        raw_filenames = sorted(glob.glob(os.path.join(PATH_WK, 'RAW', f'*.mlb')))

    # print(f'Processing {sorted(glob.glob(os.path.join(PATH_WK, "RAW", f"*{PLATFORM_TYPE}.raw")))}')
    print(f'Processing {raw_filenames}')
    print(f'Using configuration {PATH_CFG}')
    print(f'with ancillary data {PATH_ANC}')

    # If Zhang et al. 2017 correction is enabled a significant amount of memory is used (~3Go) for each process
    # so you might not be able to use all cores of the system
    if INST_TYPE == 'SEABIRD':
        with multiprocessing.Pool(4) as pool:
            pool.map(worker, raw_filenames) # Sends one file at a time to processor
    else:
        process_raw_to_l2(raw_filenames) # Sends list of files to... for TriOS raw .mlb triplets. No subprocessors



