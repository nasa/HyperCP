import multiprocessing
import os
import glob
import subprocess
import sys

from Main import Command, cmd

PATH_HCP = '/Users/daurin/GitRepos/HyperInSPACE'   # Adjust with full path on local computer
PATH_CFG = os.path.join(PATH_HCP, 'Config', 'sample_pySAS.cfg')
PATH_WK = '/Users/daurin/temp'  # Adjust with full path on local computer
PATH_ANC = '/Users/daurin/temp/SAMPLE_Ancillary_pySAS.sb'

TO_LEVELS = ['L1A', 'L1AQC', 'L1B', 'L1BQC', 'L2']
FROM_LEVELS = ['L0B', 'L1A', 'L1AQC', 'L1B', 'L1BQC']
FILE_EXT = ['.raw', '_L1A.hdf', '_L1AQC.hdf', '_L1B.hdf', '_L1BQC.hdf']

os.environ['HYPERINSPACE_CMD'] = 'TRUE'


def process_raw_to_l2(filename):
    ref = os.path.splitext(os.path.basename(filename))[0]
    to_skip = {level: [os.path.basename(f).split('_' + level)[0]
                       for f in glob.glob(os.path.join(PATH_WK, level, '*'))] +
                      [os.path.basename(f).split('_' + level)[0]
                       for f in glob.glob(os.path.join(PATH_WK, 'Reports', f'*_{level}_fail.pdf'))]
               for level in TO_LEVELS}
    failed = {}
    for from_level, to_level, ext in zip(FROM_LEVELS, TO_LEVELS, FILE_EXT):
        f = os.path.join(PATH_WK, from_level, ref + ext)
        if not os.path.exists(f):
            print('***********************************')
            print(f'*** [{ref}] STOPPED PROCESSING ***')
            print('***********************************')
            break
        if ref in to_skip[to_level]:
            print('************************************************')
            print(f'*** [{ref}] ALREADY PROCESSED TO {to_level} ***')
            print('************************************************')
            continue
        print('************************************************')
        print(f'*** [{ref}] PROCESSING TO {to_level} ***')
        print('************************************************')
        # Command(PATH_CFG, os.path.join(PATH_WK, from_level, ref + ext), PATH_WK, to_level, None)
        Command(PATH_CFG, os.path.join(PATH_WK, from_level, ref + ext), PATH_WK, to_level, PATH_ANC)


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
    print(f'### Processing {os.path.basename(raw_filename)} ...')
    proc = subprocess.run([sys.executable, 'run.py', '-i', raw_filename])
    print(f'### Finished {os.path.basename(raw_filename)}')
    # print('### STDOUT ##################################')
    # print(proc.stdout[-200:])
    # print('#############################################')


if __name__ == '__main__':
    raw_filenames = sorted(glob.glob(os.path.join(PATH_WK, 'L0B', '*.raw')))

    # If Zhang et al. 2017 correction is enabled a significant amount of memory is used (~3Go) for each process
    # so you might not be able to use all cores of the system
    with multiprocessing.Pool(4) as pool:
        pool.map(worker, raw_filenames)



