# PSM Inversion Tool

The Airmodus PSM Inversion Tool -software is intended for the data inversion of the Airmodus A10 and PSM 2.0.

An .exe version of the software is available by request from info@airmodus.com
## Environment setup instructions
### 1. Install Anaconda
The project is being developed using the Anaconda Python distribution. Anaconda's installation instructions can be found [here](https://docs.anaconda.com/anaconda/install/).
### 2. Create a new Anaconda environment
All required [dependencies](#dependencies) are specified in the `environment.yaml` file. To create a new environment from the file, use:
```
conda env create -f environment.yaml
```
The default environment name is `inversion-env`. To specify a different name, use `-n`:
```
conda env create -f environment.yaml -n env_name
```
### 3. Activate the new environment
Activate the new Anaconda environment using:
```
conda activate inversion-env
```
If the environment was given a different name, use it instead of `inversion-env` in the above line.
### 4. Run app.py
To start PSM Inversion Tool, navigate to the repository's `src` folder and run `app.py`.
## Dependencies
### External Python packages
- pandas
- NumPy
- SciPy
- PyQt
- PyQtGraph
### Python Standard Library modules (included with Python)
- sys
- os
- time
- datetime
- shutil
- tempfile
- traceback