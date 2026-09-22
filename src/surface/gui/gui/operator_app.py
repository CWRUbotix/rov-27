from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QTabWidget, QVBoxLayout, QWidget

from gui.app import App
from gui.widgets.float_comm import FloatComm
from gui.widgets.flood_warning import FloodWarning
from gui.widgets.heartbeat import HeartbeatWidget
from gui.widgets.ip_widget import IPWidget
from gui.widgets.logger import Logger
from gui.widgets.tabs.general_debug_tab import GeneralDebugTab
from gui.widgets.temperature import TemperatureSensor
from gui.widgets.timer import InteractiveTimer


class OperatorApp(App):
    changed_tabs = pyqtSignal(int)

    def __init__(self) -> None:
        super().__init__('operator_gui_node')

        self.setWindowTitle('Operator GUI - CWRUbotix ROV 2025')

        # Main tab
        main_tab = QWidget()
        main_layout = QHBoxLayout()
        main_tab.setLayout(main_layout)

        left_pane = QVBoxLayout()
        right_pane = QVBoxLayout()

        main_layout.addLayout(left_pane)
        main_layout.addLayout(right_pane)

        self.float_comm: FloatComm = FloatComm()
        left_pane.addWidget(self.float_comm)

        logger = Logger()
        left_pane.addWidget(logger)

        right_pane.addWidget(InteractiveTimer())
        right_pane.addWidget(HeartbeatWidget())
        right_pane.addWidget(FloodWarning())
        right_pane.addWidget(TemperatureSensor())
        right_pane.addWidget(IPWidget())
        right_pane.addStretch()

        # Add tabs to root
        root_layout = QVBoxLayout()
        self.setLayout(root_layout)

        self.tabs = QTabWidget()
        self.tabs.addTab(main_tab, 'Main')
        self.tabs.addTab(GeneralDebugTab(), 'General Debug')
        self.tabs.currentChanged.connect(self.changed_tabs)
        root_layout.addWidget(self.tabs)


def run_gui_operator() -> None:
    OperatorApp().run_gui()
