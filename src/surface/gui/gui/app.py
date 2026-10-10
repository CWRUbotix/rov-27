import atexit
import signal
from pathlib import Path
from threading import Thread

import rclpy.utilities
from ament_index_python import get_package_share_directory
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QApplication, QWidget
from qt_material import apply_stylesheet
from rclpy.duration import Duration
from rclpy.executors import MultiThreadedExecutor

from gui.gui_node import GUINode
from gui.widgets.timer import InteractiveTimer
from rov_msgs.srv import MissionTimerSet

RESET_SECONDS = 15 * 60  # The number of seconds to set the timer to when reset is clicked


class App(QWidget):
    """Main app window."""

    app = QApplication([])
    set_timer_response_signal: pyqtSignal = pyqtSignal(MissionTimerSet.Response)

    def __init__(self, node_name: str) -> None:
        if not rclpy.utilities.ok():
            rclpy.init()
        super().__init__()
        self.node = GUINode(node_name)

        self.theme_param = self.node.declare_parameter('theme', '')
        self.resize(1850, 720)

        atexit.register(self._clean_shutdown)

        # Added stuff
        self.set_timer_client = GUINode().create_client_multithreaded(
            MissionTimerSet, 'set_mission_timer'
        )

        self.timer = InteractiveTimer()

        self.shortcut1 = QShortcut(QKeySequence('Ctrl+T'), self)
        self.shortcut1.activated.connect(self.timer.toggle_timer)

        self.shortcut2 = QShortcut(QKeySequence('Ctrl+R'), self)
        self.shortcut2.activated.connect(self.reset_timer)

        self.running = False

    def run_gui(self) -> None:
        # Kills with Control + C
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        extra_blue = {'success': '#040444', 'danger': '#040444', 'warning': '#040444'}
        extra_watermelon = {'success': '#341616', 'danger': '#341616', 'warning': '#341616'}
        # Apply theme
        theme_param = self.theme_param.get_parameter_value().string_value

        match theme_param:
            case 'dark':
                base_theme = 'dark_blue.xml'
            case 'light':
                base_theme = 'light_blue.xml'
            case 'watermelon':
                base_path = Path(get_package_share_directory('gui')) / 'styles' / ('watermelon.xml')
                base_theme = base_path.as_posix()
            case _:
                base_theme = 'dark_blue.xml'
                self.node.get_logger().info(
                    'Theme ' + theme_param + ' not found, defaulting to dark.'
                )

        extra = extra_watermelon if theme_param == 'watermelon' else extra_blue
        apply_stylesheet(self, theme=base_theme, style='', extra=extra)

        executor = MultiThreadedExecutor()
        executor.add_node(self.node)
        Thread(target=executor.spin, daemon=True).start()

        self.show()

        # TODO: when the app closes it causes an error. Make not cause error?
        self.app.exec()

    def _clean_shutdown(self) -> None:
        if rclpy.utilities.ok():
            self.node.get_logger().info('Exiting.')
            self.node.destroy_node()
            rclpy.shutdown()

    def toggle_timer(self) -> None:
        """If the ROS timer is running, pause it. If it's paused, resume it."""
        GUINode().send_request_multithreaded(
            self.set_timer_client,
            MissionTimerSet.Request(set_running=True, running=not self.running),
            self.set_timer_response_signal,
        )

    def reset_timer(self) -> None:
        """Stop the timer and reset its remaining duration to the default value."""
        GUINode().send_request_multithreaded(
            self.set_timer_client,
            MissionTimerSet.Request(
                set_time=True,
                time=Duration(seconds=RESET_SECONDS).to_msg(),
                set_running=True,
                running=False,
            ),
            self.set_timer_response_signal,
        )
