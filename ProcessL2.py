
import collections
import sys
import warnings

import numpy as np
from numpy import matlib as mb
import scipy as sp
import datetime as datetime
from PyQt5 import QtWidgets

import HDFRoot
from AncillaryReader import AncillaryReader
from Utilities import Utilities
from ConfigFile import ConfigFile
from RhoCorrections import RhoCorrections
from GetAnc import GetAnc
from SB_support import readSB
from Weight_RSR import Weight_RSR


class ProcessL2:

    @staticmethod
    def Thuillier(dateTag, wavelength):
        def dop(year):
            # day of perihelion            
            years = list(range(2001,2031))
            key = [str(x) for x in years]
            day = [4, 2, 4, 4, 2, 4, 3, 2, 4, 3, 3, 5, 2, 4, 4, 2, 4, 3, 3, 5, 2, 4, 4, 3, 4, 3, 3, 5, 2, 3]            
            dop = {key[i]: day[i] for i in range(0, len(key))}            
            result = dop[str(year)]
            return result

        fp = 'Data/Thuillier_F0.sb'
        print("SB_support.readSB: " + fp)
        if not readSB(fp, no_warn=True):
            msg = "Unable to read Thuillier file. Make sure it is in SeaBASS format."
            print(msg)
            Utilities.writeLogFile(msg)  
            return None
        else:
            Thuillier = readSB(fp, no_warn=True)
            F0_raw = np.array(Thuillier.data['esun']) # uW cm^-2 nm^-1
            wv_raw = np.array(Thuillier.data['wavelength'])
            # Earth-Sun distance
            day = int(str(dateTag)[4:7])  
            year = int(str(dateTag)[0:4])  
            eccentricity = 0.01672
            dayFactor = 360/365.256363
            dayOfPerihelion = dop(year)
            dES = 1-eccentricity*np.cos(dayFactor*(day-dayOfPerihelion)) # in AU
            F0_fs = F0_raw*dES

            F0 = sp.interpolate.interp1d(wv_raw, F0_fs)(wavelength)
            # Use the strings for the F0 dict
            wavelengthStr = [str(wave) for wave in wavelength]
            F0 = collections.OrderedDict(zip(wavelengthStr, F0))
        
        return F0

    @staticmethod
    def nirCorrectionSatellite(root, sensor, rrsNIRCorr, nLwNIRCorr):        
        newReflectanceGroup = root.getGroup("REFLECTANCE")
        # newRadianceGroup = root.getGroup("RADIANCE")
        # newIrradianceGroup = root.getGroup("IRRADIANCE")    
        
        newRrsData = newReflectanceGroup.getDataset(f'Rrs_{sensor}')
        newnLwData = newReflectanceGroup.getDataset(f'nLw_{sensor}')       

        
        # These will include all slices in root so far
        # Below the most recent/current slice [-1] will be selected for processing
        rrsSlice = newRrsData.columns
        # rrsSlice.pop("Datetime")
        # rrsSlice.pop("Datetag")
        # rrsSlice.pop("Timetag2")
        nLwSlice = newnLwData.columns
        # nLwSlice.pop("Datetime")
        # nLwSlice.pop("Datetag")
        # nLwSlice.pop("Timetag2")

        for k in rrsSlice:
            if (k != 'Datetime') and (k != 'Datetag') and (k != 'Timetag2'):
                rrsSlice[k][-1] -= rrsNIRCorr
        for k in nLwSlice:
            if (k != 'Datetime') and (k != 'Datetag') and (k != 'Timetag2'):
                nLwSlice[k][-1] -= nLwNIRCorr

    @staticmethod
    def nirCorrection(root, sensor, F0):
        # F0 is sensor specific, but ultimately, SimSpec can only be applied to hyperspectral data anyway, 
        # so output the correction and apply it to satellite bands later.
        simpleNIRCorrection = int(ConfigFile.settings["bL2SimpleNIRCorrection"])
        simSpecNIRCorrection = int(ConfigFile.settings["bL2SimSpecNIRCorrection"])   

        newReflectanceGroup = root.getGroup("REFLECTANCE")        
        newRrsData = newReflectanceGroup.getDataset(f'Rrs_{sensor}')
        newnLwData = newReflectanceGroup.getDataset(f'nLw_{sensor}')
        newRrsDeltaData = newReflectanceGroup.getDataset(f'Rrs_{sensor}_delta')
        newnLwDeltaData = newReflectanceGroup.getDataset(f'nLw_{sensor}_delta')

        # These will include all slices in root so far
        # Below the most recent/current slice [-1] will be selected for processing
        rrsSlice = newRrsData.columns
        # rrsSlice.pop("Datetime")
        # rrsSlice.pop("Datetag")
        # rrsSlice.pop("Timetag2")
        nLwSlice = newnLwData.columns
        # nLwSlice.pop("Datetime")
        # nLwSlice.pop("Datetag")
        # nLwSlice.pop("Timetag2")

        # # Perfrom near-infrared residual correction to remove additional atmospheric and glint contamination
        # if ConfigFile.settings["bL2PerformNIRCorrection"]:
        if simpleNIRCorrection:
            # Data show a minimum near 725; using an average from above 750 leads to negative reflectances
            # Find the minimum between 700 and 800, and subtract it from spectrum (spectrally flat)
            msg = "Perform simple residual NIR subtraction."
            print(msg)
            Utilities.writeLogFile(msg)  
            
            # rrs correction
            NIRRRs = []
            for k in rrsSlice:
                if (k == 'Datetime') or (k == 'Datetag') or (k == 'Timetag2'):
                    continue
                if float(k) >= 700 and float(k) <= 800:
                    # avg += rrsSlice[k]
                    # num += 1
                    NIRRRs.append(rrsSlice[k][-1])
            # avg /= num
            # avg = np.median(NIRRRs)
            rrsNIRCorr = min(NIRRRs)
            # Subtract average from each waveband
            for k in rrsSlice:
                if (k == 'Datetime') or (k == 'Datetag') or (k == 'Timetag2'):
                    continue
                # rrsSlice[k] -= avg
                rrsSlice[k][-1] -= rrsNIRCorr
                # newRrsData.columns[k].append(rrsSlice[k])

            # nLw correction
            NIRRRs = []
            for k in nLwSlice:
                if (k == 'Datetime') or (k == 'Datetag') or (k == 'Timetag2'):
                    continue
                if float(k) >= 700 and float(k) <= 800:
                    NIRRRs.append(nLwSlice[k][-1])
            nLwNIRCorr = min(NIRRRs)
            # Subtract average from each waveband
            for k in nLwSlice:
                if (k == 'Datetime') or (k == 'Datetag') or (k == 'Timetag2'):
                    continue
                nLwSlice[k][-1] -= nLwNIRCorr
                # newnLwData.columns[k].append(nLwSlice[k])            

        elif simSpecNIRCorrection:
            # From Ruddick 2005, Ruddick 2006 use NIR normalized similarity spectrum
            # (spectrally flat)
            msg = "Perform simulated spectrum residual NIR subtraction."
            print(msg)
            Utilities.writeLogFile(msg)  

            # These ratios are for rho = pi*Rrs
            α1 = 2.35 # 720/780 only good for rho(720)<0.03
            α2 = 1.91 # 780/870 try to avoid, data is noisy here
            threshold = 0.03

            # Retrieve Thuilliers
            wavelength = [float(key) for key in F0.keys()]
            F0 = [value for value in F0.values()]

            # Rrs
            ρ720 = []
            x = []
            for k in rrsSlice: 
                if (k == 'Datetime') or (k == 'Datetag') or (k == 'Timetag2'):
                    continue               
                if float(k) >= 700 and float(k) <= 750:
                    x.append(float(k))

                    ρ720.append(np.pi*rrsSlice[k][-1]) # Using current element/slice

            if not ρ720:
                QtWidgets.QMessageBox.critical("Error", "NIR wavebands unavailable")
            ρ1 = sp.interpolate.interp1d(x,ρ720)(720)
            F01 = sp.interpolate.interp1d(wavelength,F0)(720)
            ρ780 = []
            x = []
            for k in rrsSlice:  
                if (k == 'Datetime') or (k == 'Datetag') or (k == 'Timetag2'):
                    continue              
                if float(k) >= 760 and float(k) <= 800:
                    x.append(float(k))
                    ρ780.append(rrsSlice[k][-1])
            if not ρ780:
                QtWidgets.QMessageBox.critical("Error", "NIR wavebands unavailable")
            ρ2 = sp.interpolate.interp1d(x,ρ780)(780)
            F02 = sp.interpolate.interp1d(wavelength,F0)(780)
            ρ870 = []
            x = []
            for k in rrsSlice: 
                if (k == 'Datetime') or (k == 'Datetag') or (k == 'Timetag2'):
                    continue               
                if float(k) >= 850 and float(k) <= 890:
                    x.append(float(k))
                    ρ870.append(rrsSlice[k][-1])
            if not ρ870:
                QtWidgets.QMessageBox.critical("Error", "NIR wavebands unavailable")
            ρ3 = sp.interpolate.interp1d(x,ρ870)(870)
            F03 = sp.interpolate.interp1d(wavelength,F0)(870)
            
            if ρ1 < threshold:
                ε = (α1*ρ2 - ρ1)/(α1-1)
                ε = ε/np.pi # convert to Rrs units
                εnLw = (α1*ρ2*F02/np.pi - ρ1*F01/np.pi)/(α1-1) # convert to nLw units
                msg = f'offset(rrs) = {ε}; offset(nLw) = {εnLw}'
                print(msg)
                Utilities.writeLogFile(msg)  
            else:
                msg = "SimSpec threshold tripped. Using 780/870 instead."
                print(msg)
                Utilities.writeLogFile(msg)  
                ε = (α2*ρ3 - ρ2)/(α2-1)
                ε = ε/np.pi # convert to Rrs units
                εnLw = (α2*ρ3*F03/np.pi - ρ2*F02/np.pi)/(α2-1) # convert to nLw units              
                msg = f'offset(rrs) = {ε}; offset(nLw) = {εnLw}'
                print(msg)
                Utilities.writeLogFile(msg)  
            for k in rrsSlice:
                if (k == 'Datetime') or (k == 'Datetag') or (k == 'Timetag2'):
                    continue
                ''' There seems to be some confusion in the Ruddick 2005 SPIE paper.
                By this method, ε is (and should be) negative, and so must be added 
                rather than subtracted.''' 
                # rrsSlice[k] -= ε
                rrsSlice[k][-1] += ε
                nLwSlice[k][-1] += εnLw

            rrsNIRCorr = -ε
            nLwNIRCorr = -εnLw
        
        newRrsData.columnsToDataset()
        newnLwData.columnsToDataset()
        newRrsDeltaData.columnsToDataset()
        newnLwDeltaData.columnsToDataset()
        
        return rrsNIRCorr, nLwNIRCorr
    
    @staticmethod
    def spectralReflectance(root, sensor, timeObj, xSlice, F0, rhoScalar, rhoDelta, rhoVec, rhoVecDelta, waveSubset):
        ''' The slices, stds, F0, rhoVec, and rhoVecDelta here are sensor-waveband specific '''
        esXSlice = xSlice['es']
        esXstd = xSlice['esSTD']
        liXSlice = xSlice['li']
        liXstd = xSlice['liSTD']
        ltXSlice = xSlice['lt']
        ltXstd = xSlice['ltSTD']
        dateTime = timeObj['dateTime']
        dateTag = timeObj['dateTag']
        timeTag = timeObj['timeTag']

        rhoDefault = float(ConfigFile.settings["fL2RhoSky"])
        RuddickRho = int(ConfigFile.settings["bL2RuddickRho"])
        ZhangRho = int(ConfigFile.settings["bL2ZhangRho"])
        
       # Root (new/output) groups:
        newReflectanceGroup = root.getGroup("REFLECTANCE")
        newRadianceGroup = root.getGroup("RADIANCE")
        newIrradianceGroup = root.getGroup("IRRADIANCE")        

        # If this is the first ensemble spectrum, set up the new datasets
        if not (f'Rrs_{sensor}' in newReflectanceGroup.datasets):           
            newRrsData = newReflectanceGroup.addDataset(f"Rrs_{sensor}")
            newESData = newIrradianceGroup.addDataset(f"ES_{sensor}")      
            newLIData = newRadianceGroup.addDataset(f"LI_{sensor}")
            newLTData = newRadianceGroup.addDataset(f"LT_{sensor}")
            newnLwData = newReflectanceGroup.addDataset(f"nLw_{sensor}")

            newRrsDeltaData = newReflectanceGroup.addDataset(f"Rrs_{sensor}_delta")
            newESDeltaData = newIrradianceGroup.addDataset(f"ES_{sensor}_delta")       
            newLIDeltaData = newRadianceGroup.addDataset(f"LI_{sensor}_delta")
            newLTDeltaData = newRadianceGroup.addDataset(f"LT_{sensor}_delta")
            newnLwDeltaData = newReflectanceGroup.addDataset(f"nLw_{sensor}_delta")             
        else:           
            newRrsData = newReflectanceGroup.getDataset(f"Rrs_{sensor}")
            newESData = newIrradianceGroup.getDataset(f"ES_{sensor}")    
            newLIData = newRadianceGroup.getDataset(f"LI_{sensor}")
            newLTData = newRadianceGroup.getDataset(f"LT_{sensor}") 
            newnLwData = newReflectanceGroup.getDataset(f"nLw_{sensor}")

            newRrsDeltaData = newReflectanceGroup.getDataset(f"Rrs_{sensor}_delta")
            newESDeltaData = newIrradianceGroup.getDataset(f"ES_{sensor}_delta")    
            newLIDeltaData = newRadianceGroup.getDataset(f"LI_{sensor}_delta")
            newLTDeltaData = newRadianceGroup.getDataset(f"LT_{sensor}_delta")
            newnLwDeltaData = newReflectanceGroup.getDataset(f"nLw_{sensor}_delta")        

        # Add datetime stamps back onto ALL datasets associated with the current sensor
        # If this is the first spectrum, add date/time, otherwise append
        # Groups REFLECTANCE, IRRADIANCE, and RADIANCE are intiallized with empty datasets, but 
        # ANCILLARY is not.
        # conditional = ("Datetag" not in newRrsData.columns)
        # if True: This is so bizarre...
        if ("Datetag" not in newRrsData.columns):        
            for gp in root.groups:
                # ''' BUG: There is no reason in world why this line is necessary, but the if/else breaks without it '''
                # print(gp.id) 
                if (gp.id == "ANCILLARY"): # Ancillary is already populated. The other groups only have empty (named) datasets  
                    continue
                else:
                    for ds in gp.datasets:
                        if sensor in ds: # Only add datetime stamps to the current sensor datasets
                            gp.datasets[ds].columns["Datetime"] = [dateTime] # mean of the ensemble datetime stamp                 
                            gp.datasets[ds].columns["Datetag"] = [dateTag]
                            gp.datasets[ds].columns["Timetag2"] = [timeTag]                  
        else:
            for gp in root.groups:
                if (gp.id == "ANCILLARY"):
                    continue
                else:
                    for ds in gp.datasets:                                                
                        if sensor in ds:
                            gp.datasets[ds].columns["Datetime"].append(dateTime)                         
                            gp.datasets[ds].columns["Datetag"].append(dateTag)
                            gp.datasets[ds].columns["Timetag2"].append(timeTag)

        deleteKey = []
        for k in esXSlice: # loop through wavebands as key 'k'
            if (k in liXSlice) and (k in ltXSlice):
                
                # Initialize the new dataset if this is the first slice
                if k not in newESData.columns:
                    newESData.columns[k] = []
                    newLIData.columns[k] = []
                    newLTData.columns[k] = []
                    newRrsData.columns[k] = []
                    newnLwData.columns[k] = []

                    newESDeltaData.columns[k] = []
                    newLIDeltaData.columns[k] = []
                    newLTDeltaData.columns[k] = []
                    newRrsDeltaData.columns[k] = []
                    newnLwDeltaData.columns[k] = []

                # At this waveband (k); still using complete wavelength set
                es = esXSlice[k][0] # Always the zeroth element; i.e. XSlice data are independent of past slices and root
                li = liXSlice[k][0]
                lt = ltXSlice[k][0]
                f0  = F0[k]

                esDelta = esXstd[k][0]
                liDelta = liXstd[k][0]
                ltDelta = ltXstd[k][0]

                # Calculate the remote sensing reflectance
                if RuddickRho:                    
                    rrs = (lt - (rhoScalar * li)) / es

                    # Rrs uncertainty
                    rrsDelta = rrs * ( 
                            (liDelta/li)**2 + (rhoDelta/rhoScalar)**2 + (liDelta/li)**2 + (esDelta/es)**2 
                            )**0.5
                
                    #Calculate the normalized water leaving radiance
                    nLw = rrs*f0

                    # nLw uncertainty; no provision for F0 uncertainty here
                    nLwDelta = nLw * (
                            (liDelta/li)**2 + (rhoDelta/rhoScalar)**2 + (liDelta/li)**2 + (esDelta/es)**2
                            )**0.5
                elif ZhangRho:
                    # Only populate the valid wavelengths
                    if float(k) in waveSubset:
                        rrs = (lt - (rhoVec[k] * li)) / es

                        # Rrs uncertainty
                        rrsDelta = rrs * ( 
                                (liDelta/li)**2 + (rhoVecDelta/rhoVec[k])**2 + (liDelta/li)**2 + (esDelta/es)**2 
                                )**0.5
                    
                        #Calculate the normalized water leaving radiance
                        nLw = rrs*f0

                        # nLw uncertainty; no provision for F0 uncertainty here
                        nLwDelta = nLw * (
                                (liDelta/li)**2 + (rhoVecDelta/rhoVec[k])**2 + (liDelta/li)**2 + (esDelta/es)**2
                                )**0.5
                else:
                    # Default rho
                    rhoScalar = rhoDefault
                    rhoDelta = 0.01 # Estimated for range of conditions in Mobley 1999 models; it's actually higher...

                    rrs = (lt - (rhoScalar * li)) / es

                    # Rrs uncertainty
                    rrsDelta = rrs * ( 
                            (liDelta/li)**2 + (rhoDelta/rhoScalar)**2 + (liDelta/li)**2 + (esDelta/es)**2 
                            )**0.5
                
                    #Calculate the normalized water leaving radiance
                    nLw = rrs*f0

                    # nLw uncertainty; no provision for F0 uncertainty here
                    nLwDelta = nLw * (
                            (liDelta/li)**2 + (rhoDelta/rhoScalar)**2 + (liDelta/li)**2 + (esDelta/es)**2
                            )**0.5

                newESData.columns[k].append(es)
                newLIData.columns[k].append(li)
                newLTData.columns[k].append(lt)                


                newESDeltaData.columns[k].append(esDelta)
                newLIDeltaData.columns[k].append(liDelta)
                newLTDeltaData.columns[k].append(ltDelta)
                
                # Only populate valid wavelengths. Mark others for deletion
                if float(k) in waveSubset:
                    newRrsDeltaData.columns[k].append(rrsDelta)
                    newnLwDeltaData.columns[k].append(nLwDelta)
                    newRrsData.columns[k].append(rrs)
                    # newRrsData.columns[k] = rrs
                    newnLwData.columns[k].append(nLw)
                    # newnLwData.columns[k] = nLw
                else:
                    deleteKey.append(k) 
        
        # Eliminate reflectance keys/values in wavebands outside of valid set for the sake of Zhang model
        deleteKey = list(set(deleteKey))
        for key in deleteKey: 
            # Only need to do this for the first ensemble in file
            if key in newRrsData.columns:
                del newRrsData.columns[key]
                del newnLwData.columns[key]
                del newRrsDeltaData.columns[key]
                del newnLwDeltaData.columns[key]

        newESData.columnsToDataset() 
        newLIData.columnsToDataset()
        newLTData.columnsToDataset()
        newRrsData.columnsToDataset()
        newnLwData.columnsToDataset()

        newESDeltaData.columnsToDataset()   
        newLIDeltaData.columnsToDataset()
        newLTDeltaData.columnsToDataset()
        newRrsDeltaData.columnsToDataset()
        newnLwDeltaData.columnsToDataset()
        
    @staticmethod    
    def filterData(group, badTimes):                    
        ''' Delete flagged records '''

        msg = f'Remove {group.id} Data'
        print(msg)
        Utilities.writeLogFile(msg)

        if group.id == "ANCILLARY":
            timeStamp = group.getDataset("LATITUDE").data["Datetime"]
        if group.id == "IRRADIANCE":
            timeStamp = group.getDataset("ES").data["Datetime"]
        if group.id == "RADIANCE":
            timeStamp = group.getDataset("LI").data["Datetime"]
        if group.id == "REFLECTANCE":
            timeStamp = group.getDataset("Rrs").data["Datetime"]

        startLength = len(timeStamp) 
        msg = f'   Length of dataset prior to removal {startLength} long'
        print(msg)
        Utilities.writeLogFile(msg)

        # Delete the records in badTime ranges from each dataset in the group
        finalCount = 0
        originalLength = len(timeStamp)        
        for dateTime in badTimes:
            # Need to reinitialize for each loop
            startLength = len(timeStamp)
            newTimeStamp = []

            # msg = f'Eliminate data between: {dateTime}'
            # print(msg)
            # Utilities.writeLogFile(msg)

            start = dateTime[0]
            stop = dateTime[1]

            if startLength > 0:  
                counter = 0              
                for i in range(startLength):
                    if start <= timeStamp[i] and stop >= timeStamp[i]:                          
                        group.datasetDeleteRow(i - counter)  # Adjusts the index for the shrinking arrays
                        counter += 1
                        finalCount += 1
                    else:
                        newTimeStamp.append(timeStamp[i])
            else:
                msg = 'Data group is empty. Continuing.'
                print(msg)
                Utilities.writeLogFile(msg)
            timeStamp = newTimeStamp.copy()

        if badTimes == []:
            startLength = 1 # avoids div by zero below when finalCount is 0

        for ds in group.datasets:
            # if ds != "STATION": 
            group.datasets[ds].datasetToColumns()

        msg = f'   Length of dataset after removal {originalLength-finalCount} long: {round(100*finalCount/originalLength)}% removed'
        print(msg)
        Utilities.writeLogFile(msg)
        return finalCount/originalLength
    
    @staticmethod
    def interpolateColumn(columns, wl):
        ''' Interpolate wavebands to estimate a single, unsampled waveband '''
        #print("interpolateColumn")

        # Values to return
        return_y = []

        # Column to interpolate to
        new_x = [wl]
        
        # Get wavelength values
        wavelength = []
        for k in columns:
            #print(k)
            wavelength.append(float(k))
        x = np.asarray(wavelength)

        # get the length of a column
        num = len(list(columns.values())[0])

        # Perform interpolation for each row
        for i in range(num):
            values = []
            for k in columns:
                #print("b")
                values.append(columns[k][i])
            y = np.asarray(values)
            
            new_y = sp.interpolate.interp1d(x, y)(new_x)
            return_y.append(new_y[0])

        return return_y

    
    @staticmethod
    def specQualityCheck(group, inFilePath, station=None):
        ''' Perform spectral filtering
        Calculate the STD of the normalized (at some max value) average ensemble.
        Then test each normalized spectrum against the ensemble average and STD.
        Plot results'''

        badTimes = []
        if group.id == 'IRRADIANCE':
            Data = group.getDataset("ES") 
            timeStamp = group.getDataset("ES").data["Datetime"]
            badTimes = Utilities.specFilter(inFilePath, Data, timeStamp, station, filterRange=[400, 700],\
                filterFactor=5, rType='Es')
            msg = f'{len(np.unique(badTimes))/len(timeStamp)*100:.1f}% of Es data flagged'
            print(msg)
            Utilities.writeLogFile(msg)  
        else:            
            Data = group.getDataset("LI")
            timeStamp = group.getDataset("LI").data["Datetime"]
            badTimes1 = Utilities.specFilter(inFilePath, Data, timeStamp, station, filterRange=[400, 700],\
                filterFactor=8, rType='Li')
            msg = f'{len(np.unique(badTimes1))/len(timeStamp)*100:.1f}% of Li data flagged'
            print(msg)
            Utilities.writeLogFile(msg)  

            Data = group.getDataset("LT")
            timeStamp = group.getDataset("LT").data["Datetime"]
            badTimes2 = Utilities.specFilter(inFilePath, Data, timeStamp, station, filterRange=[400, 700],\
                filterFactor=3, rType='Lt')
            msg = f'{len(np.unique(badTimes2))/len(timeStamp)*100:.1f}% of Lt data flagged'
            print(msg)
            Utilities.writeLogFile(msg)  

            badTimes = np.append(badTimes1,badTimes2, axis=0)
        
        if len(badTimes) == 0:
            badTimes = None
        return badTimes
            
    @staticmethod
    def ltQuality(sasGroup):   
        ''' Perform Lt Quality checking '''

        ltData = sasGroup.getDataset("LT")
        ltData.datasetToColumns()
        ltColumns = ltData.columns
        # These get popped off the columns, but restored when filterData runs datasetToColumns
        ltColumns.pop('Datetag')
        ltColumns.pop('Timetag2')
        ltDatetime = ltColumns.pop('Datetime')
                        
        badTimes = []
        for indx, dateTime in enumerate(ltDatetime):                        
            # If the Lt spectrum in the NIR is brighter than in the UVA, something is very wrong
            UVA = [350,400]
            NIR = [780,850]
            ltUVA = []
            ltNIR = []
            for wave in ltColumns:
                if float(wave) > UVA[0] and float(wave) < UVA[1]:
                    ltUVA.append(ltColumns[wave][indx])
                elif float(wave) > NIR[0] and float(wave) < NIR[1]:
                    ltNIR.append(ltColumns[wave][indx])

            if np.nanmean(ltUVA) < np.nanmean(ltNIR):
                badTimes.append(dateTime)
        
        badTimes = np.unique(badTimes)
        # Duplicate each element to a list of two elements in a list
        ''' BUG: This is not optimal as it creates one badTimes record for each bad
            timestamp, rather than span of timestamps from badtimes[i][0] to badtimes[i][1]'''
        badTimes = np.rot90(np.matlib.repmat(badTimes,2,1), 3) 
        msg = f'{len(np.unique(badTimes))/len(ltDatetime)*100:.1f}% of spectra flagged'
        print(msg)
        Utilities.writeLogFile(msg) 

        if len(badTimes) == 0:
            badTimes = None
        return badTimes
    
    @staticmethod
    def negReflectance(reflGroup,field):   
        ''' Perform negative reflectance spectra checking '''
        # Run for entire file, not just one ensemble

        reflData = reflGroup.getDataset(field)
        # reflData.datasetToColumns()
        reflColumns = reflData.columns
        reflDate = reflColumns.pop('Datetag')
        reflTime = reflColumns.pop('Timetag2')
        # reflColumns.pop('Datetag')
        # reflColumns.pop('Timetag2')
        timeStamp = reflColumns.pop('Datetime')
                        
        badTimes = []
        for indx, timeTag in enumerate(timeStamp):                        
            # If any spectra in the vis are negative, delete the whole spectrum
            VIS = [400,700]            
            reflVIS = []
            wavelengths = []
            for wave in reflColumns:
                wavelengths.append(float(wave))
                if float(wave) > VIS[0] and float(wave) < VIS[1]:
                    reflVIS.append(reflColumns[wave][indx])
                # elif float(wave) > NIR[0] and float(wave) < NIR[1]:
                #     ltNIR.append(ltColumns[wave][indx])

            # Flag entire record for removal
            if any(item < 0 for item in reflVIS):
                badTimes.append(timeTag)

            # Set negatives to 0
            NIR = [701,max(wavelengths)]
            UV = [min(wavelengths),399]
            for wave in reflColumns:
                if ((float(wave) >= UV[0] and float(wave) < UV[1]) or \
                            (float(wave) >= NIR[0] and float(wave) <= NIR[1])) and \
                            reflColumns[wave][indx] < 0:
                    reflColumns[wave][indx] = 0
                            
        badTimes = np.unique(badTimes)
        badTimes = np.rot90(np.matlib.repmat(badTimes,2,1), 3) # Duplicates each element to a list of two elements (start, stop)
        msg = f'{len(np.unique(badTimes))/len(timeStamp)*100:.1f}% of {field} spectra flagged'
        print(msg)
        Utilities.writeLogFile(msg) 

        # # Need to add these at the beginning of the ODict        
        reflColumns['Timetag2'] = reflTime
        reflColumns['Datetag'] = reflDate
        reflColumns['Datetime'] = timeStamp
        reflColumns.move_to_end('Timetag2', last=False)
        reflColumns.move_to_end('Datetag', last=False)
        reflColumns.move_to_end('Datetime', last=False)

        reflData.columnsToDataset()        

        if len(badTimes) == 0:
            badTimes = None
        return badTimes
    
    @staticmethod
    def metQualityCheck(refGroup, sasGroup):   
        ''' Perform meteorological quality control '''

        esFlag = float(ConfigFile.settings["fL2SignificantEsFlag"])
        dawnDuskFlag = float(ConfigFile.settings["fL2DawnDuskFlag"])
        humidityFlag = float(ConfigFile.settings["fL2RainfallHumidityFlag"])     
        cloudFLAG = float(ConfigFile.settings["fL2CloudFlag"]) # Not to be confused with cloudFlag...

        esData = refGroup.getDataset("ES")
        esData.datasetToColumns()
        esColumns = esData.columns
            
        esColumns.pop('Datetag')
        esColumns.pop('Timetag2')
        esTime = esColumns.pop('Datetime')

        liData = sasGroup.getDataset("LI")
        liData.datasetToColumns()
        liColumns = liData.columns
        liColumns.pop('Datetag')
        liColumns.pop('Timetag2')
        liColumns.pop('Datetime')

        ltData = sasGroup.getDataset("LT")
        ltData.datasetToColumns()
        ltColumns = ltData.columns
        ltColumns.pop('Datetag')
        ltColumns.pop('Timetag2')        
        ltColumns.pop('Datetime')    
        
        li750 = ProcessL2.interpolateColumn(liColumns, 750.0)
        es370 = ProcessL2.interpolateColumn(esColumns, 370.0)
        es470 = ProcessL2.interpolateColumn(esColumns, 470.0)
        es480 = ProcessL2.interpolateColumn(esColumns, 480.0)
        es680 = ProcessL2.interpolateColumn(esColumns, 680.0)
        es720 = ProcessL2.interpolateColumn(esColumns, 720.0)
        es750 = ProcessL2.interpolateColumn(esColumns, 750.0)
        badTimes = []
        for indx, dateTime in enumerate(esTime):                
            # Masking spectra affected by clouds (Ruddick 2006, IOCCG Protocols). 
            # The alternative to masking is to process them differently (e.g. See Ruddick_Rho)
            # Therefore, set this very high if you don't want it triggered (e.g. 1.0, see Readme)            
            if li750[indx]/es750[indx] >= cloudFLAG:
                # msg = f"Quality Check: Li(750)/Es(750) >= cloudFLAG:{cloudFLAG}"
                # print(msg)
                # Utilities.writeLogFile(msg)  
                badTimes.append(dateTime)


            # Threshold for significant es
            # Wernand 2002
            if es480[indx] < esFlag:
                # msg = f"Quality Check: es(480) < esFlag:{esFlag}"
                # print(msg)
                # Utilities.writeLogFile(msg)  
                badTimes.append(dateTime)

            # Masking spectra affected by dawn/dusk radiation
            # Wernand 2002
            #v = esXSlice["470.0"][0] / esXSlice["610.0"][0] # Fix 610 -> 680
            if es470[indx]/es680[indx] < dawnDuskFlag:
                # msg = f'Quality Check: ES(470.0)/ES(680.0) < dawnDuskFlag:{dawnDuskFlag}'
                # print(msg)
                # Utilities.writeLogFile(msg)  
                badTimes.append(dateTime)

            # Masking spectra affected by rainfall and high humidity
            # Wernand 2002 (940/370), Garaba et al. 2012 also uses Es(940/370), presumably 720 was developed by Wang...???
            ''' Follow up on the source of this flag'''            
            if es720[indx]/es370[indx] < humidityFlag:
                # msg = f'Quality Check: ES(720.0)/ES(370.0) < humidityFlag:{humidityFlag}'
                # print(msg)
                # Utilities.writeLogFile(msg)  
                badTimes.append(dateTime)
        
        badTimes = np.unique(badTimes)
        badTimes = np.rot90(np.matlib.repmat(badTimes,2,1), 3) # Duplicates each element to a list of two elements in a list
        msg = f'{len(np.unique(badTimes))/len(esTime)*100:.1f}% of spectra flagged'
        print(msg)
        Utilities.writeLogFile(msg)

        if len(badTimes) == 0:
            # Restore timestamps to columns (since it's not going to filterData, where it otherwise happens)
            esData.datasetToColumns()
            liData.datasetToColumns()
            ltData.datasetToColumns()
            badTimes = None
        return badTimes
    
    @staticmethod
    def columnToSlice(columns, start, end):
        ''' Take a slice of a dataset stored in columns '''

        # Each column is a time series either at a waveband for radiometer columns, or various grouped datasets for ancillary
        # Start and end are defined by the interval established in the Config (they are indexes)
        newSlice = collections.OrderedDict()
        for k in columns:
            if start == end:
                newSlice[k] = columns[k][start:end+1] # otherwise you get nada []
            else:
                newSlice[k] = columns[k][start:end] # up to not including end...next slice will pick it up
        return newSlice
    
    @staticmethod
    def interpAncillary(node, ancData, modData, radData):
        ''' Interpolate ancillary to radiometry and fill with model data or defaults '''

        print('Interpolating field ancillary and/or modeled ancillary data to radiometry times...')
        epoch = datetime.datetime(1970, 1, 1,tzinfo=datetime.timezone.utc)
        
        ancGroup = node.getGroup("ANCILLARY")
        # These are required and have been filled in with field, model, and/or default values
        windDataset = ancGroup.addDataset("WINDSPEED")
        aodDataset = ancGroup.addDataset("AOD")
        saltDataset = ancGroup.addDataset("SAL")
        sstDataset = ancGroup.addDataset("SST")  

        # Only concerned here with datasets from the Ancillary Data File (SeaBASS file in Main Window)
        # Additional ancillary data added after returning from this interp method

        # Optional datasets; CLOUD and WAVE are basically place holders as of ver 1.0.beta;
        # (i.e. no implementation in Rho corrections)
        cloud = False
        wave = False
        station = False
        if "CLOUD" in ancData.columns:
            cloudDataset = ancGroup.addDataset("CLOUD")
        if "WAVE_HT" in ancData.columns:
            waveDataset = ancGroup.addDataset("WAVE_HT")
        if "STATION" in ancData.columns:
            stationDataset = ancGroup.addDataset("STATION")

        # Convert radData date and time to datetime and then to seconds for interpolation
        radTime = radData.data["Timetag2"].tolist()
        radSeconds = []
        radDatetime = []
        for i, radDate in enumerate(radData.data["Datetag"].tolist()):                
            radDatetime.append(Utilities.timeTag2ToDateTime(Utilities.dateTagToDateTime(radDate),radTime[i]))
            radSeconds.append((radDatetime[i]-epoch).total_seconds())
        
        if ancData:
            ancGroup.copyAttributes(ancData)    
            # These are the entire ancillary records for the cruise
            dateTime = ancData.getColumn("DATETIME")[0]
            if "WINDSPEED" in ancData.columns:
                wind = ancData.getColumn("WINDSPEED")[0]
            if "SALINITY" in ancData.columns:
                salt = ancData.getColumn("SALINITY")[0]
            if "SST" in ancData.columns:
                sst = ancData.getColumn("SST")[0]
            if "CLOUD" in ancData.columns:
                cloud = ancData.getColumn("CLOUD")[0]
            if "WAVE_HT" in ancData.columns:
                wave = ancData.getColumn("WAVE_HT")[0]
            if "STATION" in ancData.columns:
                station = ancData.getColumn("STATION")[0]
            # Convert ancillary datetime to seconds for interpolation            
            ancSeconds = [(i-epoch).total_seconds() for i in dateTime] 
        else:
            ancData = None
            msg = "Ancillary field data missing; reverting to ancillary model or defaults"
            print(msg)
            Utilities.writeLogFile(msg)

        # Test for any field ancillary data in timeframe of rad time   
        if ancData and (max(ancSeconds) <= min(radSeconds) or min(ancSeconds) >= max(radSeconds)):
            ancData = None
            msg = "Ancillary field data do not intersect radiometric data; reverting to ancillary model or defaults"
            print(msg)
            Utilities.writeLogFile(msg)  

        # Create a framework to hold combined ancillary data...
        ancInRadSeconds = []
        windFlag = []
        saltFlag = []
        sstFlag = []
        aodFlag = []        
        windInRad = []
        saltInRad = []
        sstInRad = []
        aodInRad = []
        stationInRad = []
        if cloud:
            cloudFlag = []
            cloudInRad = []
        if wave:
            waveFlag = []
            waveInRad = []
        if station:
            # stationFlag = []
            stationInRad = []
        # Populate the fields to the size of the radiometric dataset with NaNs (or flag placeholders)
        for i, value in enumerate(radSeconds):
            ancInRadSeconds.append(value)
            # HDF5 deliberately makes including string vectors difficult
            # These will all be changed to floats or ints in HDFDataset.columnsToDataset
            windFlag.append('undetermined')                   
            saltFlag.append('undetermined')                   
            sstFlag.append('undetermined')                   
            aodFlag.append('undetermined')                             
            windInRad.append(np.nan)
            saltInRad.append(np.nan)
            sstInRad.append(np.nan)
            aodInRad.append(np.nan)            
            if cloud:
                cloudFlag.append('field')
                cloudInRad.append(np.nan)
            if wave:
                waveFlag.append('field')
                waveInRad.append(np.nan)
            if station:
                # HDF5 deliberately makes including string vectors difficult
                stationInRad.append(np.nan)
            
        # Populate with nearest field data if possible
        if ancData:
            for i, value in enumerate(ancInRadSeconds): # step through InRad...
                idx = Utilities.find_nearest(ancSeconds,value) # ...identify from entire anc record...
                # Make sure the time difference between field anc and rad is <= 1hr
                if abs(ancSeconds[idx] - value)/60/60 < 1:  # ... and place nearest into InRad variable
                    windInRad[i] = wind[idx]                    
                    saltInRad[i] = salt[idx]
                    sstInRad[i] = sst[idx]
                    # Label the data source in the flag
                    windFlag[i] = 'field'
                    saltFlag[i] = 'field'
                    sstFlag[i] = 'field'                    
                    if cloud:
                        cloudInRad[i] = cloud[idx]
                    if wave:
                        waveInRad[i] = wave[idx]
                    if station:
                        # if not np.isnan(station[idx]):
                        #     # This will be converted back to a float in columnsToDataset
                        #     stationTidy = str(round(station[idx]*100)/100)
                        #     stationInRad[i] = stationTidy
                        stationInRad[i] = station[idx]
        
        # Tallies
        msg = f'Field wind data has {np.isnan(windInRad).sum()} NaNs out of {len(windInRad)} prior to using model data'                
        print(msg)
        Utilities.writeLogFile(msg)
        msg = f'Field salt data has {np.isnan(saltInRad).sum()} NaNs out of {len(saltInRad)} prior to using model data'                
        print(msg)
        Utilities.writeLogFile(msg)
        msg = f'Field sst data has {np.isnan(sstInRad).sum()} NaNs out of {len(sstInRad)} prior to using model data'                
        print(msg)
        Utilities.writeLogFile(msg)
        msg = f'Field aod data has {np.isnan(aodInRad).sum()} NaNs out of {len(aodInRad)} prior to using model data'                
        print(msg)
        Utilities.writeLogFile(msg)
        if cloud:
            msg = f'Field cloud data has {np.isnan(cloudInRad).sum()} NaNs out of {len(cloudInRad)}'
            print(msg)
            Utilities.writeLogFile(msg)
        if wave:
            msg = f'Field wave data has {np.isnan(waveInRad).sum()} NaNs out of {len(waveInRad)}'
            print(msg)
            Utilities.writeLogFile(msg)
        if station:
            # count = stationInRad.count('underway')
            msg = f'Field station data has {np.isnan(stationInRad).sum()} non-stations out of {len(stationInRad)}'
            print(msg)
            Utilities.writeLogFile(msg)

        # Convert model data date and time to datetime and then to seconds for interpolation
        if modData is not None:                
            modTime = modData.groups[0].datasets["Timetag2"].tolist()
            modSeconds = []
            modDatetime = []
            for i, modDate in enumerate(modData.groups[0].datasets["Datetag"].tolist()):                
                modDatetime.append(Utilities.timeTag2ToDateTime(Utilities.dateTagToDateTime(modDate),modTime[i]))
                modSeconds.append((modDatetime[i]-epoch).total_seconds())  
        
        # Replace Wind, AOD NaNs with modeled data where possible. 
        # These will be within one hour of the field data.
        if modData is not None:
            msg = 'Filling in field data with model data where needed.'
            print(msg)
            Utilities.writeLogFile(msg)
            for i,value in enumerate(windInRad):
                if np.isnan(value):   
                    # msg = 'Replacing wind with model data'
                    # print(msg)
                    # Utilities.writeLogFile(msg)
                    idx = Utilities.find_nearest(modSeconds,ancInRadSeconds[i])
                    windInRad[i] = modData.groups[0].datasets['Wind'][idx]   
                    windFlag[i] = 'model'                     
            for i, value in enumerate(aodInRad):
                if np.isnan(value):
                    # msg = 'Replacing AOD with model data'
                    # print(msg)
                    # Utilities.writeLogFile(msg)
                    idx = Utilities.find_nearest(modSeconds,ancInRadSeconds[i])
                    aodInRad[i] = modData.groups[0].datasets['AOD'][idx]
                    aodFlag[i] = 'model'

        # Replace Wind, AOD, SST, and Sal with defaults where still nan
        msg = 'Filling in ancillary data with default values where still needed.'
        print(msg)
        Utilities.writeLogFile(msg)
        for i, value in enumerate(windInRad):
            if np.isnan(value):
                windInRad[i] = ConfigFile.settings["fL2DefaultWindSpeed"]
                windFlag[i] = 'default'
        for i, value in enumerate(aodInRad):
            if np.isnan(value):
                aodInRad[i] = ConfigFile.settings["fL2DefaultAOD"]
                aodFlag[i] = 'default'
        for i, value in enumerate(saltInRad):
            if np.isnan(value):
                saltInRad[i] = ConfigFile.settings["fL2DefaultSalt"]
                saltFlag[i] = 'default'
        for i, value in enumerate(sstInRad):
            if np.isnan(value):
                sstInRad[i] = ConfigFile.settings["fL2DefaultSST"]
                sstFlag[i] = 'default'

        # Populate the datasets and flags with the InRad variables
        windDataset.columns["WINDSPEED"] = windInRad
        windDataset.columns["WINDFLAG"] = windFlag
        aodDataset.columns["AOD"] = aodInRad
        aodDataset.columns["AODFLAG"] = aodFlag
        saltDataset.columns["SAL"] = saltInRad
        saltDataset.columns["SALTFLAG"] = saltFlag
        sstDataset.columns["SST"] = sstInRad
        sstDataset.columns["SSTFLAG"] = sstFlag
        if cloud:
            cloudDataset.columns["CLOUD"] = cloudInRad
            cloudDataset.columns["CLOUDFLAG"] = cloudFlag
        if wave:
            waveDataset.columns["WAVE_HT"] = waveInRad
            waveDataset.columns["WAVEFLAG"] = waveFlag
        if station:
            stationDataset.columns["STATION"] = stationInRad

        # Convert ancillary seconds back to date/timetags ...
        ancDateTag = []
        ancTimeTag2 = []  
        radDT = []          
        for i, sec in enumerate(radSeconds):
            radDT.append(datetime.datetime.utcfromtimestamp(sec).replace(tzinfo=datetime.timezone.utc))
            ancDateTag.append(float(f'{int(radDT[i].timetuple()[0]):04}{int(radDT[i].timetuple()[7]):03}'))
            ancTimeTag2.append(float( \
                f'{int(radDT[i].timetuple()[3]):02}{int(radDT[i].timetuple()[4]):02}{int(radDT[i].timetuple()[5]):02}{int(radDT[i].microsecond/1000):03}'))
            # ancTimeTag2.append(Utilities.epochSecToDateTagTimeTag2(sec))
        
        # ... and add them to the datasets
        # dateTagDataset.columns["Datetag"] = ancDateTag
        # timeTag2Dataset.columns["Timetag2"] = ancTimeTag2
        # Move the Timetag2 and Datetag into the arrays and remove the datasets
        for ds in ancGroup.datasets:           
            ancGroup.datasets[ds].columns["Datetag"] = ancDateTag
            ancGroup.datasets[ds].columns["Timetag2"] = ancTimeTag2
            ancGroup.datasets[ds].columns["Datetime"] = radDT
            ancGroup.datasets[ds].columns.move_to_end('Timetag2', last=False)
            ancGroup.datasets[ds].columns.move_to_end('Datetag', last=False)
            ancGroup.datasets[ds].columns.move_to_end('Datetime', last=False)

        windDataset.columnsToDataset()
        aodDataset.columnsToDataset()
        saltDataset.columnsToDataset()
        sstDataset.columnsToDataset()
        if cloud:
            cloudDataset.columnsToDataset()
        if wave:
            waveDataset.columnsToDataset()
        if station:
            stationDataset.columnsToDataset()      
    
    @staticmethod
    def sliceAveHyper(y, hyperSlice, xSlice, xStd):
        ''' Take the slice mean of the lowest X% of hyperspectral slices '''

        hasNan = False
        # Ignore runtime warnings when array is all NaNs
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            for k in hyperSlice: # each k is a time series at a waveband.
                v = [hyperSlice[k][i] for i in y] # selects the lowest 5% within the interval window...
                mean = np.nanmean(v) # ... and averages them
                std = np.nanstd(v) # ... and the stdev for uncertainty estimates
                xSlice[k] = [mean]
                xStd[k] = [std]
                if np.isnan(mean):
                    hasNan = True
        return hasNan
    
    @staticmethod
    def sliceAveAnc(root, start, end, y, ancGroup):
        ''' Take the slice AND the mean averages of ancillary data with X% '''

        newAncGroup = root.getGroup("ANCILLARY")

        # Build a simple dictionary of datasets to reference from (input) ancGrop
        ancDict = collections.OrderedDict()
        for dsName in ancGroup.datasets:
            ds = ancGroup.datasets[dsName] # Full HDF dataset (columns & data)
            # if dsName != "Datetime" and dsName != "Datetag" and dsName != "Timetag2":                 
            ancDict[dsName] = ds # assign the data and columns within the dataset
                # ancDict[dsName].columns.pop("Datetag")
                # ancDict[dsName].columns.pop("Timetag2")
            # elif dsName == "Datetime":
            # if dsName == "LATITUDE":
            #     timeStamp = ds.columns["Datetime"]
            # timeStamp = ancDict[ds].columns.pop("Datetime")
            

        # dateSlice=ancDict['Datetag'].data[start:end+1] #up to not including end+1
        # timeSlice=ancDict['Timetag2'].data[start:end+1]

        # Stores the mean datetime
        # if len(timeStamp) > 0:
        #     epoch = datetime.datetime(1970, 1, 1,tzinfo=datetime.timezone.utc) #Unix zero hour
        #     tsSeconds = []
        #     for dt in timeStamp:
        #         tsSeconds.append((dt-epoch).total_seconds())
        #     meanSec = np.mean(tsSeconds)
        #     dateTime = datetime.datetime.utcfromtimestamp(meanSec).replace(tzinfo=datetime.timezone.utc)
        #     date = Utilities.datetime2DateTag(dateTime)
        #     time = Utilities.datetime2TimeTag2(dateTime)

        # # Stores the middle element
        # if len(dateSlice) > 0:
        #     date = dateSlice[int(len(dateSlice)/2)]
        #     time = timeSlice[int(len(timeSlice)/2)]

        for ds in ancDict: 
            # if ds != 'Datetag' and ds != 'Timetag2':
                if not newAncGroup.getDataset(ds):
                    newDS = newAncGroup.addDataset(ds)
                else:
                    newDS = newAncGroup.getDataset(ds)

                dsSlice = ProcessL2.columnToSlice(ancDict[ds].columns,start, end)                
                dsXSlice = None

                for subset in dsSlice: # several ancillary datasets are groups which will become columns (including date, time, and flags)
                    if subset == 'Datetime':
                        timeStamp = dsSlice[subset]
                        # Stores the mean datetime by converting to (and back from) epoch second
                        if len(timeStamp) > 0:
                            epoch = datetime.datetime(1970, 1, 1,tzinfo=datetime.timezone.utc) #Unix zero hour
                            tsSeconds = []
                            for dt in timeStamp:
                                tsSeconds.append((dt-epoch).total_seconds())
                            meanSec = np.mean(tsSeconds)
                            dateTime = datetime.datetime.utcfromtimestamp(meanSec).replace(tzinfo=datetime.timezone.utc)
                            date = Utilities.datetime2DateTag(dateTime)
                            time = Utilities.datetime2TimeTag2(dateTime)
                    if subset != 'Datetime' and subset != 'Datetag' and subset != 'Timetag2':
                        v = [dsSlice[subset][i] for i in y] # y is an array of indexes for the lowest X%

                        if dsXSlice is None:
                            dsXSlice = collections.OrderedDict()                        
                            # dsXSlice['Datetag'] = date.tolist()
                            # dsXSlice['Timetag2'] = time.tolist()
                            # dsXSlice['Datetime'] = Datetime.tolist()
                            dsXSlice['Datetag'] = [date]
                            dsXSlice['Timetag2'] = [time]
                            dsXSlice['Datetime'] = [dateTime]                            
                            
                        if (subset.endswith('FLAG')) or (subset.endswith('STATION')):
                            if not subset in dsXSlice:
                                # Find the most frequest element
                                dsXSlice[subset] = []
                            dsXSlice[subset].append(Utilities.mostFrequent(v))
                        else:
                            if subset not in dsXSlice:
                                dsXSlice[subset] = []                            
                            dsXSlice[subset].append(np.mean(v)) 
                
                if subset not in newDS.columns:
                    newDS.columns = dsXSlice
                else:
                    for item in newDS.columns:
                        newDS.columns[item] = np.append(newDS.columns[item], dsXSlice[item])

                newDS.columns.move_to_end('Timetag2', last=False)
                newDS.columns.move_to_end('Datetag', last=False)
                newDS.columns.move_to_end('Datetime', last=False)                
                newDS.columnsToDataset()         
       
    @staticmethod
    def calculateREFLECTANCE2(root, sasGroup, refGroup, ancGroup, start, end):
        '''Calculate the lowest X% Lt(780). Check for Nans in Li, Lt, Es, or wind. Send out for 
        meteorological quality flags. Perform glint corrections. Calculate the Rrs. Correct for NIR
        residuals.'''

        esData = refGroup.getDataset("ES")
        liData = sasGroup.getDataset("LI")
        ltData = sasGroup.getDataset("LT") 
        
        # Copy datasets to dictionary
        esData.datasetToColumns()
        esColumns = esData.columns
        liData.datasetToColumns()
        liColumns = liData.columns        
        ltData.datasetToColumns()
        ltColumns = ltData.columns   

        esSlice = ProcessL2.columnToSlice(esColumns,start, end)
        liSlice = ProcessL2.columnToSlice(liColumns,start, end)
        ltSlice = ProcessL2.columnToSlice(ltColumns,start, end)
        n = len(list(ltSlice.values())[0])
    
        rhoDefault = float(ConfigFile.settings["fL2RhoSky"])
        RuddickRho = int(ConfigFile.settings["bL2RuddickRho"])
        ZhangRho = int(ConfigFile.settings["bL2ZhangRho"])
        enablePercentLt = float(ConfigFile.settings["bL2EnablePercentLt"])
        percentLt = float(ConfigFile.settings["fL2PercentLt"])

        # Find the central index of the date/times to s
        timeStamp = esSlice.pop("Datetime")

        esSlice.pop("Datetag")
        esSlice.pop("Timetag2")

        liSlice.pop("Datetag")
        liSlice.pop("Timetag2")
        liSlice.pop("Datetime")

        ltSlice.pop("Datetag")
        ltSlice.pop("Timetag2")
        ltSlice.pop("Datetime")

        #Convolve es/li/lt slices to satellite bands using RSRs
        if ConfigFile.settings['bL2WeightMODISA']:
            print("Convolving MODIS Aqua (ir)radiances in the slice")
            esSliceMODISA = Weight_RSR.processMODISBands(esSlice, sensor='A') # dictionary
            liSliceMODISA = Weight_RSR.processMODISBands(liSlice, sensor='A')
            ltSliceMODISA = Weight_RSR.processMODISBands(ltSlice, sensor='A')




        # Store the mean datetime of the slice
        if len(timeStamp) > 0:
            epoch = datetime.datetime(1970, 1, 1,tzinfo=datetime.timezone.utc) #Unix zero hour
            tsSeconds = []
            for dt in timeStamp:
                tsSeconds.append((dt-epoch).total_seconds())
            meanSec = np.mean(tsSeconds)
            dateTime = datetime.datetime.utcfromtimestamp(meanSec).replace(tzinfo=datetime.timezone.utc)
            dateTag = Utilities.datetime2DateTag(dateTime)
            timeTag = Utilities.datetime2TimeTag2(dateTime)

            timeObj = {}
            timeObj['dateTime'] = dateTime
            timeObj['dateTag'] = dateTag
            timeObj['timeTag'] = timeTag

        '''# Calculates the lowest X% (based on Hooker & Morel 2003; Hooker et al. 2002; Zibordi et al. 2002, IOCCG Protocols)
        X will depend on FOV and integration time of instrument. Hooker cites a rate of 2 Hz.
        It remains unclear to me from Hooker 2002 whether the recommendation is to take the average of the ir/radiances
        within the threshold and calculate Rrs, or to calculate the Rrs within the threshold, and then average, however IOCCG
        Protocols pretty clearly state to average the ir/radiances first, then calculate the Rrs...as done here.'''        
        x = round(n*percentLt/100) # number of retained values
        msg = f'{n} spectra in slice (ensemble).'
        print(msg)
        Utilities.writeLogFile(msg)
        
        # There are sometimes only a small number of spectra in the slice,
        #  so the percent Lt estimation becomes highly questionable and is overridden here.
        if n <= 5 or x == 0:
            x = n # if only 5 or fewer records retained, use them all...
        
        # Find the indexes for the lowest X%
        lt780 = ProcessL2.interpolateColumn(ltSlice, 780.0)
        index = np.argsort(lt780) # gives indexes if values were to be sorted
                
        if enablePercentLt and x > 1:
            # returns indexes of the first x values (if values were sorted); i.e. the indexes of the lowest X% of unsorted lt780
            y = index[0:x] 
            msg = f'{len(y)} spectra remaining in slice to average after filtering to lowest {percentLt}%.'
            print(msg)
            Utilities.writeLogFile(msg)
        else:
            # If Percent Lt is turned off, this will average the whole slice, and if
            # ensemble is off (set to 0), just the one spectrum will be used.
            y = index 

        # Take the mean of the lowest X% in the slice
        esXSlice = collections.OrderedDict()
        liXSlice = collections.OrderedDict()
        ltXSlice = collections.OrderedDict()  
        esXstd = collections.OrderedDict()  
        liXstd = collections.OrderedDict()  
        ltXstd = collections.OrderedDict()  

        hasNan = ProcessL2.sliceAveHyper(y, esSlice, esXSlice, esXstd)
        hasNan = ProcessL2.sliceAveHyper(y, liSlice, liXSlice, liXstd)
        hasNan = ProcessL2.sliceAveHyper(y, ltSlice, ltXSlice, ltXstd)

        # Take the mean of the lowest X% for satellite weighted (ir)radiances in the slice
        # y indexes are from the hyperspectral data
        if ConfigFile.settings['bL2WeightMODISA']:
            esXSliceMODISA = collections.OrderedDict()
            liXSliceMODISA = collections.OrderedDict()
            ltXSliceMODISA = collections.OrderedDict()  
            esXstdMODISA = collections.OrderedDict()  
            liXstdMODISA = collections.OrderedDict()  
            ltXstdMODISA = collections.OrderedDict()  

            hasNan = ProcessL2.sliceAveHyper(y, esSliceMODISA, esXSliceMODISA, esXstdMODISA)
            hasNan = ProcessL2.sliceAveHyper(y, liSliceMODISA, liXSliceMODISA, liXstdMODISA)
            hasNan = ProcessL2.sliceAveHyper(y, ltSliceMODISA, ltXSliceMODISA, ltXstdMODISA)





        # Take the mean of the lowest X% for the ancillary group in the slice
        # (Combines Slice and XSlice -- as above -- into one method)
        ProcessL2.sliceAveAnc(root, start, end, y, ancGroup)
        newAncGroup = root.getGroup("ANCILLARY") # Just populated above
        newAncGroup.attributes['Ancillary_Flags (0, 1, 2, 3)'] = ['undetermined','field','model','default']

        # Extract the last/current element/slice for each dataset and hold for use in calculating reflectances        
        # Ancillary group, unlike most groups, will have named data columns in datasets (i.e. not NONE)
        # This allows for multiple data arrays in one dataset (e.g. FLAGS)

        # These are required and will have been filled in with field data, models, and or defaults
        WINDSPEEDXSlice = newAncGroup.getDataset('WINDSPEED').data['WINDSPEED'][-1].copy()
        if isinstance(WINDSPEEDXSlice, list):
            WINDSPEEDXSlice = WINDSPEEDXSlice[0]
        AODXSlice = newAncGroup.getDataset('AOD').data['AOD'][-1].copy()
        if isinstance(AODXSlice, list):
            AODXSlice = AODXSlice[0]        
        # SOL_ELXSlice = newAncGroup.getDataset('ELEVATION').data['SUN'][-1].copy()
        # if isinstance(SOL_ELXSlice, list):
        #     SOL_ELXSlice = SOL_ELXSlice[0]
        SZAXSlice = newAncGroup.getDataset('SZA').data['SZA'][-1].copy()
        if isinstance(SZAXSlice, list):
            SZAXSlice = SZAXSlice[0]
        SSTXSlice = newAncGroup.getDataset('SST').data['SST'][-1].copy()
        if isinstance(SSTXSlice, list):
            SSTXSlice = SSTXSlice[0]
        SalXSlice = newAncGroup.getDataset('SAL').data['SAL'][-1].copy()
        if isinstance(SalXSlice, list):
            SalXSlice = SalXSlice[0]
        RelAzXSlice = newAncGroup.getDataset('REL_AZ').data['REL_AZ'][-1].copy()
        if isinstance(RelAzXSlice, list):
            RelAzXSlice = RelAzXSlice[0]

        # These are optional; in fact, there is no implementation of incorporating CLOUD or WAVEs into
        # any of the current Rho corrections yet (even though cloud IS passed to Zhang_Rho)
        if "CLOUD" in newAncGroup.datasets:
            CloudXSlice = newAncGroup.getDataset('CLOUD').data['CLOUD'].copy()
            if isinstance(CloudXSlice, list):
                CloudXSlice = CloudXSlice[0]     
        else:
            CloudXSlice = None
        if "WAVE_HT" in newAncGroup.datasets:
            WaveXSlice = newAncGroup.getDataset('WAVE_HT').data['WAVE_HT'].copy()
            if isinstance(WaveXSlice, list):
                WaveXSlice = WaveXSlice[0]        
        else:
            WaveXSlice = None
        if "STATION" in newAncGroup.datasets:
            StationSlice = newAncGroup.getDataset('STATION').data['STATION'].copy()
            if isinstance(StationSlice, list):
                StationSlice = StationSlice[0]        
        else:
            StationSlice = None

        # Make sure the XSlice averaging didn't bomb       
        if hasNan:            
            msg = 'ProcessL2.calculateREFLECTANCE2: Slice X"%" average error: Dataset all NaNs.'
            print(msg)
            Utilities.writeLogFile(msg)
            return False        

        # Calculate Rho_sky
        wavebands = [*esColumns] # just grabs the keys
        wavelength = []
        wavelengthStr = []
        for k in wavebands:            
            if k != "Datetag" and k != "Datetime" and k != "Timetag2":
                wavelengthStr.append(k)
                wavelength.append(float(k))           
        waveSubset = wavelength # Only used for Zhang; No subsetting for Ruddick or Mobley corrections
        rhoVec = {}
        
        if RuddickRho:
            '''This is the Ruddick, et al. 2006 approach, which has one method for 
            clear sky, and another for cloudy. Methods of this type (i.e. not accounting
            for spectral dependence (Lee et al. 2010, Gilerson et al. 2018) or polarization
            effects (Harmel et al. 2012, Mobley 2015, Hieronumi 2016, D'Alimonte and Kajiyama 2016, 
            Foster and Gilerson 2016, Gilerson et al. 2018)) are explicitly recommended in the 
            IOCCG Protocols for Above Water Radiometry Measurements and Data Analysis (Chapter 5, Draft 2019).'''
            
            li750 = ProcessL2.interpolateColumn(liXSlice, 750.0)
            es750 = ProcessL2.interpolateColumn(esXSlice, 750.0)
            sky750 = li750[0]/es750[0]

            rhoScalar, rhoDelta = RhoCorrections.RuddickCorr(sky750, rhoDefault, WINDSPEEDXSlice)
            # The above is not wavelength dependent. No need for seperate values/vectors for satellites  
            rhoVec = None
            rhoVecDelta = None

        elif ZhangRho:     
            ''' Zhang rho is based on Zhang et al. 2017 and calculates the wavelength-dependent rho vector
            separated for sun and sky to include polarization factors.
            
            Model limitations: AOD 0 - 0.2, Solar zenith 0-60 deg, Wavelength 350-1000 nm.'''                   

            # Need to limit the input for the model limitations. This will also mean cutting out Li, Lt, and Es 
            # from non-valid wavebands.
            if AODXSlice >0.2:
                msg = f'AOD = {AODXSlice}. Maximum Aerosol Optical Depth Reached. Setting to 0.2'
                print(msg)
                Utilities.writeLogFile(msg) 
                AODXSlice = 0.2
            if SZAXSlice > 60:
                # SZA>60 should be prevented in the ConfigWindow now anyway. Redundant...
                # msg = f'SZA = {SZAXSlice}. Maximum Solar Zenith Reached. Setting to 60'
                # SZA is too important to the model. If it's out of bounds, skip the record...
                msg = f'SZA = {SZAXSlice}. Maximum Solar Zenith Exceeded. Aborting slice.'
                print(msg)
                Utilities.writeLogFile(msg) 
                # SZAXSlice = 60                
                return False
            if min(wavelength) < 350 or max(wavelength) > 1000:
                msg = f'Wavelengths extend beyond model limits. Truncating to 350 - 1000 nm.'
                print(msg)
                Utilities.writeLogFile(msg) 
                wave_old = wavelength.copy()
                wave_list = [(i, band) for i, band in enumerate(wave_old) if (band >=350) and (band <= 1000)]
                wave_array = np.array(wave_list)
                # wavelength is now truncated to only valid wavebands for use in Zhang models
                waveSubset = wave_array[:,1].tolist()            
            
            rhoStructure, rhoVecDelta = RhoCorrections.ZhangCorr(WINDSPEEDXSlice,AODXSlice, \
                CloudXSlice,SZAXSlice,SSTXSlice,SalXSlice,RelAzXSlice,waveSubset)
            rhoVector = rhoStructure['ρ']
            for i, k in enumerate(waveSubset):
                rhoVec[str(k)] = rhoVector[0,i]

        # Calculate hyperspectral Thuillier F0 function
        F0_hyper = ProcessL2.Thuillier(dateTag, wavelength)
        if F0_hyper is None:
            msg = "No hyperspectral ThuillierF0. Aborting."
            print(msg)
            Utilities.writeLogFile(msg)
            return False

        # Calculate Thuillier for each of the satellite bandsets
        if ConfigFile.settings['bL2WeightMODISA']:
            MODISwavelength = Weight_RSR.MODISBands()
            wave_old = MODISwavelength.copy()
            wave_list = [(i, band) for i, band in enumerate(wave_old) if (band >=350) and (band <= 1000)]
            wave_array = np.array(wave_list)
            # wavelength is now truncated to only valid wavebands for use in Zhang models
            waveSubsetMODIS = wave_array[:,1].tolist() 
            # F0MODISA = Weight_RSR.processMODISBands(F0_hyper, sensor='A')
            F0_MODISA = ProcessL2.Thuillier(dateTag, MODISwavelength)




        # Build a slice object for (ir)radiances to be passed to spectralReflectance method
        # These slices are unique and independant of root data or earlier slices in the same root object
        xSlice = {}        
        # Full hyperspectral
        sensor = 'HYPER'
        xSlice['es'] = esXSlice
        xSlice['li'] = liXSlice
        xSlice['lt'] = ltXSlice
        xSlice['esSTD'] = esXstd        
        xSlice['liSTD'] = liXstd        
        xSlice['ltSTD'] = ltXstd
        F0 = F0_hyper
        # Populate the relevant fields in root      
        ProcessL2.spectralReflectance(root, sensor, timeObj, xSlice, F0, rhoScalar, rhoDelta, rhoVec, rhoVecDelta, waveSubset)  

        # Apply residual NIR corrections
        # Perfrom near-infrared residual correction to remove additional atmospheric and glint contamination
        if ConfigFile.settings["bL2PerformNIRCorrection"]:
            rrsNIRCorr, nLwNIRCorr = ProcessL2.nirCorrection(root, sensor, F0)      
        
        # Satellites
        if ConfigFile.settings['bL2WeightMODISA']:            
            print('Processing MODISA')            
            sensor = 'MODISA'
            xSlice['es'] = esXSliceMODISA
            xSlice['li'] = liXSliceMODISA
            xSlice['lt'] = ltXSliceMODISA
            xSlice['esSTD'] = esXstdMODISA   
            xSlice['liSTD'] = liXstdMODISA  
            xSlice['ltSTD'] = ltXstdMODISA
            F0 = F0_MODISA
            if ZhangRho:
                rhoVecMODISA = Weight_RSR.processMODISBands(rhoVec,sensor='A')
                rhoDeltaMODISA = Weight_RSR.processMODISBands(rhoVecDelta,sensor='A')
            else: 
                rhoVecMODISA = None
                rhoDeltaMODISA = None
            
            ProcessL2.spectralReflectance(root, sensor, timeObj, xSlice, F0, rhoScalar, rhoDelta, rhoVecMODISA, rhoDeltaMODISA, waveSubsetMODIS) 
            # Perfrom near-infrared residual correction to remove additional atmospheric and glint contamination
            # For satellite bands, this cannot use SimSpec...
            if ConfigFile.settings["bL2PerformNIRCorrection"]:                
                # Can't apply good NIR corrs, so use correction factors from hyperspectral instead.
                ProcessL2.nirCorrectionSatellite(root, sensor, rrsNIRCorr, nLwNIRCorr)
    
        return True

    @staticmethod
    def calculateREFLECTANCE(root, node, gpsGroup, satnavGroup, pyrGroup, ancData, modData):
        ''' Filter out high wind and high/low SZA.
            Interpolate ancillary/model data, average intervals.
            Run meteorology quality checks.
            Pass to calculateREFLECTANCE2 for rho calcs, Rrs, NIR correction.'''

        print("calculateREFLECTANCE")                   

        # These groups have datasets with TT2 and Datetag integrated into the array
        referenceGroup = node.getGroup("IRRADIANCE")
        sasGroup = node.getGroup("RADIANCE")

        if not ConfigFile.settings["bL1cSolarTracker"]:
            ancTemp = node.getGroup("TEMPORARY")

        # If GMAO modeled data is selected in ConfigWindow, and an ancillary field data file
        # is provided in Main Window, then use the model data to fill in gaps in the field 
        # record prior to interpolating to L2 timestamps.
        #   Otherwise, interpolate just the field ancillary data, if it exists
        #   Otherwise, use the selected default values from ConfigWindow      
        # This will populate the group ANCILLARY with ancillary and/or modelled datasets
        # and/or default values, all interpolated to the radiometric data timestamps.
        #
        # This interpolation is only necessary for the ancillary datasets that require
        # either field or GMAO or GUI default values. The remaining ancillary data
        # are culled from datasets in groups already interpolated in L1E
        esData = referenceGroup.getDataset("ES") # From node, the input file
        # InterpAncillary is basically only concerned with datasets that must be filled
        # in with model or default data (wind, sst, wt, sal, cloud, wave)
        ProcessL2.interpAncillary(node, ancData, modData, esData)
        
        # Now that ancillary data has been interpolated, it is matched up with
        #  additional ancillary data (gps, solartracker, non-solartracker, etc.), all @ 1:1.
        ancGroup = node.getGroup("ANCILLARY") # from interpAncillary above...

        # At this stage, ancGroup has Datetag & Timetag2 integrated into data arrays
        # tied to AOD, SAL, SST, and WINDSPEED. These sets also have flags.
        # Add remaining datasets (as needed)
        ancGroup.addDataset('HEADING')
        ancGroup.addDataset('LATITUDE')
        ancGroup.addDataset('LONGITUDE')        
        ancGroup.addDataset('SOLAR_AZ')
        ancGroup.addDataset('SZA')        
        ancGroup.addDataset('REL_AZ')        

        # The following datasets were interpolated to the radiometry timestamps in L1E.
        # Shift them into the ANCILLARY group as needed.
        #
        # GPS Group
        # These have TT2/Datetag incorporated in arrays
        # Change their column names from NONE to something appropriate to be consistent in 
        # ancillary group going forward
        ancGroup.datasets['LATITUDE'] = gpsGroup.getDataset('LATITUDE')
        ancGroup.datasets['LATITUDE'].changeColName('NONE','LATITUDE')
        ancGroup.datasets['LONGITUDE'] = gpsGroup.getDataset('LONGITUDE')
        ancGroup.datasets['LONGITUDE'].changeColName('NONE','LONGITUDE')
        if ConfigFile.settings["bL1cSolarTracker"]:
            # These have TT2/Datetag incorporated in arrays
            ancGroup.datasets['HEADING'] = gpsGroup.getDataset('COURSE')
            ancGroup.datasets['HEADING'].changeColName('TRUE','HEADING')
            ancGroup.addDataset('SPEED')
            ancGroup.datasets['SPEED'] = gpsGroup.getDataset('SPEED')
            ancGroup.datasets['SPEED'].changeColName('NONE','SPEED')
        else:
            # NOTRACKER Group
            # These have TT2/Datetag incorporated in arrays
            ancGroup.datasets['HEADING'] = ancTemp.getDataset('HEADING')
            ancGroup.datasets['HEADING'].changeColName('NONE','HEADING')
            ancGroup.datasets['SZA'] = ancTemp.getDataset('SZA')
            ancGroup.datasets['SZA'].changeColName('NONE','SZA')
            ancGroup.datasets['SOLAR_AZ'] = ancTemp.getDataset('SOLAR_AZ')
            ancGroup.datasets['SOLAR_AZ'].changeColName('NONE','SOLAR_AZ')
            ancGroup.datasets['REL_AZ'] = ancTemp.getDataset('REL_AZ')
            ancGroup.datasets['REL_AZ'].changeColName('NONE','REL_AZ')

            # Done with the temporary ancillary group; delete it
            for gp in node.groups:
                if gp.id == "TEMPORARY":
                    node.removeGroup(gp)
            
        if satnavGroup:
            ancGroup.datasets['SOLAR_AZ'] = satnavGroup.getDataset('AZIMUTH')
            ancGroup.datasets['SOLAR_AZ'].changeColName('SUN','SOLAR_AZ')
            elevation = satnavGroup.getDataset('ELEVATION')
            sza = []
            for k in elevation.data["SUN"]:
                sza.append(90-k)
            elevation.data["SUN"] = sza # changed for sza
            ancGroup.datasets['SZA'] = elevation # actually sza
            ancGroup.datasets['SZA'].changeColName('SUN','SZA')
            ancGroup.datasets['HUMIDITY'] = satnavGroup.getDataset('HUMIDITY')
            ancGroup.datasets['HUMIDITY'].changeColName('NONE','HUMIDITY')
            # ancGroup.datasets['HEADING'] = satnavGroup.getDataset('HEADING') # Use GPS heading instead
            ancGroup.addDataset('PITCH')            
            ancGroup.datasets['PITCH'] = satnavGroup.getDataset('PITCH')
            ancGroup.datasets['PITCH'].changeColName('SAS','PITCH')
            ancGroup.addDataset('POINTING')
            ancGroup.datasets['POINTING'] = satnavGroup.getDataset('POINTING')
            ancGroup.datasets['POINTING'].changeColName('ROTATOR','POINTING')
            ancGroup.datasets['REL_AZ'] = satnavGroup.getDataset('REL_AZ')
            ancGroup.datasets['REL_AZ'].datasetToColumns()
            ancGroup.addDataset('ROLL')
            ancGroup.datasets['ROLL'] = satnavGroup.getDataset('ROLL')  
            ancGroup.datasets['ROLL'].changeColName('SAS','ROLL')
        
        if pyrGroup is not None:
            #PYROMETER
            ancGroup.datasets['SST_IR'] = pyrGroup.getDataset("T")  
            ancGroup.datasets['SST_IR'].datasetToColumns()
            ancGroup.datasets['SST_IR'].changeColName('IR','SST_IR')

        # At this stage, all datasets in all groups of node have Timetag2
        #     and Datetag incorporated into data arrays. Calculate and add
        #     Datetime to each data array.
        Utilities.rootAddDateTimeL2(node)

        # Filter the spectra from the entire collection before slicing the intervals

        # Stations
        #   The simplest approach is to run station extraction seperately from underway data.
        #   This means, if station extraction is selected in the GUI, all non-station data will be
        #   discarded here prior to any further filtering or processing.
        station = None
        if ConfigFile.settings["bL2Stations"]:
            msg = "Extracting station data only. All other records will be discarded."
            print(msg)
            Utilities.writeLogFile(msg)

            try:
                stations = ancGroup.getDataset("STATION").columns["STATION"]
                dateTime = ancGroup.getDataset("STATION").columns["Datetime"]
            except:
                msg = "No station data found in ancGroup. Aborting."
                print(msg)
                Utilities.writeLogFile(msg)
                return False

            badTimes = []
            start = False
            stop = False         
            for index, station in enumerate(stations):
                # print(f'index: {index}, station: {station}, datetime: {dateTime[index]}')
                if np.isnan(station) and start == False:
                    start = dateTime[index]
                if not np.isnan(station) and not (start == False) and (stop == False):
                    stop = dateTime[index-1]
                    badTimes.append([start, stop])
                    start = False
                    stop = False 
                # End of file, no active station
                if np.isnan(station) and not (start == False) and (index == len(stations)-1):
                    stop = dateTime[index]
                    badTimes.append([start, stop])            

            if badTimes is not None and len(badTimes) != 0:
                print('Removing records...')
                check = ProcessL2.filterData(referenceGroup, badTimes)   
                if check > 0.99:
                    msg = "Too few spectra remaining. Abort."
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return False         
                ProcessL2.filterData(sasGroup, badTimes)
                ProcessL2.filterData(ancGroup, badTimes) 
            
            # What to do if there are multiple, non-unique station numbers??
            ''' TO DO: This needs to be addressed for non-SolarTracker files, which can
                be much longer than one hour long and capture more than one station ''' 
            
            stations = ancGroup.getDataset("STATION").columns["STATION"]
            station = np.unique(stations)
            if len(station) > 1:
                msg = "Multiple non-unique station names found in this file. Abort."
                alert = QtWidgets.QMessageBox()
                alert.setText(msg)
                alert.exec_()
                print(msg)
                Utilities.writeLogFile(msg)
                return False        

            station = str(round(station[0]*100)/100)

        # Lt Quality Filtering; anomalous elevation in the NIR
        if ConfigFile.settings["bL2LtUVNIR"]:
            msg = "Applying Lt quality filtering to eliminate spectra."
            print(msg)
            Utilities.writeLogFile(msg)
            # This is not well optimized for large files...
            badTimes = ProcessL2.ltQuality(sasGroup)
                
            if badTimes is not None:
                print('Removing records... Can be slow for large files')
                check = ProcessL2.filterData(referenceGroup, badTimes)
                # check is now fraction removed
                if check > 0.99:
                    msg = "Too few spectra remaining. Abort."
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return False                  
                ProcessL2.filterData(sasGroup, badTimes)
                ProcessL2.filterData(ancGroup, badTimes)
                
        # Filter low SZAs and high winds after interpolating model/ancillary data
        maxWind = float(ConfigFile.settings["fL2MaxWind"]) 
        SZAMin = float(ConfigFile.settings["fL2SZAMin"])
        SZAMax = float(ConfigFile.settings["fL2SZAMax"])

        wind = ancGroup.getDataset("WINDSPEED").data["WINDSPEED"]
        SZA = ancGroup.datasets["SZA"].columns["SZA"]
        timeStamp = ancGroup.datasets["SZA"].columns["Datetime"]
        
        badTimes = None
        i=0
        start = -1
        stop = []         
        for index in range(len(SZA)):
            if SZA[index] < SZAMin or SZA[index] > SZAMax or wind[index] > maxWind:
                i += 1                              
                if start == -1:
                    if wind[index] > maxWind:
                        msg =f'High Wind: {round(wind[index])}'
                    else:
                        msg =f'Low SZA. SZA: {round(SZA[index])}'
                    print(msg)
                    Utilities.writeLogFile(msg)                                                                   
                    start = index
                stop = index 
                if badTimes is None:
                    badTimes = []                               
            else:                                
                if start != -1:
                    msg = f'Passed. SZA: {round(SZA[index])}, Wind: {round(wind[index])}'
                    print(msg)
                    Utilities.writeLogFile(msg)                                               
                    startstop = [timeStamp[start],timeStamp[stop]]
                    msg = f'   Flag data from TT2: {startstop[0]} to {startstop[1]}'
                    # print(msg)
                    Utilities.writeLogFile(msg)                                               
                    badTimes.append(startstop)
                    start = -1
        msg = f'Percentage of data out of SZA and Wind limits: {round(100*i/len(timeStamp))} %'
        print(msg)
        Utilities.writeLogFile(msg)

        if start != -1 and stop == index: # Records from a mid-point to the end are bad
            startstop = [timeStamp[start],timeStamp[stop]]
            msg = f'   Flag data from TT2: {startstop[0]} to {startstop[1]}'
            # print(msg)
            Utilities.writeLogFile(msg)                                               
            if badTimes is None: # only one set of records
                badTimes = [startstop]
            else:
                badTimes.append(startstop)

        if start==0 and stop==index: # All records are bad                           
            return False
        
        if badTimes is not None and len(badTimes) != 0:
            print('Removing records...')
            check = ProcessL2.filterData(referenceGroup, badTimes)   
            if check > 0.99:
                msg = "Too few spectra remaining. Abort."
                print(msg)
                Utilities.writeLogFile(msg)
                return False         
            ProcessL2.filterData(sasGroup, badTimes)
            ProcessL2.filterData(ancGroup, badTimes)            
                    
       # Spectral Outlier Filter
        enableSpecQualityCheck = ConfigFile.settings['bL2EnableSpecQualityCheck']
        if enableSpecQualityCheck:
            badTimes = None
            msg = "Applying spectral filtering to eliminate noisy spectra."
            print(msg)
            Utilities.writeLogFile(msg)
            inFilePath = root.attributes['In_Filepath']
            badTimes1 = ProcessL2.specQualityCheck(referenceGroup, inFilePath, station)
            badTimes2 = ProcessL2.specQualityCheck(sasGroup, inFilePath, station)
            if badTimes1 is not None and badTimes2 is not None:
                badTimes = np.append(badTimes1,badTimes2, axis=0)
            elif badTimes1 is not None:
                badTimes = badTimes1
            elif badTimes2 is not None:
                badTimes = badTimes2

            if badTimes is not None:
                print('Removing records...')
                check = ProcessL2.filterData(referenceGroup, badTimes)   
                if check > 0.99:
                    msg = "Too few spectra remaining. Abort."
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return False                 
                ProcessL2.filterData(sasGroup, badTimes)
                ProcessL2.filterData(ancGroup, badTimes)       

        # Next apply the Meteorological Filter prior to slicing
        enableMetQualityCheck = int(ConfigFile.settings["bL2EnableQualityFlags"])          
        if enableMetQualityCheck:
            msg = "Applying meteorological filtering to eliminate spectra."
            print(msg)
            Utilities.writeLogFile(msg)
            badTimes = ProcessL2.metQualityCheck(referenceGroup, sasGroup)
                                  
            if badTimes is not None:
                if len(badTimes) == esData.data.size:
                    msg = "All data flagged for deletion. Abort."
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return False
                print('Removing records...')
                check = ProcessL2.filterData(referenceGroup, badTimes)   
                if check > 0.99:
                    msg = "Too few spectra remaining. Abort."
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return False              
                ProcessL2.filterData(sasGroup, badTimes)
                ProcessL2.filterData(ancGroup, badTimes)
        
        #
        # Break up data into time intervals, and calculate reflectance
        #
        esColumns = esData.columns
        timeStamp = esColumns["Datetime"]
        # tt2 = esColumns["Timetag2"]        
        esLength = len(list(esColumns.values())[0])
        interval = float(ConfigFile.settings["fL2TimeInterval"])    
        
        if interval == 0:
            # Here, take the complete time series
            print("No time binning. This can take a moment.")
            # Utilities.printProgressBar(0, esLength-1, prefix = 'Progress:', suffix = 'Complete', length = 50)
            for i in range(0, esLength-1):
                Utilities.printProgressBar(i+1, esLength-1, prefix = 'Progress:', suffix = 'Complete', length = 50)
                start = i
                end = i+1

                if not ProcessL2.calculateREFLECTANCE2(root, sasGroup, referenceGroup, ancGroup, start, end):
                    msg = 'ProcessL2.calculateREFLECTANCE2 unsliced failed. Abort.'
                    print(msg)
                    Utilities.writeLogFile(msg)                      
                    continue                                                      
        else:
            msg = 'Binning datasets to ensemble time interval.'
            print(msg)
            Utilities.writeLogFile(msg)    
            # Iterate over the time ensembles
            start = 0
            # endTime = Utilities.timeTag2ToSec(tt2[0]) + interval
            # endFileTime = Utilities.timeTag2ToSec(tt2[-1])
            endTime = timeStamp[0] + datetime.timedelta(0,interval)
            endFileTime = timeStamp[-1]
            timeFlag = False
            if endTime > endFileTime:
                endTime = endFileTime
                timeFlag = True # In case the whole file is shorter than the selected interval

            for i in range(0, esLength):
                # time = Utilities.timeTag2ToSec(tt2[i])
                time = timeStamp[i]
                if (time > endTime) or timeFlag: # end of increment reached
                                        
                    if timeFlag:
                        end = len(timeStamp)-1 # File shorter than interval; include all spectra
                    else:
                        endTime = time + datetime.timedelta(0,interval) # increment for the next bin loop
                        end = i # end of the slice is up to and not including...so -1 is not needed   
                    if endTime > endFileTime:
                        endTime = endFileTime                 

                    if not ProcessL2.calculateREFLECTANCE2(root, sasGroup, referenceGroup, ancGroup, start, end):
                        msg = 'ProcessL2.calculateREFLECTANCE2 with slices failed. Continue.'
                        print(msg)
                        Utilities.writeLogFile(msg)    

                        start = i                       
                        continue                          
                    start = i

                    if timeFlag:
                        break
            # Try converting any remaining
            end = esLength-1
            time = timeStamp[start]
            if time < (endTime - datetime.timedelta(0,interval)):          

                if not ProcessL2.calculateREFLECTANCE2(root,sasGroup, referenceGroup, ancGroup, start, end):
                    msg = 'ProcessL2.calculateREFLECTANCE2 ender failed.'
                    print(msg)
                    Utilities.writeLogFile(msg)    

        # Filter reflectances for negative spectra  
        ''' # 1) Any spectrum that has any negative values between
            #  380 - 700ish, remove the entire spectrum. Otherwise, 
            # set negative bands to 0.
            # This should probably wait until further analysis to see
            # how much overcorrecting is being done by the SimSpec NIR
            # correction. '''
        if ConfigFile.settings["bL2NegativeSpec"]:
            msg = "Filtering reflectance spectra for negative values."
            print(msg)
            Utilities.writeLogFile(msg)
            # newReflectanceGroup = root.groups[0]
            newReflectanceGroup = root.getGroup("REFLECTANCE")
            badTimes1 = ProcessL2.negReflectance(newReflectanceGroup, 'Rrs_HYPER')
            badTimes2 = ProcessL2.negReflectance(newReflectanceGroup, 'nLw_HYPER')

            # if ConfigFile.settings['bL2WeightMODISA']:



            if badTimes1 is not None and badTimes2 is not None:
                badTimes = np.append(badTimes1,badTimes2, axis=0)
            elif badTimes1 is not None:
                badTimes = badTimes1
            elif badTimes2 is not None:
                badTimes = badTimes2
                
            if badTimes is not None:
                print('Removing records...')               
                
                check = ProcessL2.filterData(newReflectanceGroup, badTimes)
                if check > 0.99:
                    msg = "Too few spectra remaining. Abort."
                    print(msg)
                    Utilities.writeLogFile(msg)
                    return False                  
                # ProcessL2.filterData(root.groups[1], badTimes)
                ProcessL2.filterData(root.getGroup("IRRADIANCE"), badTimes)
                # ProcessL2.filterData(root.groups[2], badTimes)
                ProcessL2.filterData(root.getGroup("RADIANCE"), badTimes)
                # ProcessL2.filterData(root.groups[3], badTimes)        
                ProcessL2.filterData(root.getGroup("ANCILLARY"), badTimes)

        return True
    
    @staticmethod
    def processL2(node, ancillaryData=None):
        '''Calculates Rrs and nLw after quality checks and filtering, glint removal, residual 
            subtraction. Weights for satellite bands, and outputs plots and SeaBASS datasets'''

        root = HDFRoot.HDFRoot()
        root.copyAttributes(node)
        root.attributes["PROCESSING_LEVEL"] = "2"

        root.addGroup("REFLECTANCE")
        root.addGroup("IRRADIANCE")
        root.addGroup("RADIANCE")    

        pyrGroup = None
        gpsGroup = None
        satnavGroup = None
        ancGroupNoTracker = None
        for gp in node.groups:
            if gp.id.startswith("GPS"):
                gpsGroup = gp
            if gp.id == ("SOLARTRACKER"):
                satnavGroup = gp
            # if gp.id == ("SOLARTRACKER_STATUS"):
            #     satnavGroup = gp            
            if gp.id.startswith("PYROMETER"):
                pyrGroup = gp
            if gp.id.startswith("ANCILLARY_NOTRACKER"):
                # This copies the ancillary data from NOTRACKER into AncillaryData so it can be
                # interpolated as in SOLARTRACKER, at which time it is flipped back into ancGroup
                ancGroupNoTracker = gp
                ancillaryData = AncillaryReader.ancillaryFromNoTracker(gp)
                # SZA = ancGroupNoTracker.datasets["SZA"].data["NONE"]                
                temp = node.addGroup("TEMPORARY")
                temp.copy(ancGroupNoTracker)
                # for ds in ancGroupNoTracker.datasets:
                #     temp.addDataset(ds)
        node.removeGroup(ancGroupNoTracker)
                
        root.addGroup("ANCILLARY")
        node.addGroup("ANCILLARY")

        # Retrieve MERRA2 model ancillary data        
        if ConfigFile.settings["bL2pGetAnc"] ==1:         
            msg = 'Model data for Wind and AOD may be used to replace blank values. Reading in model data...'
            print(msg)
            Utilities.writeLogFile(msg)  
            modData = GetAnc.getAnc(gpsGroup)
            if modData == None:
                return None
        else:
            modData = None

        # Need to either create a new ancData object, or populate the nans in the current one with the model data
        if not ProcessL2.calculateREFLECTANCE(root, node, gpsGroup, satnavGroup, pyrGroup, ancillaryData, modData):
            return None

        root.attributes["Rrs_UNITS"] = "1/sr"
        root.attributes["nLw_UNITS"] = "uW/cm^2/nm/sr"
        
        # Check to insure at least some data survived quality checks
        if root.getGroup("REFLECTANCE").getDataset("Rrs_HYPER").data is None:
            msg = "All data appear to have been eliminated from the file. Aborting."
            print(msg)
            Utilities.writeLogFile(msg)  
            return None

        # Now strip datetimes from all datasets
        for gp in root.groups:
            for dsName in gp.datasets:                
                ds = gp.datasets[dsName]
                if "Datetime" in ds.columns:
                    ds.columns.pop("Datetime")
                ds.columnsToDataset() 

        return root
