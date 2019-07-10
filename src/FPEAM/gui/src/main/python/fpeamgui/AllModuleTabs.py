# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'OtherWindow.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!
import os

#import args as args
import self as self
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtWidgets import QRadioButton, QComboBox, QPushButton, QTextEdit, QFileDialog, QMessageBox
from PyQt5.QtWidgets import QGridLayout, QLabel, QButtonGroup, QLineEdit, QSpinBox, QCheckBox


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
import subprocess
from configparser import *

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
        self.labelRE.setToolTip("Do you want to se Router Engine - Yes/No")
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
        self.labelBF.setToolTip("Do you want to se Backfill Flag - Yes/No")
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
        self.labelEq = QLabel()
        self.labelEq.setText("Equipment")
        self.labelEq.setToolTip("Select equipment input dataset")
        self.radioGroupEq = QButtonGroup(self.windowLayout)
        self.radioButtonEqDefault = QRadioButton("Default")
        self.radioButtonEqDefault.setFixedWidth(100)
        self.radioButtonEqDefault.setFixedHeight(30)
        self.radioButtonEqDefault.setChecked(True)
        self.radioButtonEqDefault.toggled.connect(self.radioButtonEqDefaultClicked)
        self.radioButtonEqCustom = QRadioButton("Custom")
        self.radioButtonEqCustom.setFixedWidth(100)
        self.radioButtonEqCustom.setFixedHeight(30)
        self.radioButtonEqCustom.toggled.connect(self.radioButtonEqCustomClicked)
        self.radioGroupEq.addButton(self.radioButtonEqDefault)
        self.radioGroupEq.addButton(self.radioButtonEqCustom)
        self.browseBtnEq = QPushButton("Browse", self)
        self.browseBtnEq.setFixedWidth(100)
        self.browseBtnEq.clicked.connect(self.getfilesEq)
        self.browseBtnEq.setEnabled(False)
        self.browseBtnEq.hide()
        self.lineEditEq = QLineEdit(self)
        self.lineEditEq.setFixedWidth(100)
        self.lineEditEq.hide()
        self.windowLayout.addWidget(self.labelEq, 7, 0)
        self.windowLayout.addWidget(self.radioButtonEqDefault, 7, 1)
        self.windowLayout.addWidget(self.radioButtonEqCustom, 7, 2)
        self.windowLayout.addWidget(self.browseBtnEq, 7, 3)
        self.windowLayout.addWidget(self.lineEditEq, 7, 4)

        # UI element - Production
        self.labelProd = QLabel()
        self.labelProd = QLabel()
        self.labelProd.setText("Production")
        self.labelProd.setToolTip("Select production input dataset")
        self.radioGroupProd = QButtonGroup(self.windowLayout)
        self.radioButtonProdDefault = QRadioButton("Default")
        self.radioButtonProdDefault.setFixedWidth(100)
        self.radioButtonProdDefault.setFixedHeight(30)
        self.radioButtonProdDefault.setChecked(True)
        self.radioButtonProdDefault.toggled.connect(self.radioButtonProdDefaultClicked)
        self.radioButtonProdCustom = QRadioButton("Custom")
        self.radioButtonProdCustom.setFixedWidth(100)
        self.radioButtonProdCustom.setFixedHeight(30)
        self.radioButtonProdCustom.toggled.connect(self.radioButtonProdCustomClicked)
        self.radioGroupProd.addButton(self.radioButtonProdDefault)
        self.radioGroupProd.addButton(self.radioButtonProdCustom)
        self.browseBtnProd = QPushButton("Browse", self)
        self.browseBtnProd.setFixedWidth(100)
        self.browseBtnProd.clicked.connect(self.getfilesProd)
        self.browseBtnProd.setEnabled(False)
        self.browseBtnProd.hide()
        self.lineEditProd = QLineEdit(self)
        self.lineEditProd.setFixedWidth(100)
        self.lineEditProd.hide()
        self.windowLayout.addWidget(self.labelProd, 8, 0)
        self.windowLayout.addWidget(self.radioButtonProdDefault, 8, 1)
        self.windowLayout.addWidget(self.radioButtonProdCustom, 8, 2)
        self.windowLayout.addWidget(self.browseBtnProd, 8, 3)
        self.windowLayout.addWidget(self.lineEditProd, 8, 4)

        # Feedstock Loss Factors
        self.labelFedLossFact = QLabel()
        self.labelFedLossFact = QLabel()
        self.labelFedLossFact.setText("Feedstock Loss Factors")
        self.labelFedLossFact.setToolTip("Select Feedstock Loss Factors dataset")
        self.radioGroupFeedLossFact = QButtonGroup(self.windowLayout)
        self.radioButtonFedLossFactDefault = QRadioButton("Default")
        self.radioButtonFedLossFactDefault.setFixedWidth(100)
        self.radioButtonFedLossFactDefault.setFixedHeight(30)
        self.radioButtonFedLossFactDefault.setChecked(True)
        self.radioButtonFedLossFactDefault.toggled.connect(self.radioButtonFLossDefaultClicked)
        self.radioButtonFedLossFactCustom = QRadioButton("Custom")
        self.radioButtonFedLossFactCustom.setFixedWidth(100)
        self.radioButtonFedLossFactCustom.setFixedHeight(30)
        self.radioButtonFedLossFactCustom.toggled.connect(self.radioButtonFLossCustomClicked)
        self.radioGroupFeedLossFact.addButton(self.radioButtonFedLossFactDefault)
        self.radioGroupFeedLossFact.addButton(self.radioButtonFedLossFactCustom)
        self.browseBtnFLoss = QPushButton("Browse", self)
        self.browseBtnFLoss.setFixedWidth(100)
        self.browseBtnFLoss.clicked.connect(self.getfilesFLoss)
        self.browseBtnFLoss.setEnabled(False)
        self.browseBtnFLoss.hide()
        self.lineEditFedLossFact = QLineEdit(self)
        self.lineEditFedLossFact.setFixedWidth(100)
        self.lineEditFedLossFact.hide()
        self.windowLayout.addWidget(self.labelFedLossFact, 9, 0)
        self.windowLayout.addWidget(self.radioButtonFedLossFactDefault, 9, 1)
        self.windowLayout.addWidget(self.radioButtonFedLossFactCustom, 9, 2)
        self.windowLayout.addWidget(self.browseBtnFLoss, 9, 3)
        self.windowLayout.addWidget(self.lineEditFedLossFact, 9, 4)

        # Transportation graph
        self.labelTransGraph = QLabel()
        self.labelTransGraph = QLabel()
        self.labelTransGraph.setText("Transportation Graph")
        self.labelTransGraph.setToolTip("Select Transportation graph dataset")
        self.radioGroupTransGraph = QButtonGroup(self.windowLayout)
        self.radioButtonTransGraphDefault = QRadioButton("Default")
        self.radioButtonTransGraphDefault.setFixedWidth(100)
        self.radioButtonTransGraphDefault.setFixedHeight(30)
        self.radioButtonTransGraphDefault.setChecked(True)
        self.radioButtonTransGraphDefault.toggled.connect(self.radioButtonTransGrDefaultClicked)
        self.radioButtonTransGraphCustom = QRadioButton("Custom")
        self.radioButtonTransGraphCustom.setFixedWidth(100)
        self.radioButtonTransGraphCustom.setFixedHeight(30)
        self.radioButtonTransGraphCustom.toggled.connect(self.radioButtonTransGrCustomClicked)
        self.radioGroupTransGraph.addButton(self.radioButtonTransGraphDefault)
        self.radioGroupTransGraph.addButton(self.radioButtonTransGraphCustom)
        self.browseBtnTransGr = QPushButton("Browse", self)
        self.browseBtnTransGr.setFixedWidth(100)
        self.browseBtnTransGr.clicked.connect(self.getfilesTransGr)
        self.browseBtnTransGr.setEnabled(False)
        self.browseBtnTransGr.hide()
        self.lineEditTransGraph = QLineEdit(self)
        self.lineEditTransGraph.setFixedWidth(100)
        self.lineEditTransGraph.hide()
        self.windowLayout.addWidget(self.labelTransGraph, 10, 0)
        self.windowLayout.addWidget(self.radioButtonTransGraphDefault, 10, 1)
        self.windowLayout.addWidget(self.radioButtonTransGraphCustom, 10, 2)
        self.windowLayout.addWidget(self.browseBtnTransGr, 10, 3)
        self.windowLayout.addWidget(self.lineEditTransGraph, 10, 4)

        # County Node
        self.labelCountyNode = QLabel()
        self.labelCountyNode = QLabel()
        self.labelCountyNode.setText("County Node")
        self.labelCountyNode.setToolTip("Select County Node dataset")
        self.radioGroupCountyNode = QButtonGroup(self.windowLayout)
        self.radioButtonCountyNodeDefault = QRadioButton("Default")
        self.radioButtonCountyNodeDefault.setChecked(True)
        self.radioButtonCountyNodeDefault.toggled.connect(self.radioButtonCountyNodeDefaultClicked)
        self.radioButtonCountyNodeCustom = QRadioButton("Custom")
        self.radioButtonCountyNodeCustom.toggled.connect(self.radioButtonCountyNodeCustomClicked)
        self.radioGroupCountyNode.addButton(self.radioButtonCountyNodeDefault)
        self.radioGroupCountyNode.addButton(self.radioButtonCountyNodeCustom)
        self.browseBtnCountyNode = QPushButton("Browse", self)
        self.browseBtnCountyNode.clicked.connect(self.getfilesCountyNode)
        self.browseBtnCountyNode.setEnabled(False)
        self.browseBtnCountyNode.hide()
        self.lineEditCountyNode = QLineEdit(self)
        self.lineEditCountyNode.hide()
        self.windowLayout.addWidget(self.labelCountyNode, 11, 0)
        self.windowLayout.addWidget(self.radioButtonCountyNodeDefault, 11, 1)
        self.windowLayout.addWidget(self.radioButtonCountyNodeCustom, 11, 2)
        self.windowLayout.addWidget(self.browseBtnCountyNode, 11, 3)
        self.windowLayout.addWidget(self.lineEditCountyNode, 11, 4)


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
    def radioButtonEqDefaultClicked(self, enabled):
        if enabled:
            self.browseBtnEq.hide()
            self.lineEditEq.hide()
            self.browseBtnEq.setEnabled(False)
            self.lineEditEq.setEnabled(False)

    def radioButtonEqCustomClicked(self, enabled):
        if enabled:
            self.browseBtnEq.show()
            self.lineEditEq.show()
            self.browseBtnEq.setEnabled(True)
            self.lineEditEq.setEnabled(True)

    def getfilesEq(self):
        fileNameEq = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        fileNameEqWithBracketEq = str(fileNameEq).split(',')
        fileNameEqWitoutBracketEq = str(fileNameEqWithBracketEq).split('(')
        selectedFileNameEq = str(fileNameEqWitoutBracketEq).split(',')
        self.lineEditEq.setText(selectedFileNameEq[1])

    # Production
    def radioButtonProdDefaultClicked(self, enabled):
        if enabled:
            self.browseBtnProd.hide()
            self.lineEditProd.hide()
            self.browseBtnProd.setEnabled(False)
            self.lineEditProd.setEnabled(False)

    def radioButtonProdCustomClicked(self, enabled):
        if enabled:
            self.browseBtnProd.show()
            self.lineEditProd.show()
            self.browseBtnProd.setEnabled(True)
            self.lineEditProd.setEnabled(True)

    def getfilesProd(self):
        fileNameProd = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        fileNameEqWithBracketProd = str(fileNameProd).split(',')
        fileNameEqWitoutBracketProd = str(fileNameEqWithBracketProd).split('(')
        selectedFileNameProd = str(fileNameEqWitoutBracketProd).split(',')
        self.lineEditProd.setText(selectedFileNameProd[1])

    # Feedstock Loss Factors
    def radioButtonFLossDefaultClicked(self, enabled):
        if enabled:
            self.browseBtnFLoss.hide()
            self.lineEditFedLossFact.hide()
            self.browseBtnFLoss.setEnabled(False)
            self.lineEditFedLossFact.setEnabled(False)

    def radioButtonFLossCustomClicked(self, enabled):
        if enabled:
            self.browseBtnFLoss.show()
            self.lineEditFedLossFact.show()
            self.browseBtnFLoss.setEnabled(True)
            self.lineEditFedLossFact.setEnabled(True)

    def getfilesFLoss(self):
        fileNameFLoss = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        fileNameEqWithBracketFLoss = str(fileNameFLoss).split(',')
        fileNameEqWitoutBracketFLoss = str(fileNameEqWithBracketFLoss).split('(')
        selectedFileNameFLoss = str(fileNameEqWitoutBracketFLoss).split(',')
        self.lineEditFedLossFact.setText(selectedFileNameFLoss[1])

    # Transportation graph
    def radioButtonTransGrDefaultClicked(self, enabled):
        if enabled:
            self.browseBtnTransGr.hide()
            self.lineEditTransGraph.hide()
            self.browseBtnTransGr.setEnabled(False)
            self.lineEditTransGraph.setEnabled(False)

    def radioButtonTransGrCustomClicked(self, enabled):
        if enabled:
            self.browseBtnTransGr.show()
            self.lineEditTransGraph.show()
            self.browseBtnTransGr.setEnabled(True)
            self.lineEditTransGraph.setEnabled(True)

    def getfilesTransGr(self):
        fileNameTransGr = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        fileNameEqWithBracketTransGr = str(fileNameTransGr).split(',')
        fileNameEqWitoutBracketTransGr = str(fileNameEqWithBracketTransGr).split('(')
        selectedFileNameTransGr = str(fileNameEqWitoutBracketTransGr).split(',')
        self.lineEditTransGraph.setText(selectedFileNameTransGr[1])

    # County Node
    def radioButtonCountyNodeDefaultClicked(self, enabled):
        if enabled:
            self.browseBtnCountyNode.hide()
            self.lineEditCountyNode.hide()
            self.browseBtnCountyNode.setEnabled(False)
            self.lineEditCountyNode.setEnabled(False)

    def radioButtonCountyNodeCustomClicked(self, enabled):
        if enabled:
            self.browseBtnCountyNode.show()
            self.lineEditCountyNode.show()
            self.browseBtnCountyNode.setEnabled(True)
            self.lineEditCountyNode.setEnabled(True)

    def getfilesCountyNode(self):
        fileNameCountyNode = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        fileNameEqWithBracketCountyNode = str(fileNameCountyNode).split(',')
        fileNameEqWitoutBracketCountyNode = str(fileNameEqWithBracketCountyNode).split('(')
        selectedFileNameCountyNode = str(fileNameEqWitoutBracketCountyNode).split(',')
        self.lineEditCountyNode.setText(selectedFileNameCountyNode[1])




        ###########################################################################################################################################################################

    def setupUIMoves(self):
        # MOves tab created
        self.tabMoves = QtWidgets.QWidget()


        # Moves tab added
        self.centralwidget.addTab(self.tabMoves, "MOVES")

        # Moves code start
        self.windowLayout = QGridLayout()
        self.windowLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.windowLayout.setColumnStretch(3, 1)
        self.windowLayout.setColumnStretch(4, 1)

        self.tabMoves.setLayout(self.windowLayout)

        # Created UI element Aggregation Level

        self.labelAggLevel = QLabel()
        self.labelAggLevel = QLabel()
        self.labelAggLevel.setText("Aggregation Level")
        self.radioGroupAggLevel = QButtonGroup(self.windowLayout)
        self.radioButtonByCounty = QRadioButton("Moves By Each County")
        self.radioButtonByCounty.setChecked(True)
        self.radioButtonByState = QRadioButton("Moves By State ")
        self.radioButtonByStateandFeed = QRadioButton("Moves By State and Feedstock ")
        self.radioGroupAggLevel.addButton(self.radioButtonByCounty)
        self.radioGroupAggLevel.addButton(self.radioButtonByState)
        self.radioGroupAggLevel.addButton(self.radioButtonByStateandFeed)
        self.windowLayout.addWidget(self.labelAggLevel, 1, 0)
        self.windowLayout.addWidget(self.radioButtonByCounty, 1, 1)
        self.windowLayout.addWidget(self.radioButtonByState, 1, 2)
        self.windowLayout.addWidget(self.radioButtonByStateandFeed, 1, 3)

        # Created UI element Cached Result usage
        self.labelCachedResUse = QLabel()
        self.labelCachedResUse.setText("Cached Result usage")
        self.labelCachedResUse.setToolTip("Use existing results in MOVES output database or run MOVES for all counties")
        self.comboBoxCachedResUse = QComboBox(self)
        self.comboBoxCachedResUse.addItem("Yes")
        self.comboBoxCachedResUse.addItem("No")
        self.index = self.comboBoxCachedResUse.findText("Yes")
        self.comboBoxCachedResUse.setCurrentIndex(self.index)
        self.windowLayout.addWidget(self.labelCachedResUse, 2, 0)
        self.windowLayout.addWidget(self.comboBoxCachedResUse, 2, 1)

        # Created UI element Feedstock Measure Type
        self.labelFeedMeasureType = QLabel()
        self.labelFeedMeasureType.setText("Feedstock Measure Type")
        self.labelFeedMeasureType.setToolTip("Enter Feedstock Measure Type Identifier")
        self.lineEditFeedMeasureType = QLineEdit(self)
        regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(regex)
        self.lineEditFeedMeasureType.setValidator(validator)
        self.lineEditFeedMeasureType.setPlaceholderText("Production")
        self.windowLayout.addWidget(self.labelFeedMeasureType, 3, 0)
        self.windowLayout.addWidget(self.lineEditFeedMeasureType, 3, 1)

        # Created UI element Moves Path
        self.MovesPathLable = QLabel()
        self.MovesPathLable.setText("Moves Path")
        self.MovesPathLable.setToolTip("Path where Moves is installed. If it's not installed, then download from the link - <a href ='https://www.epa.gov/moves/moves-versions-limited-current-use#downloading-2014a'>MOVES</a> ")
        #self.MovesPathLable.setToolTipDuration(10)
        self.radioGroupMovesPath = QButtonGroup(self.windowLayout)
        self.radioButtonMovesPathDefault = QRadioButton("Default")
        self.radioButtonMovesPathDefault.setChecked(True)
        self.radioButtonMovesPathDefault.toggled.connect(self.radioButtonDeMovesPathDefaultClicked)
        self.radioButtonMovesPathCustom = QRadioButton("Custom")
        self.radioButtonMovesPathCustom.toggled.connect(self.radioButtonDeMovesPathCustomClicked)
        self.radioGroupMovesPath.addButton(self.radioButtonMovesPathDefault)
        self.radioGroupMovesPath.addButton(self.radioButtonMovesPathCustom)
        self.browseBtnMovesPath = QPushButton("Browse", self)
        self.browseBtnMovesPath.setEnabled(False)
        self.browseBtnMovesPath.hide()
        self.browseBtnMovesPath.clicked.connect(self.getfilesMovesPath)
        self.lineEditMovesPath = QLineEdit(self)
        self.lineEditMovesPath.setEnabled(False)
        self.lineEditMovesPath.hide()
        self.windowLayout.addWidget(self.MovesPathLable, 4, 0)
        self.windowLayout.addWidget(self.radioButtonMovesPathDefault, 4, 1)
        self.windowLayout.addWidget(self.radioButtonMovesPathCustom, 4, 2)
        self.windowLayout.addWidget(self.browseBtnMovesPath, 4, 3)
        self.windowLayout.addWidget(self.lineEditMovesPath, 4,4)

        # Created UI element VMT per Truck
        self.labelVMTperTruck = QLabel()
        self.labelVMTperTruck.setText("VMT per Truck")
        self.labelVMTperTruck.setToolTip("Vehicle Miles Traveled calculated per Truck")
        self.lineEditVMTperTruck = QLineEdit(self)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 6)
        self.lineEditVMTperTruck.setValidator(self.onlyFlaot)
        self.lineEditVMTperTruck.setPlaceholderText("20")
        self.windowLayout.addWidget(self.labelVMTperTruck, 5, 0)
        self.windowLayout.addWidget(self.lineEditVMTperTruck, 5, 1)


        # Created UI element No of Trucks used
        self.labelNoofTruck = QLabel()
        self.labelNoofTruck.setText("No of Trucks used")
        self.labelNoofTruck.setToolTip("No of trucks used in a scenario")
        self.spinBoxNoofTruck = QSpinBox()
        self.spinBoxNoofTruck.setMinimum(1)
        self.spinBoxNoofTruck.setValue(1)
        self.windowLayout.addWidget(self.labelNoofTruck, 6, 0)
        self.windowLayout.addWidget(self.spinBoxNoofTruck, 6, 1)

        # Created UI element Year
        self.labelYear = QLabel()
        self.labelYear.setText("Year")
        self.labelYear.setToolTip("Start year of Equipment")
        self.comboBoxYear = QComboBox(self)
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
        for i in range(1, 25):
            self.number = i
            self.comboBoxEndHr.addItem(str(i))
        self.index = self.comboBoxEndHr.findText("18")
        self.comboBoxEndHr.setCurrentIndex(self.index)
        self.windowLayout.addWidget(self.labelEndHr, 12, 0)
        self.windowLayout.addWidget(self.comboBoxEndHr, 12, 1)

        # Created UI element Timestamp - Day Type
        self.labelDayType = QLabel()
        self.labelDayType.setText("Day type")
        self.comboBoxDayType = QComboBox(self)
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
        self.radioGroupTruckCapa = QButtonGroup(self.windowLayout)
        self.radioVuttonTruckCapaDefault = QRadioButton("Default")
        self.radioVuttonTruckCapaDefault.setChecked(True)
        self.radioVuttonTruckCapaDefault.toggled.connect(self.radioButtonTruckCapaDefaultClicked)
        self.radioButtonTruckCapaCustom = QRadioButton("Custom")
        self.radioButtonTruckCapaCustom.toggled.connect(self.radioButtonTruckCapaCustomClicked)
        self.radioGroupTruckCapa.addButton(self.radioVuttonTruckCapaDefault)
        self.radioGroupTruckCapa.addButton(self.radioButtonTruckCapaCustom)
        self.browseBtnTruckCapa = QPushButton("Browse", self)
        self.browseBtnTruckCapa.setEnabled(False)
        self.browseBtnTruckCapa.hide()
        self.browseBtnTruckCapa.clicked.connect(self.getfilesTruckCapa)
        self.lineEditTruckCapa = QLineEdit(self)
        self.lineEditTruckCapa.setEnabled(False)
        self.lineEditTruckCapa.hide()
        self.windowLayout.addWidget(self.labelTruckCapacity, 15, 0)
        self.windowLayout.addWidget(self.radioVuttonTruckCapaDefault, 15, 1)
        self.windowLayout.addWidget(self.radioButtonTruckCapaCustom, 15, 2)
        self.windowLayout.addWidget(self.browseBtnTruckCapa, 15, 3)
        self.windowLayout.addWidget(self.lineEditTruckCapa, 15, 4)

        # Created UI element AVFT
        self.labelAVFT = QLabel()
        self.labelAVFT.setText("AVFT")
        self.labelAVFT.setToolTip("Select AVFT ( fuel fraction by engine type) dataset")
        self.radioGroupAVFT = QButtonGroup(self.windowLayout)
        self.radioVuttonAVFTDefault = QRadioButton("Default")
        self.radioVuttonAVFTDefault.setChecked(True)
        self.radioVuttonAVFTDefault.toggled.connect(self.radioButtonAVFTDefaultClicked)
        self.radioButtonAVFTCustom = QRadioButton("Custom")
        self.radioButtonAVFTCustom.toggled.connect(self.radioButtonAVFTCustomClicked)
        self.radioGroupAVFT.addButton(self.radioVuttonAVFTDefault)
        self.radioGroupAVFT.addButton(self.radioButtonAVFTCustom)
        self.browseBtnAVFT = QPushButton("Browse", self)
        self.browseBtnAVFT.setEnabled(False)
        self.browseBtnAVFT.hide()
        self.browseBtnAVFT.clicked.connect(self.getfilesAVFT)
        self.lineEditAVFT = QLineEdit(self)
        self.lineEditAVFT.setEnabled(False)
        self.lineEditAVFT.hide()
        self.windowLayout.addWidget(self.labelAVFT, 16, 0)
        self.windowLayout.addWidget(self.radioVuttonAVFTDefault, 16, 1)
        self.windowLayout.addWidget(self.radioButtonAVFTCustom, 16, 2)
        self.windowLayout.addWidget(self.browseBtnAVFT, 16, 3)
        self.windowLayout.addWidget(self.lineEditAVFT, 16, 4)

        # Created UI element Region FIPs Map
        self.labelFips = QLabel()
        self.labelFips.setText("Region FIPs Map")
        self.labelFips.setToolTip("Select Region FIPs Map (production region to MOVES FIPS mapping) dataset")
        self.radioGroupFips = QButtonGroup(self.windowLayout)
        self.radioVuttonFipsDefault = QRadioButton("Default")
        self.radioVuttonFipsDefault.setChecked(True)
        self.radioVuttonFipsDefault.toggled.connect(self.radioButtonFipsDefaultClicked)
        self.radioButtonFipsCustom = QRadioButton("Custom")
        self.radioButtonFipsCustom.toggled.connect(self.radioButtonFipsCustomClicked)
        self.radioGroupFips.addButton(self.radioVuttonFipsDefault)
        self.radioGroupFips.addButton(self.radioButtonFipsCustom)
        self.browseBtnFips = QPushButton("Browse", self)
        self.browseBtnFips.setEnabled(False)
        self.browseBtnFips.hide()
        self.browseBtnFips.clicked.connect(self.getfilesFips)
        self.lineEditFips = QLineEdit(self)
        self.lineEditFips.setEnabled(False)
        self.lineEditFips.hide()
        self.windowLayout.addWidget(self.labelFips, 17, 0)
        self.windowLayout.addWidget(self.radioVuttonFipsDefault, 17, 1)
        self.windowLayout.addWidget(self.radioButtonFipsCustom, 17, 2)
        self.windowLayout.addWidget(self.browseBtnFips, 17, 3)
        self.windowLayout.addWidget(self.lineEditFips, 17, 4)

        # Created UI element Moves Datafiles
        self.labelDatafiles = QLabel()
        self.labelDatafiles.setText("Moves Datafiles")
        self.labelDatafiles.setToolTip("Select all input files created for MOVES runs")
        self.radioGroupDatafiles = QButtonGroup(self.windowLayout)
        self.radioVuttonDatafilesDefault = QRadioButton("Default")
        self.radioVuttonDatafilesDefault.setChecked(True)
        self.radioVuttonDatafilesDefault.toggled.connect(self.radioButtonDatafilesDefaultClicked)
        self.radioButtonDatafilesCustom = QRadioButton("Custom")
        self.radioButtonDatafilesCustom.toggled.connect(self.radioButtonDatafilesCustomClicked)
        self.radioGroupDatafiles.addButton(self.radioVuttonDatafilesDefault)
        self.radioGroupDatafiles.addButton(self.radioButtonDatafilesCustom)
        self.browseBtnDatafiles = QPushButton("Browse", self)
        self.browseBtnDatafiles.setEnabled(False)
        self.browseBtnDatafiles.hide()
        self.browseBtnDatafiles.clicked.connect(self.getfilesDatafiles)
        self.lineEditDatafiles = QLineEdit(self)
        self.lineEditDatafiles.setEnabled(False)
        self.lineEditDatafiles.hide()
        self.windowLayout.addWidget(self.labelDatafiles, 18, 0)
        self.windowLayout.addWidget(self.radioVuttonDatafilesDefault, 18, 1)
        self.windowLayout.addWidget(self.radioButtonDatafilesCustom, 18, 2)
        self.windowLayout.addWidget(self.browseBtnDatafiles, 18, 3)
        self.windowLayout.addWidget(self.lineEditDatafiles, 18, 4)

        # Created UI element VMT Fraction
        self.labelVMTFraction = QLabel()
        self.labelVMTFraction.setText("VMT Fraction")
        self.labelVMTFraction.setToolTip("Fraction of VMT(Vehicle MilesTraveled) by road type (All must sum to 1)")
        self.windowLayout.addWidget(self.labelVMTFraction, 19, 0)

        # Created UI element VMT - Rural Restricted
        self.labelRuralRes = QLabel()
        self.labelRuralRes.setText("Rural Restricted")
        self.lineEditRuralRes = QLineEdit(self)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditRuralRes.setValidator(self.onlyFlaot)
        self.lineEditRuralRes.setPlaceholderText("0.3")
        self.windowLayout.addWidget(self.labelRuralRes, 20, 0)
        self.windowLayout.addWidget(self.lineEditRuralRes, 20, 1)

        # Created UI element VMT - Rural Unrestricted
        self.labelRuralUnres = QLabel()
        self.labelRuralUnres.setText("Rural Unrestricted")
        self.lineEditRuralUnres = QLineEdit(self)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditRuralUnres.setValidator(self.onlyFlaot)
        self.lineEditRuralUnres.setPlaceholderText("0.28")
        self.windowLayout.addWidget(self.labelRuralUnres, 21, 0)
        self.windowLayout.addWidget(self.lineEditRuralUnres, 21, 1)

        # Created UI element VMT - Urban Restricted
        self.labelUrbanRes = QLabel()
        self.labelUrbanRes.setText("Urban Restricted")
        self.lineEditUrbanRes = QLineEdit(self)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditUrbanRes.setValidator(self.onlyFlaot)
        self.lineEditUrbanRes.setPlaceholderText("0.21")
        self.windowLayout.addWidget(self.labelUrbanRes, 22, 0)
        self.windowLayout.addWidget(self.lineEditUrbanRes, 22, 1)

        # Created UI element VMT - Urban Unrestricted
        self.labelUrbanUnres = QLabel()
        self.labelUrbanUnres.setText("Urban Unrestricted")
        self.lineEditUrbanUnres = QLineEdit()
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditUrbanUnres.setValidator(self.onlyFlaot)
        self.lineEditUrbanUnres.setPlaceholderText("0.28")
        self.windowLayout.addWidget(self.labelUrbanUnres, 23, 0)
        self.windowLayout.addWidget(self.lineEditUrbanUnres, 23, 1)


        additionVMTFraction = self.lineEditRuralRes.text() + self.lineEditRuralUnres.text() \
                              + self.lineEditUrbanRes.text() + self.lineEditUrbanUnres.text()

        # Created UI element VMT Fraction Error
        self.labelVMTFractionError = QLabel()
        self.labelVMTFractionError.setText("##########")
        if additionVMTFraction > str(1):
            self.labelVMTFractionError.setText("Sum of all VMT Fraction should be equal to 1")
        self.windowLayout.addWidget(self.labelVMTFractionError, 19, 1)


    # CHeck for consistent input for year
    def handleItemPressedMoves(self, index):
        if str(self.comboBoxYearNon.currentText()) != str(self.comboBoxYear.currentText()):
            self.comboBoxYear.setStyleSheet(
                """QComboBox { background-color: red; color: white }""")

    # Functions used for Moves Path
    def radioButtonDeMovesPathDefaultClicked(self, enabled):
        if enabled:
            self.browseBtnMovesPath.hide()
            self.lineEditMovesPath.hide()
            self.browseBtnMovesPath.setEnabled(False)
            self.lineEditMovesPath.setEnabled(False)

    def radioButtonDeMovesPathCustomClicked(self, enabled):
        if enabled:
            self.browseBtnMovesPath.show()
            self.lineEditMovesPath.show()
            self.browseBtnMovesPath.setEnabled(True)
            self.lineEditMovesPath.setEnabled(True)

    def getfilesMovesPath(self):
        fileNameMovesPath = QFileDialog.getExistingDirectory(self, "Browse")
        selectedFileNameMovesPath = str(fileNameMovesPath).split(',')
        self.lineEditMovesPath.setText(selectedFileNameMovesPath[0])



    # Functions used for Truck Capacity
    def radioButtonTruckCapaDefaultClicked(self, enabled):
        if enabled:
            self.browseBtnTruckCapa.hide()
            self.lineEditTruckCapa.hide()
            self.browseBtnTruckCapa.setEnabled(False)
            self.lineEditTruckCapa.setEnabled(False)

    def radioButtonTruckCapaCustomClicked(self, enabled):
        if enabled:
            self.browseBtnTruckCapa.show()
            self.lineEditTruckCapa.show()
            self.browseBtnTruckCapa.setEnabled(True)
            self.lineEditTruckCapa.setEnabled(True)

    def getfilesTruckCapa(self):
        fileNameTruckCapa = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        fileNameEqWithBracketTruckCapa= str(fileNameTruckCapa).split(',')
        fileNameEqWitoutBracketTruckCapa = str(fileNameEqWithBracketTruckCapa).split('(')
        selectedFileNameTruckCapa = str(fileNameEqWitoutBracketTruckCapa).split(',')
        self.lineEditTruckCapa.setText(selectedFileNameTruckCapa[1])

    # Functions used for AVFT
    def radioButtonAVFTDefaultClicked(self, enabled):
        if enabled:
            self.browseBtnAVFT.hide()
            self.lineEditAVFT.hide()
            self.browseBtnAVFT.setEnabled(False)
            self.lineEditAVFT.setEnabled(False)

    def radioButtonAVFTCustomClicked(self, enabled):
        if enabled:
            self.browseBtnAVFT.show()
            self.lineEditAVFT.show()
            self.browseBtnAVFT.setEnabled(True)
            self.lineEditAVFT.setEnabled(True)

    def getfilesAVFT(self):
        fileNameAVFT = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        fileNameEqWithBracketAVFT= str(fileNameAVFT).split(',')
        fileNameEqWitoutBracketAVFT = str(fileNameEqWithBracketAVFT).split('(')
        selectedFileNameAVFT = str(fileNameEqWitoutBracketAVFT).split(',')
        self.lineEditAVFT.setText(selectedFileNameAVFT[1])


    # Functions used for Fips
    def radioButtonFipsDefaultClicked(self, enabled):
        if enabled:
            self.browseBtnFips.hide()
            self.lineEditFips.hide()
            self.browseBtnFips.setEnabled(False)
            self.lineEditFips.setEnabled(False)

    def radioButtonFipsCustomClicked(self, enabled):
        if enabled:
            self.browseBtnFips.show()
            self.lineEditFips.show()
            self.browseBtnFips.setEnabled(True)
            self.lineEditFips.setEnabled(True)

    def getfilesFips(self):
        fileNameFips = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        fileNameEqWithBracketFips = str(fileNameFips).split(',')
        fileNameEqWitoutBracketFips = str(fileNameEqWithBracketFips).split('(')
        selectedFileNameFips = str(fileNameEqWitoutBracketFips).split(',')
        self.lineEditFips.setText(selectedFileNameFips[1])

    # Functions used for Moves Datafiles
    def radioButtonDatafilesDefaultClicked(self, enabled):
        if enabled:
            self.browseBtnDatafiles.hide()
            self.lineEditDatafiles.hide()
            self.browseBtnDatafiles.setEnabled(False)
            self.lineEditDatafiles.setEnabled(False)

    def radioButtonDatafilesCustomClicked(self, enabled):
        if enabled:
            self.browseBtnDatafiles.show()
            self.lineEditDatafiles.show()
            self.browseBtnDatafiles.setEnabled(True)
            self.lineEditDatafiles.setEnabled(True)

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
        self.windowLayout.setColumnStretch(3, 1)
        self.windowLayout.setColumnStretch(4, 1)

        self.tabNonroad.setLayout(self.windowLayout)

        # Created UI element Year - Nonroad
        self.labelYearNon = QLabel()
        self.labelYearNon.setText("Year")
        self.labelYearNon.setToolTip("Start year of Equipment")
        self.comboBoxYearNon = QComboBox(self)
        for i in range(2018, 1990, -1):
            self.number = i
            self.comboBoxYearNon.addItem(str(i))
        self.index = self.comboBoxYearNon.findText("2017")
        self.comboBoxYearNon.setCurrentIndex(self.index)
        self.labelYearNonErrorMsg = QLabel()
        self.labelYearNonErrorMsg.setText("")
        self.windowLayout.addWidget(self.labelYearNon, 2, 0)
        self.windowLayout.addWidget(self.comboBoxYearNon, 2, 1)
        self.windowLayout.addWidget(self.labelYearNonErrorMsg, 2, 2, 1, 2)
        # Check whether Moves year matches with Nonroad year
        self.comboBoxYearNon.currentIndexChanged.connect(self.handleItemPressed)


        # Created UI element Paths
        self.labelPathNon = QLabel()
        self.labelPathNon.setText("Paths")
        self.windowLayout.addWidget(self.labelPathNon, 3, 0)

        # Created UI element Nonroad Datafiles
        self.labelDatafilesNon = QLabel()
        self.labelDatafilesNon.setText("Nonroad Datafiles")
        self.labelDatafilesNon.setToolTip("Select NONROAD output folder")
        self.radioGroupDatafilesNon = QButtonGroup(self.windowLayout)
        self.radioVuttonDatafilesNonDefault = QRadioButton("Default")
        self.radioVuttonDatafilesNonDefault.setChecked(True)
        self.radioVuttonDatafilesNonDefault.toggled.connect(self.radioButtonDatafilesNonDefaultClicked)
        self.radioButtonDatafilesNonCustom = QRadioButton("Custom")
        self.radioButtonDatafilesNonCustom.toggled.connect(self.radioButtonDatafilesNonCustomClicked)
        self.radioGroupDatafilesNon.addButton(self.radioVuttonDatafilesNonDefault)
        self.radioGroupDatafilesNon.addButton(self.radioButtonDatafilesNonCustom)
        self.browseBtnDatafilesNon = QPushButton("Browse", self)
        self.browseBtnDatafilesNon.setEnabled(False)
        self.browseBtnDatafilesNon.hide()
        self.browseBtnDatafilesNon.clicked.connect(self.getfilesDatafilesNon)
        self.lineEditDatafilesNon = QLineEdit(self)
        self.lineEditDatafilesNon.setEnabled(False)
        self.lineEditDatafilesNon.hide()
        self.windowLayout.addWidget(self.labelDatafilesNon, 4, 0)
        self.windowLayout.addWidget(self.radioVuttonDatafilesNonDefault, 4, 1)
        self.windowLayout.addWidget(self.radioButtonDatafilesNonCustom, 4, 2)
        self.windowLayout.addWidget(self.browseBtnDatafilesNon, 4, 3)
        self.windowLayout.addWidget(self.lineEditDatafilesNon, 4, 4)

        # Created UI element Region FIPs Map Nonroad
        self.labelFipsNon = QLabel()
        self.labelFipsNon.setText("Region FIPs Map")
        self.labelFipsNon.setToolTip("Select Region FIPs Map (production region to Nonroad FIPS mapping) dataset")
        self.radioGroupFipsNon = QButtonGroup(self.windowLayout)
        self.radioVuttonFipsNonDefault = QRadioButton("Default")
        self.radioVuttonFipsNonDefault.setChecked(True)
        self.radioVuttonFipsNonDefault.toggled.connect(self.radioButtonFipsNonDefaultClicked)
        self.radioButtonFipsNonCustom = QRadioButton("Custom")
        self.radioButtonFipsNonCustom.toggled.connect(self.radioButtonFipsNonCustomClicked)
        self.radioGroupFipsNon.addButton(self.radioVuttonFipsNonDefault)
        self.radioGroupFipsNon.addButton(self.radioButtonFipsNonCustom)
        self.browseBtnFipsNon = QPushButton("Browse", self)
        self.browseBtnFipsNon.setEnabled(False)
        self.browseBtnFipsNon.hide()
        self.browseBtnFipsNon.clicked.connect(self.getfilesFipsNon)
        self.lineEditFipsNon = QLineEdit(self)
        self.lineEditFipsNon.setEnabled(False)
        self.lineEditFipsNon.hide()
        self.windowLayout.addWidget(self.labelFipsNon, 5, 0)
        self.windowLayout.addWidget(self.radioVuttonFipsNonDefault, 5, 1)
        self.windowLayout.addWidget(self.radioButtonFipsNonCustom, 5, 2)
        self.windowLayout.addWidget(self.browseBtnFipsNon, 5, 3)
        self.windowLayout.addWidget(self.lineEditFipsNon, 5, 4)


        # Created UI element Region Nonroad Irrigation
        self.labelNonIrrig = QLabel()
        self.labelNonIrrig.setText("Irrigation")
        self.labelNonIrrig.setToolTip("Select irrigation dataset")
        self.radioGroupNonIrrig = QButtonGroup(self.windowLayout)
        self.radioVuttonNonIrrigDefault = QRadioButton("Default")
        self.radioVuttonNonIrrigDefault.setChecked(True)
        self.radioVuttonNonIrrigDefault.toggled.connect(self.radioButtonNonIrrigDefaultClicked)
        self.radioButtonNonIrrigCustom = QRadioButton("Custom")
        self.radioButtonNonIrrigCustom.toggled.connect(self.radioButtonNonIrrigCustomClicked)
        self.radioGroupNonIrrig.addButton(self.radioVuttonNonIrrigDefault)
        self.radioGroupNonIrrig.addButton(self.radioButtonNonIrrigCustom)
        self.browseBtnNonIrrig = QPushButton("Browse", self)
        self.browseBtnNonIrrig.setEnabled(False)
        self.browseBtnNonIrrig.hide()
        self.browseBtnNonIrrig.clicked.connect(self.getfilesNonIrrig)
        self.lineEditNonIrrig = QLineEdit(self)
        self.lineEditNonIrrig.setEnabled(False)
        self.lineEditNonIrrig.hide()
        self.windowLayout.addWidget(self.labelNonIrrig, 6, 0)
        self.windowLayout.addWidget(self.radioVuttonNonIrrigDefault, 6, 1)
        self.windowLayout.addWidget(self.radioButtonNonIrrigCustom, 6, 2)
        self.windowLayout.addWidget(self.browseBtnNonIrrig, 6, 3)
        self.windowLayout.addWidget(self.lineEditNonIrrig, 6, 4)

        # Created UI element Region Nonroad Encode Names
        self.labelNonEncodeNames = QLabel()
        self.labelNonEncodeNames.setText("Encode Names")
        self.labelNonEncodeNames.setToolTip("Encode feedstock, tillage type and activity names")
        self.comboBoxEncodeNames = QComboBox(self)
        self.comboBoxEncodeNames.addItem("Yes")
        self.comboBoxEncodeNames.addItem("No")
        self.comboBoxEncodeNames.setCurrentText("Yes")
        self.windowLayout.addWidget(self.labelNonEncodeNames, 7, 0)
        self.windowLayout.addWidget(self.comboBoxEncodeNames, 7, 1)


        # Created UI element Feedstock Measure Type Nonroad
        self.labelFeedMeasureTypeNon = QLabel()
        self.labelFeedMeasureTypeNon.setText("Feedstock Measure Type")
        self.labelFeedMeasureTypeNon.setToolTip("Enter Feedstock Measure Type Identifier")
        self.lineEditFeedMeasureTypeNon = QLineEdit()
        self.regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(self.regex)
        self.lineEditFeedMeasureTypeNon.setValidator(validator)
        # Set Default text
        self.lineEditFeedMeasureTypeNon.setPlaceholderText("Harvested")
        self.windowLayout.addWidget(self.labelFeedMeasureTypeNon, 8, 0)
        self.windowLayout.addWidget(self.lineEditFeedMeasureTypeNon, 8, 1)

        # Created UI element Irrigation Feedstock Measure Type Nonroad
        self.labelFeedMeasureTypeIrrigNon = QLabel()
        self.labelFeedMeasureTypeIrrigNon.setText("Irrigation Feedstock Measure Type")
        self.labelFeedMeasureTypeIrrigNon.setToolTip("Productio table ow identifier for irrigation activity calculation")
        self.lineEditFeedMeasureTypeIrrigNon = QLineEdit()
        self.regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(self.regex)
        self.lineEditFeedMeasureTypeIrrigNon.setValidator(validator)
        self.lineEditFeedMeasureTypeIrrigNon.setPlaceholderText("Planted")
        self.windowLayout.addWidget(self.labelFeedMeasureTypeIrrigNon, 9, 0)
        self.windowLayout.addWidget(self.lineEditFeedMeasureTypeIrrigNon, 9, 1)

        # Created UI element Irrigation Feedstock Names
        self.labelIrrigationFeedNamesNon = QLabel()
        self.labelIrrigationFeedNamesNon.setText("Irrigation Feedstock Names")
        self.labelIrrigationFeedNamesNon.setToolTip("List of irrigated feedstocks")
        self.lineEditFeedIrrigNamesNon = QLineEdit()
        self.regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(self.regex)
        self.lineEditFeedIrrigNamesNon.setValidator(validator)
        self.lineEditFeedIrrigNamesNon.setPlaceholderText("Corn Garin")
        self.windowLayout.addWidget(self.labelIrrigationFeedNamesNon, 10, 0)
        self.windowLayout.addWidget(self.lineEditFeedIrrigNamesNon, 10, 1)

        # Created UI element Time Resource Name
        self.labelTimeResNamesNon = QLabel()
        self.labelTimeResNamesNon.setText("Time Resource Name")
        self.labelTimeResNamesNon.setToolTip("Equipment table row identifier")
        self.lineEditTimeResNamesNon = QLineEdit()
        self.regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(self.regex)
        self.lineEditTimeResNamesNon.setValidator(validator)
        self.lineEditTimeResNamesNon.setPlaceholderText("Time")
        self.windowLayout.addWidget(self.labelTimeResNamesNon, 11, 0)
        self.windowLayout.addWidget(self.lineEditTimeResNamesNon, 11, 1)


        # Created UI element Forestry Feedstock Names
        self.labelForestryNamesNon = QLabel()
        self.labelForestryNamesNon.setText("Forestry Feedstock Names")
        self.labelForestryNamesNon.setToolTip("Different allocation indicators of forest feedstocks")
        self.lineEditForestryNamesNon = QLineEdit(self)
        self.regex = QtCore.QRegExp("[a-z-A-Z_,]+")
        validator = QtGui.QRegExpValidator(self.regex)
        self.lineEditForestryNamesNon.setValidator(validator)
        self.lineEditForestryNamesNon.setPlaceholderText("forest residues, forest whole tree")
        self.windowLayout.addWidget(self.labelForestryNamesNon, 12, 0)
        self.windowLayout.addWidget(self.lineEditForestryNamesNon, 12, 1)

        # Created UI element Temperature
        self.labelTemper = QLabel()
        self.labelTemper.setText("Temperature")
        self.labelTemper.setToolTip("Enter temperature range for Nonroad")
        self.windowLayout.addWidget(self.labelTemper, 13, 0)

        # Created UI element Minimum Temperature
        self.labelMinTemp = QLabel()
        self.labelMinTemp.setText("Minimum")
        self.lineEditMinTemp = QLineEdit(self)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditMinTemp.setValidator(self.onlyFlaot)
        self.lineEditMinTemp.setPlaceholderText("50")
        self.windowLayout.addWidget(self.labelMinTemp, 14, 0)
        self.windowLayout.addWidget(self.lineEditMinTemp, 14, 1)

        # Created UI element Maximum Temperature
        self.labelMaxTemp = QLabel()
        self.labelMaxTemp.setText("Maximum")
        self.lineEditMaxTemp = QLineEdit()
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditMaxTemp.setValidator(self.onlyFlaot)
        self.lineEditMaxTemp.setPlaceholderText("68.8")
        self.windowLayout.addWidget(self.labelMaxTemp, 15, 0)
        self.windowLayout.addWidget(self.lineEditMaxTemp, 15, 1)

        # Created UI element Mean Temperature
        self.labelMeanTemp = QLabel()
        self.labelMeanTemp.setText("Mean")
        self.lineEditMeanTemp = QLineEdit(self)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditMeanTemp.setValidator(self.onlyFlaot)
        self.lineEditMeanTemp.setPlaceholderText("60")
        self.windowLayout.addWidget(self.labelMeanTemp, 16, 0)
        self.windowLayout.addWidget(self.lineEditMeanTemp, 16, 1)

        # Created UI element Diesel
        self.labelDiesel = QLabel()
        self.labelDiesel.setText("Diesel")
        self.windowLayout.addWidget(self.labelDiesel, 17, 0)

        # Created UI element Low Heating Value
        self.labelLowHeat = QLabel()
        self.labelLowHeat.setText("Low Heating Value")
        self.labelLowHeat.setToolTip("Lower heating value for diesel fuel")
        self.lineEditLowHeat = QLineEdit(self)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 6)
        self.lineEditLowHeat.setValidator(self.onlyFlaot)
        self.lineEditLowHeat.setPlaceholderText("0.012845")
        self.windowLayout.addWidget(self.labelLowHeat, 18, 0)
        self.windowLayout.addWidget(self.lineEditLowHeat, 18, 1)

        # Created UI element NH3 Emission Factor
        self.labelNH3 = QLabel()
        self.labelNH3.setText("NH3 Emission Factor")
        self.labelNH3.setToolTip("NH3 emissionn factor for diesel fuel")
        self.lineEditNH3 = QLineEdit(self)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 6)
        self.lineEditNH3.setValidator(self.onlyFlaot)
        self.lineEditNH3.setPlaceholderText("0.68")
        self.windowLayout.addWidget(self.labelNH3, 19, 0)
        self.windowLayout.addWidget(self.lineEditNH3, 19, 1)

        # Created UI element Hydrocarbon to VOC Conversion Factor
        self.labelHydeo = QLabel()
        self.labelHydeo.setText("Hydrocarbon to VOC Conversion Factor")
        self.labelHydeo.setToolTip("VOC conversion factor for Hydrocarbon Emission components")
        self.lineEditHydro = QLineEdit()
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 6)
        self.lineEditHydro.setValidator(self.onlyFlaot)
        self.lineEditHydro.setPlaceholderText("1.053")
        self.windowLayout.addWidget(self.labelHydeo, 20, 0)
        self.windowLayout.addWidget(self.lineEditHydro, 20, 1)

        # Created UI element PM10 to PM2.5 Conversion Factor
        self.labelPM10 = QLabel()
        self.labelPM10.setText("Hydrocarbon to VOC Conversion Factor")
        self.labelPM10.setToolTip("PM10 to PM2.5 conversion factor")
        self.lineEditPM10 = QLineEdit(self)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 6)
        self.lineEditPM10.setValidator(self.onlyFlaot)
        self.lineEditPM10.setPlaceholderText("0.97")
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
            fieldNames.append("Moves")

        if self.tabNonroad.isEnabled():
            fieldValues.add(self.comboBoxYearNon.currentText())
            fieldNames.append("Nonroad")

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
    def radioButtonDatafilesNonDefaultClicked(self, enabled):
        if enabled:
            self.browseBtnDatafilesNon.hide()
            self.lineEditDatafilesNon.hide()
            self.browseBtnDatafilesNon.setEnabled(False)
            self.lineEditDatafilesNon.setEnabled(False)

    def radioButtonDatafilesNonCustomClicked(self, enabled):
        if enabled:
            self.browseBtnDatafilesNon.show()
            self.lineEditDatafilesNon.show()
            self.browseBtnDatafilesNon.setEnabled(True)
            self.lineEditDatafilesNon.setEnabled(True)

    def getfilesDatafilesNon(self):
        fileName = QFileDialog.getExistingDirectory(self, "Browse")
        selectedFileName = str(fileName).split(',')
        self.lineEditDatafilesNon.setText(selectedFileName[0])

    # Functions used for Fips Nonroad
    def radioButtonFipsNonDefaultClicked(self, enabled):
        if enabled:
            self.browseBtnFipsNon.hide()
            self.lineEditFipsNon.hide()
            self.browseBtnFipsNon.setEnabled(False)
            self.lineEditFipsNon.setEnabled(False)

    def radioButtonFipsNonCustomClicked(self, enabled):
        if enabled:
            self.browseBtnFipsNon.show()
            self.lineEditFipsNon.show()
            self.browseBtnFipsNon.setEnabled(True)
            self.lineEditFipsNon.setEnabled(True)

    def getfilesFipsNon(self):
        fileNameFipsNon = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        fileNameEqWithBracketFipsNon = str(fileNameFipsNon).split(',')
        fileNameEqWitoutBracketFipsNon = str(fileNameEqWithBracketFipsNon).split('(')
        selectedFileNameFipsNon = str(fileNameEqWitoutBracketFipsNon).split(',')
        self.lineEditFipsNon.setText(selectedFileNameFipsNon[1])

    # Functions used for Nonroad Irrigation
    def radioButtonNonIrrigDefaultClicked(self, enabled):
        if enabled:
            self.browseBtnNonIrrig.hide()
            self.lineEditNonIrrig.hide()
            self.browseBtnNonIrrig.setEnabled(False)
            self.lineEditNonIrrig.setEnabled(False)

    def radioButtonNonIrrigCustomClicked(self, enabled):
        if enabled:
            self.browseBtnNonIrrig.show()
            self.lineEditNonIrrig.show()
            self.browseBtnNonIrrig.setEnabled(True)
            self.lineEditNonIrrig.setEnabled(True)

    def getfilesNonIrrig(self):
        fileNameNonEq = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        fileNameEqWithBracketNonEq = str(fileNameNonEq).split(',')
        fileNameEqWitoutBracketNonEq = str(fileNameEqWithBracketNonEq).split('(')
        selectedFileNameNonEq = str(fileNameEqWitoutBracketNonEq).split(',')
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
        self.windowLayout.setColumnStretch(3, 1)
        self.windowLayout.setColumnStretch(4, 1)

        self.tabEmissionFactors.setLayout(self.windowLayout)

        # Created UI element Feedstock Measure Type Emission Factors
        self.labelFeedMeasureTypeEF = QLabel()
        self.labelFeedMeasureTypeEF.setText("Feedstock Measure Type")
        self.labelFeedMeasureTypeEF.setToolTip("Production table Identifier")
        self.lineEditFeedMeasureTypeEF = QLineEdit()
        regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(regex)
        self.lineEditFeedMeasureTypeEF.setValidator(validator)
        self.lineEditFeedMeasureTypeEF.setPlaceholderText("Harvested")
        self.windowLayout.addWidget(self.labelFeedMeasureTypeEF, 2, 0)
        self.windowLayout.addWidget(self.lineEditFeedMeasureTypeEF, 2, 1)

        # Created UI element Emission Factors
        self.labelEmiFact = QLabel()
        self.labelEmiFact.setText("Emission Factors")
        self.labelEmiFact.setToolTip("Emission factors as lb pollutant per lb resource subtype")
        self.radioGroupEmiFact = QButtonGroup(self.windowLayout)
        self.radioVuttonEmiFactDefault = QRadioButton("Default")
        self.radioVuttonEmiFactDefault.setChecked(True)
        self.radioVuttonEmiFactDefault.toggled.connect(self.radioButtonEmiFactDefaultClicked)
        self.radioButtonEmiFactCustom = QRadioButton("Custom")
        self.radioButtonEmiFactCustom.toggled.connect(self.radioButtonEmiFactCustomClicked)
        self.radioGroupEmiFact.addButton(self.radioVuttonEmiFactDefault)
        self.radioGroupEmiFact.addButton(self.radioButtonEmiFactCustom)
        self.browseBtnEmiFact = QPushButton("Browse", self)
        self.browseBtnEmiFact.setEnabled(False)
        self.browseBtnEmiFact.hide()
        self.browseBtnEmiFact.clicked.connect(self.getfilesEmiFact)
        self.lineEditEmiFact = QLineEdit(self)
        self.lineEditEmiFact.setEnabled(False)
        self.lineEditEmiFact.hide()
        self.windowLayout.addWidget(self.labelEmiFact, 3, 0)
        self.windowLayout.addWidget(self.radioVuttonEmiFactDefault, 3, 1)
        self.windowLayout.addWidget(self.radioButtonEmiFactCustom, 3, 2)
        self.windowLayout.addWidget(self.browseBtnEmiFact, 3, 3)
        self.windowLayout.addWidget(self.lineEditEmiFact, 3, 4)

        # Created UI element Resource Distribution
        self.labelResDist = QLabel()
        self.labelResDist.setText("Resource Distribution")
        self.labelResDist.setToolTip("Resource subtype distribution for all resources")
        self.radioGroupResDist = QButtonGroup(self.windowLayout)
        self.radioVuttonResDistDefault = QRadioButton("Default")
        self.radioVuttonResDistDefault.setChecked(True)
        self.radioVuttonResDistDefault.toggled.connect(self.radioButtonResDistDefaultClicked)
        self.radioButtonResDistCustom = QRadioButton("Custom")
        self.radioButtonResDistCustom.toggled.connect(self.radioButtonResDistCustomClicked)
        self.radioGroupResDist.addButton(self.radioVuttonResDistDefault)
        self.radioGroupResDist.addButton(self.radioButtonResDistCustom)
        self.browseBtnReDist = QPushButton("Browse", self)
        self.browseBtnReDist.setEnabled(False)
        self.browseBtnReDist.hide()
        self.browseBtnReDist.clicked.connect(self.getfilesResDist)
        self.lineEditResDist = QLineEdit(self)
        self.lineEditResDist.setEnabled(False)
        self.lineEditResDist.hide()
        self.windowLayout.addWidget(self.labelResDist, 4, 0)
        self.windowLayout.addWidget(self.radioVuttonResDistDefault, 4, 1)
        self.windowLayout.addWidget(self.radioButtonResDistCustom, 4, 2)
        self.windowLayout.addWidget(self.browseBtnReDist, 4, 3)
        self.windowLayout.addWidget(self.lineEditResDist, 4, 4)

        # Add Empty PlainText
        self.emptyPlainText2 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText2, 5, 0)


    # Functions used for Emission Factors
    def radioButtonEmiFactDefaultClicked(self, enabled):
        if enabled:
            self.browseBtnEmiFact.hide()
            self.lineEditEmiFact.hide()
            self.browseBtnEmiFact.setEnabled(False)
            self.lineEditEmiFact.setEnabled(False)

    def radioButtonEmiFactCustomClicked(self, enabled):
        if enabled:
            self.browseBtnEmiFact.show()
            self.lineEditEmiFact.show()
            self.browseBtnEmiFact.setEnabled(True)
            self.lineEditEmiFact.setEnabled(True)

    def getfilesEmiFact(self):
        fileNameTruckCapa = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        fileNameEqWithBracketTruckCapa = str(fileNameTruckCapa).split(',')
        fileNameEqWitoutBracketTruckCapa = str(fileNameEqWithBracketTruckCapa).split('(')
        selectedFileNameTruckCapa = str(fileNameEqWitoutBracketTruckCapa).split(',')
        self.lineEditEmiFact.setText(selectedFileNameTruckCapa[1])

    # Functions used for Resource Distribution
    def radioButtonResDistDefaultClicked(self, enabled):
        if enabled:
            self.browseBtnReDist.hide()
            self.lineEditResDist.hide()
            self.browseBtnReDist.setEnabled(False)
            self.lineEditResDist.setEnabled(False)

    def radioButtonResDistCustomClicked(self, enabled):
        if enabled:
            self.browseBtnReDist.show()
            self.lineEditResDist.show()
            self.browseBtnReDist.setEnabled(True)
            self.lineEditResDist.setEnabled(True)

    def getfilesResDist(self):
        fileNameTruckCapa = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        fileNameEqWithBracketTruckCapa = str(fileNameTruckCapa).split(',')
        fileNameEqWitoutBracketTruckCapa = str(fileNameEqWithBracketTruckCapa).split('(')
        selectedFileNameTruckCapa = str(fileNameEqWitoutBracketTruckCapa).split(',')
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
        self.windowLayout.setColumnStretch(3, 1)
        self.windowLayout.setColumnStretch(4, 1)

        self.tabFugitiveDust.setLayout(self.windowLayout)


        # Created UI element Feedstock Measure Type - Fugitive Dust
        self.labelFeedMeasureTypeFD = QLabel()
        self.labelFeedMeasureTypeFD.setText("Feedstock Measure Type")
        self.labelFeedMeasureTypeFD.setToolTip("Production table identifier ")
        self.lineEditFeedMeasureTypeFD = QLineEdit(self)
        regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(regex)
        self.lineEditFeedMeasureTypeFD.setValidator(validator)
        self.lineEditFeedMeasureTypeFD.setPlaceholderText("Harvested")
        self.windowLayout.addWidget(self.labelFeedMeasureTypeFD, 2, 0)
        self.windowLayout.addWidget(self.lineEditFeedMeasureTypeFD, 2, 1)


        # Created UI element Emission Factors - Fugitive Dust
        self.labelEmiFactFD = QLabel()
        self.labelEmiFactFD.setText("Emission Factors")
        self.labelEmiFactFD.setToolTip("Pollutant emission factors for resources")
        self.radioGroupEmiFactFD = QButtonGroup(self.windowLayout)
        self.radioVuttonEmiFactFDDefault = QRadioButton("Default")
        self.radioVuttonEmiFactFDDefault.setChecked(True)
        self.radioVuttonEmiFactFDDefault.toggled.connect(self.radioButtonEmiFactFDDefaultClicked)
        self.radioButtonEmiFactFDCustom = QRadioButton("Custom")
        self.radioButtonEmiFactFDCustom.toggled.connect(self.radioButtonEmiFactFDCustomClicked)
        self.radioGroupEmiFactFD.addButton(self.radioVuttonEmiFactFDDefault)
        self.radioGroupEmiFactFD.addButton(self.radioButtonEmiFactFDCustom)
        self.browseBtnEmiFactFD = QPushButton("Browse", self)
        self.browseBtnEmiFactFD.setEnabled(False)
        self.browseBtnEmiFactFD.hide()
        self.browseBtnEmiFactFD.clicked.connect(self.getfilesEmiFactFD)
        self.lineEditEmiFactFD = QLineEdit(self)
        self.lineEditEmiFactFD.setEnabled(False)
        self.lineEditEmiFactFD.hide()
        self.windowLayout.addWidget(self.labelEmiFactFD, 3, 0)
        self.windowLayout.addWidget(self.radioVuttonEmiFactFDDefault, 3, 1)
        self.windowLayout.addWidget(self.radioButtonEmiFactFDCustom, 3, 2)
        self.windowLayout.addWidget(self.browseBtnEmiFactFD, 3, 3)
        self.windowLayout.addWidget(self.lineEditEmiFactFD, 3, 4)


        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 4, 0)


    # Functions used for Emission Factors - - Fugitive Dust
    def radioButtonEmiFactFDDefaultClicked(self, enabled):
        if enabled:
            self.browseBtnEmiFactFD.hide()
            self.lineEditEmiFactFD.hide()
            self.browseBtnEmiFactFD.setEnabled(False)
            self.lineEditEmiFactFD.setEnabled(False)

    def radioButtonEmiFactFDCustomClicked(self, enabled):
        if enabled:
            self.browseBtnEmiFactFD.show()
            self.lineEditEmiFactFD.show()
            self.browseBtnEmiFactFD.setEnabled(True)
            self.lineEditEmiFactFD.setEnabled(True)

    def getfilesEmiFactFD(self):
        fileNameTruckCapaFD = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        fileNameEqWithBracketTruckCapaFD = str(fileNameTruckCapaFD).split(',')
        fileNameEqWitoutBracketTruckCapaFD = str(fileNameEqWithBracketTruckCapaFD).split('(')
        selectedFileNameTruckCapaFD = str(fileNameEqWitoutBracketTruckCapaFD).split(',')
        self.lineEditEmiFactFD.setText(selectedFileNameTruckCapaFD[1])



    # Run Button
    def runTheSelectedModules(self):

        attributeValueObj = AttributeValueStorage()

        tmpFolder = tempfile.mkdtemp()

        # check if scenario name and project path is entered or not
        if self.lineEditProjectPath.text() == "":
            self.lineEditProjectPath.setStyleSheet("border: 2px solid red;")
        else:
            self.lineEditProjectPath.setStyleSheet("border: 1px solid black;")

        if self.lineEditScenaName.text() == "":
            self.lineEditScenaName.setStyleSheet("border: 2px solid red;")
        else:
            self.lineEditScenaName.setStyleSheet("border: 1px solid black;")


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

        #attributeValueObj.module = self.selected_module_list

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

        if self.radioButtonEqCustom.isChecked():
            attributeValueObj.equipment = self.lineEditEq.text().strip()

        if self.radioButtonProdCustom.isChecked():
            attributeValueObj.production = self.lineEditProd.text().strip()

        if self.radioButtonFedLossFactCustom.isChecked():
            attributeValueObj.feedstockLossFactors = self.lineEditFedLossFact.text().strip()

        if self.radioButtonTransGraphCustom.isChecked():
            attributeValueObj.transportationGraph = self.lineEditTransGraph.text().strip()

        if self.radioButtonCountyNodeCustom.isChecked():
            attributeValueObj.countyNodes = self.lineEditCountyNode.text().strip()

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

        if self.radioButtonMovesPathCustom.isChecked():
            attributeValueObj.movesPath = self.lineEditMovesPath.text().strip()

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

        if self.radioButtonTruckCapaCustom.isChecked():
            attributeValueObj.truckCapacity = self.lineEditTruckCapa.text().strip()

        if self.radioButtonAVFTCustom.isChecked():
            attributeValueObj.avft = self.lineEditAVFT.text().strip()

        if self.radioButtonFipsCustom.isChecked():
            attributeValueObj.regionFipsMapMoves = self.lineEditFips.text().strip()

        if self.radioButtonDatafilesCustom.isChecked():
            attributeValueObj.movesDatafilesPath = self.lineEditDatafiles.text().strip()

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

        if self.radioButtonFipsNonCustom.isChecked():
            attributeValueObj.regionFipsMapNonroad = self.lineEditFipsNon.text().strip()

        if self.radioButtonDatafilesNonCustom.isChecked():
            attributeValueObj.nonroadDatafilesPath = self.lineEditDatafilesNon.text().strip()

        if self.radioButtonNonIrrigCustom.isChecked():
            attributeValueObj.irrigation = self.lineEditNonIrrig.text().strip()












        ###############################################################################################################

        # Emission Factors attributs value Initialization

        changedFeedMeasureTypeFEF= self.lineEditFeedMeasureTypeEF.text().strip()
        if changedFeedMeasureTypeFEF:
            attributeValueObj.feedMeasureTypeEF = changedFeedMeasureTypeFEF

        if self.radioButtonEmiFactCustom.isChecked():
            attributeValueObj.emissionFactorsEF = self.lineEditEmiFact.text().strip()
        if self.radioButtonResDistCustom.isChecked():
            attributeValueObj.resourceDistributionEF = self.lineEditResDist.text().strip()

        ###############################################################################################################

        # Fugititve Dust attributes value initialization

        changedFeedMeasureTypeFD = self.lineEditFeedMeasureTypeFD.text().strip()
        if changedFeedMeasureTypeFD:
            attributeValueObj.feedMeasureTypeFD = changedFeedMeasureTypeFD

        if self.radioButtonEmiFactFDCustom.isChecked():
            attributeValueObj.emissionFactorsFD = self.lineEditEmiFactFD.text().strip()

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
        t = threading.Thread(target= runCommand , args = (runConfigObj , emissionFactorsConfigCreationObj, ))
        t.start()

        while t.is_alive():
            print("alive. Waiting for 1 second to recheck")
            time.sleep(1)

        t.join()



    #########################################################################################################################



    def setupUIResult(self):
        # Result tab created
        self.tabResult = QtWidgets.QWidget()

        # Result tab added
        self.centralwidget.addTab(self.tabResult, "RESULT")

        # Result code start
        self.windowLayout = QGridLayout()
        self.windowLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)

        self.windowLayout.setColumnStretch(3, 1)
        self.windowLayout.setColumnStretch(4, 1)

        self.tabResult.setLayout(self.windowLayout)


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

def runCommand(runConfigObj , emissionFactorsConfigCreationObj):
    #runModuleCommand = "fpeam " + runConfigObj + " --emissionfactors_config " + emissionFactorsConfigCreationObj

    # runModuleCommad = command
    #
    # process = subprocess.Popen(runModuleCommad, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #
    # while process.poll():
    #     print("running")
    #     time.sleep(1)
    # output, error = process.communicate()
    # print("--------------")
    #
    # print("Output" + str(output, "utf-8") + "\n" + "Error" + str(error, "utf-8"))

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

##############################################################################################


# Merge config files

# def ParseThis(file1, file2):
#     parser = ConfigParser()
#     parser.read(file1)
#
#     for option in parser.options(file2):
#         print("\t" + option)
#         try:
#             if parser.get(file2, option) != 'None':
#                 print(option + ": " + parser.get(file2, option))
#             else:
#                 print(option + ": Option doesn't exist")
#         except:
#             print(option + ": Something went wrong")

# print "First File:"
# print "Section 1"
# ParseThis('emmissionfactors.ini', 'run_config.ini')

#
# print "\n"
# print "Second File: "
# print "Section 1"
# ParseThis('test1.ini', 'Section 1')
#
# print "\n"
# print "First File: "
# print "Section 1"
# ParseThis('runConfig.ini', 'fugitiveDustConfig.ini')
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