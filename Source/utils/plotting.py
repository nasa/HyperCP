'''################################# PLOTTING ORIENTED #################################'''

import os

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from pandas.plotting import register_matplotlib_converters
import pandas as pd
from tqdm import tqdm

from Source import PACKAGE_DIR as dirPath
from Source.ConfigFile import ConfigFile
from Source.MainConfig import MainConfig
import Source.utils.comparing as comparing
import Source.utils.averaging as averaging
from Source.utils.dating import dateTagToDateTime, timeTag2ToDateTime

register_matplotlib_converters()

def plotRadiometry(root, filename, rType, plotDelta = False):
    ''' Called by Controller for L2 products '''
    plt.figure(1, figsize=(8,6))

    outDir = MainConfig.settings["outDir"]
    if os.path.abspath(outDir) == os.path.join(dirPath,'Data'):
        outDir = dirPath
    plotDir = os.path.join(outDir,'Plots','L2')

    if not os.path.exists(plotDir):
        os.makedirs(plotDir)

    # dataDelta in this case can be STD (for TriOS Factory) or UNC (otherwise)
    dataDelta = None
    # Note: If only one spectrum is left in a given ensemble, STD will
    #be zero for Es, Li, and Lt.'''
    if  (ConfigFile.settings['SensorType'].lower()  in ["dalec", "sorad", "trios", "trios es only"]
            and ConfigFile.settings['fL1bCal'] == 1):
        suffix = 'sd'
    else:
        suffix = 'unc'

    # In the case of reflectances, only use _unc. There are no _std, because reflectances are calculated
    # from the average Lw and Es values within the ensembles
    Data, lwData, Data_MODISA, Data_MODIST = None, None, None, None
    Data_Sentinel3A, Data_Sentinel3B, Data_VIIRSJ,Data_VIIRSN = None, None, None, None
    dataDelta, dataDelta_MODISA, dataDelta_MODIST, dataDelta_Sentinel3A = None, None, None, None
    dataDelta_Sentinel3B, dataDelta_VIIRSJ, dataDelta_VIIRSN, units = None, None, None, None
    if rType=='Rrs' or rType=='nLw':
        print('Plotting Rrs or nLw')
        group = root.getGroup("REFLECTANCE")
        if rType=='Rrs':
            units = group.attributes['Rrs_UNITS']
        else:
            units = group.attributes['nLw_UNITS']
        Data = group.getDataset(f'{rType}_HYPER')
        if plotDelta:
            dataDelta = group.getDataset(f'{rType}_HYPER_unc').data.copy()

        plotRange = [340, 800]
        if ConfigFile.settings['bL2WeightMODISA']:
            Data_MODISA = group.getDataset(f'{rType}_MODISA')
            if plotDelta:
                dataDelta_MODISA = group.getDataset(f'{rType}_MODISA_unc')

        if ConfigFile.settings['bL2WeightMODIST']:
            Data_MODIST = group.getDataset(f'{rType}_MODIST')
            if plotDelta:
                dataDelta_MODIST = group.getDataset(f'{rType}_MODIST_unc')

        if ConfigFile.settings['bL2WeightVIIRSN']:
            Data_VIIRSN = group.getDataset(f'{rType}_VIIRSN')
            if plotDelta:
                dataDelta_VIIRSN = group.getDataset(f'{rType}_VIIRSN_unc')
        if ConfigFile.settings['bL2WeightVIIRSJ']:
            Data_VIIRSJ = group.getDataset(f'{rType}_VIIRSJ')
            if plotDelta:
                dataDelta_VIIRSJ = group.getDataset(f'{rType}_VIIRSJ_unc')
        if ConfigFile.settings['bL2WeightSentinel3A']:
            Data_Sentinel3A = group.getDataset(f'{rType}_Sentinel3A')
            if plotDelta:
                dataDelta_Sentinel3A = group.getDataset(f'{rType}_Sentinel3A_unc')
        if ConfigFile.settings['bL2WeightSentinel3B']:
            Data_Sentinel3B = group.getDataset(f'{rType}_Sentinel3B')
            if plotDelta:
                dataDelta_Sentinel3B = group.getDataset(f'{rType}_Sentinel3B_unc')

    else:
        # Could include satellite convolved (ir)radiances in the future '''
        if rType=='ES':
            print('Plotting Es')
            group = root.getGroup("IRRADIANCE")
            units = group.attributes['ES_UNITS']
            Data = group.getDataset(f'{rType}_HYPER')

        if rType=='LI':
            print('Plotting Li')
            group = root.getGroup("RADIANCE")
            units = group.attributes['LI_UNITS']
            Data = group.getDataset(f'{rType}_HYPER')

        if rType=='LT':
            print('Plotting Lt')
            group = root.getGroup("RADIANCE")
            units = group.attributes['LT_UNITS']
            Data = group.getDataset(f'{rType}_HYPER')
            lwData = group.getDataset('LW_HYPER')
            if plotDelta:
                # lwDataDelta = group.getDataset(f'LW_HYPER_{suffix}')
                lwDataDelta = group.getDataset('LW_HYPER_unc').data.copy() # Lw does not have STD
                # For the purpose of plotting, use zeros for NaN uncertainties
                lwDataDelta = comparing.datasetNan2Zero(lwDataDelta)

        if plotDelta:
            dataDelta = group.getDataset(f'{rType}_HYPER_{suffix}').data.copy() # Do not change the L2 data
            # For the purpose of plotting, use zeros for NaN uncertainties
            dataDelta = comparing.datasetNan2Zero(dataDelta)
        # plotRange = [305, 1140]
        plotRange = [305, 1000]

    font = {'family': 'serif',
        'color':  'darkred',
        'weight': 'normal',
        'size': 16,
        }

    # Hyperspectral
    x = []
    xLw = []
    wave = []
    subwave = [] # accomodates Zhang, which deletes out-of-bounds wavebands
    # For each waveband
    for k in Data.data.dtype.names:
        if comparing.isFloat(k):
            if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                x.append(k)
                wave.append(float(k))
    # Add Lw to Lt plots
    if rType=='LT':
        for k in lwData.data.dtype.names:
            if comparing.isFloat(k):
                if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                    xLw.append(k)
                    subwave.append(float(k))

    # Satellite Bands
    x_MODISA = []
    wave_MODISA = []
    if ConfigFile.settings['bL2WeightMODISA'] and (rType == 'Rrs' or rType == 'nLw'):
        for k in Data_MODISA.data.dtype.names:
            if comparing.isFloat(k):
                if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                    x_MODISA.append(k)
                    wave_MODISA.append(float(k))
    x_MODIST = []
    wave_MODIST = []
    if ConfigFile.settings['bL2WeightMODIST'] and (rType == 'Rrs' or rType == 'nLw'):
        for k in Data_MODIST.data.dtype.names:
            if comparing.isFloat(k):
                if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                    x_MODIST.append(k)
                    wave_MODIST.append(float(k))
    x_VIIRSN = []
    wave_VIIRSN = []
    if ConfigFile.settings['bL2WeightVIIRSN'] and (rType == 'Rrs' or rType == 'nLw'):
        for k in Data_VIIRSN.data.dtype.names:
            if comparing.isFloat(k):
                if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                    x_VIIRSN.append(k)
                    wave_VIIRSN.append(float(k))
    x_VIIRSJ = []
    wave_VIIRSJ = []
    if ConfigFile.settings['bL2WeightVIIRSJ'] and (rType == 'Rrs' or rType == 'nLw'):
        for k in Data_VIIRSJ.data.dtype.names:
            if comparing.isFloat(k):
                if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                    x_VIIRSJ.append(k)
                    wave_VIIRSJ.append(float(k))
    x_Sentinel3A = []
    wave_Sentinel3A = []
    if ConfigFile.settings['bL2WeightSentinel3A'] and (rType == 'Rrs' or rType == 'nLw'):
        for k in Data_Sentinel3A.data.dtype.names:
            if comparing.isFloat(k):
                if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                    x_Sentinel3A.append(k)
                    wave_Sentinel3A.append(float(k))
    x_Sentinel3B = []
    wave_Sentinel3B = []
    if ConfigFile.settings['bL2WeightSentinel3B'] and (rType == 'Rrs' or rType == 'nLw'):
        for k in Data_Sentinel3B.data.dtype.names:
            if comparing.isFloat(k):
                if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                    x_Sentinel3B.append(k)
                    wave_Sentinel3B.append(float(k))

    total = Data.data.shape[0]
    maxRad = 0
    minRad = 0
    cmap = plt.cm.get_cmap("jet")
    color=iter(cmap(np.linspace(0,1,total)))

    # plt.figure(1, figsize=(8,6))
    for i in range(total):
        # Hyperspectral
        y = []
        dy = []
        for k in x:
            y.append(Data.data[k][i])
            if plotDelta:
                dy.append(dataDelta[k][i])
        # Add Lw to Lt plots
        if rType=='LT':
            yLw = []
            dyLw = []
            for k in xLw:
                yLw.append(lwData.data[k][i])
                if plotDelta:
                    dyLw.append(lwDataDelta[k][i])

        # Satellite Bands
        y_MODISA = []
        dy_MODISA = []
        if ConfigFile.settings['bL2WeightMODISA']  and (rType == 'Rrs' or rType == 'nLw'):
            for k in x_MODISA:
                y_MODISA.append(Data_MODISA.data[k][i])
                if plotDelta:
                    dy_MODISA.append(dataDelta_MODISA.data[k][i])
        y_MODIST = []
        dy_MODIST = []
        if ConfigFile.settings['bL2WeightMODIST']  and (rType == 'Rrs' or rType == 'nLw'):
            for k in x_MODIST:
                y_MODIST.append(Data_MODIST.data[k][i])
                if plotDelta:
                    dy_MODIST.append(dataDelta_MODIST.data[k][i])
        y_VIIRSN = []
        dy_VIIRSN = []
        if ConfigFile.settings['bL2WeightVIIRSN']  and (rType == 'Rrs' or rType == 'nLw'):
            for k in x_VIIRSN:
                y_VIIRSN.append(Data_VIIRSN.data[k][i])
                if plotDelta:
                    dy_VIIRSN.append(dataDelta_VIIRSN.data[k][i])
        y_VIIRSJ = []
        dy_VIIRSJ = []
        if ConfigFile.settings['bL2WeightVIIRSJ']  and (rType == 'Rrs' or rType == 'nLw'):
            for k in x_VIIRSJ:
                y_VIIRSJ.append(Data_VIIRSJ.data[k][i])
                if plotDelta:
                    dy_VIIRSJ.append(dataDelta_VIIRSJ.data[k][i])
        y_Sentinel3A = []
        dy_Sentinel3A = []
        if ConfigFile.settings['bL2WeightSentinel3A']  and (rType == 'Rrs' or rType == 'nLw'):
            for k in x_Sentinel3A:
                y_Sentinel3A.append(Data_Sentinel3A.data[k][i])
                if plotDelta:
                    dy_Sentinel3A.append(dataDelta_Sentinel3A.data[k][i])
        y_Sentinel3B = []
        dy_Sentinel3B = []
        if ConfigFile.settings['bL2WeightSentinel3B']  and (rType == 'Rrs' or rType == 'nLw'):
            for k in x_Sentinel3B:
                y_Sentinel3B.append(Data_Sentinel3B.data[k][i])
                if plotDelta:
                    dy_Sentinel3B.append(dataDelta_Sentinel3B.data[k][i])

        c=next(color)
        if max(y) > maxRad:
            maxRad = max(y)+0.1*max(y)
        if rType == 'LI' and maxRad > 20:
            maxRad = 20
        if rType == 'LT' and maxRad > 2:
            maxRad = 2.5
        if min(y) < minRad:
            minRad = min(y)-0.1*min(y)
        if rType == 'LI':
            minRad = 0
        if rType == 'LT':
            minRad = 0
        if rType == 'ES':
            minRad = 0

        # Plot the Hyperspectral spectrum
        plt.plot(wave, y, c=c, zorder=-1)

        # Add the Wei QA score to the Rrs plot, if calculated
        if rType == 'Rrs':
            # Add the Wei score to the Rrs plot, if calculated
            if ConfigFile.products['bL2ProdweiQA']:
                groupProd = root.getGroup("DERIVED_PRODUCTS")
                score = groupProd.getDataset('wei_QA')
                QA_note = f"Wei: {score.columns['QA_score'][i]}"
                axes = plt.gca()
                axes.text(0.7,1.1 - (i+1)/len(score.columns['QA_score']), QA_note,
                    verticalalignment='top', horizontalalignment='right',
                    transform=axes.transAxes,
                    color=c, fontdict=font)

            # Add the QWIP score to the Rrs plot, if calculated
            if ConfigFile.products['bL2Prodqwip']:
                groupProd = root.getGroup("DERIVED_PRODUCTS")
                score = groupProd.getDataset('qwip')
                QA_note = f"QWIP: {score.columns['qwip'][i]:5.3f}"
                axes = plt.gca()
                axes.text(0.75,1.1 - (i+1)/len(score.columns['qwip']), QA_note,
                    verticalalignment='top', horizontalalignment='left',
                    transform=axes.transAxes,
                    color=c, fontdict=font)

        # Add Lw to Lt plots
        if rType=='LT':
            plt.plot(subwave, yLw, c=c, zorder=-1, linestyle='dashed')

        if plotDelta:
            # Generate the polygon for uncertainty bounds
            deltaPolyx = wave + list(reversed(wave))
            dPolyyPlus = [(y[i]+dy[i]) for i in range(len(y))]
            dPolyyMinus = [(y[i]-dy[i]) for i in range(len(y))]
            deltaPolyyPlus = y + list(reversed(dPolyyPlus))
            deltaPolyyMinus = y + list(reversed(dPolyyMinus))

            plt.fill(deltaPolyx, deltaPolyyPlus, alpha=0.2, c=c, zorder=-1)
            plt.fill(deltaPolyx, deltaPolyyMinus, alpha=0.2, c=c, zorder=-1)

            if rType=='LT':
                dPolyyPlus = [(yLw[i]+dyLw[i]) for i in range(len(yLw))]
                dPolyyMinus = [(yLw[i]-dyLw[i]) for i in range(len(yLw))]
                deltaPolyyPlus = yLw + list(reversed(dPolyyPlus))
                deltaPolyyMinus = yLw + list(reversed(dPolyyMinus))
                plt.fill(deltaPolyx, deltaPolyyPlus, alpha=0.2, c=c, zorder=-1)
                plt.fill(deltaPolyx, deltaPolyyMinus, alpha=0.2, c=c, zorder=-1)

        # Satellite Bands
        if ConfigFile.settings['bL2WeightMODISA']:
            # Plot the MODISA spectrum
            if plotDelta:
                plt.errorbar(wave_MODISA, y_MODISA, yerr=dy_MODISA, fmt='.',
                    elinewidth=0.1, color=c, ecolor='black', zorder=3) # ecolor is broken
            else:
                plt.plot(wave_MODISA, y_MODISA, 'o', c=c)
        if ConfigFile.settings['bL2WeightMODIST']:
            # Plot the MODIST spectrum
            if plotDelta:
                plt.errorbar(wave_MODIST, y_MODIST, yerr=dy_MODIST, fmt='.',
                    elinewidth=0.1, color=c, ecolor='black')
            else:
                plt.plot(wave_MODIST, y_MODIST, 'o', c=c)
        if ConfigFile.settings['bL2WeightVIIRSN']:
            # Plot the VIIRSN spectrum
            if plotDelta:
                plt.errorbar(wave_VIIRSN, y_VIIRSN, yerr=dy_VIIRSN, fmt='.',
                    elinewidth=0.1, color=c, ecolor='black')
            else:
                plt.plot(wave_VIIRSN, y_VIIRSN, 'o', c=c)
        if ConfigFile.settings['bL2WeightVIIRSJ']:
            # Plot the VIIRSJ spectrum
            if plotDelta:
                plt.errorbar(wave_VIIRSJ, y_VIIRSJ, yerr=dy_VIIRSJ, fmt='.',
                    elinewidth=0.1, color=c, ecolor='black')
            else:
                plt.plot(wave_VIIRSJ, y_VIIRSJ, 'o', c=c)
        if ConfigFile.settings['bL2WeightSentinel3A']:
            # Plot the Sentinel3A spectrum
            if plotDelta:
                plt.errorbar(wave_Sentinel3A, y_Sentinel3A, yerr=dy_Sentinel3A, fmt='.',
                    elinewidth=0.1, color=c, ecolor='black')
            else:
                plt.plot(wave_Sentinel3A, y_Sentinel3A, 'o', c=c)
        if ConfigFile.settings['bL2WeightSentinel3B']:
            # Plot the Sentinel3B spectrum
            if plotDelta:
                plt.errorbar(wave_Sentinel3B, y_Sentinel3B, yerr=dy_Sentinel3B, fmt='.',
                    elinewidth=0.1, color=c, ecolor='black')
            else:
                plt.plot(wave_Sentinel3B, y_Sentinel3B, 'o', c=c)

    axes = plt.gca()
    axes.set_title(filename, fontdict=font)
    # axes.set_xlim([390, 800])
    axes.set_ylim([minRad, maxRad])

    plt.xlabel('wavelength (nm)', fontdict=font)
    if rType=='LT':
        plt.ylabel(f'LT (LW dash) [{units}]', fontdict=font)
    else:
        plt.ylabel(f'{rType} [{units}]', fontdict=font)

    # Tweak spacing to prevent clipping of labels
    plt.subplots_adjust(left=0.15)
    plt.subplots_adjust(bottom=0.15)

    note = f'Interval: {ConfigFile.settings["fL2TimeInterval"]} s'
    axes.text(0.2, -0.1, note,
    verticalalignment='top', horizontalalignment='right',
    transform=axes.transAxes,
    color='black', fontdict=font)
    axes.grid()

    # Save the plot
    filebasename = filename.split('.hdf')
    fp = os.path.join(plotDir, filebasename[0] + '_' + rType + '.png')
    plt.savefig(fp)
    plt.close() # This prevents displaying the plot on screen with certain IDEs



def plotTimeInterp(xData, xTimer, newXData, yTimer, instr, fp):
    ''' Plot results of L1B time interpolation '''

    outDir = MainConfig.settings["outDir"]
    if os.path.abspath(outDir) == os.path.join(dirPath,'Data'):
        outDir = dirPath
    plotDir = os.path.join(outDir,'Plots','L1B_Interp')

    if not os.path.exists(plotDir):
        os.makedirs(plotDir)

    # For the sake of MacOS, need to hack the datetimes into panda dataframes for plotting
    dfx = pd.DataFrame(data=xTimer, index=list(range(0,len(xTimer))), columns=['x'])
    # *** HACK: CONVERT datetime column to string and back again - who knows why this works? ***
    dfx['x'] = pd.to_datetime(dfx['x'].astype(str))
    dfy = pd.DataFrame(data=yTimer, index=list(range(0,len(yTimer))), columns=['x'])
    dfy['x'] = pd.to_datetime(dfy['x'].astype(str))

    [_,fileName] = os.path.split(fp)
    fileBaseName,_ = fileName.rsplit('.',1)
    register_matplotlib_converters()

    font = {'family': 'serif',
        'color':  'darkred',
        'weight': 'normal',
        'size': 16,
        }

    progressBar = None
    # Steps in wavebands used for plots
    # This happens prior to waveband interpolation, so each interval is ~3.3 nm
    step = ConfigFile.settings['fL1bPlotInterval']

    intervalList = ['ES','LI','LT','sixS_irradiance','direct_ratio','diffuse_ratio']
    # if instr == 'ES' or instr == 'LI' or instr == 'LT':
    if instr in intervalList:
        l = round((len(xData.data.dtype.names)-3)/step) # skip date and time and datetime
        index = l
    else:
        l = len(xData.data.dtype.names)-3 # skip date and time and datetime
        index = None

    if index:
        progressBar = tqdm(total=l, unit_scale=True, unit_divisor=step)

    ticker = 0
    if index is not None:
        for k in xData.data.dtype.names:
            if index % step == 0:
                if k == "Datetag" or k == "Timetag2" or k == "Datetime":
                    continue
                ticker += 1
                progressBar.update(1)

                x = np.copy(xData.data[k]).tolist()
                new_x = np.copy(newXData.columns[k]).tolist()

                fig = plt.figure(figsize=(12, 4))
                ax = fig.add_subplot(1, 1, 1)
                # ax.plot(xTimer, x, 'bo', label='Raw')
                ax.plot(dfx['x'], x, 'bo', label='Raw')
                # ax.plot(yTimer, new_x, 'k.', label='Interpolated')
                ax.plot(dfy['x'], new_x, 'k.', label='Interpolated')
                ax.legend()

                plt.xlabel('Date/Time (UTC)', fontdict=font)
                plt.ylabel(f'{instr}_{k}', fontdict=font)
                plt.subplots_adjust(left=0.15)
                plt.subplots_adjust(bottom=0.15)

                # plt.savefig(os.path.join('Plots','L1E',f'{fileBaseName}_{instr}_{k}.png'))
                plt.savefig(os.path.join(plotDir,f'{fileBaseName}_{instr}_{k}.png'))
                plt.close()
            index +=1
    else:
        for k in xData.data.dtype.names:
            if k == "Datetag" or k == "Timetag2" or k == "Datetime":
                continue

            x = np.copy(xData.data[k]).tolist()
            new_x = np.copy(newXData.columns[k]).tolist()

            fig = plt.figure(figsize=(12, 4))
            ax = fig.add_subplot(1, 1, 1)
            # ax.plot(xTimer, x, 'bo', label='Raw')
            ax.plot(dfx['x'], x, 'bo', label='Raw')
            # ax.plot(yTimer, new_x, 'k.', label='Interpolated')
            ax.plot(dfy['x'], new_x, 'k.', label='Interpolated')
            ax.legend()

            plt.xlabel('Date/Time (UTC)', fontdict=font)
            plt.ylabel(f'{instr}', fontdict=font)
            plt.subplots_adjust(left=0.15)
            plt.subplots_adjust(bottom=0.15)

            if k == 'NONE':
                plt.savefig(os.path.join(plotDir,f'{fileBaseName}_{instr}.png'))
            else:
                plt.savefig(os.path.join(plotDir,f'{fileBaseName}_{instr}_{k}.png'))
            plt.close()

    print('\n')


def specFilter(inFilePath, Dataset, timeStamp, station=None, filterRange=[400, 700],\
            filterFactor=3, rType='None'):

    if ConfigFile.settings['bL1bqcEnableSpecQualityCheckPlot']:
        import logging
        logging.getLogger('matplotlib.font_manager').disabled = True

        outDir = MainConfig.settings["outDir"]
        # If default output path (HyperInSPACE/Data) is used, choose the root HyperInSPACE path,
        # and build on that (HyperInSPACE/Plots/etc...)
        if os.path.abspath(outDir) == os.path.join(dirPath,'Data'):
            outDir = dirPath

        # Otherwise, put Plots in the chosen output directory from Main
        plotDir = os.path.join(outDir,'Plots','L1BQC_Spectral_Filter')

        if not os.path.exists(plotDir):
            os.makedirs(plotDir)

        font = {'family': 'serif',
                'color':  'darkred',
                'weight': 'normal',
                'size': 16,
                }

    # Collect each column name ignoring Datetag and Timetag2 (i.e. each wavelength) in the desired range
    x = []
    wave = []
    for k in Dataset.data.dtype.names:
        if comparing.isFloat(k):
            if float(k)>=filterRange[0] and float(k)<=filterRange[1]:
                x.append(k)
                wave.append(float(k))

    # Read in each spectrum
    total = Dataset.data.shape[0]
    specArray = []
    normSpec = []

    if ConfigFile.settings['bL1bqcEnableSpecQualityCheckPlot']:
        # cmap = plt.cm.get_cmap("jet")
        # color=iter(cmap(np.linspace(0,1,total)))
        print('Creating plots...')
        # plt.figure(1, figsize=(10,8))
        plt.figure(figsize=(10,8))

    for timei in range(total):
        y = []
        for waveband in x:
            y.append(Dataset.data[waveband][timei])

        specArray.append(y)
        peakIndx = y.index(max(y))
        normSpec.append(y / y[peakIndx])
        # plt.plot(wave, y / y[peakIndx], color='grey')

    normSpec = np.array(normSpec)

    aveSpec = np.median(normSpec, axis = 0)
    stdSpec = np.std(normSpec, axis = 0)

    badTimes  = []
    badIndx = []
    # For each spectral band...
    for i in range(0, len(normSpec[0])-1):
        # For each timeseries radiometric measurement...
        for j, rad in enumerate(normSpec[:,i]):
            # Identify outliers and negative values for elimination
            if rad > (aveSpec[i] + filterFactor*stdSpec[i]) or \
                rad < (aveSpec[i] - filterFactor*stdSpec[i]) or \
                rad < 0:
                badIndx.append(j)
                badTimes.append(timeStamp[j])

    badIndx = np.unique(badIndx)
    badTimes = np.unique(badTimes)
    # Duplicates each element to a list of two elements in a list:
    badTimes = np.rot90(np.matlib.repmat(badTimes,2,1), 3)

    if ConfigFile.settings['bL1bqcEnableSpecQualityCheckPlot']:
        # t0 = time.time()
        for timei in range(total):
        # for i in badIndx:
            if timei in badIndx:
                # plt.plot( wave, normSpec[i,:], color='red', linewidth=0.5, linestyle=(0, (1, 10)) ) # long-dot
                plt.plot( wave, normSpec[timei,:], color='red', linewidth=0.5, linestyle=(0, (5, 5)) ) # dashed
            else:
                plt.plot(wave, normSpec[timei,:], color='grey')

        # t1 = time.time()
        # print(f'Time elapsed: {str(round((t1-t0)))} Seconds')

        plt.plot(wave, aveSpec, color='black', linewidth=0.5)
        plt.plot(wave, aveSpec + filterFactor*stdSpec, color='black', linewidth=2, linestyle='dashed')
        plt.plot(wave, aveSpec - filterFactor*stdSpec, color='black', linewidth=2, linestyle='dashed')

        plt.title(f'Sigma = {filterFactor}', fontdict=font)
        plt.xlabel('Wavelength [nm]', fontdict=font)
        plt.ylabel(f'{rType} [Normalized to peak value]', fontdict=font)
        plt.subplots_adjust(left=0.15)
        plt.subplots_adjust(bottom=0.15)
        axes = plt.gca()
        axes.grid()

        # Save the plot
        _,filename = os.path.split(inFilePath)
        filebasename,_ = filename.rsplit('_',1)
        if station:
            fp = os.path.join(plotDir, f'STATION_{station}_{filebasename}_{rType}.png')
        else:
            fp = os.path.join(plotDir, f'{filebasename}_{rType}.png')
        plt.savefig(fp)
        plt.close()

    return badTimes

@staticmethod
def plotUncertainties(root, filename):
    # read in required values and uncs from root
    # import relevant methods
    
    irrGrp = root.getGroup("IRRADIANCE")
    radGrp = root.getGroup("RADIANCE")
    refGrp = root.getGroup("REFLECTANCE")

    es_cols  = irrGrp.getDataset("ES_HYPER").columns
    li_cols  = radGrp.getDataset("LI_HYPER").columns
    lt_cols  = radGrp.getDataset("LT_HYPER").columns
    nlw_cols = refGrp.getDataset("nLw_HYPER").columns
    rrs_cols = refGrp.getDataset("Rrs_HYPER").columns

    for sensor, cols in zip(
        ['ES', 'LI', 'LT', 'Rrs', 'nLw'],
        [es_cols, li_cols, lt_cols, nlw_cols, rrs_cols]
    ):
        if sensor == 'ES':
            casts = []
            dates = cols.pop("Datetag")
            times = cols.pop("Timetag2")  # convert from timetag to time
            for date, tt2 in zip(dates, times):
                casts.append(timeTag2ToDateTime(dateTagToDateTime(date), tt2))
        else:
            cols.pop("Datetag")
            cols.pop("Timetag2")
    
    # TODO: add BRDF UNC to BD_UNCS if available
    bd_grp = root.getGroup("BREAKDOWN")
    waveSubset = np.array(list(es_cols.keys()), float)
    waveKeys   = np.array(list(es_cols.keys()))
    for t, cast in enumerate(casts):
        es  = np.array([es_cols[wvl][t] for wvl in waveKeys])
        li  = np.array([li_cols[wvl][t] for wvl in waveKeys])
        lt  = np.array([lt_cols[wvl][t] for wvl in waveKeys])
        nlw = np.array([nlw_cols[wvl][t] for wvl in waveKeys])
        rrs = np.array([rrs_cols[wvl][t] for wvl in waveKeys])

        ancGroup = root.getGroup("ANCILLARY")
        sza = round(ancGroup.getDataset("SZA").columns["SZA"][0], 2)
        # station is a string moniker for the ensemble, either a station number or a timestamp
        if ConfigFile.settings['bL2Stations']:
            station = f"Station_{ancGroup.getDataset('STATION').columns['STATION'][t]}"
        else:
            station = cast.strftime("%Y%m%d_%H%M%S")

        BD_UNCS = {}
        for _id, ds in bd_grp.datasets.items():
            if "Datetag" in list(ds.columns.keys()):  # remove datetag/timetag if required
                ds.columns.pop("Datetag")
                ds.columns.pop("Timetag2")
            try:
                s, _, src = _id.split('_')  # get uncertainty source and sensor from ds.id
            except ValueError:
                s, _, src1, src2 = _id.split('_')
                src = f"{src1}_{src2}"  # if underscore in error name then handle it here
            if s not in BD_UNCS:
                BD_UNCS[s] = {}  # make new dict if required
            BD_UNCS[s][src] = np.array([ds.columns[wvl][t] for wvl in waveKeys])  # use list comp to turn Odict to np.array per cast

        if ConfigFile.settings['fL1bCal'] <= 2:
            from Source.PIU.Breakdown_CB import plottingToolsCB
            PT = plottingToolsCB(sza, station)

            PT.PlotL1B(
                root,
                waveSubset,
                BD_UNCS,
                es,
                li,
                lt,
            )
            PT.PlotL2(
                root,
                waveSubset, 
                BD_UNCS, 
                nlw, 
                rrs
            )

        elif ConfigFile.settings['fL1bCal'] == 3:
            from Source.PIU.Breakdown_FRM import plottingToolsFRM
            PT = plottingToolsFRM(sza, station)

            PT.plotL1B(
                waveSubset, 
                BD_UNCS,
                dict(
                    ES=es,
                    LI=li,
                    LT=lt,
                ),
            )
            PT.plotL2(
                waveSubset, 
                BD_UNCS, 
                dict(
                    Rrs=rrs,
                    nLw=nlw,
                ) 
            )

def plotIOPs(root, filename, algorithm, iopType, plotDelta = False):

    outDir = MainConfig.settings["outDir"]
    # If default output path (HyperInSPACE/Data) is used, choose the root HyperInSPACE path,
    # and build on that (HyperInSPACE/Plots/etc...)
    if os.path.abspath(outDir) == os.path.join(dirPath,'Data'):
        outDir = dirPath

    # Otherwise, put Plots in the chosen output directory from Main
    plotDir = os.path.join(outDir,'Plots','L2_Products')

    if not os.path.exists(plotDir):
        os.makedirs(plotDir)

    font = {'family': 'serif',
        'color':  'darkred',
        'weight': 'normal',
        'size': 16,
        }

    cmap = plt.cm.get_cmap("jet")

    # dataDelta = None
    group = root.getGroup("DERIVED_PRODUCTS")
    if algorithm == "qaa" or algorithm == "giop":
        plotRange = [340, 700]
        qaaName = f'bL2Prod{iopType}Qaa'
        giopName = f'bL2Prod{iopType}Giop'
        if ConfigFile.products["bL2Prodqaa"] and ConfigFile.products[qaaName]:
            label = f'qaa_{iopType}'
            DataQAA = group.getDataset(label)
            # if plotDelta:
            #     dataDelta = group.getDataset(f'{iopType}_HYPER_delta')
            xQAA = []
            waveQAA = []
            # For each waveband
            for k in DataQAA.data.dtype.names:
                if comparing.isFloat(k):
                    if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                        xQAA.append(k)
                        waveQAA.append(float(k))
            totalQAA = DataQAA.data.shape[0]
            colorQAA = iter(cmap(np.linspace(0,1,totalQAA)))

        if ConfigFile.products["bL2Prodgiop"] and ConfigFile.products[giopName]:
            label = f'giop_{iopType}'
            DataGIOP = group.getDataset(label)
            # if plotDelta:
            #     dataDelta = group.getDataset(f'{iopType}_HYPER_delta')
            xGIOP = []
            waveGIOP = []
            # For each waveband
            for k in DataGIOP.data.dtype.names:
                if comparing.isFloat(k):
                    if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                        xGIOP.append(k)
                        waveGIOP.append(float(k))
            totalGIOP = DataQAA.data.shape[0]
            colorGIOP = iter(cmap(np.linspace(0,1,totalGIOP)))

    if algorithm == "gocad":
        plotRange = [270, 700]
        gocadName = f'bL2Prod{iopType}'
        if ConfigFile.products["bL2Prodgocad"] and ConfigFile.products[gocadName]:

            # ag
            label = f'gocad_{iopType}'
            agDataGOCAD = group.getDataset(label)
            # if plotDelta:
            #     dataDelta = group.getDataset(f'{iopType}_HYPER_delta')
            agGOCAD = []
            waveGOCAD = []
            # For each waveband
            for k in agDataGOCAD.data.dtype.names:
                if comparing.isFloat(k):
                    if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                        agGOCAD.append(k)
                        waveGOCAD.append(float(k))
            totalGOCAD = agDataGOCAD.data.shape[0]
            colorGOCAD = iter(cmap(np.linspace(0,1,totalGOCAD)))

            # Sg
            sgDataGOCAD = group.getDataset('gocad_Sg')

            sgGOCAD = []
            waveSgGOCAD = []
            # For each waveband
            for k in sgDataGOCAD.data.dtype.names:
                if comparing.isFloat(k):
                    if float(k)>=plotRange[0] and float(k)<=plotRange[1]: # also crops off date and time
                        sgGOCAD.append(k)
                        waveSgGOCAD.append(float(k))

            # DOC
            docDataGOCAD = group.getDataset('gocad_doc')

    maxIOP = 0
    minIOP = 0

    # Plot
    plt.figure(1, figsize=(8,6))

    if algorithm == "qaa" or algorithm == "giop":
        if ConfigFile.products["bL2Prodqaa"] and ConfigFile.products[qaaName]:
            for i in range(totalQAA):
                y = []
                # dy = []
                for k in xQAA:
                    y.append(DataQAA.data[k][i])
                    # if plotDelta:
                    #     dy.append(dataDelta[k][i])

                c=next(colorQAA)
                if max(y) > maxIOP:
                    maxIOP = max(y)+0.1*max(y)
                # if iopType == 'LI' and maxIOP > 20:
                #     maxIOP = 20

                # Plot the Hyperspectral spectrum
                plt.plot(waveQAA, y, c=c, zorder=-1)
                # if plotDelta:
                #     # Generate the polygon for uncertainty bounds
                #     deltaPolyx = wave + list(reversed(wave))
                #     dPolyyPlus = [(y[i]+dy[i]) for i in range(len(y))]
                #     dPolyyMinus = [(y[i]-dy[i]) for i in range(len(y))]
                #     deltaPolyyPlus = y + list(reversed(dPolyyPlus))
                #     deltaPolyyMinus = y + list(reversed(dPolyyMinus))
                #     plt.fill(deltaPolyx, deltaPolyyPlus, alpha=0.2, c=c, zorder=-1)
                #     plt.fill(deltaPolyx, deltaPolyyMinus, alpha=0.2, c=c, zorder=-1)
        if ConfigFile.products["bL2Prodgiop"] and ConfigFile.products[giopName]:
            for i in range(totalGIOP):
                y = []
                for k in xGIOP:
                    y.append(DataGIOP.data[k][i])

                c=next(colorGIOP)
                if max(y) > maxIOP:
                    maxIOP = max(y)+0.1*max(y)

                # Plot the Hyperspectral spectrum
                plt.plot(waveGIOP, y,  c=c, ls='--', zorder=-1)

    if algorithm == "gocad":
        if ConfigFile.products["bL2Prodgocad"] and ConfigFile.products[gocadName]:
            for i in range(totalGOCAD):
                y = []
                for k in agGOCAD:
                    y.append(agDataGOCAD.data[k][i])

                c=next(colorGOCAD)
                if max(y) > maxIOP:
                    maxIOP = max(y)+0.1*max(y)

                # Plot the point spectrum
                # plt.scatter(waveGOCAD, y, s=100, c=c, marker='*', zorder=-1)
                plt.plot(waveGOCAD, y, c=c, marker='*', markersize=13, linestyle = '', zorder=-1)

                # Now extrapolate using the slopes
                Sg = []
                for k in sgGOCAD:
                    Sg.append(sgDataGOCAD.data[k][i])
                    yScaler = maxIOP*i/totalGOCAD
                    if k == '275':
                        wave = np.array(list(range(275, 300)))
                        ag_extrap = agDataGOCAD.data['275'][i] * np.exp(-1*sgDataGOCAD.data[k][i] * (wave - 275))
                        plt.plot(wave, ag_extrap,  c=[0.9, 0.9, 0.9], ls='--', zorder=-1)
                        plt.text(285, 0.9*maxIOP - 0.12*yScaler, '{} {:.4f}'.format('S275 = ', sgDataGOCAD.data[k][i]), color=c)

                    if k == '300':
                        wave = np.array(list(range(300, 355)))
                        # uses the trailing end of the last extrapolation.
                        ag_extrap = ag_extrap[-1] * np.exp(-1*sgDataGOCAD.data[k][i] * (wave - 300))
                        plt.plot(wave, ag_extrap,  c=[0.9, 0.9, 0.9], ls='--', zorder=-1)
                        plt.text(300, 0.7*maxIOP - 0.12*yScaler, '{} {:.4f}'.format('S300 = ', sgDataGOCAD.data[k][i]), color=c)

                    if k == '350':
                        # Use the 350 slope starting at 355 (where we have ag)
                        wave = np.array(list(range(355, 380)))
                        ag_extrap = agDataGOCAD.data['355'][i] * np.exp(-1*sgDataGOCAD.data[k][i] * (wave - 355))
                        plt.plot(wave, ag_extrap,  c=[0.9, 0.9, 0.9], ls='--', zorder=-1)
                        plt.text(350, 0.5*maxIOP - 0.12*yScaler, '{} {:.4f}'.format('S350 = ', sgDataGOCAD.data[k][i]), color=c)

                    if k == '380':
                        wave = np.array(list(range(380, 412)))
                        ag_extrap = agDataGOCAD.data['380'][i] * np.exp(-1*sgDataGOCAD.data[k][i] * (wave - 380))
                        plt.plot(wave, ag_extrap,  c=[0.9, 0.9, 0.9], ls='--', zorder=-1)
                        plt.text(380, 0.3*maxIOP - 0.12*yScaler, '{} {:.4f}'.format('S380 = ', sgDataGOCAD.data[k][i]), color=c)

                    if k == '412':
                        wave = np.array(list(range(412, 700)))
                        ag_extrap = agDataGOCAD.data['412'][i] * np.exp(-1*sgDataGOCAD.data[k][i] * (wave - 412))
                        plt.plot(wave, ag_extrap,  c=[0.9, 0.9, 0.9], ls='--', zorder=-1)
                        plt.text(440, 0.15*maxIOP- 0.12*yScaler, '{} {:.4f}'.format('S412 = ', sgDataGOCAD.data[k][i]), color=c)

                # Now tack on DOC
                plt.text(600, 0.5 - 0.12*yScaler, '{} {:3.2f}'.format('DOC = ', docDataGOCAD.data['doc'][i]) , color=c)

    axes = plt.gca()
    axes.set_title(filename, fontdict=font)
    axes.set_ylim([minIOP, maxIOP])

    plt.xlabel('wavelength (nm)', fontdict=font)
    plt.ylabel(f'{label} [1/m]', fontdict=font)

    # Tweak spacing to prevent clipping of labels
    plt.subplots_adjust(left=0.15)
    plt.subplots_adjust(bottom=0.15)

    note = f'Interval: {ConfigFile.settings["fL2TimeInterval"]} s'
    axes.text(0.95, 0.95, note,
    verticalalignment='top', horizontalalignment='right',
    transform=axes.transAxes,
    color='black', fontdict=font)
    axes.grid()

    # Save the plot
    filebasename = filename.split('_')
    fp = os.path.join(plotDir, '_'.join(filebasename[0:-1]) + '_' + label + '.png')
    plt.savefig(fp)
    plt.close() # This prevents displaying the plot on screen with certain IDEs

def saveDeglitchPlots(fileName,timeSeries,dateTime,sensorType,lightDark,windowSize,sigma,badIndex,badIndex2,badIndex3):#,\
    ''' Plot the results of the L1AQC anomaly analysis '''
    outDir = MainConfig.settings["outDir"]
    if os.path.abspath(outDir) == os.path.join(dirPath,'Data'):
        outDir = dirPath
    plotDir = os.path.join(outDir,'Plots','L1AQC_Anoms')

    if not os.path.exists(plotDir):
        os.makedirs(plotDir)

    font = {'family': 'serif',
        'color':  'darkred',
        'weight': 'normal',
        'size': 16}

    waveBand = timeSeries[0]

    radiometry1D = timeSeries[1]
    x = np.array(dateTime)
    avg = averaging.movingAverage(radiometry1D, windowSize).tolist()

    text_ylabel=f'{sensorType}({waveBand}) {lightDark}'
    fig, ax = plt.subplots(1)
    fig.autofmt_xdate()

    # First Pass
    y_anomaly = np.array(radiometry1D)[badIndex]
    x_anomaly = x[badIndex]
    # Second Pass
    y_anomaly2 = np.array(radiometry1D)[badIndex2]
    x_anomaly2 = x[badIndex2]
    # Thresholds
    y_anomaly3 = np.array(radiometry1D)[badIndex3]
    x_anomaly3 = x[badIndex3]

    plt.plot(x, radiometry1D, marker='o', color='k', linestyle='', fillstyle='none')
    plt.plot(x_anomaly, y_anomaly, marker='x', color='red', markersize=12, linestyle='')
    plt.plot(x_anomaly2, y_anomaly2, marker='+', color='red', markersize=12, linestyle='')
    plt.plot(x_anomaly3, y_anomaly3, marker='o', color='red', markersize=12, linestyle='', fillstyle='full', markerfacecolor='blue')
    plt.plot(x[3:-3], avg[3:-3], color='green')

    xfmt = mdates.DateFormatter('%y-%m-%d %H:%M')
    ax.xaxis.set_major_formatter(xfmt)

    plt.text(0,0.95,'Marked for exclusions in ALL bands', transform=plt.gcf().transFigure)
    plt.ylabel(text_ylabel, fontdict=font)
    plt.title('WindowSize = ' + str(windowSize) + ' Sigma Factor = ' + str(sigma), fontdict=font)

    fp = os.path.join(plotDir,fileName)
    # plotName = f'{fp}_W{windowSize}S{sigma}_{sensorType}{lightDark}_{waveBand}.png'
    plotName = f'{fp}_{sensorType}{lightDark}_{waveBand}.png'

    print(plotName)
    plt.savefig(plotName)
    plt.close()

