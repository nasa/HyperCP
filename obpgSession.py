

import os
import re
import subprocess
import requests
from requests.adapters import HTTPAdapter
import logging
import platform

DEFAULT_CHUNK_SIZE = 131072

# requests session object used to keep connections around
obpgSession = None

def getSession(verbose=0, ntries=5):
    global obpgSession

    if not obpgSession:
        # turn on debug statements for requests
        if verbose > 1:
            logging.basicConfig(level=logging.DEBUG)
        obpgSession = requests.Session()
        obpgSession.mount('https://', HTTPAdapter(max_retries=ntries))
        if verbose:
            print("OBPG session started")
    else:
        if verbose > 1:
            print("reusing existing OBPG session")

    return obpgSession

def httpdl(server, request, localpath='.', outputfilename=None, ntries=5,
           uncompress=False, timeout=30., verbose=0,
           chunk_size=DEFAULT_CHUNK_SIZE):
    status = 0
    urlStr = 'https://' + server + request

    global obpgSession
    getSession(verbose=verbose, ntries=ntries)

    with obpgSession.get(urlStr, stream=True, timeout=timeout) as req:
        ctype = req.headers.get('Content-Type')
        if verbose:
            print(f'Status code: {req.status_code}')
            print(f'ctype: {ctype}')

        if req.status_code in (400, 401, 403, 404, 416):
            status = req.status_code
        elif ctype and ctype.startswith('text/html'):
            status = 401
        else:
            if not os.path.exists(localpath):
                os.umask(0o02)
                os.makedirs(localpath, mode=0o2775)
   
            if not outputfilename:
                cd = req.headers.get('Content-Disposition')
                if cd:
                    outputfilename = re.findall("filename=(.+)", cd)[0]
                else:
                    outputfilename = urlStr.split('/')[-1]
   
            ofile = os.path.join(localpath, outputfilename)
       
            with open(ofile, 'wb') as fd:
                if verbose:
                    print(f'Writing file to disk {ofile}')
                for chunk in req.iter_content(chunk_size=chunk_size):
                    if chunk: # filter out keep-alive new chunks
                        fd.write(chunk)
   
            if uncompress and re.search(".(Z|gz|bz2)$", ofile):
                compressStatus = uncompressFile(ofile)
                if compressStatus:
                    status = compressStatus
            else:
               status = 0
 
    return status

def uncompressFile(compressed_file):
    """
    uncompress file
    compression methods:
        bzip2
        gzip
        UNIX compress
    """
 
    compProg = {"gz": "gunzip -f ", "Z": "gunzip -f ", "bz2": "bunzip2 -f "}
    exten = os.path.basename(compressed_file).split('.')[-1]
    unzip = compProg[exten]
    p = subprocess.Popen(unzip + compressed_file, shell=True)
    status = os.waitpid(p.pid, 0)[1]
    if status:
        print("Warning! Unable to decompress %s" % compressed_file)
        return status
    else:
        return 0