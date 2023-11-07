
# Importing all the required packages
import sys,io
import PyQt5.sip
from PIL import Image
import pandas as pd
import numpy as np
from scipy.interpolate import griddata
import time
from PyQt5.QtWidgets import (QApplication,
                             QGraphicsPixmapItem,
                             QMainWindow,
                             QSplitter,
                             QVBoxLayout,
                             QHBoxLayout,
                             QGridLayout,
                             QComboBox,
                             QSpacerItem,
                             QRadioButton,
                             QTextEdit,
                             QLineEdit,
                             QWidget,
                             QSlider,
                             QLabel,
                             QPushButton,
                             QFileDialog,
                             QCheckBox,
                             QSizePolicy)


from PyQt5.QtWidgets import QProgressDialog
from PyQt5.QtCore import Qt, QRectF,QPointF,QLocale
from PyQt5 import QtGui, QtWidgets
import pyqtgraph as pg
from pyqtgraph.exporters import ImageExporter
from pyqtgraph import Color, QtWidgets, ScatterPlotItem, AxisItem
from pyqtgraph.colormap import ColorMap
from PyQt5.QtGui import (QPen,
                        QColor,
                        QPainterPath,
                        QIntValidator,
                        QImage,
                        QPixmap,
                        QLinearGradient,
                        QBrush,
                        QGradient,
                        QFont)

from pyqtgraph import QtCore,mkPen
import PyQt5.QtCore as QtCore
import shutil
import tempfile
import datetime
import math
from scipy import stats
import os