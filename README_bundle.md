# HyperCP build executable

## Bundle HyperCP locally
Install PyInstaller in your `hypercp` environment. Note that only version 6.0.0 of PyInstaller was tested.

    conda activate hypercp
    conda install --channel=conda-forge pyinstaller==6.0

Bundle the application with:

    python make.py

If the command is executed successfully, you will find an executable in the folder `hypercp/Bundled/dist/HyperCP-v{version}-{platform}`. Execute the bundled executable in your terminal or powershell on Windows to start HyperCP.

On macOS the executable should work on both Intel and Apple Silicon processors despite the host used for bundling the application. However, this feature wasn't tested.

These steps were tested on macOS Ventura, Sonoma, and Windows 10 only. The application is bundled automatically on Windows, macOS (Darwin), and Linux, when a commit is pushed to the master branch.

## Executing HyperCP bundle on macOS
On macOS, bundled application are not signed, hence macOS Gatekeeper will raise a warning and prevent the application to run. The preferred workaround is to authorize the application to run.

    cd HyperCP-v1.2.0-Darwin
    sudo xattr -r -d com.apple.quarantine HyperCP-v1.2.0-Darwin
    sudo xattr -r -d com.apple.quarantine **/*.dylib
    sudo xattr -r -d com.apple.quarantine **/*.so

Another workaround (not recommended) is to disable macOS Gatekeeper only during the time HyperCP is used.

    sudo spctl --master-disable

When done running HyperCP do not forget to re-enable macOS Gatekeeper.

    sudo spctl --master-enable  
