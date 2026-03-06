
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

    def lightDarkStats(self, grp: HDFGroup, XSlice: OrderedDict, sensortype: str) -> Union[bool, dict[str, Union[np.array, dict]]]:
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
            ) = DALECUtils.readParams(grp, XSlice, sensortype)
        # %%
        # K1=d0*(V-DC)+d1
        # Ed=a0*((V-DC)/(Inttime+DeltaT_Ed)/K1)/(Tempco_Ed*(Temp-Tref)+1)

        # # Calibration Equation:
        # for i in range(raw_data.data.shape[0]):
        #     c1=inttime[i]+delta_t
        #     for j in range(cd_shape):
        #         raw_data.data[i][j] = 100.0*abc0[j]*((raw_data.data[i][j]-dc[i])/c1
        #         /(def1*(raw_data.data[i][j]-dc[i])+def0))/(tempco[j]*(temp[i]-tref)+1)
        # %%%

        # Presumably, dc is like TriOS raw_back
        #   but dc is from grp, so has len of grp raw, not xSlice raw...
        #   and yet this is how PIU.TriOS.TriOSUtils.readParams handles it. How does that work?


        # check size of data
        nband = len(dc)  # indexes changed for raw_back as is brought to L2
        nmes = len(raw_data)
        if nband != len(raw_data[0]):
            print("ERROR: different number of pixels between dat and back")
            return False


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
    def readParams(grp, xSliceData, s):
        specialNames = {
            'ES':['Delta_T_Ed','Tempco_Ed','d0','d1','a0'],
            'LT':['Delta_T_Lu','Tempco_Lu','e0','e1','b0'],
            'LI':['Delta_T_Lsky','Tempco_Lsky','f0','f1','c0']}

        delta_t=float(grp.attributes[specialNames[s][0]])
        tref=float(grp.attributes['Tref'])
        def0=float(grp.attributes[specialNames[s][2]])
        def1=float(grp.attributes[specialNames[s][3]])

        # ds=gp.datasets[s]
        raw_data = np.asarray(list(xSliceData.values())).transpose() 

        dc=grp.datasets['DARK_CNT'].data[s].tolist()
        inttime=grp.datasets['INTTIME'].data[s].tolist()
        temp=grp.datasets['SPECTEMP'].data['NONE'].tolist()
        cd=grp.datasets['CAL_COEF']
        abc0 = cd.data[specialNames[s][4]].tolist()
        tempco=cd.data[specialNames[s][1]].tolist()
        cd_shape = cd.data.shape[0]

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
        )