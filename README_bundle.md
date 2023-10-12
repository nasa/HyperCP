# HyperCP build executable

To bundle the application, first install PyInstaller in your `hypercp` environment. Note that only version 6.0.0 of PyInstaller was tested.

    conda activate hypercp
    conda install pyinstaller

On Windows, the command above might install PyInstaller 5.6.2 which could result in build failure (at execution time), a fix was to upgrade as follow

    pip install --upgrade auto-py-to-exe

To bundle the application run the `make.py` script

    python make.py

If the command is executed successfully, you will find an executable in the folder `hypercp/Bundled/dist/HyperCP-v{version}-{platform}`. Executing the bundled executable in your terminal or powershell on Windows to start HyperCP. This executable can be shared with others and should run on their host machine.

On macOS the executable should work on both Intel and Apple Silicon processors despite the host used for building the application. However, this feature wasn't tested.

These steps were tested on macOS Ventura and Windows 10 only.
