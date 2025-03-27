import json
import os
import re
import numpy as np
import platform
import stat
import webbrowser

class GetAnc_credentials:

    # Credentials specifications for the different ancillary sources
    @staticmethod
    def credentialsSpec(credentialsID: str) -> dict:
        '''
        Define credentials specifications.

        credentialsID: a string, 'NASA_Earth_Data', 'ECWMF_ADS' or 'ECMWF_CDS'

        title: the title of the pop-up window
        key_string: how the key is called (depends on credentials specs)
        secret_string: how the secret is called (depends on credentials specs)
        key: the key (aka the user or url)
        secret: the secret (aka password)
        credentialsFile: credentials filename (not full path)
        credentials_filename: /full/path/to/credentialsFile
        URL_string: the url to be stored in given netrc line ("https:://" or similar prefix is removed)


        output: a dictionary with the specifications bounded to credentialsID
        '''

        out = {'credentialsID':credentialsID}

        if credentialsID == 'NASA_Earth_Data':
            if platform.system() == 'Windows':
                out['credentials_filename'] = '_netrc'
            else:
                out['credentials_filename'] = '.netrc'
            out['title'] = 'Login NASA Earth Data credentials - MERRA-2 Ancillary'
            out['storeCredsString'] = 'Store %s credentials in your home directory.' % credentialsID.replace('_', ' ')
            out['key_string'] = 'login'
            out['secret_string'] = 'password'
            out['URL_string'] = 'https://urs.earthdata.nasa.gov'
            out['obtainCredsString'] = 'Click here to obtain these credentials'
        elif credentialsID == 'ECMWF_ADS':
            out['credentials_filename'] = '.ecmwf_ads_credentials.json'
            out['title'] = 'Login ECMWF ADS API credentials - CAMS Ancillary'
            out['storeCredsString'] = 'Store %s credentials in your home directory.\nNB: These are NOT the ECMWF login credentials' % credentialsID.replace('_', ' ')
            out['key_string'] = 'url'
            out['secret_string'] = 'key'
            out['URL_string'] = 'https://ads.atmosphere.copernicus.eu/how-to-api'
            out['obtainCredsString'] = 'Click here to obtain API credentials (log in to ECMWF first and accept "Terms of Use", see README!)'
        elif credentialsID == 'ECMWF_CDS':
            out['credentials_filename'] = '.ecmwf_cds_credentials.json'
            out['title'] = 'Login ECMWF CDS API credentials - ERA-5 Ancillary'
            out['storeCredsString'] = 'Store %s credentials in your home directory.\nNB: These are NOT the ECMWF login credentials' % credentialsID.replace('_', ' ')
            out['key_string'] = 'url'
            out['secret_string'] = 'key'
            out['URL_string'] = 'https://cds.climate.copernicus.eu/how-to-api'
            out['obtainCredsString'] = 'Click here to obtain API credentials (log in to ECMWF first and accept "Terms of Use", see README!)'
        elif credentialsID == 'EUMETSAT_Data_Store':
            out['credentials_filename'] = '.eumdac_credentials.json'
            out['title'] = 'Login EUMETSAT Data Store credentials'
            out['storeCredsString'] = 'Store %s credentials in your home directory.\nNB: These are NOT the EO Portal login credentials' % credentialsID.replace('_', ' ')
            out['key_string'] = 'consumer_key'
            out['secret_string'] = 'consumer_secret'
            out['URL_string'] = 'https://api.eumetsat.int/api-key/'
            out['obtainCredsString'] = 'Click here to obtain API credentials (log in to EO Portal first!)'

        out['credentialsFile'] = os.path.join(os.path.expanduser('~'), out['credentials_filename'])

        return out

    # Erase already existing user credentials
    @staticmethod
    def erase_user_credentials(credentialsID: str, PyQT_or_Tk='PyQT') -> None:
        '''
        Erase credentials line in file (netrc case) or full credentials file (json case)

        credentialsID: a string, 'NASA_Earth_Data', 'ECWMF_ADS' or 'ECMWF_CDS'
        PyQT_or_Tk: a string, either 'PyQT' or 'Tk' (default='PyQT')
        '''

        # Determine case
        specs = GetAnc_credentials.credentialsSpec(credentialsID)
        credentialsFile = os.path.join(os.path.expanduser('~'),specs['credentials_filename'])

        # If file does not even exist, return.
        if not os.path.exists(credentialsFile):
            return

        erase = GetAnc_credentials.messageBox('Erase credentials?', 'This action will erase and replace your currently stored %s credentials, continue?' % credentialsID,'Warning',cancelButton=True, PyQT_or_Tk=PyQT_or_Tk)

        # Skip if reset was canceled...
        if not erase:
            return

        # If JSON file, remove file. If netrc, remove specific line. (JSON or netrc according to "specs")
        if credentialsFile.endswith('.json'):
            os.remove(credentialsFile)
        elif credentialsFile.endswith('netrc'):
            credLine = f'machine {specs["URL_string"].split("://")[-1]}'
            os.chmod(credentialsFile, stat.S_IRUSR | stat.S_IWUSR)

            with open(credentialsFile, 'r') as file:
                lines = file.readlines()

            lines_to_keep = [line for line in lines if credLine not in line]
            with open(credentialsFile, 'w') as file:
                file.writelines(lines_to_keep)

        return

    # Check if credentials are stored
    @staticmethod
    def credentials_stored(credentialsID: str) -> bool:
        '''
        Check if credentials are already stored.

        credentialsID: a string, 'NASA_Earth_Data', 'ECWMF_ADS' or 'ECMWF_CDS'

        return: credentialsStored, a Boolean.
        '''

        # Get credentials file
        specs = GetAnc_credentials.credentialsSpec(credentialsID)
        credentialsFile = specs['credentialsFile']

        # If JSON file exists, assume credentials are stored. If netrc check for specific line. (JSON or netrc according to "specs")
        if credentialsFile.endswith('json'):
            return os.path.exists(credentialsFile)
        elif credentialsFile.endswith('netrc'):
            if not os.path.exists(credentialsFile):
                return False
            else:
                os.chmod(credentialsFile, stat.S_IRUSR | stat.S_IWUSR)
                fo = open(credentialsFile)
                lines = fo.readlines()
                fo.close()
                credentialsStored = np.any(['machine %s ' % specs['URL_string'].split('://')[-1] in line for line in lines])
                return credentialsStored

    # Read user credentials
    @staticmethod
    def read_user_credentials(credentialsID: str) -> tuple[str,str]:
        '''
        Read user credentials

        credentialsID: a string, 'NASA_Earth_Data', 'ECWMF_ADS' or 'ECMWF_CDS'
        '''

        # Get credentials file
        specs = GetAnc_credentials.credentialsSpec(credentialsID)
        credentialsFile = specs['credentialsFile']

        # Error string
        missingCredentials = '%s: Credentials file missing or incomplete. Check %s' % (credentialsID.replace('_',' '),credentialsFile)

        # NB: This function should be triggered only if credentials are already stored...
        if not os.path.exists(credentialsFile):
            raise ValueError(missingCredentials)

        # Read credentials, either from json or from netrc (according to "specs")
        if credentialsFile.endswith('.json'):
            with open(credentialsFile, 'r') as file:
                data = json.load(file)
                key = data[specs['key_string']]
                secret = data[specs['secret_string']]
        elif credentialsFile.endswith('netrc'):
            credLine = f'machine {specs["URL_string"].split("://")[-1]}'
            os.chmod(credentialsFile, stat.S_IRUSR | stat.S_IWUSR)

            with open(credentialsFile, 'r') as file:
                lines = file.readlines()

            line_to_keep = [line for line in lines if credLine in line]

            if len(line_to_keep) != 1:
                raise ValueError(missingCredentials)

            # Search for the pattern in the line
            match = re.search(r"%s (.*?) %s (.*)" % (specs['key_string'],specs['secret_string']), line_to_keep[0])

            if match:
                key = match.group(1)  # Value after 'login'
                secret = match.group(2)  # Value after 'password'
            else:
                raise ValueError(missingCredentials)

        return key,secret

    # Function to save user credentials
    @staticmethod
    def save_user_credentials(specs: dict,key: str,secret: str) -> None:
        '''
        specs: a dictionary with the specifications according to credentialsID (output of function credentialsSpec)
        key: a string, the key/username/URL
        secret: a string, the secret/password

        Save user credentials
        '''

        # Unpack specs
        key_string      = specs['key_string']
        secret_string   = specs['secret_string']
        credentialsFile = specs['credentialsFile']
        URL_string      = specs['URL_string']

        # ECMWF: Remove "key:" and "url:" in case user incidentally copied that from ECMWF source
        if specs['credentialsID'] in ['ECMWF_ADS', 'ECMWF_CDS']:
            if key.startswith('url:'):
                key = key[4:]
            if secret.startswith('key:'):
                secret = secret[4:]

        # "strip" removes extra spaces in case password was copied-pasted with extra spaces on the sides.
        credentials = {
            key_string: key.strip(),
            secret_string: secret.strip()
        }

        # Save credentials differently if file is JSON or netrc (JSON or netrc according to credentials "specs")
        if credentialsFile.endswith('.json'):
            with open(credentialsFile, "w") as f:
                json.dump(credentials, f, indent=4)
        elif credentialsFile.endswith('netrc'):
            credLine = f'machine {URL_string.split("://")[-1]} {key_string} {key} {secret_string} {secret}\n'
            if not os.path.exists(credentialsFile):
                with open(credentialsFile, 'w') as fo:
                    fo.write(credLine)
                fo.close()
                os.chmod(credentialsFile, stat.S_IRUSR | stat.S_IWUSR)
            else:
                os.chmod(credentialsFile, stat.S_IRUSR | stat.S_IWUSR)
                with open(credentialsFile, 'a') as fo:
                    fo.write(credLine)
                fo.close()

        return

    #
    @staticmethod
    def messageBox(title: str,text: str,boxType: str, cancelButton: bool = False, PyQT_or_Tk: str = 'PyQT') -> None:
        '''
        Message box after submit button is clicked

        title: a string. The title of the message box
        text: a string. the title of the message box
        boxType: a string, the message box type, either 'Information' or 'Warning'.
        cancelButton: a boolean, if True add a Cancel button (default=False)
        PyQT_or_Tk: a string, either 'PyQT' or 'Tk' (default='PyQT')
        '''

        if PyQT_or_Tk == 'PyQT':
            from PyQt5.QtWidgets import QMessageBox
            msg_box = QMessageBox()
            if boxType == 'Information':
                msg_box.setIcon(QMessageBox.Information)
                window_pop_up.deleteLater()
            elif boxType == 'Warning':
                msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle(title)
            msg_box.setText(text)
            if cancelButton:
                msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                result = msg_box.exec() == QMessageBox.Ok
            else:
                msg_box.setStandardButtons(QMessageBox.Ok)
                result = True
                msg_box.exec()
        elif PyQT_or_Tk == 'Tk':
            from tkinter import messagebox
            if boxType == 'Information':
                messagebox.showinfo(title, text)
                result = True
                root.destroy()
            elif boxType == 'Warning':
                if cancelButton:
                    result = messagebox.askokcancel(title, text, icon="warning")
                else:
                    messagebox.showwarning(title, text)
                    result = True
        return result

    # Function to handle submission of key and secret
    @staticmethod
    def submit(specs: dict,key: str,secret: str, PyQT_or_Tk: str = 'PyQT') -> None:
        '''
        specs: a dictionary with the specifications according to credentialsID (output of function credentialsSpec)

        Action: either save or show error if either key or secret were not properly inputted in pop-up window
        '''

        if key and secret:
            GetAnc_credentials.save_user_credentials(specs,key,secret)
            _ = GetAnc_credentials.messageBox('Success', 'Credentials and settings saved successfully!','Information',PyQT_or_Tk=PyQT_or_Tk)
        else:
            _ = GetAnc_credentials.messageBox('Input Error', "Please, don't leave empty fields!",'Warning',PyQT_or_Tk=PyQT_or_Tk)
        return

    @staticmethod
    def custom_close_event(event) -> None:
        # Schedule the window for deletion
        window_pop_up.deleteLater()

        # Accept the event (allow the window to close)
        event.accept()
        return

    # Pop-up window: PyQt implementation
    @staticmethod
    def create_popup_PyQT(specs: dict) -> None:
        '''
        specs: a dictionary with the specifications according to credentialsID (output of function credentialsSpec)

        Define the pop-up window to input credentials
        '''

        from PyQt5 import QtWidgets, QtGui, QtCore

        global app_pop_up, window_pop_up

        # Unpack specs
        title                = specs['title']
        key_string           = specs['key_string']
        secret_string        = specs['secret_string']
        URL_string           = specs['URL_string']
        icon_path            = specs['icon_path']
        obtainCredsString    = specs['obtainCredsString']
        storeCredsString     = specs['storeCredsString']

        window_pop_up = QtWidgets.QDialog()
        window_pop_up.setWindowTitle(title)
        window_pop_up.resize(400, 200)

        app_pop_up_icon = QtGui.QIcon(icon_path)
        window_pop_up.setWindowIcon(app_pop_up_icon)
        window_pop_up.closeEvent = GetAnc_credentials.custom_close_event

        layout = QtWidgets.QVBoxLayout()

        label = QtWidgets.QLabel(storeCredsString)
        layout.addWidget(label)

        key_label = QtWidgets.QLabel(key_string.title())
        layout.addWidget(key_label)
        key_entry = QtWidgets.QLineEdit()
        layout.addWidget(key_entry)

        secret_label = QtWidgets.QLabel(secret_string.title())
        layout.addWidget(secret_label)
        secret_entry = QtWidgets.QLineEdit()
        secret_entry.setEchoMode(QtWidgets.QLineEdit.Password)
        layout.addWidget(secret_entry)

        link_button = QtWidgets.QLabel('<a href="%s">%s</a>' % (URL_string,obtainCredsString))
        link_button.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
        link_button.setOpenExternalLinks(True)
        link_button.linkActivated.connect(lambda: webbrowser.open(URL_string))
        layout.addWidget(link_button)

        submit_button = QtWidgets.QPushButton("Submit")
        submit_button.clicked.connect(lambda: GetAnc_credentials.submit(specs, key_entry.text(), secret_entry.text(), PyQT_or_Tk='PyQT'))
        layout.addWidget(submit_button)

        window_pop_up.setLayout(layout)
        window_pop_up.exec()

        return

    # Pop-up window: Tk implementation
    @staticmethod
    def create_popup_Tk(specs: dict) -> None:
        '''
        specs: a dictionary with the specifications according to credentialsID (output of function credentialsSpec)

        Define the pop-up window to input credentials
        '''

        # Unpack specs
        title                = specs['title']
        key_string           = specs['key_string']
        secret_string        = specs['secret_string']
        URL_string           = specs['URL_string']
        icon_path            = specs['icon_path']
        obtainCredsString    = specs['obtainCredsString']
        storeCredsString     = specs['storeCredsString']

        global root

        import tkinter as tk
        from PIL import Image, ImageTk

        # Tkinter window initialization
        root = tk.Tk()

        # Set minimum size for the window
        root.minsize(400, 200)
        root.title(title)
        root.geometry("450x180")
        root.option_add("*Font", "Helvetica 10")
        root.configure(bg='#f0f0f0')
        root.option_add("*Button*background",'#f0f0f0')
        root.option_add("*Entry*background",'#f0f0f0')
        root.option_add("*Label*background",'#f0f0f0')
        root.option_add("*Checkbutton*background",'#f0f0f0')

        # Read icon (specific to ancillary source)
        load_icon = Image.open(icon_path)
        render = ImageTk.PhotoImage(load_icon) # Loads the given icon
        root.iconphoto(False, render)

        # Define frame
        frame = tk.Frame(root)
        frame.grid(row=0, columnspan=2, padx=10, pady=5)

        # Define fonts
        normal_font = ('Helvetica', 10)
        bold_font = ('Helvetica', 10, 'bold')

        # Create labels for normal and bold parts
        _ = tk.Label(frame, text=storeCredsString, font=normal_font).pack(side="left")

        # Key entry
        tk.Label(root, text=key_string.title()).grid(row=1, column=0, padx=10, pady=5)
        key_entry = tk.Entry(root,bg='white')
        key_entry.grid(row=1, column=1, padx=10, pady=5)

        # Secret entry (with ***)
        tk.Label(root, text=secret_string.title()).grid(row=2, column=0, padx=10, pady=5)
        secret_entry = tk.Entry(root, show="*",bg='white')
        secret_entry.grid(row=2, column=1, padx=10, pady=5)

        # Hyperlink to URL
        link_label = tk.Label(root, text=obtainCredsString, fg="blue", cursor="hand2")
        link_label.grid(row=4, columnspan=2, padx=10, pady=5)
        link_label.bind("<Button-1>", lambda event: webbrowser.open(URL_string))

        # Submit button
        submit_button = tk.Button(root, text="Submit", command=lambda: GetAnc_credentials.submit(specs, key_entry.get(), secret_entry.get(), PyQT_or_Tk='Tk'))
        submit_button.grid(row=5, columnspan=2, padx=10, pady=5)

        # Run input credentials window
        root.mainloop()

        return

    # Pop-up window to save credentials
    @staticmethod
    def credentialsWindow(credentialsID: str,PyQT_or_Tk: str = 'PyQT') -> None:
        '''
        Main credentials window function.
        credentialsID: a string, 'EUMETSAT_Data_Store', 'NASA_Earth_Data', 'ECWMF_ADS' or 'ECMWF_CDS'

        Action: if credentials not stored, open pop-up window to input credentials.
        '''
        specs = GetAnc_credentials.credentialsSpec(credentialsID)

        # If credentials not stored, pop-up window.
        if not GetAnc_credentials.credentials_stored(credentialsID):
            if PyQT_or_Tk == 'PyQT':
                # HyperCP
                specs['icon_path'] = os.path.join(os.path.dirname(__file__), '..', 'Data', 'Img', '%s_logo.png' % credentialsID)
                GetAnc_credentials.create_popup_PyQT(specs)
            elif PyQT_or_Tk == 'Tk':
                # ThoMaS
                specs['icon_path'] = os.path.join(os.path.dirname(__file__), '%s_logo.png' % credentialsID)
                GetAnc_credentials.create_popup_Tk(specs)
        else:
            print("%s: Credentials already available at: %s" % (credentialsID,specs['credentialsFile']))

        return