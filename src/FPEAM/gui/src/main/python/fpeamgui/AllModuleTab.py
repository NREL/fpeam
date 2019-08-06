# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'OtherWindow.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

import logging
import os
import sys,time
import random, string

from PyQt5 import QtCore, QtGui, QtWidgets, Qt
from PyQt5 import QtCore, QtGui, QtWidgets, Qt
from PyQt5.QtCore import QEventLoop, QTimer
from PyQt5.QtGui import  QDoubleValidator, QPixmap
from PyQt5.QtWidgets import QComboBox, QPushButton, QFileDialog, QPlainTextEdit, \
    QScrollArea, QProgressBar
from PyQt5.QtWidgets import QGridLayout, QLabel, QLineEdit, QSpinBox, QCheckBox

from FPEAM.gui.src.main.python.fpeamgui.AttributeValueStorage import AttributeValueStorage
from FPEAM import (IO, FPEAM, utils)

from FPEAM.gui.src.main.python.fpeamgui.run_config import runConfigCreation
from FPEAM.gui.src.main.python.fpeamgui.MovesConfig import movesConfigCreation
from FPEAM.gui.src.main.python.fpeamgui.NonroadConfig import nonroadConfigCreation
from FPEAM.gui.src.main.python.fpeamgui.emissionFactorsConfig import emissionFactorsConfigCreation
from FPEAM.gui.src.main.python.fpeamgui.fugitiveDustConfig import fugitiveDustConfigCreation

import tempfile
import threading

import matplotlib.pyplot as plt
plt.rcdefaults()

WIDTH = 900
HEIGHT = 800

class AlltabsModule(QtWidgets.QWidget):

    def setupUIHomePage(self):
        # Home Page tab created
        self.tabHome = QtWidgets.QWidget()
        self.tabHome.setWindowTitle("HOME")
        # Home Page tab added
        self.centralwidget.addTab(self.tabHome, "HOME")

        # Home Page code start
        self.windowLayout = QGridLayout()
        self.windowLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.windowLayout.setColumnStretch(5, 1)

        self.scrollAreaFPEAM = QScrollArea(self.tabHome)
        self.scrollAreaFPEAM.setWidgetResizable(True)
        self.scrollAreaFPEAM.resize(WIDTH, HEIGHT)
        self.scrollAreaFPEAM.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollAreaFPEAM.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self.innerWidgetFPEAM = QtWidgets.QWidget()
        self.innerWidgetFPEAM.resize(WIDTH, HEIGHT)
        self.scrollAreaFPEAM.setWidget(self.innerWidgetFPEAM)
        self.innerWidgetFPEAM.setLayout(self.windowLayout)

        # Created UI element - Title
        self.labelTitleFPEAM = QLabel()
        self.labelTitleFPEAM.setText("Feedstock Production Emissions to Air Model")
        self.labelTitleFPEAM.setObjectName("title")
        self.labelTitleFPEAM.setFixedHeight(39)
        self.labelTitleFPEAM.setAlignment(QtCore.Qt.AlignCenter)
        self.windowLayout.addWidget(self.labelTitleFPEAM, 0, 0, 1, 5)

        # Created UI element - Title Line
        self.labelTitleFPEAMLine = QLabel()
        pixmapLine = QPixmap('line.png')
        pixmap = pixmapLine.scaledToHeight(14)
        self.labelTitleFPEAMLine.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.windowLayout.addWidget(self.labelTitleFPEAMLine, 1, 0, 1, 5)

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
        self.windowLayout.addWidget(self.labelScenaName, 2,0)
        self.windowLayout.addWidget(self.lineEditScenaName, 2, 1, 1, 4)

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
        self.windowLayout.addWidget(self.labelProjPath, 3, 0)
        self.windowLayout.addWidget(self.browseBtn, 3, 1)
        self.windowLayout.addWidget(self.lineEditProjectPath, 3, 2, 1, 3)

        # Created UI element Module Selection
        self.labelModules = QLabel()
        self.labelModules.setText("Select Modules")
        self.labelModules.setFixedHeight(30)
        self.labelModules.setObjectName("subTitleLabels")
        self.labelModules.setStyleSheet("color: #000000;")
        self.checkBoxMoves = QCheckBox("MOVES")
        self.checkBoxMoves.setFixedWidth(120)
        self.checkBoxMoves.setFixedHeight(30)
        self.checkBoxMoves.setChecked(True)
        self.checkBoxMoves.stateChanged.connect(self.onStateChangedMoves)
        self.checkBoxNonroad = QCheckBox("NONROAD")
        self.checkBoxNonroad.setFixedWidth(120)
        self.checkBoxNonroad.setFixedHeight(30)
        self.checkBoxNonroad.setChecked(True)
        self.checkBoxNonroad.stateChanged.connect(self.onStateChangedNonroad)
        self.checkBoxEmissionFactors = QCheckBox("Emission Factors")
        self.checkBoxEmissionFactors.setFixedWidth(120)
        self.checkBoxEmissionFactors.setFixedHeight(30)
        self.checkBoxEmissionFactors.setChecked(True)
        self.checkBoxEmissionFactors.stateChanged.connect(self.onStateChangedEmissionFactors)
        self.checkBoxFugitiveDust = QCheckBox("Fugitve Dust")
        self.checkBoxFugitiveDust.setFixedWidth(120)
        self.checkBoxFugitiveDust.setFixedHeight(30)
        self.checkBoxFugitiveDust.setChecked(True)
        self.checkBoxFugitiveDust.stateChanged.connect(self.onStateChangedFugitiveDust)
        self.windowLayout.addWidget(self.labelModules, 4, 0, 1, 6)
        self.windowLayout.addWidget(self.checkBoxMoves, 5, 0)
        self.windowLayout.addWidget(self.checkBoxNonroad, 5, 1)
        self.windowLayout.addWidget(self.checkBoxEmissionFactors, 5, 2)
        self.windowLayout.addWidget(self.checkBoxFugitiveDust, 5, 3)

        #NREL Logo Label
        self.logoImage = QLabel()
        pixmap = QPixmap('logo.png')
        pixmap = pixmap.scaledToWidth(182)
        pixmap = pixmap.scaledToHeight(40)
        self.logoImage.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.windowLayout.addWidget(self.logoImage, 6, 0)

        # Created UI element Reset Button
        self.resetBtn = QPushButton("Reset", self)
        self.resetBtn.setFixedHeight(40)
        self.resetBtn.setFixedWidth(152)
        self.resetBtn.setObjectName("resetRunBtn")
        self.resetBtn.clicked.connect(self.rresetFields)
        self.windowLayout.addWidget(self.resetBtn, 6, 3)

        # Created UI element Run Button
        self.runBtn = QPushButton("Run", self)
        self.runBtn.setFixedWidth(152)
        self.runBtn.setFixedHeight(40)
        self.runBtn.setObjectName("resetRunBtn")
        self.runBtn.setStyleSheet("border-color: #028ACC; color : #ffffff; background-color : #028ACC;")
        self.runBtn.clicked.connect(self.runTheSelectedModules)
        self.windowLayout.addWidget(self.runBtn, 6, 4)

        # Custom Data Filepaths Label
        self.customDataFilepathsLabel = QLabel()
        self.customDataFilepathsLabel.setText("Custom Data Filepaths")
        self.customDataFilepathsLabel.setFixedHeight(30)
        self.customDataFilepathsLabel.setObjectName("subTitleLabels")
        self.windowLayout.addWidget(self.customDataFilepathsLabel, 7, 0, 1, 6)

        # Created UI element - Custom Dtatfiles below Line
        self.labelCustomDatafilsLine = QLabel()
        pixmapLine1 = QPixmap('line.png')
        pixmap1 = pixmapLine1.scaledToHeight(15)
        self.labelCustomDatafilsLine.setPixmap(pixmap1)
        self.resize(pixmap1.width(), pixmap1.height())
        self.windowLayout.addWidget(self.labelCustomDatafilsLine, 8, 0, 1, 6)

        # Expand/Collapse code
        # Created UI element Custom Data Filepaths FPEAM
        self.labelCustomDatafileFPEAMExpand = QPushButton()
        self.labelCustomDatafileFPEAMExpand.setFixedHeight(30)
        self.labelCustomDatafileFPEAMExpand.setFixedWidth(30)
        self.labelCustomDatafileFPEAMExpand.setObjectName("expandCollapseIcon")
        self.labelCustomDatafileFPEAMExpand.setIconSize(QtCore.QSize(40, 40))
        self.labelCustomDatafileFPEAMExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
        #self.labelCustomDatafileFPEAMExpand.setText(u'\u25B2')
        self.windowLayout.addWidget(self.labelCustomDatafileFPEAMExpand, 7, 5)

        self.customDatafileFPEAMexpandWidget = QtWidgets.QWidget()
        self.customDatafileFPEAMexpandWidget.setStyleSheet("border-color: #028ACC; border-style: outset; border-width: 1px;border-radius: 5px;")
        self.customDatafileFPEAMGridLayout = QtWidgets.QGridLayout()
        self.customDatafileFPEAMexpandWidget.setLayout(self.customDatafileFPEAMGridLayout)
        self.customDatafileFPEAMexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.customDatafileFPEAMexpandWidget, 9, 0, 1, 5)

        def labelCustomDatafileFPEAMOnClickEvent():
            if self.customDatafileFPEAMexpandWidget.isVisible():
                #self.labelCustomDatafileFPEAMExpand.setText(u'\u25B2')
                self.labelCustomDatafileFPEAMExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
                self.labelCustomDatafileFPEAMExpand.setIconSize(QtCore.QSize(40, 40))
                self.customDatafileFPEAMexpandWidget.setVisible(False)
            else:
                #self.labelCustomDatafileFPEAMExpand.setText(u'\u25BC')
                self.labelCustomDatafileFPEAMExpand.setIcon(QtGui.QIcon('downWardArrow.png'))
                self.labelCustomDatafileFPEAMExpand.setIconSize(QtCore.QSize(40, 40))
                self.customDatafileFPEAMexpandWidget.setVisible(True)

        self.labelCustomDatafileFPEAMExpand.clicked.connect(labelCustomDatafileFPEAMOnClickEvent)


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
        self.lineEditEq.setText("data/equipment/bts16_equipment.csv")
        self.lineEditEq.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditEq.setFixedHeight(30)
        self.customDatafileFPEAMGridLayout.addWidget(self.labelEq, 0, 0)
        self.customDatafileFPEAMGridLayout.addWidget(self.browseBtnEq, 0, 1)
        self.customDatafileFPEAMGridLayout.addWidget(self.lineEditEq, 0, 2, 1, 3)

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
        self.lineEditProd.setText("data/production/production_2015_bc1060.csv")
        self.lineEditProd.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditProd.setFixedHeight(30)
        self.customDatafileFPEAMGridLayout.addWidget(self.labelProd, 1, 0)
        self.customDatafileFPEAMGridLayout.addWidget(self.browseBtnProd, 1, 1)
        self.customDatafileFPEAMGridLayout.addWidget(self.lineEditProd, 1, 2, 1, 3)

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
        self.lineEditFedLossFact.setText("data/inputs/feedstock_loss_factors.csv")
        self.lineEditFedLossFact.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditFedLossFact.setFixedHeight(30)
        self.customDatafileFPEAMGridLayout.addWidget(self.labelFedLossFact, 2, 0)
        self.customDatafileFPEAMGridLayout.addWidget(self.browseBtnFLoss, 2, 1)
        self.customDatafileFPEAMGridLayout.addWidget(self.lineEditFedLossFact, 2, 2, 1, 3)

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
        self.lineEditTransGraph.setText("data/inputs/transportation_graph.csv")
        self.lineEditTransGraph.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditTransGraph.setFixedHeight(30)
        self.customDatafileFPEAMGridLayout.addWidget(self.labelTransGraph, 3, 0)
        self.customDatafileFPEAMGridLayout.addWidget(self.browseBtnTransGr, 3, 1)
        self.customDatafileFPEAMGridLayout.addWidget(self.lineEditTransGraph, 3, 2, 1, 3)

        # Advanced Options Label
        self.advOptionsLabel = QLabel()
        self.advOptionsLabel.setText("Advanced Options")
        self.advOptionsLabel.setFixedHeight(30)
        self.advOptionsLabel.setObjectName("subTitleLabels")
        self.windowLayout.addWidget(self.advOptionsLabel, 13, 0, 1, 6)

        # Created UI element - Advanced Optiones below Line
        self.labelAdvOptionsLine = QLabel()
        pixmapLine2 = QPixmap('line.png')
        pixmap2 = pixmapLine2.scaledToHeight(15)
        self.labelTitleFPEAMLine.setPixmap(pixmap2)
        self.resize(pixmap2.width(), pixmap2.height())
        self.windowLayout.addWidget(self.labelTitleFPEAMLine, 14, 0, 1, 6)

        # Expand/Collapse code
        # Created UI element Advanced Options FPEAM
        self.labelAdvOptionsFPEAMExpand = QPushButton()
        self.labelAdvOptionsFPEAMExpand.setStyleSheet("QPushButton { text-align : right}")
        self.labelAdvOptionsFPEAMExpand.setFixedHeight(30)
        self.labelAdvOptionsFPEAMExpand.setFixedWidth(30)
        self.labelAdvOptionsFPEAMExpand.setObjectName("expandCollapseIcon")
        #elf.labelAdvOptionsFPEAMExpand.setText(u'\u25B2')
        self.labelAdvOptionsFPEAMExpand.setIconSize(QtCore.QSize(36, 40))
        self.labelAdvOptionsFPEAMExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
        self.windowLayout.addWidget(self.labelAdvOptionsFPEAMExpand, 13, 5)

        self.advOptionsFPEAMexpandWidget = QtWidgets.QWidget()
        self.advOptionsFPEAMexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 1px;outline-style: solid; outline-color:black;border-radius: 5px;")
        self.advOptionsFPEAMGridLayout = QtWidgets.QGridLayout()
        self.advOptionsFPEAMexpandWidget.setLayout(self.advOptionsFPEAMGridLayout)
        self.advOptionsFPEAMexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.advOptionsFPEAMexpandWidget, 15, 0, 1, 5)

        def labelAdvOptionsFPEAMOnClickEvent():
            if self.advOptionsFPEAMexpandWidget.isVisible():
                #self.labelAdvOptionsFPEAMExpand.setText(u'\u25B2')
                self.labelAdvOptionsFPEAMExpand.setIconSize(QtCore.QSize(36, 40))
                self.labelAdvOptionsFPEAMExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
                self.advOptionsFPEAMexpandWidget.setVisible(False)
            else:
                #self.labelAdvOptionsFPEAMExpand.setText(u'\u25BC')
                self.labelAdvOptionsFPEAMExpand.setIconSize(QtCore.QSize(36, 40))
                self.labelAdvOptionsFPEAMExpand.setIcon(QtGui.QIcon('downWardArrow.png'))
                self.advOptionsFPEAMexpandWidget.setVisible(True)

        self.labelAdvOptionsFPEAMExpand.clicked.connect(labelAdvOptionsFPEAMOnClickEvent)

        # Ui Element - Logging Verbosity Level
        self.labelLoggVerboLevel = QLabel()
        self.labelLoggVerboLevel.setObjectName("allLabels")
        self.labelLoggVerboLevel.setAlignment(QtCore.Qt.AlignCenter)
        self.labelLoggVerboLevel.setText("Logging Level")
        self.labelLoggVerboLevel.setFixedHeight(30)
        self.labelLoggVerboLevel.setFixedWidth(155)
        self.comboBoxVerbosityLevel = QComboBox(self)
        self.comboBoxVerbosityLevel.setFixedWidth(155)
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
        self.advOptionsFPEAMGridLayout.addWidget(self.labelLoggVerboLevel, 0, 0)
        self.advOptionsFPEAMGridLayout.addWidget(self.comboBoxVerbosityLevel, 1, 0)

        # UI element  -  Router Engine
        self.labelRE = QLabel()
        self.labelRE.setObjectName("allLabels")
        self.labelRE.setAlignment(QtCore.Qt.AlignCenter)
        self.labelRE.setFixedHeight(30)
        self.labelRE.setFixedWidth(155)
        self.labelRE.setText("Use Router Engine")
        self.labelRE.setToolTip("Do you want to set Router Engine - Yes/No")
        self.comboBoxRE = QComboBox(self)
        self.comboBoxRE.setFixedWidth(155)
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
        self.advOptionsFPEAMGridLayout.addWidget(self.labelRE, 0, 1)
        self.advOptionsFPEAMGridLayout.addWidget(self.comboBoxRE, 1, 1)

        # UI element -  Backfill Flag
        self.labelBF = QLabel()
        self.labelBF.setObjectName("allLabels")
        self.labelBF.setFixedHeight(30)
        self.labelBF.setFixedWidth(155)
        self.labelBF.setAlignment(QtCore.Qt.AlignCenter)
        self.labelBF.setText("Backfill Missing Data")
        self.labelBF.setToolTip("Do you want to set Backfill Flag - Yes/No")
        self.comboBoxBF = QComboBox(self)
        self.comboBoxBF.setFixedWidth(155)
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
        self.advOptionsFPEAMGridLayout.addWidget(self.labelBF, 0, 2)
        self.advOptionsFPEAMGridLayout.addWidget(self.comboBoxBF, 1, 2)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.emptyPlainText3.setStyleSheet( "border-color: white;")
        self.emptyPlainText3.setFixedWidth(155)
        self.emptyPlainText3.setFixedHeight(60)
        self.advOptionsFPEAMGridLayout.addWidget(self.emptyPlainText3, 0, 3)

        # Add Empty PlainText
        self.emptyPlainText2 = QLabel()
        self.emptyPlainText2.setStyleSheet("border-color: white;")
        self.emptyPlainText2.setFixedWidth(155)
        self.emptyPlainText2.setFixedHeight(30)
        self.advOptionsFPEAMGridLayout.addWidget(self.emptyPlainText2, 0, 4)


        # Empty space
        self.labelEmpty1 = QLabel()
        self.windowLayout.addWidget(self.labelEmpty1, 18, 0, 1, 5)

        # Empty space
        self.labelEmpty2 = QLabel()
        self.windowLayout.addWidget(self.labelEmpty2, 19, 0, 1, 5)

        # Add Empty PlainText
        self.emptyPlainTextt = QLabel()
        self.windowLayout.addWidget(self.emptyPlainTextt, 20, 0)

        # Add Empty PlainText
        self.emptyPlainText10 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText10, 21, 0)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 22, 0)

        # Add Empty PlainText
        self.emptyPlainText14 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText14, 23, 0)

        # Add Empty PlainText
        self.emptyPlainText7 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText7, 24, 0)

        # Add Empty PlainText
        self.emptyPlainText11 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText11, 25, 0)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 26, 0)

        # Add Empty PlainText
        self.emptyPlainText13 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText13, 27, 0)

        # Add Empty PlainText
        self.emptyPlainText8 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText8, 28, 0)

        # Add Empty PlainText
        self.emptyPlainText9 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText9, 29, 0)

        # Add Empty PlainText
        self.emptyPlainText12 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText12, 30, 0)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 31, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 32, 0)


    # Checkbox - MOves Module - Checked

    def onStateChangedMoves(self,state1):
        if state1 == self.checkBoxMoves.isChecked():
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
        if fileName != "":
            selectedFileName = str(fileName).split(',')
            self.lineEditProjectPath.setText(selectedFileName[0])
        else:
            pass

    # Logging Verbosity Level
    def selectionchangecombo(self):
        self.comboBoxVerbosityLevel.currentText()

    # Equipment

    def getfilesEq(self):
        fileNameEq = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        if fileNameEq[0] != "":
            selectedFileNameEq = fileNameEq[0].split("FPEAM/")
            self.lineEditEq.setText(selectedFileNameEq[1])

    # Production

    def getfilesProd(self):
        fileNameProd = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        if fileNameProd[0] != "":
            selectedFileNameProd = fileNameProd[0].split("FPEAM/")
            self.lineEditProd.setText(selectedFileNameProd[1])

    # Feedstock Loss Factors

    def getfilesFLoss(self):
        fileNameFLoss = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        if fileNameFLoss[0] != "":
            selectedFileNameFLoss = fileNameFLoss[0].split("FPEAM/")
            self.lineEditFedLossFact.setText(selectedFileNameFLoss[1])

    # Transportation graph

    def getfilesTransGr(self):
        fileNameTransGr = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        if fileNameTransGr[0] != "":
            selectedFileNameTransGr = fileNameTransGr[0].split("FPEAM/")
            self.lineEditTransGraph.setText(selectedFileNameTransGr[1])


        ###########################################################################################################################################################################

    def setupUIMoves(self):

        # Moves code start
        self.windowLayout = QGridLayout()
        self.windowLayout.setSpacing(15)
        self.windowLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.windowLayout.setColumnStretch(6, 1)

        # MOves tab created
        self.tabMoves = QtWidgets.QWidget()
        # Moves tab added
        self.centralwidget.addTab(self.tabMoves, "MOVES")

        self.scrollAreaMOVES = QScrollArea(self.tabMoves)
        self.scrollAreaMOVES.setWidgetResizable(True)
        self.scrollAreaMOVES.resize(WIDTH,HEIGHT)
        self.scrollAreaMOVES.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollAreaMOVES.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self.innerWidgetMOVES = QtWidgets.QWidget()
        self.innerWidgetMOVES.resize(WIDTH,HEIGHT)
        self.scrollAreaMOVES.setWidget(self.innerWidgetMOVES)
        self.innerWidgetMOVES.setLayout(self.windowLayout)


        # Created UI element - Title MOVES
        self.labelTitleMOVES = QLabel()
        self.labelTitleMOVES.setText("MOVES Configuration Options")
        self.labelTitleMOVES.setObjectName("title")
        self.labelTitleMOVES.setFixedHeight(39)
        self.labelTitleMOVES.setAlignment(QtCore.Qt.AlignCenter)
        self.windowLayout.addWidget(self.labelTitleMOVES, 0, 0, 1, 5)

        # Created UI element - Title Line
        self.labelTitleMOVESLine = QLabel()
        pixmapLine = QPixmap('line.png')
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
        self.lineEditDatafiles.setText("C:\MOVESdatb")
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
        self.windowLayout.addWidget(self.dbConnectionParaLabel, 7, 0, 1, 4)

        # Created UI element - Database Connection Parameters below Line
        self.dbConnectionParaLine = QLabel()
        pixmapLine1M = QPixmap('line.png')
        pixmap1M = pixmapLine1M.scaledToHeight(14)
        self.dbConnectionParaLine.setPixmap(pixmap1M)
        self.resize(pixmap1M.width(), pixmap1M.height())
        self.windowLayout.addWidget(self.dbConnectionParaLine, 8, 0, 1, 5)

        # Expand/Collapse code
        # Created UI element Database Connection Parameters MOVES
        self.labeldbConnectionsMOVESExpand = QPushButton()
        self.labeldbConnectionsMOVESExpand.setFixedHeight(30)
        self.labeldbConnectionsMOVESExpand.setFixedWidth(30)
        self.labeldbConnectionsMOVESExpand.setObjectName("expandCollapseIcon")
        #self.labeldbConnectionsMOVESExpand.setText(u'\u25B2')
        self.labeldbConnectionsMOVESExpand.setIconSize(QtCore.QSize(40, 40))
        self.labeldbConnectionsMOVESExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
        self.windowLayout.addWidget(self.labeldbConnectionsMOVESExpand, 7, 4)

        self.dbConnectionsMOVESexpandWidget = QtWidgets.QWidget()
        self.dbConnectionsMOVESexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 1px;border-radius: 5px;")
        self.dbConnectionsMOVESGridLayout = QtWidgets.QGridLayout()
        self.dbConnectionsMOVESexpandWidget.setLayout(self.dbConnectionsMOVESGridLayout)
        self.dbConnectionsMOVESexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.dbConnectionsMOVESexpandWidget, 9, 0, 1, 4)

        def labelDbConnectionsMOVESOnClickEvent():
            if self.dbConnectionsMOVESexpandWidget.isVisible():
                #self.labeldbConnectionsMOVESExpand.setText(u'\u25B2')
                self.labeldbConnectionsMOVESExpand.setIconSize(QtCore.QSize(40, 40))
                self.labeldbConnectionsMOVESExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
                self.dbConnectionsMOVESexpandWidget.setVisible(False)
            else:
                #self.labeldbConnectionsMOVESExpand.setText(u'\u25BC')
                self.labeldbConnectionsMOVESExpand.setIconSize(QtCore.QSize(40, 40))
                self.labeldbConnectionsMOVESExpand.setIcon(QtGui.QIcon('downWardArrow.png'))
                self.dbConnectionsMOVESexpandWidget.setVisible(True)

        self.labeldbConnectionsMOVESExpand.clicked.connect(labelDbConnectionsMOVESOnClickEvent)

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
        self.dbConnectionsMOVESGridLayout.addWidget(self.labelDbHost, 0, 0)
        self.dbConnectionsMOVESGridLayout.addWidget(self.lineEditDbHost, 0, 1)

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
        self.dbConnectionsMOVESGridLayout.addWidget(self.labelDbUsername, 0, 2)
        self.dbConnectionsMOVESGridLayout.addWidget(self.lineEditDbUsername, 0, 3)

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
        self.dbConnectionsMOVESGridLayout.addWidget(self.labelDbName, 1, 0)
        self.dbConnectionsMOVESGridLayout.addWidget(self.lineEditDbName, 1, 1)

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
        self.lineEditDbPwd.setEchoMode(QLineEdit.Password)
        self.lineEditDbPwd.show()
        self.lineEditDbPwd.setText("root")
        self.dbConnectionsMOVESGridLayout.addWidget(self.labelDbPwd, 1, 2)
        self.dbConnectionsMOVESGridLayout.addWidget(self.lineEditDbPwd, 1, 3)

        #Empty Label
        self.emptyLabel = QLabel()
        self.emptyLabel.setStyleSheet("border-color: white; ")
        self.dbConnectionsMOVESGridLayout.addWidget(self.emptyLabel, 1, 4)

        # Execution Timeframe Label
        self.executionTimeLabel = QLabel()
        self.executionTimeLabel.setText("Execution Timeframe")
        self.executionTimeLabel.setFixedHeight(30)
        self.executionTimeLabel.setObjectName("subTitleLabels")
        self.windowLayout.addWidget(self.executionTimeLabel, 11, 0, 1, 4)

        # Created UI element - Execution Timeframe below Line
        self.executionTimeLine = QLabel()
        pixmapLine1M = QPixmap('line.png')
        pixmap1M = pixmapLine1M.scaledToHeight(14)
        self.executionTimeLine.setPixmap(pixmap1M)
        self.resize(pixmap1M.width(), pixmap1M.height())
        self.windowLayout.addWidget(self.executionTimeLine, 12, 0, 1, 5)

        # Expand/Collapse code
        # Created UI element Execution Timeframe MOVES
        self.labelTimeframeMOVESExpand = QPushButton()
        self.labelTimeframeMOVESExpand.setFixedHeight(30)
        self.labelTimeframeMOVESExpand.setFixedWidth(30)
        self.labelTimeframeMOVESExpand.setObjectName("expandCollapseIcon")
        self.labelTimeframeMOVESExpand.setIconSize(QtCore.QSize(40, 40))
        self.labelTimeframeMOVESExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
        #self.labelTimeframeMOVESExpand.setText(u'\u25B2')
        self.windowLayout.addWidget(self.labelTimeframeMOVESExpand, 11, 4)

        self.timeframeMOVESexpandWidget = QtWidgets.QWidget()
        self.timeframeMOVESexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 1px;border-radius: 5px;")
        self.timeframeMOVESGridLayout = QtWidgets.QGridLayout()
        self.timeframeMOVESexpandWidget.setLayout(self.timeframeMOVESGridLayout)
        self.timeframeMOVESexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.timeframeMOVESexpandWidget, 13, 0, 1, 4)

        def labelTimeframeMOVESOnClickEvent():
            if self.timeframeMOVESexpandWidget.isVisible():
                #self.labelTimeframeMOVESExpand.setText(u'\u25B2')
                self.labelTimeframeMOVESExpand.setIconSize(QtCore.QSize(40, 40))
                self.labelTimeframeMOVESExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
                self.timeframeMOVESexpandWidget.setVisible(False)
            else:
                #self.labelTimeframeMOVESExpand.setText(u'\u25BC')
                self.labelTimeframeMOVESExpand.setIconSize(QtCore.QSize(40, 40))
                self.labelTimeframeMOVESExpand.setIcon(QtGui.QIcon('downWardArrow.png'))
                self.timeframeMOVESexpandWidget.setVisible(True)

        self.labelTimeframeMOVESExpand.clicked.connect(labelTimeframeMOVESOnClickEvent)

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
        self.timeframeMOVESGridLayout.addWidget(self.labelAnalysisYear, 0, 0)
        self.timeframeMOVESGridLayout.addWidget(self.comboBoxYear, 0, 1)
        self.timeframeMOVESGridLayout.addWidget(self.labelYearErrorMsg, 0, 2, 1, 4)
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
        self.timeframeMOVESGridLayout.addWidget(self.labelMonth, 1, 0)
        self.timeframeMOVESGridLayout.addWidget(self.comboBoxMonth, 1, 1)

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
        self.timeframeMOVESGridLayout.addWidget(self.labelDate, 1, 2)
        self.timeframeMOVESGridLayout.addWidget(self.comboBoxDate, 1, 3)

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
        self.timeframeMOVESGridLayout.addWidget(self.labelBegHr, 2, 0)
        self.timeframeMOVESGridLayout.addWidget(self.comboBoxBegHr, 2, 1)

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
        self.timeframeMOVESGridLayout.addWidget(self.labelEndHr, 2, 2)
        self.timeframeMOVESGridLayout.addWidget(self.comboBoxEndHr, 2, 3)

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
        self.timeframeMOVESGridLayout.addWidget(self.labelDayType, 3, 0)
        self.timeframeMOVESGridLayout.addWidget(self.comboBoxDayType, 3, 1)


        # Custom Data Filepaths Label MOVES
        self.customDataFilepathsLabelM = QLabel()
        self.customDataFilepathsLabelM.setText("Custom Data Filepaths")
        self.customDataFilepathsLabelM.setFixedHeight(30)
        self.customDataFilepathsLabelM.setObjectName("subTitleLabels")
        self.windowLayout.addWidget(self.customDataFilepathsLabelM, 17, 0, 1, 4)

        # Created UI element - Custom Dtatfiles below Line MOVES
        self.labelCustomDatafilsLineM = QLabel()
        pixmapLine2 = QPixmap('line.png')
        pixmap2 = pixmapLine2.scaledToHeight(14)
        self.labelCustomDatafilsLineM.setPixmap(pixmap2)
        self.resize(pixmap2.width(), pixmap2.height())
        self.windowLayout.addWidget(self.labelCustomDatafilsLineM, 18, 0, 1, 5)

        # Expand/Collapse code
        # Created UI element Custom Data Filepaths MOVES
        self.labelCustomDatafileMOVESExpand = QPushButton()
        self.labelCustomDatafileMOVESExpand.setFixedHeight(30)
        self.labelCustomDatafileMOVESExpand.setFixedWidth(30)
        self.labelCustomDatafileMOVESExpand.setObjectName("expandCollapseIcon")
        #self.labelCustomDatafileMOVESExpand.setText(u'\u25B2')
        self.labelCustomDatafileMOVESExpand.setIconSize(QtCore.QSize(40, 40))
        self.labelCustomDatafileMOVESExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
        self.windowLayout.addWidget(self.labelCustomDatafileMOVESExpand, 17, 4)

        self.customDatafileMOVESexpandWidget = QtWidgets.QWidget()
        self.customDatafileMOVESexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 1px;border-radius: 5px;")
        self.customDatafileMOVESGridLayout = QtWidgets.QGridLayout()
        self.customDatafileMOVESexpandWidget.setLayout(self.customDatafileMOVESGridLayout)
        self.customDatafileMOVESexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.customDatafileMOVESexpandWidget, 19, 0, 1, 4)

        def labelCustomDatafileMOVESOnClickEvent():
            if self.customDatafileMOVESexpandWidget.isVisible():
                #self.labelCustomDatafileMOVESExpand.setText(u'\u25B2')
                self.labelCustomDatafileMOVESExpand.setIconSize(QtCore.QSize(40, 40))
                self.labelCustomDatafileMOVESExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
                self.customDatafileMOVESexpandWidget.setVisible(False)
            else:
                #self.labelCustomDatafileMOVESExpand.setText(u'\u25BC')
                self.labelCustomDatafileMOVESExpand.setIconSize(QtCore.QSize(40, 40))
                self.labelCustomDatafileMOVESExpand.setIcon(QtGui.QIcon('downWardArrow.png'))
                self.customDatafileMOVESexpandWidget.setVisible(True)

        self.labelCustomDatafileMOVESExpand.clicked.connect(labelCustomDatafileMOVESOnClickEvent)

        # Created UI element Truck Capacity
        self.labelTruckCapacity = QLabel()
        self.labelTruckCapacity.setText("Truck Capacity")
        self.labelTruckCapacity.setObjectName("allLabels")
        self.labelTruckCapacity.setAlignment(QtCore.Qt.AlignCenter)
        self.labelTruckCapacity.setFixedHeight(30)
        self.labelTruckCapacity.setFixedWidth(175)
        self.labelTruckCapacity.setToolTip(
            "Select Truck Capacity (truck capacities for feedstock transportation) dataset")
        self.browseBtnTruckCapa = QPushButton("Browse", self)
        self.browseBtnTruckCapa.setFixedWidth(116)
        self.browseBtnTruckCapa.setFixedHeight(30)
        self.browseBtnTruckCapa.clicked.connect(self.getfilesTruckCapa)
        self.lineEditTruckCapa = QLineEdit(self)
        self.lineEditTruckCapa.setText("data/inputs/truck_capacity.csv")
        self.lineEditTruckCapa.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditTruckCapa.setFixedHeight(30)
        self.customDatafileMOVESGridLayout.addWidget(self.labelTruckCapacity, 0, 0)
        self.customDatafileMOVESGridLayout.addWidget(self.browseBtnTruckCapa, 0, 1)
        self.customDatafileMOVESGridLayout.addWidget(self.lineEditTruckCapa, 0, 2, 1, 3)

        # Created UI element AVFT
        self.labelAVFT = QLabel()
        self.labelAVFT.setText("AVFT")
        self.labelAVFT.setObjectName("allLabels")
        self.labelAVFT.setAlignment(QtCore.Qt.AlignCenter)
        self.labelAVFT.setFixedHeight(30)
        self.labelAVFT.setFixedWidth(175)
        self.labelAVFT.setToolTip("Select AVFT (fuel fraction by engine type) dataset")
        self.browseBtnAVFT = QPushButton("Browse", self)
        self.browseBtnAVFT.setFixedWidth(116)
        self.browseBtnAVFT.setFixedHeight(30)
        self.browseBtnAVFT.clicked.connect(self.getfilesAVFT)
        self.lineEditAVFT = QLineEdit(self)
        self.lineEditAVFT.setText("data/inputs/avft.csv")
        self.lineEditAVFT.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditAVFT.setFixedHeight(30)
        self.customDatafileMOVESGridLayout.addWidget(self.labelAVFT, 1, 0)
        self.customDatafileMOVESGridLayout.addWidget(self.browseBtnAVFT, 1, 1)
        self.customDatafileMOVESGridLayout.addWidget(self.lineEditAVFT, 1, 2, 1, 3)

        # Created UI element MOVES Region to FIPS Map
        self.labelFips = QLabel()
        self.labelFips.setText("MOVES Region to FIPS Map")
        self.labelFips.setObjectName("allLabels")
        self.labelFips.setAlignment(QtCore.Qt.AlignCenter)
        self.labelFips.setFixedHeight(30)
        self.labelFips.setFixedWidth(175)
        self.labelFips.setToolTip("Select Region FIPS Map (production region to MOVES FIPS mapping) dataset")
        self.browseBtnFips = QPushButton("Browse", self)
        self.browseBtnFips.setFixedWidth(116)
        self.browseBtnFips.setFixedHeight(30)
        self.browseBtnFips.clicked.connect(self.getfilesFips)
        self.lineEditFips = QLineEdit(self)
        self.lineEditFips.setText("data/inputs/region_fips_map.csv")
        self.lineEditFips.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditFips.setFixedHeight(30)
        self.customDatafileMOVESGridLayout.addWidget(self.labelFips, 2, 0)
        self.customDatafileMOVESGridLayout.addWidget(self.browseBtnFips, 2, 1)
        self.customDatafileMOVESGridLayout.addWidget(self.lineEditFips, 2, 2, 1, 3)

        # Advanced Options Label MOVES
        self.advOptionsLabelM = QLabel()
        self.advOptionsLabelM.setText("Advanced Options")
        self.advOptionsLabelM.setFixedHeight(30)
        self.advOptionsLabelM.setObjectName("subTitleLabels")
        self.windowLayout.addWidget(self.advOptionsLabelM, 22, 0, 1, 4)

        # Created UI element - Advanced Optiones below Line
        self.labelAdvOptionsLineM = QLabel()
        pixmapLine2 = QPixmap('line.png')
        pixmap2 = pixmapLine2.scaledToHeight(14)
        self.labelAdvOptionsLineM.setPixmap(pixmap2)
        self.resize(pixmap2.width(), pixmap2.height())
        self.windowLayout.addWidget(self.labelAdvOptionsLineM, 23, 0, 1, 5)

        # Expand/Collapse code
        # Created UI element Advanced Options MOVES
        self.labelAdvOptionsMOVESExpand = QPushButton()
        self.labelAdvOptionsMOVESExpand.setFixedHeight(30)
        self.labelAdvOptionsMOVESExpand.setFixedWidth(30)
        self.labelAdvOptionsMOVESExpand.setObjectName("expandCollapseIcon")
        #self.labelAdvOptionsMOVESExpand.setText(u'\u25B2')
        self.labelAdvOptionsMOVESExpand.setIconSize(QtCore.QSize(40, 40))
        self.labelAdvOptionsMOVESExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
        self.windowLayout.addWidget(self.labelAdvOptionsMOVESExpand, 22, 4)

        self.advOptionsMOVESexpandWidget = QtWidgets.QWidget()
        self.advOptionsMOVESexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 1px;border-radius: 5px;")
        self.advOptionsMOVESGridLayout = QtWidgets.QGridLayout()
        self.advOptionsMOVESexpandWidget.setLayout(self.advOptionsMOVESGridLayout)
        self.advOptionsMOVESexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.advOptionsMOVESexpandWidget, 26, 0, 1, 4)

        def labelAdvOptionsMOVESOnClickEvent():
            if self.advOptionsMOVESexpandWidget.isVisible():
                #self.labelAdvOptionsMOVESExpand.setText(u'\u25B2')
                self.labelAdvOptionsMOVESExpand.setIconSize(QtCore.QSize(40, 40))
                self.labelAdvOptionsMOVESExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
                self.advOptionsMOVESexpandWidget.setVisible(False)
            else:
                #self.labelAdvOptionsMOVESExpand.setText(u'\u25BC')
                self.labelAdvOptionsMOVESExpand.setIconSize(QtCore.QSize(40, 40))
                self.labelAdvOptionsMOVESExpand.setIcon(QtGui.QIcon('downWardArrow.png'))
                self.advOptionsMOVESexpandWidget.setVisible(True)

        self.labelAdvOptionsMOVESExpand.clicked.connect(labelAdvOptionsMOVESOnClickEvent)

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
        self.leditNofTrucksUsed = self.spinBoxNoofTruck.lineEdit()
        self.leditNofTrucksUsed.setAlignment(QtCore.Qt.AlignCenter)
        self.leditNofTrucksUsed = self.spinBoxNoofTruck.lineEdit()
        self.leditNofTrucksUsed.setReadOnly(True)
        self.advOptionsMOVESGridLayout.addWidget(self.labelNoofTruck, 0, 0)
        self.advOptionsMOVESGridLayout.addWidget(self.spinBoxNoofTruck, 0, 1)

        # Created UI element VMT - Empty Label
        self.labelEmpty = QLabel()
        self.labelEmpty.setStyleSheet("border-color: white; ")
        self.advOptionsMOVESGridLayout.addWidget(self.labelEmpty, 0, 2)

        # Created UI element VMT - Empty Label
        self.labelEmpty1 = QLabel()
        self.labelEmpty1.setStyleSheet("border-color: white; ")
        self.advOptionsMOVESGridLayout.addWidget(self.labelEmpty1, 0, 3)

        # Created UI element VMT - Empty Label
        self.labelEmpty2 = QLabel()
        self.labelEmpty2.setStyleSheet("border-color: white; ")
        self.advOptionsMOVESGridLayout.addWidget(self.labelEmpty2, 0, 4)


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
        self.advOptionsMOVESGridLayout.addWidget(self.labelVMTperTruck, 1, 0)
        self.advOptionsMOVESGridLayout.addWidget(self.lineEditVMTperTruck, 1, 1)

        # Created UI element VMT Fractions
        self.labelVMTFraction = QLabel()
        self.labelVMTFraction.setText("VMT Fractions")
        self.labelVMTFraction.setToolTip("Fraction of VMT(Vehicle MilesTraveled) by road type (All must sum to 1)")
        self.labelVMTFraction.setFixedHeight(30)
        self.labelVMTFraction.setObjectName("subTitleLabels")
        self.windowLayout.addWidget(self.labelVMTFraction, 27, 0, 1, 4)

        # Created UI element - VMT Fractions below Line MOVES
        self.vMTFractionLine = QLabel()
        pixmapLine3 = QPixmap('line.png')
        pixmap3 = pixmapLine3.scaledToHeight(14)
        self.vMTFractionLine.setPixmap(pixmap2)
        self.resize(pixmap3.width(), pixmap3.height())
        self.windowLayout.addWidget(self.vMTFractionLine, 28, 0, 1, 5)



        #Expand/Collapse code

        # Created UI element VMT Fractions
        self.labelVMTFractionExpand = QPushButton()
        self.labelVMTFractionExpand.setFixedHeight(30)
        self.labelVMTFractionExpand.setFixedWidth(30)
        self.labelVMTFractionExpand.setObjectName("expandCollapseIcon")
        #self.labelVMTFractionExpand.setText(u'\u25B2')
        self.labelVMTFractionExpand.setIconSize(QtCore.QSize(40, 40))
        self.labelVMTFractionExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
        self.windowLayout.addWidget(self.labelVMTFractionExpand, 27, 4)

        self.vmtexpandWidget = QtWidgets.QWidget()
        self.vmtexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 1px;border-radius: 5px;")
        self.vmtGridLayout = QtWidgets.QGridLayout()
        self.vmtexpandWidget.setLayout(self.vmtGridLayout)
        self.vmtexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.vmtexpandWidget, 31,0, 1, 4)

        def labelVMTFractionOnClickEvent():
            if self.vmtexpandWidget.isVisible():
                #self.labelVMTFractionExpand.setText(u'\u25B2')
                self.labelVMTFractionExpand.setIconSize(QtCore.QSize(40, 40))
                self.labelVMTFractionExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
                self.vmtexpandWidget.setVisible(False)
            else:
               # self.labelVMTFractionExpand.setText(u'\u25BC')
                self.labelVMTFractionExpand.setIconSize(QtCore.QSize(40, 40))
                self.labelVMTFractionExpand.setIcon(QtGui.QIcon('downWardArrow.png'))
                self.vmtexpandWidget.setVisible(True)

        self.labelVMTFractionExpand.clicked.connect(labelVMTFractionOnClickEvent)

        # Created UI element VMT - Rural Restricted
        self.labelRuralRes = QLabel()
        self.labelRuralRes.setText("Rural Restricted")
        self.labelRuralRes.setObjectName("allLabels")
        self.labelRuralRes.setAlignment(QtCore.Qt.AlignCenter)
        self.labelRuralRes.setFixedHeight(30)
        self.labelRuralRes.setFixedWidth(165)
        self.lineEditRuralRes = QLineEdit(self)
        self.lineEditRuralRes.setFixedWidth(116)
        self.lineEditRuralRes.setFixedHeight(30)
        self.lineEditRuralRes.setAlignment(QtCore.Qt.AlignCenter)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditRuralRes.setValidator(self.onlyFlaot)
        self.lineEditRuralRes.setText("0.3")
        self.vmtGridLayout.addWidget(self.labelRuralRes, 0, 0)
        self.vmtGridLayout.addWidget(self.lineEditRuralRes, 0, 1)

        # Created UI element VMT - Urban Restricted
        self.labelUrbanRes = QLabel()
        self.labelUrbanRes.setText("Urban Restricted")
        self.labelUrbanRes.setObjectName("allLabels")
        self.labelUrbanRes.setAlignment(QtCore.Qt.AlignCenter)
        self.labelUrbanRes.setFixedHeight(30)
        self.labelUrbanRes.setFixedWidth(165)
        self.lineEditUrbanRes = QLineEdit(self)
        self.lineEditUrbanRes.setFixedWidth(116)
        self.lineEditUrbanRes.setFixedHeight(30)
        self.lineEditUrbanRes.setAlignment(QtCore.Qt.AlignCenter)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditUrbanRes.setValidator(self.onlyFlaot)
        self.lineEditUrbanRes.setText("0.21")
        self.vmtGridLayout.addWidget(self.labelUrbanRes, 0, 2)
        self.vmtGridLayout.addWidget(self.lineEditUrbanRes, 0, 3)

        # Created UI element VMT - Rural Unrestricted
        self.labelRuralUnres = QLabel()
        self.labelRuralUnres.setText("Rural Unrestricted")
        self.labelRuralUnres.setObjectName("allLabels")
        self.labelRuralUnres.setAlignment(QtCore.Qt.AlignCenter)
        self.labelRuralUnres.setFixedHeight(30)
        self.labelRuralUnres.setFixedWidth(165)
        self.lineEditRuralUnres = QLineEdit(self)
        self.lineEditRuralUnres.setFixedWidth(116)
        self.lineEditRuralUnres.setFixedHeight(30)
        self.lineEditRuralUnres.setAlignment(QtCore.Qt.AlignCenter)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditRuralUnres.setValidator(self.onlyFlaot)
        self.lineEditRuralUnres.setText("0.28")
        self.vmtGridLayout.addWidget(self.labelRuralUnres, 1, 0)
        self.vmtGridLayout.addWidget(self.lineEditRuralUnres, 1, 1)

        # Created UI element VMT - Urban Unrestricted
        self.labelUrbanUnres = QLabel()
        self.labelUrbanUnres.setText("Urban Unrestricted")
        self.labelUrbanUnres.setObjectName("allLabels")
        self.labelUrbanUnres.setAlignment(QtCore.Qt.AlignCenter)
        self.labelUrbanUnres.setFixedHeight(30)
        self.labelUrbanUnres.setFixedWidth(165)
        self.lineEditUrbanUnres = QLineEdit()
        self.lineEditUrbanUnres.setFixedWidth(116)
        self.lineEditUrbanUnres.setFixedHeight(30)
        self.lineEditUrbanUnres.setFixedHeight(30)
        self.lineEditUrbanUnres.setAlignment(QtCore.Qt.AlignCenter)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditUrbanUnres.setValidator(self.onlyFlaot)
        self.lineEditUrbanUnres.setText("0.28")
        self.vmtGridLayout.addWidget(self.labelUrbanUnres, 1, 2)
        self.vmtGridLayout.addWidget(self.lineEditUrbanUnres, 1, 3)

        # Created UI element VMT - Empty Label
        self.labelEmpty = QLabel()
        self.labelEmpty.setStyleSheet("border-color: white; ")
        self.vmtGridLayout.addWidget(self.labelEmpty, 1, 4)



    # CHeck for consistent input for year
    def handleItemPressedMoves(self, index):
        if str(self.comboBoxYearNon.currentText()) != str(self.comboBoxYear.currentText()):
            self.comboBoxYear.setStyleSheet(
                """QComboBox { background-color: red; color: white }""")

    # Functions used for Moves Path

    def getfilesMovesPath(self):
        fileNameMovesPath = QFileDialog.getExistingDirectory(self, "Browse")
        if fileNameMovesPath != "":
            selectedFileNameMovesPath = str(fileNameMovesPath).split(',')
            self.lineEditMovesPath.setText(selectedFileNameMovesPath[0])



    # Functions used for Truck Capacity

    def getfilesTruckCapa(self):
        fileNameTruckCapa = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        if fileNameTruckCapa[0] != "":
            selectedFileNameTruckCapa = fileNameTruckCapa[0].split("FPEAM/")
            self.lineEditTruckCapa.setText(selectedFileNameTruckCapa[1])

    # Functions used for AVFT

    def getfilesAVFT(self):
        fileNameAVFT = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        if fileNameAVFT[0] != "":
            selectedFileNameAVFT = fileNameAVFT[0].split("FPEAM/")
            self.lineEditAVFT.setText(selectedFileNameAVFT[1])


    # Functions used for Fips

    def getfilesFips(self):
        fileNameFips = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        if fileNameFips[0] != "":
            selectedFileNameFips = fileNameFips[0].split("FPEAM/")
            self.lineEditFips.setText(selectedFileNameFips[1])

    # Functions used for Moves Datafiles

    def getfilesDatafiles(self):
        fileNameDatafile = QFileDialog.getExistingDirectory(self, "Browse")
        if fileNameDatafile != "":
            selectedFileNameDatafile = str(fileNameDatafile).split(',')
            self.lineEditDatafiles.setText(selectedFileNameDatafile[0])


    def getEnteredText(self):
        self.enteredText.setText(self.lineEditVMTperTruck)

        #########################################################################################################################


        #### Nonroad Module   #####

    def setupUINonroad(self):
        # Nonroad tab created
        self.tabNonroad = QtWidgets.QWidget()
        self.tabNonroad.resize(WIDTH, HEIGHT - 200)
        # Nonroad tab added
        self.centralwidget.addTab(self.tabNonroad, "NONROAD")

        # Nonroad code start
        self.windowLayout = QGridLayout()
        self.windowLayout.setSpacing(15)
        self.windowLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.windowLayout.setColumnStretch(6, 1)

        self.scrollAreaNONROAD = QScrollArea(self.tabNonroad)
        self.scrollAreaNONROAD.setWidgetResizable(True)
        self.scrollAreaNONROAD.resize(WIDTH, HEIGHT)
        self.scrollAreaNONROAD.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollAreaNONROAD.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self.innerWidgetNONROAD = QtWidgets.QWidget()
        self.innerWidgetNONROAD.resize(WIDTH, HEIGHT)
        self.scrollAreaNONROAD.setWidget(self.innerWidgetNONROAD)
        self.innerWidgetNONROAD.setLayout(self.windowLayout)

        # Created UI element - Title NONROAD
        self.labelTitleNONROAD = QLabel()
        self.labelTitleNONROAD.setText("NONROAD Configuration Options")
        self.labelTitleNONROAD.setObjectName("title")
        self.labelTitleNONROAD.setFixedHeight(39)
        self.labelTitleNONROAD.setAlignment(QtCore.Qt.AlignCenter)
        self.windowLayout.addWidget(self.labelTitleNONROAD, 0, 0, 1, 5)

        # Created UI element - Title Line NONROAD
        self.labelTitleNONROADLine = QLabel()
        pixmapLine = QPixmap('line.png')
        pixmap = pixmapLine.scaledToHeight(14)
        self.labelTitleNONROADLine.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.windowLayout.addWidget(self.labelTitleNONROADLine, 1, 0, 1, 5)

        # Created UI element Nonroad Datafiles
        self.labelDatafilesNon = QLabel()
        self.labelDatafilesNon.setObjectName("allLabels")
        self.labelDatafilesNon.setFixedHeight(30)
        self.labelDatafilesNon.setFixedWidth(175)
        self.labelDatafilesNon.setAlignment(QtCore.Qt.AlignCenter)
        self.labelDatafilesNon.setText("NONROAD Executabel Path")
        self.labelDatafilesNon.setToolTip("Select NONROAD output folder")
        self.browseBtnDatafilesNon = QPushButton("Browse", self)
        self.browseBtnDatafilesNon.setFixedWidth(116)
        self.browseBtnDatafilesNon.setFixedHeight(30)
        self.browseBtnDatafilesNon.clicked.connect(self.getfilesDatafilesNon)
        self.lineEditDatafilesNon = QLineEdit(self)
        self.lineEditDatafilesNon.setText("C:/Nonroad")
        self.lineEditDatafilesNon.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditDatafilesNon.setFixedHeight(30)
        self.windowLayout.addWidget(self.labelDatafilesNon, 2, 0)
        self.windowLayout.addWidget(self.browseBtnDatafilesNon, 2, 1)
        self.windowLayout.addWidget(self.lineEditDatafilesNon, 2, 2, 1, 4)

        # Created UI element Year - Nonroad
        self.labelYearNon = QLabel()
        self.labelYearNon.setObjectName("allLabels")
        self.labelYearNon.setFixedHeight(30)
        self.labelYearNon.setFixedWidth(175)
        self.labelYearNon.setAlignment(QtCore.Qt.AlignCenter)
        self.labelYearNon.setText("Analysis Year")
        self.labelYearNon.setToolTip("Start year of equipment")
        self.comboBoxYearNon = QComboBox(self)
        self.comboBoxYearNon.setFixedHeight(30)
        for i in range(2018, 1990, -1):
            self.number = i
            self.comboBoxYearNon.addItem(str(i))
        self.index = self.comboBoxYearNon.findText("2017")
        self.comboBoxYearNon.setCurrentIndex(self.index)
        self.comboBoxYearNon.setEditable(True)
        self.leditYear = self.comboBoxYearNon.lineEdit()
        self.leditYear.setAlignment(QtCore.Qt.AlignCenter)
        self.leditYear = self.comboBoxYearNon.lineEdit()
        self.leditYear.setReadOnly(True)
        self.labelYearNonErrorMsg = QLabel()
        self.labelYearNonErrorMsg.setObjectName("yearErrorMsg")
        self.labelYearNonErrorMsg.setFixedHeight(30)
        self.labelYearNonErrorMsg.setText("")
        self.windowLayout.addWidget(self.labelYearNon, 3, 0)
        self.windowLayout.addWidget(self.comboBoxYearNon, 3, 1)
        self.windowLayout.addWidget(self.labelYearNonErrorMsg, 3, 2)
        # Check whether Moves year matches with Nonroad year
        self.comboBoxYearNon.currentIndexChanged.connect(self.handleItemPressed)

        # Database Connection Parameters Label NONROAD
        self.dbConnectionParaLabelN = QLabel()
        self.dbConnectionParaLabelN.setText("Database Connection Parameters")
        self.dbConnectionParaLabelN.setFixedHeight(30)
        self.dbConnectionParaLabelN.setObjectName("subTitleLabels")
        self.windowLayout.addWidget(self.dbConnectionParaLabelN, 4, 0, 1, 4)

        # Created UI element - Advanced Optiones below Line NONROAD
        self.dbConnectionParaLineN = QLabel()
        pixmapLine1M = QPixmap('line.png')
        pixmap1M = pixmapLine1M.scaledToHeight(14)
        self.dbConnectionParaLineN.setPixmap(pixmap1M)
        self.resize(pixmap1M.width(), pixmap1M.height())
        self.windowLayout.addWidget(self.dbConnectionParaLineN, 5, 0, 1, 5)


        # Expand/Collapse code
        # Created UI element Database Connection Parameters NONROAD
        self.labeldbConnectionsNONROADExpand = QPushButton()
        self.labeldbConnectionsNONROADExpand.setFixedHeight(30)
        self.labeldbConnectionsNONROADExpand.setFixedWidth(30)
        self.labeldbConnectionsNONROADExpand.setObjectName("expandCollapseIcon")
        #self.labeldbConnectionsNONROADExpand.setText(u'\u25B2')
        self.labeldbConnectionsNONROADExpand.setIconSize(QtCore.QSize(40, 40))
        self.labeldbConnectionsNONROADExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
        self.windowLayout.addWidget(self.labeldbConnectionsNONROADExpand, 4, 4)

        self.dbConnectionsNONROADexpandWidget = QtWidgets.QWidget()
        self.dbConnectionsNONROADexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 1px;border-radius: 5px;")
        self.dbConnectionsNONROADGridLayout = QtWidgets.QGridLayout()
        self.dbConnectionsNONROADexpandWidget.setLayout(self.dbConnectionsNONROADGridLayout)
        self.dbConnectionsNONROADexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.dbConnectionsNONROADexpandWidget, 6, 0, 1, 4)

        def labelDbConnectionsNONROADOnClickEvent():
            if self.dbConnectionsNONROADexpandWidget.isVisible():
                #self.labeldbConnectionsNONROADExpand.setText(u'\u25B2')
                self.labeldbConnectionsNONROADExpand.setIconSize(QtCore.QSize(40, 40))
                self.labeldbConnectionsNONROADExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
                self.dbConnectionsNONROADexpandWidget.setVisible(False)
            else:
                #self.labeldbConnectionsNONROADExpand.setText(u'\u25BC')
                self.labeldbConnectionsNONROADExpand.setIconSize(QtCore.QSize(40, 40))
                self.labeldbConnectionsNONROADExpand.setIcon(QtGui.QIcon('downWardArrow.png'))
                self.dbConnectionsNONROADexpandWidget.setVisible(True)

        self.labeldbConnectionsNONROADExpand.clicked.connect(labelDbConnectionsNONROADOnClickEvent)

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
        self.dbConnectionsNONROADGridLayout.addWidget(self.labelDbHostN, 0, 0)
        self.dbConnectionsNONROADGridLayout.addWidget(self.lineEditDbHostN, 0, 1)

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
        self.dbConnectionsNONROADGridLayout.addWidget(self.labelDbUsernameN, 0, 2)
        self.dbConnectionsNONROADGridLayout.addWidget(self.lineEditDbUsernameN, 0, 3)

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
        self.dbConnectionsNONROADGridLayout.addWidget(self.labelDbNameN, 1, 0)
        self.dbConnectionsNONROADGridLayout.addWidget(self.lineEditDbNameN, 1, 1)

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
        self.lineEditDbPwdN.setEchoMode(QLineEdit.Password)
        self.lineEditDbPwdN.show()
        self.lineEditDbPwdN.setText("root")
        self.dbConnectionsNONROADGridLayout.addWidget(self.labelDbPwdN, 1, 2)
        self.dbConnectionsNONROADGridLayout.addWidget(self.lineEditDbPwdN, 1, 3)

        #Empty Label
        self.emptyLberl = QLabel()
        self.emptyLberl.setStyleSheet("border-color: white; ")
        self.dbConnectionsNONROADGridLayout.addWidget(self.emptyLberl, 1, 4)

        #Data Label
        self.dataLabel = QLabel()
        self.dataLabel.setText("Data Labels")
        self.dataLabel.setFixedHeight(30)
        self.dataLabel.setObjectName("subTitleLabels")
        self.windowLayout.addWidget(self.dataLabel, 8, 0, 1, 4)

        # Created UI element - Data Labels Line
        self.dataLabelLine = QLabel()
        pixmapLine1M = QPixmap('line.png')
        pixmap1M = pixmapLine1M.scaledToHeight(14)
        self.dataLabelLine.setPixmap(pixmap1M)
        self.resize(pixmap1M.width(), pixmap1M.height())
        self.windowLayout.addWidget(self.dataLabelLine, 9, 0, 1, 5)

        # Expand/Collapse code
        # Created UI element Database Connection Parameters NONROAD
        self.labelDataLabelsNONROADExpand = QPushButton()
        self.labelDataLabelsNONROADExpand.setFixedHeight(30)
        self.labelDataLabelsNONROADExpand.setFixedWidth(30)
        self.labelDataLabelsNONROADExpand.setObjectName("expandCollapseIcon")
        #self.labelDataLabelsNONROADExpand.setText(u'\u25B2')
        self.labelDataLabelsNONROADExpand.setIconSize(QtCore.QSize(40, 40))
        self.labelDataLabelsNONROADExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
        self.windowLayout.addWidget(self.labelDataLabelsNONROADExpand, 8, 4)

        self.dataLabelsNONROADexpandWidget = QtWidgets.QWidget()
        self.dataLabelsNONROADexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 1px;border-radius: 5px;")
        self.dtaLabelsNONROADGridLayout = QtWidgets.QGridLayout()
        self.dataLabelsNONROADexpandWidget.setLayout(self.dtaLabelsNONROADGridLayout)
        self.dataLabelsNONROADexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.dataLabelsNONROADexpandWidget, 10, 0, 1, 4)

        def labelDataLabelsNONROADOnClickEvent():
            if self.dataLabelsNONROADexpandWidget.isVisible():
                #self.labelDataLabelsNONROADExpand.setText(u'\u25B2')
                self.labelDataLabelsNONROADExpand.setIconSize(QtCore.QSize(40, 40))
                self.labelDataLabelsNONROADExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
                self.dataLabelsNONROADexpandWidget.setVisible(False)
            else:
                #self.labelDataLabelsNONROADExpand.setText(u'\u25BC')
                self.labelDataLabelsNONROADExpand.setIconSize(QtCore.QSize(40, 40))
                self.labelDataLabelsNONROADExpand.setIcon(QtGui.QIcon('downWardArrow.png'))
                self.dataLabelsNONROADexpandWidget.setVisible(True)

        self.labelDataLabelsNONROADExpand.clicked.connect(labelDataLabelsNONROADOnClickEvent)

        # Created UI element Feedstock Measure Type Nonroad
        self.labelFeedMeasureTypeNon = QLabel()
        self.labelFeedMeasureTypeNon.setObjectName("allLabels")
        self.labelFeedMeasureTypeNon.setFixedHeight(30)
        self.labelFeedMeasureTypeNon.setFixedWidth(175)
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
        self.dtaLabelsNONROADGridLayout.addWidget(self.labelFeedMeasureTypeNon, 0, 0)
        self.dtaLabelsNONROADGridLayout.addWidget(self.lineEditFeedMeasureTypeNon, 0, 1)

        # Created UI element Forestry Feedstock Names
        self.labelForestryNamesNon = QLabel()
        self.labelForestryNamesNon.setObjectName("allLabels")
        self.labelForestryNamesNon.setFixedHeight(30)
        self.labelForestryNamesNon.setFixedWidth(175)
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
        self.lineEditForestryNamesNon.setText("forest whole tree")
        self.dtaLabelsNONROADGridLayout.addWidget(self.labelForestryNamesNon, 0, 2)
        self.dtaLabelsNONROADGridLayout.addWidget(self.lineEditForestryNamesNon, 0, 3)

        # Created UI element Irrigation Feedstock Measure Type Nonroad
        self.labelFeedMeasureTypeIrrigNon = QLabel()
        self.labelFeedMeasureTypeIrrigNon.setObjectName("allLabels")
        self.labelFeedMeasureTypeIrrigNon.setFixedHeight(30)
        self.labelFeedMeasureTypeIrrigNon.setFixedWidth(175)
        self.labelFeedMeasureTypeIrrigNon.setAlignment(QtCore.Qt.AlignCenter)
        self.labelFeedMeasureTypeIrrigNon.setText("Irrigation Feedstock "+ "\n"+ "Measure Type")
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
        self.dtaLabelsNONROADGridLayout.addWidget(self.labelFeedMeasureTypeIrrigNon, 1, 0)
        self.dtaLabelsNONROADGridLayout.addWidget(self.lineEditFeedMeasureTypeIrrigNon, 1, 1)


        # Created UI element Time Resource Name
        self.labelTimeResNamesNon = QLabel()
        self.labelTimeResNamesNon.setObjectName("allLabels")
        self.labelTimeResNamesNon.setFixedHeight(30)
        self.labelTimeResNamesNon.setFixedWidth(175)
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
        self.dtaLabelsNONROADGridLayout.addWidget(self.labelTimeResNamesNon, 1, 2)
        self.dtaLabelsNONROADGridLayout.addWidget(self.lineEditTimeResNamesNon, 1, 3)

        #Empty Label
        self.emptyLabel = QLabel()
        self.emptyLabel.setStyleSheet("border-color: white; ")
        self.dtaLabelsNONROADGridLayout.addWidget(self.emptyLabel, 1, 4)

        # Created UI element Irrigation Feedstock Names
        self.labelIrrigationFeedNamesNon = QLabel()
        self.labelIrrigationFeedNamesNon.setObjectName("allLabels")
        self.labelIrrigationFeedNamesNon.setFixedHeight(30)
        self.labelIrrigationFeedNamesNon.setFixedWidth(175)
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
        self.dtaLabelsNONROADGridLayout.addWidget(self.labelIrrigationFeedNamesNon, 2, 0)
        self.dtaLabelsNONROADGridLayout.addWidget(self.lineEditFeedIrrigNamesNon, 2, 1)

        # Custom Data Filepaths Label
        self.cusromDatafileLabel = QLabel()
        self.cusromDatafileLabel.setText("Custom Data Filepaths")
        self.cusromDatafileLabel.setFixedHeight(30)
        self.cusromDatafileLabel.setObjectName("subTitleLabels")
        self.windowLayout.addWidget(self.cusromDatafileLabel, 13, 0, 1, 4)

        # Custom Data Filepaths Label Line
        self.customDatafileLabelLine = QLabel()
        pixmapLine1M = QPixmap('line.png')
        pixmap1M = pixmapLine1M.scaledToHeight(14)
        self.customDatafileLabelLine.setPixmap(pixmap1M)
        self.resize(pixmap1M.width(), pixmap1M.height())
        self.windowLayout.addWidget(self.customDatafileLabelLine, 14, 0, 1, 5)

        # Expand/Collapse code
        # Created UI element Custom Dtatfiles NONROAD
        self.labelcustomDatafileNONROADExpand = QPushButton()
        self.labelcustomDatafileNONROADExpand.setFixedHeight(30)
        self.labelcustomDatafileNONROADExpand.setFixedWidth(30)
        self.labelcustomDatafileNONROADExpand.setObjectName("expandCollapseIcon")
        #self.labelcustomDatafileNONROADExpand.setText(u'\u25B2')
        self.labelcustomDatafileNONROADExpand.setIconSize(QtCore.QSize(40, 40))
        self.labelcustomDatafileNONROADExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
        self.windowLayout.addWidget(self.labelcustomDatafileNONROADExpand, 13, 4)

        self.customDatafileNONROADexpandWidget = QtWidgets.QWidget()
        self.customDatafileNONROADexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 1px;border-radius: 5px;")
        self.customDatafileNONROADGridLayout = QtWidgets.QGridLayout()
        self.customDatafileNONROADexpandWidget.setLayout(self.customDatafileNONROADGridLayout)
        self.customDatafileNONROADexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.customDatafileNONROADexpandWidget, 15, 0, 1, 4)

        def labelCustomDatafileNONROADOnClickEvent():
            if self.customDatafileNONROADexpandWidget.isVisible():
                #self.labelcustomDatafileNONROADExpand.setText(u'\u25B2')
                self.labelcustomDatafileNONROADExpand.setIconSize(QtCore.QSize(40, 40))
                self.labelcustomDatafileNONROADExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
                self.customDatafileNONROADexpandWidget.setVisible(False)
            else:
                #self.labelcustomDatafileNONROADExpand.setText(u'\u25BC')
                self.labelcustomDatafileNONROADExpand.setIconSize(QtCore.QSize(40, 40))
                self.labelcustomDatafileNONROADExpand.setIcon(QtGui.QIcon('downWardArrow.png'))
                self.customDatafileNONROADexpandWidget.setVisible(True)

        self.labelcustomDatafileNONROADExpand.clicked.connect(labelCustomDatafileNONROADOnClickEvent)

        # Created UI element Region Nonroad Irrigation
        self.labelNonIrrig = QLabel()
        self.labelNonIrrig.setObjectName("allLabels")
        self.labelNonIrrig.setFixedHeight(30)
        self.labelNonIrrig.setFixedWidth(175)
        self.labelNonIrrig.setAlignment(QtCore.Qt.AlignCenter)
        self.labelNonIrrig.setText("Irrigation")
        self.labelNonIrrig.setToolTip("Select irrigation dataset")
        self.browseBtnNonIrrig = QPushButton("Browse", self)
        self.browseBtnNonIrrig.setFixedWidth(116)
        self.browseBtnNonIrrig.setFixedHeight(30)
        self.browseBtnNonIrrig.clicked.connect(self.getfilesNonIrrig)
        self.lineEditNonIrrig = QLineEdit(self)
        self.lineEditNonIrrig.setText("data/inputs/irrigation.csv")
        self.lineEditNonIrrig.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditNonIrrig.setFixedHeight(30)
        self.customDatafileNONROADGridLayout.addWidget(self.labelNonIrrig, 0, 0)
        self.customDatafileNONROADGridLayout.addWidget(self.browseBtnNonIrrig, 0, 1)
        self.customDatafileNONROADGridLayout.addWidget(self.lineEditNonIrrig, 0, 2, 1, 5)

        # Created UI element Region FIPs Map Nonroad
        self.labelFipsNon = QLabel()
        self.labelFipsNon.setObjectName("allLabels")
        self.labelFipsNon.setFixedHeight(30)
        self.labelFipsNon.setFixedWidth(175)
        self.labelFipsNon.setAlignment(QtCore.Qt.AlignCenter)
        self.labelFipsNon.setText("NONROAD Region "+ "\n"+ "to FIPS Map")
        self.labelFipsNon.setToolTip("Select Region FIPS Map (production region to Nonroad FIPS mapping) dataset")
        self.browseBtnFipsNon = QPushButton("Browse", self)
        self.browseBtnFipsNon.setFixedWidth(116)
        self.browseBtnFipsNon.setFixedHeight(30)
        self.browseBtnFipsNon.clicked.connect(self.getfilesFipsNon)
        self.lineEditFipsNon = QLineEdit(self)
        self.lineEditFipsNon.setText("data/inputs/region_fips_map.csv")
        self.lineEditFipsNon.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditFipsNon.setFixedHeight(30)
        self.customDatafileNONROADGridLayout.addWidget(self.labelFipsNon, 1, 0)
        self.customDatafileNONROADGridLayout.addWidget(self.browseBtnFipsNon, 1, 1)
        self.customDatafileNONROADGridLayout.addWidget(self.lineEditFipsNon, 1, 2, 1, 5)

        # Operating Temperature Label
        self.opTempLabel = QLabel()
        self.opTempLabel.setText("Operating Temperature")
        self.opTempLabel.setFixedHeight(30)
        self.opTempLabel.setObjectName("subTitleLabels")
        self.windowLayout.addWidget(self.opTempLabel, 17, 0, 1, 4)

        # Operating Temperature Label Line
        self.opTempLabelLine = QLabel()
        pixmapLine1M = QPixmap('line.png')
        pixmap1M = pixmapLine1M.scaledToHeight(14)
        self.opTempLabelLine.setPixmap(pixmap1M)
        self.resize(pixmap1M.width(), pixmap1M.height())
        self.windowLayout.addWidget(self.opTempLabelLine, 18, 0, 1, 5)

        # Expand/Collapse code
        # Created UI element Operating Temperature NONROAD
        self.labelTempNONROADExpand = QPushButton()
        self.labelTempNONROADExpand.setFixedHeight(30)
        self.labelTempNONROADExpand.setFixedWidth(30)
        self.labelTempNONROADExpand.setObjectName("expandCollapseIcon")
        #self.labelTempNONROADExpand.setText(u'\u25B2')
        self.labelTempNONROADExpand.setIconSize(QtCore.QSize(40, 40))
        self.labelTempNONROADExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
        self.windowLayout.addWidget(self.labelTempNONROADExpand, 17, 4)

        self.tempNONROADexpandWidget = QtWidgets.QWidget()
        self.tempNONROADexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 1px;border-radius: 5px;")
        self.tempNONROADGridLayout = QtWidgets.QGridLayout()
        self.tempNONROADexpandWidget.setLayout(self.tempNONROADGridLayout)
        self.tempNONROADexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.tempNONROADexpandWidget, 19, 0, 1, 4)

        def labelTempNONROADOnClickEvent():
            if self.tempNONROADexpandWidget.isVisible():
                #self.labelTempNONROADExpand.setText(u'\u25B2')
                self.labelTempNONROADExpand.setIconSize(QtCore.QSize(40, 40))
                self.labelTempNONROADExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
                self.tempNONROADexpandWidget.setVisible(False)
            else:
                #self.labelTempNONROADExpand.setText(u'\u25BC')
                self.labelTempNONROADExpand.setIconSize(QtCore.QSize(40, 40))
                self.labelTempNONROADExpand.setIcon(QtGui.QIcon('downWardArrow.png'))
                self.tempNONROADexpandWidget.setVisible(True)

        self.labelTempNONROADExpand.clicked.connect(labelTempNONROADOnClickEvent)

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
        self.tempNONROADGridLayout.addWidget(self.labelMinTemp, 0, 0)
        self.tempNONROADGridLayout.addWidget(self.lineEditMinTemp, 0, 1)

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
        self.tempNONROADGridLayout.addWidget(self.labelMeanTemp, 0, 2)
        self.tempNONROADGridLayout.addWidget(self.lineEditMeanTemp, 0, 3)

        #Empty Label
        self.emptyLabe = QLabel()
        self.emptyLabe.setStyleSheet("border-color: white; ")
        self.tempNONROADGridLayout.addWidget(self.emptyLabe, 0, 4)

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
        self.tempNONROADGridLayout.addWidget(self.labelMaxTemp, 1, 0)
        self.tempNONROADGridLayout.addWidget(self.lineEditMaxTemp, 1, 1)

        # Conversion Factors Label
        self.convFactorsLabel = QLabel()
        self.convFactorsLabel.setText("Conversion Factors")
        self.convFactorsLabel.setFixedHeight(30)
        self.convFactorsLabel.setObjectName("subTitleLabels")
        self.windowLayout.addWidget(self.convFactorsLabel, 21, 0, 1, 4)

        #  Conversion Factors Label Line
        self.convFactorsLabelLine = QLabel()
        pixmapLine1M = QPixmap('line.png')
        pixmap1M = pixmapLine1M.scaledToHeight(14)
        self.convFactorsLabelLine.setPixmap(pixmap1M)
        self.resize(pixmap1M.width(), pixmap1M.height())
        self.windowLayout.addWidget(self.convFactorsLabelLine, 22, 0, 1, 5)

        # Expand/Collapse code
        # Created UI element Conversion Factors NONROAD
        self.labelConvFactorsNONROADExpand = QPushButton()
        self.labelConvFactorsNONROADExpand.setFixedHeight(30)
        self.labelConvFactorsNONROADExpand.setFixedWidth(30)
        self.labelConvFactorsNONROADExpand.setObjectName("expandCollapseIcon")
        #self.labelConvFactorsNONROADExpand.setText(u'\u25B2')
        self.labelConvFactorsNONROADExpand.setIconSize(QtCore.QSize(40, 40))
        self.labelConvFactorsNONROADExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
        self.windowLayout.addWidget(self.labelConvFactorsNONROADExpand, 21, 4)

        self.convFactorsNONROADexpandWidget = QtWidgets.QWidget()
        self.convFactorsNONROADexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 1px;border-radius: 5px;")
        self.convFactorsNONROADGridLayout = QtWidgets.QGridLayout()
        self.convFactorsNONROADexpandWidget.setLayout(self.convFactorsNONROADGridLayout)
        self.convFactorsNONROADexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.convFactorsNONROADexpandWidget, 23, 0, 1, 4)

        def labelConvFactorsNONROADOnClickEvent():
            if self.convFactorsNONROADexpandWidget.isVisible():
                #self.labelConvFactorsNONROADExpand.setText(u'\u25B2')
                self.labelConvFactorsNONROADExpand.setIconSize(QtCore.QSize(40, 40))
                self.labelConvFactorsNONROADExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
                self.convFactorsNONROADexpandWidget.setVisible(False)
            else:
                #self.labelConvFactorsNONROADExpand.setText(u'\u25BC')
                self.labelConvFactorsNONROADExpand.setIconSize(QtCore.QSize(40, 40))
                self.labelConvFactorsNONROADExpand.setIcon(QtGui.QIcon('downWardArrow.png'))
                self.convFactorsNONROADexpandWidget.setVisible(True)

        self.labelConvFactorsNONROADExpand.clicked.connect(labelConvFactorsNONROADOnClickEvent)

        # Created UI element Low Heating Value
        self.labelLowHeat = QLabel()
        self.labelLowHeat.setObjectName("allLabels")
        self.labelLowHeat.setFixedHeight(30)
        self.labelLowHeat.setFixedWidth(170)
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
        self.convFactorsNONROADGridLayout.addWidget(self.labelLowHeat, 0, 0)
        self.convFactorsNONROADGridLayout.addWidget(self.lineEditLowHeat, 0, 1)

        # Created UI element Hydrocarbon to VOC Conversion Factor
        self.labelHydeo = QLabel()
        self.labelHydeo.setObjectName("allLabels")
        self.labelHydeo.setFixedHeight(30)
        self.labelHydeo.setFixedWidth(170)
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
        self.convFactorsNONROADGridLayout.addWidget(self.labelHydeo, 0, 2)
        self.convFactorsNONROADGridLayout.addWidget(self.lineEditHydro, 0, 3)

        # Created UI element NH3 Emission Factor
        self.labelNH3 = QLabel()
        self.labelNH3.setObjectName("allLabels")
        self.labelNH3.setFixedHeight(30)
        self.labelNH3.setFixedWidth(170)
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
        self.convFactorsNONROADGridLayout.addWidget(self.labelNH3, 1, 0)
        self.convFactorsNONROADGridLayout.addWidget(self.lineEditNH3, 1, 1)

        # Created UI element PM10 to PM2.5 Conversion Factor
        self.labelPM10 = QLabel()
        self.labelPM10.setObjectName("allLabels")
        self.labelPM10.setFixedHeight(30)
        self.labelPM10.setFixedWidth(170)
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
        self.convFactorsNONROADGridLayout.addWidget(self.labelPM10, 1, 2)
        self.convFactorsNONROADGridLayout.addWidget(self.lineEditPM10, 1, 3)

        #Empty Label
        self.emptyLabel = QLabel()
        self.emptyLabel.setStyleSheet("border-color: white; ")
        self.convFactorsNONROADGridLayout.addWidget(self.emptyLabel, 1, 4)

        # Advanced Options Label
        self.advOptionsLabelN = QLabel()
        self.advOptionsLabelN.setText("Advanced Options")
        self.advOptionsLabelN.setFixedHeight(30)
        self.advOptionsLabelN.setObjectName("subTitleLabels")
        self.windowLayout.addWidget(self.advOptionsLabelN, 25, 0, 1, 4)

        #  Advanced Options Label Line
        self.labelAdvOptionsLineN = QLabel()
        pixmapLine1M = QPixmap('line.png')
        pixmap1M = pixmapLine1M.scaledToHeight(14)
        self.labelAdvOptionsLineN.setPixmap(pixmap1M)
        self.resize(pixmap1M.width(), pixmap1M.height())
        self.windowLayout.addWidget(self.labelAdvOptionsLineN, 26, 0, 1, 5)

        # Expand/Collapse code
        # Created UI element Advanced Options NONROAD
        self.labelAdvOptionsNONROADExpand = QPushButton()
        self.labelAdvOptionsNONROADExpand.setStyleSheet("QPushButton { text-align : right}")
        self.labelAdvOptionsNONROADExpand.setFixedHeight(30)
        self.labelAdvOptionsNONROADExpand.setFixedWidth(30)
        self.labelAdvOptionsNONROADExpand.setObjectName("expandCollapseIcon")
        #self.labelAdvOptionsNONROADExpand.setText(u'\u25B2')
        self.labelAdvOptionsNONROADExpand.setIconSize(QtCore.QSize(36, 40))
        self.labelAdvOptionsNONROADExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
        self.windowLayout.addWidget(self.labelAdvOptionsNONROADExpand, 25, 4)

        self.advOptionsNONROADexpandWidget = QtWidgets.QWidget()
        self.advOptionsNONROADexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 1px;border-radius: 5px;")
        self.advOptionsNONROADGridLayout = QtWidgets.QGridLayout()
        self.advOptionsNONROADexpandWidget.setLayout(self.advOptionsNONROADGridLayout)
        self.advOptionsNONROADexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.advOptionsNONROADexpandWidget, 27, 0, 1, 4)

        def labelAdvOptionsNONROADOnClickEvent():
            if self.advOptionsNONROADexpandWidget.isVisible():
                #self.labelAdvOptionsNONROADExpand.setText(u'\u25B2')
                self.labelAdvOptionsNONROADExpand.setIconSize(QtCore.QSize(36, 40))
                self.labelAdvOptionsNONROADExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
                self.advOptionsNONROADexpandWidget.setVisible(False)
            else:
                #self.labelAdvOptionsNONROADExpand.setText(u'\u25BC')
                self.labelAdvOptionsNONROADExpand.setIconSize(QtCore.QSize(36, 40))
                self.labelAdvOptionsNONROADExpand.setIcon(QtGui.QIcon('downWardArrow.png'))
                self.advOptionsNONROADexpandWidget.setVisible(True)

        self.labelAdvOptionsNONROADExpand.clicked.connect(labelAdvOptionsNONROADOnClickEvent)

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
        self.comboBoxEncodeNames.setEditable(True)
        self.leditEncodeName = self.comboBoxEncodeNames.lineEdit()
        self.leditEncodeName.setAlignment(QtCore.Qt.AlignCenter)
        self.leditEncodeName = self.comboBoxEncodeNames.lineEdit()
        self.leditEncodeName.setReadOnly(True)
        self.advOptionsNONROADGridLayout.addWidget(self.labelNonEncodeNames, 0, 0)
        self.advOptionsNONROADGridLayout.addWidget(self.comboBoxEncodeNames, 0, 1)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.emptyPlainText.setStyleSheet(
            "border-color: white; ")
        self.advOptionsNONROADGridLayout.addWidget(self.emptyPlainText, 0, 2)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.emptyPlainText1.setStyleSheet(
            "border-color: white; ")
        self.advOptionsNONROADGridLayout.addWidget(self.emptyPlainText1, 0, 3)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.emptyPlainText3.setStyleSheet(
            "border-color: white; ")
        self.advOptionsNONROADGridLayout.addWidget(self.emptyPlainText3, 0, 4)


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
            self.labelYearErrorMsg.setText(message)
            self.labelYearNonErrorMsg.setText(message)


    # Functions used for Moves Datafiles

    def getfilesDatafilesNon(self):
        fileName = QFileDialog.getExistingDirectory(self, "Browse")
        if fileName != "":
            selectedFileName = str(fileName).split(',')
            self.lineEditDatafilesNon.setText(selectedFileName[0])

    # Functions used for Fips Nonroad

    def getfilesFipsNon(self):
        fileNameFipsNon = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        if fileNameFipsNon[0] != "":
            selectedFileNameFipsNon = fileNameFipsNon[0].split("FPEAM/")
            self.lineEditFipsNon.setText(selectedFileNameFipsNon[1])

    # Functions used for Nonroad Irrigation

    def getfilesNonIrrig(self):
        fileNameNonEq = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        if fileNameNonEq[0] != "":
            selectedFileNameNonEq = fileNameNonEq[0].split("FPEAM/")
            self.lineEditNonIrrig.setText(selectedFileNameNonEq[1])

    ###########################################################################################################################################################

    #####    EmissionFactors Module   ######


    def setupUIEmissionFactors(self):
        # Emission Factors tab created
        self.tabEmissionFactors = QtWidgets.QWidget()
        self.tabEmissionFactors.resize(WIDTH, HEIGHT - 200)
        # Emission Factors tab added
        self.centralwidget.addTab(self.tabEmissionFactors, "EMISSION FACTORS")

        # Emission Factors code start
        self.windowLayout = QGridLayout()
        self.windowLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.windowLayout.setColumnStretch(6, 1)

        self.scrollAreaEF = QScrollArea(self.tabEmissionFactors)
        self.scrollAreaEF.setWidgetResizable(True)
        self.scrollAreaEF.resize(WIDTH, HEIGHT)
        self.scrollAreaEF.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollAreaEF.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self.innerWidgetEF = QtWidgets.QWidget()
        self.innerWidgetEF.resize(WIDTH, HEIGHT)
        self.scrollAreaEF.setWidget(self.innerWidgetEF)
        self.innerWidgetEF.setLayout(self.windowLayout)

        # Created UI element - Title EF
        self.labelTitleEF = QLabel()
        self.labelTitleEF.setText("Emission Factors Configuration Options")
        self.labelTitleEF.setObjectName("title")
        self.labelTitleEF.setFixedHeight(39)
        self.labelTitleEF.setAlignment(QtCore.Qt.AlignCenter)
        self.windowLayout.addWidget(self.labelTitleEF, 0, 0, 1, 5)

        # Created UI element - Title Line EF
        self.labelTitleEFLine = QLabel()
        print(os.getcwd())
        pixmapLine = QPixmap('line.png')
        pixmap = pixmapLine.scaledToHeight(14)
        self.labelTitleEFLine.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.windowLayout.addWidget(self.labelTitleEFLine, 1, 0, 1, 5)

        # Created UI element Feedstock Measure Type Emission Factors
        self.labelFeedMeasureTypeEF = QLabel()
        self.labelFeedMeasureTypeEF.setObjectName("allLabels")
        self.labelFeedMeasureTypeEF.setFixedHeight(30)
        self.labelFeedMeasureTypeEF.setFixedWidth(170)
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
        self.windowLayout.addWidget(self.customDataFilepathLabelEF, 3, 0, 1, 4)

        # Created UI element - Custom Dtatfiles below Line
        self.labelCustomDatafilsLine = QLabel()
        pixmapLine1 = QPixmap('line.png')
        pixmap1 = pixmapLine1.scaledToHeight(14)
        self.labelCustomDatafilsLine.setPixmap(pixmap1)
        self.resize(pixmap1.width(), pixmap1.height())
        self.windowLayout.addWidget(self.labelCustomDatafilsLine, 4, 0, 1, 5)

        # Expand/Collapse code
        # Created UI element Custom Dtatfiles EF
        self.labelcustomDatafileEFExpand = QPushButton()
        self.labelcustomDatafileEFExpand.setFixedHeight(30)
        self.labelcustomDatafileEFExpand.setFixedWidth(30)
        self.labelcustomDatafileEFExpand.setObjectName("expandCollapseIcon")
        #self.labelcustomDatafileEFExpand.setText(u'\u25B2')
        self.labelcustomDatafileEFExpand.setIconSize(QtCore.QSize(40, 40))
        self.labelcustomDatafileEFExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
        self.windowLayout.addWidget(self.labelcustomDatafileEFExpand, 3, 4)

        self.customDatafileEFexpandWidget = QtWidgets.QWidget()
        self.customDatafileEFexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 1px;border-radius: 5px;")
        self.customDatafileEFGridLayout = QtWidgets.QGridLayout()
        self.customDatafileEFexpandWidget.setLayout(self.customDatafileEFGridLayout)
        self.customDatafileEFexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.customDatafileEFexpandWidget, 5, 0, 1, 4)

        def labelCustomDatafileEFOnClickEvent():
            if self.customDatafileEFexpandWidget.isVisible():
                #self.labelcustomDatafileEFExpand.setText(u'\u25B2')
                self.labelcustomDatafileEFExpand.setIconSize(QtCore.QSize(40, 40))
                self.labelcustomDatafileEFExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
                self.customDatafileEFexpandWidget.setVisible(False)
            else:
                #self.labelcustomDatafileEFExpand.setText(u'\u25BC')
                self.labelcustomDatafileEFExpand.setIconSize(QtCore.QSize(40, 40))
                self.labelcustomDatafileEFExpand.setIcon(QtGui.QIcon('downWardArrow.png'))
                self.customDatafileEFexpandWidget.setVisible(True)

        self.labelcustomDatafileEFExpand.clicked.connect(labelCustomDatafileEFOnClickEvent)


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
        self.lineEditEmiFact.setText("data/inputs/emission_factors.csv")
        self.lineEditEmiFact.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditEmiFact.setFixedHeight(30)
        self.customDatafileEFGridLayout.addWidget(self.labelEmiFact, 0, 0)
        self.customDatafileEFGridLayout.addWidget(self.browseBtnEmiFact, 0, 1)
        self.customDatafileEFGridLayout.addWidget(self.lineEditEmiFact, 0, 2,1, 3)

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
        self.lineEditResDist.setText("data/inputs/resource_distribution.csv")
        self.lineEditResDist.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditResDist.setFixedHeight(30)
        self.customDatafileEFGridLayout.addWidget(self.labelResDist, 1, 0)
        self.customDatafileEFGridLayout.addWidget(self.browseBtnReDist, 1, 1)
        self.customDatafileEFGridLayout.addWidget(self.lineEditResDist, 1, 2, 1, 3)

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
        if fileNameTruckCapa[0] != "":
            selectedFileNameTruckCapa = fileNameTruckCapa[0].split("FPEAM/")
            self.lineEditEmiFact.setText(selectedFileNameTruckCapa[1])

    # Functions used for Resource Distribution

    def getfilesResDist(self):
        fileNameTruckCapa = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        if fileNameTruckCapa[0] != "":
            selectedFileNameTruckCapa = fileNameTruckCapa[0].split("FPEAM/")
            self.lineEditResDist.setText(selectedFileNameTruckCapa[1])


    ###################################################################################################################################################################


    #####    Fugitive Dust  Module   ######

    def setupUIFugitiveDust(self):
        # Fugitive Dust tab created
        self.tabFugitiveDust = QtWidgets.QWidget()
        self.tabFugitiveDust.resize(WIDTH, HEIGHT - 200)
        # Fugitive Dust tab added
        self.centralwidget.addTab(self.tabFugitiveDust, "FUGITIVE DUST")

        # Fugitive Dust code start
        self.windowLayout = QGridLayout()
        self.windowLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.windowLayout.setColumnStretch(6, 1)

        self.scrollAreaFD = QScrollArea(self.tabFugitiveDust)
        self.scrollAreaFD.setWidgetResizable(True)
        self.scrollAreaFD.resize(WIDTH, HEIGHT)
        self.scrollAreaFD.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollAreaFD.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self.innerWidgetFD = QtWidgets.QWidget()
        self.innerWidgetFD.resize(WIDTH, HEIGHT)
        self.scrollAreaFD.setWidget(self.innerWidgetFD)
        self.innerWidgetFD.setLayout(self.windowLayout)

        # Created UI element - Title FD
        self.labelTitleFD = QLabel()
        self.labelTitleFD.setText("Fugitive Dust Configuration Options")
        self.labelTitleFD.setObjectName("title")
        self.labelTitleFD.setFixedHeight(39)
        self.labelTitleFD.setAlignment(QtCore.Qt.AlignCenter)
        self.windowLayout.addWidget(self.labelTitleFD, 0, 0, 1, 5)

        # Created UI element - Title Line FD
        self.labelTitleFDLine = QLabel()
        pixmapLine = QPixmap('line.png')
        pixmap = pixmapLine.scaledToHeight(14)
        self.labelTitleFDLine.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.windowLayout.addWidget(self.labelTitleFDLine, 1, 0, 1, 5)


        # Created UI element Feedstock Measure Type - Fugitive Dust
        self.labelFeedMeasureTypeFD = QLabel()
        self.labelFeedMeasureTypeFD.setObjectName("allLabels")
        self.labelFeedMeasureTypeFD.setFixedHeight(30)
        self.labelFeedMeasureTypeFD.setFixedWidth(170)
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
        self.windowLayout.addWidget(self.customDataFilepathLabelFD, 3, 0, 1, 4)

        # Created UI element - Custom Dtatfiles below Line
        self.labelCustomDatafilsLine = QLabel()
        pixmapLine1 = QPixmap('line.png')
        pixmap1 = pixmapLine1.scaledToHeight(14)
        self.labelCustomDatafilsLine.setPixmap(pixmap1)
        self.resize(pixmap1.width(), pixmap1.height())
        self.windowLayout.addWidget(self.labelCustomDatafilsLine, 4, 0, 1, 5)

        # Expand/Collapse code
        # Created UI element Custom Dtatfiles FD
        self.labelcustomDatafileFDExpand = QPushButton()
        self.labelcustomDatafileFDExpand.setFixedHeight(30)
        self.labelcustomDatafileFDExpand.setFixedWidth(30)
        self.labelcustomDatafileFDExpand.setObjectName("expandCollapseIcon")
        #self.labelcustomDatafileFDExpand.setText(u'\u25B2')
        self.labelcustomDatafileFDExpand.setIconSize(QtCore.QSize(40, 40))
        self.labelcustomDatafileFDExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
        self.windowLayout.addWidget(self.labelcustomDatafileFDExpand, 3, 4)

        self.customDatafileFDexpandWidget = QtWidgets.QWidget()
        self.customDatafileFDexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 1px;border-radius: 5px;")
        self.customDatafileFDGridLayout = QtWidgets.QGridLayout()
        self.customDatafileFDexpandWidget.setLayout(self.customDatafileFDGridLayout)
        self.customDatafileFDexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.customDatafileFDexpandWidget, 5, 0, 1, 4)

        def labelCustomDatafileFDOnClickEvent():
            if self.customDatafileFDexpandWidget.isVisible():
                #self.labelcustomDatafileFDExpand.setText(u'\u25B2')
                self.labelcustomDatafileFDExpand.setIconSize(QtCore.QSize(40, 40))
                self.labelcustomDatafileFDExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
                self.customDatafileFDexpandWidget.setVisible(False)
            else:
                #self.labelcustomDatafileFDExpand.setText(u'\u25BC')
                self.labelcustomDatafileFDExpand.setIconSize(QtCore.QSize(40, 40))
                self.labelcustomDatafileFDExpand.setIcon(QtGui.QIcon('upWardArrow.png'))
                self.customDatafileFDexpandWidget.setVisible(True)

        self.labelcustomDatafileFDExpand.clicked.connect(labelCustomDatafileFDOnClickEvent)

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
        self.lineEditEmiFactFD.setText("data/inputs/fugitive_dust_emission_factors.csv")
        self.lineEditEmiFactFD.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditEmiFactFD.setFixedHeight(30)
        self.customDatafileFDGridLayout.addWidget(self.labelEmiFactFD, 0, 0)
        self.customDatafileFDGridLayout.addWidget(self.browseBtnEmiFactFD, 0, 1)
        self.customDatafileFDGridLayout.addWidget(self.lineEditEmiFactFD, 0, 2, 1, 3)

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


    # Functions used for Fugitive Dust

    def getfilesEmiFactFD(self):
        fileNameTruckCapaFD = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        if fileNameTruckCapaFD[0] != "":
            selectedFileNameTruckCapaFD = fileNameTruckCapaFD[0].split("FPEAM/")
            self.lineEditEmiFactFD.setText(selectedFileNameTruckCapaFD[1])

    def rresetFields(self):

        self.lineEditScenaName.setStyleSheet("border: 2px solid black;")
        self.lineEditProjectPath.setStyleSheet("border: 2px solid black;")

        self.plainTextLog.setPlainText("")

        # FPEAM home page - Attribute Initialization
        self.lineEditScenaName.setText("")
        self.lineEditProjectPath.setText("")
        self.checkBoxMoves.setChecked(True)
        self.checkBoxNonroad.setChecked(True)
        self.checkBoxEmissionFactors.setChecked(True)
        self.checkBoxFugitiveDust.setChecked(True)
        self.index = self.comboBoxVerbosityLevel.findText("DEBUG")
        self.comboBoxVerbosityLevel.setCurrentIndex(self.index)
        self.lineEditEq.setText("data/equipment/bts16_equipment.csv")
        self.lineEditProd.setText("data/production/production_2015_bc1060.csv")
        self.lineEditFedLossFact.setText("data/inputs/feedstock_loss_factors.csv")
        self.lineEditTransGraph.setText("data/inputs/transportation_graph.csv")
        self.index = self.comboBoxBF.findText("Yes")
        self.comboBoxBF.setCurrentIndex(self.index)
        self.index = self.comboBoxRE.findText("Yes")
        self.comboBoxRE.setCurrentIndex(self.index)

        # Fugitive Dust module - Attribute Initialization
        self.lineEditFeedMeasureTypeFD.setText("harvested")
        self.lineEditEmiFactFD.setText("../data/inputs/fugitive_dust_emission_factors.csv")

        # Emission Factors Module - Attribute Initialization
        self.lineEditFeedMeasureTypeEF.setText("harvested")
        self.lineEditEmiFact.setText('data/inputs/emission_factors.csv')
        self.lineEditResDist.setText('data/inputs/resource_distribution.csv')

        # Nonroad Module - Attribute Initialization
        self.index = self.comboBoxYearNon.findText("2017")
        self.comboBoxYearNon.setCurrentIndex(self.index)
        self.lineEditDbHostN.setText("localhost")
        self.lineEditDbUsernameN.setText("root")
        self.lineEditDbNameN.setText("movesdb20151028")
        self.lineEditDbPwdN.setText("root")
        self.lineEditFeedMeasureTypeNon.setText("harvested")
        self.lineEditTimeResNamesNon.setText("time")
        self.lineEditForestryNamesNon.setText('forest whole tree')
        self.lineEditFipsNon.setText("../data/inputs/region_fips_map.csv")
        self.lineEditDatafilesNon.setText("C:/Nonroad")
        self.lineEditMinTemp.setText("50.0")
        self.lineEditMaxTemp.setText("68.8")
        self.lineEditMeanTemp.setText("60.0")
        self.lineEditLowHeat.setText("0.12845")
        self.lineEditNH3.setText("0.68")
        self.lineEditHydro.setText("1.053")
        self.lineEditPM10.setText("0.97")
        self.lineEditFeedMeasureTypeIrrigNon.setText("planted")
        self.lineEditFeedIrrigNamesNon.setText("corn grain")
        self.lineEditNonIrrig.setText("../data/inputs/irrigation.csv")
        self.comboBoxEncodeNames.setCurrentText("Yes")

        # Moves Module - Attribute Initialization
        self.index = self.comboBoxAggLevel.findText("By County")
        self.comboBoxAggLevel.setCurrentIndex(self.index)
        self.index = self.comboBoxCachedResUse.findText("Yes")
        self.comboBoxCachedResUse.setCurrentIndex(self.index)
        self.lineEditFeedMeasureType.setText("production")
        self.lineEditVMTperTruck.setText("20")
        self.spinBoxNoofTruck.setValue(1)
        self.index = self.comboBoxYear.findText("2017")
        self.comboBoxYear.setCurrentIndex(self.index)
        self.lineEditDbHost.setText("localhost")
        self.lineEditDbUsername.setText("root")
        self.lineEditDbName.setText("movesdb20151028")
        self.lineEditDbPwd.setText("root")
        self.lineEditDatafiles.setText("C:\MOVESdatb")
        self.lineEditMovesPath.setText("C:\MOVES2014b")
        self.lineEditTruckCapa.setText("../data/inputs/truck_capacity.csv")
        self.lineEditAVFT.setText("../data/inputs/avft.csv")
        self.lineEditFips.setText("../data/inputs/region_fips_map.csv")
        self.lineEditRuralRes.setText("0.30")
        self.lineEditRuralUnres.setText("0.28")
        self.lineEditUrbanRes.setText("0.21")
        self.lineEditUrbanUnres.setText("0.21")
        self.index = self.comboBoxMonth.findText("10")
        self.comboBoxMonth.setCurrentIndex(self.index)
        self.index = self.comboBoxBegHr.findText("7")
        self.comboBoxBegHr.setCurrentIndex(self.index)
        self.index = self.comboBoxDate.findText("5")
        self.comboBoxDate.setCurrentIndex(self.index)
        self.index = self.comboBoxEndHr.findText("18")
        self.comboBoxEndHr.setCurrentIndex(self.index)
        self.index = self.comboBoxDayType.findText("Weekday")
        self.comboBoxDayType.setCurrentIndex(self.index)

        print("-------------------------Reset clicked")

###################################################################

    # Run Button
    def runTheSelectedModules(self):

        self.attributeValueObj = AttributeValueStorage()

        tmpFolder = tempfile.mkdtemp()

        # check if scenario name and project path is entered or not
        if self.lineEditScenaName.text() == "" or self.lineEditProjectPath.text() == "":
            if self.lineEditScenaName.text() == "" and self.lineEditProjectPath.text() != "":
                self.lineEditScenaName.setStyleSheet("border: 2px solid red;")
                self.lineEditProjectPath.setStyleSheet("border: 2px solid black;")
            if self.lineEditProjectPath.text() == "" and self.lineEditScenaName.text() != "":
                self.lineEditScenaName.setStyleSheet("border: 2px solid black;")
                self.lineEditProjectPath.setStyleSheet("border: 2px solid red;")
            if self.lineEditScenaName.text() == "" and self.lineEditProjectPath.text() == "":
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
                self.selected_module_string += "'" + "MOVES" + "'"
                self.self.attributeValueObj.module = self.selected_module_string
                self.selected_module_string += ", "
            if self.checkBoxNonroad.isChecked():

                #attributeValueObj.module = self.selected_module_list.append(self.checkBoxNonroad.text())
                self.selected_module_string += "'" + "NONROAD" + "'"
                self.attributeValueObj.module = self.selected_module_string
                self.selected_module_string += ", "
            if self.checkBoxEmissionFactors.isChecked():

                #attributeValueObj.module = self.selected_module_list.append(self.checkBoxEmissionFactors.text())
                self.selected_module_string +=  "'" + "emissionfactors" + "'"
                self.attributeValueObj.module = self.selected_module_string
                self.selected_module_string += ", "
            if self.checkBoxFugitiveDust.isChecked():

                #attributeValueObj.module = "'" + self.selected_module_list.append(self.checkBoxFugitiveDust.text())
                self.selected_module_string +=  "'" + "fugitvedust" + "'"
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

            changedDbHostN = self.lineEditDbHostN.text().strip()
            if changedDbHostN:
                self.attributeValueObj.dbHostN = changedDbHostN

            changedDbUsernameN = self.lineEditDbUsernameN.text().strip()
            if changedDbUsernameN:
                self.attributeValueObj.dbUsernameN = changedDbUsernameN

            changedDbNameN = self.lineEditDbNameN.text().strip()
            if changedDbNameN:
                self.attributeValueObj.dbNameN = changedDbNameN

            changedDbPwdN = self.lineEditDbPwdN.text().strip()
            if changedDbPwdN:
                self.attributeValueObj.dbPwdN = changedDbPwdN

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

            # Emission Factors attributes value Initialization

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
            if self.checkBoxMoves.isChecked():
                movesConfigCreationObj = movesConfigCreation(tmpFolder)
            if self.checkBoxNonroad.isChecked():
                nonroadConfigCreationObj = nonroadConfigCreation(tmpFolder)
            if self.checkBoxEmissionFactors.isChecked():
                emissionFactorsConfigCreationObj = emissionFactorsConfigCreation(tmpFolder, self.attributeValueObj)
            if self.checkBoxFugitiveDust.isChecked():
                fugitiveDustConfigCreationObj = fugitiveDustConfigCreation(tmpFolder)
            runConfigObj = runConfigCreation(tmpFolder, self.attributeValueObj)

            # run FugitiveDust module
            command = "fpeam " + runConfigObj + " --emissionfactors_config " + emissionFactorsConfigCreationObj
            print(command)

            # Display logs in result tab after completion of running
            self.centralwidget.setCurrentWidget(self.tabResult)


            threadMOVES = None
            threadNONROAD = None
            threadEF = None
            threadFD = None
            self.centralwidget.setTabEnabled(0, False)

            if self.centralwidget.isTabEnabled(1):
                self.centralwidget.setTabEnabled(1, False)
                threadMOVES = threading.Thread(target= runCommand , args = (runConfigObj , movesConfigCreationObj, self.attributeValueObj, self.plainTextLog, ))
                threadMOVES.start()

            if self.centralwidget.isTabEnabled(2):
                self.centralwidget.setTabEnabled(2, False)
                threadNONROAD = threading.Thread(target= runCommand , args = (runConfigObj , nonroadConfigCreationObj, self.attributeValueObj, self.plainTextLog, ))
                threadNONROAD.start()

            if self.centralwidget.isTabEnabled(3):
                self.centralwidget.setTabEnabled(3, False)
                threadEF = threading.Thread(target= runCommand , args = (runConfigObj , emissionFactorsConfigCreationObj, self.attributeValueObj, self.plainTextLog, ))
                threadEF.start()

            if self.centralwidget.isTabEnabled(4):
                self.centralwidget.setTabEnabled(4, False)
                threadFD = threading.Thread(target= runCommand , args = (runConfigObj , fugitiveDustConfigCreationObj, self.attributeValueObj, self.plainTextLog, ))
                threadFD.start()

            while (threadMOVES and threadMOVES.is_alive()) or \
                    (threadNONROAD and threadNONROAD.is_alive()) or \
                    (threadEF and threadEF.is_alive()) or \
                    (threadFD and threadFD.is_alive()):
                #print("alive. Waiting for 1 second to recheck")

                self.progressBar.setVisible(True)
                self.progressBar.move(300,200)
                # self.completed += 1
                # self.progressBar.setValue(self.completed)
                # self.completed %= 100
                self.progressBar.setRange(0,0)

                loop = QEventLoop()
                QTimer.singleShot(10, loop.quit)
                loop.exec_()

            self.progressBar.setVisible(False)
            #self.plainTextLog.setVisible(True)


            if threadMOVES:
                threadMOVES.join()
                self.centralwidget.setTabEnabled(1, True)
            if threadNONROAD:
                threadNONROAD.join()
                self.centralwidget.setTabEnabled(2, True)
            if threadEF:
                threadEF.join()
                self.centralwidget.setTabEnabled(3, True)
            if threadFD:
                threadFD.join()
                self.centralwidget.setTabEnabled(4, True)
            self.centralwidget.setTabEnabled(0, True)

            # Set logs to Plaintext in Result tab
            #self.plainTextLog.setPlainText(self.attributeValueObj.logContents)

            # #Generate graph for MOVES module
            # fileNameMoves = self.lineEditScenaName.text().strip() + "_raw.csv"
            # dataframePathMOVES = os.path.join(self.lineEditProjectPath.text().strip(), fileNameMoves)
            # df = pd.read_csv(dataframePathMOVES)
            # df.groupby(['pollutant', 'feedstock_measure']).size().unstack().plot(kind='bar', stacked=True)
            # imageNameMOVES = self.lineEditScenaName.text().strip() + "_output.png"
            # imagePathMOVES = os.path.join(self.lineEditProjectPath.text().strip(), imageNameMOVES)
            # plt.savefig(imagePathMOVES, bbox_inches='tight', dpi='figure')
            # self.pixmap = QtGui.QPixmap(imagePathMOVES)
            # self.labelMOVESGraph.resize(self.width(), self.height())
            # self.labelMOVESGraph.setPixmap(
            #     self.pixmap.scaled(self.labelMOVESGraph.size(), QtCore.Qt.IgnoreAspectRatio))
            #
            # # Generate graph for NONROAD module
            # fileNameNONROAD = self.lineEditScenaName.text().strip() + "_raw.csv"
            # dataframePathNONROAD = os.path.join(self.lineEditProjectPath.text().strip(), fileNameNONROAD)
            # df = pd.read_csv(dataframePathNONROAD)
            # df.groupby(['pollutant', 'feedstock_measure']).size().unstack().plot(kind='bar', stacked=True)
            # imageNameNONROAD = self.lineEditScenaName.text().strip() + "_output.png"
            # imagePathNONROAD = os.path.join(self.lineEditProjectPath.text().strip(), imageNameNONROAD)
            # plt.savefig(imagePathNONROAD, bbox_inches='tight')
            # self.pixmap = QtGui.QPixmap(imagePathNONROAD)
            # self.labelNONROADGraph.resize(self.width(), self.height())
            # self.labelNONROADGraph.setPixmap(
            #     self.pixmap.scaled(self.labelNONROADGraph.size(), QtCore.Qt.IgnoreAspectRatio))
            #
            # # Generate graph for Emissionfactors module
            # fileNameEF = self.lineEditScenaName.text().strip() + "_raw.csv"
            # dataframePathEF = os.path.join(self.lineEditProjectPath.text().strip(), fileNameEF)
            # df = pd.read_csv(dataframePathEF)
            # df.groupby(['pollutant', 'feedstock_measure']).size().unstack().plot(kind='bar', stacked=True)
            # imageNameEF = self.lineEditScenaName.text().strip() + "_output.png"
            # imagePathEF = os.path.join(self.lineEditProjectPath.text().strip(), imageNameEF)
            # plt.savefig(imagePathEF, bbox_inches='tight')
            # self.pixmap = QtGui.QPixmap(imagePathEF)
            # self.labelEmissionFactorsGraph.resize(self.width(), self.height())
            # self.labelEmissionFactorsGraph.setPixmap(
            #     self.pixmap.scaled(self.labelEmissionFactorsGraph.size(), QtCore.Qt.IgnoreAspectRatio))
            #
            # # Generate graph for Emissionfactors module
            # fileNameFD = self.lineEditScenaName.text().strip() + "_raw.csv"
            # dataframePathFD = os.path.join(self.lineEditProjectPath.text().strip(), fileNameFD)
            # df = pd.read_csv(dataframePathFD)
            # df.groupby(['pollutant', 'feedstock_measure']).size().unstack().plot(kind='bar', stacked=True)
            # imageNameFD = self.lineEditScenaName.text().strip() + "_output.png"
            # imagePathFD = os.path.join(self.lineEditProjectPath.text().strip(), imageNameFD)
            # plt.savefig(imagePathFD, bbox_inches='tight')
            # self.pixmap = QtGui.QPixmap(imagePathFD)
            # self.labelFugitivedustGraph.resize(self.width(), self.height())
            # self.labelFugitivedustGraph.setPixmap(
            #     self.pixmap.scaled(self.labelFugitivedustGraph.size(), QtCore.Qt.IgnoreAspectRatio))



    #########################################################################################################################



    def setupUIResult(self):
        # Result tab created
        self.tabResult = QtWidgets.QWidget()
        self.tabResult.resize(WIDTH, HEIGHT - 200)
        # Result tab added
        self.centralwidget.addTab(self.tabResult, "RESULT")

        # Result code start
        windowLayoutResult = QGridLayout()
        windowLayoutResult.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        windowLayoutResult.setColumnStretch(6, 1)

        self.scrollAreaResult = QScrollArea(self.tabResult)
        self.scrollAreaResult.setWidgetResizable(True)
        self.scrollAreaResult.resize(WIDTH, HEIGHT)
        self.scrollAreaResult.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollAreaResult.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self.innerWidgetResult = QtWidgets.QWidget()
        self.innerWidgetResult.resize(WIDTH, HEIGHT)
        self.scrollAreaResult.setWidget(self.innerWidgetResult)
        self.innerWidgetResult.setLayout(windowLayoutResult)

        self.plainTextLog = QPlainTextEdit()
        #self.plainTextLog.setVisible(False)
        self.plainTextLog.setPlainText("")
        self.plainTextLog.setReadOnly(True)
        self.plainTextLog.setFixedHeight(100)
        windowLayoutResult.addWidget(self.plainTextLog, 0, 0, 1 , 4)

        self.labelMOVESGraph = QLabel()
        self.labelMOVESGraph.setFixedHeight(300)
        self.labelMOVESGraph.setFixedWidth(400)
        windowLayoutResult.addWidget(self.labelMOVESGraph,1 , 0)

        self.plainLabel1 = QLabel()
        windowLayoutResult.addWidget(self.plainLabel1, 1, 1)

        self.labelNONROADGraph = QLabel()
        self.labelNONROADGraph.setFixedHeight(300)
        self.labelNONROADGraph.setFixedWidth(400)
        windowLayoutResult.addWidget(self.labelNONROADGraph, 1, 2)

        self.labelEmissionFactorsGraph = QLabel()
        self.labelEmissionFactorsGraph.setFixedHeight(300)
        self.labelEmissionFactorsGraph.setFixedWidth(400)
        windowLayoutResult.addWidget(self.labelEmissionFactorsGraph,2 , 0)

        self.plainLabel2 = QLabel()
        windowLayoutResult.addWidget(self.plainLabel2, 2, 1)

        self.labelFugitivedustGraph = QLabel()
        self.labelFugitivedustGraph.setFixedHeight(300)
        self.labelFugitivedustGraph.setFixedWidth(400)
        windowLayoutResult.addWidget(self.labelFugitivedustGraph, 2, 2)


        self.progressBar = QProgressBar()
        self.progressBar.setVisible(False)
        #self.progressBar.setBarStyle(QRoundProgressBar.BarStyle.DONUT)
        #self.completed = 0
        windowLayoutResult.addWidget(self.progressBar, 0, 0)

        #########################################################################################################################

    def setupUi(self, OtherWindow):

        OtherWindow.setObjectName("OtherWindow")
        self.centralwidget = QtWidgets.QTabWidget(OtherWindow)
        OtherWindow.setCentralWidget(self.centralwidget)
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


class SelectedModuleThreadExecution(QtCore.QThread):
    taskFinished = QtCore.pyqtSignal()

    def __init__(self, runConfigObj, emissionFactorsConfigCreationObj, attributeValueObj):
        super.__init__()
        self.runConfigObj = runConfigObj
        self.emissionFactorsConfigCreationObj = emissionFactorsConfigCreationObj
        self.attributeValueObj = attributeValueObj


    def run(self):
        runCommand(self.runConfigObj,self.emissionFactorsConfigCreationObj,self.attributeValueObj)

        ############################################################################

def logsPrinter(textField, loggerOutputFilePath, doRun):
    with open(loggerOutputFilePath) as f:
        while doRun:

            line = f.readline()
            if not line:
                time.sleep(0.1)
            else:
                textField.appendPlainText(line)

def runCommand(runConfigObj , emissionFactorsConfigCreationObj, attributeValueStorageObj, textFieldLog):
    # Generate Logs
    loggerOutputFilePath = time.strftime("%Y%m%d-%H%M%S") + ''.join(
        random.choice(string.ascii_letters) for _ in range(10)) + ".log"
    tempfile.gettempdir()
    loggerOutputFilePath = os.path.join(tempfile.gettempdir(), loggerOutputFilePath)

    logging.basicConfig(level='DEBUG', format='%(asctime)s, %(levelname)-8s'
                                              ' [%(filename)s:%(module)s.'
                                              '%(funcName)s.%(lineno)d] %(message)s',
                        filename=loggerOutputFilePath)

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

    doRun = True

    t = threading.Thread(target=logsPrinter, args=(textFieldLog, loggerOutputFilePath, doRun,))
    t.daemon = True
    t.start()

    with FPEAM(run_config=_config) as _fpeam:

        # count no of record based on how many counties are running
        _fpeam.run()

        # save the raw results to the project path folder specified in run_config
        _fpath = os.path.join(_fpeam.config['project_path'],
                              '%s_raw.csv' % _fpeam.config['scenario_name'])
        _fpeam.results.to_csv(_fpath, index=False)

        # save several summarized results files to the project folder
        _fpeam.summarize()
        print("Done")

    #attributeValueStorageObj.logContents = attributeValueStorageObj.streamGenerated.getvalue()

    with open(loggerOutputFilePath) as lg:
        print(lg.readlines())

##############################################################################################



if __name__ == "__main__":

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
        background: #ffffff;
        border: 1px solid #495965;
        box-sizing: border-box;
        box-shadow: 1px 1px 2px rgba(0, 0, 0, 0.25);
        border-radius: 5px;
        font-family: Roboto;
        font-style: normal;
        font-weight: bold;
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
        color: #028ACC;
        
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
        color: #028ACC;
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
    
    QPushButton#expandCollapseIcon {
        background: #ffffff;
        align-items: center;
        text-align: center;        
        color: #000000;  
        border: 1px solid #ffffff; 
        font-style: bold;
        font-size : 30px   
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
        border-radius: 5px;
        font-family: Roboto;
        font-style: normal;
        font-weight: normal;
        font-size: 14px;
        text-align: center;        
        color: #000000;          
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
    
    QScrollBar {
        background-color: grey;
    }
    
    QTabBar::tab:selected {
        background: 028ACC;
    }
    
    
    
    """

    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(styleSheet)
    OtherWindow = QtWidgets.QMainWindow()
    OtherWindow.setFixedSize(WIDTH,HEIGHT+25)
    OtherWindow.setWindowTitle("FPEAM")
    #OtherWindow.setWindowFlags(QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowMinimizeButtonHint)
    ui = AlltabsModule()
    ui.setupUi(OtherWindow)
    OtherWindow.show()
    sys.exit(app.exec_())