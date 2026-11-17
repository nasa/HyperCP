# HyperCP Executable Bundle Releases
[Bundled releases](https://github.com/nasa/HyperCP/releases) are available for download for Mac, Windows, and Linux. These do not require that you manage your python environment or your Git repository for HyperCP, but they should be downloaded regularly to stay up to date, which can be more cumbersome in the long run.

Execute your unzipped bundle from your terminal or powershell (Windows) to start HyperCP.

## Executing HyperCP bundle on macOS
On macOS, bundled applications are unsigned, hence macOS Gatekeeper will raise a warning and prevent the application from running. The preferred workaround is to authorize the application to run. This does not require sudo priviledges.

    cd HyperCP-v1.2.XX-Darwin
    xattr -dr com.apple.quarantine HyperCP-v1.2.XX-Darwin

Where XX is your version number. Another workaround (not recommended) is to disable macOS Gatekeeper only during the time HyperCP is used.

    sudo spctl --master-disable

When done running HyperCP do not forget to re-enable macOS Gatekeeper.

    sudo spctl --master-enable  


## To bundle HyperCP yourself locally
Install PyInstaller in your `hypercp` environment. Note that only version 6.0.0 of PyInstaller was tested.

    conda activate hypercp
    conda install --channel=conda-forge pyinstaller==6.0

Bundle the application with:

    python make.py

If the command is executed successfully, you will find an executable in the folder `hypercp/Bundled/dist/HyperCP-v{version}-{platform}`. Execute the bundled executable in your terminal or powershell on Windows to start HyperCP.

On macOS the executable should work on both Intel and Apple Silicon processors despite the host used for bundling the application. However, this feature wasn't tested.

These steps were tested on macOS Ventura, Sonoma, and Windows 10/11 only. The application is bundled with releases automatically on Windows, macOS (Darwin), and Linux, when a commit is pushed to the master branch.
