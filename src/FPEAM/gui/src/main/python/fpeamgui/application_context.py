import sys
from fbs_runtime.application_context import ApplicationContext, cached_property

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QSize

import configobj
import validate

from fpeamgui.tabs import Tabs

class AppContext(ApplicationContext):
    def run(self):
        self.main_window.show()
        return self.app.exec_()

    @cached_property
    def main_window(self):
        result = QMainWindow()
        result.setMinimumSize(QSize(780, 500))
        result.setWindowTitle('FPEAM')

        configs = self.configs

        table_widget = Tabs(result, configs)
        result.setCentralWidget(table_widget)

        return result

    @cached_property
    def configs(self):
        validator = validate.Validator()

        fpeam_config = configobj.ConfigObj(self.get_resource('fpeam.ini'), configspec=self.get_resource('fpeam.spec'))
        fpeam_tooltips = configobj.ConfigObj(self.get_resource('fpeam_tooltips.ini'))
        config = fpeam_config.validate(validator)

        moves_config = configobj.ConfigObj(self.get_resource('moves.ini'), configspec=self.get_resource('moves.spec'))
        moves_tooltips = configobj.ConfigObj(self.get_resource('moves_tooltips.ini'))
        config = moves_config.validate(validator)

        chemical_config = configobj.ConfigObj(self.get_resource('chemical.ini'), configspec=self.get_resource('chemical.spec'))
        chemical_tooltips = configobj.ConfigObj(self.get_resource('chemical_tooltips.ini'))
        config = chemical_config.validate(validator)

        nonroad_config = configobj.ConfigObj(self.get_resource('nonroad.ini'), configspec=self.get_resource('nonroad.spec'))
        nonroad_tooltips = configobj.ConfigObj(self.get_resource('nonroad_tooltips.ini'))
        config = nonroad_config.validate(validator)

        fugitivedust_config = configobj.ConfigObj(self.get_resource('fugitivedust.ini'), configspec=self.get_resource('fugitivedust.spec'))
        fugitivedust_tooltips = configobj.ConfigObj(self.get_resource('fugitivedust_tooltips.ini'))
        config = fugitivedust_config.validate(validator)

        configs_dict = {'moves': {'moves_config': moves_config, 'moves_tooltips': moves_tooltips},
                        'chemical': {'chemical_config': chemical_config, 'chemical_tooltips': chemical_tooltips},
                        'fpeam': {'fpeam_config': fpeam_config, 'fpeam_tooltips': fpeam_tooltips},
                        'nonroad': {'nonroad_config': nonroad_config, 'nonroad_tooltips': nonroad_tooltips},
                        'fugitivedust': {'fugitivedust_config': fugitivedust_config, 'fugitivedust_tooltips': fugitivedust_tooltips} 
                        }

        return configs_dict