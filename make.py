import os
import re
import glob
import platform
import subprocess

import PyInstaller.__main__


root = os.path.join('.', 'Bundled')

# Set parameters specific to platform
if platform.system() not in ['Windows', 'Darwin', 'Linux']:
    raise ValueError(f"Platform {platform.system()} not supported.")
os_specific_options = []
add_data_sep = ':'
if platform.system() == 'Darwin':
    os_specific_options = [
        f'--icon={os.path.relpath(os.path.join("Data", "Img", "logo.icns"), root)}',
        '--windowed',
        # '--target-arch=universal2',  # Fails on GitHub but bundle works on both architecture
        # Required for code signing
        '--osx-bundle-identifier=com.nasa.hypercp.hypercp',
        # f'--codesign-identity={os.getenv("CODESIGN_HASH")}',
        # f'--osx-entitlements-file={os.path.join("Bundled", "entitlements.plist")}',

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
        if l.startswith('VERSION'):
            version = l.split('=')[1].strip(" \n'\"")
            break

# Get git hash (without git package)
try:
    __git_hash__ = subprocess.check_output(['git', 'rev-parse', 'HEAD'],  #'--short',
                                           cwd=os.path.dirname(os.path.abspath(__file__))).decode('ascii').strip()
except (subprocess.SubprocessError, FileNotFoundError):
    __git_hash__ = 'git_na'

# Update version.txt file
if os.path.exists('version.txt'):
    os.remove('version.txt')
with open('version.txt', 'w') as f:
    f.write(f"version={version}\n")
    f.write(f"git_hash={__git_hash__}\n")
    f.close()

# Include all Data files (except Zhang table)
linked_data = [
    f'--add-data={os.path.relpath("version.txt", root)}{add_data_sep}.',
    f'--add-data={os.path.relpath("Config", root)}{add_data_sep}Config',
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
