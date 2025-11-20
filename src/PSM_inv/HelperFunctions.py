import pandas as pd
import numpy as np
import datetime as dt

# Function for calculating concentration above largest bin
def concentration_above_bins(scan_start_time, data_df, lowest_bin_limit):

    # store columns named 'concentration', 'satflow', 't' from data_df to data_df_copy
    data_df_copy = data_df.filter(items=['concentration', 'satflow', 't'], axis=1)
    # create array for storing concentration values
    concentration_values = np.ndarray(dtype='float64', shape=(1, 0))

    # go through scan_start_time values
    # columns: 0 = concentration, 1 = saturator flow, 2 = datetime
    for i in range(len(scan_start_time)):

        # if final scan_start_time hasn't been reached
        if i != len(scan_start_time)-1:
            # read rows in data_df_copy that start from current scan start time and end in next scan start time
            scan = data_df_copy[(data_df_copy.iloc[:, 2] >= scan_start_time[i]) & (data_df_copy.iloc[:, 2] < scan_start_time[i+1])]
        # if final scan_start_time has been reached
        else:
            # read rows in data_df_copy from current scan start time to end
            scan = data_df_copy[data_df_copy.iloc[:, 2] >= scan_start_time[i]]
        
        # filter rows with saturator flow between lowest_bin_limit-0.02 and lowest_bin_limit
        scan = scan[(scan.iloc[:, 1] >= lowest_bin_limit-0.02) & (scan.iloc[:, 1] <= lowest_bin_limit)]
        # if scan is empty
        if scan.empty:
            # store nan in concentration_values
            concentration_values = np.append(concentration_values, np.nan)
        else:
            # calculate average of concentration values in scan and round to 2 decimals
            average_concentration = round(np.average(scan.iloc[:, 0]), 2)
            # store average_concentration in concentration_values
            concentration_values = np.append(concentration_values, average_concentration)

    #print("\nconcentration values:\n", concentration_values)
    return concentration_values

def moving_average(a, n=3):
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n

def expand_psm_data(df):

    # get scan min and max flow rates from data or use defaults
    if 0 in df['Scan status'].values:
        min_flow = df.loc[df['Scan status'] == 0, 'satflow'].median()
    else:
        min_flow = 0.15
    if 2 in df['Scan status'].values:
        max_flow = df.loc[df['Scan status'] == 2, 'satflow'].median()
    else:
        max_flow = 1.9
    print("min_flow, max_flow:", min_flow, max_flow)

    # create 10 Hz time index and forward fill scan status and dilution factor
    df = df.set_index('t').resample('100ms').asfreq().reset_index()
    df['Scan status'] = df['Scan status'].ffill()
    df['dilution'] = df['dilution'].ffill()
    
    # mark scan status changes and calculate time since last change
    df['status_change'] = df['Scan status'] != df['Scan status'].shift()
    df['last_change_time'] = df.loc[df['status_change'], 't']
    df['last_change_time'] = df['last_change_time'].ffill()
    df['time_since_change'] = (df['t'] - df['last_change_time']).dt.total_seconds()

    # calculate length of each scan phase (rising and falling)
    # TODO calculate rising and falling times separately? (in case different scan lengths are used)
    phase_times = df['time_since_change'][((df['Scan status'] == 1) & (df['Scan status'].shift(-1) != 1)) | ((df['Scan status'] == 3) & (df['Scan status'].shift(-1) != 3))]
    #print(f"scan phase lengths:\n{phase_times.value_counts()}") # print unique phase time counts
    scan_time = np.median(phase_times) + 0.1 # add 0.1 to get full rise time at exact status change
    print(f"scan time (s): {scan_time}")

    # get first saturator flow value of each rising and falling scan, exclude first value (partial scan)
    first_values_rising = df['satflow'][((df['Scan status'] == 1) & (df['status_change'] == True) & (df.index != 0))]
    first_values_falling = df['satflow'][((df['Scan status'] == 3) & (df['status_change'] == True) & (df.index != 0))]
    #print("first flow values of rising scans:\n", first_values_rising.value_counts())
    #print("first flow values of falling scans:\n", first_values_falling.value_counts())
    # calculate first value means
    first_rising_mean = np.mean(first_values_rising)
    first_falling_mean = np.mean(first_values_falling)
    #print("first_rising_mean:", first_rising_mean)
    #print("first_falling_mean:", first_falling_mean)

    # calculate first rising and falling time offsets
    scan_power = (max_flow / min_flow) ** (1.0 / scan_time)
    rising_offset = np.log(first_rising_mean / min_flow) / np.log(scan_power)
    falling_offset = np.log(first_falling_mean / max_flow) / np.log(1 / scan_power)
    print("rising_offset, falling_offset:", rising_offset, falling_offset)
    # calculate average offset time
    scan_offset_time = (rising_offset + falling_offset) / 2
    print("scan_offset_time:", scan_offset_time)
    # round to nearest 0.1s
    scan_offset_time = round(scan_offset_time, 1)
    print("rounded scan_offset_time:", scan_offset_time)
    # convert to index amount
    scan_offset_index = int(-1 * scan_offset_time * 10) # negative to shift backwards
    print("scan_offset_index:", scan_offset_index)

    # shift status_change by offset time
    df['status_change'] = df['status_change'].shift(scan_offset_index).fillna(False) # set last values to False
    # shift Scan status by offset time
    df['Scan status'] = df['Scan status'].shift(scan_offset_index).ffill() # forward fill last values
    # shift time_since_change by offset time
    df['time_since_change'] = df['time_since_change'].shift(scan_offset_index)
    # fill last values
    fill_row_index = scan_offset_index
    fill_column_index = df.columns.get_loc('time_since_change')
    while fill_row_index < 0:
        # fill index value by incrementing previous value with 0.1
        df.iloc[fill_row_index, fill_column_index] = df['time_since_change'].iloc[fill_row_index - 1] + 0.1
        fill_row_index += 1

    # if first scan is partial (start status not high/low), calculate time_since_change values
    if df['Scan status'].iloc[0] in [1, 3]:
        # get first status_change index
        first_change_index = df.index[df['status_change']].tolist()[0]
        # calculate time_since_change values
        df.loc[:first_change_index, 'time_since_change'] = (
            (scan_time - 0.1) + df['time_since_change'][:first_change_index] - np.nanmax(df['time_since_change'][:first_change_index])
        )

    # create flow column with nans
    df['flow'] = np.nan
    # calculate flow for scan up and scan down phases
    df.loc[df['Scan status'] == 1, 'flow'] = min_flow * (scan_power ** df['time_since_change'])
    #print(df['flow'][df['Scan status'] == 1])
    df.loc[df['Scan status'] == 3, 'flow'] = max_flow * ((1 / scan_power) ** df['time_since_change'])
    #print(df['flow'][df['Scan status'] == 3])

    df.loc[df['Scan status'] == 0, 'flow'] = min_flow
    df.loc[df['Scan status'] == 2, 'flow'] = max_flow

    df.drop(columns=['status_change', 'last_change_time', 'time_since_change'], inplace=True)

    # print(df)
    # print(df[df['YYYY.MM.DD hh:mm:ss'] == '2025.10.06 15:10:01']) # print row with specific timestamp (testing / debug)

    return df

def expand_cpc_data(df):
    df['YYYY.MM.DD hh:mm:ss'] = pd.to_datetime(df.iloc[:, 0], format='%Y.%m.%d %H:%M:%S')
    print(df)
    expanded_rows = []
    # go through each row and create 10 rows with 100ms intervals
    for row_index, row in df.iterrows():
        base_time = row.iloc[0] # get row base time
        concentrations = row.iloc[1:] # get row concentrations
        # if first row, set only the last value to base time
        if row_index == 0:
            expanded_rows.append([base_time, pd.to_numeric(concentrations.iloc[9], errors='coerce')])
            continue
        # set each concentration to corresponding 10Hz timestamp (backwards offset)
        for i in range(10):
            offset_index = i - 9 # get index for time offset (i 0 = -900ms, i 9 = 0ms)
            new_time = base_time + dt.timedelta(milliseconds=100 * offset_index)
            conc_value = pd.to_numeric(concentrations.iloc[i], errors='coerce')  # <- This ensures NaT/invalids become NaN
            expanded_rows.append([new_time, conc_value])
            
    df_exp = pd.DataFrame(expanded_rows, columns=['t', 'CPC_concentration'])

    return df_exp

def correct_concentration(df, alpha, mu, sigma, slope, intercept, shift):
    
    flow = df['flow']
    dilution_correction = ((np.exp(-0.5 * ((flow - mu) / sigma) ** 2) / np.sqrt(2 * np.pi * sigma ** 2)) *
                           ((1 + np.tanh(alpha * (flow - mu) / sigma)) / sigma) + flow * slope + intercept)
    df['CPC_concentration'] = df['CPC_concentration'].astype('float')
    df['concentration'] = (df['CPC_concentration'].shift(shift) * df['dilution'] / dilution_correction).round(2)
    df['satflow'] = flow.round(4)   
    df['satflow'][df['satflow'] > 1.9] = 1.9
    df['CPC concentration (1/cm3)'] = df['CPC_concentration'].round(2)
    # drop temporary columns
    df.drop(['flow', 'CPC_concentration'], axis=1, inplace=True)
    
    return df