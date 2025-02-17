#! python3  # noqa: E265

"""
    Plugin dialog.
"""

# PyQGIS
from qgis.core import QgsMapLayerProxyModel
from qgis.gui import QgsFieldComboBox, QgsMapLayerComboBox
from qgis.PyQt.Qt import QUrl
from qgis.PyQt.QtCore import QSize, QThread, pyqtSignal
from qgis.PyQt.QtGui import QDesktopServices, QIcon, QPixmap
from qgis.PyQt.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

# project
from taxref_collector.__about__ import (
    __service_credit_col__,
    __service_credit_gbif__,
    __service_credit_inpn__,
    __service_logo_col__,
    __service_logo_gbif__,
    __service_logo_inpn__,
    __service_metadata__,
    __title__,
    __uri_homepage__,
)

# ############################################################################
# ########## Classes ###############
# ##################################


class TaxrefCollectorDialog(QDialog):
    def __init__(self, project=None, iface=None, manager=None):
        """Constructor.
        :param
        project: The current QGIS project instance
        iface: An interface instance that will be passed to this class which \
        provides the hook by which you can manipulate the QGIS application \
        at run time.
        """
        super(TaxrefCollectorDialog, self).__init__()
        self.setObjectName(__title__)

        self.iface = iface
        self.project = project
        self.manager = manager
        self.canvas = self.iface.mapCanvas()

        self.layer = None
        self.rectangle = None

        self.setWindowTitle(__title__)

        self.layout = QVBoxLayout()

        # Source and credit
        self.source_doc_layout = QGridLayout()
        credit_label = QLabel(self)
        credit_label.setText(self.tr("Data provided by :"))
        self.layout.addWidget(credit_label)

        pixmap = QPixmap(str(__service_logo_gbif__))
        self.producer_gbif_label = QToolButton(self)
        self.producer_gbif_label.setObjectName(__service_credit_gbif__)
        icon = QIcon()
        icon.addPixmap(pixmap)
        self.producer_gbif_label.setIcon(icon)
        self.producer_gbif_label.setIconSize(QSize(60, 60))
        self.source_doc_layout.addWidget(self.producer_gbif_label, 0, 0, 3, 3)
        pixmap = QPixmap(str(__service_logo_col__))
        self.producer_col_label = QToolButton(self)
        self.producer_col_label.setObjectName(__service_credit_col__)
        icon = QIcon()
        icon.addPixmap(pixmap)
        self.producer_col_label.setIcon(icon)
        self.producer_col_label.setIconSize(QSize(60, 60))
        self.source_doc_layout.addWidget(self.producer_col_label, 0, 1, 3, 3)
        pixmap = QPixmap(str(__service_logo_inpn__))
        self.producer_inpn_label = QToolButton(self)
        self.producer_inpn_label.setObjectName(__service_credit_inpn__)
        icon = QIcon()
        icon.addPixmap(pixmap)
        self.producer_inpn_label.setIcon(icon)
        self.producer_inpn_label.setIconSize(QSize(60, 60))
        self.source_doc_layout.addWidget(self.producer_inpn_label, 0, 2, 3, 3)

        widget = QWidget()
        self.doc_layout = QVBoxLayout()
        self.documentation_button = QPushButton(self)
        self.documentation_button.setObjectName(__uri_homepage__)
        self.documentation_button.setText(self.tr("Documentation"))
        self.doc_layout.addWidget(self.documentation_button)

        self.doc_layout.addStretch()

        self.metadata_button = QPushButton(self)
        self.metadata_button.setObjectName(__service_metadata__)
        self.metadata_button.setText(self.tr("Metadata"))
        self.doc_layout.addWidget(self.metadata_button)
        widget.setLayout(self.doc_layout)
        self.source_doc_layout.addWidget(widget, 0, 3, 1, -1)

        self.layout.addLayout(self.source_doc_layout)
        self.layout.insertSpacing(100, 25)

        # Select layer tool
        select_layer_label = QLabel(self)
        select_layer_label.setText(self.tr("Select a layer with data species"))
        self.layout.addWidget(select_layer_label)
        self.select_layer_combo_box = QgsMapLayerComboBox(self)
        self.select_layer_combo_box.setFilters(
            QgsMapLayerProxyModel.PolygonLayer
            | QgsMapLayerProxyModel.LineLayer
            | QgsMapLayerProxyModel.PointLayer
        )
        self.select_layer_combo_box.setAllowEmptyLayer(False)
        self.layout.addWidget(self.select_layer_combo_box)
        self.layout.insertSpacing(100, 25)

        # Choose reference database
        database_check_group = QButtonGroup(self)
        database_check_group.setExclusive(True)
        self.gbif_checkbox = QCheckBox(self)
        self.gbif_checkbox.setText(
            self.tr("Use GBIF id as reference to get TAXREF id:")
        )
        self.gbif_checkbox.setChecked(True)
        database_check_group.addButton(self.gbif_checkbox, 0)
        self.clb_checkbox = QCheckBox(self)
        self.clb_checkbox.setText(
            self.tr("Use scientific name as reference to get TAXREF id:")
        )
        self.clb_checkbox.setChecked(False)
        database_check_group.addButton(self.clb_checkbox, 1)
        self.layout.addWidget(self.gbif_checkbox)
        self.layout.addWidget(self.clb_checkbox)

        # Chosse field containing link to reference database
        self.stack = QStackedWidget()
        gbif_page = QWidget()
        gbif_layout = QVBoxLayout()
        select_field_gbif_label = QLabel(self)
        select_field_gbif_label.setText(
            self.tr("Select a field containing data reference")
        )
        gbif_layout.addWidget(select_field_gbif_label)
        self.select_field_gbif_combo_box = QgsFieldComboBox(self)
        self.select_field_gbif_combo_box.setAllowEmptyFieldName(False)
        if self.select_layer_combo_box.currentLayer():
            self.select_field_gbif_combo_box.setLayer(
                self.select_layer_combo_box.currentLayer()
            )
        self.select_layer_combo_box.layerChanged.connect(
            lambda: self.select_field_gbif_combo_box.setLayer(
                self.select_layer_combo_box.currentLayer()
            )
        )
        gbif_layout.addWidget(self.select_field_gbif_combo_box)
        gbif_page.setLayout(gbif_layout)

        clb_page = QWidget()
        clb_layout = QVBoxLayout()
        select_field_name_label = QLabel(self)
        select_field_name_label.setText(
            self.tr("Select a field containing species name")
        )
        clb_layout.addWidget(select_field_name_label)
        self.select_field_name_combo_box = QgsFieldComboBox(self)
        self.select_field_name_combo_box.setAllowEmptyFieldName(False)
        if self.select_layer_combo_box.currentLayer():
            self.select_field_name_combo_box.setLayer(
                self.select_layer_combo_box.currentLayer()
            )
        self.select_layer_combo_box.layerChanged.connect(
            lambda: self.select_field_name_combo_box.setLayer(
                self.select_layer_combo_box.currentLayer()
            )
        )
        clb_layout.addWidget(self.select_field_name_combo_box)
        select_field_rank_label = QLabel(self)
        select_field_rank_label.setText(
            self.tr("Select a field containing rank of observation")
        )
        clb_layout.addWidget(select_field_rank_label)
        self.select_field_rank_combo_box = QgsFieldComboBox(self)
        self.select_field_rank_combo_box.setAllowEmptyFieldName(True)
        if self.select_layer_combo_box.currentLayer():
            self.select_field_rank_combo_box.setLayer(
                self.select_layer_combo_box.currentLayer()
            )
        self.select_layer_combo_box.layerChanged.connect(
            lambda: self.select_field_rank_combo_box.setLayer(
                self.select_layer_combo_box.currentLayer()
            )
        )
        clb_layout.addWidget(self.select_field_rank_combo_box)
        clb_page.setLayout(clb_layout)

        self.stack.addWidget(gbif_page)
        self.stack.addWidget(clb_page)
        self.layout.addWidget(self.stack)
        self.layout.insertSpacing(100, 25)

        # Accept and reject button box
        self.button_box = QDialogButtonBox(self)
        self.button_box.setEnabled(False)
        self.button_box.addButton(self.tr("Ok"), QDialogButtonBox.AcceptRole)
        self.button_box.addButton(self.tr("Cancel"), QDialogButtonBox.RejectRole)
        self.layout.addWidget(self.button_box)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # Progress Bar
        self.select_progress_bar_label = QLabel(self)
        self.select_progress_bar_label.setText("")
        self.layout.addWidget(self.select_progress_bar_label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.thread = Thread()
        self.thread._signal.connect(self.signal_accept)
        self.layout.addWidget(self.progress_bar)

        # Add layout
        self.setLayout(self.layout)

        # Ui signals
        self.producer_gbif_label.clicked.connect(self.open_url)
        self.producer_col_label.clicked.connect(self.open_url)
        self.producer_inpn_label.clicked.connect(self.open_url)
        self.metadata_button.clicked.connect(self.open_url)
        self.documentation_button.clicked.connect(self.open_url)
        self.select_layer_combo_box.layerChanged.connect(self.check_valid)
        database_check_group.buttonClicked.connect(
            lambda: self.stack.setCurrentIndex(database_check_group.checkedId())
        )

        self.check_valid()

    def check_valid(self):
        if self.select_layer_combo_box.currentLayer():
            if self.select_layer_combo_box.currentLayer().fields().count() > 0:
                self.button_box.setEnabled(True)
            else:
                self.button_box.setEnabled(False)
        else:
            self.button_box.setEnabled(False)

    def open_url(self):
        # Function to open the url of the buttons
        url = QUrl(self.sender().objectName())
        QDesktopServices.openUrl(url)

    def signal_accept(self, msg):
        # Update the progress bar when result is pressed
        self.progress_bar.setValue(int(msg))
        if self.progress_bar.value() == 101:
            self.progress_bar.setValue(0)

    def activate_window(self):
        # Put the dialog on top once the rectangle is drawn
        self.showNormal()
        self.activateWindow()


class Thread(QThread):
    """Thread used fot the ProgressBar"""

    _signal = pyqtSignal(int)

    def __init__(self):
        super(Thread, self).__init__()
        self.max_value = 1
        self.value = 0

    def __del__(self):
        self.wait()

    def set_max(self, max_value):
        self.max_value = max_value

    def add_one(self, to_add):
        self.value = self.value + to_add
        self._signal.emit(int((self.value / self.max_value) * 100))

    def finish(self):
        self._signal.emit(101)

    def reset_value(self):
        self.value = 0
