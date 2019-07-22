# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'OtherWindow.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!
import io
import logging
import os

#import args as args
import pandas
import pylab
from PyQt5 import QtCore, QtGui, QtWidgets, Qt
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QPixmap
from PyQt5.QtWidgets import QRadioButton, QComboBox, QPushButton, QTextEdit, QFileDialog, QMessageBox, QPlainTextEdit, \
    QScrollArea
from PyQt5.QtWidgets import QGridLayout, QLabel, QButtonGroup, QLineEdit, QSpinBox, QCheckBox

from pkg_resources import resource_filename
from pyqtgraph import PlotWidget

from FPEAM.gui.src.main.python.fpeamgui.AttributeValueStorage import AttributeValueStorage
#from FPEAM.gui.src.main.python.fpeamgui.AttributeValueStorage import attributeValueObj
from FPEAM import (IO, FPEAM, utils)

from FPEAM.gui.src.main.python.fpeamgui.run_config import runConfigCreation
from FPEAM.gui.src.main.python.fpeamgui.MovesConfig import movesConfigCreation
from FPEAM.gui.src.main.python.fpeamgui.NonroadConfig import nonroadConfigCreation
from FPEAM.gui.src.main.python.fpeamgui.emissionFactorsConfig import emissionFactorsConfigCreation
from FPEAM.gui.src.main.python.fpeamgui.fugitiveDustConfig import fugitiveDustConfigCreation

from FPEAM.scripts.fpeam import main

import tempfile
import threading, time

import matplotlib.pyplot as plt
plt.rcdefaults()
import numpy as np
import pandas as pd

class AlltabsModule(QtWidgets.QWidget):

    def setupUIHomePage(self):
        # Home Page tab created
        self.tabHome = QtWidgets.QWidget()
        self.tabHome.setWindowTitle("FPEAM")
        # Home Page tab added
        self.centralwidget.addTab(self.tabHome, "FPEAM")

        # Home Page code start
        self.windowLayout = QGridLayout()
        self.windowLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.windowLayout.setColumnStretch(5, 1)
        #self.windowLayout.setColumnStretch(4, 1)

        self.tabHome.setLayout(self.windowLayout)

        self.windowLayout.setSpacing(15)

        # Created UI element - Title
        self.labelTitleFPEAM = QLabel()
        self.labelTitleFPEAM.setText("Feedstock Production Emissions to Air Model")
        self.labelTitleFPEAM.setObjectName("title")
        self.labelTitleFPEAM.setFixedHeight(39)
        self.labelTitleFPEAM.setAlignment(QtCore.Qt.AlignCenter)
        self.windowLayout.addWidget(self.labelTitleFPEAM, 0, 0, 1, 5)

        # Created UI element - Title Line
        self.labelTitleFPEAMLine = QLabel()
        pixmapLine = QPixmap('C:\Project\snehal/line.png')
        pixmap = pixmapLine.scaledToHeight(14)
        self.labelTitleFPEAMLine.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.windowLayout.addWidget(self.labelTitleFPEAMLine, 1, 0, 1, 5)

        # Created UI element Module Selection
        self.labelModules = QLabel()
        self.labelModules.setText("Modules")
        self.labelModules.setObjectName("allLabels")
        self.labelModules.setAlignment(QtCore.Qt.AlignCenter)
        self.labelModules.setFixedHeight(30)
        self.labelModules.setFixedWidth(160)
        self.checkBoxMoves = QCheckBox("MOVES")
        self.checkBoxMoves.setFixedWidth(100)
        self.checkBoxMoves.setFixedHeight(30)
        self.checkBoxMoves.setChecked(True)
        self.checkBoxMoves.stateChanged.connect(self.onStateChangedMoves)
        self.checkBoxNonroad = QCheckBox("NONROAD")
        self.checkBoxNonroad.setFixedWidth(100)
        self.checkBoxNonroad.setFixedHeight(30)
        self.checkBoxNonroad.setChecked(True)
        self.checkBoxNonroad.stateChanged.connect(self.onStateChangedNonroad)
        self.checkBoxEmissionFactors = QCheckBox("emissionfactors")
        self.checkBoxEmissionFactors.setFixedWidth(100)
        self.checkBoxEmissionFactors.setFixedHeight(30)
        self.checkBoxEmissionFactors.setChecked(True)
        self.checkBoxEmissionFactors.stateChanged.connect(self.onStateChangedEmissionFactors)
        self.checkBoxFugitiveDust = QCheckBox("fugitivedust")
        self.checkBoxFugitiveDust.setFixedWidth(100)
        self.checkBoxFugitiveDust.setFixedHeight(30)
        self.checkBoxFugitiveDust.setChecked(True)
        self.checkBoxFugitiveDust.stateChanged.connect(self.onStateChangedFugitiveDust)
        self.windowLayout.addWidget(self.labelModules, 2, 0)
        self.windowLayout.addWidget(self.checkBoxMoves, 2, 1)
        self.windowLayout.addWidget(self.checkBoxNonroad, 2, 2)
        self.windowLayout.addWidget(self.checkBoxEmissionFactors, 2, 3)
        self.windowLayout.addWidget(self.checkBoxFugitiveDust, 2, 4)


        # Created UI element Scenario Name
        self.labelScenaName = QLabel()
        self.labelScenaName.setText("Scenario Name")
        self.labelScenaName.setToolTip("Enter the Scenario Name")
        self.labelScenaName.setFixedHeight(30)
        self.labelScenaName.setFixedWidth(160)
        self.labelScenaName.setObjectName("allLabels")
        self.labelScenaName.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditScenaName = QLineEdit(self)
        self.lineEditScenaName.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditScenaName.setFixedHeight(30)
        regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(regex)
        self.lineEditScenaName.setValidator(validator)
        self.windowLayout.addWidget(self.labelScenaName, 3,0)
        self.windowLayout.addWidget(self.lineEditScenaName, 3, 1, 1, 4)

        # UI element - Project Path
        self.labelProjPath = QLabel()
        self.labelProjPath.setText("Project Path")
        self.labelProjPath.setObjectName("allLabels")
        self.labelProjPath.setAlignment(QtCore.Qt.AlignCenter)
        self.labelProjPath.setFixedHeight(30)
        self.labelProjPath.setFixedWidth(160)
        self.labelProjPath.setToolTip("Folder path where input and output files will be stored")
        self.browseBtn = QPushButton("Browse", self)
        self.browseBtn.setFixedWidth(100)
        self.browseBtn.setFixedHeight(30)
        self.browseBtn.clicked.connect(self.getfiles)
        self.lineEditProjectPath = QLineEdit(self)
        self.lineEditProjectPath.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditProjectPath.setFixedHeight(30)
        self.windowLayout.addWidget(self.labelProjPath, 4, 0)
        self.windowLayout.addWidget(self.browseBtn, 4, 1)
        self.windowLayout.addWidget(self.lineEditProjectPath, 4, 2, 1, 3)

        #NREL Logo Label
        self.logoImage = QLabel()
        pixmap = QPixmap('C:\Project\snehal/image.png')
        pixmap = pixmap.scaledToWidth(182)
        pixmap = pixmap.scaledToHeight(40)
        self.logoImage.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.windowLayout.addWidget(self.logoImage, 5, 0)

        # Created UI element Reset Button
        self.resetBtn = QPushButton("Reset", self)
        self.resetBtn.setFixedHeight(40)
        self.resetBtn.setFixedWidth(152)
        self.resetBtn.setObjectName("resetRunBtn")
        self.resetBtn.clicked.connect(self.rresetFields)
        self.windowLayout.addWidget(self.resetBtn, 5, 3)

        # Created UI element Run Button
        self.runBtn = QPushButton("Run", self)
        self.runBtn.setFixedWidth(152)
        self.runBtn.setFixedHeight(40)
        self.runBtn.setObjectName("resetRunBtn")
        self.runBtn.clicked.connect(self.runTheSelectedModules)
        self.windowLayout.addWidget(self.runBtn, 5, 4)

        # Custom Data Filepaths Label
        self.customDataFilepathsLabel = QLabel()
        self.customDataFilepathsLabel.setText("Custom Data Filepaths")
        self.customDataFilepathsLabel.setFixedHeight(30)
        self.customDataFilepathsLabel.setObjectName("subTitleLabels")
        self.labeCustomDatafilesArrow = QLabel()
        self.labeCustomDatafilesArrow.setAlignment(QtCore.Qt.AlignCenter)
        pixmapLine = QPixmap('C:\Project\snehal/arrow.png')
        pixmap = pixmapLine.scaledToHeight(25)
        self.labeCustomDatafilesArrow.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.windowLayout.addWidget(self.customDataFilepathsLabel, 6, 0, 1, 4)
        self.windowLayout.addWidget(self.labeCustomDatafilesArrow)

        # Created UI element - Custom Dtatfiles below Line
        self.labelCustomDatafilsLine = QLabel()
        pixmapLine1 = QPixmap('C:\Project\snehal/line.png')
        pixmap1 = pixmapLine1.scaledToHeight(14)
        self.labelCustomDatafilsLine.setPixmap(pixmap1)
        self.resize(pixmap1.width(), pixmap1.height())
        self.windowLayout.addWidget(self.labelCustomDatafilsLine, 7, 0, 1, 5)


        # UI element - Equipment
        self.labelEq = QLabel()
        self.labelEq.setObjectName("allLabels")
        self.labelEq.setAlignment(QtCore.Qt.AlignCenter)
        self.labelEq.setFixedHeight(30)
        self.labelEq.setFixedWidth(160)
        self.labelEq.setText("Farm Equipment")
        self.labelEq.setToolTip("Select equipment input dataset")
        self.browseBtnEq = QPushButton("Browse", self)
        self.browseBtnEq.setFixedWidth(100)
        self.browseBtnEq.setFixedHeight(30)
        self.browseBtnEq.clicked.connect(self.getfilesEq)
        self.lineEditEq = QLineEdit(self)
        self.lineEditEq.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditEq.setFixedHeight(30)
        self.windowLayout.addWidget(self.labelEq, 8, 0)
        self.windowLayout.addWidget(self.browseBtnEq, 8, 1)
        self.windowLayout.addWidget(self.lineEditEq, 8, 2, 1, 3)

        # UI element - Production
        self.labelProd = QLabel()
        self.labelProd.setObjectName("allLabels")
        self.labelProd.setAlignment(QtCore.Qt.AlignCenter)
        self.labelProd.setFixedHeight(30)
        self.labelProd.setFixedWidth(160)
        self.labelProd.setText("Feedstock Production")
        self.labelProd.setToolTip("Select production input dataset")
        self.browseBtnProd = QPushButton("Browse", self)
        self.browseBtnProd.setFixedWidth(100)
        self.browseBtnProd.setFixedHeight(30)
        self.browseBtnProd.clicked.connect(self.getfilesProd)
        self.lineEditProd = QLineEdit(self)
        self.lineEditProd.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditProd.setFixedHeight(30)
        self.windowLayout.addWidget(self.labelProd, 9, 0)
        self.windowLayout.addWidget(self.browseBtnProd, 9, 1)
        self.windowLayout.addWidget(self.lineEditProd, 9, 2, 1, 3)

        # Feedstock Loss Factors
        self.labelFedLossFact = QLabel()
        self.labelFedLossFact.setObjectName("allLabels")
        self.labelFedLossFact.setAlignment(QtCore.Qt.AlignCenter)
        self.labelFedLossFact.setFixedHeight(30)
        self.labelFedLossFact.setFixedWidth(160)
        self.labelFedLossFact.setText("Feedstock Loss Factors")
        self.labelFedLossFact.setToolTip("Select Feedstock Loss Factors dataset")
        self.browseBtnFLoss = QPushButton("Browse", self)
        self.browseBtnFLoss.setFixedWidth(100)
        self.browseBtnFLoss.setFixedHeight(30)
        self.browseBtnFLoss.clicked.connect(self.getfilesFLoss)
        self.lineEditFedLossFact = QLineEdit(self)
        self.lineEditFedLossFact.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditFedLossFact.setFixedHeight(30)
        self.windowLayout.addWidget(self.labelFedLossFact, 10, 0)
        self.windowLayout.addWidget(self.browseBtnFLoss, 10, 1)
        self.windowLayout.addWidget(self.lineEditFedLossFact, 10, 2, 1, 3)

        # Transportation graph
        self.labelTransGraph = QLabel()
        self.labelTransGraph.setObjectName("allLabels")
        self.labelTransGraph.setAlignment(QtCore.Qt.AlignCenter)
        self.labelTransGraph.setText("Transportation Graph")
        self.labelTransGraph.setFixedHeight(30)
        self.labelTransGraph.setFixedWidth(160)
        self.labelTransGraph.setToolTip("Select Transportation graph dataset")
        self.browseBtnTransGr = QPushButton("Browse", self)
        self.browseBtnTransGr.setFixedWidth(100)
        self.browseBtnTransGr.setFixedHeight(30)
        self.browseBtnTransGr.clicked.connect(self.getfilesTransGr)
        self.lineEditTransGraph = QLineEdit(self)
        self.lineEditTransGraph.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditTransGraph.setFixedHeight(30)
        self.windowLayout.addWidget(self.labelTransGraph, 11, 0)
        self.windowLayout.addWidget(self.browseBtnTransGr, 11, 1)
        self.windowLayout.addWidget(self.lineEditTransGraph, 11, 2, 1, 3)

        # Advanced Options Label
        self.advOptionsLabel = QLabel()
        self.advOptionsLabel.setText("Advanced Options")
        self.advOptionsLabel.setFixedHeight(30)
        self.advOptionsLabel.setObjectName("subTitleLabels")
        self.labelAdvOptionsArrow = QLabel()
        self.labelAdvOptionsArrow.setAlignment(QtCore.Qt.AlignCenter)
        pixmapLine = QPixmap('C:\Project\snehal/arrow.png')
        pixmap = pixmapLine.scaledToHeight(25)
        self.labelAdvOptionsArrow.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.windowLayout.addWidget(self.advOptionsLabel, 12, 0, 1, 4)
        self.windowLayout.addWidget(self.labelAdvOptionsArrow)

        # Created UI element - Advanced Optiones below Line
        self.labelAdvOptionsLine = QLabel()
        pixmapLine2 = QPixmap('C:\Project\snehal/line.png')
        pixmap2 = pixmapLine2.scaledToHeight(14)
        self.labelTitleFPEAMLine.setPixmap(pixmap2)
        self.resize(pixmap2.width(), pixmap2.height())
        self.windowLayout.addWidget(self.labelTitleFPEAMLine, 13, 0, 1, 5)

        # Ui Element - Logging Verbosity Level
        self.labelLoggVerboLevel = QLabel()
        self.labelLoggVerboLevel.setObjectName("allLabels")
        self.labelLoggVerboLevel.setAlignment(QtCore.Qt.AlignCenter)
        self.labelLoggVerboLevel.setText("Logging Level")
        self.labelLoggVerboLevel.setFixedHeight(30)
        self.labelLoggVerboLevel.setFixedWidth(160)
        self.comboBoxVerbosityLevel = QComboBox(self)
        self.comboBoxVerbosityLevel.setFixedWidth(100)
        self.comboBoxVerbosityLevel.setFixedHeight(30)
        self.comboBoxVerbosityLevel.addItem("INFO")
        self.comboBoxVerbosityLevel.addItem("ERROR")
        self.comboBoxVerbosityLevel.addItem("WARNING")
        self.comboBoxVerbosityLevel.addItem("UNSET")
        self.comboBoxVerbosityLevel.addItem("CRITICAL")
        self.comboBoxVerbosityLevel.addItem("DEBUG")
        self.index = self.comboBoxVerbosityLevel.findText("DEBUG")
        self.comboBoxVerbosityLevel.setCurrentIndex(self.index)
        self.comboBoxVerbosityLevel.setEditable(True)
        self.leditVerboLevel = self.comboBoxVerbosityLevel.lineEdit()
        self.leditVerboLevel.setAlignment(QtCore.Qt.AlignCenter)
        self.leditVerboLevel = self.comboBoxVerbosityLevel.lineEdit()
        self.leditVerboLevel.setReadOnly(True)
        self.windowLayout.addWidget(self.labelLoggVerboLevel, 14, 0)
        self.windowLayout.addWidget(self.comboBoxVerbosityLevel, 14, 1)

        # UI element  -  Router Engine
        self.labelRE = QLabel()
        self.labelRE.setObjectName("allLabels")
        self.labelRE.setAlignment(QtCore.Qt.AlignCenter)
        self.labelRE.setFixedHeight(30)
        self.labelRE.setFixedWidth(160)
        self.labelRE.setText("Use Router Engine")
        self.labelRE.setToolTip("Do you want to set Router Engine - Yes/No")
        self.comboBoxRE = QComboBox(self)
        self.comboBoxRE.setFixedWidth(100)
        self.comboBoxRE.setFixedHeight(30)
        self.comboBoxRE.addItem("Yes")
        self.comboBoxRE.addItem("No")
        self.comboBoxRE.setCurrentText("Yes")
        self.index = self.comboBoxRE.findText("Yes")
        self.comboBoxRE.setCurrentIndex(self.index)
        self.comboBoxRE.setEditable(True)
        self.leditRE = self.comboBoxRE.lineEdit()
        self.leditRE.setAlignment(QtCore.Qt.AlignCenter)
        self.leditRE = self.comboBoxRE.lineEdit()
        self.leditRE.setReadOnly(True)
        self.windowLayout.addWidget(self.labelRE, 15, 0)
        self.windowLayout.addWidget(self.comboBoxRE, 15, 1)

        # UI element -  Backfill Flag
        self.labelBF = QLabel()
        self.labelBF.setObjectName("allLabels")
        self.labelBF.setFixedHeight(30)
        self.labelBF.setFixedWidth(160)
        self.labelBF.setAlignment(QtCore.Qt.AlignCenter)
        self.labelBF.setText("Backfill Missing Data")
        self.labelBF.setToolTip("Do you want to set Backfill Flag - Yes/No")
        self.comboBoxBF = QComboBox(self)
        self.comboBoxBF.setFixedWidth(100)
        self.comboBoxBF.setFixedHeight(30)
        self.comboBoxBF.addItem("Yes")
        self.comboBoxBF.addItem("No")
        self.comboBoxBF.setCurrentText("Yes")
        self.index = self.comboBoxBF.findText("Yes")
        self.comboBoxBF.setCurrentIndex(self.index)
        self.comboBoxBF.setEditable(True)
        self.leditBE = self.comboBoxBF.lineEdit()
        self.leditBE.setAlignment(QtCore.Qt.AlignCenter)
        self.leditBF = self.comboBoxBF.lineEdit()
        self.leditBF.setReadOnly(True)
        self.windowLayout.addWidget(self.labelBF, 16, 0)
        self.windowLayout.addWidget(self.comboBoxBF, 16, 1)

        #Empty space
        self.labelEmpty = QLabel()
        self.windowLayout.addWidget(self.labelEmpty, 17, 0, 1, 5)

        # Empty space
        self.labelEmpty1 = QLabel()
        self.windowLayout.addWidget(self.labelEmpty1, 18, 0, 1, 5)

        # Empty space
        self.labelEmpty2 = QLabel()
        self.windowLayout.addWidget(self.labelEmpty2, 19, 0, 1, 5)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 20, 0)

        # Add Empty PlainText
        self.emptyPlainText2 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText2, 21, 0)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 22, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 23, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 24, 0)

        # Add Empty PlainText
        self.emptyPlainText2 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText2, 25, 0)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 26, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 27, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 28, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 29, 0)

        # Add Empty PlainText
        self.emptyPlainText2 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText2, 30, 0)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 31, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 32, 0)


    # Checkbox - MOves Module - Checked

    def onStateChangedMoves(self,state):
        if state == self.checkBoxMoves.isChecked():
            self.centralwidget.setTabEnabled(1, False)

        else:
            self.centralwidget.setTabEnabled(1, True)


    # Checkbox - Nonroad Module- Checked

    def onStateChangedNonroad(self,state2):

        if state2 == self.checkBoxNonroad.isChecked():
            self.centralwidget.setTabEnabled(2, False)
        else:
            self.centralwidget.setTabEnabled(2, True)


    # Checkbox - Emission Factors Module- Checked

    def onStateChangedEmissionFactors(self,state3):

        if state3 == self.checkBoxEmissionFactors.isChecked():
            self.centralwidget.setTabEnabled(3, False)
        else:
            self.centralwidget.setTabEnabled(3, True)


    # Checkbox - Fugitive Dust Module- Checked

    def onStateChangedFugitiveDust(self,state4):
        if state4 == self.checkBoxFugitiveDust.isChecked():
            self.centralwidget.setTabEnabled(4, False)
        else:
            self.centralwidget.setTabEnabled(4, True)


    # Project Path
    def getfiles(self):
        fileName = QFileDialog.getExistingDirectory(self, "Browse")
        selectedFileName = str(fileName).split(',')
        self.lineEditProjectPath.setText(selectedFileName[0])

    # Logging Verbosity Level
    def selectionchangecombo(self):
        self.comboBoxVerbosityLevel.currentText()

    # Equipment

    def getfilesEq(self):
        fileNameEq = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        selectedFileNameEq = fileNameEq[0].split("FPEAM/")
        self.lineEditEq.setText(selectedFileNameEq[1])

    # Production

    def getfilesProd(self):
        fileNameProd = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        selectedFileNameProd = fileNameProd[0].split("FPEAM/")
        self.lineEditProd.setText(selectedFileNameProd[1])

    # Feedstock Loss Factors

    def getfilesFLoss(self):
        fileNameFLoss = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        selectedFileNameFLoss = fileNameFLoss[0].split("FPEAM/")
        self.lineEditFedLossFact.setText(selectedFileNameFLoss[1])

    # Transportation graph

    def getfilesTransGr(self):
        fileNameTransGr = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        selectedFileNameTransGr = fileNameTransGr[0].split("FPEAM/")
        self.lineEditTransGraph.setText(selectedFileNameTransGr[1])


        ###########################################################################################################################################################################

    def setupUIMoves(self):
        # MOves tab created
        self.tabMoves = QtWidgets.QWidget()


        # Moves tab added
        self.centralwidget.addTab(self.tabMoves, "MOVES")

        # Moves code start
        self.windowLayout = QGridLayout()
        self.windowLayout.setSpacing(15)
        self.windowLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.windowLayout.setColumnStretch(6, 1)

        self.tabMoves.setLayout(self.windowLayout)


        # self.vScrollArea = QScrollArea(self.tabMoves)
        # self.vScrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        # self.vScrollArea.setWidgetResizable(False)
        # self.vScrollArea.setWidget(self.centralwidget)
        # self.windowLayout.addWidget(self.vScrollArea)
        # self.vScrollArea.show()


        # Created UI element - Title MOVES
        self.labelTitleMOVES = QLabel()
        self.labelTitleMOVES.setText("MOVES Configuration Options")
        self.labelTitleMOVES.setObjectName("title")
        self.labelTitleMOVES.setFixedHeight(39)
        self.labelTitleMOVES.setAlignment(QtCore.Qt.AlignCenter)
        self.windowLayout.addWidget(self.labelTitleMOVES, 0, 0, 1, 5)

        # Created UI element - Title Line
        self.labelTitleMOVESLine = QLabel()
        pixmapLine = QPixmap('C:\Project\snehal/line.png')
        pixmap = pixmapLine.scaledToHeight(14)
        self.labelTitleMOVESLine.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.windowLayout.addWidget(self.labelTitleMOVESLine, 1, 0, 1, 5)

        # Created UI element Aggregation Level
        self.labelAggLevel = QLabel()
        self.labelAggLevel.setText("Aggregation Level")
        self.labelAggLevel.setObjectName("allLabels")
        self.labelAggLevel.setAlignment(QtCore.Qt.AlignCenter)
        self.labelAggLevel.setFixedHeight(30)
        self.labelAggLevel.setFixedWidth(165)
        self.comboBoxAggLevel = QComboBox(self)
        self.comboBoxAggLevel.setObjectName("AggLevelCombo")
        self.comboBoxAggLevel.setFixedWidth(116)
        self.comboBoxAggLevel.setFixedHeight(30)
        self.comboBoxAggLevel.addItem("By State")
        self.comboBoxAggLevel.addItem("By County")
        self.comboBoxAggLevel.addItem("By State-Feedstock")
        self.comboBoxAggLevel.setCurrentText("By County")
        self.index = self.comboBoxAggLevel.findText("By County")
        self.comboBoxAggLevel.setCurrentIndex(self.index)
        self.comboBoxAggLevel.setEditable(True)
        self.leditAggLevel = self.comboBoxAggLevel.lineEdit()
        self.leditAggLevel.setAlignment(QtCore.Qt.AlignCenter)
        self.leditAggLevel = self.comboBoxAggLevel.lineEdit()
        self.leditAggLevel.setReadOnly(True)
        self.windowLayout.addWidget(self.labelAggLevel, 2, 0)
        self.windowLayout.addWidget(self.comboBoxAggLevel, 2, 1)

        # Created UI element Cached Result usage
        self.labelCachedResUse = QLabel()
        self.labelCachedResUse.setText("Use Previous Results")
        self.labelCachedResUse.setObjectName("allLabels")
        self.labelCachedResUse.setAlignment(QtCore.Qt.AlignCenter)
        self.labelCachedResUse.setFixedHeight(30)
        self.labelCachedResUse.setFixedWidth(165)
        self.labelCachedResUse.setToolTip("Use existing results in MOVES output database or run MOVES for all counties")
        self.comboBoxCachedResUse = QComboBox(self)
        self.comboBoxCachedResUse.setFixedWidth(116)
        self.comboBoxCachedResUse.setFixedHeight(30)
        self.comboBoxCachedResUse.addItem("Yes")
        self.comboBoxCachedResUse.addItem("No")
        self.index = self.comboBoxCachedResUse.findText("Yes")
        self.comboBoxCachedResUse.setCurrentIndex(self.index)
        self.comboBoxCachedResUse.setEditable(True)
        self.leditCachedRes = self.comboBoxCachedResUse.lineEdit()
        self.leditCachedRes.setAlignment(QtCore.Qt.AlignCenter)
        self.leditCachedRes = self.comboBoxCachedResUse.lineEdit()
        self.leditCachedRes.setReadOnly(True)
        # Add Empty PlainText
        self.emptyPlainTextCachedRes = QLabel()
        self.windowLayout.addWidget(self.labelCachedResUse, 3, 0)
        self.windowLayout.addWidget(self.comboBoxCachedResUse, 3, 1)
        self.windowLayout.addWidget(self.emptyPlainTextCachedRes, 3, 2)

        # Created UI element Moves Path
        self.MovesPathLable = QLabel()
        self.MovesPathLable.setText("MOVES Executable Path")
        self.MovesPathLable.setObjectName("allLabels")
        self.MovesPathLable.setAlignment(QtCore.Qt.AlignCenter)
        self.MovesPathLable.setFixedHeight(30)
        self.MovesPathLable.setFixedWidth(165)
        self.MovesPathLable.setToolTip("Path where Moves is installed. If it's not installed, then download from the "
                                       "link - "
                                       "<a href ='https://www.epa.gov/moves/moves-versions-limited-current-use#downloading-2014a'>MOVES</a> ")
        self.browseBtnMovesPath = QPushButton("Browse", self)
        self.browseBtnMovesPath.setFixedWidth(116)
        self.browseBtnMovesPath.setFixedHeight(30)
        self.browseBtnMovesPath.clicked.connect(self.getfilesMovesPath)
        self.lineEditMovesPath = QLineEdit(self)
        self.lineEditMovesPath.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditMovesPath.setFixedHeight(30)
        self.lineEditMovesPath.setText("C:\MOVES2014b")
        self.windowLayout.addWidget(self.MovesPathLable, 4, 0)
        self.windowLayout.addWidget(self.browseBtnMovesPath, 4, 1)
        self.windowLayout.addWidget(self.lineEditMovesPath, 4, 2, 1, 3)

        # Created UI element Moves Datafiles
        self.labelDatafiles = QLabel()
        self.labelDatafiles.setText("MOVES Datafiles")
        self.labelDatafiles.setObjectName("allLabels")
        self.labelDatafiles.setAlignment(QtCore.Qt.AlignCenter)
        self.labelDatafiles.setFixedHeight(30)
        self.labelDatafiles.setFixedWidth(165)
        self.labelDatafiles.setToolTip("Select all input files created for MOVES runs")
        self.browseBtnDatafiles = QPushButton("Browse", self)
        self.browseBtnDatafiles.setFixedWidth(116)
        self.browseBtnDatafiles.setFixedHeight(30)
        self.browseBtnDatafiles.clicked.connect(self.getfilesDatafiles)
        self.lineEditDatafiles = QLineEdit(self)
        self.lineEditDatafiles.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditDatafiles.setFixedHeight(30)
        self.windowLayout.addWidget(self.labelDatafiles, 5, 0)
        self.windowLayout.addWidget(self.browseBtnDatafiles, 5, 1)
        self.windowLayout.addWidget(self.lineEditDatafiles, 5, 2, 1, 3)

        # Created UI element Feedstock Measure Type
        self.labelFeedMeasureType = QLabel()
        self.labelFeedMeasureType.setObjectName("allLabels")
        self.labelFeedMeasureType.setAlignment(QtCore.Qt.AlignCenter)
        self.labelFeedMeasureType.setFixedHeight(30)
        self.labelFeedMeasureType.setFixedWidth(165)
        self.labelFeedMeasureType.setText("Feedstock Measure Type")
        self.labelFeedMeasureType.setToolTip("Enter Feedstock Measure Type Identifier")
        self.lineEditFeedMeasureType = QLineEdit(self)
        self.lineEditFeedMeasureType.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditFeedMeasureType.setFixedWidth(116)
        self.lineEditFeedMeasureType.setFixedHeight(30)
        regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(regex)
        self.lineEditFeedMeasureType.setValidator(validator)
        self.lineEditFeedMeasureType.setText("production")
        self.windowLayout.addWidget(self.labelFeedMeasureType, 6, 0)
        self.windowLayout.addWidget(self.lineEditFeedMeasureType, 6, 1)

        # Database Connection Parameters Label
        self.dbConnectionParaLabel = QLabel()
        self.dbConnectionParaLabel.setText("Database Connection Parameters")
        self.dbConnectionParaLabel.setFixedHeight(30)
        self.dbConnectionParaLabel.setObjectName("subTitleLabels")
        self.labelDbConnectionArrow = QLabel()
        self.labelDbConnectionArrow.setAlignment(QtCore.Qt.AlignCenter)
        pixmapLine = QPixmap('C:\Project\snehal/arrow.png')
        pixmap = pixmapLine.scaledToHeight(25)
        self.labelDbConnectionArrow.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.windowLayout.addWidget(self.dbConnectionParaLabel, 7, 0, 1, 4)
        self.windowLayout.addWidget(self.labelDbConnectionArrow)

        # Created UI element - Advanced Optiones below Line
        self.dbConnectionParaLine = QLabel()
        pixmapLine1M = QPixmap('C:\Project\snehal/line.png')
        pixmap1M = pixmapLine1M.scaledToHeight(14)
        self.dbConnectionParaLine.setPixmap(pixmap1M)
        self.resize(pixmap1M.width(), pixmap1M.height())
        self.windowLayout.addWidget(self.dbConnectionParaLine, 8, 0, 1, 5)

        # Created UI element Database Host
        self.labelDbHost = QLabel()
        self.labelDbHost.setText("Database Host")
        self.labelDbHost.setObjectName("allLabels")
        self.labelDbHost.setAlignment(QtCore.Qt.AlignCenter)
        self.labelDbHost.setFixedHeight(30)
        self.labelDbHost.setFixedWidth(165)
        self.labelDbHost.setToolTip("Enter the database host")
        self.lineEditDbHost = QLineEdit(self)
        self.lineEditDbHost.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditDbHost.setFixedHeight(30)
        self.lineEditDbHost.setFixedWidth(125)
        regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(regex)
        self.lineEditDbHost.setValidator(validator)
        self.lineEditDbHost.setText("localhost")
        self.windowLayout.addWidget(self.labelDbHost, 9, 0)
        self.windowLayout.addWidget(self.lineEditDbHost, 9, 1)

        # Created UI element Database Username
        self.labelDbUsername = QLabel()
        self.labelDbUsername.setText("Username")
        self.labelDbUsername.setObjectName("allLabels")
        self.labelDbUsername.setAlignment(QtCore.Qt.AlignCenter)
        self.labelDbUsername.setFixedHeight(30)
        self.labelDbUsername.setFixedWidth(165)
        self.labelDbUsername.setToolTip("Enter the username used for database connection")
        self.lineEditDbUsername = QLineEdit(self)
        self.lineEditDbUsername.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditDbUsername.setFixedHeight(30)
        self.lineEditDbUsername.setFixedWidth(125)
        self.lineEditDbUsername.setText("root")
        self.windowLayout.addWidget(self.labelDbUsername, 9, 2)
        self.windowLayout.addWidget(self.lineEditDbUsername, 9, 3)

        # Created UI element Database Name
        self.labelDbName = QLabel()
        self.labelDbName.setText("Database Name")
        self.labelDbName.setObjectName("allLabels")
        self.labelDbName.setAlignment(QtCore.Qt.AlignCenter)
        self.labelDbName.setFixedHeight(30)
        self.labelDbName.setFixedWidth(165)
        self.labelDbName.setToolTip("Enter database name")
        self.lineEditDbName = QLineEdit(self)
        self.lineEditDbName.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditDbName.setFixedHeight(30)
        self.lineEditDbName.setFixedWidth(125)
        self.lineEditDbName.setText("movesdb20151028")
        self.windowLayout.addWidget(self.labelDbName, 10, 0)
        self.windowLayout.addWidget(self.lineEditDbName, 10, 1)

        # Created UI element Database Password
        self.labelDbPwd = QLabel()
        self.labelDbPwd.setText("Password")
        self.labelDbPwd.setObjectName("allLabels")
        self.labelDbPwd.setAlignment(QtCore.Qt.AlignCenter)
        self.labelDbPwd.setFixedHeight(30)
        self.labelDbPwd.setFixedWidth(165)
        self.labelDbPwd.setToolTip("Enter the password used for database connection")
        self.lineEditDbPwd = QLineEdit(self)
        self.lineEditDbPwd.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditDbPwd.setFixedHeight(30)
        self.lineEditDbPwd.setFixedWidth(125)
        self.lineEditDbPwd.setEchoMode(QtGui.QLineEdit.Password)
        self.lineEditDbPwd.show()
        self.lineEditDbPwd.setText("root")
        self.windowLayout.addWidget(self.labelDbPwd, 10, 2)
        self.windowLayout.addWidget(self.lineEditDbPwd, 10, 3)

        # Execution Timeframe Label
        self.executionTimeLabel = QLabel()
        self.executionTimeLabel.setText("Execution Timeframe")
        self.executionTimeLabel.setFixedHeight(30)
        self.executionTimeLabel.setObjectName("subTitleLabels")
        self.labelExecutionTimeArrow = QLabel()
        self.labelExecutionTimeArrow.setAlignment(QtCore.Qt.AlignCenter)
        pixmapLine = QPixmap('C:\Project\snehal/arrow.png')
        pixmap = pixmapLine.scaledToHeight(25)
        self.labelExecutionTimeArrow.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.windowLayout.addWidget(self.executionTimeLabel, 11, 0, 1, 4)
        self.windowLayout.addWidget(self.labelExecutionTimeArrow)

        # Created UI element - Execution Timeframe below Line
        self.executionTimeLine = QLabel()
        pixmapLine1M = QPixmap('C:\Project\snehal/line.png')
        pixmap1M = pixmapLine1M.scaledToHeight(14)
        self.executionTimeLine.setPixmap(pixmap1M)
        self.resize(pixmap1M.width(), pixmap1M.height())
        self.windowLayout.addWidget(self.executionTimeLine, 12, 0, 1, 5)

        # Created UI element Analysis Year
        self.labelAnalysisYear = QLabel()
        self.labelAnalysisYear.setText("Analysis Year")
        self.labelAnalysisYear.setObjectName("allLabels")
        self.labelAnalysisYear.setAlignment(QtCore.Qt.AlignCenter)
        self.labelAnalysisYear.setFixedHeight(30)
        self.labelAnalysisYear.setFixedWidth(165)
        self.labelAnalysisYear.setToolTip("Start year of Equipment")
        self.comboBoxYear = QComboBox(self)
        self.comboBoxYear.setFixedWidth(116)
        self.comboBoxYear.setFixedHeight(30)
        for i in range(2018, 1990, -1):
            self.number = i
            self.comboBoxYear.addItem(str(i))
        self.index = self.comboBoxYear.findText("2017")
        self.comboBoxYear.setCurrentIndex(self.index)
        self.comboBoxYear.setEditable(True)
        self.leditYear = self.comboBoxYear.lineEdit()
        self.leditYear.setAlignment(QtCore.Qt.AlignCenter)
        self.leditYear = self.comboBoxYear.lineEdit()
        self.leditYear.setReadOnly(True)
        self.labelYearErrorMsg = QLabel()
        self.labelYearErrorMsg.setObjectName("yearErrorMsg")
        self.labelYearErrorMsg.setFixedHeight(30)
        self.labelYearErrorMsg.setText("")
        self.windowLayout.addWidget(self.labelAnalysisYear, 13, 0)
        self.windowLayout.addWidget(self.comboBoxYear, 13, 1)
        self.windowLayout.addWidget(self.labelYearErrorMsg, 13, 2, 1, 4)
        self.comboBoxYear.currentIndexChanged.connect(self.handleItemPressed)

        # Created UI element Timestamp - Month
        self.labelMonth = QLabel()
        self.labelMonth.setText("Month")
        self.labelMonth.setObjectName("allLabels")
        self.labelMonth.setAlignment(QtCore.Qt.AlignCenter)
        self.labelMonth.setFixedHeight(30)
        self.labelMonth.setFixedWidth(165)
        self.comboBoxMonth = QComboBox(self)
        self.comboBoxMonth.setFixedWidth(116)
        self.comboBoxMonth.setFixedHeight(30)
        for i in range(1, 13):
            self.number = i
            self.comboBoxMonth.addItem(str(i))
        self.index = self.comboBoxMonth.findText("10")
        self.comboBoxMonth.setCurrentIndex(self.index)
        self.comboBoxMonth.setEditable(True)
        self.leditMonth = self.comboBoxMonth.lineEdit()
        self.leditMonth.setAlignment(QtCore.Qt.AlignCenter)
        self.leditMonth = self.comboBoxMonth.lineEdit()
        self.leditMonth.setReadOnly(True)
        self.windowLayout.addWidget(self.labelMonth, 14, 0)
        self.windowLayout.addWidget(self.comboBoxMonth, 14, 1)

        # Created UI element Timestamp - Date
        self.labelDate = QLabel()
        self.labelDate.setText("Day of Month")
        self.labelDate.setObjectName("allLabels")
        self.labelDate.setAlignment(QtCore.Qt.AlignCenter)
        self.labelDate.setFixedHeight(30)
        self.labelDate.setFixedWidth(165)
        self.comboBoxDate = QComboBox(self)
        self.comboBoxDate.setFixedWidth(116)
        self.comboBoxDate.setFixedHeight(30)
        for i in range(1, 32):
            self.number = i
            self.comboBoxDate.addItem(str(i))
        self.index = self.comboBoxDate.findText("5")
        self.comboBoxDate.setCurrentIndex(self.index)
        self.comboBoxDate.setEditable(True)
        self.leditDate = self.comboBoxDate.lineEdit()
        self.leditDate.setAlignment(QtCore.Qt.AlignCenter)
        self.leditDate = self.comboBoxDate.lineEdit()
        self.leditDate.setReadOnly(True)
        self.windowLayout.addWidget(self.labelDate, 14, 2)
        self.windowLayout.addWidget(self.comboBoxDate, 14, 3)

        # Created UI element Timestamp - Beginning Hour
        self.labelBegHr = QLabel()
        self.labelBegHr.setText("Beginning Hour")
        self.labelBegHr.setObjectName("allLabels")
        self.labelBegHr.setAlignment(QtCore.Qt.AlignCenter)
        self.labelBegHr.setFixedHeight(30)
        self.labelBegHr.setFixedWidth(165)
        self.comboBoxBegHr = QComboBox(self)
        self.comboBoxBegHr.setFixedWidth(116)
        self.comboBoxBegHr.setFixedHeight(30)
        for i in range(1, 25):
            self.number = i
            self.comboBoxBegHr.addItem(str(i))
        self.index = self.comboBoxBegHr.findText("7")
        self.comboBoxBegHr.setCurrentIndex(self.index)
        self.comboBoxBegHr.setEditable(True)
        self.leditBeghr = self.comboBoxBegHr.lineEdit()
        self.leditBeghr.setAlignment(QtCore.Qt.AlignCenter)
        self.leditBeghr = self.comboBoxBegHr.lineEdit()
        self.leditBeghr.setReadOnly(True)
        self.windowLayout.addWidget(self.labelBegHr, 15, 0)
        self.windowLayout.addWidget(self.comboBoxBegHr, 15, 1)

        # Created UI element Timestamp - Ending Hour
        self.labelEndHr = QLabel()
        self.labelEndHr.setText("Ending Hour")
        self.labelEndHr.setObjectName("allLabels")
        self.labelEndHr.setAlignment(QtCore.Qt.AlignCenter)
        self.labelEndHr.setFixedHeight(30)
        self.labelEndHr.setFixedWidth(165)
        self.comboBoxEndHr = QComboBox(self)
        self.comboBoxEndHr.setFixedWidth(116)
        self.comboBoxEndHr.setFixedHeight(30)
        for i in range(1, 25):
            self.number = i
            self.comboBoxEndHr.addItem(str(i))
        self.index = self.comboBoxEndHr.findText("18")
        self.comboBoxEndHr.setCurrentIndex(self.index)
        self.comboBoxEndHr.setEditable(True)
        self.leditEndhr = self.comboBoxEndHr.lineEdit()
        self.leditEndhr.setAlignment(QtCore.Qt.AlignCenter)
        self.leditEndhr = self.comboBoxEndHr.lineEdit()
        self.leditEndhr.setReadOnly(True)
        self.windowLayout.addWidget(self.labelEndHr, 15, 2)
        self.windowLayout.addWidget(self.comboBoxEndHr, 15, 3)

        # Created UI element Timestamp - Day Type
        self.labelDayType = QLabel()
        self.labelDayType.setText("Day Type")
        self.labelDayType.setObjectName("allLabels")
        self.labelDayType.setAlignment(QtCore.Qt.AlignCenter)
        self.labelDayType.setFixedHeight(30)
        self.labelDayType.setFixedWidth(165)
        self.comboBoxDayType = QComboBox(self)
        self.comboBoxDayType.setFixedWidth(116)
        self.comboBoxDayType.setFixedHeight(30)
        self.comboBoxDayType.addItem("Weekday")
        self.comboBoxDayType.addItem("Weekend")
        self.index = self.comboBoxDayType.findText("Weekday")
        self.comboBoxDayType.setCurrentIndex(self.index)
        self.comboBoxDayType.setEditable(True)
        self.leditDayType = self.comboBoxDayType.lineEdit()
        self.leditDayType.setAlignment(QtCore.Qt.AlignCenter)
        self.leditDayType = self.comboBoxDayType.lineEdit()
        self.leditDayType.setReadOnly(True)
        self.windowLayout.addWidget(self.labelDayType, 16, 0)
        self.windowLayout.addWidget(self.comboBoxDayType, 16, 1)

        # Custom Data Filepaths Label MOVES
        self.customDataFilepathsLabelM = QLabel()
        self.customDataFilepathsLabelM.setText("Custom Data Filepaths")
        self.customDataFilepathsLabelM.setFixedHeight(30)
        self.customDataFilepathsLabelM.setObjectName("subTitleLabels")
        self.labelCustomDatafilesMOVESArrow = QLabel()
        self.labelCustomDatafilesMOVESArrow.setAlignment(QtCore.Qt.AlignCenter)
        pixmapLine = QPixmap('C:\Project\snehal/arrow.png')
        pixmap = pixmapLine.scaledToHeight(25)
        self.labelCustomDatafilesMOVESArrow.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.windowLayout.addWidget(self.customDataFilepathsLabelM, 17, 0, 1, 4)
        self.windowLayout.addWidget(self.labelCustomDatafilesMOVESArrow)

        # Created UI element - Custom Dtatfiles below Line MOVES
        self.labelCustomDatafilsLineM = QLabel()
        pixmapLine2 = QPixmap('C:\Project\snehal/line.png')
        pixmap2 = pixmapLine2.scaledToHeight(14)
        self.labelCustomDatafilsLineM.setPixmap(pixmap2)
        self.resize(pixmap2.width(), pixmap2.height())
        self.windowLayout.addWidget(self.labelCustomDatafilsLineM, 18, 0, 1, 5)

        # Created UI element Truck Capacity
        self.labelTruckCapacity = QLabel()
        self.labelTruckCapacity.setText("Truck Capacity")
        self.labelTruckCapacity.setObjectName("allLabels")
        self.labelTruckCapacity.setAlignment(QtCore.Qt.AlignCenter)
        self.labelTruckCapacity.setFixedHeight(30)
        self.labelTruckCapacity.setFixedWidth(165)
        self.labelTruckCapacity.setToolTip(
            "Select Truck Capacity (truck capacities for feedstock transportation) dataset")
        self.browseBtnTruckCapa = QPushButton("Browse", self)
        self.browseBtnTruckCapa.setFixedWidth(116)
        self.browseBtnTruckCapa.setFixedHeight(30)
        self.browseBtnTruckCapa.clicked.connect(self.getfilesTruckCapa)
        self.lineEditTruckCapa = QLineEdit(self)
        self.lineEditTruckCapa.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditTruckCapa.setFixedHeight(30)
        self.windowLayout.addWidget(self.labelTruckCapacity, 19, 0)
        self.windowLayout.addWidget(self.browseBtnTruckCapa, 19, 1)
        self.windowLayout.addWidget(self.lineEditTruckCapa, 19, 2, 1, 3)

        # Created UI element AVFT
        self.labelAVFT = QLabel()
        self.labelAVFT.setText("AVFT")
        self.labelAVFT.setObjectName("allLabels")
        self.labelAVFT.setAlignment(QtCore.Qt.AlignCenter)
        self.labelAVFT.setFixedHeight(30)
        self.labelAVFT.setFixedWidth(165)
        self.labelAVFT.setToolTip("Select AVFT (fuel fraction by engine type) dataset")
        self.browseBtnAVFT = QPushButton("Browse", self)
        self.browseBtnAVFT.setFixedWidth(116)
        self.browseBtnAVFT.setFixedHeight(30)
        self.browseBtnAVFT.clicked.connect(self.getfilesAVFT)
        self.lineEditAVFT = QLineEdit(self)
        self.lineEditAVFT.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditAVFT.setFixedHeight(30)
        self.windowLayout.addWidget(self.labelAVFT, 20, 0)
        self.windowLayout.addWidget(self.browseBtnAVFT, 20, 1)
        self.windowLayout.addWidget(self.lineEditAVFT, 20, 2, 1, 3)

        # Created UI element MOVES Region to FIPS Map
        self.labelFips = QLabel()
        self.labelFips.setText("MOVES Region to FIPS Map")
        self.labelFips.setObjectName("allLabels")
        self.labelFips.setAlignment(QtCore.Qt.AlignCenter)
        self.labelFips.setFixedHeight(30)
        self.labelFips.setFixedWidth(165)
        self.labelFips.setToolTip("Select Region FIPS Map (production region to MOVES FIPS mapping) dataset")
        self.browseBtnFips = QPushButton("Browse", self)
        self.browseBtnFips.setFixedWidth(116)
        self.browseBtnFips.setFixedHeight(30)
        self.browseBtnFips.clicked.connect(self.getfilesFips)
        self.lineEditFips = QLineEdit(self)
        self.lineEditFips.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditFips.setFixedHeight(30)
        self.windowLayout.addWidget(self.labelFips, 21, 0)
        self.windowLayout.addWidget(self.browseBtnFips, 21, 1)
        self.windowLayout.addWidget(self.lineEditFips, 21, 2, 1, 3)

        # Advanced Options Label MOVES
        self.advOptionsLabelM = QLabel()
        self.advOptionsLabelM.setText("Advanced Options")
        self.advOptionsLabelM.setFixedHeight(30)
        self.advOptionsLabelM.setObjectName("subTitleLabels")
        self.labelAdvOptionsMOVESArrow = QLabel()
        self.labelAdvOptionsMOVESArrow.setAlignment(QtCore.Qt.AlignCenter)
        pixmapLine = QPixmap('C:\Project\snehal/arrow.png')
        pixmap = pixmapLine.scaledToHeight(25)
        self.labelAdvOptionsMOVESArrow.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.windowLayout.addWidget(self.advOptionsLabelM, 22, 0, 1, 4)
        self.windowLayout.addWidget(self.labelAdvOptionsMOVESArrow)

        # Created UI element - Advanced Optiones below Line
        self.labelAdvOptionsLineM = QLabel()
        pixmapLine2 = QPixmap('C:\Project\snehal/line.png')
        pixmap2 = pixmapLine2.scaledToHeight(14)
        self.labelAdvOptionsLineM.setPixmap(pixmap2)
        self.resize(pixmap2.width(), pixmap2.height())
        self.windowLayout.addWidget(self.labelAdvOptionsLineM, 23, 0, 1, 5)

        # Created UI element No of Trucks used
        self.labelNoofTruck = QLabel()
        self.labelNoofTruck.setText("Number Of Trucks Used")
        self.labelNoofTruck.setObjectName("allLabels")
        self.labelNoofTruck.setAlignment(QtCore.Qt.AlignCenter)
        self.labelNoofTruck.setFixedHeight(30)
        self.labelNoofTruck.setFixedWidth(165)
        self.labelNoofTruck.setToolTip("Number of trucks used in a scenario")
        self.spinBoxNoofTruck = QSpinBox()
        self.spinBoxNoofTruck.setFixedWidth(116)
        self.spinBoxNoofTruck.setFixedHeight(30)
        self.spinBoxNoofTruck.setMinimum(1)
        self.spinBoxNoofTruck.setValue(1)
        self.windowLayout.addWidget(self.labelNoofTruck, 24, 0)
        self.windowLayout.addWidget(self.spinBoxNoofTruck, 24, 1, QtCore.Qt.AlignCenter)


        # Created UI element VMT per Truck
        self.labelVMTperTruck = QLabel()
        self.labelVMTperTruck.setText("VMT Per Truck")
        self.labelVMTperTruck.setObjectName("allLabels")
        self.labelVMTperTruck.setAlignment(QtCore.Qt.AlignCenter)
        self.labelVMTperTruck.setFixedHeight(30)
        self.labelVMTperTruck.setFixedWidth(165)
        self.labelVMTperTruck.setToolTip("Vehicle Miles Traveled calculated per Truck")
        self.lineEditVMTperTruck = QLineEdit(self)
        self.lineEditVMTperTruck.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditVMTperTruck.setFixedWidth(116)
        self.lineEditVMTperTruck.setFixedHeight(30)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 6)
        self.lineEditVMTperTruck.setValidator(self.onlyFlaot)
        self.lineEditVMTperTruck.setText("20")
        self.windowLayout.addWidget(self.labelVMTperTruck, 25, 0)
        self.windowLayout.addWidget(self.lineEditVMTperTruck, 25, 1)

        # Created UI element VMT Fractions
        self.labelVMTFraction = QLabel()
        self.labelVMTFraction.setText("VMT Fractions")
        self.labelVMTFraction.setToolTip("Fraction of VMT(Vehicle MilesTraveled) by road type (All must sum to 1)")
        self.labelVMTFraction.setFixedHeight(30)
        self.labelVMTFraction.setObjectName("subTitleLabels")
        self.labelVMTFractionsArrow = QLabel()
        self.labelVMTFractionsArrow.setAlignment(QtCore.Qt.AlignCenter)
        pixmapLine = QPixmap('C:\Project\snehal/arrow.png')
        pixmap = pixmapLine.scaledToHeight(25)
        self.labelVMTFractionsArrow.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.windowLayout.addWidget(self.labelVMTFraction, 26, 0, 1, 4)
        self.windowLayout.addWidget(self.labelVMTFractionsArrow)

        # Created UI element - VMT Fractions below Line MOVES
        self.vMTFractionLine = QLabel()
        pixmapLine3 = QPixmap('C:\Project\snehal/line.png')
        pixmap3 = pixmapLine3.scaledToHeight(14)
        self.vMTFractionLine.setPixmap(pixmap2)
        self.resize(pixmap3.width(), pixmap3.height())
        self.windowLayout.addWidget(self.vMTFractionLine, 27, 0, 1, 5)

        # Created UI element VMT - Rural Restricted
        self.labelRuralRes = QLabel()
        self.labelRuralRes.setText("Rural Restricted")
        self.labelRuralRes.setObjectName("allLabels")
        self.labelRuralRes.setAlignment(QtCore.Qt.AlignCenter)
        self.labelRuralRes.setFixedHeight(30)
        self.labelRuralRes.setFixedWidth(165)
        self.lineEditRuralRes = QLineEdit(self)
        self.lineEditRuralRes.setFixedWidth(100)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditRuralRes.setValidator(self.onlyFlaot)
        self.lineEditRuralRes.setText("0.3")
        self.windowLayout.addWidget(self.labelRuralRes, 28, 0)
        self.windowLayout.addWidget(self.lineEditRuralRes, 28, 1)

        # Created UI element VMT - Urban Restricted
        self.labelUrbanRes = QLabel()
        self.labelUrbanRes.setText("Urban Restricted")
        self.labelUrbanRes.setObjectName("allLabels")
        self.labelUrbanRes.setAlignment(QtCore.Qt.AlignCenter)
        self.labelUrbanRes.setFixedHeight(30)
        self.labelUrbanRes.setFixedWidth(165)
        self.lineEditUrbanRes = QLineEdit(self)
        self.lineEditUrbanRes.setFixedWidth(100)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditUrbanRes.setValidator(self.onlyFlaot)
        self.lineEditUrbanRes.setText("0.21")
        self.windowLayout.addWidget(self.labelUrbanRes, 28, 2)
        self.windowLayout.addWidget(self.lineEditUrbanRes, 28, 3)

        # Created UI element VMT - Rural Unrestricted
        self.labelRuralUnres = QLabel()
        self.labelRuralUnres.setText("Rural Unrestricted")
        self.labelRuralUnres.setObjectName("allLabels")
        self.labelRuralUnres.setAlignment(QtCore.Qt.AlignCenter)
        self.labelRuralUnres.setFixedHeight(30)
        self.labelRuralUnres.setFixedWidth(165)
        self.lineEditRuralUnres = QLineEdit(self)
        self.lineEditRuralUnres.setFixedWidth(100)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditRuralUnres.setValidator(self.onlyFlaot)
        self.lineEditRuralUnres.setText("0.28")
        self.windowLayout.addWidget(self.labelRuralUnres, 29, 0)
        self.windowLayout.addWidget(self.lineEditRuralUnres, 29, 1)


        # Created UI element VMT - Urban Unrestricted
        self.labelUrbanUnres = QLabel()
        self.labelUrbanUnres.setText("Urban Unrestricted")
        self.labelUrbanUnres.setObjectName("allLabels")
        self.labelUrbanUnres.setAlignment(QtCore.Qt.AlignCenter)
        self.labelUrbanUnres.setFixedHeight(30)
        self.labelUrbanUnres.setFixedWidth(165)
        self.lineEditUrbanUnres = QLineEdit()
        self.lineEditUrbanUnres.setFixedWidth(100)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditUrbanUnres.setValidator(self.onlyFlaot)
        self.lineEditUrbanUnres.setText("0.28")
        self.windowLayout.addWidget(self.labelUrbanUnres, 29, 2)
        self.windowLayout.addWidget(self.lineEditUrbanUnres, 29, 3)




    # CHeck for consistent input for year
    def handleItemPressedMoves(self, index):
        if str(self.comboBoxYearNon.currentText()) != str(self.comboBoxYear.currentText()):
            self.comboBoxYear.setStyleSheet(
                """QComboBox { background-color: red; color: white }""")

    # Functions used for Moves Path

    def getfilesMovesPath(self):
        fileNameMovesPath = QFileDialog.getExistingDirectory(self, "Browse")
        selectedFileNameMovesPath = str(fileNameMovesPath).split(',')
        self.lineEditMovesPath.setText(selectedFileNameMovesPath[0])



    # Functions used for Truck Capacity

    def getfilesTruckCapa(self):
        fileNameTruckCapa = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        selectedFileNameTruckCapa = fileNameTruckCapa[0].split("FPEAM/")
        self.lineEditTruckCapa.setText(selectedFileNameTruckCapa[1])

    # Functions used for AVFT

    def getfilesAVFT(self):
        fileNameAVFT = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        selectedFileNameAVFT = fileNameAVFT[0].split("FPEAM/")
        self.lineEditAVFT.setText(selectedFileNameAVFT[1])


    # Functions used for Fips

    def getfilesFips(self):
        fileNameFips = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        selectedFileNameFips = fileNameFips[0].split("FPEAM/")
        self.lineEditFips.setText(selectedFileNameFips[1])

    # Functions used for Moves Datafiles

    def getfilesDatafiles(self):
        fileNameDatafile = QFileDialog.getExistingDirectory(self, "Browse")
        selectedFileNameDatafile = str(fileNameDatafile).split(',')
        self.lineEditDatafiles.setText(selectedFileNameDatafile[0])


    def getEnteredText(self):
        self.enteredText.setText(self.lineEditVMTperTruck)

        #########################################################################################################################


        #### Nonroad Module   #####

    def setupUINonroad(self):
        # Nonroad tab created
        self.tabNonroad = QtWidgets.QWidget()

        # Nonroad tab added
        self.centralwidget.addTab(self.tabNonroad, "NONROAD")

        # Nonroad code start
        self.windowLayout = QGridLayout()
        self.windowLayout.setSpacing(15)
        self.windowLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.windowLayout.setColumnStretch(6, 1)
        self.windowLayout.setSpacing(15)

        self.tabNonroad.setLayout(self.windowLayout)

        # Created UI element - Title NONROAD
        self.labelTitleNONROAD = QLabel()
        self.labelTitleNONROAD.setText("NONROAD Configuration Options")
        self.labelTitleNONROAD.setObjectName("title")
        self.labelTitleNONROAD.setFixedHeight(39)
        self.labelTitleNONROAD.setAlignment(QtCore.Qt.AlignCenter)
        self.windowLayout.addWidget(self.labelTitleNONROAD, 0, 0, 1, 5)

        # Created UI element - Title Line NONROAD
        self.labelTitleNONROADLine = QLabel()
        pixmapLine = QPixmap('C:\Project\snehal/line.png')
        pixmap = pixmapLine.scaledToHeight(14)
        self.labelTitleNONROADLine.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.windowLayout.addWidget(self.labelTitleNONROADLine, 1, 0, 1, 5)

        # Created UI element Nonroad Datafiles
        self.labelDatafilesNon = QLabel()
        self.labelDatafilesNon.setObjectName("allLabels")
        self.labelDatafilesNon.setFixedHeight(30)
        self.labelDatafilesNon.setFixedWidth(160)
        self.labelDatafilesNon.setAlignment(QtCore.Qt.AlignCenter)
        self.labelDatafilesNon.setText("NONROAD Executabel Path")
        self.labelDatafilesNon.setToolTip("Select NONROAD output folder")
        self.browseBtnDatafilesNon = QPushButton("Browse", self)
        self.browseBtnDatafilesNon.setFixedWidth(116)
        self.browseBtnDatafilesNon.setFixedHeight(30)
        self.browseBtnDatafilesNon.clicked.connect(self.getfilesDatafilesNon)
        self.lineEditDatafilesNon = QLineEdit(self)
        self.lineEditDatafilesNon.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditDatafilesNon.setFixedHeight(30)
        self.windowLayout.addWidget(self.labelDatafilesNon, 2, 0)
        self.windowLayout.addWidget(self.browseBtnDatafilesNon, 2, 1)
        self.windowLayout.addWidget(self.lineEditDatafilesNon, 2, 2, 1, 4)

        # Database Connection Parameters Label NONROAD
        self.dbConnectionParaLabelN = QLabel()
        self.dbConnectionParaLabelN.setText("Database Connection Parameters")
        self.dbConnectionParaLabelN.setFixedHeight(30)
        self.dbConnectionParaLabelN.setObjectName("subTitleLabels")
        self.labelDbConnectionArrowN = QLabel()
        self.labelDbConnectionArrowN.setAlignment(QtCore.Qt.AlignCenter)
        pixmapLine = QPixmap('C:\Project\snehal/arrow.png')
        pixmap = pixmapLine.scaledToHeight(25)
        self.labelDbConnectionArrowN.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.windowLayout.addWidget(self.dbConnectionParaLabelN, 3, 0, 1, 4)
        self.windowLayout.addWidget(self.labelDbConnectionArrowN)

        # Created UI element - Advanced Optiones below Line NONROAD
        self.dbConnectionParaLineN = QLabel()
        pixmapLine1M = QPixmap('C:\Project\snehal/line.png')
        pixmap1M = pixmapLine1M.scaledToHeight(14)
        self.dbConnectionParaLineN.setPixmap(pixmap1M)
        self.resize(pixmap1M.width(), pixmap1M.height())
        self.windowLayout.addWidget(self.dbConnectionParaLineN, 4, 0, 1, 5)

        # Created UI element Database Host
        self.labelDbHostN = QLabel()
        self.labelDbHostN.setText("Database Host")
        self.labelDbHostN.setObjectName("allLabels")
        self.labelDbHostN.setAlignment(QtCore.Qt.AlignCenter)
        self.labelDbHostN.setFixedHeight(30)
        self.labelDbHostN.setFixedWidth(165)
        self.labelDbHostN.setToolTip("Enter the database host")
        self.lineEditDbHostN = QLineEdit(self)
        self.lineEditDbHostN.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditDbHostN.setFixedHeight(30)
        self.lineEditDbHostN.setFixedWidth(125)
        regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(regex)
        self.lineEditDbHostN.setValidator(validator)
        self.lineEditDbHostN.setText("localhost")
        self.windowLayout.addWidget(self.labelDbHostN, 5, 0)
        self.windowLayout.addWidget(self.lineEditDbHostN, 5, 1)

        # Created UI element Database Username
        self.labelDbUsernameN = QLabel()
        self.labelDbUsernameN.setText("Username")
        self.labelDbUsernameN.setObjectName("allLabels")
        self.labelDbUsernameN.setAlignment(QtCore.Qt.AlignCenter)
        self.labelDbUsernameN.setFixedHeight(30)
        self.labelDbUsernameN.setFixedWidth(165)
        self.labelDbUsernameN.setToolTip("Enter the username used for database connection")
        self.lineEditDbUsernameN = QLineEdit(self)
        self.lineEditDbUsernameN.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditDbUsernameN.setFixedHeight(30)
        self.lineEditDbUsernameN.setFixedWidth(125)
        self.lineEditDbUsernameN.setText("root")
        self.windowLayout.addWidget(self.labelDbUsernameN, 5, 2)
        self.windowLayout.addWidget(self.lineEditDbUsernameN, 5, 3)

        # Created UI element Database Name
        self.labelDbNameN = QLabel()
        self.labelDbNameN.setText("Database Name")
        self.labelDbNameN.setObjectName("allLabels")
        self.labelDbNameN.setAlignment(QtCore.Qt.AlignCenter)
        self.labelDbNameN.setFixedHeight(30)
        self.labelDbNameN.setFixedWidth(165)
        self.labelDbNameN.setToolTip("Enter database name")
        self.lineEditDbNameN = QLineEdit(self)
        self.lineEditDbNameN.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditDbNameN.setFixedHeight(30)
        self.lineEditDbNameN.setFixedWidth(125)
        self.lineEditDbNameN.setText("movesdb20151028")
        self.windowLayout.addWidget(self.labelDbNameN, 6, 0)
        self.windowLayout.addWidget(self.lineEditDbNameN, 6, 1)

        # Created UI element Database Password
        self.labelDbPwdN = QLabel()
        self.labelDbPwdN.setText("Password")
        self.labelDbPwdN.setObjectName("allLabels")
        self.labelDbPwdN.setAlignment(QtCore.Qt.AlignCenter)
        self.labelDbPwdN.setFixedHeight(30)
        self.labelDbPwdN.setFixedWidth(165)
        self.labelDbPwdN.setToolTip("Enter the password used for database connection")
        self.lineEditDbPwdN = QLineEdit(self)
        self.lineEditDbPwdN.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditDbPwdN.setFixedHeight(30)
        self.lineEditDbPwdN.setFixedWidth(125)
        self.lineEditDbPwdN.setEchoMode(QtGui.QLineEdit.Password)
        self.lineEditDbPwdN.show()
        self.lineEditDbPwdN.setText("root")
        self.windowLayout.addWidget(self.labelDbPwdN, 6, 2)
        self.windowLayout.addWidget(self.lineEditDbPwdN, 6, 3)

        #Data Label
        self.dataLabel = QLabel()
        self.dataLabel.setText("Data Labels")
        self.dataLabel.setFixedHeight(30)
        self.dataLabel.setObjectName("subTitleLabels")
        self.dataLabelArrow = QLabel()
        self.dataLabelArrow.setAlignment(QtCore.Qt.AlignCenter)
        pixmapLine = QPixmap('C:\Project\snehal/arrow.png')
        pixmap = pixmapLine.scaledToHeight(25)
        self.dataLabelArrow.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.windowLayout.addWidget(self.dataLabel, 7, 0, 1, 4)
        self.windowLayout.addWidget(self.dataLabelArrow)

        # Created UI element - Data Labels Line
        self.dataLabelLine = QLabel()
        pixmapLine1M = QPixmap('C:\Project\snehal/line.png')
        pixmap1M = pixmapLine1M.scaledToHeight(14)
        self.dataLabelLine.setPixmap(pixmap1M)
        self.resize(pixmap1M.width(), pixmap1M.height())
        self.windowLayout.addWidget(self.dataLabelLine, 8, 0, 1, 5)

        # Created UI element Feedstock Measure Type Nonroad
        self.labelFeedMeasureTypeNon = QLabel()
        self.labelFeedMeasureTypeNon.setObjectName("allLabels")
        self.labelFeedMeasureTypeNon.setFixedHeight(30)
        self.labelFeedMeasureTypeNon.setFixedWidth(160)
        self.labelFeedMeasureTypeNon.setAlignment(QtCore.Qt.AlignCenter)
        self.labelFeedMeasureTypeNon.setText("Feedstock Measure Type")
        self.labelFeedMeasureTypeNon.setToolTip("Enter Feedstock Measure Type identifier")
        self.lineEditFeedMeasureTypeNon = QLineEdit()
        self.lineEditFeedMeasureTypeNon.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditFeedMeasureTypeNon.setFixedHeight(30)
        self.lineEditFeedMeasureTypeNon.setFixedWidth(125)
        self.regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(self.regex)
        self.lineEditFeedMeasureTypeNon.setValidator(validator)
        # Set Default text
        self.lineEditFeedMeasureTypeNon.setText("harvested")
        self.windowLayout.addWidget(self.labelFeedMeasureTypeNon, 9, 0)
        self.windowLayout.addWidget(self.lineEditFeedMeasureTypeNon, 9, 1)

        # Created UI element Forestry Feedstock Names
        self.labelForestryNamesNon = QLabel()
        self.labelForestryNamesNon.setObjectName("allLabels")
        self.labelForestryNamesNon.setFixedHeight(30)
        self.labelForestryNamesNon.setFixedWidth(160)
        self.labelForestryNamesNon.setAlignment(QtCore.Qt.AlignCenter)
        self.labelForestryNamesNon.setText("Forestry Feedstock Name")
        self.labelForestryNamesNon.setToolTip("Different allocation indicators of forest feedstocks")
        self.lineEditForestryNamesNon = QLineEdit(self)
        self.lineEditForestryNamesNon.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditForestryNamesNon.setFixedHeight(30)
        self.lineEditForestryNamesNon.setFixedWidth(125)
        self.regex = QtCore.QRegExp("[a-z-A-Z_,]+")
        validator = QtGui.QRegExpValidator(self.regex)
        self.lineEditForestryNamesNon.setValidator(validator)
        self.lineEditForestryNamesNon.setText("forest residues, forest whole tree")
        self.windowLayout.addWidget(self.labelForestryNamesNon, 9, 2)
        self.windowLayout.addWidget(self.lineEditForestryNamesNon, 9, 3)

        # Created UI element Irrigation Feedstock Measure Type Nonroad
        self.labelFeedMeasureTypeIrrigNon = QLabel()
        self.labelFeedMeasureTypeIrrigNon.setObjectName("allLabels")
        self.labelFeedMeasureTypeIrrigNon.setFixedHeight(30)
        self.labelFeedMeasureTypeIrrigNon.setFixedWidth(160)
        self.labelFeedMeasureTypeIrrigNon.setAlignment(QtCore.Qt.AlignCenter)
        self.labelFeedMeasureTypeIrrigNon.setText("Irrigation Feedstock Measure Type")
        self.labelFeedMeasureTypeIrrigNon.setToolTip(
            "Production table of identifier for irrigation activity calculation")
        self.lineEditFeedMeasureTypeIrrigNon = QLineEdit()
        self.lineEditFeedMeasureTypeIrrigNon.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditFeedMeasureTypeIrrigNon.setFixedHeight(30)
        self.lineEditFeedMeasureTypeIrrigNon.setFixedWidth(125)
        self.regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(self.regex)
        self.lineEditFeedMeasureTypeIrrigNon.setValidator(validator)
        self.lineEditFeedMeasureTypeIrrigNon.setText("planted")
        self.windowLayout.addWidget(self.labelFeedMeasureTypeIrrigNon, 10, 0)
        self.windowLayout.addWidget(self.lineEditFeedMeasureTypeIrrigNon, 10, 1)


        # Created UI element Time Resource Name
        self.labelTimeResNamesNon = QLabel()
        self.labelTimeResNamesNon.setObjectName("allLabels")
        self.labelTimeResNamesNon.setFixedHeight(30)
        self.labelTimeResNamesNon.setFixedWidth(160)
        self.labelTimeResNamesNon.setAlignment(QtCore.Qt.AlignCenter)
        self.labelTimeResNamesNon.setText("Time Resource Name")
        self.labelTimeResNamesNon.setToolTip("Equipment table row identifier")
        self.lineEditTimeResNamesNon = QLineEdit()
        self.lineEditTimeResNamesNon.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditTimeResNamesNon.setFixedHeight(30)
        self.lineEditTimeResNamesNon.setFixedWidth(125)
        self.regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(self.regex)
        self.lineEditTimeResNamesNon.setValidator(validator)
        self.lineEditTimeResNamesNon.setText("time")
        self.windowLayout.addWidget(self.labelTimeResNamesNon, 10, 2)
        self.windowLayout.addWidget(self.lineEditTimeResNamesNon, 10, 3)

        # Created UI element Irrigation Feedstock Names
        self.labelIrrigationFeedNamesNon = QLabel()
        self.labelIrrigationFeedNamesNon.setObjectName("allLabels")
        self.labelIrrigationFeedNamesNon.setFixedHeight(30)
        self.labelIrrigationFeedNamesNon.setFixedWidth(160)
        self.labelIrrigationFeedNamesNon.setAlignment(QtCore.Qt.AlignCenter)
        self.labelIrrigationFeedNamesNon.setText("Irrigation Feedstock Name")
        self.labelIrrigationFeedNamesNon.setToolTip("List of irrigated feedstocks")
        self.lineEditFeedIrrigNamesNon = QLineEdit()
        self.lineEditFeedIrrigNamesNon.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditFeedIrrigNamesNon.setFixedHeight(30)
        self.lineEditFeedIrrigNamesNon.setFixedWidth(125)
        self.regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(self.regex)
        self.lineEditFeedIrrigNamesNon.setValidator(validator)
        self.lineEditFeedIrrigNamesNon.setText("corn garin")
        self.windowLayout.addWidget(self.labelIrrigationFeedNamesNon, 11, 0)
        self.windowLayout.addWidget(self.lineEditFeedIrrigNamesNon, 11, 1)

        # Custom Data Filepaths Label
        self.cusromDatafileLabel = QLabel()
        self.cusromDatafileLabel.setText("Custom Data Filepaths")
        self.cusromDatafileLabel.setFixedHeight(30)
        self.cusromDatafileLabel.setObjectName("subTitleLabels")
        self.customDatafileLabelArrow = QLabel()
        self.customDatafileLabelArrow.setAlignment(QtCore.Qt.AlignCenter)
        pixmapLine = QPixmap('C:\Project\snehal/arrow.png')
        pixmap = pixmapLine.scaledToHeight(25)
        self.customDatafileLabelArrow.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.windowLayout.addWidget(self.cusromDatafileLabel, 12, 0, 1, 4)
        self.windowLayout.addWidget(self.customDatafileLabelArrow)

        # Custom Data Filepaths Label Line
        self.customDatafileLabelLine = QLabel()
        pixmapLine1M = QPixmap('C:\Project\snehal/line.png')
        pixmap1M = pixmapLine1M.scaledToHeight(14)
        self.customDatafileLabelLine.setPixmap(pixmap1M)
        self.resize(pixmap1M.width(), pixmap1M.height())
        self.windowLayout.addWidget(self.customDatafileLabelLine, 13, 0, 1, 5)

        # Created UI element Region Nonroad Irrigation
        self.labelNonIrrig = QLabel()
        self.labelNonIrrig.setObjectName("allLabels")
        self.labelNonIrrig.setFixedHeight(30)
        self.labelNonIrrig.setFixedWidth(160)
        self.labelNonIrrig.setAlignment(QtCore.Qt.AlignCenter)
        self.labelNonIrrig.setText("Irrigation")
        self.labelNonIrrig.setToolTip("Select irrigation dataset")
        self.browseBtnNonIrrig = QPushButton("Browse", self)
        self.browseBtnNonIrrig.setFixedWidth(116)
        self.browseBtnNonIrrig.setFixedHeight(30)
        self.browseBtnNonIrrig.clicked.connect(self.getfilesNonIrrig)
        # Add Empty PlainText
        self.emptyPlainTextNonIrri = QLabel()
        self.emptyPlainTextNonIrri.setFixedWidth(90)
        self.lineEditNonIrrig = QLineEdit(self)
        self.lineEditNonIrrig.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditNonIrrig.setFixedHeight(30)
        self.lineEditNonIrrig.setFixedWidth(125)
        self.windowLayout.addWidget(self.labelNonIrrig, 14, 0)
        self.windowLayout.addWidget(self.browseBtnNonIrrig, 14, 1)
        self.windowLayout.addWidget(self.emptyPlainTextNonIrri, 14, 2)
        self.windowLayout.addWidget(self.lineEditNonIrrig, 14, 3)

        # Created UI element Region FIPs Map Nonroad
        self.labelFipsNon = QLabel()
        self.labelFipsNon.setObjectName("allLabels")
        self.labelFipsNon.setFixedHeight(30)
        self.labelFipsNon.setFixedWidth(160)
        self.labelFipsNon.setAlignment(QtCore.Qt.AlignCenter)
        self.labelFipsNon.setText("NONROAD Region to FIPS Map")
        self.labelFipsNon.setToolTip("Select Region FIPS Map (production region to Nonroad FIPS mapping) dataset")
        self.browseBtnFipsNon = QPushButton("Browse", self)
        self.browseBtnFipsNon.setFixedWidth(116)
        self.browseBtnFipsNon.setFixedHeight(30)
        self.browseBtnFipsNon.clicked.connect(self.getfilesFipsNon)
        # Add Empty PlainText
        self.emptyPlainTextNonRegFips = QLabel()
        self.emptyPlainTextNonRegFips.setFixedWidth(90)
        self.lineEditFipsNon = QLineEdit(self)
        self.lineEditFipsNon.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditFipsNon.setFixedHeight(30)
        self.lineEditFipsNon.setFixedWidth(125)
        self.windowLayout.addWidget(self.labelFipsNon, 15, 0)
        self.windowLayout.addWidget(self.browseBtnFipsNon, 15, 1)
        self.windowLayout.addWidget(self.emptyPlainTextNonRegFips, 15, 2)
        self.windowLayout.addWidget(self.lineEditFipsNon, 15, 3)

        # Operating Temperature Label
        self.opTempLabel = QLabel()
        self.opTempLabel.setText("Operating Temperature")
        self.opTempLabel.setFixedHeight(30)
        self.opTempLabel.setObjectName("subTitleLabels")
        self.opTempLabelArrow = QLabel()
        self.opTempLabelArrow.setAlignment(QtCore.Qt.AlignCenter)
        pixmapLine = QPixmap('C:\Project\snehal/arrow.png')
        pixmap = pixmapLine.scaledToHeight(25)
        self.opTempLabelArrow.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.windowLayout.addWidget(self.opTempLabel, 16, 0, 1, 4)
        self.windowLayout.addWidget(self.opTempLabelArrow)

        # Operating Temperature Label Line
        self.opTempLabelLine = QLabel()
        pixmapLine1M = QPixmap('C:\Project\snehal/line.png')
        pixmap1M = pixmapLine1M.scaledToHeight(14)
        self.opTempLabelLine.setPixmap(pixmap1M)
        self.resize(pixmap1M.width(), pixmap1M.height())
        self.windowLayout.addWidget(self.opTempLabelLine, 17, 0, 1, 5)

        # Created UI element Minimum Temperature
        self.labelMinTemp = QLabel()
        self.labelMinTemp.setObjectName("allLabels")
        self.labelMinTemp.setFixedHeight(30)
        self.labelMinTemp.setFixedWidth(160)
        self.labelMinTemp.setAlignment(QtCore.Qt.AlignCenter)
        self.labelMinTemp.setText("Minimum")
        self.lineEditMinTemp = QLineEdit(self)
        self.lineEditMinTemp.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditMinTemp.setFixedHeight(30)
        self.lineEditMinTemp.setFixedWidth(125)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditMinTemp.setValidator(self.onlyFlaot)
        self.lineEditMinTemp.setText("50")
        self.windowLayout.addWidget(self.labelMinTemp, 18, 0)
        self.windowLayout.addWidget(self.lineEditMinTemp, 18, 1)

        # Created UI element Average Temperature
        self.labelMeanTemp = QLabel()
        self.labelMeanTemp.setObjectName("allLabels")
        self.labelMeanTemp.setFixedHeight(30)
        self.labelMeanTemp.setFixedWidth(160)
        self.labelMeanTemp.setAlignment(QtCore.Qt.AlignCenter)
        self.labelMeanTemp.setText("Average")
        self.lineEditMeanTemp = QLineEdit(self)
        self.lineEditMeanTemp.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditMeanTemp.setFixedHeight(30)
        self.lineEditMeanTemp.setFixedWidth(125)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditMeanTemp.setValidator(self.onlyFlaot)
        self.lineEditMeanTemp.setText("60")
        self.windowLayout.addWidget(self.labelMeanTemp, 18, 2)
        self.windowLayout.addWidget(self.lineEditMeanTemp, 18, 3)

        # Created UI element Maximum Temperature
        self.labelMaxTemp = QLabel()
        self.labelMaxTemp.setObjectName("allLabels")
        self.labelMaxTemp.setFixedHeight(30)
        self.labelMaxTemp.setFixedWidth(160)
        self.labelMaxTemp.setAlignment(QtCore.Qt.AlignCenter)
        self.labelMaxTemp.setText("Maximum")
        self.lineEditMaxTemp = QLineEdit()
        self.lineEditMaxTemp.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditMaxTemp.setFixedHeight(30)
        self.lineEditMaxTemp.setFixedWidth(125)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditMaxTemp.setValidator(self.onlyFlaot)
        self.lineEditMaxTemp.setText("68.8")
        self.windowLayout.addWidget(self.labelMaxTemp, 19, 0)
        self.windowLayout.addWidget(self.lineEditMaxTemp, 19, 1)

        # Conversion Factors Label
        self.convFactorsLabel = QLabel()
        self.convFactorsLabel.setText("Conversion Factors")
        self.convFactorsLabel.setFixedHeight(30)
        self.convFactorsLabel.setObjectName("subTitleLabels")
        self.convFactorsLabelArrow = QLabel()
        self.convFactorsLabelArrow.setAlignment(QtCore.Qt.AlignCenter)
        pixmapLine = QPixmap('C:\Project\snehal/arrow.png')
        pixmap = pixmapLine.scaledToHeight(25)
        self.convFactorsLabelArrow.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.windowLayout.addWidget(self.convFactorsLabel, 20, 0, 1, 4)
        self.windowLayout.addWidget(self.convFactorsLabelArrow)

        #  Conversion Factors Label Line
        self.convFactorsLabelLine = QLabel()
        pixmapLine1M = QPixmap('C:\Project\snehal/line.png')
        pixmap1M = pixmapLine1M.scaledToHeight(14)
        self.convFactorsLabelLine.setPixmap(pixmap1M)
        self.resize(pixmap1M.width(), pixmap1M.height())
        self.windowLayout.addWidget(self.convFactorsLabelLine, 21, 0, 1, 5)

        # Created UI element Low Heating Value
        self.labelLowHeat = QLabel()
        self.labelLowHeat.setObjectName("allLabels")
        self.labelLowHeat.setFixedHeight(30)
        self.labelLowHeat.setFixedWidth(160)
        self.labelLowHeat.setAlignment(QtCore.Qt.AlignCenter)
        self.labelLowHeat.setText("Diesel Low Heating Value")
        self.labelLowHeat.setToolTip("Lower Heating Value for diesel fuel")
        self.lineEditLowHeat = QLineEdit(self)
        self.lineEditLowHeat.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditLowHeat.setFixedHeight(30)
        self.lineEditLowHeat.setFixedWidth(125)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 6)
        self.lineEditLowHeat.setValidator(self.onlyFlaot)
        self.lineEditLowHeat.setText("0.012845")
        self.windowLayout.addWidget(self.labelLowHeat, 22, 0)
        self.windowLayout.addWidget(self.lineEditLowHeat, 22, 1)

        # Created UI element Hydrocarbon to VOC Conversion Factor
        self.labelHydeo = QLabel()
        self.labelHydeo.setObjectName("allLabels")
        self.labelHydeo.setFixedHeight(30)
        self.labelHydeo.setFixedWidth(160)
        self.labelHydeo.setAlignment(QtCore.Qt.AlignCenter)
        self.labelHydeo.setText("Hydrocarbon to VOC")
        self.labelHydeo.setToolTip("VOC Conversion Factor for Hydrocarbon Emission components")
        self.lineEditHydro = QLineEdit()
        self.lineEditHydro.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditHydro.setFixedHeight(30)
        self.lineEditHydro.setFixedWidth(125)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 6)
        self.lineEditHydro.setValidator(self.onlyFlaot)
        self.lineEditHydro.setText("1.053")
        self.windowLayout.addWidget(self.labelHydeo, 22, 2)
        self.windowLayout.addWidget(self.lineEditHydro, 22, 3)

        # Created UI element NH3 Emission Factor
        self.labelNH3 = QLabel()
        self.labelNH3.setObjectName("allLabels")
        self.labelNH3.setFixedHeight(30)
        self.labelNH3.setFixedWidth(160)
        self.labelNH3.setAlignment(QtCore.Qt.AlignCenter)
        self.labelNH3.setText("NH3 Emission Factor")
        self.labelNH3.setToolTip("NH3 Emissionn Factor for diesel fuel")
        self.lineEditNH3 = QLineEdit(self)
        self.lineEditNH3.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditNH3.setFixedHeight(30)
        self.lineEditNH3.setFixedWidth(125)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 6)
        self.lineEditNH3.setValidator(self.onlyFlaot)
        self.lineEditNH3.setText("0.68")
        self.windowLayout.addWidget(self.labelNH3, 23, 0)
        self.windowLayout.addWidget(self.lineEditNH3, 23, 1)



        # Created UI element PM10 to PM2.5 Conversion Factor
        self.labelPM10 = QLabel()
        self.labelPM10.setObjectName("allLabels")
        self.labelPM10.setFixedHeight(30)
        self.labelPM10.setFixedWidth(160)
        self.labelPM10.setAlignment(QtCore.Qt.AlignCenter)
        self.labelPM10.setText("PM10 to PM2.5")
        self.labelPM10.setToolTip("PM10 to PM2.5 Conversion Factor")
        self.lineEditPM10 = QLineEdit(self)
        self.lineEditPM10.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditPM10.setFixedHeight(30)
        self.lineEditPM10.setFixedWidth(125)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 6)
        self.lineEditPM10.setValidator(self.onlyFlaot)
        self.lineEditPM10.setText("0.97")
        self.windowLayout.addWidget(self.labelPM10, 23, 2)
        self.windowLayout.addWidget(self.lineEditPM10, 23, 3)

        # Advanced Options Label
        self.advOptionsLabelN = QLabel()
        self.advOptionsLabelN.setText("Advanced Options")
        self.advOptionsLabelN.setFixedHeight(30)
        self.advOptionsLabelN.setObjectName("subTitleLabels")
        self.labelAdvOptionsArrowN = QLabel()
        self.labelAdvOptionsArrowN.setAlignment(QtCore.Qt.AlignCenter)
        pixmapLine = QPixmap('C:\Project\snehal/arrow.png')
        pixmap = pixmapLine.scaledToHeight(25)
        self.labelAdvOptionsArrowN.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.windowLayout.addWidget(self.advOptionsLabelN, 20, 0, 1, 4)
        self.windowLayout.addWidget(self.labelAdvOptionsArrowN)

        #  Advanced Options Label Line
        self.labelAdvOptionsLineN = QLabel()
        pixmapLine1M = QPixmap('C:\Project\snehal/line.png')
        pixmap1M = pixmapLine1M.scaledToHeight(14)
        self.labelAdvOptionsLineN.setPixmap(pixmap1M)
        self.resize(pixmap1M.width(), pixmap1M.height())
        self.windowLayout.addWidget(self.labelAdvOptionsLineN, 21, 0, 1, 5)

        # Created UI element Region Nonroad Encode Names
        self.labelNonEncodeNames = QLabel()
        self.labelNonEncodeNames.setObjectName("allLabels")
        self.labelNonEncodeNames.setFixedHeight(30)
        self.labelNonEncodeNames.setFixedWidth(160)
        self.labelNonEncodeNames.setAlignment(QtCore.Qt.AlignCenter)
        self.labelNonEncodeNames.setText("Encode Names")
        self.labelNonEncodeNames.setToolTip("Encode feedstock, tillage type and activity names")
        self.comboBoxEncodeNames = QComboBox(self)
        self.comboBoxEncodeNames.setFixedHeight(30)
        self.comboBoxEncodeNames.addItem("Yes")
        self.comboBoxEncodeNames.addItem("No")
        self.comboBoxEncodeNames.setCurrentText("Yes")
        self.windowLayout.addWidget(self.labelNonEncodeNames, 22, 0)
        self.windowLayout.addWidget(self.comboBoxEncodeNames, 22, 1)



        # Created UI element Year - Nonroad
        self.labelYearNon = QLabel()
        self.labelYearNon.setObjectName("allLabels")
        self.labelYearNon.setFixedHeight(30)
        self.labelYearNon.setFixedWidth(160)
        self.labelYearNon.setAlignment(QtCore.Qt.AlignCenter)
        self.labelYearNon.setText("NONROAD Year")
        self.labelYearNon.setToolTip("Start year of equipment")
        self.comboBoxYearNon = QComboBox(self)
        self.comboBoxYearNon.setFixedHeight(30)
        for i in range(2018, 1990, -1):
            self.number = i
            self.comboBoxYearNon.addItem(str(i))
        self.index = self.comboBoxYearNon.findText("2017")
        self.comboBoxYearNon.setCurrentIndex(self.index)
        self.labelYearNonErrorMsg = QLabel()
        self.labelYearNonErrorMsg.setObjectName("yearErrorMsg")
        self.labelYearNonErrorMsg.setFixedHeight(30)
        self.labelYearNonErrorMsg.setText("")
        self.windowLayout.addWidget(self.labelYearNon, 23, 0)
        self.windowLayout.addWidget(self.comboBoxYearNon, 23, 1)
        self.windowLayout.addWidget(self.labelYearNonErrorMsg, 23, 2)
        # Check whether Moves year matches with Nonroad year
        self.comboBoxYearNon.currentIndexChanged.connect(self.handleItemPressed)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 24, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 25, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 26, 0)

        # Add Empty PlainText
        self.emptyPlainText2 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText2, 27, 0)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 28, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 29, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 30, 0)

    # CHeck for consistent input for year
    def handleItemPressed(self, index):

        fieldValues = set()
        fieldNames = []

        if self.tabMoves.isEnabled():
            fieldValues.add(self.comboBoxYear.currentText())
            fieldNames.append("MOVES")

        if self.tabNonroad.isEnabled():
            fieldValues.add(self.comboBoxYearNon.currentText())
            fieldNames.append("NONROAD")

        if len(fieldValues) == 1:
            self.comboBoxYearNon.setStyleSheet("border: 1px solid black;color: black ")
            self.comboBoxYear.setStyleSheet("border: 1px solid black;color: black ")
            self.labelYearErrorMsg.setText("")
            self.labelYearNonErrorMsg.setText("")

        else:
            self.comboBoxYearNon.setStyleSheet("border: 2px solid red;color: red ")
            self.comboBoxYear.setStyleSheet("border: 2px solid red;color: red ")
            self.labelYearErrorMsg.setStyleSheet("color: red ")
            self.labelYearNonErrorMsg.setStyleSheet("color: red ")

            tabsNamesInSentence = ""
            if len(fieldNames) == 1:
                tabsNamesInSentence = fieldNames[0]
            elif len(fieldNames) > 1:
                tabsNamesInSentence = tabsNamesInSentence.join(fieldNames[0]) + " and " + fieldNames[1]
            message = "Values for Feedstock Measure Type should be same for tabs: " + tabsNamesInSentence
            print(message)
            self.labelYearErrorMsg.setText(message)
            self.labelYearNonErrorMsg.setText(message)


    # Functions used for Moves Datafiles

    def getfilesDatafilesNon(self):
        fileName = QFileDialog.getExistingDirectory(self, "Browse")
        selectedFileName = str(fileName).split(',')
        self.lineEditDatafilesNon.setText(selectedFileName[0])

    # Functions used for Fips Nonroad

    def getfilesFipsNon(self):
        fileNameFipsNon = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        selectedFileNameFipsNon = fileNameFipsNon[0].split("FPEAM/")
        self.lineEditFipsNon.setText(selectedFileNameFipsNon[1])

    # Functions used for Nonroad Irrigation

    def getfilesNonIrrig(self):
        fileNameNonEq = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        selectedFileNameNonEq = fileNameNonEq[0].split("FPEAM/")
        self.lineEditNonIrrig.setText(selectedFileNameNonEq[1])

    ###########################################################################################################################################################

    #####    EmissionFactors Module   ######


    def setupUIEmissionFactors(self):
        # Emission Factors tab created
        self.tabEmissionFactors = QtWidgets.QWidget()

        # Emission Factors tab added
        self.centralwidget.addTab(self.tabEmissionFactors, "EMISSION FACTORS")

        # Emission Factors code start
        self.windowLayout = QGridLayout()
        self.windowLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.windowLayout.setColumnStretch(6, 1)
        self.windowLayout.setSpacing(15)

        self.tabEmissionFactors.setLayout(self.windowLayout)

        # Created UI element - Title EF
        self.labelTitleEF = QLabel()
        self.labelTitleEF.setText("Emission Factors Configuration Options")
        self.labelTitleEF.setObjectName("title")
        self.labelTitleEF.setFixedHeight(39)
        self.labelTitleEF.setAlignment(QtCore.Qt.AlignCenter)
        self.windowLayout.addWidget(self.labelTitleEF, 0, 0, 1, 5)

        # Created UI element - Title Line EF
        self.labelTitleEFLine = QLabel()
        pixmapLine = QPixmap('C:\Project\snehal/line.png')
        pixmap = pixmapLine.scaledToHeight(14)
        self.labelTitleEFLine.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.windowLayout.addWidget(self.labelTitleEFLine, 1, 0, 1, 5)

        # Created UI element Feedstock Measure Type Emission Factors
        self.labelFeedMeasureTypeEF = QLabel()
        self.labelFeedMeasureTypeEF.setObjectName("allLabels")
        self.labelFeedMeasureTypeEF.setFixedHeight(30)
        self.labelFeedMeasureTypeEF.setFixedWidth(160)
        self.labelFeedMeasureTypeEF.setAlignment(QtCore.Qt.AlignCenter)
        self.labelFeedMeasureTypeEF.setText("Feedstock Measure Type")
        self.labelFeedMeasureTypeEF.setToolTip("Production table Identifier")
        self.lineEditFeedMeasureTypeEF = QLineEdit()
        self.lineEditFeedMeasureTypeEF.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditFeedMeasureTypeEF.setFixedWidth(116)
        self.lineEditFeedMeasureTypeEF.setFixedHeight(30)
        regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(regex)
        self.lineEditFeedMeasureTypeEF.setValidator(validator)
        self.lineEditFeedMeasureTypeEF.setText("harvested")
        self.windowLayout.addWidget(self.labelFeedMeasureTypeEF, 2, 0)
        self.windowLayout.addWidget(self.lineEditFeedMeasureTypeEF, 2, 1)

        # Custom Data Filepaths Label EF
        self.customDataFilepathLabelEF = QLabel()
        self.customDataFilepathLabelEF.setText("Custom Data Filepaths")
        self.customDataFilepathLabelEF.setFixedHeight(30)
        self.customDataFilepathLabelEF.setObjectName("subTitleLabels")
        self.labeCustomDatafilesArrowEF = QLabel()
        self.labeCustomDatafilesArrowEF.setAlignment(QtCore.Qt.AlignCenter)
        pixmapLine = QPixmap('C:\Project\snehal/arrow.png')
        pixmap = pixmapLine.scaledToHeight(25)
        self.labeCustomDatafilesArrowEF.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.windowLayout.addWidget(self.customDataFilepathLabelEF, 3, 0, 1, 4)
        self.windowLayout.addWidget(self.labeCustomDatafilesArrowEF)

        # Created UI element - Custom Dtatfiles below Line
        self.labelCustomDatafilsLine = QLabel()
        pixmapLine1 = QPixmap('C:\Project\snehal/line.png')
        pixmap1 = pixmapLine1.scaledToHeight(14)
        self.labelCustomDatafilsLine.setPixmap(pixmap1)
        self.resize(pixmap1.width(), pixmap1.height())
        self.windowLayout.addWidget(self.labelCustomDatafilsLine, 4, 0, 1, 5)


        # Created UI element Emission Factors
        self.labelEmiFact = QLabel()
        self.labelEmiFact.setObjectName("allLabels")
        self.labelEmiFact.setFixedHeight(30)
        self.labelEmiFact.setFixedWidth(160)
        self.labelEmiFact.setAlignment(QtCore.Qt.AlignCenter)
        self.labelEmiFact.setText("Emission Factors")
        self.labelEmiFact.setToolTip("Emission Factors as lb pollutant per lb resource subtype")
        self.browseBtnEmiFact = QPushButton("Browse", self)
        self.browseBtnEmiFact.setFixedWidth(116)
        self.browseBtnEmiFact.setFixedHeight(30)
        self.browseBtnEmiFact.clicked.connect(self.getfilesEmiFact)
        self.lineEditEmiFact = QLineEdit(self)
        self.lineEditEmiFact.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditEmiFact.setFixedHeight(30)
        self.windowLayout.addWidget(self.labelEmiFact, 5, 0)
        self.windowLayout.addWidget(self.browseBtnEmiFact, 5, 1)
        self.windowLayout.addWidget(self.lineEditEmiFact, 5, 2,1, 3)

        # Created UI element Resource Distribution
        self.labelResDist = QLabel()
        self.labelResDist.setObjectName("allLabels")
        self.labelResDist.setFixedHeight(30)
        self.labelResDist.setFixedWidth(160)
        self.labelResDist.setAlignment(QtCore.Qt.AlignCenter)
        self.labelResDist.setText("Resource Distribution")
        self.labelResDist.setToolTip("Resource subtype distribution for all resources")
        self.browseBtnReDist = QPushButton("Browse", self)
        self.browseBtnReDist.setFixedWidth(116)
        self.browseBtnReDist.setFixedHeight(30)
        self.browseBtnReDist.clicked.connect(self.getfilesResDist)
        self.lineEditResDist = QLineEdit(self)
        self.lineEditResDist.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditResDist.setFixedHeight(30)
        self.windowLayout.addWidget(self.labelResDist, 6, 0)
        self.windowLayout.addWidget(self.browseBtnReDist, 6, 1)
        self.windowLayout.addWidget(self.lineEditResDist, 6, 2, 1, 3)

        # Add Empty PlainText
        self.emptyPlainText2 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText2, 7, 0)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 8, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 9, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 10, 0)

        # Add Empty PlainText
        self.emptyPlainText2 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText2, 11, 0)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 12, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 13, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 14, 0)

        # Add Empty PlainText
        self.emptyPlainText2 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText2, 15, 0)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 16, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 17, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 18, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 19, 0)

        # Add Empty PlainText
        self.emptyPlainText2 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText2, 20, 0)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 21, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 22, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 23, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 24, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 25, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 26, 0)

        # Add Empty PlainText
        self.emptyPlainText2 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText2, 27, 0)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 28, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 29, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 30, 0)

    # Functions used for Emission Factors

    def getfilesEmiFact(self):
        fileNameTruckCapa = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        selectedFileNameTruckCapa = fileNameTruckCapa[0].split("FPEAM/")
        self.lineEditEmiFact.setText(selectedFileNameTruckCapa[1])

    # Functions used for Resource Distribution

    def getfilesResDist(self):
        fileNameTruckCapa = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        selectedFileNameTruckCapa = fileNameTruckCapa[0].split("FPEAM/")
        self.lineEditResDist.setText(selectedFileNameTruckCapa[1])


    ###################################################################################################################################################################


    #####    Fugitive Dust  Module   ######

    def setupUIFugitiveDust(self):
        # Fugitive Dust tab created
        self.tabFugitiveDust = QtWidgets.QWidget()

        # Fugitive Dust tab added
        self.centralwidget.addTab(self.tabFugitiveDust, "FUGITIVE DUST")

        # Fugitive Dust code start
        self.windowLayout = QGridLayout()
        self.windowLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.windowLayout.setColumnStretch(6, 1)
        self.windowLayout.setSpacing(15)

        # Created UI element - Title FD
        self.labelTitleFD = QLabel()
        self.labelTitleFD.setText("Fugitive Dust Configuration Options")
        self.labelTitleFD.setObjectName("title")
        self.labelTitleFD.setFixedHeight(39)
        self.labelTitleFD.setAlignment(QtCore.Qt.AlignCenter)
        self.windowLayout.addWidget(self.labelTitleFD, 0, 0, 1, 5)

        # Created UI element - Title Line FD
        self.labelTitleFDLine = QLabel()
        pixmapLine = QPixmap('C:\Project\snehal/line.png')
        pixmap = pixmapLine.scaledToHeight(14)
        self.labelTitleFDLine.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.windowLayout.addWidget(self.labelTitleFDLine, 1, 0, 1, 5)

        self.tabFugitiveDust.setLayout(self.windowLayout)

        # Created UI element Feedstock Measure Type - Fugitive Dust
        self.labelFeedMeasureTypeFD = QLabel()
        self.labelFeedMeasureTypeFD.setObjectName("allLabels")
        self.labelFeedMeasureTypeFD.setFixedHeight(30)
        self.labelFeedMeasureTypeFD.setFixedWidth(160)
        self.labelFeedMeasureTypeFD.setAlignment(QtCore.Qt.AlignCenter)
        self.labelFeedMeasureTypeFD.setText("Feedstock Measure Type")
        self.labelFeedMeasureTypeFD.setToolTip("Production table identifier ")
        self.lineEditFeedMeasureTypeFD = QLineEdit(self)
        self.lineEditFeedMeasureTypeFD.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditFeedMeasureTypeFD.setFixedWidth(116)
        self.lineEditFeedMeasureTypeFD.setFixedHeight(30)
        regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(regex)
        self.lineEditFeedMeasureTypeFD.setValidator(validator)
        self.lineEditFeedMeasureTypeFD.setText("harvested")
        self.windowLayout.addWidget(self.labelFeedMeasureTypeFD, 2, 0)
        self.windowLayout.addWidget(self.lineEditFeedMeasureTypeFD, 2, 1)

        # Custom Data Filepaths Label FD
        self.customDataFilepathLabelFD = QLabel()
        self.customDataFilepathLabelFD.setText("Custom Data Filepaths")
        self.customDataFilepathLabelFD.setFixedHeight(30)
        self.customDataFilepathLabelFD.setObjectName("subTitleLabels")
        self.labeCustomDatafilesArrowFD = QLabel()
        self.labeCustomDatafilesArrowFD.setAlignment(QtCore.Qt.AlignCenter)
        pixmapLine = QPixmap('C:\Project\snehal/arrow.png')
        pixmap = pixmapLine.scaledToHeight(25)
        self.labeCustomDatafilesArrowFD.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.windowLayout.addWidget(self.customDataFilepathLabelFD, 3, 0, 1, 4)
        self.windowLayout.addWidget(self.labeCustomDatafilesArrowFD)

        # Created UI element - Custom Dtatfiles below Line
        self.labelCustomDatafilsLine = QLabel()
        pixmapLine1 = QPixmap('C:\Project\snehal/line.png')
        pixmap1 = pixmapLine1.scaledToHeight(14)
        self.labelCustomDatafilsLine.setPixmap(pixmap1)
        self.resize(pixmap1.width(), pixmap1.height())
        self.windowLayout.addWidget(self.labelCustomDatafilsLine, 4, 0, 1, 5)

        # Created UI element Emission Factors - Fugitive Dust
        self.labelEmiFactFD = QLabel()
        self.labelEmiFactFD.setObjectName("allLabels")
        self.labelEmiFactFD.setFixedHeight(30)
        self.labelEmiFactFD.setFixedWidth(160)
        self.labelEmiFactFD.setAlignment(QtCore.Qt.AlignCenter)
        self.labelEmiFactFD.setText("Emission Factors")
        self.labelEmiFactFD.setToolTip("Pollutant emission factors for resources")
        self.browseBtnEmiFactFD = QPushButton("Browse", self)
        self.browseBtnEmiFactFD.setFixedWidth(116)
        self.browseBtnEmiFactFD.setFixedHeight(30)
        self.browseBtnEmiFactFD.clicked.connect(self.getfilesEmiFactFD)
        self.lineEditEmiFactFD = QLineEdit(self)
        self.lineEditEmiFactFD.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditEmiFactFD.setFixedHeight(30)
        self.windowLayout.addWidget(self.labelEmiFactFD, 5, 0)
        self.windowLayout.addWidget(self.browseBtnEmiFactFD, 5, 1)
        self.windowLayout.addWidget(self.lineEditEmiFactFD, 5, 2, 1, 3)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 6, 0)

        # Add Empty PlainText
        self.emptyPlainText2 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText2, 7, 0)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 8, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 9, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 10, 0)

        # Add Empty PlainText
        self.emptyPlainText2 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText2, 11, 0)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 12, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 13, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 14, 0)

        # Add Empty PlainText
        self.emptyPlainText2 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText2, 15, 0)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 16, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 17, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 18, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 19, 0)

        # Add Empty PlainText
        self.emptyPlainText2 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText2, 20, 0)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 21, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 22, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 23, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 24, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 25, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 26, 0)

        # Add Empty PlainText
        self.emptyPlainText2 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText2, 27, 0)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 28, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 29, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 30, 0)


    # Functions used for Emission Factors - - Fugitive Dust

    def getfilesEmiFactFD(self):
        fileNameTruckCapaFD = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        selectedFileNameTruckCapaFD = fileNameTruckCapaFD[0].split("FPEAM/")
        self.lineEditEmiFactFD.setText(selectedFileNameTruckCapaFD[1])

    def rresetFields(self):


        # self.attributeValueObj.logContents = ""
        # self.attributeValueObj.streamGenerated = io.StringIO()

        # # FPEAM home page - Attribute Initialization
        # self.lineEditScenaName.setText("")
        # self.lineEditProjectPath.setText("")
        # self.checkBoxMoves.setChecked(True)
        # self.checkBoxNonroad.setChecked(True)
        # self.checkBoxEmissionFactors.setChecked(True)
        # self.checkBoxFugitiveDust.setChecked(True)
        # self.index = self.comboBoxVerbosityLevel.findText("DEBUG")
        # self.comboBoxVerbosityLevel.setCurrentIndex(self.index)
        # self.lineEditEq.setText("data/equipment/bts16_equipment.csv")
        # self.lineEditProd.setText("data/production/production_2015_bc1060.csv")
        # self.lineEditFedLossFact.setText("data/inputs/feedstock_loss_factors.csv")
        # self.lineEditTransGraph.setText("data/inputs/transportation_graph.csv")
        # self.index = self.comboBoxBF.findText("Yes")
        # self.comboBoxBF.setCurrentIndex(self.index)
        # self.index = self.comboBoxRE.findText("Yes")
        # self.comboBoxRE.setCurrentIndex(self.index)
        #
        # # Fugitive Dust module - Attribute Initialization
        # self.lineEditFeedMeasureTypeFD = "harvested"
        # self.lineEditEmiFactFD = "../data/inputs/fugitive_dust_emission_factors.csv"
        #
        # # Emission Factors Module - Attribute Initialization
        # self.lineEditFeedMeasureTypeEF = "harvested"
        # self.lineEditEmiFact = 'data/inputs/emission_factors.csv'
        # self.lineEditResDist = 'data/inputs/resource_distribution.csv'

        # # Nonroad Module - Attribute Initialization
        # self.yearNonroad = 2017
        # self.feedstockMeasureTypeNon = "harvested"
        # self.timeResourceNameNon = "time"
        # self.forestryFeedstockNames = 'forest whole tree', 'forest residues'
        # self.regionFipsMapNonroad = "../data/inputs/region_fips_map.csv"
        # self.nonroadDatafilesPath = "C:/Nonroad"
        # self.tempMin = 50.0
        # self.tempMax = 68.8
        # self.tempMean = 60.0
        # self.dieselLHV = 0.12845
        # self.dieselNh3Ef = 0.68
        # self.dieselThcVocConversion = 1.053
        # self.dieselPm10topm25 = 0.97
        # self.irrigationFeedstockMeasureType = "planted"
        # self.irrigatedFeedstockNames = "corn grain"
        # self.irrigation = "../data/inputs/irrigation.csv"
        # self.encodeNames = True
        #
        # # Moves Module - Attribute Initialization
        # self.aggegationLevel = "By County"
        # self.cachedResults = "Yes"
        # self.feedstockMeasureType = "production"
        # self.vMTPerTruck = 20
        # self.noOfTrucksUsed = 1
        # self.yearMoves = 2017
        # self.dbHost = "localhost"
        # self.dbUsername = "root"
        # self.dbName = "movesdb20151028"
        # self.dbPwd = "root"
        # self.movesDatafilesPath = "C:\MOVESdata"
        # self.movesPath = "C:\MOVES2014a"
        # self.truckCapacity = "../data/inputs/truck_capacity.csv"
        # self.avft = "../data/inputs/avft.csv"
        # self.regionFipsMapMoves = "../data/inputs/region_fips_map.csv"
        # self.ruralRestricted = 0.30
        # self.ruralUnrestricted = 0.28
        # self.urbanRestricted = 0.21
        # self.urbanUnrestricted = 0.21
        # self.month = 10
        # self.date = 5
        # self.beginningHr = 7
        # self.endingHr = 18
        # self.dayType = 5



        print("-------------------------Reset clicked")

###################################################################

    # Run Button
    def runTheSelectedModules(self):

        self.attributeValueObj = AttributeValueStorage()

        tmpFolder = tempfile.mkdtemp()

        # check if scenario name and project path is entered or not
        if self.lineEditProjectPath.text() == "":
            self.lineEditProjectPath.setStyleSheet("border: 2px solid red;")
            self.lineEditScenaName.setStyleSheet("border: 2px solid red;")
            return
        else:


            # FPEAM Home Page attributes value initialization

            self.attributeValueObj.scenarioName = self.lineEditScenaName.text().strip()
            self.attributeValueObj.projectPath = self.lineEditProjectPath.text().strip()

            # Check which module is selected
            self.selected_module_string = ""
            if self.checkBoxMoves.isChecked():
                #attributeValueObj.module = self.selected_module_list.append(self.checkBoxMoves.text())
                self.selected_module_string += "'" + self.checkBoxMoves.text() + "'"
                self.self.attributeValueObj.module = self.selected_module_string
                self.selected_module_string += ", "
            if self.checkBoxNonroad.isChecked():

                #attributeValueObj.module = self.selected_module_list.append(self.checkBoxNonroad.text())
                self.selected_module_string += "'" + self.checkBoxNonroad.text() + "'"
                self.attributeValueObj.module = self.selected_module_string
                self.selected_module_string += ", "
            if self.checkBoxEmissionFactors.isChecked():

                #attributeValueObj.module = self.selected_module_list.append(self.checkBoxEmissionFactors.text())
                self.selected_module_string +=  "'" + self.checkBoxEmissionFactors.text() + "'"
                self.attributeValueObj.module = self.selected_module_string
                self.selected_module_string += ", "
            if self.checkBoxFugitiveDust.isChecked():

                #attributeValueObj.module = "'" + self.selected_module_list.append(self.checkBoxFugitiveDust.text())
                self.selected_module_string +=  "'" + self.checkBoxFugitiveDust.text() + "'"
                self.attributeValueObj.module = self.selected_module_string


            changedVerboLoggerLevel = self.comboBoxVerbosityLevel.currentText()
            if changedVerboLoggerLevel:
                self.attributeValueObj.loggerLevel = changedVerboLoggerLevel

            changedBackfill = self.comboBoxBF.currentText()
            if changedBackfill:
                if changedBackfill == "No":
                    changedBackfill = False
                else:
                    changedBackfill = True
                self.attributeValueObj.backfill = changedBackfill

            changedRouterEngine = self.comboBoxRE.currentText()
            if changedRouterEngine:
                if changedRouterEngine == "No":
                    changedRouterEngine = False
                else:
                    changedRouterEngine = True
                self.attributeValueObj.useRouterEngine = changedRouterEngine

            changedEqPath = self.lineEditEq.text().strip()
            if changedEqPath:
                self.attributeValueObj.equipment = changedEqPath

            changedProdPath = self.lineEditProd.text().strip()
            if changedProdPath:
                self.attributeValueObj.production = changedProdPath

            changedFeedLossFactPath = self.lineEditFedLossFact.text().strip()
            if changedFeedLossFactPath:
                self.attributeValueObj.feedstockLossFactors = changedFeedLossFactPath

            changedTranGraphPath = self.lineEditTransGraph.text().strip()
            if changedTranGraphPath:
                self.attributeValueObj.transportationGraph = changedTranGraphPath


            ###############################################################################################################

            # Moves attributes value initialization

            changedAggLevel = self.comboBoxAggLevel.currentText()
            if changedAggLevel:
                self.attributeValueObj.aggegationLevel = changedAggLevel

            changedcachedResults = self.comboBoxCachedResUse.currentText()
            if changedcachedResults:
                self.attributeValueObj.cachedResults = changedcachedResults

            changedFeedstockMeasureTypeMoves = self.lineEditFeedMeasureType.text().strip()
            if changedFeedstockMeasureTypeMoves:
                self.attributeValueObj.feedstockMeasureTypeMoves = changedFeedstockMeasureTypeMoves

            changedVMTPerTruck = self.lineEditVMTperTruck.text().strip()
            if changedVMTPerTruck:
                self.attributeValueObj.vMTPerTruck = changedVMTPerTruck

            changedNoOfTrucksUsed = self.spinBoxNoofTruck.text()
            if changedNoOfTrucksUsed:
                self.attributeValueObj.noOfTrucksUsed = changedNoOfTrucksUsed

            changedYearMoves = self.comboBoxYear.currentText()
            if changedYearMoves:
                self.attributeValueObj.yearMoves = changedYearMoves

            changedMonth = self.comboBoxMonth.currentText()
            if changedMonth:
                self.attributeValueObj.month = changedMonth

            changedDbHost = self.lineEditDbHost.text().strip()
            if changedDbHost:
                self.attributeValueObj.dbHost = changedDbHost

            changedDbUsername = self.lineEditDbUsername.text().strip()
            if changedDbUsername:
                self.attributeValueObj.dbUsername = changedDbUsername

            changedDbName = self.lineEditDbName.text().strip()
            if changedDbName:
                self.attributeValueObj.dbName = changedDbName

            changedDbPwd = self.lineEditDbPwd.text().strip()
            if changedDbPwd:
                self.attributeValueObj.dbPwd = changedDbPwd

            changedDate = self.comboBoxDate.currentText()
            if changedDate:
                self.attributeValueObj.date = changedDate

            changedBegHr = self.comboBoxBegHr.currentText()
            if changedBegHr:
                self.attributeValueObj.beginningHr = changedBegHr

            changedEndHr = self.comboBoxEndHr.currentText()
            if changedEndHr:
                self.attributeValueObj.endingHr = changedEndHr

            if self.comboBoxDayType.currentText() == "Weekday":
                self.attributeValueObj.dayType = "5"
            else:
                self.attributeValueObj.dayType = "2"
            print("---------------------------", self.attributeValueObj.dayType)

            # changedDayType = self.comboBoxDayType.currentText()
            # if changedDayType:
            #     self.attributeValueObj.dayType = changedDayType

            changedTruckCapacityPath = self.lineEditTruckCapa.text().strip()
            if changedTruckCapacityPath:
                self.attributeValueObj.truckCapacity = changedTruckCapacityPath

            changedAvftPath = self.lineEditAVFT.text().strip()
            if changedAvftPath:
                self.attributeValueObj.avft = changedAvftPath

            changedFipsMapNovesPath = self.lineEditFips.text().strip()
            if changedFipsMapNovesPath:
                self.attributeValueObj.regionFipsMapMoves = changedFipsMapNovesPath

            changedDatafilesMovesPath = self.lineEditDatafiles.text().strip()
            if changedDatafilesMovesPath:
                self.attributeValueObj.movesDatafilesPath = changedDatafilesMovesPath

            changedRuralRes = self.lineEditRuralRes.text().strip()
            if changedRuralRes:
                self.attributeValueObj.ruralRestricted = changedRuralRes

            changedRuralUnres = self.lineEditRuralUnres.text().strip()
            if changedRuralUnres:
                self.attributeValueObj.ruralUnrestricted = changedRuralUnres

            changedUrbanRes = self.lineEditUrbanRes.text().strip()
            if changedUrbanRes:
                self.attributeValueObj.urbanRestricted = changedUrbanRes

            changedUrbanUnres = self.lineEditUrbanUnres.text().strip()
            if changedUrbanUnres:
                self.attributeValueObj.urbanUnrestricted = changedUrbanUnres

            ###############################################################################################################

            # Nonroad attributes value initialization

            changedYearNonroad = self.comboBoxYearNon.currentText()
            if changedYearNonroad:
                self.attributeValueObj.yearNonroad = changedYearNonroad

            changedFipsMapNon = self.lineEditFipsNon.text().strip()
            if changedFipsMapNon:
                self.attributeValueObj.regionFipsMapNonroad = changedFipsMapNon

            changedDatafilesNon = self.lineEditDatafilesNon.text().strip()
            if changedDatafilesNon:
                self.attributeValueObj.nonroadDatafilesPath = changedDatafilesNon

            changedIrrigNon = self.lineEditNonIrrig.text().strip()
            if changedIrrigNon:
                self.attributeValueObj.irrigation = changedIrrigNon


            changedEncodeName = self.comboBoxEncodeNames.currentText()
            if changedEncodeName:
                self.attributeValueObj.encodeNames = changedEncodeName

            changedFeedstockMeasureTypeNonroad = self.lineEditFeedMeasureTypeNon.text().strip()
            if changedFeedstockMeasureTypeNonroad:
                self.attributeValueObj.feedstockMeasureTypeNon = changedFeedstockMeasureTypeNonroad

            changedIrrigationFeedMeasureType = self.lineEditFeedMeasureTypeIrrigNon.text().strip()
            if changedIrrigationFeedMeasureType:
                self.attributeValueObj.irrigationFeedstockMeasureType = changedIrrigationFeedMeasureType

            changedIrrigationFeedNames = self.lineEditFeedIrrigNamesNon.text().strip()
            if changedIrrigationFeedNames:
                self.attributeValueObj.irrigatedFeedstockNames = changedIrrigationFeedNames

            changedTimeResName = self.lineEditTimeResNamesNon.text().strip()
            if changedTimeResName:
                self.attributeValueObj.timeResourceNameNon = changedTimeResName

            changedForestryFeedNames = self.lineEditForestryNamesNon.text().strip()
            if changedForestryFeedNames:
                self.attributeValueObj.forestryFeedstockNames = changedForestryFeedNames

            changedTempMin = self.lineEditMinTemp.text().strip()
            if changedTempMin:
                self.attributeValueObj.tempMin = changedTempMin

            changedTempMax = self.lineEditMaxTemp.text().strip()
            if changedTempMax:
                self.attributeValueObj.tempMax = changedTempMax

            changedTempMean = self.lineEditMeanTemp.text().strip()
            if changedTempMean:
                self.attributeValueObj.tempMean = changedTempMean

            changeddieselLHV = self.lineEditLowHeat.text().strip()
            if changeddieselLHV:
                self.attributeValueObj.dieselLHV = changeddieselLHV

            changeddieselNH3 = self.lineEditNH3.text().strip()
            if changeddieselNH3:
                self.attributeValueObj.dieselNh3Ef = changeddieselNH3

            changeddieselHydrotoVOC = self.lineEditHydro.text().strip()
            if changeddieselHydrotoVOC:
                self.attributeValueObj.tempMean = changeddieselHydrotoVOC

            changedPMConversionFact = self.lineEditPM10.text().strip()
            if changedPMConversionFact:
                self.attributeValueObj.dieselPm10topm25 = changedPMConversionFact


        ###############################################################################################################

            # Emission Factors attributs value Initialization

            changedFeedMeasureTypeFEF= self.lineEditFeedMeasureTypeEF.text().strip()
            if changedFeedMeasureTypeFEF:
                self.attributeValueObj.feedMeasureTypeEF = changedFeedMeasureTypeFEF

            changedEmissionFactEFPath = self.lineEditEmiFact.text().strip()
            if changedEmissionFactEFPath:
                self.attributeValueObj.emissionFactorsEF = changedEmissionFactEFPath

            changedResDistriEFPath = self.lineEditResDist.text().strip()
            if changedResDistriEFPath:
                self.attributeValueObj.resourceDistributionEF = changedResDistriEFPath

            ###############################################################################################################

            # Fugititve Dust attributes value initialization

            changedFeedMeasureTypeFD = self.lineEditFeedMeasureTypeFD.text().strip()
            if changedFeedMeasureTypeFD:
                self.attributeValueObj.feedMeasureTypeFD = changedFeedMeasureTypeFD

            changedEmissionFactFDPath = self.lineEditEmiFactFD.text().strip()
            if changedEmissionFactFDPath:
                self.attributeValueObj.emissionFactorsFD = changedEmissionFactFDPath


            ###############################################################################################################

            # Call config file creation function - working code
            # if self.checkBoxMoves.isChecked():
            #     movesConfigCreationObj = movesConfigCreation(tmpFolder)
            # if self.checkBoxNonroad.isChecked():
            #     nonroadConfigCreationObj = nonroadConfigCreation(tmpFolder)
            if self.checkBoxEmissionFactors.isChecked():
                emissionFactorsConfigCreationObj = emissionFactorsConfigCreation(tmpFolder, self.attributeValueObj)
            # if self.checkBoxFugitiveDust.isChecked():
            #     fugitiveDustConfigCreationObj = fugitiveDustConfigCreation(tmpFolder)
            runConfigObj = runConfigCreation(tmpFolder, self.attributeValueObj)

            # run FugitiveDust module
            command = "fpeam " + runConfigObj + " --emissionfactors_config " + emissionFactorsConfigCreationObj
            print(command)
            t = threading.Thread(target= runCommand , args = (runConfigObj , emissionFactorsConfigCreationObj, self.attributeValueObj, ))
            t.start()

            while t.is_alive():
                print("alive. Waiting for 1 second to recheck")
                time.sleep(1)

            t.join()

            # Display logs in result tab after completion of running
            self.centralwidget.setCurrentWidget(self.tabResult)

            # Set logs to Plaintext in Result tab
            self.plainTextLog.setPlainText(self.attributeValueObj.logContents)

            #Generate graph for MOVES module
            fileNameMoves = self.lineEditScenaName.text().strip() + "_raw.csv"
            dataframePathMOVES = os.path.join(self.lineEditProjectPath.text().strip(), fileNameMoves)
            df = pd.read_csv(dataframePathMOVES)
            df.groupby(['pollutant', 'feedstock_measure']).size().unstack().plot(kind='bar', stacked=True)
            imageNameMOVES = self.lineEditScenaName.text().strip() + "_output.png"
            imagePathMOVES = os.path.join(self.lineEditProjectPath.text().strip(), imageNameMOVES)
            plt.savefig(imagePathMOVES, bbox_inches='tight', dpi='figure')
            self.pixmap = QtGui.QPixmap(imagePathMOVES)
            self.labelMOVESGraph.resize(self.width(), self.height())
            self.labelMOVESGraph.setPixmap(
                self.pixmap.scaled(self.labelMOVESGraph.size(), QtCore.Qt.IgnoreAspectRatio))

            # Generate graph for NONROAD module
            fileNameNONROAD = self.lineEditScenaName.text().strip() + "_raw.csv"
            dataframePathNONROAD = os.path.join(self.lineEditProjectPath.text().strip(), fileNameNONROAD)
            df = pd.read_csv(dataframePathNONROAD)
            df.groupby(['pollutant', 'feedstock_measure']).size().unstack().plot(kind='bar', stacked=True)
            imageNameNONROAD = self.lineEditScenaName.text().strip() + "_output.png"
            imagePathNONROAD = os.path.join(self.lineEditProjectPath.text().strip(), imageNameNONROAD)
            plt.savefig(imagePathNONROAD, bbox_inches='tight')
            self.pixmap = QtGui.QPixmap(imagePathNONROAD)
            self.labelNONROADGraph.resize(self.width(), self.height())
            self.labelNONROADGraph.setPixmap(
                self.pixmap.scaled(self.labelNONROADGraph.size(), QtCore.Qt.IgnoreAspectRatio))

            # Generate graph for Emissionfactors module
            fileNameEF = self.lineEditScenaName.text().strip() + "_raw.csv"
            dataframePathEF = os.path.join(self.lineEditProjectPath.text().strip(), fileNameEF)
            df = pd.read_csv(dataframePathEF)
            df.groupby(['pollutant', 'feedstock_measure']).size().unstack().plot(kind='bar', stacked=True)
            imageNameEF = self.lineEditScenaName.text().strip() + "_output.png"
            imagePathEF = os.path.join(self.lineEditProjectPath.text().strip(), imageNameEF)
            plt.savefig(imagePathEF, bbox_inches='tight')
            self.pixmap = QtGui.QPixmap(imagePathEF)
            self.labelEmissionFactorsGraph.resize(self.width(), self.height())
            self.labelEmissionFactorsGraph.setPixmap(
                self.pixmap.scaled(self.labelEmissionFactorsGraph.size(), QtCore.Qt.IgnoreAspectRatio))

            # Generate graph for Emissionfactors module
            fileNameFD = self.lineEditScenaName.text().strip() + "_raw.csv"
            dataframePathFD = os.path.join(self.lineEditProjectPath.text().strip(), fileNameFD)
            df = pd.read_csv(dataframePathFD)
            df.groupby(['pollutant', 'feedstock_measure']).size().unstack().plot(kind='bar', stacked=True)
            imageNameFD = self.lineEditScenaName.text().strip() + "_output.png"
            imagePathFD = os.path.join(self.lineEditProjectPath.text().strip(), imageNameFD)
            plt.savefig(imagePathFD, bbox_inches='tight')
            self.pixmap = QtGui.QPixmap(imagePathFD)
            self.labelFugitivedustGraph.resize(self.width(), self.height())
            self.labelFugitivedustGraph.setPixmap(
                self.pixmap.scaled(self.labelFugitivedustGraph.size(), QtCore.Qt.IgnoreAspectRatio))



    #########################################################################################################################



    def setupUIResult(self):
        # Result tab created
        self.tabResult = QtWidgets.QWidget()

        # Result tab added
        self.centralwidget.addTab(self.tabResult, "RESULT")

        # Result code start
        windowLayout = QGridLayout()
        windowLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)

        self.windowLayout.setColumnStretch(6, 1)

        self.plainTextLog = QPlainTextEdit()
        self.plainTextLog.setPlainText("")
        self.plainTextLog.setReadOnly(True)
        self.plainTextLog.setFixedHeight(100)
        windowLayout.addWidget(self.plainTextLog, 0, 0, 1 , 4)

        self.labelMOVESGraph = QLabel()
        self.labelMOVESGraph.setFixedHeight(300)
        self.labelMOVESGraph.setFixedWidth(400)
        windowLayout.addWidget(self.labelMOVESGraph,1 , 0)

        self.plainLabel1 = QLabel()
        windowLayout.addWidget(self.plainLabel1, 1, 1)

        self.labelNONROADGraph = QLabel()
        self.labelNONROADGraph.setFixedHeight(300)
        self.labelNONROADGraph.setFixedWidth(400)
        windowLayout.addWidget(self.labelNONROADGraph, 1, 2)

        self.labelEmissionFactorsGraph = QLabel()
        self.labelEmissionFactorsGraph.setFixedHeight(300)
        self.labelEmissionFactorsGraph.setFixedWidth(400)
        windowLayout.addWidget(self.labelEmissionFactorsGraph,2 , 0)

        self.plainLabel2 = QLabel()
        windowLayout.addWidget(self.plainLabel2, 2, 1)

        self.labelFugitivedustGraph = QLabel()
        self.labelFugitivedustGraph.setFixedHeight(300)
        self.labelFugitivedustGraph.setFixedWidth(400)
        windowLayout.addWidget(self.labelFugitivedustGraph, 2, 2)

        self.tabResult.setLayout(windowLayout)


        #########################################################################################################################

    def setupUi(self, OtherWindow):

        OtherWindow.setObjectName("OtherWindow")
        OtherWindow.setGeometry(0,0,400,400)
        self.centralwidget = QtWidgets.QTabWidget(OtherWindow)
        OtherWindow.setCentralWidget(self.centralwidget)
        self.centralwidget.setGeometry(0,0,400,400)

        #self.centralwidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)

        self.centralwidget.setObjectName("centralwidget")
        font = QtGui.QFont()
        font.setPointSize(22)


        self.setupUIHomePage()
        self.setupUIMoves()
        self.setupUINonroad()
        self.setupUIEmissionFactors()
        self.setupUIFugitiveDust()
        self.setupUIResult()


        ####### ==================================================================

def runCommand(runConfigObj , emissionFactorsConfigCreationObj, attributeValueStorageObj):
    # Generate Logs
    logging.basicConfig(level='DEBUG', format='%(asctime)s, %(levelname)-8s'
                                              ' [%(filename)s:%(module)s.'
                                              '%(funcName)s.%(lineno)d] %(message)s',
                        stream=attributeValueStorageObj.streamGenerated)

    # Set Logger level according to selection of Verbosity Logger Level on Home Page
    if attributeValueStorageObj.loggerLevel == "INFO":
        logging.getLogger().setLevel(logging.INFO)
    elif attributeValueStorageObj.loggerLevel == "DEBUG":
        logging.getLogger().setLevel(logging.DEBUG)
    elif attributeValueStorageObj.loggerLevel == "WARNING":
        logging.getLogger().setLevel(logging.WARNING)
    elif attributeValueStorageObj.loggerLevel == "ERROR":
        logging.getLogger().setLevel(logging.ERROR)
    elif attributeValueStorageObj.loggerLevel == "CRITICAL":
        logging.getLogger().setLevel(logging.CRITICAL)
    elif attributeValueStorageObj.loggerLevel == "UNSET":
        logging.getLogger().setLevel(logging.NOTSET)

    # load config options
    _config = IO.load_configs(emissionFactorsConfigCreationObj, runConfigObj)
    print(_config)

    with FPEAM(run_config=_config) as _fpeam:
        _fpeam.run()

        # save the raw results to the project path folder specified in run_config
        _fpath = os.path.join(_fpeam.config['project_path'],
                              '%s_raw.csv' % _fpeam.config['scenario_name'])
        _fpeam.results.to_csv(_fpath, index=False)

        # save several summarized results files to the project folder
        _fpeam.summarize()
        print("Done")

    attributeValueStorageObj.logContents = attributeValueStorageObj.streamGenerated.getvalue()

##############################################################################################



if __name__ == "__main__":
    import sys


    styleSheet = """

    QWidget {
        background-color: #ffffff;
    }


    QLabel#titleFPEAMLine {
        border: 1px solid #000000;
    }
    
    QLabel#yearErrorMsg {
        width: 160px;
        height: 30px;
        background: #ffffff;
        box-sizing: border-box;
        box-shadow: 1px 1px 2px rgba(0, 0, 0, 0.25);
        border-radius: 5px;
        font-family: Roboto;
        font-style: normal;
        font-weight: normal;
        font-size: 13px;
        line-height: 16px;
        display: flex;
        align-items: center;
        text-align: center;        
        color: #000000;
    }

    QLabel#allLabels {
        width: 160px;
        height: 30px;
        background: #C6CDD1;
        border: 1px solid #495965;
        box-sizing: border-box;
        box-shadow: 1px 1px 2px rgba(0, 0, 0, 0.25);
        border-radius: 5px;
        font-family: Roboto;
        font-style: normal;
        font-weight: normal;
        font-size: 13px;
        line-height: 16px;
        display: flex;
        align-items: center;
        text-align: center;        
        color: #000000;
    }

    QLabel#title {
        font-family: Roboto;
        font-style: normal;
        font-weight: normal;
        font-size: 33px;
        line-height: 39px;
        display: flex;
        align-items: center;
        text-align: center;
        color: #000000;
        
    }

    QLabel#subTitleLabels {
        font-family: Roboto;
        font-style: normal;
        font-weight: normal;
        font-size: 24px;
        line-height: 28px;
        display: flex;
        align-items: center;
        text-align: center;        
        color: #000000;
        backgroud-color: #000000
    }

    QCheckBox {
        background: #FFFFFF;
        box-sizing: border-box;
        border-radius: 5px;
        box-shadow: 1px 1px 1px rgba(0, 0, 0, 0.25);
        font-family: Roboto;
        font-style: normal;
        font-weight: normal;
        font-size: 13px;
        line-height: 15px;
        display: flex;
        align-items: center;
        text-align: center;        
        color: #000000;        
        border-radius: 5px;
    }

    QPushButton {
        background: #F4F7F7;
        border: 1px solid #495965;
        box-sizing: border-box;
        box-shadow: 2px 2px 1px rgba(0, 0, 0, 0.25);
        border-radius: 5px;
        font-family: Roboto;
        font-style: normal;
        font-weight: normal;
        font-size: 14px;
        line-height: 16px;
        display: flex;
        align-items: center;
        text-align: center;        
        color: #000000;        
        border-radius: 5px;
    }
    
    QPushButton#resetRunBtn {
        background: #C6CDD1;
        border: 1px solid #000000;
        box-sizing: border-box;
        box-shadow: 1px 1px 2px rgba(0, 0, 0, 0.25);
        border-radius: 5px;
        font-family: Roboto;
        font-style: normal;
        font-weight: normal;
        font-size: 18px;
        line-height: 21px;
        display: flex;
        align-items: center;
        text-align: center;
        color: #000000;        
        border-radius: 5px
    }
    
    QLineEdit {
        background: #FFFFFF;
        border: 1px solid #495965;
        box-sizing: border-box;
        box-shadow: 1px 1px 2px rgba(0, 0, 0, 0.25);
        border-radius: 5px;        
        font-family: Roboto;
        font-style: normal;
        font-weight: normal;
        font-size: 14px;
        line-height: 16px;
        align-items: center;
        text-align: center;

    }
    
    QComboBox {
        background: #FFFFFF;
        border: 1px solid #495965;
        box-sizing: border-box;
        border-radius: 5px;
        font-family: Roboto;
        font-style: normal;
        font-weight: normal;
        font-size: 14px;
        line-height: 16px;
        display: flex;
        text-align: center;        
        color: #000000;        
        border-radius: 5px;
        
    }
    
    QComboBox#AggLevelCombo {
        background: #FFFFFF;
        border: 1px solid #495965;
        box-sizing: border-box;
        border-radius: 5px;
        font-family: Roboto;
        font-style: normal;
        font-weight: normal;
        font-size: 14px;
        line-height: 16px;
        display: flex;
        text-align: center;        
        color: #000000;        
        border-radius: 5px;
        
    }
    
    QSpinBox {
        background: #FFFFFF;
        border: 1px solid #495965;
        box-sizing: border-box;
        border-radius: 5px;
        font-family: Roboto;
        font-style: normal;
        font-weight: normal;
        font-size: 14px;
        line-height: 16px;
        display: flex;
        text-align: center;        
        color: #000000;        
        border-radius: 5px;
        
    }
    
    """

    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(styleSheet)
    OtherWindow = QtWidgets.QMainWindow()
    OtherWindow.setWindowTitle("FPEAM")
    OtherWindow.setWindowFlags(QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowMinimizeButtonHint)
    ui = AlltabsModule()
    ui.setupUi(OtherWindow)
    OtherWindow.show()
    sys.exit(app.exec_())