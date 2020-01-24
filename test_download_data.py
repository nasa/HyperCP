
import os
import urllib.request as ur
import requests
# import base64

'''conda install -c anaconda certifi''' # Does not solve the SSL: CERTIFICATE_VERIFY_FAILED error

username = "daurin"
password = "EarthData2019"

year = 2018
doy = 141
hr = 12
cwd = os.getcwd()

file1 = f"N{year}{doy:03.0f}{hr:02.0f}_MERRA2_1h.nc"
# filePath1 = os.path.join(cwd,"Data","Anc",file1)
filePath1 = os.path.join(cwd,file1)
url = f"https://oceandata.sci.gsfc.nasa.gov/cgi/getfile/{file1}"
print(f'File to get: {url}')

''' Before'''
# ur.urlretrieve(url, filePath1)

''' Now '''
 # create a password manager
password_mgr = ur.HTTPPasswordMgrWithDefaultRealm()

# Add the username and password.
# If we knew the realm, we could use it instead of None.
top_level_url = "https://urs.earthdata.nasa.gov"
password_mgr.add_password(None, top_level_url, username, password)
handler = ur.HTTPBasicAuthHandler(password_mgr)

# create "opener" (OpenerDirector instance)
opener = ur.build_opener(handler)

# use the opener to fetch a URL
'''I do not understand this line. Guessed at url to use'''
# opener.open(top_level_url)
opener.open(url)

# Install the opener.
# Now all calls to urllib.request.urlopen use our opener.
ur.install_opener(opener)

filedata = ur.urlopen(url).read()

# base64string = base64.b64encode(bytes('%s:%s' % (username, password),'ascii'))
# request.add_header("Authorization", "Basic %s" % base64string.decode('utf-8'))

# filedata = requests.get(url, auth=(username,password))
print(f'File status: {filedata.status_code}')

if filedata.status_code == 200:
    with open(filePath1, 'wb') as out:
        for bits in filedata.iter_content():
            out.write(bits)