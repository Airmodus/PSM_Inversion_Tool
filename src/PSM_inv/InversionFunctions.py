

skip = 7
skip = 7
n_average = 20
import pandas as pd 
import numpy as np
from scipy.optimize import curve_fit


class InversionError(Exception):
    "Expection occuring during data inversion"
    pass

class dataReadError(Exception):
    "Error occured during reading in the measurement or calibration data"
    pass


def averagedata(Ninv,Sn):
    # Averaging over scans
    try:
        # if Sn > 1 make a running average of dN and make a new dataframe called Ninv_avg
        if Sn > 1:
            Ninv_avg = Ninv.iloc[:,0:skip]
            temp = Ninv.iloc[:,skip:]
            temp = temp.rolling(Sn, min_periods=1,axis = 1 ).mean()
            temp['bins'] = Ninv['bins']
            Ninv_avg = Ninv_avg.merge(temp, how = 'left',on='bins')
        else:
            messageStatus = 1
            message = "Can't average over one scan, please increase the number of scans to be avaraged."
        return Ninv_avg
    
    except:
        raise InversionError
        messageStatus = 1
        message = "Unexpected error arose during scan averaging"

#%%

# Calculate the bins for inverting the data, using the calibration data and the number of bins and maximum Dp
# Minimum Dp is estimated directly from the calibration file
"""
def calculateBins(calibration_df,maxDp = 12,num_bins = 15):

    # create logarithmically separated bins
    diam_bins = np.logspace(np.log10(np.nanmin(calibration_df['cal_diameter'])), np.log10(maxDp), num_bins)

    # Interpolate the bin limits based on the calibration data on points requested by diam_bins
    bin_lims = np.flip(np.interp(diam_bins, calibration_df['cal_diameter'], calibration_df['cal_satflow']))

    # add one limit in between first and second bin, and between the last and second last bin
    bin_diff = np.diff(bin_lims)/2
    bins = np.append(np.append(bin_lims[0],bin_lims[:-1] + bin_diff),bin_lims[-1])

    return bins,bin_lims
"""
# Function to return the geometric mean of two diameters
def geom_means(x):
    x_mean_bins = np.zeros(len(x)-1)
    for i in range(len(x)-1):
      x_mean_bins[i] = (x[i+1]*x[i])**.5
    return x_mean_bins

# Calculate the limit value of the geometric mean diameter of the first and last bin
def inverse_geom_mean(GMD,lim1):
    return GMD**2/lim1

def calculateBins(calibration_df,fixed_bin_limits):
    # Interpolate the bin limits based on the calibration data on points requested by diam_bins
    # bin_lims = np.flip(np.interp(fixed_bin_limits, calibration_df['cal_diameter'], calibration_df['cal_satflow']))
    # print('calculateBins - bin_lims 1: ', bin_lims)
    # calculate geometric mean diameters of bin limits (used in calculating conc at the real bin limits)
    binning_limit = geom_means(fixed_bin_limits)
    #print('calculateBins - binning_limit 1: ', binning_limit)
    
    # Calculte the smallest and largest size for the diff bins
#    min_bin_edge = inverse_geom_mean(fixed_bin_limits[0],binning_limit[0])
#    max_bin_edge = inverse_geom_mean(fixed_bin_limits[-1],binning_limit[-1])
#    min_bin_edge = inverse_geom_mean(fixed_bin_limits[0],binning_limit[0])
#    max_bin_edge = inverse_geom_mean(fixed_bin_limits[-1],binning_limit[-1])
    max_bin_edge = fixed_bin_limits[-1]
    min_bin_edge = fixed_bin_limits[0]

    # Append the values to the binning limits
    binning_limit = np.append(binning_limit, max_bin_edge)
    binning_limit = np.append(min_bin_edge, binning_limit)
    #print('calculateBins - binning_limit 2: ', binning_limit)

    # Append the values to the binning limits
    #binning_limit = np.append(fixed_bin_limits, max_bin_edge)
    #binning_limit = np.append(min_bin_edge, binning_limit)

    # Convert to flow ranges
    bin_lims = np.flip(np.interp(binning_limit, calibration_df['cal_diameter'], calibration_df['cal_satflow']))
    #print('calculateBins - bin_lims 2: ', bin_lims)

    return bin_lims

# Function to read in the calibration data and add a few column names
def read_calibration_data(file_name):
    try:
        calibration_df = pd.read_csv(file_name, delimiter='\t')
        calibration_df.columns = ['cal_satflow'] + calibration_df.columns[1:].tolist()
        calibration_df.columns = [calibration_df.columns[0], 'cal_diameter'] + calibration_df.columns[2:].tolist()
        calibration_df.columns = calibration_df.columns[:2].tolist() + ['cal_maxdeteff'] + calibration_df.columns[3:].tolist()
        return calibration_df
    except:
        raise dataReadError

# Function to read in the raw measurement data and add a few column names
def readRawData(file_name):
    try:
        data_df = pd.read_csv(file_name, delimiter=',', skiprows=1, header=None)
        data_df['t'] = pd.to_datetime(data_df.iloc[:, 0], format='%d.%m.%Y %H:%M:%S')
        data_df.rename(columns={1: 'concentration', 3: 'satflow'}, inplace=True)
        return data_df
    except:
        raise dataReadError

# Function for grouping the raw data according to the bins generated in calculateBins
# Inputs: data_df, bins
# Outputs: df_sorted, scan_start_time
def groupRawData(data_df,bins):
    # add bins column grouping the sat flows to sat flow bins
    data_df['bins'] = pd.cut(data_df['satflow'],bins)

    # find satlow up and down transitions and average satflow_diff over 20s
    satflow_diff = np.convolve(np.diff(data_df['satflow']), np.ones((n_average,))/n_average, mode='valid')

    # find the values where the satflow_diff changes sign
    satflow_diff_sign_change = np.diff(np.sign(satflow_diff))

    # define where the satflow_diff_sign_change is not equal to 0
    satflow_diff_sign_change = np.where(satflow_diff_sign_change != 0)

    # add 10 to satflow_diff_sign_change to account for the averaging
    satflow_diff_sign_change = satflow_diff_sign_change[0] + n_average/2

    nan_filler = np.zeros(int(n_average/2))
    nan_filler[:] = np.nan

    data_df['up_scan'] = np.append(np.append(nan_filler, np.sign(satflow_diff)), nan_filler)

    # Add scan number from the point of changing scans
    data_df['scan_no'] = np.cumsum(abs(data_df['up_scan'].diff() / 2))

    # filter satflow 0 out of the data
    data_df = data_df[data_df['satflow'] != 0]

    # Calculate bin mean concentration grouped by scans and flow bins
    data_df['bin_mean_c'] = data_df.groupby(['bins', 'scan_no'])['concentration'].transform('mean')

    # Clean nans from data
    data_df.dropna(inplace=True)

    df_binmean = data_df.groupby(['bins', 'scan_no']).mean()
    df_binmean.reset_index(inplace=True)
    n_scans = np.unique(df_binmean['scan_no'])

    df_sorted = data_df[['t','scan_no']].sort_values(by=['t'], ascending=True)
    df_sorted = df_sorted.groupby('scan_no').first()
    scan_start_time = np.array(df_sorted.reset_index(drop=True))[:,0]

    return df_sorted,scan_start_time,df_binmean,n_scans


def generateNinv(data_df,df_binmean,bins,calibration_df,bin_lims,n_scans):

    # create a new dataframe where first column is lower bin edge and second column is upper bin edge
    Ninv = pd.DataFrame({'lower':bins[:-1], 'upper':bins[1:]})
    Ninv['bins'] = pd.unique(df_binmean['bins'])

    # calculate new parameter called Dp by interpolating the cal_diameter as a function of cal_satflow
    Ninv['LowerDp'] = np.interp(Ninv['lower'], np.flip(calibration_df['cal_satflow']), np.flip(calibration_df['cal_diameter']))
    Ninv['UpperDp'] = np.interp(Ninv['upper'], np.flip(calibration_df['cal_satflow']), np.flip(calibration_df['cal_diameter']))
    Ninv['dlogDp'] = np.log10(Ninv['LowerDp']) - np.log10(Ninv['UpperDp'])
    Ninv['MaxDeteff'] = np.interp(Ninv['UpperDp'], calibration_df['cal_diameter'],calibration_df['cal_maxdeteff'])
    Dplot = np.interp(bin_lims, np.flip(calibration_df['cal_satflow']), np.flip(calibration_df['cal_diameter']))

    for i in range(len(n_scans)):
        # add columns to dataframe Ninv with dN values
        temp = df_binmean[['bins','bin_mean_c']].where(df_binmean['scan_no'] == i).dropna()
        temp = temp.rename(columns={"bins": "bins", "bin_mean_c": 'dN'+str(i)})   
        # calculate the difference between the upper and lower bin edge in temp
        temp['dN'+str(i)] = temp['dN'+str(i)].diff()
        # merge temp to Ninv
        Ninv = Ninv.merge(temp, how = 'left',on='bins')

    # set negative values to zero in the dataframe Ninv
    temp = Ninv.iloc[:,skip:]
    temp[temp<0] = 0
    Ninv.iloc[:,skip:] =temp

    # multiply columns of dataframe Ninv from 7 onwards by the column MaxDeteff
    Ninv.iloc[:,skip:] = Ninv.iloc[:,skip:].divide(Ninv['MaxDeteff'], axis="index")

    for i in Ninv.columns[skip:]:
        Ninv[i] = Ninv[i] / Ninv['dlogDp']

    # Drop the first row of the dataframe Ninv (as this is only the first bin edge)
    Ninv = Ninv.drop(Ninv.index[0])

    Ninv['LowerDp'] = np.interp(bin_lims[1:], np.flip(calibration_df['cal_satflow']), np.flip(calibration_df['cal_diameter']))
    Ninv['UpperDp'] = np.interp(bin_lims[:-1], np.flip(calibration_df['cal_satflow']), np.flip(calibration_df['cal_diameter']))
   
    return Ninv,Dplot


def check_instrument_errors(df):
    # assing 46th column of df as PSM system status error
    df['PSM_system_status_error'] = df.iloc[:,46]

    # convert the system status hex to row of binary
    df['PSM_system_status_error'] = df['PSM_system_status_error'].apply(lambda x: bin(int(x, 16))[2:].zfill(16))

    # assing 44th column of df as CPC system status error
    df['CPC_system_status_error'] = df.iloc[:,44]

    # convert the system status hex to row of binary
    df['CPC_system_status_error'] = df['CPC_system_status_error'].apply(lambda x: bin(int(x, 16))[2:].zfill(16))

    # PSM bits correspond to errors:
    # 0 CODES_STATUS_GROWTH_TUBE_TEMP
    # 1 CODES_STATUS_SATURATOR_TEMP
    # 2 CODES_STATUS_SATURATOR_FLOW
    # 3 CODES_STATUS_PREHEATER_TEMP
    # 4 CODES_STATUS_INLET_TEMP
    # 5 CODES_STATUS_MIX1_PRESS
    # 6 CODES_STATUS_MIX2_PRESS
    # 7 CODES_STATUS_ABS_PRESS
    # 8 CODES_STATUS_EXCESS_FLOW
    # 9 CODES_STATUS_DRAIN_LEVEL
    # 10 CODES_STATUS_AMBIENT_TEMP
    # 11 CODES_STATUS_DRAIN_TEMP

    # Make a table out of the PSM system status error based on the text above
    PSM_system_status_error = pd.DataFrame({'PSM_system_status_error':
                                                ['GROWTH TUBE TEMPERATURE', 
                                                'SATURATOR TEMPERATURE', 
                                                'SATURATOR FLOW', 
                                                'PREHEATER TEMPERATURE', 
                                                'INLET TEMPERATURE', 
                                                'MIX1 PRESSURE', 
                                                'MIX2 PRESSURE', 
                                                'ABSOLUTE PRESSURE', 
                                                'EXCESS FLOW', 
                                                'DRAIN LEVEL', 
                                                'AMBIENT TEMPERATURE', 
                                                'DRAIN TEMPERATURE']})

    # Find all unique PSM system status errors from df['PSM_system_status_error']
    PSM_system_status_error_unique = np.unique(df['PSM_system_status_error'])

    # make a 16 bit binary row of zeros
    zeros = '0000000000000000'
    # change every bit of "zeros" based on all the CPC_system_status_error_unique bit rows
    for i in range(len(PSM_system_status_error_unique)):
        for j in range(16):
            if PSM_system_status_error_unique[i][j] == '1':
                zeros = zeros[:j] + '1' + zeros[j+1:]
    # print the errors in zeros based on PSM_system_status_error table and start from the right
    print("PSM errors found in the data:")
    if zeros == '0000000000000000':
        print('No CPC errors')
    else:
        for i in range(16):
            if zeros[15-i] == '1':
                print(PSM_system_status_error.iloc[i,0])

    PSM_errors_list = [PSM_system_status_error.iloc[i, 0] for i in range(16) if zeros[15 - i] == '1']

    # CPC bits correspond to errors:
    # 0 CODES_STATUS_OPTICS_TEMP
    # 1 CODES_STATUS_SATURATOR_TEMP
    # 2 CODES_STATUS_CONDENSER_TEMP
    # 3 CODES_STATUS_ABS_PRESS
    # 4 CODES_STATUS_NOZ_PRESS
    # 5 CODES_STATUS_LASER_POWER
    # 6 CODES_STATUS_LIQUID_LEVEL
    # 7 CODES_STATUS_AMBIENT_TEMP
    # 8 CODES_STATUS_CRITICAL_PRESS

    # Make a table out of the CPC system status error based on the text above
    CPC_system_status_error = pd.DataFrame({'CPC_system_status_error': 
                                            ['OPTICS TEMPERATURE', 
                                                'SATURATOR TEMPERATURE', 
                                                'CONDENSER TEMPERATURE', 
                                                'ABSOLUTE PRESSURE', 
                                                'NOZZLE PRESSURE', 
                                                'LASER POWER', 
                                                'LIQUID LEVEL', 
                                                'AMBIENT TEMPERATURE', 
                                                'CRITICAL PRESSURE']})

    # Find all unique CPC system status errors
    CPC_system_status_error_unique = df['CPC_system_status_error'].unique()

    # make a 16 bit binary row of zeros
    zeros = '0000000000000000'
    # change every bit of "zeros" based on all the CPC_system_status_error_unique bit rows
    for i in range(len(CPC_system_status_error_unique)):
        for j in range(16):
            if CPC_system_status_error_unique[i][j] == '1':
                zeros = zeros[:j] + '1' + zeros[j+1:]
    # print the errors in zeros based on CPC_system_status_error table and start from the right
    print("CPC errors found in the data:")
    if zeros == '0000000000000000':
        print('No CPC errors')
    else:
        for i in range(16):
            if zeros[15-i] == '1':
                print(CPC_system_status_error.iloc[i,0])

    # Return PSM and CPC errors as lists
    CPC_errors_list = [CPC_system_status_error.iloc[i, 0] for i in range(16) if zeros[15 - i] == '1']

    return PSM_errors_list, CPC_errors_list


# Goes through the calibration data and calculates the calibration curves
def inst_calib(calibration_df):
    # make a linear fit of cal_diameter as a function of cal_satflow for the last three values of the dataframe cal
    cal_fit = np.polyfit(calibration_df['cal_satflow'][-3:], calibration_df['cal_diameter'][-3:], 1)


    # use cal_fit to define the satflow where the diameter is the upper limit of the instrument
    if np.nanmax(calibration_df['cal_diameter']) > 8:
        maxDp = 12
    else:
        maxDp = 4

    satflowlimit = (maxDp - cal_fit[1])/cal_fit[0]

    if np.nanmax(calibration_df['cal_diameter']) > 8:
        # limit satflow lower limit to 0.05
        if satflowlimit < 0.05:
            satflowlimit = 0.05
    else:
        # limit satflow lower limit to 0.1
        if satflowlimit < 0.1:
            satflowlimit = 0.1

    # Manually set the upper limits of the fits from calibration     
    calibration_df['cal_satflow'][len(calibration_df)-1] = satflowlimit
    calibration_df['cal_diameter'][len(calibration_df)-1] = maxDp

    # sort cal dataframe by cal_satflow in descending order and reindex
    calibration_df.sort_values(by=['cal_satflow'], ascending=False,inplace = True)
    calibration_df.reset_index(drop=True,inplace = True)

    return calibration_df


def calculate_bin_limits(min_size, max_size, num_bins):
    
    # set number of limits to number of bins + 1
    num_limits = num_bins + 1
    # calculate bin limits
    bin_limits = 10**np.linspace(np.log10(min_size), np.log10(max_size), num_limits)
    print('bin_limits:', bin_limits)

    return bin_limits

# calculate size calibration fitting curve
def calculate_size_fitting(qsat, d50):

    x = qsat
    y = d50

    def se(x,a = 3.5,b=2.5,c = .5,d = 10):
        return x/(x-a)+b + x/((x+c)**d)

    popt0 = np.array([3.5,2.5,.5,10])
    popt, _ = curve_fit(se, x, y,popt0)
    # define new input values
    x_new = 10**np.linspace(np.log10(0.1), np.log10(2.0),50)
    # unpack optima parameters for the objective function
    a,b,c,d = popt
    # use optimal parameters to calculate new values
    y_new = se(x_new,*popt)

    return x_new, y_new

# calculate detection efficiency fitting curve
def calculate_deteff_fitting(d50, det, d50fit):

    x = d50
    y = det

    def de(x, shift=1, scale=1,max_val = 1):
        return (1 / (1 + np.exp(-(x - shift) / scale)))*max_val

    popt0 = np.array([1.5,0.015,1])
    popt, _ = curve_fit(de, x, y, popt0)
    # define new input values
    #x_new = np.linspace(0.01, 14, 250)
    #x_new = 10**np.linspace(np.log10(0.2), np.log10(16),50)
    x_new = d50fit
    # unpack optima parameters for the objective function
    a0, b0, c0 = popt
    #a0, b0, c0 ,d0 = popt
    # use optimal parameters to calculate new values
    y_new = de(x_new,*popt)

    return x_new, y_new

#%%


# Get unique bin limits from the inverted data matrix
def getDplot(Ninv,calibration_df,Dplot):
    return np.unique([Ninv['UpperDp'],Ninv['LowerDp']])

    # plot cal['cal_diameter'] as a function of cal['cal_satflow'] and the Dplot
    plt.figure(6)
    plt.plot(calibration_df['cal_satflow'], calibration_df['cal_diameter'], 'o', label='calibration data')
    plt.plot(bin_lims, Dplot, 'o', label='bin limits')
    plt.xlabel('Saturation flow (cm3/s)')
    plt.ylabel('Diameter (nm)')
    plt.title('Calibration data and bin limits')
    plt.legend()
    # add dashed gray line to show the bin limits
    for i in range(len(bin_lims)):
        plt.axvline(bin_lims[i], color='gray', linestyle='--')
    # change the x axis to log scale
    plt.xscale('log')
    # change the y axis to log scale
    plt.yscale('log')

    # Plot the maxdeteff value for Dplot in a separate figure
    plt.figure(7)
    plt.plot(Dplot, Ninv['MaxDeteff'], 'o')
    plt.xlabel('Diameter (nm)')
    plt.ylabel('Maximum Detection Efficiency')
    plt.title('Maximum Detection Efficiency as a function of diameter')
    # change the x axis to log scale
    plt.xscale('log')


def fit_calibration(calibration_df,model,n_average = 20):
    # make a linear fit of cal_diameter as a function of cal_satflow for the last three values of the dataframe cal
    cal_fit = np.polyfit(calibration_df['cal_satflow'][-3:], calibration_df['cal_diameter'][-3:], 1)

    # use cal_fit to define the satflow where the diameter is the upper limit of the instrument
    if model == 'PSM2.0':
        maxDp = 12
        satflowlimit = (maxDp - cal_fit[1])/cal_fit[0]
        # limit satflow lower limit to 0.05
        if satflowlimit < 0.05:
            satflowlimit = 0.05
        calibration_df['cal_satflow'][len(calibration_df)-1] = satflowlimit
        calibration_df['cal_diameter'][len(calibration_df)-1] = maxDp
    else:
        maxDp = 4
        satflowlimit = (maxDp - cal_fit[1])/cal_fit[0]
        # limit satflow lower limit to 0.1
        if satflowlimit < 0.1:
            satflowlimit = 0.1
        calibration_df['cal_satflow'][len(calibration_df)-1] = satflowlimit
        calibration_df['cal_diameter'][len(calibration_df)-1] = maxDp

    # sort cal dataframe by cal_satflow in descending order and reindex
    calibration_df = calibration_df.sort_values(by=['cal_satflow'], ascending=False)
    calibration_df = calibration_df.reset_index(drop=True)

    return calibration_df

