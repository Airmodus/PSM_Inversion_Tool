# PSM Inversion Tool - Software change log 

### 0.8.0 - 2025.06.19
- Scan validation (check scan length and min/max satflow values)
- Min Dp from calibration file

### 0.7.4 - 2025.06.09
- CPC time lag correction fix (incorrect values before data gaps)
- Skip metadata index bug fix (first scan missing in plot)

### 0.7.3 - 2025.04.30
- Replace inf values with nan

### 0.7.2 - 2025.04.16
- File load error handling (skip error files)

### 0.7.1 - 2025.04.15
- Timestamp fractional seconds support (10 Hz data)
- Partial inversion bug fix
- Clear button focus after click (reponsive arrow keys)

### 0.7.0 - 2025.04.02
- Custom bin limit input
- Max Dp from calibration file

### 0.6.0 - 2025.03.25
- Multi-file inversion
- Loading cursor for lengthy processes
- Load data filter for PSM data files (*PSM*.dat)
- Improved raw data processing speed (reduced color resolution)
- Daily file saving
- Inversion plot day markers

### 0.5.5 - 2025.03.11
- 'Remove data with errors' button fix
- Added CPC error code 9 (pulse quality)

### 0.5.4 - 2025.02.07
- Save software version and calibration filename to file
- Filename suggestion bug fix

### 0.5.3 - 2024.08.13
- Improved file reading flexibility

### 0.5.2 - 2024.07.02
- Improved robustness of scan detection