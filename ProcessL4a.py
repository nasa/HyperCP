import HDFRoot
#import HDFGroup
#import HDFDataset


from BandData import MODIS, Sentinel3


class ProcessL4a:

    @staticmethod
    def calculateBand(rrsData, band):
        #print("Calculate Band")
        n = len(list(rrsData.columns.values())[0])
        m = len(band["lambda"])
        result = []

        # For each row of rrs data
        for i in range(n):
            srf_sum = 0
            c_sum = 0.0

            # For each lamda in band
            for j in range(m):
                ld = str(band["lambda"][j]) + ".0"
                srf = band["response"][j]
                #print("ld, srf",ld,srf)

                # Check if lamda in rrs
                if ld in rrsData.columns:
                    rrs = rrsData.columns[ld][i]
                    #print("srf, rrs", srf, rrs)
                    srf_sum += rrs*srf
                    c_sum += band["response"][j]

            # Calculate srf value for that band
            c = 1/c_sum
            result.append(c * srf_sum)

        return result

    
    @staticmethod
    def processMODISBands(rrsData, bandData):
        print("Process MODIS Bands")
        rrsData.datasetToColumns()
        rrsColumns = rrsData.columns
        
        date = rrsColumns["Datetag"]
        tt2 = rrsColumns["Timetag2"]
        
        bandData.columns["Datetag"] = date
        bandData.columns["Timetag2"] = tt2

        if "Latpos" in rrsColumns:
            latpos = rrsColumns["Latpos"]
            lonpos = rrsColumns["Lonpos"]
            bandData.columns["Latpos"] = latpos
            bandData.columns["Lonpos"] = lonpos
        
        bandData.columns["Band1"] = ProcessL4a.calculateBand(rrsData, MODIS.band1)
        bandData.columns["Band3"] = ProcessL4a.calculateBand(rrsData, MODIS.band3)
        bandData.columns["Band4"] = ProcessL4a.calculateBand(rrsData, MODIS.band4)
        bandData.columns["Band8"] = ProcessL4a.calculateBand(rrsData, MODIS.band8)
        bandData.columns["Band9"] = ProcessL4a.calculateBand(rrsData, MODIS.band9)
        bandData.columns["Band10"] = ProcessL4a.calculateBand(rrsData, MODIS.band10)
        bandData.columns["Band11"] = ProcessL4a.calculateBand(rrsData, MODIS.band11)
        bandData.columns["Band12"] = ProcessL4a.calculateBand(rrsData, MODIS.band12)
        bandData.columns["Band13"] = ProcessL4a.calculateBand(rrsData, MODIS.band13)
        bandData.columns["Band14"] = ProcessL4a.calculateBand(rrsData, MODIS.band14)
        bandData.columns["Band15"] = ProcessL4a.calculateBand(rrsData, MODIS.band15)
        
        bandData.columnsToDataset()


    @staticmethod
    def processSentinel3Bands(rrsData, bandData):
        print("Process Sentinel3 Bands")
        rrsData.datasetToColumns()
        rrsColumns = rrsData.columns
        
        date = rrsColumns["Datetag"]
        tt2 = rrsColumns["Timetag2"]
        
        bandData.columns["Datetag"] = date
        bandData.columns["Timetag2"] = tt2

        if "Latpos" in rrsColumns:
            latpos = rrsColumns["Latpos"]
            lonpos = rrsColumns["Lonpos"]
            bandData.columns["Latpos"] = latpos
            bandData.columns["Lonpos"] = lonpos

        bandData.columns["Band1"] = ProcessL4a.calculateBand(rrsData, Sentinel3.band1)
        bandData.columns["Band2"] = ProcessL4a.calculateBand(rrsData, Sentinel3.band2)
        bandData.columns["Band3"] = ProcessL4a.calculateBand(rrsData, Sentinel3.band3)
        bandData.columns["Band4"] = ProcessL4a.calculateBand(rrsData, Sentinel3.band4)
        bandData.columns["Band5"] = ProcessL4a.calculateBand(rrsData, Sentinel3.band5)
        bandData.columns["Band6"] = ProcessL4a.calculateBand(rrsData, Sentinel3.band6)
        bandData.columns["Band7"] = ProcessL4a.calculateBand(rrsData, Sentinel3.band7)
        bandData.columns["Band8"] = ProcessL4a.calculateBand(rrsData, Sentinel3.band8)
        bandData.columns["Band9"] = ProcessL4a.calculateBand(rrsData, Sentinel3.band9)
        bandData.columns["Band10"] = ProcessL4a.calculateBand(rrsData, Sentinel3.band10)
        bandData.columns["Band11"] = ProcessL4a.calculateBand(rrsData, Sentinel3.band11)
        bandData.columns["Band12"] = ProcessL4a.calculateBand(rrsData, Sentinel3.band12)
        bandData.columns["Band13"] = ProcessL4a.calculateBand(rrsData, Sentinel3.band13)
        
        bandData.columnsToDataset()



    # Converts Rrs to satellite bands
    @staticmethod
    def processL4a(node):
        print("Process L4a")

        root = HDFRoot.HDFRoot()
        root.copy(node)
        #root.copyAttributes(node)

        satelliteGroup = root.addGroup("Satellite")
        #bandData = satelliteGroup.addDataset("Bands")
        modisData = satelliteGroup.addDataset("MODIS")
        sentinel3Data = satelliteGroup.addDataset("Sentinel3")
        
        reflectanceGroup = node.getGroup("Reflectance")
        rrsData = reflectanceGroup.getDataset("Rrs")

        ProcessL4a.processMODISBands(rrsData, modisData)
        ProcessL4a.processSentinel3Bands(rrsData, sentinel3Data)

return root