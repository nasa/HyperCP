"""Read raw Sea-Bird file"""
import sys
import logging

from Source.Utilities import Utilities

class RawFileReader:
    """Read raw Sea-Bird file"""
    MAX_TAG_READ = 32
    MAX_BLOCK_READ = 1024
    SATHDR_READ = 128
    RESET_TAG_READ = MAX_TAG_READ-16

    # Function for reading SATHDR (Header) messages
    # Messages are in format: SATHDR <Value> (<Name>)\r\n
    @staticmethod
    def readSATHDR(hdr):

        if sys.version_info[0] < 3:
            end = hdr.find(b"\x0D\x0A".decode("string_escape"))
        else:
            end = hdr.find(bytes(b"\x0D\x0A".decode("unicode_escape"), "utf-8"))

        # BUG: TO DO: This is still screwing up the SAS SERIAL NUMBER hdr
        sp1 = hdr.find(b" ") # returns the first occurence where substring is found
        # sp2 = hdr.rfind(b" ") # returns the highest index where substring is found
        sp2 = hdr.find(b"(") - 1

        if sys.version_info[0] < 3:
            str1 = hdr[sp1+1:sp2]
            str2 = hdr[sp2+2:end-1]
        else:
            try:
                str1 = hdr[sp1 + 1:sp2].decode('utf-8')
                str2 = hdr[sp2 + 2:end - 1].decode('utf-8')
            except UnicodeDecodeError:
                logging.debug("HOCR raw header contains non UTF-8 encoded character")
                str1 = hdr[sp1 + 1:sp2].decode('utf-8', 'ignore')
                str2 = hdr[sp2 + 2:end - 1].decode('utf-8', 'ignore')


        #print(str1, str2)

        if len(str1) == 0:
            str1 = "Missing"
        return (str2, str1)

    # Reads a raw file
    @staticmethod
    def readRawFile(filepath, calibrationMap, contextMap, root):

        posframe = 1

        # Note: Prosoft adds posframe=1 to the GPS for some reason
        # print(contextMap.keys())
        #gpsGroup = contextMap["$GPRMC"]
        #ds = gpsGroup.getDataset("POSFRAME")
        #ds.appendColumn(u"COUNT", posframe)
        posframe += 1

        with open(filepath, 'rb') as f:
            while 1:
                # Reads binary file to find message frame tag
                pos = f.tell()
                b = f.read(RawFileReader.MAX_TAG_READ)
                f.seek(pos)

                if "SATHSE" in str(b):
                    pass
                if not b:
                    break

                #print b
                for i in range(0, RawFileReader.MAX_TAG_READ):
                    testString = b[i:].upper()
                    #print("test: ", testString[:6])

                    # Reset file position on max read
                    if i == RawFileReader.MAX_TAG_READ-1:
                        #f.read(RawFileReader.MAX_TAG_READ)
                        f.read(RawFileReader.RESET_TAG_READ)
                        break

                    # Detects message type from frame tag
                    if testString.startswith(b"SATHDR"):
                        #print("SATHDR")
                        if i > 0:
                            f.read(i)
                        hdr = f.read(RawFileReader.SATHDR_READ)
                        (k,v) = RawFileReader.readSATHDR(hdr)
                        root.attributes[k] = v
                        # BUG: Some are not getting TIME-STAMP from SATHDR
                        print(f"{k}: {v}")

                        break
                    else:
                        num = 0
                        for key in calibrationMap:
                            cf = calibrationMap[key]
                            if testString.startswith(cf.id.upper().encode("utf-8")):
                                if i > 0:
                                    f.read(i)

                                pos = f.tell()
                                msg = f.read(RawFileReader.MAX_BLOCK_READ)
                                f.seek(pos)

                                gp = contextMap[cf.id]
                                # Only the first time through
                                if len(gp.attributes) == 0:
                                    #gp.id += "_" + cf.id
                                    gp.id = key
                                    gp.attributes["CalFileName"] = key
                                    gp.attributes["FrameTag"] = cf.id

                                # if key.startswith('SATPYR'):
                                #     print('curious...')

                                try:
                                    num = cf.convertRaw(msg, gp)
                                except Exception:
                                    pmsg = f'Unable to convert the following raw message: {msg}'
                                    print(pmsg)
                                    Utilities.writeLogFile(pmsg)

                                if num >= 0:
                                    # Generate POSFRAME
                                    ds = gp.getDataset("POSFRAME")
                                    if ds is None:
                                        ds = gp.addDataset("POSFRAME")
                                    ds.appendColumn("COUNT", posframe)
                                    posframe += 1
                                    f.read(num)

                                break
                        if num > 0:
                            break
                        