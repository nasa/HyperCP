
import os
import platform
import obpgSession

username = "daurin"
password = "EarthData2019"
server = 'oceandata.sci.gsfc.nasa.gov'
cwd = os.getcwd()
home = os.path.expanduser('~')

# Anc to grab
year = 2018
doy = 141
hr = 12

if platform.system() == 'Windows':    
    netrcFile = os.path.join(home,'_netrc')
else: 
    netrcFile = os.path.join(home,'.netrc')

if not os.path.exists(netrcFile):
    with open(netrcFile, 'w') as fo:
        fo.write(f'machine urs.earthdata.nasa.gov login {username} password {password}\n')
else:
    # print('netrc found')
    fo = open(netrcFile)
    lines = fo.readlines()
    fo.close()
    # This will find and replace or add the Earthdata server
    foundED = False
    for i, line in enumerate(lines):
        if 'machine urs.earthdata.nasa.gov login' in line:
            foundED = True
            lineIndx = i

    if foundED == True:
        lines[lineIndx] = f'machine urs.earthdata.nasa.gov login {username} password {password}\n'
    else:
        lines = lines + [f'\nmachine urs.earthdata.nasa.gov login {username} password {password}\n']

    # with open(netrcFile, "w") as fo:
    fo = open(netrcFile,"w")
    fo.writelines(lines)
    fo.close()

file1 = f"N{year}{doy:03.0f}{hr:02.0f}_MERRA2_1h.nc"
filePath1 = os.path.join(cwd)
request = f"/cgi/getfile/{file1}"
print(f'File to get: {request}')

status = obpgSession.httpdl(server, request, localpath=filePath1, 
    outputfilename=file1, uncompress=False, verbose=2)


