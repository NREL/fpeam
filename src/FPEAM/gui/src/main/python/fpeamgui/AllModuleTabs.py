# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'OtherWindow.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!
import logging
import os

#import args as args
import pandas
import pylab
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtWidgets import QRadioButton, QComboBox, QPushButton, QTextEdit, QFileDialog, QMessageBox, QPlainTextEdit
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


        # Created UI element Module Selection
        self.labelModules = QLabel()
        self.labelModules.setText("Modules")
        self.checkBoxMoves = QCheckBox("MOVES")
        self.checkBoxMoves.setFixedWidth(200)
        self.checkBoxMoves.setFixedHeight(30)
        self.checkBoxMoves.setChecked(True)
        self.checkBoxMoves.stateChanged.connect(self.onStateChangedMoves)
        self.checkBoxNonroad = QCheckBox("NONROAD")
        self.checkBoxNonroad.setFixedWidth(200)
        self.checkBoxNonroad.setFixedHeight(30)
        self.checkBoxNonroad.setChecked(True)
        self.checkBoxNonroad.stateChanged.connect(self.onStateChangedNonroad)
        self.checkBoxEmissionFactors = QCheckBox("emissionfactors")
        self.checkBoxEmissionFactors.setFixedWidth(200)
        self.checkBoxEmissionFactors.setFixedHeight(30)
        self.checkBoxEmissionFactors.setChecked(True)
        self.checkBoxEmissionFactors.stateChanged.connect(self.onStateChangedEmissionFactors)
        self.checkBoxFugitiveDust = QCheckBox("fugitivedust")
        self.checkBoxFugitiveDust.setFixedWidth(200)
        self.checkBoxFugitiveDust.setFixedHeight(30)
        self.checkBoxFugitiveDust.setChecked(True)
        self.checkBoxFugitiveDust.stateChanged.connect(self.onStateChangedFugitiveDust)
        self.windowLayout.addWidget(self.labelModules, 0, 0)
        self.windowLayout.addWidget(self.checkBoxMoves, 0, 1)
        self.windowLayout.addWidget(self.checkBoxNonroad, 0, 2)
        self.windowLayout.addWidget(self.checkBoxEmissionFactors, 0, 3)
        self.windowLayout.addWidget(self.checkBoxFugitiveDust, 0, 4)


        # Created UI element Scenario Name
        self.labelScenaName = QLabel()
        self.labelScenaName.setText("Scenario Name")
        self.labelScenaName.setToolTip("Enter the Scenario Name")
        self.lineEditScenaName = QLineEdit(self)
        self.lineEditScenaName.setFixedWidth(100)
        regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(regex)
        self.lineEditScenaName.setValidator(validator)
        self.windowLayout.addWidget(self.labelScenaName, 1,0)
        self.windowLayout.addWidget(self.lineEditScenaName, 1, 1)

        # UI element - Project Path
        self.labelProjPath = QLabel()
        self.labelProjPath.setText("Project Path")
        self.labelProjPath.setToolTip("Folder path where input and output files will be stored")
        self.browseBtn = QPushButton("Browse", self)
        self.browseBtn.setFixedWidth(100)
        self.browseBtn.clicked.connect(self.getfiles)
        self.lineEditProjectPath = QLineEdit(self)
        self.lineEditProjectPath.setFixedWidth(100)
        self.windowLayout.addWidget(self.labelProjPath, 2, 0)
        self.windowLayout.addWidget(self.browseBtn, 2, 1)
        self.windowLayout.addWidget(self.lineEditProjectPath, 2, 2)

        # Created UI element Run Button
        self.runBtn = QPushButton("Run", self)
        self.runBtn.setFixedWidth(100)
        self.runBtn.clicked.connect(self.runTheSelectedModules)
        self.windowLayout.addWidget(self.runBtn, 3, 1)

        # Ui Element - Logging Verbosity Level
        self.labelLoggVerboLevel = QLabel()
        self.labelLoggVerboLevel.setText("Logging Verbosity Level")
        self.comboBoxVerbosityLevel = QComboBox(self)
        self.comboBoxVerbosityLevel.setFixedWidth(100)
        self.comboBoxVerbosityLevel.addItem("INFO")
        self.comboBoxVerbosityLevel.addItem("ERROR")
        self.comboBoxVerbosityLevel.addItem("WARNING")
        self.comboBoxVerbosityLevel.addItem("UNSET")
        self.comboBoxVerbosityLevel.addItem("CRITICAL")
        self.comboBoxVerbosityLevel.addItem("DEBUG")
        self.index = self.comboBoxVerbosityLevel.findText("DEBUG")
        self.comboBoxVerbosityLevel.setCurrentIndex(self.index)
        self.windowLayout.addWidget(self.labelLoggVerboLevel, 4, 0)
        self.windowLayout.addWidget(self.comboBoxVerbosityLevel, 4, 1)


        # UI element  -  Router Engine
        self.labelRE = QLabel()
        self.labelRE = QLabel()
        self.labelRE.setText("Router Engine")
        self.labelRE.setToolTip("Do you want to set Router Engine - Yes/No")
        self.comboBoxRE = QComboBox(self)
        self.comboBoxRE.setFixedWidth(100)
        self.comboBoxRE.addItem("Yes")
        self.comboBoxRE.addItem("No")
        self.comboBoxRE.setCurrentText("Yes")
        self.index = self.comboBoxRE.findText("Yes")
        self.comboBoxRE.setCurrentIndex(self.index)
        self.windowLayout.addWidget(self.labelRE, 5, 0)
        self.windowLayout.addWidget(self.comboBoxRE, 5, 1)

        # UI element -  Backfill Flag
        self.labelBF = QLabel()
        self.labelBF = QLabel()
        self.labelBF.setText("Backfill Flag")
        self.labelBF.setToolTip("Do you want to set Backfill Flag - Yes/No")
        self.comboBoxBF = QComboBox(self)
        self.comboBoxBF.setFixedWidth(100)
        self.comboBoxBF.addItem("Yes")
        self.comboBoxBF.addItem("No")
        self.comboBoxBF.setCurrentText("Yes")
        self.index = self.comboBoxBF.findText("Yes")
        self.comboBoxBF.setCurrentIndex(self.index)
        self.windowLayout.addWidget(self.labelBF, 6, 0)
        self.windowLayout.addWidget(self.comboBoxBF, 6, 1)

        # UI element - Equipment
        self.labelEq = QLabel()
        self.labelEq.setText("Equipment")
        self.labelEq.setToolTip("Select equipment input dataset")
        self.browseBtnEq = QPushButton("Browse", self)
        self.browseBtnEq.setFixedWidth(100)
        self.browseBtnEq.clicked.connect(self.getfilesEq)
        self.lineEditEq = QLineEdit(self)
        self.lineEditEq.setFixedWidth(100)
        self.windowLayout.addWidget(self.labelEq, 7, 0)
        self.windowLayout.addWidget(self.browseBtnEq, 7, 1)
        self.windowLayout.addWidget(self.lineEditEq, 7, 2)

        # UI element - Production
        self.labelProd = QLabel()
        self.labelProd.setText("Production")
        self.labelProd.setToolTip("Select production input dataset")
        self.browseBtnProd = QPushButton("Browse", self)
        self.browseBtnProd.setFixedWidth(100)
        self.browseBtnProd.clicked.connect(self.getfilesProd)
        self.lineEditProd = QLineEdit(self)
        self.lineEditProd.setFixedWidth(100)
        self.windowLayout.addWidget(self.labelProd, 8, 0)
        self.windowLayout.addWidget(self.browseBtnProd, 8, 1)
        self.windowLayout.addWidget(self.lineEditProd, 8, 2)

        # Feedstock Loss Factors
        self.labelFedLossFact = QLabel()
        self.labelFedLossFact.setText("Feedstock Loss Factors")
        self.labelFedLossFact.setToolTip("Select Feedstock Loss Factors dataset")
        self.browseBtnFLoss = QPushButton("Browse", self)
        self.browseBtnFLoss.setFixedWidth(100)
        self.browseBtnFLoss.clicked.connect(self.getfilesFLoss)
        self.lineEditFedLossFact = QLineEdit(self)
        self.lineEditFedLossFact.setFixedWidth(100)
        self.windowLayout.addWidget(self.labelFedLossFact, 9, 0)
        self.windowLayout.addWidget(self.browseBtnFLoss, 9, 1)
        self.windowLayout.addWidget(self.lineEditFedLossFact, 9, 2)

        # Transportation graph
        self.labelTransGraph = QLabel()
        self.labelTransGraph.setText("Transportation Graph")
        self.labelTransGraph.setToolTip("Select Transportation graph dataset")
        self.browseBtnTransGr = QPushButton("Browse", self)
        self.browseBtnTransGr.setFixedWidth(100)
        self.browseBtnTransGr.clicked.connect(self.getfilesTransGr)
        self.lineEditTransGraph = QLineEdit(self)
        self.lineEditTransGraph.setFixedWidth(100)
        self.windowLayout.addWidget(self.labelTransGraph, 10, 0)
        self.windowLayout.addWidget(self.browseBtnTransGr, 10, 1)
        self.windowLayout.addWidget(self.lineEditTransGraph, 10, 2)



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
        self.windowLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.windowLayout.setColumnStretch(6, 1)
        #self.windowLayout.setColumnStretch(4, 1)

        self.tabMoves.setLayout(self.windowLayout)

        # Created UI element Aggregation Level

        self.labelAggLevel = QLabel()
        self.labelAggLevel = QLabel()
        self.labelAggLevel.setText("Aggregation Level")
        self.radioGroupAggLevel = QButtonGroup(self.windowLayout)
        self.radioButtonByCounty = QRadioButton("MOVES By Each County")
        self.radioButtonByCounty.setFixedWidth(200)
        self.radioButtonByCounty.setFixedHeight(30)
        self.radioButtonByCounty.setChecked(True)
        self.radioButtonByState = QRadioButton("MOVES By State ")
        self.radioButtonByState.setFixedWidth(200)
        self.radioButtonByState.setFixedHeight(30)
        self.radioButtonByStateandFeed = QRadioButton("MOVES By State and Feedstock ")
        self.radioButtonByStateandFeed.setFixedWidth(210)
        self.radioButtonByStateandFeed.setFixedHeight(30)
        self.radioGroupAggLevel.addButton(self.radioButtonByCounty)
        self.radioGroupAggLevel.addButton(self.radioButtonByState)
        self.radioGroupAggLevel.addButton(self.radioButtonByStateandFeed)
        # Add Empty PlainText
        self.emptyPlainTextAggLevel = QLabel()
        self.windowLayout.addWidget(self.labelAggLevel, 1, 0)
        self.windowLayout.addWidget(self.radioButtonByCounty, 1, 1)
        self.windowLayout.addWidget(self.radioButtonByState, 1, 2)
        self.windowLayout.addWidget(self.radioButtonByStateandFeed, 1, 3)
        self.windowLayout.addWidget(self.emptyPlainTextAggLevel, 1, 4)

        # Created UI element Cached Result usage
        self.labelCachedResUse = QLabel()
        self.labelCachedResUse.setText("Cached Result Usage")
        self.labelCachedResUse.setToolTip("Use existing results in MOVES output database or run MOVES for all counties")
        self.comboBoxCachedResUse = QComboBox(self)
        self.comboBoxCachedResUse.setFixedWidth(100)
        self.comboBoxCachedResUse.addItem("Yes")
        self.comboBoxCachedResUse.addItem("No")
        self.index = self.comboBoxCachedResUse.findText("Yes")
        self.comboBoxCachedResUse.setCurrentIndex(self.index)
        # Add Empty PlainText
        self.emptyPlainTextCachedRes = QLabel()
        self.windowLayout.addWidget(self.labelCachedResUse, 2, 0)
        self.windowLayout.addWidget(self.comboBoxCachedResUse, 2, 1)
        self.windowLayout.addWidget(self.emptyPlainTextCachedRes, 2, 2)

        # Created UI element Feedstock Measure Type
        self.labelFeedMeasureType = QLabel()
        self.labelFeedMeasureType.setText("Feedstock Measure Type")
        self.labelFeedMeasureType.setToolTip("Enter Feedstock Measure Type Identifier")
        self.lineEditFeedMeasureType = QLineEdit(self)
        self.lineEditFeedMeasureType.setFixedWidth(100)
        regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(regex)
        self.lineEditFeedMeasureType.setValidator(validator)
        self.lineEditFeedMeasureType.setText("production")
        self.windowLayout.addWidget(self.labelFeedMeasureType, 3, 0)
        self.windowLayout.addWidget(self.lineEditFeedMeasureType, 3, 1)

        # Created UI element Moves Path
        self.MovesPathLable = QLabel()
        self.MovesPathLable.setText("Moves Path")
        self.MovesPathLable.setToolTip("Path where Moves is installed. If it's not installed, then download from the "
                                       "link - "
                                       "<a href ='https://www.epa.gov/moves/moves-versions-limited-current-use#downloading-2014a'>MOVES</a> ")
        self.browseBtnMovesPath = QPushButton("Browse", self)
        self.browseBtnMovesPath.clicked.connect(self.getfilesMovesPath)
        self.lineEditMovesPath = QLineEdit(self)
        self.lineEditMovesPath.setFixedWidth(100)
        self.lineEditMovesPath.setText("C:\MOVES2014b")
        self.windowLayout.addWidget(self.MovesPathLable, 4, 0)
        self.windowLayout.addWidget(self.lineEditMovesPath, 4, 1)
        self.windowLayout.addWidget(self.browseBtnMovesPath, 4, 2)

        # Created UI element VMT per Truck
        self.labelVMTperTruck = QLabel()
        self.labelVMTperTruck.setText("VMT per Truck")
        self.labelVMTperTruck.setToolTip("Vehicle Miles Traveled calculated per Truck")
        self.lineEditVMTperTruck = QLineEdit(self)
        self.lineEditVMTperTruck.setFixedWidth(100)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 6)
        self.lineEditVMTperTruck.setValidator(self.onlyFlaot)
        self.lineEditVMTperTruck.setText("20")
        self.windowLayout.addWidget(self.labelVMTperTruck, 5, 0)
        self.windowLayout.addWidget(self.lineEditVMTperTruck, 5, 1)


        # Created UI element No of Trucks used
        self.labelNoofTruck = QLabel()
        self.labelNoofTruck.setText("Number Of Trucks Used")
        self.labelNoofTruck.setToolTip("Number of trucks used in a scenario")
        self.spinBoxNoofTruck = QSpinBox()
        self.spinBoxNoofTruck.setFixedWidth(100)
        self.spinBoxNoofTruck.setMinimum(1)
        self.spinBoxNoofTruck.setValue(1)
        self.windowLayout.addWidget(self.labelNoofTruck, 6, 0)
        self.windowLayout.addWidget(self.spinBoxNoofTruck, 6, 1)

        # Created UI element Year
        self.labelYear = QLabel()
        self.labelYear.setText("Year")
        self.labelYear.setToolTip("Start year of Equipment")
        self.comboBoxYear = QComboBox(self)
        self.comboBoxYear.setFixedWidth(100)
        for i in range(2018,1990,-1):
            self.number = i
            self.comboBoxYear.addItem(str(i))
        self.index = self.comboBoxYear.findText("2017")
        self.comboBoxYear.setCurrentIndex(self.index)
        self.labelYearErrorMsg = QLabel()
        self.labelYearErrorMsg.setText("")
        self.windowLayout.addWidget(self.labelYear, 7, 0)
        self.windowLayout.addWidget(self.comboBoxYear, 7,1)
        self.windowLayout.addWidget(self.labelYearErrorMsg, 7, 2, 1, 2)
        self.comboBoxYear.currentIndexChanged.connect(self.handleItemPressed)

        # Created UI element Timestamp
        self.labelTimestamp = QLabel()
        self.labelTimestamp.setText("Timestamp")
        self.windowLayout.addWidget(self.labelTimestamp, 8, 0)

        # Created UI element Timestamp - Month
        self.labelMonth = QLabel()
        self.labelMonth.setText("Month")
        self.comboBoxMonth = QComboBox(self)
        self.comboBoxMonth.setFixedWidth(100)
        for i in range(1,13):
            self.number = i
            self.comboBoxMonth.addItem(str(i))
        self.index = self.comboBoxMonth.findText("10")
        self.comboBoxMonth.setCurrentIndex(self.index)
        self.windowLayout.addWidget(self.labelMonth, 9, 0)
        self.windowLayout.addWidget(self.comboBoxMonth, 9, 1)

        # Created UI element Timestamp - Date
        self.labelDate = QLabel()
        self.labelDate.setText("Date")
        self.comboBoxDate = QComboBox(self)
        self.comboBoxDate.setFixedWidth(100)
        for i in range(1, 32):
            self.number = i
            self.comboBoxDate.addItem(str(i))
        self.index = self.comboBoxDate.findText("5")
        self.comboBoxDate.setCurrentIndex(self.index)
        self.windowLayout.addWidget(self.labelDate, 10, 0)
        self.windowLayout.addWidget(self.comboBoxDate, 10, 1)

        # Created UI element Timestamp - Beginning Hour
        self.labelBegHr = QLabel()
        self.labelBegHr.setText("Beginning Hour")
        self.comboBoxBegHr = QComboBox(self)
        self.comboBoxBegHr.setFixedWidth(100)
        for i in range(1, 25):
            self.number = i
            self.comboBoxBegHr.addItem(str(i))
        self.index = self.comboBoxBegHr.findText("7")
        self.comboBoxBegHr.setCurrentIndex(self.index)
        self.windowLayout.addWidget(self.labelBegHr, 11, 0)
        self.windowLayout.addWidget(self.comboBoxBegHr, 11, 1)

        # Created UI element Timestamp - Ending Hour
        self.labelEndHr = QLabel()
        self.labelEndHr.setText("Ending Hour")
        self.comboBoxEndHr = QComboBox(self)
        self.comboBoxEndHr.setFixedWidth(100)
        for i in range(1, 25):
            self.number = i
            self.comboBoxEndHr.addItem(str(i))
        self.index = self.comboBoxEndHr.findText("18")
        self.comboBoxEndHr.setCurrentIndex(self.index)
        self.windowLayout.addWidget(self.labelEndHr, 12, 0)
        self.windowLayout.addWidget(self.comboBoxEndHr, 12, 1)

        # Created UI element Timestamp - Day Type
        self.labelDayType = QLabel()
        self.labelDayType.setText("Day Type")
        self.comboBoxDayType = QComboBox(self)
        self.comboBoxDayType.setFixedWidth(100)
        self.comboBoxDayType.addItem(str(2))
        self.comboBoxDayType.addItem(str(5))
        self.index = self.comboBoxDayType.findText("5")
        self.comboBoxDayType.setCurrentIndex(self.index)
        self.windowLayout.addWidget(self.labelDayType, 13, 0)
        self.windowLayout.addWidget(self.comboBoxDayType, 13, 1)

        # Created UI element Paths
        self.labelPath = QLabel()
        self.labelPath.setText("Paths")
        self.windowLayout.addWidget(self.labelPath, 14, 0)

        # Created UI element Truck Capacity
        self.labelTruckCapacity = QLabel()
        self.labelTruckCapacity.setText("Truck Capacity")
        self.labelTruckCapacity.setToolTip("Select Truck Capacity (truck capacities for feedstock transportation) dataset")
        self.browseBtnTruckCapa = QPushButton("Browse", self)
        self.browseBtnTruckCapa.setFixedWidth(100)
        self.browseBtnTruckCapa.clicked.connect(self.getfilesTruckCapa)
        self.lineEditTruckCapa = QLineEdit(self)
        self.lineEditTruckCapa.setFixedWidth(100)
        self.windowLayout.addWidget(self.labelTruckCapacity, 15, 0)
        self.windowLayout.addWidget(self.browseBtnTruckCapa, 15, 1)
        self.windowLayout.addWidget(self.lineEditTruckCapa, 15, 2)

        # Created UI element AVFT
        self.labelAVFT = QLabel()
        self.labelAVFT.setText("AVFT")
        self.labelAVFT.setToolTip("Select AVFT (fuel fraction by engine type) dataset")
        self.browseBtnAVFT = QPushButton("Browse", self)
        self.browseBtnAVFT.setFixedWidth(100)
        self.browseBtnAVFT.clicked.connect(self.getfilesAVFT)
        self.lineEditAVFT = QLineEdit(self)
        self.lineEditAVFT.setFixedWidth(100)
        self.windowLayout.addWidget(self.labelAVFT, 16, 0)
        self.windowLayout.addWidget(self.browseBtnAVFT, 16, 1)
        self.windowLayout.addWidget(self.lineEditAVFT, 16, 2)

        # Created UI element Region FIPs Map
        self.labelFips = QLabel()
        self.labelFips.setText("Region FIPS Map")
        self.labelFips.setToolTip("Select Region FIPS Map (production region to MOVES FIPS mapping) dataset")
        self.browseBtnFips = QPushButton("Browse", self)
        self.browseBtnFips.setFixedWidth(100)
        self.browseBtnFips.clicked.connect(self.getfilesFips)
        self.lineEditFips = QLineEdit(self)
        self.lineEditFips.setFixedWidth(100)
        self.windowLayout.addWidget(self.labelFips, 17, 0)
        self.windowLayout.addWidget(self.browseBtnFips, 17, 1)
        self.windowLayout.addWidget(self.lineEditFips, 17, 2)

        # Created UI element Moves Datafiles
        self.labelDatafiles = QLabel()
        self.labelDatafiles.setText("Moves Datafiles")
        self.labelDatafiles.setToolTip("Select all input files created for MOVES runs")
        self.browseBtnDatafiles = QPushButton("Browse", self)
        self.browseBtnDatafiles.setFixedWidth(100)
        self.browseBtnDatafiles.clicked.connect(self.getfilesDatafiles)
        self.lineEditDatafiles = QLineEdit(self)
        self.lineEditDatafiles.setFixedWidth(100)
        self.windowLayout.addWidget(self.labelDatafiles, 18, 0)
        self.windowLayout.addWidget(self.browseBtnDatafiles, 18, 1)
        self.windowLayout.addWidget(self.lineEditDatafiles, 18, 2)

        # Created UI element VMT Fraction
        self.labelVMTFraction = QLabel()
        self.labelVMTFraction.setText("VMT Fraction")
        self.labelVMTFraction.setToolTip("Fraction of VMT(Vehicle MilesTraveled) by road type (All must sum to 1)")
        self.windowLayout.addWidget(self.labelVMTFraction, 19, 0)

        # Created UI element VMT - Rural Restricted
        self.labelRuralRes = QLabel()
        self.labelRuralRes.setText("Rural Restricted")
        self.lineEditRuralRes = QLineEdit(self)
        self.lineEditRuralRes.setFixedWidth(100)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditRuralRes.setValidator(self.onlyFlaot)
        self.lineEditRuralRes.setText("0.3")
        self.windowLayout.addWidget(self.labelRuralRes, 20, 0)
        self.windowLayout.addWidget(self.lineEditRuralRes, 20, 1)

        # Created UI element VMT - Rural Unrestricted
        self.labelRuralUnres = QLabel()
        self.labelRuralUnres.setText("Rural Unrestricted")
        self.lineEditRuralUnres = QLineEdit(self)
        self.lineEditRuralUnres.setFixedWidth(100)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditRuralUnres.setValidator(self.onlyFlaot)
        self.lineEditRuralUnres.setText("0.28")
        self.windowLayout.addWidget(self.labelRuralUnres, 21, 0)
        self.windowLayout.addWidget(self.lineEditRuralUnres, 21, 1)

        # Created UI element VMT - Urban Restricted
        self.labelUrbanRes = QLabel()
        self.labelUrbanRes.setText("Urban Restricted")
        self.lineEditUrbanRes = QLineEdit(self)
        self.lineEditUrbanRes.setFixedWidth(100)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditUrbanRes.setValidator(self.onlyFlaot)
        self.lineEditUrbanRes.setText("0.21")
        self.windowLayout.addWidget(self.labelUrbanRes, 22, 0)
        self.windowLayout.addWidget(self.lineEditUrbanRes, 22, 1)

        # Created UI element VMT - Urban Unrestricted
        self.labelUrbanUnres = QLabel()
        self.labelUrbanUnres.setText("Urban Unrestricted")
        self.lineEditUrbanUnres = QLineEdit()
        self.lineEditUrbanUnres.setFixedWidth(100)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditUrbanUnres.setValidator(self.onlyFlaot)
        self.lineEditUrbanUnres.setText("0.28")
        self.windowLayout.addWidget(self.labelUrbanUnres, 23, 0)
        self.windowLayout.addWidget(self.lineEditUrbanUnres, 23, 1)


        additionVMTFraction = self.lineEditRuralRes.text() + self.lineEditRuralUnres.text() \
                              + self.lineEditUrbanRes.text() + self.lineEditUrbanUnres.text()

        # Created UI element VMT Fraction Error
        self.labelVMTFractionError = QLabel()
        self.labelVMTFractionError.setText("")


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
        self.windowLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.windowLayout.setColumnStretch(6, 1)
        # self.windowLayout.setColumnStretch(4, 1)

        self.tabNonroad.setLayout(self.windowLayout)

        # Created UI element Year - Nonroad
        self.labelYearNon = QLabel()
        self.labelYearNon.setText("Year")
        self.labelYearNon.setToolTip("Start year of equipment")
        self.comboBoxYearNon = QComboBox(self)
        self.comboBoxYearNon.setFixedWidth(100)
        for i in range(2018, 1990, -1):
            self.number = i
            self.comboBoxYearNon.addItem(str(i))
        self.index = self.comboBoxYearNon.findText("2017")
        self.comboBoxYearNon.setCurrentIndex(self.index)
        self.labelYearNonErrorMsg = QLabel()
        self.labelYearNonErrorMsg.setText("")
        self.windowLayout.addWidget(self.labelYearNon, 2, 0)
        self.windowLayout.addWidget(self.comboBoxYearNon, 2, 1)
        self.windowLayout.addWidget(self.labelYearNonErrorMsg, 2, 2)
        # Check whether Moves year matches with Nonroad year
        self.comboBoxYearNon.currentIndexChanged.connect(self.handleItemPressed)

        # Created UI element Paths
        self.labelPathNon = QLabel()
        self.labelPathNon.setText("Paths")
        self.windowLayout.addWidget(self.labelPathNon, 3, 0)

        # Created UI element Nonroad Datafiles
        self.labelDatafilesNon = QLabel()
        self.labelDatafilesNon.setText("NONROAD Datafiles")
        self.labelDatafilesNon.setToolTip("Select NONROAD output folder")
        self.browseBtnDatafilesNon = QPushButton("Browse", self)
        self.browseBtnDatafilesNon.setFixedWidth(100)
        self.browseBtnDatafilesNon.clicked.connect(self.getfilesDatafilesNon)
        # Add Empty PlainText
        self.emptyPlainTextNonDatafiles = QLabel()
        self.emptyPlainTextNonDatafiles.setFixedWidth(90)
        self.lineEditDatafilesNon = QLineEdit(self)
        self.lineEditDatafilesNon.setFixedWidth(100)
        self.windowLayout.addWidget(self.labelDatafilesNon, 4, 0)
        self.windowLayout.addWidget(self.browseBtnDatafilesNon, 4, 1)
        self.windowLayout.addWidget(self.emptyPlainTextNonDatafiles, 4, 2)
        self.windowLayout.addWidget(self.lineEditDatafilesNon, 4, 3)

        # Created UI element Region FIPs Map Nonroad
        self.labelFipsNon = QLabel()
        self.labelFipsNon.setText("Region FIPS Map")
        self.labelFipsNon.setToolTip("Select Region FIPS Map (production region to Nonroad FIPS mapping) dataset")
        self.browseBtnFipsNon = QPushButton("Browse", self)
        self.browseBtnFipsNon.setFixedWidth(100)
        self.browseBtnFipsNon.clicked.connect(self.getfilesFipsNon)
        # Add Empty PlainText
        self.emptyPlainTextNonRegFips = QLabel()
        self.emptyPlainTextNonRegFips.setFixedWidth(90)
        self.lineEditFipsNon = QLineEdit(self)
        self.lineEditFipsNon.setFixedWidth(100)
        self.windowLayout.addWidget(self.labelFipsNon, 5, 0)
        self.windowLayout.addWidget(self.browseBtnFipsNon, 5, 1)
        self.windowLayout.addWidget(self.emptyPlainTextNonRegFips, 5, 2)
        self.windowLayout.addWidget(self.lineEditFipsNon, 5, 3)

        # Created UI element Region Nonroad Irrigation
        self.labelNonIrrig = QLabel()
        self.labelNonIrrig.setText("Irrigation")
        self.labelNonIrrig.setToolTip("Select irrigation dataset")
        self.browseBtnNonIrrig = QPushButton("Browse", self)
        self.browseBtnNonIrrig.setFixedWidth(100)
        self.browseBtnNonIrrig.clicked.connect(self.getfilesNonIrrig)
        # Add Empty PlainText
        self.emptyPlainTextNonIrri = QLabel()
        self.emptyPlainTextNonIrri.setFixedWidth(90)
        self.lineEditNonIrrig = QLineEdit(self)
        self.lineEditNonIrrig.setFixedWidth(100)
        self.windowLayout.addWidget(self.labelNonIrrig, 6, 0)
        self.windowLayout.addWidget(self.browseBtnNonIrrig, 6, 1)
        self.windowLayout.addWidget(self.emptyPlainTextNonIrri, 6, 2)
        self.windowLayout.addWidget(self.lineEditNonIrrig, 6, 3)

        # Created UI element Region Nonroad Encode Names
        self.labelNonEncodeNames = QLabel()
        self.labelNonEncodeNames.setText("Encode Names")
        self.labelNonEncodeNames.setToolTip("Encode feedstock, tillage type and activity names")
        self.comboBoxEncodeNames = QComboBox(self)
        self.comboBoxEncodeNames.setFixedWidth(100)
        self.comboBoxEncodeNames.addItem("Yes")
        self.comboBoxEncodeNames.addItem("No")
        self.comboBoxEncodeNames.setCurrentText("Yes")
        self.windowLayout.addWidget(self.labelNonEncodeNames, 7, 0)
        self.windowLayout.addWidget(self.comboBoxEncodeNames, 7, 1)

        # Created UI element Feedstock Measure Type Nonroad
        self.labelFeedMeasureTypeNon = QLabel()
        self.labelFeedMeasureTypeNon.setText("Feedstock Measure Type")
        self.labelFeedMeasureTypeNon.setToolTip("Enter Feedstock Measure Type identifier")
        self.lineEditFeedMeasureTypeNon = QLineEdit()
        self.lineEditFeedMeasureTypeNon.setFixedWidth(100)
        self.regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(self.regex)
        self.lineEditFeedMeasureTypeNon.setValidator(validator)
        # Set Default text
        self.lineEditFeedMeasureTypeNon.setText("harvested")
        self.windowLayout.addWidget(self.labelFeedMeasureTypeNon, 8, 0)
        self.windowLayout.addWidget(self.lineEditFeedMeasureTypeNon, 8, 1)

        # Created UI element Irrigation Feedstock Measure Type Nonroad
        self.labelFeedMeasureTypeIrrigNon = QLabel()
        self.labelFeedMeasureTypeIrrigNon.setText("Irrigation Feedstock Measure Type")
        self.labelFeedMeasureTypeIrrigNon.setToolTip(
            "Production table of identifier for irrigation activity calculation")
        self.lineEditFeedMeasureTypeIrrigNon = QLineEdit()
        self.lineEditFeedMeasureTypeIrrigNon.setFixedWidth(100)
        self.regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(self.regex)
        self.lineEditFeedMeasureTypeIrrigNon.setValidator(validator)
        self.lineEditFeedMeasureTypeIrrigNon.setText("planted")
        self.windowLayout.addWidget(self.labelFeedMeasureTypeIrrigNon, 9, 0)
        self.windowLayout.addWidget(self.lineEditFeedMeasureTypeIrrigNon, 9, 1)

        # Created UI element Irrigation Feedstock Names
        self.labelIrrigationFeedNamesNon = QLabel()
        self.labelIrrigationFeedNamesNon.setText("Irrigation Feedstock Names")
        self.labelIrrigationFeedNamesNon.setToolTip("List of irrigated feedstocks")
        self.lineEditFeedIrrigNamesNon = QLineEdit()
        self.lineEditFeedIrrigNamesNon.setFixedWidth(100)
        self.regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(self.regex)
        self.lineEditFeedIrrigNamesNon.setValidator(validator)
        self.lineEditFeedIrrigNamesNon.setText("corn garin")
        self.windowLayout.addWidget(self.labelIrrigationFeedNamesNon, 10, 0)
        self.windowLayout.addWidget(self.lineEditFeedIrrigNamesNon, 10, 1)

        # Created UI element Time Resource Name
        self.labelTimeResNamesNon = QLabel()
        self.labelTimeResNamesNon.setText("Time Resource Name")
        self.labelTimeResNamesNon.setToolTip("Equipment table row identifier")
        self.lineEditTimeResNamesNon = QLineEdit()
        self.lineEditTimeResNamesNon.setFixedWidth(100)
        self.regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(self.regex)
        self.lineEditTimeResNamesNon.setValidator(validator)
        self.lineEditTimeResNamesNon.setText("time")
        self.windowLayout.addWidget(self.labelTimeResNamesNon, 11, 0)
        self.windowLayout.addWidget(self.lineEditTimeResNamesNon, 11, 1)

        # Created UI element Forestry Feedstock Names
        self.labelForestryNamesNon = QLabel()
        self.labelForestryNamesNon.setText("Forestry Feedstock Names")
        self.labelForestryNamesNon.setToolTip("Different allocation indicators of forest feedstocks")
        self.lineEditForestryNamesNon = QLineEdit(self)
        self.lineEditForestryNamesNon.setFixedWidth(100)
        self.regex = QtCore.QRegExp("[a-z-A-Z_,]+")
        validator = QtGui.QRegExpValidator(self.regex)
        self.lineEditForestryNamesNon.setValidator(validator)
        self.lineEditForestryNamesNon.setText("forest residues, forest whole tree")
        self.windowLayout.addWidget(self.labelForestryNamesNon, 12, 0)
        self.windowLayout.addWidget(self.lineEditForestryNamesNon, 12, 1)

        # Created UI element Temperature
        self.labelTemper = QLabel()
        self.labelTemper.setText("Temperature")
        self.labelTemper.setToolTip("Enter temperature range for NONROAD")
        self.windowLayout.addWidget(self.labelTemper, 13, 0)

        # Created UI element Minimum Temperature
        self.labelMinTemp = QLabel()
        self.labelMinTemp.setText("Minimum")
        self.lineEditMinTemp = QLineEdit(self)
        self.lineEditMinTemp.setFixedWidth(100)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditMinTemp.setValidator(self.onlyFlaot)
        self.lineEditMinTemp.setText("50")
        self.windowLayout.addWidget(self.labelMinTemp, 14, 0)
        self.windowLayout.addWidget(self.lineEditMinTemp, 14, 1)

        # Created UI element Maximum Temperature
        self.labelMaxTemp = QLabel()
        self.labelMaxTemp.setText("Maximum")
        self.lineEditMaxTemp = QLineEdit()
        self.lineEditMaxTemp.setFixedWidth(100)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditMaxTemp.setValidator(self.onlyFlaot)
        self.lineEditMaxTemp.setText("68.8")
        self.windowLayout.addWidget(self.labelMaxTemp, 15, 0)
        self.windowLayout.addWidget(self.lineEditMaxTemp, 15, 1)

        # Created UI element Mean Temperature
        self.labelMeanTemp = QLabel()
        self.labelMeanTemp.setText("Mean")
        self.lineEditMeanTemp = QLineEdit(self)
        self.lineEditMeanTemp.setFixedWidth(100)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditMeanTemp.setValidator(self.onlyFlaot)
        self.lineEditMeanTemp.setText("60")
        self.windowLayout.addWidget(self.labelMeanTemp, 16, 0)
        self.windowLayout.addWidget(self.lineEditMeanTemp, 16, 1)

        # Created UI element Diesel
        self.labelDiesel = QLabel()
        self.labelDiesel.setText("Diesel")
        self.windowLayout.addWidget(self.labelDiesel, 17, 0)

        # Created UI element Low Heating Value
        self.labelLowHeat = QLabel()
        self.labelLowHeat.setText("Low Heating Value")
        self.labelLowHeat.setToolTip("Lower Heating Value for diesel fuel")
        self.lineEditLowHeat = QLineEdit(self)
        self.lineEditLowHeat.setFixedWidth(100)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 6)
        self.lineEditLowHeat.setValidator(self.onlyFlaot)
        self.lineEditLowHeat.setText("0.012845")
        self.windowLayout.addWidget(self.labelLowHeat, 18, 0)
        self.windowLayout.addWidget(self.lineEditLowHeat, 18, 1)

        # Created UI element NH3 Emission Factor
        self.labelNH3 = QLabel()
        self.labelNH3.setText("NH3 Emission Factor")
        self.labelNH3.setToolTip("NH3 Emissionn Factor for diesel fuel")
        self.lineEditNH3 = QLineEdit(self)
        self.lineEditNH3.setFixedWidth(100)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 6)
        self.lineEditNH3.setValidator(self.onlyFlaot)
        self.lineEditNH3.setText("0.68")
        self.windowLayout.addWidget(self.labelNH3, 19, 0)
        self.windowLayout.addWidget(self.lineEditNH3, 19, 1)

        # Created UI element Hydrocarbon to VOC Conversion Factor
        self.labelHydeo = QLabel()
        self.labelHydeo.setText("Hydrocarbon to VOC Conversion Factor")
        self.labelHydeo.setToolTip("VOC Conversion Factor for Hydrocarbon Emission components")
        self.lineEditHydro = QLineEdit()
        self.lineEditHydro.setFixedWidth(100)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 6)
        self.lineEditHydro.setValidator(self.onlyFlaot)
        self.lineEditHydro.setText("1.053")
        self.windowLayout.addWidget(self.labelHydeo, 20, 0)
        self.windowLayout.addWidget(self.lineEditHydro, 20, 1)

        # Created UI element PM10 to PM2.5 Conversion Factor
        self.labelPM10 = QLabel()
        self.labelPM10.setText("PM10 to PM2.5 Conversion Factor")
        self.labelPM10.setToolTip("PM10 to PM2.5 Conversion Factor")
        self.lineEditPM10 = QLineEdit(self)
        self.lineEditPM10.setFixedWidth(100)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 6)
        self.lineEditPM10.setValidator(self.onlyFlaot)
        self.lineEditPM10.setText("0.97")
        self.windowLayout.addWidget(self.labelPM10, 21, 0)
        self.windowLayout.addWidget(self.lineEditPM10, 21, 1)

    # CHeck for consistent input for year
    def handleItemPressed(self, index):

        print(str(self.comboBoxYear.currentText()))
        print(str(self.comboBoxYearNon.currentText()))

        fieldValues = set()
        fieldNames = []

        if self.tabMoves.isEnabled():
            fieldValues.add(self.comboBoxYear.currentText())
            fieldNames.append("MOVES")

        if self.tabNonroad.isEnabled():
            fieldValues.add(self.comboBoxYearNon.currentText())
            fieldNames.append("NONROAD")

        print(fieldValues)
        if len(fieldValues) == 1:
            self.comboBoxYearNon.setStyleSheet("border: 1px solid black;color: black ")
            self.comboBoxYear.setStyleSheet("border: 1px solid black;color: black ")
            self.labelYearErrorMsg.setText("")
            self.labelYearNonErrorMsg.setText("")

        else:
            self.comboBoxYearNon.setStyleSheet("border: 2px solid red;color: red ")
            self.comboBoxYear.setStyleSheet("border: 2px solid red;color: red ")

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
        # self.windowLayout.setColumnStretch(4, 1)

        self.tabEmissionFactors.setLayout(self.windowLayout)

        # Created UI element Feedstock Measure Type Emission Factors
        self.labelFeedMeasureTypeEF = QLabel()
        self.labelFeedMeasureTypeEF.setText("Feedstock Measure Type")
        self.labelFeedMeasureTypeEF.setToolTip("Production table Identifier")
        self.lineEditFeedMeasureTypeEF = QLineEdit()
        self.lineEditFeedMeasureTypeEF.setFixedWidth(100)
        regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(regex)
        self.lineEditFeedMeasureTypeEF.setValidator(validator)
        self.lineEditFeedMeasureTypeEF.setText("harvested")
        self.windowLayout.addWidget(self.labelFeedMeasureTypeEF, 2, 0)
        self.windowLayout.addWidget(self.lineEditFeedMeasureTypeEF, 2, 1)

        # Created UI element Emission Factors
        self.labelEmiFact = QLabel()
        self.labelEmiFact.setText("Emission Factors")
        self.labelEmiFact.setToolTip("Emission Factors as lb pollutant per lb resource subtype")
        self.browseBtnEmiFact = QPushButton("Browse", self)
        self.browseBtnEmiFact.setFixedWidth(100)
        self.browseBtnEmiFact.clicked.connect(self.getfilesEmiFact)
        # Add Empty PlainText
        self.emptyPlainTextEmiFact = QLabel()
        self.emptyPlainTextEmiFact.setFixedWidth(90)
        self.lineEditEmiFact = QLineEdit(self)
        self.lineEditEmiFact.setFixedWidth(100)
        self.windowLayout.addWidget(self.labelEmiFact, 3, 0)
        self.windowLayout.addWidget(self.browseBtnEmiFact, 3, 1)
        self.windowLayout.addWidget(self.emptyPlainTextEmiFact, 3, 2)
        self.windowLayout.addWidget(self.lineEditEmiFact, 3, 3)

        # Created UI element Resource Distribution
        self.labelResDist = QLabel()
        self.labelResDist.setText("Resource Distribution")
        self.labelResDist.setToolTip("Resource subtype distribution for all resources")
        self.browseBtnReDist = QPushButton("Browse", self)
        self.browseBtnReDist.setFixedWidth(100)
        self.browseBtnReDist.clicked.connect(self.getfilesResDist)
        # Add Empty PlainText
        self.emptyPlainTextResDistri = QLabel()
        self.emptyPlainTextResDistri.setFixedWidth(90)
        self.lineEditResDist = QLineEdit(self)
        self.lineEditResDist.setFixedWidth(100)
        self.windowLayout.addWidget(self.labelResDist, 4, 0)
        self.windowLayout.addWidget(self.browseBtnReDist, 4, 1)
        self.windowLayout.addWidget(self.emptyPlainTextResDistri, 4, 2)
        self.windowLayout.addWidget(self.lineEditResDist, 4, 3)

        # Add Empty PlainText
        self.emptyPlainText2 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText2, 5, 0)

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
        # self.windowLayout.setColumnStretch(4, 1)

        self.tabFugitiveDust.setLayout(self.windowLayout)

        # Created UI element Feedstock Measure Type - Fugitive Dust
        self.labelFeedMeasureTypeFD = QLabel()
        self.labelFeedMeasureTypeFD.setText("Feedstock Measure Type")
        self.labelFeedMeasureTypeFD.setToolTip("Production table identifier ")
        self.lineEditFeedMeasureTypeFD = QLineEdit(self)
        self.lineEditFeedMeasureTypeFD.setFixedWidth(100)
        regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(regex)
        self.lineEditFeedMeasureTypeFD.setValidator(validator)
        self.lineEditFeedMeasureTypeFD.setText("harvested")
        self.windowLayout.addWidget(self.labelFeedMeasureTypeFD, 2, 0)
        self.windowLayout.addWidget(self.lineEditFeedMeasureTypeFD, 2, 1)

        # Created UI element Emission Factors - Fugitive Dust
        self.labelEmiFactFD = QLabel()
        self.labelEmiFactFD.setText("Emission Factors")
        self.labelEmiFactFD.setToolTip("Pollutant emission factors for resources")
        self.browseBtnEmiFactFD = QPushButton("Browse", self)
        self.browseBtnEmiFactFD.setFixedWidth(100)
        self.browseBtnEmiFactFD.clicked.connect(self.getfilesEmiFactFD)
        # Add Empty PlainText
        self.emptyPlainTextEmiFactFD = QLabel()
        self.emptyPlainTextEmiFactFD.setFixedWidth(90)
        self.lineEditEmiFactFD = QLineEdit(self)
        self.lineEditEmiFactFD.setFixedWidth(100)
        self.windowLayout.addWidget(self.labelEmiFactFD, 3, 0)
        self.windowLayout.addWidget(self.browseBtnEmiFactFD, 3, 1)
        self.windowLayout.addWidget(self.emptyPlainTextEmiFactFD, 3, 2)
        self.windowLayout.addWidget(self.lineEditEmiFactFD, 3, 3)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 4, 0)

    # Functions used for Emission Factors - - Fugitive Dust

    def getfilesEmiFactFD(self):
        fileNameTruckCapaFD = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        selectedFileNameTruckCapaFD = fileNameTruckCapaFD[0].split("FPEAM/")
        self.lineEditEmiFactFD.setText(selectedFileNameTruckCapaFD[1])

###################################################################

    # Run Button
    def runTheSelectedModules(self):

        attributeValueObj = AttributeValueStorage()

        tmpFolder = tempfile.mkdtemp()

        # check if scenario name and project path is entered or not
        if self.lineEditProjectPath.text() == "":
            self.lineEditProjectPath.setStyleSheet("border: 2px solid red;")
            self.lineEditScenaName.setStyleSheet("border: 2px solid red;")
            return
        else:


            # FPEAM Home Page attributes value initialization

            attributeValueObj.scenarioName = self.lineEditScenaName.text().strip()
            attributeValueObj.projectPath = self.lineEditProjectPath.text().strip()

            # Check which module is selected
            self.selected_module_string = ""
            if self.checkBoxMoves.isChecked():
                #attributeValueObj.module = self.selected_module_list.append(self.checkBoxMoves.text())
                self.selected_module_string += "'" + self.checkBoxMoves.text() + "'"
                attributeValueObj.module = self.selected_module_string
                self.selected_module_string += ", "
            if self.checkBoxNonroad.isChecked():

                #attributeValueObj.module = self.selected_module_list.append(self.checkBoxNonroad.text())
                self.selected_module_string += "'" + self.checkBoxNonroad.text() + "'"
                attributeValueObj.module = self.selected_module_string
                self.selected_module_string += ", "
            if self.checkBoxEmissionFactors.isChecked():

                #attributeValueObj.module = self.selected_module_list.append(self.checkBoxEmissionFactors.text())
                self.selected_module_string +=  "'" + self.checkBoxEmissionFactors.text() + "'"
                attributeValueObj.module = self.selected_module_string
                self.selected_module_string += ", "
            if self.checkBoxFugitiveDust.isChecked():

                #attributeValueObj.module = "'" + self.selected_module_list.append(self.checkBoxFugitiveDust.text())
                self.selected_module_string +=  "'" + self.checkBoxFugitiveDust.text() + "'"
                attributeValueObj.module = self.selected_module_string


            changedVerboLoggerLevel = self.comboBoxVerbosityLevel.currentText()
            if changedVerboLoggerLevel:
                attributeValueObj.loggerLevel = changedVerboLoggerLevel

            changedBackfill = self.comboBoxBF.currentText()
            if changedBackfill:
                if changedBackfill == "No":
                    changedBackfill = False
                else:
                    changedBackfill = True
                attributeValueObj.backfill = changedBackfill

            changedRouterEngine = self.comboBoxRE.currentText()
            if changedRouterEngine:
                if changedRouterEngine == "No":
                    changedRouterEngine = False
                else:
                    changedRouterEngine = True
                attributeValueObj.useRouterEngine = changedRouterEngine

            changedEqPath = self.lineEditEq.text().strip()
            if changedEqPath:
                attributeValueObj.equipment = changedEqPath

            changedProdPath = self.lineEditProd.text().strip()
            if changedProdPath:
                attributeValueObj.production = changedProdPath

            changedFeedLossFactPath = self.lineEditFedLossFact.text().strip()
            if changedFeedLossFactPath:
                attributeValueObj.feedstockLossFactors = changedFeedLossFactPath

            changedTranGraphPath = self.lineEditTransGraph.text().strip()
            if changedTranGraphPath:
                attributeValueObj.transportationGraph = changedTranGraphPath


            ###############################################################################################################

            # Moves attributes value initialization

            if self.radioButtonByState.isChecked():
                attributeValueObj.aggegationLevel = "Moves By State"
            if self.radioButtonByStateandFeed.isChecked():
                attributeValueObj.aggegationLevel = "Moves By State and Feedstock"

            changedcachedResults = self.comboBoxCachedResUse.currentText()
            if changedcachedResults:
                attributeValueObj.cachedResults = changedcachedResults

            changedFeedstockMeasureTypeMoves = self.lineEditFeedMeasureType.text().strip()
            if changedFeedstockMeasureTypeMoves:
                attributeValueObj.feedstockMeasureTypeMoves = changedFeedstockMeasureTypeMoves

            changedVMTPerTruck = self.lineEditVMTperTruck.text().strip()
            if changedVMTPerTruck:
                attributeValueObj.vMTPerTruck = changedVMTPerTruck

            changedNoOfTrucksUsed = self.spinBoxNoofTruck.text()
            if changedNoOfTrucksUsed:
                attributeValueObj.noOfTrucksUsed = changedNoOfTrucksUsed

            changedYearMoves = self.comboBoxYear.currentText()
            if changedYearMoves:
                attributeValueObj.yearMoves = changedYearMoves

            changedMonth = self.comboBoxMonth.currentText()
            if changedMonth:
                attributeValueObj.month = changedMonth

            changedDate = self.comboBoxDate.currentText()
            if changedDate:
                attributeValueObj.date = changedDate

            changedBegHr = self.comboBoxBegHr.currentText()
            if changedBegHr:
                attributeValueObj.beginningHr = changedBegHr

            changedEndHr = self.comboBoxEndHr.currentText()
            if changedEndHr:
                attributeValueObj.endingHr = changedEndHr

            changedDayType = self.comboBoxDayType.currentText()
            if changedDayType:
                attributeValueObj.dayType = changedDayType

            changedTruckCapacityPath = self.lineEditTruckCapa.text().strip()
            if changedTruckCapacityPath:
                attributeValueObj.truckCapacity = changedTruckCapacityPath

            changedAvftPath = self.lineEditAVFT.text().strip()
            if changedAvftPath:
                attributeValueObj.avft = changedAvftPath

            changedFipsMapNovesPath = self.lineEditFips.text().strip()
            if changedFipsMapNovesPath:
                attributeValueObj.regionFipsMapMoves = changedFipsMapNovesPath

            changedDatafilesMovesPath = self.lineEditDatafiles.text().strip()
            if changedDatafilesMovesPath:
                attributeValueObj.movesDatafilesPath = changedDatafilesMovesPath

            changedRuralRes = self.lineEditRuralRes.text().strip()
            if changedRuralRes:
                attributeValueObj.ruralRestricted = changedRuralRes

            changedRuralUnres = self.lineEditRuralUnres.text().strip()
            if changedRuralUnres:
                attributeValueObj.ruralUnrestricted = changedRuralUnres

            changedUrbanRes = self.lineEditUrbanRes.text().strip()
            if changedUrbanRes:
                attributeValueObj.urbanRestricted = changedUrbanRes

            changedUrbanUnres = self.lineEditUrbanUnres.text().strip()
            if changedUrbanUnres:
                attributeValueObj.urbanUnrestricted = changedUrbanUnres

            ###############################################################################################################

            # Nonroad attributes value initialization

            changedYearNonroad = self.comboBoxYearNon.currentText()
            if changedYearNonroad:
                attributeValueObj.yearNonroad = changedYearNonroad

            changedRegionFIPSMapNonroad = self.lineEditFipsNon.text().strip()
            if changedRegionFIPSMapNonroad:
                attributeValueObj.regionFipsMapNonroad = changedRegionFIPSMapNonroad

            changedNonroadDatafiles = self.lineEditDatafilesNon.text().strip()
            if changedNonroadDatafiles:
                attributeValueObj.nonroadDatafilesPath = changedNonroadDatafiles

            changedNonroadIrrigation = self.lineEditNonIrrig.text().strip()
            if changedNonroadIrrigation:
                attributeValueObj.irrigation = changedNonroadIrrigation

            changedEncodeName = self.comboBoxEncodeNames.currentText()
            if changedEncodeName:
                attributeValueObj.encodeNames = changedEncodeName

            changedFeedstockMeasureTypeNonroad = self.lineEditFeedMeasureTypeNon.text().strip()
            if changedFeedstockMeasureTypeNonroad:
                attributeValueObj.feedstockMeasureTypeNon = changedFeedstockMeasureTypeNonroad

            changedIrrigationFeedMeasureType = self.lineEditFeedMeasureTypeIrrigNon.text().strip()
            if changedIrrigationFeedMeasureType:
                attributeValueObj.irrigationFeedstockMeasureType = changedIrrigationFeedMeasureType

            changedIrrigationFeedNames = self.lineEditFeedIrrigNamesNon.text().strip()
            if changedIrrigationFeedNames:
                attributeValueObj.irrigatedFeedstockNames = changedIrrigationFeedNames

            changedTimeResName = self.lineEditTimeResNamesNon.text().strip()
            if changedTimeResName:
                attributeValueObj.timeResourceNameNon = changedTimeResName

            changedForestryFeedNames = self.lineEditForestryNamesNon.text().strip()
            if changedForestryFeedNames:
                attributeValueObj.forestryFeedstockNames = changedForestryFeedNames

            changedTempMin = self.lineEditMinTemp.text().strip()
            if changedTempMin:
                attributeValueObj.tempMin = changedTempMin

            changedTempMax = self.lineEditMaxTemp.text().strip()
            if changedTempMax:
                attributeValueObj.tempMax = changedTempMax

            changedTempMean = self.lineEditMeanTemp.text().strip()
            if changedTempMean:
                attributeValueObj.tempMean = changedTempMean

            changeddieselLHV = self.lineEditLowHeat.text().strip()
            if changeddieselLHV:
                attributeValueObj.dieselLHV = changeddieselLHV

            changeddieselNH3 = self.lineEditNH3.text().strip()
            if changeddieselNH3:
                attributeValueObj.dieselNh3Ef = changeddieselNH3

            changeddieselHydrotoVOC = self.lineEditHydro.text().strip()
            if changeddieselHydrotoVOC:
                attributeValueObj.tempMean = changeddieselHydrotoVOC

            changedPMConversionFact = self.lineEditPM10.text().strip()
            if changedPMConversionFact:
                attributeValueObj.dieselPm10topm25 = changedPMConversionFact


        ###############################################################################################################

            # Emission Factors attributs value Initialization

            changedFeedMeasureTypeFEF= self.lineEditFeedMeasureTypeEF.text().strip()
            if changedFeedMeasureTypeFEF:
                attributeValueObj.feedMeasureTypeEF = changedFeedMeasureTypeFEF

            changedEmissionFactEFPath = self.lineEditEmiFact.text().strip()
            if changedEmissionFactEFPath:
                attributeValueObj.emissionFactorsEF = changedEmissionFactEFPath

            changedResDistriEFPath = self.lineEditResDist.text().strip()
            if changedResDistriEFPath:
                attributeValueObj.resourceDistributionEF = changedResDistriEFPath


            ###############################################################################################################

            # Fugititve Dust attributes value initialization

            changedFeedMeasureTypeFD = self.lineEditFeedMeasureTypeFD.text().strip()
            if changedFeedMeasureTypeFD:
                attributeValueObj.feedMeasureTypeFD = changedFeedMeasureTypeFD

            changedEmissionFactFDPath = self.lineEditEmiFactFD.text().strip()
            if changedEmissionFactFDPath:
                attributeValueObj.emissionFactorsFD = changedEmissionFactFDPath


            ###############################################################################################################


            # Call config file creation function - working code
            # if self.checkBoxMoves.isChecked():
            #     movesConfigCreationObj = movesConfigCreation(tmpFolder)
            # if self.checkBoxNonroad.isChecked():
            #     nonroadConfigCreationObj = nonroadConfigCreation(tmpFolder)
            if self.checkBoxEmissionFactors.isChecked():
                emissionFactorsConfigCreationObj = emissionFactorsConfigCreation(tmpFolder, attributeValueObj)
            # if self.checkBoxFugitiveDust.isChecked():
            #     fugitiveDustConfigCreationObj = fugitiveDustConfigCreation(tmpFolder)
            runConfigObj = runConfigCreation(tmpFolder, attributeValueObj)

            # run FugitiveDust module
            command = "fpeam " + runConfigObj + " --emissionfactors_config " + emissionFactorsConfigCreationObj
            print(command)
            t = threading.Thread(target= runCommand , args = (runConfigObj , emissionFactorsConfigCreationObj, attributeValueObj, ))
            t.start()

            while t.is_alive():
                print("alive. Waiting for 1 second to recheck")
                time.sleep(1)

            t.join()

            # Display logs in result tab after completion of running
            self.centralwidget.setCurrentWidget(self.tabResult)

            # Set logs to Plaintext in Result tab
            self.plainTextLog.setPlainText(attributeValueObj.logContents)

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
        self.plainTextLog.setFixedHeight(200)
        windowLayout.addWidget(self.plainTextLog, 0, 0, 1 , 4)

        self.labelMOVESGraph = QLabel()
        self.labelMOVESGraph.setFixedHeight(350)
        self.labelMOVESGraph.setFixedWidth(500)
        windowLayout.addWidget(self.labelMOVESGraph,1 , 0)

        self.plainLabel1 = QLabel()
        windowLayout.addWidget(self.plainLabel1, 1, 1)

        self.labelNONROADGraph = QLabel()
        self.labelNONROADGraph.setFixedHeight(350)
        self.labelNONROADGraph.setFixedWidth(500)
        windowLayout.addWidget(self.labelNONROADGraph, 1, 2)

        self.labelEmissionFactorsGraph = QLabel()
        self.labelEmissionFactorsGraph.setFixedHeight(350)
        self.labelEmissionFactorsGraph.setFixedWidth(500)
        windowLayout.addWidget(self.labelEmissionFactorsGraph,2 , 0)

        self.plainLabel2 = QLabel()
        windowLayout.addWidget(self.plainLabel2, 2, 1)

        self.labelFugitivedustGraph = QLabel()
        self.labelFugitivedustGraph.setFixedHeight(350)
        self.labelFugitivedustGraph.setFixedWidth(500)
        windowLayout.addWidget(self.labelFugitivedustGraph, 2, 2)

        self.tabResult.setLayout(windowLayout)


        #########################################################################################################################

    def setupUi(self, OtherWindow):

        OtherWindow.setObjectName("OtherWindow")
        OtherWindow.setGeometry(0,0,500,700)
        self.centralwidget = QtWidgets.QTabWidget(OtherWindow)
        OtherWindow.setCentralWidget(self.centralwidget)
        self.centralwidget.setGeometry(0,0,500,700)

        self.centralwidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)

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
    app = QtWidgets.QApplication(sys.argv)
    OtherWindow = QtWidgets.QMainWindow()
    OtherWindow.setWindowTitle("FPEAM")
    ui = AlltabsModule()
    ui.setupUi(OtherWindow)
    OtherWindow.show()
    sys.exit(app.exec_())