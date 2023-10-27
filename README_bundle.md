# HyperCP build executable


## Bundle Locally
To bundle the application, first install PyInstaller in your `hypercp` environment. Note that only version 6.0.0 of PyInstaller was tested.

    conda activate hypercp
    conda install --channel=conda-forge pyinstaller==6.0

To bundle the application run the `make.py` script

    python make.py

If the command is executed successfully, you will find an executable in the folder `hypercp/Bundled/dist/HyperCP-v{version}-{platform}`. Executing the bundled executable in your terminal or powershell on Windows to start HyperCP. This executable can be shared with others and should run on their host machine.

On macOS the executable should work on both Intel and Apple Silicon processors despite the host used for building the application. However, this feature wasn't tested.

These steps were tested on macOS Ventura, Sonoma, and Windows 10 only.

## Bundle with GitHub Workflow
On any push to the main, dev, or workflow branch the application will be bundled

On macOS, bundled application are not signed, hence macOS Gatekeeper will raise a warning and prevent the application to run. The preferred workaround is to authorize the application to run.

    cd HyperCP-v1.2.0-Darwin
    sudo xattr -r -d com.apple.quarantine HyperCP-v1.2.0-Darwin
    sudo xattr -r -d com.apple.quarantine _internal/*.dylib 

Another workaround (not recommended) is to disable macOS Gatekeeper only during the time HyperCP is used.

    sudo spctl --master-disable

When done running HyperCP do not forget to re-enable macOS Gatekeeper.

    sudo spctl --master-enable  
