
from collections import OrderedDict
from typing import Union

# Maths
import numpy as np
import pandas as pd

from Source.HDFGroup import HDFGroup

# PIU
from Source.PIU.BaseInstrument import BaseInstrument
from Source.PIU.PIUDataStore import PIUDataStore as pds

# Utilities
from Source.utils.loggingHCP import writeLogFileAndPrint


class Dalec(BaseInstrument):

    def __init__(self):
        super().__init__()  # call to instrument __init__
        self.instrument = "Dalec"

    # def lightDarkStats(self, grp: HDFGroup, XSlice: OrderedDict, sensortype: str) -> Union[bool, dict[str, Union[np.array, dict]]]:
    def lightDarkStats(self, grp: HDFGroup, lightSlice: OrderedDict, darkSlice: OrderedDict, sensortype: str) -> Union[bool, dict[str, Union[np.array, dict]]]:    
        ''' Under development. '''

        (delta_t,
        tref,
        def0,
        def1,
        raw_data,
        dc,
        inttime,
        temp,
        abc0,
        tempco,
        cd_shape,
        raw_wvl
            ) = DALECUtils.readParams(grp, lightSlice, darkSlice,sensortype)
        # %%
        # K1=d0*(V-DC)+d1
        # Ed=a0*((V-DC)/(Inttime+DeltaT_Ed)/K1)/(Tempco_Ed*(Temp-Tref)+1)

        # # Calibration Equation:
        # for i in range(raw_data.data.shape[0]):
        #     c1=inttime[i]+delta_t
        #     for j in range(cd_shape):
        #
        #         raw_data.data[i][j] = 100.0*abc0[j]*((raw_data.data[i][j]-dc[i])/c1
        #         /(def1*(raw_data.data[i][j]-dc[i])+def0))/(tempco[j]*(temp[i]-tref)+1)
        #
        #
        # %%%
        # check size of data
        nband = len(dc)  # indexes changed for raw_back as is brought to L2
        nmes = len(raw_data)
        if nband != len(raw_data[0]):
            print("ERROR: different number of pixels between dat and back")
            return False
        
        # offset = []
        # for n in range(nmes):
            # std(back) + std(raw) add in quad  - what about normalise and cal?
            # No background correction for DALEC cal, just the dark offset, equivalant to dark pixels for Trios
            # back_mesure[n, :] = raw_back[:, 0] + raw_back[:, 1]*(int_time[n]/int_time_t0)
            # back_corrected_mesure[n, :] = mesure[n] - back_mesure[n, :]

            # Offset substraction : dark index read from attribute
            # offset.append(np.mean(dc[n]))
            # offset_corrected_mesure[n, :] = back_corrected_mesure[n] - offset[-1]

        # get light and dark data before correction
        light_avg = np.mean(raw_data, axis=1)  # [ind_nocal == False]
        if nmes > 25:
            light_std = np.std(raw_data, axis=1) / pow(nmes, 0.5)  # [ind_nocal == False]
        elif nmes > 3:
            light_std = np.sqrt(((nmes-1)/(nmes-3))*(np.std(raw_data, axis=1) / np.sqrt(nmes))**2)
        else:
            writeLogFileAndPrint("too few scans to make meaningful statistics")
            return False
        # ensure all Dalec outputs are length 255 to match SeaBird HyperOCR stats output
        ones = np.ones(nband)  # to provide array of 1s with the correct shape
        dark_avg = ones * np.mean(dc)
        if nmes > 25:
            dark_std = ones * (np.std(np.mean(dc)) / pow(nmes, 0.5))
        else:  # already checked for light data so we know nmes > 3
            dark_std = np.sqrt(((nmes-1)/(nmes-3))*
            (ones * (np.std(np.mean(dc))/np.sqrt(nmes)**2)))
            # adjusting the dark_ave and dark_std shapes will remove sensor specific behaviour in Default and Factory

        offset_corrected_mesure = raw_data - dc

        signal_noise = {}
        for i, wvl in enumerate(raw_wvl):
            signal_noise[wvl] = pow(
                (pow(light_std[i], 2) + pow(dark_std[i], 2)) / pow(np.average(offset_corrected_mesure, axis=0)[i], 2), 0.5)  # sqrt(sigma_light^2 + sigma_dark^2 / dark_corrected_signal^2)

        std_signal = np.std(offset_corrected_mesure, axis=0) / np.average(offset_corrected_mesure, axis=0)  # this is relative



        return dict(
            ave_Light=np.array(light_avg),
            ave_Dark=np.array(dark_avg),
            std_Light=np.array(light_std),
            std_Dark=np.array(dark_std),
            Signal_std=np.array(std_signal),
            Signal_noise=signal_noise,
        )

    def FRM(self, PDS: pds, stats: dict, newWaveBands: np.array) -> dict[str, np.array]:
        # calibration of HyperOCR following the FRM processing of FRM4SOC2
        output = {}
        return output

class DALECUtils():

    @staticmethod
    def readParams(grp, lightSlice, darkSlice, s):
        specialNames = {
            'ES':['Delta_T_Ed','Tempco_Ed','d0','d1','a0'],
            'LT':['Delta_T_Lu','Tempco_Lu','e0','e1','b0'],
            'LI':['Delta_T_Lsky','Tempco_Lsky','f0','f1','c0']}

        delta_t=float(grp.attributes[specialNames[s][0]])
        tref=float(grp.attributes['Tref'])
        def0=float(grp.attributes[specialNames[s][2]])
        def1=float(grp.attributes[specialNames[s][3]])

        # ds=gp.datasets[s]
        # raw_data = np.asarray(list(xSliceData.values())).transpose()
        raw_data = np.asarray(list(lightSlice.values())) #.transpose()
        dc = np.asarray(list(darkSlice[s])) #.transpose()

        # dc=grp.datasets['DARK_CNT'].data[s].tolist()
        inttime=grp.datasets['INTTIME'].data[s].tolist()
        temp=grp.datasets['SPECTEMP'].data['NONE'].tolist()
        cd=grp.datasets['CAL_COEF']
        abc0 = cd.data[specialNames[s][4]].tolist()
        tempco=cd.data[specialNames[s][1]].tolist()
        cd_shape = cd.data.shape[0]

        raw_wl = np.array(list(grp.datasets[s].columns.keys()),dtype=float)

        return(
            delta_t,
            tref,
            def0,
            def1,
            raw_data,
            dc,
            inttime,
            temp,
            abc0,
            tempco,
            cd_shape,
            raw_wl
        )