import tkinter as tk
from PIL import Image, ImageTk
from tkinter import messagebox
import json
import os
import re
import numpy as np
import webbrowser
import platform
import stat

# Erase already existing user credentials
def erase_user_credentials(credentialsID):
    '''
    Erase credentials line in file (netrc case) or full credentials file (json case)

    credentialsID: a string, 'NASA_Earth_Data', 'ECWMF_ADS' or 'ECMWF_CDS'
    '''

    # Determine case
    specs = credentialsSpec(credentialsID)
    credentialsFile = os.path.join(os.path.expanduser('~'),specs['credentials_filename'])

    # If file does not even exist, return.
    if not os.path.exists(credentialsFile):
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
def credentials_stored(credentialsID):
    '''
    Check if credentials are already stored.

    credentialsID: a string, 'NASA_Earth_Data', 'ECWMF_ADS' or 'ECMWF_CDS'

    return: credentialsStored, a Boolean.
    '''
    specs = credentialsSpec(credentialsID)
    credentialsFile = os.path.join(os.path.expanduser('~'), specs['credentials_filename'])

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
def read_user_credentials(credentialsID):
    '''
    Read user credentials

    credentialsID: a string, 'NASA_Earth_Data', 'ECWMF_ADS' or 'ECMWF_CDS'
    '''

    specs = credentialsSpec(credentialsID)
    credentialsFile = os.path.join(os.path.expanduser('~'), specs['credentials_filename'])

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
def save_user_credentials(key_string, secret_string, key, secret, credentialsFile, URL_string):
    '''
    Save user credentials

    key_string: a string, how the key is called (depends on credentials specs)
    secret_string: a string, how the secret is called (depends on credentials specs)
    key: a string, the key (aka the user or url)
    secret: a string, the secret (aka password)
    credentialsFile: a string, /full/path/to/credentials/file
    URL_string: a string, the url to be stored in given netrc line ("https:://" or similar prefix is removed)
    '''

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

# Function to handle submission of key and secret
def submit(key_string, secret_string, credentials_filename, URL_string):
    '''
    Action: either save or show error if either key or secret were not properly inputted in pop-up window

    key_string: a string, how the key is called (depends on credentials specs)
    secret_string: a string, how the secret is called (depends on credentials specs)
    key: a string, the key (aka the user or url)
    secret: a string, the secret (aka password)
    credentialsFile: a string, credentials filename (not full path)
    URL_string: a string, the url to be stored in given netrc line ("https:://" or similar prefix is removed)
    '''

    credentialsFile = os.path.join(os.path.expanduser('~'), credentials_filename)
    key = key_entry.get()
    secret = secret_entry.get()

    if key and secret:
        save_user_credentials(key_string, secret_string, key, secret, credentialsFile, URL_string)
        messagebox.showinfo("Success", "Credentials and settings saved successfully!")
        root.destroy()
    else:
        messagebox.showwarning("Input Error", "Please, don't leave empty fields!")
    return

# Create the main popup window
def create_popup(title, key_string, secret_string, credentials_filename, URL_string, credentialsID):
    '''
    Define the pop-up window to input credentials

    title: a string, the title of the pop-up window
    key_string: a string, how the key is called (depends on credentials specs)
    secret_string: a string, how the secret is called (depends on credentials specs)
    key: a string, the key (aka the user or url)
    secret: a string, the secret (aka password)
    credentialsFile: a string, credentials filename (not full path)
    URL_string: a string, the url to be stored in given netrc line ("https:://" or similar prefix is removed)
    credentialsID: a string, 'NASA_Earth_Data', 'ECWMF_ADS' or 'ECMWF_CDS'
    '''


    global root, key_entry, secret_entry

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
    icon_path = os.path.join(os.path.dirname(__file__),'..','Data','Img','%s_logo.png' % credentialsID)
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
    label1 = tk.Label(frame, text="Store ", font=normal_font).pack(side="left")
    label2 = tk.Label(frame, text=credentialsID.replace('_',' '), font=bold_font).pack(side="left")
    label3 = tk.Label(frame, text=" credentials in your home directory.", font=normal_font).pack(side="left")

    # Key entry
    tk.Label(root, text=key_string.title()).grid(row=1, column=0, padx=10, pady=5)
    key_entry = tk.Entry(root,bg='white')
    key_entry.grid(row=1, column=1, padx=10, pady=5)

    # Secret entry (with ***)
    tk.Label(root, text=secret_string.title()).grid(row=2, column=0, padx=10, pady=5)
    secret_entry = tk.Entry(root, show="*",bg='white')
    secret_entry.grid(row=2, column=1, padx=10, pady=5)

    # Hyperlink to URL
    link_label = tk.Label(root, text='Click here to obtain these credentials', fg="blue", cursor="hand2")
    link_label.grid(row=4, columnspan=2, padx=10, pady=5)
    link_label.bind("<Button-1>", lambda event: webbrowser.open(URL_string))

    # Submit button
    submit_button = tk.Button(root, text="Submit", command=lambda: submit(key_string, secret_string, credentials_filename, URL_string))
    submit_button.grid(row=5, columnspan=2, padx=10, pady=5)

    # Run input credentials window
    root.mainloop()

    return

# Credentials specifications for the different ancillary sources
def credentialsSpec(credentialsID):
    '''
    Define credentials specifications.

    credentialsID: a string, 'NASA_Earth_Data', 'ECWMF_ADS' or 'ECMWF_CDS'

    output: a dictionary with the specifications bounded to credentialsID
    '''

    out = {}

    if credentialsID == 'NASA_Earth_Data':
        if platform.system() == 'Windows':
            out['credentials_filename'] = '_netrc'
        else:
            out['credentials_filename'] = '.netrc'
        out['title'] = 'Login NASA Earth Data credentials - MERRA-2 Ancillary'
        out['key_string'] = 'login'
        out['secret_string'] = 'password'
        out['URL_string'] = 'https://urs.earthdata.nasa.gov'
    elif credentialsID == 'ECMWF_ADS':
        out['credentials_filename'] = '.ecmwf_ads_credentials.json'
        out['title'] = 'Login ECMWF ADS credentials - EAC-4 Ancillary'
        out['key_string'] = 'url'
        out['secret_string'] = 'key'
        out['URL_string'] = 'https://ads.atmosphere.copernicus.eu/how-to-api'
    elif credentialsID == 'ECMWF_CDS':    # Not actually used in HyperCP, kept just in case...
        out['credentials_filename'] = '.ecmwf_cds_credentials.json'
        out['title'] = 'Login ECMWF CDS credentials - ERA-5 Ancillary'
        out['key_string'] = 'url'
        out['secret_string'] = 'key'
        out['URL_string'] = 'https://cds.climate.copernicus.eu/how-to-api'

    return out

# Pop-up window to save credentials
def credentialsWindow(credentialsID):
    '''
    Main credentials window function.
    credentialsID: a string, 'NASA_Earth_Data', 'ECWMF_ADS' or 'ECMWF_CDS'

    Action: if credentials not stored, open pop-up window to input credentials.
    '''

    # Specifications assigned from credentialsID
    specs = credentialsSpec(credentialsID)
    credentialsFile = os.path.join(os.path.expanduser('~'), specs['credentials_filename'])

    # If credentials not stored, pop-up window.
    if not credentials_stored(credentialsID):
        create_popup(specs['title'],
                     specs['key_string'],
                     specs['secret_string'],
                     specs['credentials_filename'],
                     specs['URL_string'],
                     credentialsID)
    else:
        print("%s: Credentials already available at: %s" % (credentialsID,credentialsFile))