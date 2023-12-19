import pandas as pd
import numpy as np

# Function for calculating concentrations above largest bin
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

# Calculate total concentration of each scan
def total_concentration(save_data, dlogDp_values):

    # create column for storing total concentration values
    save_data['Total number concentration'] = np.nan

    # go through each row in save_data
    for row in range(len(save_data)):
        # reset total_concentration
        total_concentration = 0
        # go through each bin column
        for column in range(1, len(save_data.columns)-2):
            # if current cell is not nan
            if not np.isnan(save_data.iloc[row, column]):
                # calculate total concentration of scan and add to total concentration
                total_concentration += save_data.iloc[row, column] * dlogDp_values[column-1]
        # add concentration of second last column
        total_concentration += save_data.iloc[row, len(save_data.columns)-2]
        # store total_concentration in last column of current row
        save_data.iloc[row, len(save_data.columns)-1] = round(total_concentration, 2)
                
    return save_data