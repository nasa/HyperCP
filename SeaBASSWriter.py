
import csv
import os

from HDFRoot import HDFRoot


class SeaBASSWriter:

    @staticmethod
    def writeSeaBASS(name, dirpath, data, sensorName, level):

        # Create output directory
        csvdir = os.path.join(dirpath, 'csv')
        os.makedirs(csvdir, exist_ok=True)

        # Write csv file
        filename = name + "_" + sensorName + "_" + level
        csvPath = os.path.join(csvdir, filename + ".csv")
        #np.savetxt(csvPath, data, delimiter=',')
        with open(csvPath, 'w') as f:
            writer = csv.writer(f)
            writer.writerows(data)


    @staticmethod
    def outputTXT_L1a(fp):
        SeaBASSWriter.outputTXT_Type1(fp, "L1a")

    @staticmethod
    def outputTXT_L1b(fp):
        SeaBASSWriter.outputTXT_Type1(fp, "L1b")

    @staticmethod
    def outputTXT_L2(fp):
        SeaBASSWriter.outputTXT_Type1(fp, "L2")

    # Converts the data into a list of rows
    @staticmethod
    def formatData(ds, dsTimer):
        dataOut = []

        # Add the csv header
        ls = ["Timetag2"] + list(ds.data.dtype.names)
        dataOut.append(ls)

        # Add data for each row
        total = ds.data.shape[0]
        for i in range(total):
            #print(dsTimer.data["NONE"][i])
            ls = [dsTimer.data["NONE"][i]] + ['%f' % num for num in ds.data[i]]
            dataOut.append(ls)

        return dataOut


    # Convert Level 1a, 1b, & 2 data to csv file
    @staticmethod
    def outputTXT_Type1(fp, level):

        # Get filepath of input hdf
        (dirpath, filename) = os.path.split(fp)
        filename = os.path.splitext(filename)[0]

        filepath = os.path.join(dirpath, filename + "_" + level + ".hdf")
        if not os.path.isfile(filepath):
            return

        # Make sure hdf can be read
        root = HDFRoot.readHDF5(filepath)
        if root is None:
            print("outputCSV: root is None")
            return

        #name = filename[28:43]
        name = filename[0:15]

        # Get datasets to output
        esData = None
        liData = None
        ltData = None

        # Find the light data
        for gp in root.groups:
            if gp.attributes["FrameType"] == "ShutterLight":
                if gp.getDataset("ES"):
                    esData = gp.getDataset("ES")
                    esTimer = gp.getDataset("TIMETAG2")
                elif gp.getDataset("LI"):
                    liData = gp.getDataset("LI")
                    liTimer = gp.getDataset("TIMETAG2")
                elif gp.getDataset("LT"):
                    ltData = gp.getDataset("LT")
                    ltTimer = gp.getDataset("TIMETAG2")

        if esData is None or liData is None or ltData is None:
            return

        # Format for output
        es = SeaBASSWriter.formatData(esData, esTimer)
        li = SeaBASSWriter.formatData(liData, liTimer)
        lt = SeaBASSWriter.formatData(ltData, ltTimer)

        # Write csv files
        SeaBASSWriter.writeSeaBASS(name, dirpath, es, "ES", level)
        SeaBASSWriter.writeSeaBASS(name, dirpath, li, "LI", level)
        SeaBASSWriter.writeSeaBASS(name, dirpath, lt, "LT", level)



    @staticmethod
    def outputTXT_L2s(fp):
        SeaBASSWriter.outputTXT_Type2(fp, "L2s")

    @staticmethod
    def outputTXT_L3a(fp):
        SeaBASSWriter.outputTXT_Type2(fp, "L3a")

    # Converts the data into a list of rows
    @staticmethod
    def formatData2(data, timer):
        dataOut = []

        # Add the csv header
        ls = ["Timetag2"] + list(data.dtype.names)
        dataOut.append(ls)

        # Add data for each row
        total = data.shape[0]
        for i in range(total):
            #print(dsTimer.data["NONE"][i])
            ls = [timer[i]] + ['%f' % num for num in data[i]]
            dataOut.append(ls)

        return dataOut

    @staticmethod
    def removeColumns(a, removeNameList):
        return a[[name for name in a.dtype.names if name not in removeNameList]]

    # Convert Level 2s & 3a data to csv file
    @staticmethod
    def outputTXT_Type2(fp, level):

        # Get filepath of input hdf
        (dirpath, filename) = os.path.split(fp)
        filename = os.path.splitext(filename)[0]

        filepath = os.path.join(dirpath, filename + "_" + level +".hdf")
        if not os.path.isfile(filepath):
            return

        # Make sure hdf can be read
        root = HDFRoot.readHDF5(filepath)
        if root is None:
            print("outputCSV: root is None")
            return

        #name = filename[28:43]
        name = filename[0:15]

        # Get datasets to output
        referenceGroup = root.getGroup("Reference")
        sasGroup = root.getGroup("SAS")

        esData = referenceGroup.getDataset("ES_hyperspectral")
        liData = sasGroup.getDataset("LI_hyperspectral")
        ltData = sasGroup.getDataset("LT_hyperspectral")

        if esData is None or liData is None or ltData is None:
            return

        esTT2 = esData.data["Timetag2"]
        liTT2 = liData.data["Timetag2"]
        ltTT2 = ltData.data["Timetag2"]

        esData = SeaBASSWriter.removeColumns(esData.data, ["Datetag", "Timetag2"])
        liData = SeaBASSWriter.removeColumns(liData.data, ["Datetag", "Timetag2"])
        ltData = SeaBASSWriter.removeColumns(ltData.data, ["Datetag", "Timetag2"])

        # Format for output
        es = SeaBASSWriter.formatData2(esData, esTT2)
        li = SeaBASSWriter.formatData2(liData, liTT2)
        lt = SeaBASSWriter.formatData2(ltData, ltTT2)

        # Write SeaBASS files
        SeaBASSWriter.writeSeaBASS(name, dirpath, es, "ES", level)
        SeaBASSWriter.writeSeaBASS(name, dirpath, li, "LI", level)
        SeaBASSWriter.writeSeaBASS(name, dirpath, lt, "LT", level)



    @staticmethod
    def outputTXT_L4(fp):
        SeaBASSWriter.outputTXT_Type3(fp, "L4")
        SeaBASSWriter.outputTXT_Type3(fp, "L4-flags")

    # Converts the data into a list of rows
    @staticmethod
    def formatData3(ds):
        dataOut = []

        # Add the SeaBASS header
        ls = list(ds.data.dtype.names)
        dataOut.append(ls)

        # Add data for each row
        total = ds.data.shape[0]
        for i in range(total):
            ls = ['%f' % num for num in ds.data[i]]
            dataOut.append(ls)

        return dataOut

    # Convert Level 4 data to SeaBASS file
    @staticmethod
    def outputTXT_Type3(fp, level):

        # Get filepath of input hdf
        (dirpath, filename) = os.path.split(fp)
        filename = os.path.splitext(filename)[0]

        filepath = os.path.join(dirpath, filename + "_" + level +".hdf")
        if not os.path.isfile(filepath):
            return

        # Make sure hdf can be read
        root = HDFRoot.readHDF5(filepath)
        if root is None:
            print("outputSeaBASS: root is None")
            return

        #name = filename[28:43]
        name = filename[0:15]

        # Get datasets to output
        gp = root.getGroup("Reflectance")

        esData = gp.getDataset("ES")
        liData = gp.getDataset("LI")
        ltData = gp.getDataset("LT")
        rrsData = gp.getDataset("Rrs")

        if esData is None or liData is None or ltData is None or rrsData is None:
            return

        # Format for output
        es = SeaBASSWriter.formatData3(esData)
        li = SeaBASSWriter.formatData3(liData)
        lt = SeaBASSWriter.formatData3(ltData)
        rrs = SeaBASSWriter.formatData3(rrsData)

        # Write SeaBASS files
        SeaBASSWriter.writeSeaBASS(name, dirpath, es, "ES", level)
        SeaBASSWriter.writeSeaBASS(name, dirpath, li, "LI", level)
        SeaBASSWriter.writeSeaBASS(name, dirpath, lt, "LT", level)
        SeaBASSWriter.writeSeaBASS(name, dirpath, rrs, "RRS", level)

