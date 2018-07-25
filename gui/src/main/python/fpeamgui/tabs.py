from PyQt5.QtWidgets import QFileDialog, QPushButton, QWidget, QTabWidget,QVBoxLayout

import functools
from configobj import ConfigObj

from fpeamgui.configtab import ConfigTab

class Tabs(QWidget):

    def __init__(self, parent, configs):
        super(QWidget, self).__init__(parent)
        layout = QVBoxLayout(self)

        # Initialize tab screen
        tabs = QTabWidget()

        # Add tabs
        self.fpeam_tab = ConfigTab(parent, 
                                    configs['fpeam']['fpeam_config'], 
                                    configs['fpeam']['fpeam_tooltips'])
        tabs.addTab(self.fpeam_tab, "FPEAM Config")

        self.moves_tab = ConfigTab(parent, 
                                    configs['moves']['moves_config'], 
                                    configs['moves']['moves_tooltips'])
        tabs.addTab(self.moves_tab ,"MOVES Config")

        self.chemical_tab = ConfigTab(parent, 
                                    configs['chemical']['chemical_config'], 
                                    configs['chemical']['chemical_tooltips'])
        tabs.addTab(self.chemical_tab, "chemical Config")

        self.nonroad_tab = ConfigTab(parent, 
                                    configs['nonroad']['nonroad_config'], 
                                    configs['nonroad']['nonroad_tooltips'])
        tabs.addTab(self.nonroad_tab, "nonroad Config")

        self.fugitivedust_tab = ConfigTab(parent, 
                                    configs['fugitivedust']['fugitivedust_config'], 
                                    configs['fugitivedust']['fugitivedust_tooltips'])
        tabs.addTab(self.fugitivedust_tab, "fugitivedust Config")

        # # Add tabs to widget
        layout.addWidget(tabs)
        # parent.setLayout(self.layout)

        createConfigBtn = QPushButton("Generate Config")
        createConfigBtn.clicked.connect(functools.partial(self.prepare_config))

        layout.addWidget(createConfigBtn)

    def prepare_config(self):
        config = ConfigObj()

        fpeam_config = self.fpeam_tab.default_config
        moves_config = self.moves_tab.default_config
        chemical_config = self.chemical_tab.default_config
        nonroad_config = self.nonroad_tab.default_config

        for s in fpeam_config.keys():
            config[s] = {}

            for k, v in fpeam_config[s].items():
                config[s][k] = v

        for s in moves_config.keys():
            config[s] = {}

            for k, v in moves_config[s].items():
                config[s][k] = v

        for s in chemical_config.keys():
            config[s] = {}

            for k, v in chemical_config[s].items():
                config[s][k] = v

        for s in nonroad_config.keys():
            config[s] = {}

            for k, v in nonroad_config.items():
                config[s][k] = v

        name = QFileDialog.getSaveFileName(self, 'Save File')[0]
        if name:
            config.filename = name
            config.write()
