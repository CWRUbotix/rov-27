import time
from threading import Thread

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QIntValidator
from PyQt6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from rclpy.qos import qos_profile_system_default

from gui.gui_node import GUINode
from rov_msgs.msg import MotorTest

# Buttons to test each thruster
# Call command to test thruster
# Update loop to test all thrusters

class ThrusterTester(QWidget):
    """Widget to command to test the thrusters, and reassign thruster ports."""

    TEST_LENGTH: float = 2.0  # time between adjacent tests of individual thrusters
    TEST_THROTTLE: float = 0.50  # 50%
    MOTOR_COUNT = 8


    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout()
        self.setLayout(layout)

        heading = QLabel('Thruster Pin Configuration')
        heading.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        pin_numbers_grid = QGridLayout()
        self.pin_input_widgets = []

        pin_number_validator = QIntValidator()
        pin_number_validator.setRange(0, self.MOTOR_COUNT - 1)

        for i in range(self.MOTOR_COUNT):
            pin_label = QLabel(str(i))
            pin_label.setMaximumWidth(20)
            pin_input = QLineEdit()
            pin_input.setValidator(pin_number_validator)
            pin_input.insert(str(i))
            pin_input.setMaximumWidth(40)
            self.pin_input_widgets.append(pin_input)

            pin_test_button = QPushButton('Test')
            # The i=i makes sure that it uses the value of i from this loop instead of the last loop
            pin_test_button.clicked.connect(lambda i=i: self.send_single_test_message(i))

            on_first_column = i < self.MOTOR_COUNT / 2
            column = 1 if on_first_column else 5
            row = i if on_first_column else i - self.MOTOR_COUNT // 2
            pin_numbers_grid.addWidget(pin_label, row, column)
            pin_numbers_grid.addWidget(pin_input, row, column + 1)
            pin_numbers_grid.addWidget(pin_test_button, row, column + 2)

        pin_numbers_grid.setColumnStretch(0, 1)
        pin_numbers_grid.setColumnStretch(4, 1)
        pin_numbers_grid.setColumnStretch(8, 1)

        pin_assignment_row = QHBoxLayout()
        pin_apply_button = QPushButton()
        pin_apply_button.setText('Apply Pins')

        pin_save_button = QPushButton()
        pin_save_button.setText('Save Pins')

        pin_assignment_row.addWidget(pin_apply_button)
        pin_assignment_row.addWidget(pin_save_button)

        test_button = QPushButton()
        test_button.setText('Test All Thrusters')
        test_button.clicked.connect(self.async_send_message)

        layout.addWidget(heading)
        layout.addLayout(pin_numbers_grid)
        layout.addLayout(pin_assignment_row)
        layout.addWidget(test_button)

        self.motor_test_publisher = GUINode().create_publisher(
            MotorTest, 'motor_test', qos_profile_system_default
        )

    def test_motor_for_time(self, motor_index: int, throttle: float, duration: float) -> None:
        """
        Run a motor for an (approximate) length of time (blocking).

        Based on https://github.com/mavlink/qgroundcontrol/blob/f79b466/src/Vehicle/Vehicle.cc

        Parameters
        ----------
        motor_index : int
            A motor index, from 1 to 8
        throttle : float
            A float from -1 to 1, where -1 is full reverse and 1 is full forward
        duration : float
            Time in seconds to run the motor

        """
        throttle = max(min(throttle, 1.0), -1.0)  # Clamp the throttle between -1 and 1
        throttle_percent = 50 * throttle + 50  # Rescale to be from 0 to 100, with 50 at the center

        start_time = time.time()
        while time.time() - start_time < duration:
            motor_test_msg = MotorTest(motor_id=motor_index, throttle_percent=throttle_percent)
            self.motor_test_publisher.publish(motor_test_msg)
            time.sleep(0.05)

    def async_send_message(self) -> None:
        Thread(target=self.send_test_message, daemon=True, name='thruster_test_thread').start()

    def send_test_message(self) -> None:
        for motor_index in range(1, self.MOTOR_COUNT + 1):
            self.send_single_test_message(motor_index)

    def send_pin_assignments(self) -> None:
        # TODO: Send the pin assignments inputted by the user to the pixhawk as parameters
        # https://wiki.ros.org/mavros/Plugins#param
        # https://ardupilot.org/copter/docs/parameters.html#servo10-parameters
        pass

    def send_single_test_message(self, motor_index: int) -> None:
        GUINode().get_logger().info(f'Testing thruster {motor_index}')
        self.test_motor_for_time(motor_index, self.TEST_THROTTLE, self.TEST_LENGTH)
        self.test_motor_for_time(motor_index, 0.0, 0.5)
