''' Process L1BQC to L2 '''
import os
import collections
import warnings
import time
import datetime
import copy
import numpy as np
import scipy as sp
from PyQt5 import QtWidgets
from tqdm import tqdm

# Source
from Source.HDFRoot import HDFRoot
from Source.ConfigFile import ConfigFile
from Source.RhoCorrections import RhoCorrections
from Source.Weight_RSR import Weight_RSR
from Source.ProcessL2OCproducts import ProcessL2OCproducts
from Source.ProcessL2BRDF import ProcessL2BRDF

# PIU
from Source.PIU.Uncertainty_Analysis import Propagate
from Source.PIU.HyperOCR import HyperOCR, HyperOCRUtils
from Source.PIU.TriOS import TriOS
from Source.PIU.DALEC import Dalec

#Utilities
from Source.utils import loggingHCP as logging
from Source.utils import dating
from Source.utils import filtering
from Source.utils import comparing
from Source.utils import F0ing


class ProcessL2:
    ''' Process L2 '''

    @staticmethod
    def nirCorrectionSatellite(root, sensor, rrsNIRCorr, nLwNIRCorr):
        newReflectanceGroup = root.getGroup("REFLECTANCE")
        newRrsData = newReflectanceGroup.getDataset(f'Rrs_{sensor}')
        newnLwData = newReflectanceGroup.getDataset(f'nLw_{sensor}')

        # These will include all slices in root so far
        # Below the most recent/current slice [-1] will be selected for processing
        rrsSlice = newRrsData.columns
        nLwSlice = newnLwData.columns

        for k in rrsSlice:
            if (k != 'Datetime') and (k != 'Datetag') and (k != 'Timetag2'):
                rrsSlice[k][-1] -= rrsNIRCorr
        for k in nLwSlice:
            if (k != 'Datetime') and (k != 'Datetag') and (k != 'Timetag2'):
                nLwSlice[k][-1] -= nLwNIRCorr

        newRrsData.columnsToDataset()
        newnLwData.columnsToDataset()


    @staticmethod
    def nirCorrection(node, sensor, F0):
        # F0 is sensor specific, but ultimately, SimSpec can only be applied to hyperspectral data anyway,
        # so output the correction and apply it to satellite bands later.
        simpleNIRCorrection = int(ConfigFile.settings["bL2SimpleNIRCorrection"])
        simSpecNIRCorrection = int(ConfigFile.settings["bL2SimSpecNIRCorrection"])

        newReflectanceGroup = node.getGroup("REFLECTANCE")
        newRrsData = newReflectanceGroup.getDataset(f'Rrs_{sensor}')
        newnLwData = newReflectanceGroup.getDataset(f'nLw_{sensor}')
        newRrsUNCData = newReflectanceGroup.getDataset(f'Rrs_{sensor}_unc')
        newnLwUNCData = newReflectanceGroup.getDataset(f'nLw_{sensor}_unc')

        newNIRData = newReflectanceGroup.getDataset(f'nir_{sensor}')
        newNIRnLwData = newReflectanceGroup.getDataset(f'nir_nLw_{sensor}')

        # These will include all slices in node so far
        # Below the most recent/current slice [-1] will be selected for processing
        rrsSlice = newRrsData.columns
        nLwSlice = newnLwData.columns
        nirSlice = newNIRData.columns
        nirnLwSlice = newNIRnLwData.columns

        # # Perform near-infrared residual correction to remove additional atmospheric and glint contamination
        # if ConfigFile.settings["bL2PerformNIRCorrection"]:
        if simpleNIRCorrection:
            # Data show a minimum near 725; using an average from above 750 leads to negative reflectances
            # Find the minimum between 700 and 800, and subtract it from spectrum (spectrally flat)
            logging.writeLogFileAndPrint("Perform simple residual NIR subtraction.")

            # rrs correction
            NIRRRs = []
            for k in rrsSlice:
                if (k == 'Datetime') or (k == 'Datetag') or (k == 'Timetag2'):
                    continue
                if float(k) >= 700 and float(k) <= 800:
                    NIRRRs.append(rrsSlice[k][-1])
            rrsNIRCorr = min(NIRRRs)
            if rrsNIRCorr < 0:
                #   NOTE: SeaWiFS protocols for residual NIR were never intended to ADD reflectance
                #   This is most likely in blue, non-turbid waters not intended for NIR offset correction.
                #   Revert to NIR correction of 0 when this happens. No good way to update the L2 attribute
                #   metadata because it may only be on some ensembles within a file.
                logging.writeLogFileAndPrint(f'Bad NIR Correction {rrsNIRCorr:0.4f} [sr^-1]. Revert to No NIR correction.')
                rrsNIRCorr = 0
            # Subtract average from each waveband
            for k in rrsSlice:
                if (k == 'Datetime') or (k == 'Datetag') or (k == 'Timetag2'):
                    continue

                rrsSlice[k][-1] -= rrsNIRCorr

            nirSlice['NIR_offset'].append(rrsNIRCorr)

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

            nirnLwSlice['NIR_offset'].append(nLwNIRCorr)

        elif simSpecNIRCorrection:
            # From Ruddick 2005, Ruddick 2006 use NIR normalized similarity spectrum
            # (spectrally flat)
            logging.writeLogFileAndPrint("Perform similarity spectrum residual NIR subtraction.")

            # For simplicity, follow calculation in rho (surface reflectance), then covert to rrs
            ρSlice = copy.deepcopy(rrsSlice)
            for k,value in ρSlice.items():
                if (k == 'Datetime') or (k == 'Datetag') or (k == 'Timetag2'):
                    continue
                ρSlice[k][-1] = value[-1] * np.pi

            # These ratios are for rho = pi*Rrs
            α1 = 2.35 # 720/780 only good for rho(720)<0.03
            α2 = 1.91 # 780/870 try to avoid, data is noisy here
            threshold = 0.03

            # Retrieve TSIS-1s
            wavelength = [float(key) for key in F0.keys()]
            F0 = [value for value in F0.values()]

            # Rrs
            ρ720 = []
            x = []
            for k in ρSlice:
                if (k == 'Datetime') or (k == 'Datetag') or (k == 'Timetag2'):
                    continue
                if float(k) >= 700 and float(k) <= 750:
                    x.append(float(k))

                    # convert to surface reflectance ρ = π * Rrs
                    ρ720.append(ρSlice[k][-1]) # Using current element/slice [-1]

            # if not ρ720:
            #     print("Error: NIR wavebands unavailable")
            #     if os.environ["HYPERINSPACE_CMD"].lower() == 'false':
            #         QtWidgets.QMessageBox.critical("Error", "NIR wavebands unavailable")
            ρ1 = sp.interpolate.interp1d(x,ρ720)(720)
            F01 = sp.interpolate.interp1d(wavelength,F0)(720)
            ρ780 = []
            x = []
            for k in ρSlice:
                if k in ('Datetime', 'Datetag', 'Timetag2'):
                    continue
                if float(k) >= 760 and float(k) <= 800:
                    x.append(float(k))
                    ρ780.append(ρSlice[k][-1])
            if not ρ780:
                print("Error: NIR wavebands unavailable")
                if os.environ["HYPERINSPACE_CMD"].lower() == 'false':
                    QtWidgets.QMessageBox.critical("Error", "NIR wavebands unavailable")
            ρ2 = sp.interpolate.interp1d(x,ρ780)(780)
            F02 = sp.interpolate.interp1d(wavelength,F0)(780)
            ρ870 = []
            x = []
            for k in ρSlice:
                if k in ('Datetime', 'Datetag', 'Timetag2'):
                    continue
                if float(k) >= 850 and float(k) <= 890:
                    x.append(float(k))
                    ρ870.append(ρSlice[k][-1])
            if not ρ870:
                logging.writeLogFileAndPrint('No data found at 870 nm')
                ρ3 = None
                F03 = None
            else:
                ρ3 = sp.interpolate.interp1d(x,ρ870)(870)
                F03 = sp.interpolate.interp1d(wavelength,F0)(870)

            # Reverts to primary mode even on threshold trip in cases where no 870nm available
            if ρ1 < threshold or not ρ870:
                ε = (α1*ρ2 - ρ1)/(α1-1)
                εnLw = (α1*ρ2*F02 - ρ1*F01)/(α1-1)
                logging.writeLogFileAndPrint(f'offset(rrs) = {ε}; offset(nLw) = {εnLw}')
            else:
                logging.writeLogFileAndPrint("SimSpec threshold tripped. Using 780/870 instead.")
                ε = (α2*ρ3 - ρ2)/(α2-1)
                εnLw = (α2*ρ3*F03 - ρ2*F02)/(α2-1)
                logging.writeLogFileAndPrint(f'offset(rrs) = {ε}; offset(nLw) = {εnLw}')

            rrsNIRCorr = ε/np.pi
            nLwNIRCorr = εnLw/np.pi

            # Now apply to rrs and nLw
            # NOTE: This correction is also susceptible to a correction that ADDS to reflectance
            #   spectrally, depending on spectral shape (see test_SimSpec.m).
            #   This is most likely in blue, non-turbid waters not intended for SimSpec.
            #   Revert to NIR correction of 0 when this happens. No good way to update the L2 attribute
            #   metadata because it may only be on some ensembles within a file.
            if rrsNIRCorr < 0:
                logging.writeLogFileAndPrint('Bad NIR Correction. Revert to No NIR correction.')
                rrsNIRCorr = 0
                nLwNIRCorr = 0
                # L2 metadata will be updated

            for k in rrsSlice:
                if (k == 'Datetime') or (k == 'Datetag') or (k == 'Timetag2'):
                    continue

                rrsSlice[k][-1] -= float(rrsNIRCorr) # Only working on the last (most recent' [-1]) element of the slice
                nLwSlice[k][-1] -= float(nLwNIRCorr)


            nirSlice['NIR_offset'].append(rrsNIRCorr)
            nirnLwSlice['NIR_offset'].append(nLwNIRCorr)

        newRrsData.columnsToDataset()
        newnLwData.columnsToDataset()
        newRrsUNCData.columnsToDataset()
        newnLwUNCData.columnsToDataset()
        newNIRData.columnsToDataset()
        newNIRnLwData.columnsToDataset()

        return rrsNIRCorr, nLwNIRCorr


    @staticmethod
    def spectralReflectance(node, sensor, timeObj, xSlice, F0, F0_unc, rhoScalar, rhoVec, waveSubset, xUNC, xBreakdownUNC=None, xBreakdownCORR=None):
        ''' The slices, stds, F0, rhoVec here are sensor-waveband specific '''
        esXSlice = xSlice['es'] # mean
        esXmedian = xSlice['esMedian']
        esXRemaining = xSlice['esRemaining']
        esXstd = xSlice['esSTD']
        liXSlice = xSlice['li']
        liXmedian = xSlice['liMedian']
        liXRemaining = xSlice['liRemaining']
        liXstd = xSlice['liSTD']
        ltXSlice = xSlice['lt']
        ltXmedian = xSlice['ltMedian']
        ltXRemaining = xSlice['ltRemaining']
        ltXstd = xSlice['ltSTD']
        dateTime = timeObj['dateTime']
        dateTag = timeObj['dateTag']
        timeTag = timeObj['timeTag']

        threeCRho = int(ConfigFile.settings["bL23CRho"])
        ZhangRho = int(ConfigFile.settings["bL2Z17Rho"])

        # Root (new/output) groups:
        newReflectanceGroup = node.getGroup("REFLECTANCE")
        newRadianceGroup = node.getGroup("RADIANCE")
        newIrradianceGroup = node.getGroup("IRRADIANCE")

        newRhoHyper, newRhoUNCHyper, newNIRnLwData, newNIRData, nLw = None, None, None, None, None

        # If this is the first ensemble spectrum, set up the new datasets
        if not f'Rrs_{sensor}' in newReflectanceGroup.datasets:
            newESData = newIrradianceGroup.addDataset(f"ES_{sensor}")
            newLIData = newRadianceGroup.addDataset(f"LI_{sensor}")
            newLTData = newRadianceGroup.addDataset(f"LT_{sensor}")
            newLWData = newRadianceGroup.addDataset(f"LW_{sensor}")

            newESDataMedian = newIrradianceGroup.addDataset(f"ES_{sensor}_median")
            newLIDataMedian = newRadianceGroup.addDataset(f"LI_{sensor}_median")
            newLTDataMedian = newRadianceGroup.addDataset(f"LT_{sensor}_median")

            newRrsData = newReflectanceGroup.addDataset(f"Rrs_{sensor}")
            newRrsUncorrData = newReflectanceGroup.addDataset(f"Rrs_{sensor}_uncorr") # Preserve uncorrected Rrs (= lt/es)
            newnLwData = newReflectanceGroup.addDataset(f"nLw_{sensor}")

            # September 2023. For clarity, drop the "Delta" nominclature in favor of
            # either STD (standard deviation of the sample) or UNC (uncertainty)
            newESSTDData = newIrradianceGroup.addDataset(f"ES_{sensor}_sd")
            newLISTDData = newRadianceGroup.addDataset(f"LI_{sensor}_sd")
            newLTSTDData = newRadianceGroup.addDataset(f"LT_{sensor}_sd")

            # No average (mean or median) or standard deviation values associated with Lw or reflectances,
            #   because these are calculated from the means of Lt, Li, Es

            newESUNCData = newIrradianceGroup.addDataset(f"ES_{sensor}_unc")
            newLIUNCData = newRadianceGroup.addDataset(f"LI_{sensor}_unc")
            newLTUNCData = newRadianceGroup.addDataset(f"LT_{sensor}_unc")
            newLWUNCData = newRadianceGroup.addDataset(f"LW_{sensor}_unc")
            newRrsUNCData = newReflectanceGroup.addDataset(f"Rrs_{sensor}_unc")
            newnLwUNCData = newReflectanceGroup.addDataset(f"nLw_{sensor}_unc")

            # Add standard deviation datasets for comparison
            newLWSTDData = newRadianceGroup.addDataset(f"LW_{sensor}_sd")
            newRrsSTDData = newReflectanceGroup.addDataset(f"Rrs_{sensor}_sd")
            newnLwSTDData = newReflectanceGroup.addDataset(f"nLw_{sensor}_sd")

            # add breakdowns to HDF
            if xBreakdownUNC is not None:
                newBreakdownGroup = node.addGroup("BREAKDOWN")
                newBreakdownGroup.attributes.update({
                    "unc_type": "absolute",
                    "units": "same as measurement",
                    "correlation": "not-implemented",
                    "discalimer": "components added in quadrature expected to be less accurate than Monte Carlo propagation due to lack of correlation effects"
                })
                BDData = {'ES': {}, 'LI': {}, 'LT': {}, 'LW': {}, 'Rrs': {}, 'nLw': {}}
                for key in xBreakdownUNC['ES'].keys():
                    BDData['ES'][key] = newBreakdownGroup.addDataset(f"ES_{sensor}_{key}")
                for key in xBreakdownUNC['LI'].keys():
                    BDData['LI'][key] = newBreakdownGroup.addDataset(f"LI_{sensor}_{key}")
                    BDData['LT'][key] = newBreakdownGroup.addDataset(f"LT_{sensor}_{key}")
                for key in xBreakdownUNC['Lw'].keys():
                    BDData['LW'][key]  = newBreakdownGroup.addDataset(f"LW_{sensor}_{key}")
                for key in xBreakdownUNC['nLw'].keys():
                    BDData['nLw'][key]  = newBreakdownGroup.addDataset(f"nLw_{sensor}_{key}")
                for key in xBreakdownUNC['Rrs'].keys():
                    BDData['Rrs'][key] = newBreakdownGroup.addDataset(f"Rrs_{sensor}_{key}")

            if xBreakdownCORR is not None:
                newBreakdownCORRGroup = node.addGroup("BREAKDOWN_CORRECTIONS")
                newBreakdownCORRGroup.attributes.update({
                    "units": "same as measurement",
                    "disclaimer": "values encompas the magnitude of instrument corrections: corrected signal - uncorrected signal",
                })
                BDCorr = {'ES': {}, 'LI': {}, 'LT': {}, 'LW': {}, 'Rrs': {}}
                for key in xBreakdownCORR['ES'].keys():
                    BDCorr['ES'][key] = newBreakdownCORRGroup.addDataset(f"ES_{sensor}_{key}")
                for key in xBreakdownCORR['LI'].keys():
                    BDCorr['LI'][key] = newBreakdownCORRGroup.addDataset(f"LI_{sensor}_{key}")
                    BDCorr['LT'][key] = newBreakdownCORRGroup.addDataset(f"LT_{sensor}_{key}")
                # for key in xBreakdownCORR['Lw'].keys():
                #     BDCorr['LW'][key]  = newBreakdownCORRGroup.addDataset(f"LW_{sensor}_{key}")
                # for key in xBreakdownCORR['Rrs'].keys():
                #     BDCorr['Rrs'][key] = newBreakdownCORRGroup.addDataset(f"Rrs_{sensor}_{key}")

            if sensor == 'HYPER':
                newRhoHyper = newReflectanceGroup.addDataset(f"rho_{sensor}")
                newRhoUNCHyper = newReflectanceGroup.addDataset(f"rho_{sensor}_unc")
                if ConfigFile.settings["bL2PerformNIRCorrection"]:
                    newNIRData = newReflectanceGroup.addDataset(f'nir_{sensor}')
                    newNIRnLwData = newReflectanceGroup.addDataset(f'nir_nLw_{sensor}')
        else:
            newESData = newIrradianceGroup.getDataset(f"ES_{sensor}")
            newLIData = newRadianceGroup.getDataset(f"LI_{sensor}")
            newLTData = newRadianceGroup.getDataset(f"LT_{sensor}")
            newLWData = newRadianceGroup.getDataset(f"LW_{sensor}")

            newESDataMedian = newIrradianceGroup.getDataset(f"ES_{sensor}_median")
            newLIDataMedian = newRadianceGroup.getDataset(f"LI_{sensor}_median")
            newLTDataMedian = newRadianceGroup.getDataset(f"LT_{sensor}_median")

            newRrsData = newReflectanceGroup.getDataset(f"Rrs_{sensor}")
            newRrsUncorrData = newReflectanceGroup.getDataset(f"Rrs_{sensor}_uncorr")
            newnLwData = newReflectanceGroup.getDataset(f"nLw_{sensor}")

            newESSTDData = newIrradianceGroup.getDataset(f"ES_{sensor}_sd")
            newLISTDData = newRadianceGroup.getDataset(f"LI_{sensor}_sd")
            newLTSTDData = newRadianceGroup.getDataset(f"LT_{sensor}_sd")

            # No average (mean or median) values associated with Lw or reflectances,
            #   because these are calculated from the means of Lt, Li, Es

            newESUNCData = newIrradianceGroup.getDataset(f"ES_{sensor}_unc")
            newLIUNCData = newRadianceGroup.getDataset(f"LI_{sensor}_unc")
            newLTUNCData = newRadianceGroup.getDataset(f"LT_{sensor}_unc")
            newLWUNCData = newRadianceGroup.getDataset(f"LW_{sensor}_unc")
            newRrsUNCData = newReflectanceGroup.getDataset(f"Rrs_{sensor}_unc")
            newnLwUNCData = newReflectanceGroup.getDataset(f"nLw_{sensor}_unc")

            newLWSTDData = newRadianceGroup.getDataset(f"LW_{sensor}_sd")
            newRrsSTDData = newReflectanceGroup.getDataset(f"Rrs_{sensor}_sd")
            newnLwSTDData = newReflectanceGroup.getDataset(f"nLw_{sensor}_sd")

            # add breakdowns to HDF
            if xBreakdownUNC is not None:
                newBreakdownGroup = node.addGroup("BREAKDOWN")
                BDData = {'ES': {}, 'LI': {}, 'LT': {}, 'LW': {}, 'Rrs': {}, 'nLw': {}}
                for key in xBreakdownUNC['ES'].keys():
                    BDData['ES'][key] = newBreakdownGroup.getDataset(f"ES_{sensor}_{key}")
                for key in xBreakdownUNC['LI'].keys():
                    BDData['LI'][key] = newBreakdownGroup.getDataset(f"LI_{sensor}_{key}")
                    BDData['LT'][key] = newBreakdownGroup.getDataset(f"LT_{sensor}_{key}")
                for key in xBreakdownUNC['Lw'].keys():
                    BDData['LW'][key]  = newBreakdownGroup.getDataset(f"LW_{sensor}_{key}")
                for key in xBreakdownUNC['nLw'].keys():
                    BDData['nLw'][key]  = newBreakdownGroup.getDataset(f"nLw_{sensor}_{key}")
                for key in xBreakdownUNC['Rrs'].keys():
                    BDData['Rrs'][key] = newBreakdownGroup.getDataset(f"Rrs_{sensor}_{key}")

            if xBreakdownCORR is not None:
                newBreakdownCORRGroup = node.addGroup("BREAKDOWN_CORRECTIONS")
                BDCorr = {'ES': {}, 'LI': {}, 'LT': {}, 'LW': {}, 'Rrs': {}}
                for key in xBreakdownCORR['ES'].keys():
                    BDCorr['ES'][key] = newBreakdownCORRGroup.getDataset(f"ES_{sensor}_{key}")
                for key in xBreakdownCORR['LI'].keys():
                    BDCorr['LI'][key] = newBreakdownCORRGroup.getDataset(f"LI_{sensor}_{key}")
                    BDCorr['LT'][key] = newBreakdownCORRGroup.getDataset(f"LT_{sensor}_{key}")

            if sensor == 'HYPER':
                newRhoHyper = newReflectanceGroup.getDataset(f"rho_{sensor}")
                newRhoUNCHyper = newReflectanceGroup.getDataset(f"rho_{sensor}_unc")
                if ConfigFile.settings["bL2PerformNIRCorrection"]:
                    newNIRData = newReflectanceGroup.getDataset(f'nir_{sensor}')
                    newNIRnLwData = newReflectanceGroup.addDataset(f'nir_nLw_{sensor}')

        # Add datetime stamps back onto ALL datasets associated with the current sensor
        # If this is the first spectrum, add date/time, otherwise append
        # Groups REFLECTANCE, IRRADIANCE, and RADIANCE are intiallized with empty datasets, but
        # ANCILLARY is not.
        if "Datetag" not in newRrsData.columns:
            for gp in node.groups:
                if gp.id == "ANCILLARY": # Ancillary is already populated. The other groups only have empty (named) datasets
                    continue
                else:
                    for ds in gp.datasets:
                        if sensor in ds: # Only add datetime stamps to the current sensor datasets
                            gp.datasets[ds].columns["Datetime"] = [dateTime] # mean of the ensemble datetime stamp
                            gp.datasets[ds].columns["Datetag"] = [dateTag]
                            gp.datasets[ds].columns["Timetag2"] = [timeTag]
        else:
            for gp in node.groups:
                if gp.id == "ANCILLARY":
                    continue
                else:
                    for ds in gp.datasets:
                        if sensor in ds:
                            gp.datasets[ds].columns["Datetime"].append(dateTime)
                            gp.datasets[ds].columns["Datetag"].append(dateTag)
                            gp.datasets[ds].columns["Timetag2"].append(timeTag)

        # Organise Uncertainty into wavebands
        lwUNC = {}
        rrsUNC = {}
        rhoUNC = {}
        esUNC = {}
        liUNC = {}
        ltUNC = {}

        # Only Factory - Trios has no uncertainty here
        if ConfigFile.settings['fL1bCal'] >= 2 or ConfigFile.settings['SensorType'].lower() == 'seabird':
            #or ConfigFile.settings['SensorType'].lower() == 'dalec':
            esUNC = xUNC[f'esUNC_{sensor}']  # should already be convolved to hyperspec
            liUNC = xUNC[f'liUNC_{sensor}']  # added reference to HYPER as band convolved uncertainties will no longer
            ltUNC = xUNC[f'ltUNC_{sensor}']  # overwite normal instrument uncertainties during processing
            rhoUNC = xUNC[f'rhoUNC_{sensor}']
            for i, wvl in enumerate(waveSubset):
                k = str(wvl)
                if (any([wvl == float(x) for x in esXSlice]) and
                        any([wvl == float(x) for x in liXSlice]) and
                        any([wvl == float(x) for x in ltXSlice])):  # More robust (able to handle sensor and hyper bands
                    if sensor == 'HYPER':
                        lwUNC[k] = xUNC['lwUNC'][i]
                        rrsUNC[k] = xUNC['rrsUNC'][i]
                    else:  # apply the sensor specific Lw and Rrs uncertainties
                        lwUNC[k] = xUNC[f'lwUNC_{sensor}'][i]
                        rrsUNC[k] = xUNC[f'rrsUNC_{sensor}'][i]
            #print(sensor+" rrsUNC")
            #print(rrsUNC)
        else:
            # factory case
            for wvl in waveSubset:
                k = str(wvl)
                if (any([wvl == float(x) for x in esXSlice]) and
                        any([wvl == float(x) for x in liXSlice]) and
                        any([wvl == float(x) for x in ltXSlice])):  # old version had issues with '.0'
                    esUNC[k] = 0
                    liUNC[k] = 0
                    ltUNC[k] = 0
                    rhoUNC[k] = 0
                    lwUNC[k] = 0
                    rrsUNC[k] = 0

        deleteKey = []
        for i, wvl in enumerate(waveSubset):  # loop through wavebands
            k = str(wvl)
            if (any(wvl == float(x) for x in esXSlice) and
                any(wvl == float(x) for x in liXSlice) and
                any(wvl == float(x) for x in ltXSlice)):
                # Initialize the new dataset if this is the first slice
                if k not in newESData.columns:
                    newESData.columns[k] = []
                    newLIData.columns[k] = []
                    newLTData.columns[k] = []
                    newLWData.columns[k] = []
                    newRrsData.columns[k] = []
                    newRrsUncorrData.columns[k] = []
                    newnLwData.columns[k] = []

                    # No average (mean or median) or standard deviation values associated with Lw or reflectances,
                    #   because these are calculated from the means of Lt, Li, Es
                    newESDataMedian.columns[k] = []
                    newLIDataMedian.columns[k] = []
                    newLTDataMedian.columns[k] = []

                    newESSTDData.columns[k] = []
                    newLISTDData.columns[k] = []
                    newLTSTDData.columns[k] = []
                    newESUNCData.columns[k] = []
                    newLIUNCData.columns[k] = []
                    newLTUNCData.columns[k] = []
                    newLWUNCData.columns[k] = []
                    newRrsUNCData.columns[k] = []
                    newnLwUNCData.columns[k] = []

                    newLWSTDData.columns[k] = []
                    newRrsSTDData.columns[k] = []
                    newnLwSTDData.columns[k] = []

                    if xBreakdownUNC is not None:
                        for key in BDData['ES']:
                            BDData['ES'][key].columns[k] = []
                        for key in BDData['LI']:
                            BDData['LI'][key].columns[k] = []
                            BDData['LT'][key].columns[k] = []
                        for key in BDData['LW']:
                            BDData['LW'][key].columns[k] = []
                        for key in BDData['nLw']:
                            BDData['nLw'][key].columns[k] = []
                        for key in BDData['Rrs']:
                            BDData['Rrs'][key].columns[k] = []

                    if xBreakdownCORR is not None:
                        for key in BDCorr['ES']:
                            BDCorr['ES'][key].columns[k] = []
                        for key in BDCorr['LI']:
                            BDCorr['LI'][key].columns[k] = []
                            BDCorr['LT'][key].columns[k] = []
                        for key in BDCorr['LW']:
                            BDCorr['LW'][key].columns[k] = []
                        for key in BDCorr['Rrs']:
                            BDCorr['Rrs'][key].columns[k] = []

                    if sensor == 'HYPER':
                        newRhoHyper.columns[k] = []
                        newRhoUNCHyper.columns[k] = []
                        if ConfigFile.settings["bL2PerformNIRCorrection"]:
                            newNIRData.columns['NIR_offset'] = [] # not used until later; highly unpythonic
                            newNIRnLwData.columns['NIR_offset'] = []

                # At this waveband (k); still using complete wavelength set
                es = esXSlice[k][0] # Always the zeroth element; i.e. XSlice data are independent of past slices and node
                li = liXSlice[k][0]
                lt = ltXSlice[k][0]
                esRemaining = np.asarray(esXRemaining[k]) # array of remaining ensemble values in this band
                liRemaining = np.asarray(liXRemaining[k])
                ltRemaining = np.asarray(ltXRemaining[k])
                f0 = F0[k]
                f0UNC = F0_unc[k]

                esMedian = esXmedian[k][0]
                liMedian = liXmedian[k][0]
                ltMedian = ltXmedian[k][0]

                esSTD = esXstd[k][0]
                liSTD = liXstd[k][0]
                ltSTD = ltXstd[k][0]

                # Calculate the remote sensing reflectance
                nLwUNC = {}
                lwRemainingSD = 0
                rrsRemainingSD = 0
                nLwRemainingSD = 0

                if ZhangRho or threeCRho:
                    # Only populate the valid wavelengths
                    if float(k) in waveSubset:
                        lw = lt - (rhoVec[k] * li)
                        rrs = lw / es
                        nLw = rrs*f0

                        # Now calculate the std for lw, rrs
                        lwRemaining = ltRemaining - (rhoVec[k] * liRemaining)
                        rrsRemaining = lwRemaining / esRemaining
                        lwRemainingSD = np.std(lwRemaining)
                        rrsRemainingSD = np.std(rrsRemaining)
                        nLwRemainingSD = np.std(rrsRemaining*f0)

                else:
                    lw = lt - (rhoScalar * li)
                    rrs = lw / es
                    nLw = rrs*f0

                    # Now calculate the std for lw, rrs
                    lwRemaining = ltRemaining - (rhoScalar * liRemaining)
                    rrsRemaining = lwRemaining / esRemaining
                    lwRemainingSD = np.std(lwRemaining)
                    rrsRemainingSD = np.std(rrsRemaining)
                    nLwRemainingSD = np.std(rrsRemaining*f0)

                # nLw uncertainty;
                nLwUNC[k] = np.power((rrsUNC[k]**2)*(f0**2) + (rrs**2)*(f0UNC**2), 0.5)

                newESData.columns[k].append(es)
                newLIData.columns[k].append(li)
                newLTData.columns[k].append(lt)

                rrs_uncorr = lt / es

                newESSTDData.columns[k].append(esSTD)
                newLISTDData.columns[k].append(liSTD)
                newLTSTDData.columns[k].append(ltSTD)

                newLWSTDData.columns[k].append(lwRemainingSD)
                newRrsSTDData.columns[k].append(rrsRemainingSD)
                newnLwSTDData.columns[k].append(nLwRemainingSD)

                newESDataMedian.columns[k].append(esMedian)
                newLIDataMedian.columns[k].append(liMedian)
                newLTDataMedian.columns[k].append(ltMedian)

                if xBreakdownUNC is not None:
                    for key in BDData['ES']:
                        BDData['ES'][key].columns[k].append(xBreakdownUNC['ES'][key][i])
                    for key in BDData['LI']:
                        BDData['LI'][key].columns[k].append(xBreakdownUNC['LI'][key][i])
                        BDData['LT'][key].columns[k].append(xBreakdownUNC['LT'][key][i])
                    for key in BDData['LW']:
                        BDData['LW'][key].columns[k].append(xBreakdownUNC['Lw'][key][i])
                    for key in BDData['nLw']:
                        BDData['nLw'][key].columns[k].append(xBreakdownUNC['nLw'][key][i])
                    for key in BDData['Rrs']:
                        BDData['Rrs'][key].columns[k].append(xBreakdownUNC['Rrs'][key][i])

                if xBreakdownCORR is not None:
                    for key in BDCorr['ES']:
                        BDCorr['ES'][key].columns[k].append(xBreakdownCORR['ES'][key][i])
                    for key in BDCorr['LI']:
                        BDCorr['LI'][key].columns[k].append(xBreakdownCORR['LI'][key][i])
                        BDCorr['LT'][key].columns[k].append(xBreakdownCORR['LT'][key][i])
                    # for key in BDCorr['LW']:
                    #     BDCorr['LW'][key].columns[k].append(xBreakdownCORR['Lw'][key][i])
                    # for key in BDCorr['Rrs']:
                    #     BDCorr['Rrs'][key].columns[k].append(xBreakdownCORR['Rrs'][key][i])

                # Only populate valid wavelengths. Mark others for deletion
                if float(k) in waveSubset:  # should be redundant!
                    newRrsUncorrData.columns[k].append(rrs_uncorr)
                    newLWData.columns[k].append(lw)
                    newRrsData.columns[k].append(rrs)
                    newnLwData.columns[k].append(nLw)

                    newLWUNCData.columns[k].append(lwUNC[k])
                    newRrsUNCData.columns[k].append(rrsUNC[k])
                    # newnLwUNCData.columns[k].append(nLwUNC)
                    newnLwUNCData.columns[k].append(nLwUNC[k])
                    if (ConfigFile.settings['fL1bCal']==1 and
                            ConfigFile.settings["SensorType"].lower() in ["dalec", "sorad", "trios", "trios es only"]):
                    # Specifique case for Factory-Trios
                        newESUNCData.columns[k].append(esUNC[k])
                        newLIUNCData.columns[k].append(liUNC[k])
                        newLTUNCData.columns[k].append(ltUNC[k])
                    else:
                        newESUNCData.columns[k].append(esUNC[k][0])
                        newLIUNCData.columns[k].append(liUNC[k][0])
                        newLTUNCData.columns[k].append(ltUNC[k][0])

                    if sensor == 'HYPER':
                        if ZhangRho or threeCRho:
                            newRhoHyper.columns[k].append(rhoVec[k])
                            if xUNC is not None:  # TriOS factory does not require uncertainties
                                newRhoUNCHyper.columns[k].append(xUNC[f'rhoUNC_{sensor}'][k])
                            else:
                                newRhoUNCHyper.columns[k].append(np.nan)
                        else:
                            newRhoHyper.columns[k].append(rhoScalar)
                            if xUNC is not None:  # perhaps there is a better check for TriOS Factory branch?
                                try:
                                    # TODO: explore why rho UNC is 1 index smaller than everything else
                                    # last wvl is missing
                                    newRhoUNCHyper.columns[k].append(xUNC[f'rhoUNC_{sensor}'][k])
                                except KeyError:
                                    newRhoUNCHyper.columns[k].append(0)
                            else:
                                newRhoUNCHyper.columns[k].append(np.nan)
                else:
                    deleteKey.append(k)

        # Eliminate reflectance keys/values in wavebands outside of valid set for the sake of Zhang model
        deleteKey = list(set(deleteKey))
        for key in deleteKey:
            # Only need to do this for the first ensemble in file
            if key in newRrsData.columns:
                del newLWData.columns[key]
                del newRrsUncorrData.columns[key]
                del newRrsData.columns[key]
                del newnLwData.columns[key]

                del newLWUNCData.columns[key]
                del newRrsUNCData.columns[key]
                del newnLwUNCData.columns[key]
                if sensor == 'HYPER':
                    del newRhoHyper.columns[key]

        newESData.columnsToDataset()
        newLIData.columnsToDataset()
        newLTData.columnsToDataset()
        newLWData.columnsToDataset()
        newRrsUncorrData.columnsToDataset()
        newRrsData.columnsToDataset()
        newnLwData.columnsToDataset()

        newESDataMedian.columnsToDataset()
        newLIDataMedian.columnsToDataset()
        newLTDataMedian.columnsToDataset()

        newESSTDData.columnsToDataset()
        newLISTDData.columnsToDataset()
        newLTSTDData.columnsToDataset()
        newLWSTDData.columnsToDataset()
        newRrsSTDData.columnsToDataset()
        newnLwSTDData.columnsToDataset()
        newESUNCData.columnsToDataset()
        newLIUNCData.columnsToDataset()
        newLTUNCData.columnsToDataset()
        newLWUNCData.columnsToDataset()
        newRrsUNCData.columnsToDataset()
        newnLwUNCData.columnsToDataset()

        # TODO: add f0 unc to breakdown? - Ashley
        if xBreakdownUNC is not None:
            for key in BDData['ES']:
                BDData['ES'][key].columnsToDataset()
            for key in BDData['LI']:
                BDData['LI'][key].columnsToDataset()
                BDData['LT'][key].columnsToDataset()
            for key in BDData['LW']:
                BDData['LW'][key].columnsToDataset()
            for key in BDData['nLw']:
                BDData['nLw'][key].columnsToDataset()
            for key in BDData['Rrs']:
                BDData['Rrs'][key].columnsToDataset()

        if xBreakdownCORR is not None:
            for key in BDCorr['ES']:
                BDCorr['ES'][key].columnsToDataset()
            for key in BDCorr['LI']:
                BDCorr['LI'][key].columnsToDataset()
                BDCorr['LT'][key].columnsToDataset()
            for key in BDCorr['LW']:
                BDCorr['LW'][key].columnsToDataset()
            for key in BDCorr['Rrs']:
                BDCorr['Rrs'][key].columnsToDataset()

        if sensor == 'HYPER':
            newRhoHyper.columnsToDataset()
            newRhoUNCHyper.columnsToDataset()
            newRrsUncorrData.columnsToDataset()


    @staticmethod
    def spectralIrradiance(node, sensor, timeObj, xSlice, F0, F0_unc, waveSubset, xUNC):
        """
        Same as spectralReflectance, but only applies to irradiance data. Use for Es only processing
        """
        esXSlice = xSlice['es']  # mean
        esXmedian = xSlice['esMedian']
        esXRemaining = xSlice['esRemaining']
        esXstd = xSlice['esSTD']

        dateTime = timeObj['dateTime']
        dateTag = timeObj['dateTag']
        timeTag = timeObj['timeTag']

        # Root (new/output) groups:
        newIrradianceGroup = node.getGroup("IRRADIANCE")

        # If this is the first ensemble spectrum, set up the new datasets
        if not f'ES_{sensor}' in newIrradianceGroup.datasets:
            newESData = newIrradianceGroup.addDataset(f"ES_{sensor}")
            newESDataMedian = newIrradianceGroup.addDataset(f"ES_{sensor}_median")
            newESSTDData = newIrradianceGroup.addDataset(f"ES_{sensor}_sd")
            newESUNCData = newIrradianceGroup.addDataset(f"ES_{sensor}_unc")
        else:
            newESData = newIrradianceGroup.getDataset(f"ES_{sensor}")
            newESDataMedian = newIrradianceGroup.getDataset(f"ES_{sensor}_median")
            newESSTDData = newIrradianceGroup.getDataset(f"ES_{sensor}_sd")
            newESUNCData = newIrradianceGroup.getDataset(f"ES_{sensor}_unc")

        # Add datetime stamps back onto ALL datasets associated with the current sensor
        # If this is the first spectrum, add date/time, otherwise append
        # Groups REFLECTANCE, IRRADIANCE, and RADIANCE are intiallized with empty datasets, but
        # ANCILLARY is not.
        if "Datetag" not in newESData.columns:
            for gp in node.groups:
                if gp.id == "ANCILLARY":  # Ancillary is already populated. The other groups only have empty (named) datasets
                    continue
                else:
                    for ds in gp.datasets:
                        if sensor in ds:  # Only add datetime stamps to the current sensor datasets
                            gp.datasets[ds].columns["Datetime"] = [dateTime]  # mean of the ensemble datetime stamp
                            gp.datasets[ds].columns["Datetag"] = [dateTag]
                            gp.datasets[ds].columns["Timetag2"] = [timeTag]
        else:
            for gp in node.groups:
                if gp.id == "ANCILLARY":
                    continue
                else:
                    for ds in gp.datasets:
                        if sensor in ds:
                            gp.datasets[ds].columns["Datetime"].append(dateTime)
                            gp.datasets[ds].columns["Datetag"].append(dateTag)
                            gp.datasets[ds].columns["Timetag2"].append(timeTag)

        # Organise Uncertainty into wavebands
        esUNC = {}

        # Only Factory - Trios has no uncertainty here
        if (ConfigFile.settings['fL1bCal'] >= 2 or ConfigFile.settings['SensorType'].lower() == 'seabird'):
            esUNC = xUNC[f'esUNC_{sensor}']  # should already be convolved to hyperspec
        else:
            # factory case
            for wvl in waveSubset:
                k = str(wvl)
                if any([wvl == float(x) for x in esXSlice]):
                    esUNC[k] = 0

        for wvl in waveSubset:
            k = str(wvl)
            if any([wvl == float(x) for x in esXSlice]):
                # Initialize the new dataset if this is the first slice
                if k not in newESData.columns:
                    newESData.columns[k] = []
                    newESDataMedian.columns[k] = []
                    newESSTDData.columns[k] = []
                    newESUNCData.columns[k] = []

                # At this waveband (k); still using complete wavelength set
                es = esXSlice[k][0]  # Always the zeroth element; i.e. XSlice data are independent of past slices and node
                # esRemaining = np.asarray(esXRemaining[k])  # array of remaining ensemble values in this band
                # f0 = F0[k]
                # f0UNC = F0_unc[k]

                esMedian = esXmedian[k][0]
                esSTD = esXstd[k][0]

                newESData.columns[k].append(es)
                newESSTDData.columns[k].append(esSTD)
                newESDataMedian.columns[k].append(esMedian)

                # Only populate valid wavelengths. Mark others for deletion
                if (ConfigFile.settings['fL1bCal'] == 1 and
                        ConfigFile.settings["SensorType"].lower() in ["trios", "trios es only"]):
                    # Specifique case for Factory-Trios
                    newESUNCData.columns[k].append(esUNC[k])
                else:
                    newESUNCData.columns[k].append(esUNC[k][0])

        newESData.columnsToDataset()
        newESDataMedian.columnsToDataset()
        newESSTDData.columnsToDataset()
        newESUNCData.columnsToDataset()


    # @staticmethod
    # def filterData(group, badTimes, sensor = None):
    #     ''' Delete flagged records. Sensor is only specified to get the timestamp.
    #         All data in the group (including satellite sensors) will be deleted. '''

    #     logging.writeLogFileAndPrint(f'Remove {group.id} Data')
    #     timeStamp = None
    #     if sensor is None:
    #         if group.id == "ANCILLARY":
    #             timeStamp = group.getDataset("LATITUDE").data["Datetime"]
    #         if group.id == "IRRADIANCE":
    #             timeStamp = group.getDataset("ES").data["Datetime"]
    #         if group.id == "RADIANCE":
    #             timeStamp = group.getDataset("LI").data["Datetime"]
    #         if group.id == "SIXS_MODEL":
    #             timeStamp = group.getDataset("direct_ratio").data["Datetime"]
    #     else:
    #         if group.id == "IRRADIANCE":
    #             timeStamp = group.getDataset(f"ES_{sensor}").data["Datetime"]
    #         if group.id == "RADIANCE":
    #             timeStamp = group.getDataset(f"LI_{sensor}").data["Datetime"]
    #         if group.id == "REFLECTANCE":
    #             timeStamp = group.getDataset(f"Rrs_{sensor}").data["Datetime"]

    #     startLength = len(timeStamp)
    #     logging.writeLogFileAndPrint(f'   Length of dataset prior to removal {startLength} long')

    #     # Delete the records in badTime ranges from each dataset in the group
    #     finalCount = 0
    #     originalLength = len(timeStamp)
    #     for dateTime in badTimes:
    #         # Need to reinitialize for each loop
    #         startLength = len(timeStamp)
    #         newTimeStamp = []

    #         # logging.writeLogFileAndPrint(f'Eliminate data between: {dateTime}'

    #         start = dateTime[0]
    #         stop = dateTime[1]

    #         if startLength > 0:
    #             rowsToDelete = []
    #             for i in range(startLength):
    #                 if start <= timeStamp[i] and stop >= timeStamp[i]:
    #                     try:
    #                         rowsToDelete.append(i)
    #                         finalCount += 1
    #                     except Exception as err:
    #                         print(err)
    #                 else:
    #                     newTimeStamp.append(timeStamp[i])
    #             group.datasetDeleteRow(rowsToDelete)
    #         else:
    #             logging.writeLogFileAndPrint('Data group is empty. Continuing.')
    #         timeStamp = newTimeStamp.copy()

    #     if len(badTimes) == 0:
    #         startLength = 1 # avoids div by zero below when finalCount is 0

    #     for ds in group.datasets:
    #         # if ds != "STATION":
    #         try:
    #             group.datasets[ds].datasetToColumns()
    #         except Exception as err:
    #             print(err)

    #     logging.writeLogFileAndPrint(f'   Length of dataset after removal {originalLength-finalCount} long: {round(100*finalCount/originalLength)}% removed')
    #     return finalCount/originalLength


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
    def negReflectance(reflGroup, field, VIS = None):
        ''' Perform negative reflectance spectra checking for all ensembles '''
        # Run for entire file, not just one ensemble
        if VIS is None:
            VIS = [400,700]

        reflData = reflGroup.getDataset(field)
        # reflData.datasetToColumns()
        reflColumns = reflData.columns
        reflDate = reflColumns.pop('Datetag')
        reflTime = reflColumns.pop('Timetag2')
        # reflColumns.pop('Datetag')
        # reflColumns.pop('Timetag2')
        timeStamp = reflColumns.pop('Datetime')

        badTimes = []
        # Iterate over ensembles
        for indx, timeTag in enumerate(timeStamp):
            # If any spectra in the vis are negative, delete the whole spectrum
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
                logging.writeLogFileAndPrint(f'Ensemble {indx} of {field} flagged for negative Rrs')

            # Set negatives to 0
            NIR = [VIS[-1] + 1, max(wavelengths)]
            UV = [min(wavelengths),VIS[0]-1]
            for wave in reflColumns:
                if ((float(wave) >= UV[0] and float(wave) < UV[1]) or \
                            (float(wave) >= NIR[0] and float(wave) <= NIR[1])) and \
                            reflColumns[wave][indx] < 0:
                    reflColumns[wave][indx] = 0

        badTimes = np.unique(badTimes)
        badTimes = np.rot90(np.matlib.repmat(badTimes,2,1), 3) # Duplicates each element to a list of two elements (start, stop)
        logging.writeLogFileAndPrint(f'{len(np.unique(badTimes))/len(timeStamp)*100:.1f}% of {field} spectra flagged')

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
    def columnToSlice(columns, start, end):
        ''' Take a slice of a dataset stored in columns '''

        # Each column is a time series either at a waveband for radiometer columns, or various grouped datasets for ancillary
        # Start and end are defined by the interval established in the Config (they are indexes)
        newSlice = collections.OrderedDict()
        for col in columns:
            if start == end:
                newSlice[col] = columns[col][start:end+1] # otherwise you get nada []
            else:
                newSlice[col] = columns[col][start:end] # up to not including end...next slice will pick it up
        return newSlice


    @staticmethod
    def sliceAveHyper(y, hyperSlice):
        ''' Take the slice mean of the lowest X% of hyperspectral slices '''
        xSlice = collections.OrderedDict()
        xSliceRemaining = collections.OrderedDict()
        xMedian = collections.OrderedDict()
        hasNan = False
        # Ignore runtime warnings when array is all NaNs
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            for k in hyperSlice: # each k is a time series at a waveband.
                v = hyperSlice[k] if y is None else [hyperSlice[k][i] for i in y]  # selects the lowest X% within the ensemble...
                mean = np.nanmean(v) # ... and averages them
                median = np.nanmedian(v) # ... and the median spectrum
                xSlice[k] = [mean]
                xMedian[k] = [median]
                if np.isnan(mean):
                    hasNan = True

                # Retain remaining spectra for use in calculating Rrs_sd
                xSliceRemaining[k] = v

        return hasNan, xSlice, xMedian, xSliceRemaining


    @staticmethod
    def sliceAveOther(node, start, end, y, ancGroup, sixSGroup):
        ''' Take the slice AND the mean averages of ancillary and 6S data with X% '''        

        def _sliceAveOther(node, start, end, y, group):
            if node.getGroup(group.id):
                newGroup = node.getGroup(group.id)
            else:
                newGroup = node.addGroup(group.id)

            for dsID in group.datasets:
                if newGroup.getDataset(dsID):
                    newDS = newGroup.getDataset(dsID)
                else:
                    newDS = newGroup.addDataset(dsID)
                ds = group.getDataset(dsID)

                # Set relAz to abs(relAz) prior to averaging
                if dsID == 'REL_AZ':
                    ds.columns['REL_AZ'] = np.abs(ds.columns['REL_AZ']).tolist()

                ds.datasetToColumns()
                dsSlice = ProcessL2.columnToSlice(ds.columns,start, end)
                dsXSlice, date, sliceTime, subDScol = None, None, None, None

                for subDScol in dsSlice: # each dataset contains columns (including date, time, data, and possibly flags)
                    if subDScol == 'Datetime':
                        timeStamp = dsSlice[subDScol]
                        # Stores the mean datetime by converting to (and back from) epoch second
                        if len(timeStamp) > 0:
                            epoch = datetime.datetime(1970, 1, 1,tzinfo=datetime.timezone.utc) #Unix zero hour
                            tsSeconds = []
                            for dt in timeStamp:
                                tsSeconds.append((dt-epoch).total_seconds())
                            meanSec = np.mean(tsSeconds)
                            dateTime = datetime.datetime.utcfromtimestamp(meanSec).replace(tzinfo=datetime.timezone.utc)
                            date = dating.datetime2DateTag(dateTime)
                            sliceTime = dating.datetime2TimeTag2(dateTime)
                    if subDScol not in ('Datetime', 'Datetag', 'Timetag2'):
                        v = [dsSlice[subDScol][i] for i in y] # y is an array of indexes for the lowest X%

                        if dsXSlice is None:
                            dsXSlice = collections.OrderedDict()
                            dsXSlice['Datetag'] = [date]
                            dsXSlice['Timetag2'] = [sliceTime]
                            dsXSlice['Datetime'] = [dateTime]

                        if subDScol not in dsXSlice:
                            dsXSlice[subDScol] = []
                        if (subDScol.endswith('FLAG')) or (subDScol.endswith('STATION')):
                            # Find the most frequest element
                            dsXSlice[subDScol].append(comparing.mostFrequent(v))
                        else:
                            # Otherwise take a nanmean of the slice
                            with warnings.catch_warnings():
                                warnings.simplefilter("ignore", category=RuntimeWarning)
                                dsXSlice[subDScol].append(np.nanmean(v)) # Warns of empty when empty...

                # Just test a sample column to see if it needs adding or appending
                if subDScol not in newDS.columns:
                    newDS.columns = dsXSlice
                else:
                    for item in newDS.columns:
                        newDS.columns[item] = np.append(newDS.columns[item], dsXSlice[item])

                newDS.columns.move_to_end('Timetag2', last=False)
                newDS.columns.move_to_end('Datetag', last=False)
                newDS.columns.move_to_end('Datetime', last=False)
                newDS.columnsToDataset()

        _sliceAveOther(node, start, end, y, ancGroup)
        _sliceAveOther(node, start, end, y, sixSGroup)

    @staticmethod
    def ensemblesReflectance(node, sasGroup, refGroup, ancGroup, uncGroup,
                             esRawGroup, liRawGroup, ltRawGroup, sixSGroup, start, end):
        '''Calculate the lowest X% Lt(780). Check for Nans in Li, Lt, Es, or wind. Send out for
        meteorological quality flags. Perform glint corrections. Calculate the Rrs. Correct for NIR
        residuals.'''

        # %% Get dataset
        if ConfigFile.settings["SensorType"].lower() == "trios es only":
            # Only Irradiance
            groups = {'ES': refGroup}
            es_only = True
        else:
            # Radiances and Irradiance
            groups = {'ES': refGroup, 'LI': sasGroup, 'LT': sasGroup}
            es_only = False
        columns = {}
        for k, group in groups.items():
            d = group.getDataset(k)
            d.datasetToColumns()
            columns[k] = d.columns

        # %% Slice Data
        data_slice = {k: ProcessL2.columnToSlice(d, start, end) for k, d in columns.items()}

        # %% Check Length of Slice
        es_start_datetime, es_stop_datetime = data_slice['ES']['Datetime'][0], data_slice['ES']['Datetime'][-1]
        if (es_stop_datetime - es_start_datetime) < datetime.timedelta(seconds=60):
            logging.writeLogFileAndPrint("ProcessL2.ensemblesReflectance ensemble is less than 1 minute. Skipping.")
            return False

        # TODO Check why SIXS code used to be here but data manipulation is not used later on, hence dropped

        # %% Get active raw groups (based on data available in groups, required to get std)
        map_raw_groups = {'ES': esRawGroup, 'LI': liRawGroup, 'LT': ltRawGroup}
        if ConfigFile.settings['SensorType'].lower() == "seabird":
            raw_groups = {k: {t: map_raw_groups[k][t] for t in ['LIGHT', 'DARK']} for k in groups}
            raw_slices = {k: {t: {'datetime': grp[t].datasets['DATETIME'].data[start:end],
                                  'data': ProcessL2.columnToSlice(grp[t].datasets[k].columns, start, end)}
                              for t in ['LIGHT', 'DARK']} for k, grp in raw_groups.items()}
        else:
            raw_groups = {k: map_raw_groups[k] for k in groups}
            raw_slices = {k: {'data': ProcessL2.columnToSlice(grp.datasets[k].columns, start, end)}
                          for k, grp in raw_groups.items()}

        # %% Get Configuration
        enable_percent_lt = float(ConfigFile.settings["bL2EnablePercentLt"])
        percent_lt = float(ConfigFile.settings["fL2PercentLt"])
        three_c_rho = int(ConfigFile.settings["bL23CRho"])
        zhang_rho = int(ConfigFile.settings["bL2Z17Rho"])
        if ConfigFile.settings["SensorType"].lower() == "dalec":
            sensor, sensor_type = Dalec(), 'Dalec'
        elif ConfigFile.settings["SensorType"].lower() in ["sorad", "trios", "trios es only"]:
            sensor, sensor_type = TriOS(), 'TriOS'
        elif ConfigFile.settings["SensorType"].lower() == "seabird":
            sensor, sensor_type = HyperOCR(), 'SeaBird'
        else:
            raise ValueError('Sensor type not supported.')
        # TODO check why Delete Datetime, Datetag, and Timetag2 from slices

        # %% Compute mean datetime of slice
        # Based on Es timestamp only
        timestamps = data_slice['ES']['Datetime']
        epoch = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
        mean_timestamp = np.mean(np.array(timestamps) - epoch).total_seconds()
        mean_datetime = datetime.datetime.fromtimestamp(mean_timestamp, tz=datetime.timezone.utc)
        timestamp_dict = {
            'dateTime': mean_datetime,
            'dateTag': dating.datetime2DateTag(mean_datetime),
            'timeTag': dating.datetime2TimeTag2(mean_datetime)
        }

        # %% Get standard deviation of slice (entire slice, not just the lowest X%)
        # Drop time info, for stats functions
        for k in data_slice.keys():
            del data_slice[k]['Datetime']
            del data_slice[k]['Datetag']
            del data_slice[k]['Timetag2']
        wavelengths = np.asarray(list(data_slice['ES'].keys()), dtype=float)
        if ConfigFile.settings["SensorType"].lower() != "dalec":
            stats = sensor.generateSensorStats(sensor_type, raw_groups, raw_slices, wavelengths)
        else:
            # NOTE: Temporary placeholder for DALEC stats.
            stats1,stats = {},{}
            for group in raw_groups:
                bandN = len(raw_groups[group].datasets[group].columns)
                reject = ['Datetime','Datetag','Timetag2']
                bands = [key for key in groups[group].datasets[group].columns if key not in reject]
                for dataset in ['ave_Light','ave_Dark','std_Light','std_Dark','std_Signal','perturbations']:
                    stats1[dataset] = np.ones(bandN)*np.nan
                for dataset in ['std_Signal_Interpolated']:
                    stats1[dataset] = {str(wl): np.ones(bandN)*np.nan for wl in bands}
                stats[group] = stats1
        if ConfigFile.settings["SensorType"].lower() == "seabird":
            raw_groups = {k: d['LIGHT'] for k, d in raw_groups.items()}
            for key, group in raw_groups.items():
                group.id = f'{key}_L1AQC'
        if not stats:
            logging.writeLogFileAndPrint("statistics not generated")
            return False
        slice_std = {k: {str(wl): [std_interp[0]*np.average(data_slice[k][wl])] for wl, std_interp in stats[k]['Signal_std_Interpolated'].items()}
                     for k, sliceData in data_slice.items()}  # standard deviation is relatvie to signal - i.e. in %
        # Use wavelengths rather than keys from stats as stats is rounding wavelength to one decimal
        # which is inconsistent with other places in the code.

        # %% Convolve to satellite bands
        convolve_to_satellite, satellite_bands = {}, {}
        if ConfigFile.settings['bL2WeightMODISA']:
            convolve_to_satellite['MODISA'] = lambda sliceData: Weight_RSR.processMODISBands(sliceData, sensor='A')
            satellite_bands['MODIS'] = Weight_RSR.MODISBands()
        if ConfigFile.settings['bL2WeightMODIST']:
            convolve_to_satellite['MODIST'] = lambda sliceData: Weight_RSR.processMODISBands(sliceData, sensor='T')
            satellite_bands['MODIS'] = Weight_RSR.MODISBands()
        if ConfigFile.settings['bL2WeightVIIRSN']:
            convolve_to_satellite['VIIRSN'] = lambda sliceData: Weight_RSR.processVIIRSBands(sliceData, sensor='N')
            satellite_bands['VIIRS'] = Weight_RSR.VIIRSBands()
        if ConfigFile.settings['bL2WeightVIIRSJ']:
            convolve_to_satellite['VIIRSJ'] = lambda sliceData: Weight_RSR.processVIIRSBands(sliceData, sensor='J')
            satellite_bands['VIIRS'] = Weight_RSR.VIIRSBands()
        if ConfigFile.settings['bL2WeightSentinel3A']:
            convolve_to_satellite['Sentinel3A'] = lambda sliceData: Weight_RSR.processSentinel3Bands(sliceData, sensor='A')
            satellite_bands['Sentinel3'] = Weight_RSR.Sentinel3Bands()
        if ConfigFile.settings['bL2WeightSentinel3B']:
            convolve_to_satellite['Sentinel3A'] = lambda sliceData: Weight_RSR.processSentinel3Bands(sliceData, sensor='B')
            satellite_bands['Sentinel3'] = Weight_RSR.Sentinel3Bands()

        satellite_slice = {satellite: {k: convolve_to_satellite[satellite](sliceData) for k, sliceData in data_slice.items()}
                                for satellite in convolve_to_satellite}
        satellite_slice_std = {satellite: {k: convolve_to_satellite[satellite](sliceData)
                                for k, sliceData in slice_std.items()}
                                for satellite in convolve_to_satellite}

        # %% Get index of N lowest Lt frames => selection
        if enable_percent_lt and es_only:
            logging.writeLogFileAndPrint("Percent LT is not supported for Trios ES only. Disabled feature.")
            enable_percent_lt = False
        elif enable_percent_lt and 'LT' not in data_slice:
            logging.writeLogFileAndPrint("Percent LT is not available. No LT data found.")
            enable_percent_lt = False

        if 'LT' in data_slice:
            nSpecStart = len(data_slice['LT'][list(data_slice['LT'].keys())[0]])
        else:
            nSpecStart = len(timestamps)
        y = np.arange(nSpecStart) # Default to all indexes, if no LT data or percent_lt is not enabled
        # TODO NH merge Replace y assignment above by strategy below
        # # If Percent Lt is turned off, this will average the whole slice, and if
        # # ensemble is off (set to 0), just the one spectrum will be used.
        # first_band = next(iter(ltSlice))
        # first_band_values = ltSlice[first_band]
        # y=list(range(0,len(first_band_values)))
        #
        if enable_percent_lt:
            # Calculates the lowest X% (based on Hooker & Morel 2003; Hooker et al. 2002; Zibordi et al. 2002, IOCCG Protocols)
            # X will depend on FOV and integration time of instrument. Hooker cites a rate of 2 Hz.
            # It remains unclear to me from Hooker 2002 whether the recommendation is to take the average of the ir/radiances
            # within the threshold and calculate Rrs, or to calculate the Rrs within the threshold, and then average, however IOCCG
            # Protocols pretty clearly state to average the ir/radiances first, then calculate the Rrs...as done here.
            nSpecEnd = round(nSpecStart * percent_lt / 100)
            # There are sometimes only a small number of spectra in the slice,
            #  so the percent Lt estimation becomes highly questionable and is overridden here.
            if nSpecStart <= 5 or nSpecEnd == 0:
                nSpecEnd = nSpecStart  # if only 5 or fewer records retained, use them all...
            if nSpecEnd > 1:
                lt780 = ProcessL2.interpolateColumn(data_slice['LT'], 780.0)
                index = np.argsort(lt780)
                y = index[:nSpecEnd]                
                logging.writeLogFileAndPrint(f"{nSpecEnd} spectra remaining in slice to average after filtering to lowest {percent_lt}%.")
            else:
                logging.writeLogFileAndPrint(f"{nSpecEnd} spectra remaining after filtering to lowest {percent_lt}%. ABORT ENSEMBLE.")
                return False
        else:
            nSpecEnd = nSpecStart

        # %% Append Ensemble Size
        for grp in node.groups:
            if grp.id not in ['REFLECTANCE', 'IRRADIANCE', 'RADIANCE']:
                continue
            if es_only and grp.id != 'IRRADIANCE':
                continue
            if 'Ensemble_N' not in grp.datasets:
                grp.addDataset('Ensemble_N')
                grp.datasets['Ensemble_N'].columns['N'] = []
            grp.datasets['Ensemble_N'].columns['N'].append(nSpecEnd)
            grp.datasets['Ensemble_N'].columnsToDataset()

        # %% Slice averaging
        slice_mean, slice_median, slice_remaining = {}, {}, {}
        for k, sliceData in data_slice.items():
            has_nan, slice_mean[k], slice_median[k], slice_remaining[k] = ProcessL2.sliceAveHyper(y, sliceData)
            if has_nan:
                logging.writeLogFileAndPrint("ProcessL2.ensemblesReflectance: Slice X% average error: Dataset all NaNs.")
                return False

        # %% Convolution of slice averages to satellite bands
        satellite_slice_mean, satellite_slice_median, satellite_slice_remaining = {}, {}, {}
        for satellite, data in satellite_slice.items():
            satellite_slice_mean[satellite], satellite_slice_median[satellite], satellite_slice_remaining[satellite] = {}, {}, {}
            for k, sliceData in data.items():
                has_nan, satellite_slice_mean[satellite][k], satellite_slice_median[satellite][k], \
                    satellite_slice_remaining[satellite][k] = ProcessL2.sliceAveHyper(y, sliceData)
                if has_nan:
                    logging.writeLogFileAndPrint("ProcessL2.ensemblesReflectance: Slice X% average error: Dataset all NaNs.")
                    return False

        # %% Ancillary slice averaging
        ProcessL2.sliceAveOther(node, start, end, y, ancGroup, sixSGroup)
        newAncGroup = node.getGroup("ANCILLARY")  # Just populated above
        newAncGroup.attributes['ANC_SOURCE_FLAGS'] = ['0: Undetermined, 1: Field, 2: Model, 3: Fallback']

        anc_slice = {}
        for param in ['WINDSPEED', 'SZA', 'SST', 'SALINITY', 'REL_AZ', 'AOD']:
            if param in newAncGroup.datasets:
                l = newAncGroup.getDataset(param).data[param][-1].copy()
                anc_slice[param] = l[0] if isinstance(l, list) else l
            else:
                if param == 'AOD' and not zhang_rho:
                    continue   # Optional if don't use Zhang Rho
                if param == 'SALINITY':
                    continue   # Optional
                if param == 'REL_AZ' and es_only:
                    continue   # Optional for ES only
                logging.writeLogFileAndPrint(f"ProcessL2.ensemblesReflectance: Required {param} data absent in Ancillary. Aborting.")
                return False

        # These are optional; in fact, there is no implementation of incorporating CLOUD or WAVEs into
        # any of the current Rho corrections yet (even though cloud IS passed to Zhang_Rho)
        for param in ['CLOUD', 'WAVE_HT', 'STATION']:  # TODO CHECK If need second loop or could skip the [-1] for optional parameters
            if "WAVE_HT" in newAncGroup.datasets:
                l = newAncGroup.getDataset(param).data[param].copy()
                anc_slice[param] = l[0] if isinstance(l, list) else l
            else:
                anc_slice[param] = None

        # %% Calculate rho_sky for the ensemble
        if es_only:
            rho_scalar, rho_vec, rho_unc = None, None, None
        else:
            rho_scalar, rho_vec, rho_unc, wavelengths = ProcessL2.calculate_rho_sky_for_ensemble(wavelengths.tolist(), slice_mean, anc_slice)

        # %% Get TSIS-1 and convolve to satellite bands
        # NOTE: TSIS uncertainties reported as 1-sigma
        F0_hyper, F0_unc, F0_raw, F0_unc_raw, wv_raw = F0ing.TSIS_1(timestamp_dict['dateTag'], wavelengths.tolist())

        # Recycling _raw in TSIS_1 calls below prevents the dataset having to be reread
        if F0_hyper is None:
            logging.writeLogFileAndPrint("ProcessL2.ensemblesReflectance: No hyperspectral TSIS-1 F0. Aborting.")
            return False

        satellite_f0, satellite_f0_unc = {}, {}
        satellite_bands_subset = {}
        for sat, bands in satellite_bands.items():
            # Convolve TSIS-1 F0 to satellite bands
            satellite_f0[sat], satellite_f0_unc[sat] = F0ing.TSIS_1(timestamp_dict['dateTag'], bands, F0_raw, F0_unc_raw, wv_raw)[0:2]
            # Get bands for Zhang models
            b = np.array(bands)
            satellite_bands_subset[sat] = b[(350 <= b) & (b <= 1000)].tolist()

        # %% Format data and Propagate Uncertainties
        x_slice = {
            **{k.lower(): v for k, v in slice_mean.items()},
            **{k.lower() + 'Median': v for k, v in slice_median.items()},
            **{k.lower() + 'STD': {
                ave[0]: [std[0]*ave[1][0]] for std, ave in zip(v['Signal_std_Interpolated'].values(), slice_mean[k].items())} for k, v in stats.items()
                },  # changed to convert relative numpy array to (ir)rad signal standard deviation as dict
            **{k.lower() + 'STD_RAW': {
                wvl: [std] for std, wvl in zip(v['Signal_std'], stats[k]['Signal_noise'].keys())} for k, v in stats.items()
                },  # this is relative and not in DN
            **{k.lower() + 'Remaining': v for k, v in slice_remaining.items()},
        }
        
        x_unc, x_breakdown_unc, x_breakdown_corr = None, None, None
        tic = time.process_time()
        if ConfigFile.settings["fL1bCal"] <= 2:  # Factory Calibration or FRM-Class Specific
            l1b_unc, x_breakdown_unc = sensor.ClassBased(node, uncGroup, stats)
            if l1b_unc:
                x_slice.update(l1b_unc)
                # convert uncertainties back into absolute form using the signals recorded from ProcessL2
                for k, v in slice_mean.items():
                    x_slice[k.lower() + 'Unc'] = {
                        u[0]: [u[1][0] * np.abs(s[0])] for u, s in
                        zip(x_slice[k.lower() + 'Unc'].items(), v.values())
                    }
                    x_breakdown_unc[k.upper()] = {
                        u[0]: u[1] * np.abs(s[0]) for s, u in 
                        zip(v.values(), x_breakdown_unc[k.upper()].items())  # keys of x_breakdown_unc represent error sources
                    }
                if es_only:
                    x_unc = sensor.ClassBasedL2ESOnly(wavelengths.tolist(), x_slice)
                    l2_bd = {}
                else:
                    from Source.PIU.PIUDataStore import PIUDataStore
                    pds = PIUDataStore(node, uncGroup)
                    
                    x_unc, l2_bd = sensor.ClassBasedL2(node, uncGroup, pds, stats, rho_scalar, rho_vec, rho_unc, F0_hyper, F0_unc, wavelengths.tolist(), x_slice)
                x_breakdown_unc.update(l2_bd)
            elif not(ConfigFile.settings['SensorType'].lower() in ["dalec", "trios", "trios es only"] and (ConfigFile.settings["fL1bCal"] == 1)):
                logging.writeLogFileAndPrint(f"ProcessL2.ensemblesReflectance: Instrument uncertainty processing failed. Aborting.")
                return False
        elif ConfigFile.settings["fL1bCal"] == 3:  # FRM-Sensor Specific
            from Source.PIU.PIUDataStore import PIUDataStore
            pds = PIUDataStore(node, uncGroup, raw_groups, raw_slices)
            
            l1b_unc, x_breakdown_corr, x_breakdown_unc = sensor.FRM(pds, stats, wavelengths)
            x_slice['f0'] = F0_hyper
            x_slice['f0_unc'] = F0_unc
            x_slice.update(l1b_unc)
            x_unc = sensor.FRML2(pds, rho_scalar, rho_vec, rho_unc, wavelengths, x_slice, x_breakdown_unc)
        logging.writeLogFileAndPrint(f"ProcessL2.ensemblesReflectance: Uncertainty Update Elapsed Time: {time.process_time() - tic:.1f} s")

        # Move uncertainties to x_unc and drop samples form x_slice
        if x_unc is not None:
            for k in list(x_slice.keys()):  # trick to del items while looping on the dict
                if "sample" in k.lower():
                    del x_slice[k]  # samples are no longer needed
                elif "unc" in k.lower():
                    x_unc[f"{k[0:2]}UNC_HYPER"] = x_slice.pop(k)  # transfer instrument uncs to x_unc

            # Extract uncertainties for convolving to satellite bands
            slice_unc = {k: v for k, v in x_unc.items() if k.endswith('UNC_HYPER')}
        else:
            slice_unc = None

        # %% Populate relevant fields in node
        if es_only:
            ProcessL2.spectralIrradiance(node, 'HYPER', timestamp_dict, x_slice, F0_hyper, F0_unc, wavelengths, x_unc)
        else:
            ProcessL2.spectralReflectance(node, 'HYPER', timestamp_dict, x_slice, F0_hyper, F0_unc,
                                          rho_scalar, rho_vec, wavelengths, x_unc, x_breakdown_unc, x_breakdown_corr)

        # %% Apply NIR Correction to this ensemble
        # Perform near-infrared residual correction to remove additional atmospheric and glint contamination
        rrs_nir_cor, nLw_nir_corr = None, None
        if ConfigFile.settings["bL2PerformNIRCorrection"] and not es_only:
            rrs_nir_cor, nLw_nir_corr = ProcessL2.nirCorrection(node, 'HYPER', F0_hyper)

        # %% Convolve to satellite bands (this ensemble)
        for (sat, mean), median, remaining, std in zip(
                satellite_slice_mean.items(), satellite_slice_median.values(),
                satellite_slice_remaining.values(), satellite_slice_std.values()):
            sat_sensor = sat[:-1]
            x_slice = {}
            for k in mean.keys():
                x_slice[k.lower()] = mean[k]
                x_slice[k.lower() + 'Remaining'] = remaining[k]
                x_slice[k.lower() + 'Median'] = median[k]
                x_slice[k.lower() + 'STD'] = std[k]
            sat_rho_vec = None
            if zhang_rho or three_c_rho:
                sat_rho_vec = convolve_to_satellite[sat](rho_vec)
                sat_rho_vec = {key: value[0] for key, value in sat_rho_vec.items()}  # drop one level of list
            # NOTE: According to AR, this may not be a robust way of estimating convolved uncertainties.
            # He has implemented another way, but it is very slow due to multiple MC runs. Comment this out
            # for now, but a sensitivity analysis may show it to be okay.
            # NOTE: 1/2024 Why is this not commented out if the slow, more accurate way is now implemented?
            if slice_unc:
                for k, v in slice_unc.items():
                    x_unc[f'{k[:2]}UNC'] = convolve_to_satellite[sat](v)
            if es_only:
                ProcessL2.spectralIrradiance(node, sat, timestamp_dict, x_slice,
                                             satellite_f0[sat_sensor], satellite_f0_unc[sat_sensor],
                                             satellite_bands_subset[sat_sensor], x_unc)
            else:
                ProcessL2.spectralReflectance(node, sat, timestamp_dict, x_slice,
                                              satellite_f0[sat_sensor], satellite_f0_unc[sat_sensor], rho_scalar,
                                              sat_rho_vec, satellite_bands_subset[sat_sensor], x_unc)
                if ConfigFile.settings["bL2PerformNIRCorrection"]:
                    # Can't apply good NIR corrections at satellite bands,
                    # so use the correction factors from the hyperspectral instead.
                    ProcessL2.nirCorrectionSatellite(node, sat, rrs_nir_cor, nLw_nir_corr)
        return True


    @staticmethod
    def calculate_rho_sky_for_ensemble(wavelengths, data_slice_mean, anc_slice):
        # Get Configuration
        # rho_default = float(ConfigFile.settings["fL2RhoSky"]) # Not used
        rhoVector, rhoScalar, rhoUNC = None, None, None
        anc_slice['REL_AZ'] = np.abs(anc_slice['REL_AZ'])
        if int(ConfigFile.settings["bL23CRho"]):
            method = 'three_c_rho'
        elif int(ConfigFile.settings["bL2Z17Rho"]):
            method = 'zhang_rho'
        else:
            method = 'mobley_rho'

        # Calculate rho_sky for the ensemble
        if method == "three_c_rho":
            # TODO: Retrieve these values from ancillary info (is it actually necessary? TBD)
            # am: aerosol Mie parameter or similar, regulating amount of forward-to-total aerosol scattering...
            # ... eventually impacting the atmospheric transmittance
            am = 4
            rh = 60  # relative humidity, also impacting atm. transmittance
            pressure = 1013.25  # atm pressure, also impacting atm. transmittance
            weighting_option = 'Pitarch'

            # Sensor Nadir
            SVA = ConfigFile.settings['fL2SVA']

            rhoVector, rhoUNC = RhoCorrections.threeCCorr(
                data_slice_mean['LT'], data_slice_mean['LI'], data_slice_mean['ES'],
                anc_slice['SZA'], SVA, anc_slice['REL_AZ'], am, rh, pressure, weighting_option
            )

        elif method == "zhang_rho":
            # Zhang rho is based on Zhang et al. 2017 and calculates the wavelength-dependent rho vector
            # separated for sun and sky to include polarization factors.

            # Model limitations: AOD 0 - 0.5, Solar zenith 0-60 deg, Wavelength 350-1000 nm, SVA 30 or 40 degrees.

            # reduced number of draws because of how computationally intensive the Zhang method is
            rho_uncertainty_obj = Propagate(M=10, cores=1)

            # Need to limit the input for the model limitations. This will also mean cutting out Li, Lt, and Es
            # from non-valid wavebands.
            # NOTE: Need to update to 0.5 for new database
            for k, limit in [('AOD', 0.2), ('WINDSPEED', 15), ('SZA', 60)]:
                if anc_slice[k] > limit:
                    logging.writeLogFileAndPrint(
                        f'{k} = {anc_slice[k]:.3f}. Maximum {k}. Setting to {limit}. Expect larger, uncaptured errors.')
                    anc_slice[k] = limit
            if min(wavelengths) < 350 or max(wavelengths) > 1000:
                logging.writeLogFileAndPrint('Wavelengths extend beyond model limits. Truncating to 350 - 1000 nm.')
                wave_old = wavelengths.copy()
                wave_list = [(i, band) for i, band in enumerate(wave_old) if (band >= 350) and (band <= 1000)]
                wave_array = np.array(wave_list)
                # wavelength is now truncated to only valid wavebands for use in Zhang models
                wavelengths = wave_array[:, 1].tolist()

            SVA = ConfigFile.settings['fL2SVA']
            rhoVector, rhoUNC = RhoCorrections.ZhangCorr(anc_slice['WINDSPEED'], anc_slice['AOD'], anc_slice['CLOUD'],
                                                         anc_slice['SZA'], anc_slice['SST'], anc_slice['SALINITY'],
                                                         anc_slice['REL_AZ'],
                                                         SVA, wavelengths, rho_uncertainty_obj)
        elif method == "mobley_rho":
            # Full Mobley 1999 model from LUT
            rho_uncertainty_obj = Propagate(M=100, cores=1)  # Standard number of draws for reasonable uncertainty estimates
            if 'AOD' in anc_slice:
                rhoScalar, rhoUNC = RhoCorrections.M99Corr(anc_slice['WINDSPEED'], anc_slice['SZA'],
                                                           anc_slice['REL_AZ'],
                                                           rho_uncertainty_obj,
                                                           AOD=anc_slice['AOD'], cloud=anc_slice['CLOUD'],
                                                           wTemp=anc_slice['SST'],
                                                           sal=anc_slice['SALINITY'], waveBands=wavelengths)
            else:
                rhoScalar, rhoUNC = RhoCorrections.M99Corr(anc_slice['WINDSPEED'], anc_slice['SZA'],
                                                           anc_slice['REL_AZ'],
                                                           rho_uncertainty_obj)

        # Format output
        if rhoVector is not None:
            rhoVec = {}
            for i, k in enumerate(wavelengths):
                rhoVec[str(k)] = rhoVector[i]
        else:
            rhoVec = None

        return rhoScalar, rhoVec, rhoUNC, np.array(wavelengths)

    @staticmethod
    def stationsEnsemblesReflectance(node, root, station=None):
        ''' Extract stations if requested, then pass to ensemblesReflectance for ensemble
            averages, rho calcs, Rrs, Lwn, NIR correction, satellite convolution, OC Products.'''

        print("stationsEnsemblesReflectance")

        root_group_ids = [g.id for g in root.groups]

        # Create a third HDF for copying root without altering it
        rootCopy = HDFRoot()
        rootCopy.addGroup("ANCILLARY")
        rootCopy.addGroup("IRRADIANCE")
        if 'RADIANCE' in root_group_ids:
            rootCopy.addGroup("RADIANCE")
        rootCopy.addGroup('SIXS_MODEL')

        rootCopy.getGroup('ANCILLARY').copy(root.getGroup('ANCILLARY'))
        rootCopy.getGroup('IRRADIANCE').copy(root.getGroup('IRRADIANCE'))
        if 'RADIANCE' in root_group_ids:
            rootCopy.getGroup('RADIANCE').copy(root.getGroup('RADIANCE'))

        sixS_available = False
        for gp in root.groups:
            if gp.id == 'SIXS_MODEL':
                sixS_available = True
                rootCopy.getGroup('SIXS_MODEL').copy(root.getGroup('SIXS_MODEL'))
                break

        if ConfigFile.settings['SensorType'].lower() == 'seabird':
            rootCopy.addGroup("ES_DARK_L1AQC")
            rootCopy.addGroup("ES_LIGHT_L1AQC")
            rootCopy.addGroup("LI_DARK_L1AQC")
            rootCopy.addGroup("LI_LIGHT_L1AQC")
            rootCopy.addGroup("LT_DARK_L1AQC")
            rootCopy.addGroup("LT_LIGHT_L1AQC")
            rootCopy.getGroup('ES_LIGHT_L1AQC').copy(root.getGroup('ES_LIGHT_L1AQC'))
            rootCopy.getGroup('ES_DARK_L1AQC').copy(root.getGroup('ES_DARK_L1AQC'))
            rootCopy.getGroup('LI_LIGHT_L1AQC').copy(root.getGroup('LI_LIGHT_L1AQC'))
            rootCopy.getGroup('LI_DARK_L1AQC').copy(root.getGroup('LI_DARK_L1AQC'))
            rootCopy.getGroup('LT_LIGHT_L1AQC').copy(root.getGroup('LT_LIGHT_L1AQC'))
            rootCopy.getGroup('LT_DARK_L1AQC').copy(root.getGroup('LT_DARK_L1AQC'))

            esRawGroup = {"LIGHT": rootCopy.getGroup('ES_LIGHT_L1AQC'), "DARK": rootCopy.getGroup('ES_DARK_L1AQC')}
            liRawGroup = {"LIGHT": rootCopy.getGroup('LI_LIGHT_L1AQC'), "DARK": rootCopy.getGroup('LI_DARK_L1AQC')}
            ltRawGroup = {"LIGHT": rootCopy.getGroup('LT_LIGHT_L1AQC'), "DARK": rootCopy.getGroup('LT_DARK_L1AQC')}

            sasGroup = rootCopy.getGroup("RADIANCE")
        elif ConfigFile.settings["SensorType"].lower() in ["dalec", "sorad", "trios"]:
            rootCopy.addGroup("ES_L1AQC")
            rootCopy.addGroup("LI_L1AQC")
            rootCopy.addGroup("LT_L1AQC")
            rootCopy.getGroup('ES_L1AQC').copy(root.getGroup('ES_L1AQC'))
            rootCopy.getGroup('LI_L1AQC').copy(root.getGroup('LI_L1AQC'))
            rootCopy.getGroup('LT_L1AQC').copy(root.getGroup('LT_L1AQC'))

            esRawGroup = rootCopy.getGroup('ES_L1AQC')
            liRawGroup = rootCopy.getGroup('LI_L1AQC')
            ltRawGroup = rootCopy.getGroup('LT_L1AQC')

            sasGroup = rootCopy.getGroup("RADIANCE")
        elif ConfigFile.settings["SensorType"].lower() == "trios es only":
            rootCopy.addGroup("ES_L1AQC")
            rootCopy.getGroup('ES_L1AQC').copy(root.getGroup('ES_L1AQC'))
            esRawGroup = rootCopy.getGroup('ES_L1AQC')
            liRawGroup, ltRawGroup = None, None
            sasGroup = None

        # rootCopy will be manipulated in the making of node, but root will not
        referenceGroup = rootCopy.getGroup("IRRADIANCE")
        ancGroup = rootCopy.getGroup("ANCILLARY")
        if sixS_available:
            sixSGroup = rootCopy.getGroup("SIXS_MODEL")
        else:
            sixSGroup = None

        if ConfigFile.settings["fL1bCal"] >= 2 or ConfigFile.settings['SensorType'].lower() == 'seabird':
            #or ConfigFile.settings['SensorType'].lower() == 'dalec':
            rootCopy.addGroup("RAW_UNCERTAINTIES")
            rootCopy.getGroup('RAW_UNCERTAINTIES').copy(root.getGroup('RAW_UNCERTAINTIES'))
            uncGroup = rootCopy.getGroup("RAW_UNCERTAINTIES")
        # Only Factory-Trios has no unc
        else:
            uncGroup = None

        dating.rawDataAddDateTime(rootCopy) # For L1AQC data carried forward
        dating.rootAddDateTimeCol(rootCopy)

        ###############################################################################
        #
        # Stations
        #   Simplest approach is to run station extraction seperately from (i.e. in addition to)
        #   underway data. This means if station extraction is selected in the GUI, all non-station
        #   data will be discarded here prior to any further filtering or processing.

        if ConfigFile.settings["bL2Stations"]:
            logging.writeLogFileAndPrint("Extracting station data only. All other records will be discarded.")

            # If we are here, the station was already chosen in Controller
            try:
                stations = ancGroup.getDataset("STATION").columns["STATION"]
                dateTime = ancGroup.getDataset("STATION").columns["Datetime"]
            except Exception:
                logging.writeLogFileAndPrint("No station data found in ancGroup. Aborting.")
                return False

            badTimes = []
            start = False
            stop = False
            for index, stn in enumerate(stations):
                # print(f'index: {index}, station: {station}, datetime: {dateTime[index]}')
                # if np.isnan(station) and start == False:
                if (stn != station) and (start is False):
                    start = dateTime[index]
                # if not np.isnan(station) and not (start == False) and (stop == False):
                if not (stn!=station) and (start is not False) and (stop is False):
                    stop = dateTime[index-1]
                    badTimes.append([start, stop])
                    start = False
                    stop = False
                # End of file, no active station
                # if np.isnan(station) and not (start == False) and (index == len(stations)-1):
                if (stn != station) and not (start is False) and (index == len(stations)-1):
                    stop = dateTime[index]
                    badTimes.append([start, stop])

            if badTimes is not None and len(badTimes) != 0:
                print('Removing records...')
                check = filtering.filterDataL2(referenceGroup, badTimes)
                if check == 1.0:
                    logging.writeLogFileAndPrint("100% of irradiance data removed. Abort.")
                    return False
                if sasGroup is not None:
                    filtering.filterDataL2(sasGroup, badTimes)
                filtering.filterDataL2(ancGroup, badTimes)
                if sixS_available:
                    filtering.filterDataL2(sixSGroup, badTimes)

        #####################################################################
        #
        # Ensembles. Break up data into time intervals, and calculate averages and reflectances
        #
        esData = referenceGroup.getDataset("ES")
        esColumns = esData.columns
        timeStamp = esColumns["Datetime"]
        esLength = len(list(esColumns.values())[0])
        interval = float(ConfigFile.settings["fL2TimeInterval"])

        # interpolate Light/Dark data for Raw groups if HyperOCR data is being processed
        if ConfigFile.settings['SensorType'].lower() == "seabird":
            # in seabird case interpolate dark data to light timer before breaking into stations
            if not all([HyperOCRUtils.darkToLightTimer(esRawGroup, 'ES'),
                        HyperOCRUtils.darkToLightTimer(liRawGroup, 'LI'),
                        HyperOCRUtils.darkToLightTimer(ltRawGroup, 'LT')]):
                logging.writeLogFileAndPrint("failed to interpolate dark data to light data timer")
        if interval == 0:
            # Here, take the complete time series
            print("No time binning. This can take a moment.")
            progressBar = tqdm(total=esLength, unit_scale=True, unit_divisor=1)
            for i in range(0, esLength-1):
                progressBar.update(1)
                startEnsIndx = i
                stopEnsIndx = i+1

                if not ProcessL2.ensemblesReflectance(node, sasGroup, referenceGroup, ancGroup,
                                                    uncGroup, esRawGroup,liRawGroup, ltRawGroup,
                                                    sixSGroup, startEnsIndx, stopEnsIndx):
                    logging.writeLogFileAndPrint('ProcessL2.ensemblesReflectance unsliced failed. Abort.')
                    continue
        else:
            logging.writeLogFileAndPrint('Binning datasets to ensemble time interval.')

            # Iterate over the time ensembles
            startEnsIndx = 0
            stopEnsTime = timeStamp[0] + datetime.timedelta(0,interval)
            endFileTime = timeStamp[-1]
            EndOfFileFlag = False
            # stopEnsTime is theoretical based on interval
            if stopEnsTime > endFileTime:
                stopEnsTime = endFileTime
                EndOfFileFlag = True # In case the whole file is shorter than the selected interval

            for i in range(0, esLength):
                timei = timeStamp[i]
                if (timei > stopEnsTime) or EndOfFileFlag: # end of ensemble reached
                    if EndOfFileFlag:
                        stopEnsIndx = len(timeStamp)-1 # File shorter than interval; include all spectra
                        if not ProcessL2.ensemblesReflectance(node, sasGroup, referenceGroup, ancGroup,
                                                            uncGroup, esRawGroup,liRawGroup, ltRawGroup,
                                                            sixSGroup, startEnsIndx, stopEnsIndx):
                            logging.writeLogFileAndPrint('ProcessL2.ensemblesReflectance with slices failed. Continue.')
                            break # End of file reached. Safe to break

                        break # End of file reached. Safe to break
                    else:
                        stopEnsTime = timei + datetime.timedelta(0,interval) # increment for the next bin loop
                        stopEnsIndx = i # end of the slice is up to and not including...so -1 is not needed

                    if stopEnsTime > endFileTime:
                        stopEnsTime = endFileTime
                        EndOfFileFlag = True

                    if not ProcessL2.ensemblesReflectance(node, sasGroup, referenceGroup, ancGroup,
                                                            uncGroup, esRawGroup,liRawGroup, ltRawGroup,
                                                            sixSGroup, startEnsIndx, stopEnsIndx):
                        logging.writeLogFileAndPrint('ProcessL2.ensemblesReflectance with slices failed. Continue.')

                        startEnsIndx = i
                        continue # End of ensemble reached. Continue.
                    startEnsIndx = i

                    if EndOfFileFlag:
                        # No need to continue incrementing; all records captured in one ensemble
                        break

            # For the rare case where end of record is reached at, but not exceeding, stopEnsTime...
            if not EndOfFileFlag:
                stopEnsIndx = i+1 # i is the index of end of record; plus one to include i due to -1 list slicing
                if not ProcessL2.ensemblesReflectance(node, sasGroup, referenceGroup, ancGroup,
                                                            uncGroup, esRawGroup,liRawGroup, ltRawGroup,
                                                            sixSGroup, startEnsIndx, stopEnsIndx):
                    logging.writeLogFileAndPrint('ProcessL2.ensemblesReflectance ender clause failed.')

        #####################################
        #
        # Reflectance calculations complete
        #

        # Filter reflectances for negative ensemble spectra
        # NOTE: Any spectrum that has any negative values between
        #  400 - 700ish (hard-coded below), remove the entire spectrum. Otherwise,
        # set negative bands to 0.

        if ConfigFile.settings["bL2NegativeSpec"] and ConfigFile.settings["SensorType"].lower() == "trios es only":
            logging.writeLogFileAndPrint("Filtering reflectance spectra for negative values"
                                           " is not supported for Trios ES only. Disabled feature.")
        elif ConfigFile.settings["bL2NegativeSpec"]:
            fRange = [400, 680]
            logging.writeLogFileAndPrint("Filtering reflectance spectra for negative values.")
            # newReflectanceGroup = node.groups[0]
            newReflectanceGroup = node.getGroup("REFLECTANCE")
            if not newReflectanceGroup.datasets:
                logging.writeLogFileAndPrint("Reflectance group is empty. Aborting.")
                return False

            badTimes1 = ProcessL2.negReflectance(newReflectanceGroup, 'Rrs_HYPER', VIS = fRange)
            badTimes2 = ProcessL2.negReflectance(newReflectanceGroup, 'nLw_HYPER', VIS = fRange)

            badTimes = None
            if badTimes1 is not None and badTimes2 is not None:
                badTimes = np.append(badTimes1,badTimes2, axis=0)
            elif badTimes1 is not None:
                badTimes = badTimes1
            elif badTimes2 is not None:
                badTimes = badTimes2

            if badTimes is not None:
                print('Removing records...')

                # Even though HYPER is specified here, ALL data at badTimes in the group,
                # including satellite data, will be removed.
                check = filtering.filterDataL2(newReflectanceGroup, badTimes, sensor = "HYPER")
                if check > 0.99:
                    logging.writeLogFileAndPrint("Too few spectra remaining. Abort.")
                    return False
                filtering.filterDataL2(node.getGroup("IRRADIANCE"), badTimes, sensor = "HYPER")
                filtering.filterDataL2(node.getGroup("RADIANCE"), badTimes, sensor = "HYPER")
                filtering.filterDataL2(node.getGroup("ANCILLARY"), badTimes)
                if sixS_available:
                    filtering.filterDataL2(node.getGroup("SIXS_MODEL"), badTimes)

        return True

    @staticmethod
    def processL2(root,station=None):
        '''Calculates Rrs and nLw after quality checks and filtering, glint removal, residual
            subtraction. Weights for satellite bands, and outputs plots and SeaBASS datasets'''

        root_group_ids = [g.id for g in root.groups]

        # Root is the input from L1BQC, node is the output
        # Root should not be impacted by data reduction in node...
        node = HDFRoot()
        node.addGroup("ANCILLARY")
        if 'RADIANCE' in root_group_ids:
            node.addGroup("REFLECTANCE")
        node.addGroup("IRRADIANCE")
        if 'RADIANCE' in root_group_ids:
            node.addGroup("RADIANCE")
        node.addGroup("SIXS_MODEL")
        node.copyAttributes(root)
        node.attributes["PROCESSING_LEVEL"] = "2"
        # Remaining attributes managed below...

        # Copy attributes from root and for completeness, flip datasets into columns in all groups
        for grp in root.groups:
            for gp in node.groups:
                if gp.id == grp.id:
                    gp.copyAttributes(grp)
            for ds in grp.datasets:
                grp.datasets[ds].datasetToColumns()

            # Carry over L1AQC data for use in uncertainty budgets
            if grp.id.endswith('_L1AQC'): #or grp.id.startswith('SIXS_MODEL'):
                newGrp = node.addGroup(grp.id)
                newGrp.copy(grp)
                for ds in newGrp.datasets:
                    newGrp.datasets[ds].datasetToColumns()

        # Process stations, ensembles to reflectances, OC prods, etc.
        if not ProcessL2.stationsEnsemblesReflectance(node, root,station):
            return None

        # Reflectance
        gp = node.getGroup("REFLECTANCE")
        if gp:
            gp.attributes["Rrs_UNITS"] = "1/sr"
            gp.attributes["nLw_UNITS"] = "uW/cm^2/nm/sr"
            if ConfigFile.settings['bL23CRho']:
                gp.attributes['GLINT_CORR'] = 'Groetsch et al. 2017'
            if ConfigFile.settings['bL2Z17Rho']:
                gp.attributes['GLINT_CORR'] = 'Zhang et al. 2017'
            if ConfigFile.settings['bL2M99Rho']:
                gp.attributes['GLINT_CORR'] = 'Mobley 1999'
            if ConfigFile.settings['bL2PerformNIRCorrection']:
                if ConfigFile.settings['bL2SimpleNIRCorrection']:
                    gp.attributes['NIR_RESID_CORR'] = 'Mueller and Austin 1995'
                if ConfigFile.settings['bL2SimSpecNIRCorrection']:
                    gp.attributes['NIR_RESID_CORR'] = 'Ruddick et al. 2005/2006'
            if ConfigFile.settings['bL2NegativeSpec']:
                gp.attributes['NEGATIVE_VALUE_FILTER'] = 'ON'

        # Stations and Ensembles
        if ConfigFile.settings['bL2Stations']:
            node.attributes['STATION_EXTRACTION'] = 'ON'
        node.attributes['ENSEMBLE_DURATION'] = str(ConfigFile.settings['fL2TimeInterval']) + ' sec'

        # Check to insure at least some data survived quality checks
        if (ConfigFile.settings["SensorType"].lower() == "trios es only" and
                ('ES_HYPER' not in node.getGroup("IRRADIANCE").datasets or
                 node.getGroup("IRRADIANCE").getDataset("ES_HYPER").data is None)):
            logging.writeLogFileAndPrint("All irradiance data appear to have been eliminated from the file. Aborting.")
            return None
        if ConfigFile.settings["SensorType"].lower() != "trios es only" and node.getGroup("REFLECTANCE").getDataset("Rrs_HYPER").data is None:
            logging.writeLogFileAndPrint("All reflectance data appear to have been eliminated from the file. Aborting.")
            return None

        # If requested, proceed to calculation of derived geophysical and
        # inherent optical properties
        totalProds = sum(list(ConfigFile.products.values()))
        if totalProds > 0:
            if ConfigFile.settings["SensorType"].lower() == "trios es only":
                logging.writeLogFileAndPrint("Calculating derived geophysical and inherent optical properties "
                                               "is not supported for Trios ES only. Skipping.")
            else:
                ProcessL2OCproducts.procProds(node)

        # If requested, process BRDF corrections to Rrs and nLw
        if ConfigFile.settings["SensorType"].lower() == "trios es only" and ConfigFile.settings["bL2BRDF"]:
            logging.writeLogFileAndPrint("Calculating derived geophysical and inherent optical properties "
                                           "is not supported for Trios ES only. Skipping.")
        elif ConfigFile.settings["bL2BRDF"]:
            if ConfigFile.settings['bL2BRDF_fQ']:
                logging.writeLogFileAndPrint("Applying iterative Morel et al. 2002 BRDF correction to Rrs and nLw")
                ProcessL2BRDF.procBRDF(node, BRDF_option='M02')
                # brdf_unc = node.getGroup("REFLECTANCE").getDataset("Rrs_HYPER_unc_M02").columns

            if ConfigFile.settings['bL2BRDF_IOP']:
                logging.writeLogFileAndPrint("Applying Lee et al. 2011 BRDF correction to Rrs and nLw")
                ProcessL2BRDF.procBRDF(node, BRDF_option='L11')
                # brdf_unc = node.getGroup("REFLECTANCE").getDataset("Rrs_HYPER_unc_L11").columns

            if ConfigFile.settings['bL2BRDF_O25']:
                logging.writeLogFileAndPrint("Applying Pitarch et al. 2025 BRDF correction to Rrs and nLw")
                ProcessL2BRDF.procBRDF(node, BRDF_option='O25')
                # brdf_unc = node.getGroup("REFLECTANCE").getDataset("Rrs_HYPER_unc_O25").columns
            
            # BD_ds = node.getGroup("BREAKDOWN").addDataset("BRDF")
            # BD_ds.columns['BRDF'] = brdf_unc

        # Strip out L1AQC data
        for gp in reversed(node.groups):
            if gp.id.endswith('_L1AQC'):
                node.removeGroup(gp)

        # In the case of TriOS Factory, strip out uncertainty datasets
        if (ConfigFile.settings["SensorType"].lower() in ["dalec", "sorad", "trios", "trios es only"] and
                ConfigFile.settings['fL1bCal'] == 1):
            for gp in node.groups:
                if gp.id in ('IRRADIANCE', 'RADIANCE', 'REFLECTANCE'):
                    removeList = []
                    for dsName in reversed(gp.datasets):
                        if dsName.endswith('_unc'):
                            removeList.append(dsName)
                    for dsName in removeList:
                        gp.removeDataset(dsName)

        # NOTE: Unclear why this had been done. _median (not applicable to Lw or Rrs) refers to median of the slice, whereas no suffix is the mean.
        #   Chaning _median to _uncorr makes little sense...
        # # Change _median nomiclature to _uncorr
        # for gp in node.groups:
        #     if gp.id in ('IRRADIANCE', 'RADIANCE', 'REFLECTANCE'):
        #         changeList = []
        #         for dsName in gp.datasets:
        #             if dsName.endswith('_median'):
        #                 changeList.append(dsName)
        #         for dsName in changeList:
        #             gp.datasets[dsName].changeDatasetName(gp,dsName,dsName.replace('_median','_uncorr'))


        # Now strip datetimes from all datasets
        for gp in node.groups:
            for dsName in gp.datasets:
                ds = gp.datasets[dsName]
                if "Datetime" in ds.columns:
                    ds.columns.pop("Datetime")
                ds.columnsToDataset()

        now = datetime.datetime.now()
        timestr = now.strftime("%d-%b-%Y %H:%M:%S")
        node.attributes["FILE_CREATION_TIME"] = timestr

        return node
