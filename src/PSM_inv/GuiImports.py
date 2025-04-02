# Importing all the required packages

# Python Standard Library modules
import sys
import os
import time
import datetime
import shutil
import tempfile
import traceback

# external packages
import pandas as pd
import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import (Qt,
                          QLocale,
                          QRegExp)
from PyQt5.QtGui import (QIntValidator,
                         QDoubleValidator,
                         QRegExpValidator,
                         QPixmap,
                         QTransform)
from PyQt5.QtWidgets import (QApplication,
                             QMainWindow,
                             QVBoxLayout,
                             QHBoxLayout,
                             QGridLayout,
                             QComboBox,
                             QSpacerItem,
                             QTextEdit,
                             QLineEdit,
                             QWidget,
                             QLabel,
                             QPushButton,
                             QFileDialog,
                             QCheckBox,
                             QSplitter,
                             QSizePolicy)