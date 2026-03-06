
from collections import OrderedDict
from typing import Union

# Maths
import numpy as np

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
        ''' Under development. Was built like HyperOCR, but it's more like Trios. No shutter.'''

        # TODO: Need to carry CAL_COEFF group forward from L1AQC
        (
            _,
            raw_back,
            raw_data,
            raw_wvl,
            int_time,
            int_time_t0,
            DarkPixelStart,
            DarkPixelStop,
        ) = DALECUtils.readParams(grp, XSlice, sensortype)
        
        
        ''' Unsliced L1AQC grp is no longer needed here '''
        # Dalec
        lightData = XSlice['LIGHT']  # lightGrp.getDataset(sensortype)
        darkData = XSlice['DARK'][sensortype]

         # store results locally for speed
        std_light=[]
        std_dark=[]
        ave_light=[]
        ave_dark = []
        env_pert = []
        std_signal = []
        signal_noise = {}

        # number of replicates for light and dark readings
        N = np.asarray(list(lightData.values())).shape[1]
        Nd = np.asarray(darkData).shape[0]
        for i, k in enumerate(lightData.keys()):
            wvl = str(float(k))

            # apply normalisation to the standard deviations used in uncertainty calculations
            if N > 25:  # normal case
                std_light.append(np.std(lightData[k])/np.sqrt(N))
                std_dark.append(np.std(darkData)/np.sqrt(Nd) )  # sigma here is essentially sigma**2 so N must sqrt
            elif N > 3:  # few scans, use different statistics
                std_light.append(np.sqrt(((N-1)/(N-3))*(np.std(lightData[k]) / np.sqrt(N))**2))
                std_dark.append(np.sqrt(((Nd-1)/(Nd-3))*(np.std(darkData) / np.sqrt(Nd))**2))
            else:
                writeLogFileAndPrint("too few scans to make meaningful statistics")
                return False

            ave_light.append(np.average(lightData[k]))
            ave_dark.append(np.average(darkData))
            env_pert.append(np.abs(np.std(lightData[k])/np.average(lightData[k])))

            for x in range(N):
                try:
                    lightData[k][x] -= darkData[x]
                except IndexError as err:
                    writeLogFileAndPrint(f"Light/Dark indexing error PIU.HypperOCR: {err}")
                    return False

            signalAve = np.average(lightData[k])  # at this point in the code lightdata is light-dark see line 95

            if signalAve:
                signal_noise[wvl] = pow((pow(std_light[i], 2) + pow(std_dark[i], 2))/pow(signalAve, 2), 0.5)
                # this should be divided by
            else:
                signal_noise[wvl] = 0.0

            std_signal.append(np.std(lightData[k])/signalAve)  # as % of Dark corrected signal

        return dict(
            ave_Light=np.array(ave_light),
            ave_Dark=np.array(ave_dark),
            std_Light=np.array(std_light),
            std_Dark=np.array(std_dark),
            Signal_std=np.array(std_signal),
            Signal_noise=signal_noise,
            )  # output as dictionary for use in ProcessL2/PIU

    def FRM(self, PDS: pds, stats: dict, newWaveBands: np.array) -> dict[str, np.array]:
        # calibration of HyperOCR following the FRM processing of FRM4SOC2
        output = {}
        return output

class DALECUtils():

    @staticmethod
    def readParams(grp, xSliceData, s):

        # gp=node.getGroup('ES')
        gpc=node.getGroup('CAL_COEF')
        delta_t_ed=float(gpc.attributes['Delta_T_Ed'])
        tref=float(gpc.attributes['Tref'])
        d0=float(gpc.attributes['d0'])
        d1=float(gpc.attributes['d1'])
        ds=gp.datasets['ES']
        dc=gp.datasets['DARK_CNT'].data['ES'].tolist()
        inttime=gp.datasets['INTTIME'].data['ES'].tolist()
        temp=gp.datasets['SPECTEMP'].data['NONE'].tolist()
        cd=gpc.datasets['Cal_ES']
        a0 = cd.data['a0'].tolist()
        tempco_ed=cd.data['Tempco_Ed'].tolist()

        # K1=d0*(V-DC)+d1
        # Ed=a0*((V-DC)/(Inttime+DeltaT_Ed)/K1)/(Tempco_Ed*(Temp-Tref)+1)

        for i in range(ds.data.shape[0]):
            c1=inttime[i]+delta_t_ed
            for j in range(cd.data.shape[0]):
                ds.data[i][j] = 100.0*a0[j]*((ds.data[i][j]-dc[i])/c1
                /(d1*(ds.data[i][j]-dc[i])+d0))/(tempco_ed[j]*(temp[i]-tref)+1)

        # As in the calibration step above, this presumes UV bands (initial pixels) are always calibrated and
        #   any truncation in calibration is on the NIR end
        gp.attributes['CAL_START'] = str(0)
        gp.attributes['CAL_STOP'] = str(j)
        gp = node.getGroup('ES_L1AQC')
        gp.attributes['CAL_START'] = str(0)
        gp.attributes['CAL_STOP'] = str(j)