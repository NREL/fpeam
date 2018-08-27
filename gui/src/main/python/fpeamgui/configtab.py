from PyQt5 import QtCore
from PyQt5.QtWidgets import QGroupBox, QFrame, QSplitter, QScrollArea, QFormLayout, QHBoxLayout, QListWidget, \
    QWidget, QVBoxLayout, QLabel, QLineEdit, QRadioButton, QButtonGroup, QTableWidget, QTableWidgetItem, QFileDialog, \
    QPushButton
import functools
import configobj
import validate
import qtawesome as qta
import csv
from six import unichr


class ConfigTab(QWidget):
    def __init__(self, parent, config, config_tooltip):
        self.default_config = config
        self.default_config_tooltips = config_tooltip

        validator = validate.Validator()
        config = self.default_config.validate(validator)

        super(QWidget, self).__init__(parent)
        vbox = QVBoxLayout(self)

        hbox = QHBoxLayout()

        topleft = QFrame()
        topleft.setFrameShape(QFrame.StyledPanel)
        bottom = QFrame()
        bottom.setFrameShape(QFrame.StyledPanel)

        self.splitter = QSplitter(QtCore.Qt.Horizontal)

        listWidget = QListWidget()

        if 'voc_content_percent' in self.default_config.keys():
            default_config = self.default_config['chemical']
            self.default_config = {}
            self.default_config['chemical'] = default_config

        for k, v in self.default_config.items():
            listWidget.addItem(str(k))

        listWidget.itemClicked.connect(self.create_forms)

        self.splitter.addWidget(listWidget)

        hbox.addWidget(self.splitter)

        vbox.addLayout(hbox)

    def create_forms(self, key):

        # Before adding the new form to to the splitter we need to first remove any existing form
        existing_form = self.splitter.widget(1)

        if existing_form != None:
            existing_form.hide()
            existing_form.deleteLater()

        self.current_parent_param = key.text()

        current_form = QGroupBox()

        if self.current_parent_param in self.default_config_tooltips.keys():
            header = QLabel(self.current_parent_param + ' ' + unichr(0xf059))
            header.setFont(qta.font('fa', 14))
            # header.setText(self.current_parent_param)
            tooltip_text = self.default_config_tooltips[self.current_parent_param]
            header.setToolTip("<FONT COLOR=black>"+tooltip_text+"</FONT>")
        else:
            header = QLabel()
            header.setText(self.current_parent_param)

        layout = QFormLayout()
        header.setAlignment(QtCore.Qt.AlignCenter)

        layout.addWidget(header)

        layout.FieldGrowthPolicy(2)

        if self.current_parent_param == 'age_distribution':
            load_age_dist_file = QPushButton("Load Age Distribution File")

            layout.addRow(load_age_dist_file)

            self.age_dist_table = QTableWidget()

            self.age_dist_table.hide()
            layout.addRow(self.age_dist_table)

            load_age_dist_file.clicked.connect(functools.partial(self.load_age_dist, self.age_dist_table))


        else:
            for k, v in self.default_config[self.current_parent_param].items():
                try:
                    tooltip_text = self.default_config_tooltips[k]
                    label = QLabel(k + ' ' + unichr(0xf059))
                    label.setFont(qta.font('fa', 14))
                    label.setToolTip("<FONT COLOR=black>"+tooltip_text+"</FONT>")
                except Exception:
                    label = k

                if isinstance(v, bool):
                    radio_btn_layout = QHBoxLayout()

                    line_edit = QButtonGroup(radio_btn_layout)

                    b1 = QRadioButton("True")
                    b1.toggled.connect(functools.partial(self.btnstate, k, b1))
                    line_edit.addButton(b1)

                    b2 = QRadioButton("False")
                    b2.toggled.connect(functools.partial(self.btnstate, k, b2))
                    line_edit.addButton(b2)

                    if v is True:
                        b1.setChecked(True)
                        b2.setChecked(False)
                    else:
                        b1.setChecked(False)
                        b2.setChecked(True)

                    radio_btn_layout.addWidget(b1)
                    radio_btn_layout.addWidget(b2)

                    layout.addRow(label, radio_btn_layout)

                elif isinstance(v, list) and k != 'modules':
                    tableWidget = QTableWidget()

                    # set row count
                    tableWidget.setRowCount(len(v))

                    # set column count
                    tableWidget.setColumnCount(1)

                    tableWidget.setHorizontalHeaderLabels(['fraction'])

                    for idx, el in enumerate(v):
                        tableWidget.setItem(0, idx, QTableWidgetItem(str(el)))

                    layout.addRow(label, tableWidget)

                elif isinstance(v, str):

                    if 'binary' in k:
                        binary_browser_layout = QHBoxLayout()

                        selected_binary = QLineEdit(str(v))

                        file_browser = QPushButton("Browse Binary")
                        file_browser.clicked.connect(functools.partial(self.get_file_path, k, selected_binary))

                        binary_browser_layout.addWidget(selected_binary)
                        binary_browser_layout.addWidget(file_browser)

                        layout.addRow(label, binary_browser_layout)

                    else:
                        line_edit = QLineEdit(str(v))
                        line_edit.setFixedWidth(200)

                        line_edit.textChanged.connect(functools.partial(self.on_field_change, k, line_edit))

                        layout.addRow(label, line_edit)

                else:
                    line_edit = QLineEdit(str(v))

                    line_edit.textChanged.connect(functools.partial(self.on_field_change, k, line_edit))

                    layout.addRow(label, line_edit)

        current_form.setLayout(layout)
        current_form_scrollable = QScrollArea()
        current_form_scrollable.setWidget(current_form)
        current_form_scrollable.setWidgetResizable(True)

        self.splitter.addWidget(current_form_scrollable)

    def on_field_change(self, label, value):
        self.default_config[self.current_parent_param][label] = value.text()

    def btnstate(self, label, value):
        self.default_config[self.current_parent_param][label] = value.text()

    def get_file_path(self, label, selected_binary_field, i):
        name = QFileDialog.getOpenFileName(self, 'Open File')[0]
        selected_binary_field.setText(name)
        self.default_config[self.current_parent_param][label] = name

    def load_age_dist(self, age_dist_table):
        name = QFileDialog.getOpenFileName(self, 'Open File')[0]
        if name:
            with open(name) as in_file:
                reader = csv.reader(in_file)
                data = [r for r in reader]
                rows = len(data)

                age_dist_table.setRowCount(rows)
                age_dist_table.setColumnCount(1)
                age_dist_table.setHorizontalHeaderLabels(['fraction'])

                for idx, el in enumerate(data):
                    print(idx, el[0])
                    age_dist_table.setItem(0, idx, QTableWidgetItem(str(el[0])))

                age_dist_table.show()