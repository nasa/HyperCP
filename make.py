import os
import re
import glob
import platform

import PyInstaller.__main__


root = os.path.join('.', 'Bundled')

# Set parameters specific to platform
if platform.system() not in ['Windows', 'Darwin', 'Linux']:
    raise ValueError(f"Platform {platform.system()} not supported.")
os_specific_options = []
add_data_sep = ':'
if platform.system() == 'Darwin':
    os_specific_options = [
        # f'--icon={os.path.relpath(os.path.join("Data", "Img", "logo.icns"), root)}',
        '--osx-bundle-identifier=com.nasa.hypercp.hypercp',
        # '--target-arch=universal2',
    ]
elif platform.system() == 'Windows':
    os_specific_options = [
        f'--splash={os.path.relpath(os.path.join("Data", "Img", "with_background_530x223.png"), root)}',
        f'--icon={os.path.relpath(os.path.join("Data", "Img", "logo.ico"), root)}',
        # '--debug=imports',  # to debug missing imports
        '--hidden-import=sklearn.metrics._pairwise_distances_reduction._datasets_pair',
        '--hidden-import=sklearn.metrics._pairwise_distances_reduction._middle_term_computer',
    ]
    add_data_sep = ';'

# Get version number (without importing file)
version = None
with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Main.py'), 'r') as f:
    for l in f:
        if l.startswith('version'):
            version = l.split('=')[1].strip(" \n'")
            break

# Include all Data files (except Zhang table)
linked_data = [
    f'--add-data={os.path.relpath("Config", root)}{add_data_sep}Config',
    f'--add-data={os.path.relpath(".ecmwf_api_config", root)}{add_data_sep}.',
]
for f in sorted(glob.glob(os.path.join('Data', '*'))):
    if os.path.isdir(f) and os.path.basename(f) not in ['L1A', 'L1AQC', 'L1B', 'L1BQC', 'L2', 'Plots', 'Reports']:
        linked_data.append(f'--add-data={os.path.relpath(f, root)}{add_data_sep}{f}')
    elif re.match('^.*\.(txt|csv|sb|nc|hdf)$', os.path.splitext(f)[1]):
        linked_data.append(f'--add-data={os.path.relpath(f, root)}{add_data_sep}Data')

# Run PyInstaller with parameters below
PyInstaller.__main__.run([
    'Main.py',
    f'--name=HyperCP-v{version}-{platform.system()}',
    f'--distpath={os.path.join(root, "dist")}',
    f'--workpath={os.path.join(root, "build")}',
    f'--specpath={root}',
    # f'--icon={os.path.relpath(os.path.join("Data", "Img", "HyperCP_banner1.png"), root)}',  # TODO make square low-res icon in ico or icon format
    '--console',  # Open Console (hide console with windowed)
    '--noconfirm',
    # '--clean',
    *linked_data,
    *os_specific_options,
])
