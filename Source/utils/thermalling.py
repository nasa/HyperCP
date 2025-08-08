'''################################# THERMAL CORRECTION & UNCERTAINTY ORIENTED #################################'''

import numpy as np

from Source.ConfigFile import ConfigFile
import Source.utils.loggingHCP as logging

def UncTempCorrection(node):
    ''' Called by 
        ProcessL1b.read_unc_coefficient_factory, 
        ProcessL1b.read_unc_coefficient_class, 
        ProcessL1b.read_unc_coefficient_frm 

        Thermal coefficients devised for each radiometer class are base on "Working Temperature" defined as:
            TriOS G1: ambient temperature in the thermal chamber external to the radiometer in thermal equilibrium. 
            Sea-Bird: internal thermistor temperature.'''

    unc_grp = node.getGroup("RAW_UNCERTAINTIES")
    # sensorID = Utilities.get_sensor_dict(node)
    # inv_ID = {v: k for k, v in sensorID.items()}
    for sensor in ["LI", "LT", "ES"]:
        TempCoeffDS = unc_grp.getDataset(sensor+"_TEMPDATA_CAL")

        meanSPECTEMP,meanAIRTEMP,meanCAPSONTEMP = None,None,None
        airTempMargin = 2.5 # Average estimate of margin for working temperature (G1) above air temp
        # SPECTEMP should be present for all platform/sensors (SeaBird,TriOS,DALEC),
        #   but only populated with non-zeroes where an internal thermistor is available.

        # CAPSONTEMP only available for TriOS.
        sigmaT = None
        if ConfigFile.settings['SensorType'].lower() == "seabird" or \
            ConfigFile.settings['SensorType'].lower() == "dalec":
            sensorGroup = node.getGroup(f'{sensor}_LIGHT')
            if "SPECTEMP" in sensorGroup.datasets:
                specTEMP = sensorGroup.getDataset("SPECTEMP")
                meanSPECTEMP = np.mean(np.array(specTEMP.data.tolist()))
            else:
                logging.writeLogFileAndPrint("Internal temperature dataset not found")
                return False
            # NOTE: Potential placeholder for SeaBird CODs.
            # if "CAPSONTEMP" in sensorGroup.datasets:
            #     capsonTEMP = sensorGroup.getDataset("CAPSONTEMP")
            #     capsonTEMP.datasetToColumns()
            #     meanCAPSONTEMP = capsonTEMP.columns['T'][0]
            # # else:
            # #     logging.writeLogFileAndPrint("Caps-on temperature dataset not found")
        elif ConfigFile.settings['SensorType'].lower() == "trios":
            sensorGroup = node.getGroup(f'{sensor}')
            if "SPECTEMP" in sensorGroup.datasets:
                # NOTE: Need to distinguish G2 at some point
                specTEMP = sensorGroup.getDataset("SPECTEMP")
                meanSPECTEMP = np.mean(np.array(specTEMP.data.tolist()))
            else:
                logging.writeLogFileAndPrint("Internal temperature dataset not found")
            if "CAPSONTEMP" in sensorGroup.datasets:
                capsonTEMP = sensorGroup.getDataset("CAPSONTEMP")
                capsonTEMP.datasetToColumns()
                meanCAPSONTEMP = capsonTEMP.columns['T'][0]
                # NOTE: This is used for unc. in thermal corr even if COD temp is not used due to 30 deg. C threshold
                # NOTE: Confirm this.
                sigmaT = capsonTEMP.columns['sigmaT'][0]
            if "AIRTEMP" in node.getGroup('ANCILLARY_METADATA').datasets:
                airTEMP = node.getGroup('ANCILLARY_METADATA').getDataset("AIRTEMP").columns['AIRTEMP']
                meanAIRTEMP = np.mean(np.array(airTEMP))
            else:
                logging.writeLogFileAndPrint("Air temperature dataset not found")

        # Now make the decision which value to use as the internal working temperature of the sensor.
        # NOTE: Currently, only TriOS L1A processing matches dark files to extract CAPSONTEMP
        if meanSPECTEMP != 0.0:
            # NOTE: G2 thermistor acquisition is still under development
            logging.writeLogFileAndPrint(f"{sensor}: Using internal thermistor for sensor working temperature")
            workingTemp = meanSPECTEMP     # SeaBird, DALEC, and TriOS G2 should always follow this path
            workingTempSource = 'InternalThermistor'
        elif meanCAPSONTEMP and ConfigFile.settings['fL1bThermal'] == 3:
            if meanAIRTEMP:
                if (meanAIRTEMP + airTempMargin < 30) and (meanCAPSONTEMP < 30): # Both conditions must be met
                    logging.writeLogFileAndPrint(f"{sensor}: meanAIRTEMP + airTempMargin < 30. Using air temp with margin for sensor working temperature")
                    workingTemp = meanAIRTEMP + airTempMargin
                    workingTempSource = 'AirTemp+2.5C'
                else:
                    logging.writeLogFileAndPrint(f"{sensor}: (meanAIRTEMP + airTempMargin) and/or COD >= 30. Using caps-on dark algorithm for sensor working temperature")
                    workingTemp = meanCAPSONTEMP
                    workingTempSource = 'CapsOnDark'
            else:
                # Emergency fallback where no other source is available. Least accurate.
                logging.writeLogFileAndPrint(f"{sensor}:WARNING: No air temperature provided. Caps-on dark temp used despite temps < 30 C.")
                workingTemp = meanCAPSONTEMP
                workingTempSource = 'CapsOnDark'
        else:
            if meanAIRTEMP:
                logging.writeLogFileAndPrint(f"{sensor}:Using air temp with margin for sensor working temperature")
                workingTemp = meanAIRTEMP + airTempMargin
                workingTempSource = 'AirTemp+2.5C'
            else:
                # Considering fallbacks for air temperature, this should never be reached.
                logging.writeLogFileAndPrint(f"{sensor}:WARNING: No source of information available for sensor working temperature!")
                return False

        # add workingTempSource to attributes
        sensorGroup.attributes['WorkingTempSource'] = workingTempSource
        sensorGroup.attributes['WorkingTemp'] = f'{workingTemp:.1f}'

        if not generateTempCoeffs(workingTemp, sigmaT, TempCoeffDS, sensor):
            logging.writeLogFileAndPrint("Failed to generate Thermal Coefficients")

    return True

def generateTempCoeffs(workingTemp, sigmaT, thermalCoeffDS, sensor):
    # workingTemp can come from 1) internal thermistor, 2) caps-on dark, 3) airTemp + 2.5 C
    #   Option (2) is only for airTemp +2.5C and COD temp both > 30 C, otherwise (1) or (3).
    #   See Utilities.UncTempCorrection

    # Get the reference temperature
    if 'AMBIENT_TEMP' in thermalCoeffDS.attributes:
        # This is temperature of the sensor during calibration from the _THERMAL_ file
        #   REFERENCE_TEMP is the AMBIENT_TEMP during derivation of thermal coefficients, and not relevant here.
        calTemp = float(thermalCoeffDS.attributes["AMBIENT_TEMP"])
    elif 'REFERENCE_TEMP' in thermalCoeffDS.attributes:
        # This is a fallback when class-based thermal coefficients are used and AMBIENT is not provided
        calTemp = float(thermalCoeffDS.attributes["REFERENCE_TEMP"])
    else:
        logging.writeLogFileAndPrint("Reference temperature not found. Aborting ...")
        return False

    # Get thermal coefficient from characterization
    thermalCoeffDS.datasetToColumns()
    therm_coeff = thermalCoeffDS.data[list(thermalCoeffDS.columns.keys())[2]]
    therm_unc = thermalCoeffDS.data[list(thermalCoeffDS.columns.keys())[3]]     # NOTE: See below. Is this sigmaC?
    ThermCorr = []
    ThermUnc = []

    dT = workingTemp - calTemp
    if sigmaT is None:
        sigmaT = dT             # NOTE: Confirm this
    for i, therm_coeffi in enumerate(therm_coeff):
        try:
            # Thermal Correction:
            ThermCorr.append(1 + (therm_coeffi * dT))

            # Thermal Correction Uncertainty:
            # Zibordi and Talone, in prep. 2025
            # 𝑢𝑟(λ, ∆𝑇, DN) = [ε𝑐(λ, ∆𝑇)^2 + ε𝑇(λ, DN)^2]1/2
            # 𝜀𝑐(𝜆, Δ𝑇) = Δ𝑇 × 𝜎𝑐(𝜆)
            # 𝜀𝑇(𝜆, DN) = 𝑐(λ ) × 𝜎𝑇(DN)
            # σc(λ)=0.03×10-2 (°C)-1 in the 400-800 nm spectral range for the 10-40°C interval
            # σc(λ)= therm_unc from THERMAL file NOTE: Confirm this.
            # ∆𝑇 = workingT - calTemp
            sigmaC = therm_unc[i]               # NOTE: Confirm this
            # sigmaC = 0.0003 # See above
            epsC = dT*sigmaC
            epsT = therm_coeffi*sigmaT
            ur = np.sqrt(epsC**2 + epsT**2)

            if ConfigFile.settings["fL1bCal"] == 3:
                # ThermUnc.append(np.abs(therm_unc[i] * (workingTemp - calTemp)) / 2)
                # div by 2 because uncertainty is k=2
                ThermUnc.append(ur / 2)         # NOTE: Confirm this
            else:
                ThermUnc.append(ur)
        except IndexError as err:
            print(f'{err} in Utilities.generateTempCoeffs')
            ThermCorr.append(1.0)
            ThermUnc.append(0)

    # Change thermal general coefficients into ones specific for processed data
    thermalCoeffDS.columns[f"{sensor}_TEMPERATURE_COEFFICIENTS"] = ThermCorr
    thermalCoeffDS.columns[f"{sensor}_TEMPERATURE_UNCERTAINTIES"] = ThermUnc
    thermalCoeffDS.columnsToDataset()

    return True
