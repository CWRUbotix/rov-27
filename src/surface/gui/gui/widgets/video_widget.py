from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from typing import NamedTuple

import cv2
import numpy as np
from cv_bridge import CvBridge
from numpy.typing import NDArray
from PyQt6.QtCore import Qt, pyqtBoundSignal, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QImage, QMouseEvent, QPixmap
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
from rclpy.qos import qos_profile_default
from sensor_msgs.msg import Image

from gui.gui_node import GUINode
from rov_msgs.msg import VideoWidgetSwitch
from rov_msgs.srv import CameraManage

# TODO: Ubuntu26+
# Our own implementation of cv2.typing.MatLike until cv2.typing exists in a future ubuntu release
# This what is actually implemented in cv2.typing:
# MatLike = cv2.mat_wrapper.Mat | NDArray[np.integer[Any] | np.floating[Any]]
# This should be possible in a newer version of mypy:
# MatLike = NDArray[np.integer[Any] | np.floating[Any]]
MatLike = NDArray[np.generic]

WIDTH = 721
HEIGHT = 541
# 1 Pixel larger than actual pixel dimensions


COLOR = 3
GREY_SCALE = 2


class CameraType(IntEnum):
    """
    Enum Class for defining Camera Types.

    Currently only Ethernet changes behavior.
    """

    USB = 1
    ETHERNET = 2
    DEPTH = 3
    SIMULATION = 4
    QPIXMAP = 5


@dataclass
class CameraManager:
    def __init__(self, topic_name: str, camera_id: int) -> None:
        self.camera_id = camera_id
        self.topic_name = topic_name
        self.client = GUINode().create_client_multithreaded(CameraManage, topic_name)

    def set_cam_state(self, *, on: bool) -> None:
        GUINode().send_request_multithreaded(
            self.client, CameraManage.Request(cam=self.camera_id, on=on)
        )


class CameraDescription(NamedTuple):
    """
    Generic CameraDescription describes each camera for a VideoWidget.

    Parameters
    ----------
    type: CameraType
        Describes the type of Camera.
    topic: str
        The topic to listen on, by default cam
    label: str
        The label of the camera, by default Camera
    width: int
        The width of the Camera Stream, by default WIDTH constant.
    height: int
        The height of the Camera Stream, by default HEIGHT constant.
    manager: CameraManager | None
        Used for toggling cam streams in SwitchableVideoWidgets

    """

    type: CameraType
    topic: str = 'cam'
    label: str = 'Camera'
    width: int = WIDTH
    height: int = HEIGHT
    manager: CameraManager | None = None


class ClickableLabel(QLabel):
    def __init__(self, signal: pyqtBoundSignal) -> None:
        super().__init__()
        self.signal = signal

    def mousePressEvent(self, event: QMouseEvent | None) -> None:  # noqa: N802
        if event is not None:
            self.signal.emit(event)

        return super().mousePressEvent(event)


class VideoWidget(QWidget):
    """A single video stream widget."""

    update_big_video_signal = pyqtSignal(QWidget)
    handle_frame_signal = pyqtSignal(Image)

    def __init__(
        self,
        camera_description: CameraDescription,
        make_label: Callable[[], QLabel] = lambda: QLabel(),
    ) -> None:
        super().__init__()

        self.camera_description = camera_description

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.video_frame_label = make_label()
        layout.addWidget(self.video_frame_label)

        self.label = QLabel(camera_description.label)
        self.label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.label.setStyleSheet('QLabel { font-size: 35px; }')
        layout.addWidget(self.label, Qt.AlignmentFlag.AlignHCenter)

        if camera_description.type == CameraType.QPIXMAP:
            self.video_frame_label.setText('No Pixmap received')
        else:
            self.video_frame_label.setText(f'This topic had no frame: {camera_description.topic}')
            self.cv_bridge = CvBridge()
            self.handle_frame_signal.connect(self.handle_frame)
            self.camera_subscriber = GUINode().create_signal_subscription(
                Image, camera_description.topic, self.handle_frame_signal
            )

    @pyqtSlot(Image)
    def handle_frame(self, frame: Image) -> None:
        cv_image = self.cv_bridge.imgmsg_to_cv2(frame, desired_encoding='passthrough')

        qt_image: QImage = self.convert_cv_qt(
            cv_image, self.camera_description.width, self.camera_description.height
        )

        self.set_pixmap(QPixmap.fromImage(qt_image))

    def get_pixmap(self) -> QPixmap:
        return self.video_frame_label.pixmap()

    def set_pixmap(self, pixmap: QPixmap) -> None:
        if pixmap.isNull():
            return

        self.video_frame_label.setPixmap(pixmap)
        self.video_frame_label.setFixedSize(pixmap.size())

    def convert_cv_qt(self, cv_img: MatLike, width: int = 0, height: int = 0) -> QImage:
        """Convert from an opencv image to QPixmap."""
        if self.camera_description.type == CameraType.ETHERNET:
            # Switches ethernet's color profile from BayerBGR to BGR
            cv_img = cv2.cvtColor(cv_img.astype('uint8'), cv2.COLOR_BAYER_BGGR2BGR)

        # Color image
        if len(cv_img.shape) == COLOR:
            h, w, ch = cv_img.shape
            bytes_per_line = ch * w

            img_format = QImage.Format.Format_RGB888

        # Grayscale image
        elif len(cv_img.shape) == GREY_SCALE:
            h, w = cv_img.shape
            bytes_per_line = w

            img_format = QImage.Format.Format_Grayscale8

        else:
            raise ValueError('Somehow not color or grayscale image.')

        qt_image = QImage(cv_img.data.tobytes(), w, h, bytes_per_line, img_format)
        qt_image = qt_image.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio)

        return qt_image


class SwitchableVideoWidget(VideoWidget):
    BUTTON_WIDTH = 150

    controller_signal = pyqtSignal(VideoWidgetSwitch)

    def __init__(
        self,
        camera_descriptions: Sequence[CameraDescription],
        controller_button_topic: str,
        default_cam_num: int = 0,
        make_label: Callable[[], QLabel] = lambda: QLabel(),
    ) -> None:
        self.camera_descriptions = camera_descriptions
        self.active_cam = default_cam_num

        self.num_of_cams = len(camera_descriptions)

        super().__init__(camera_descriptions[self.active_cam], make_label=make_label)

        self.button: QPushButton = QPushButton(camera_descriptions[self.active_cam].label)
        self.button.setMaximumWidth(self.BUTTON_WIDTH)
        self.button.clicked.connect(self.gui_camera_switch)

        layout = self.layout()
        if isinstance(layout, QVBoxLayout):
            layout.addWidget(self.button, alignment=Qt.AlignmentFlag.AlignCenter)
        else:
            GUINode().get_logger().error('Missing Layout')

        self.controller_signal.connect(self.controller_camera_switch)
        self.controller_publisher = GUINode().create_publisher(
            VideoWidgetSwitch, controller_button_topic, qos_profile_default
        )
        self.controller_subscriber = GUINode().create_signal_subscription(
            VideoWidgetSwitch, controller_button_topic, self.controller_signal
        )

    @pyqtSlot(VideoWidgetSwitch)
    def controller_camera_switch(self, switch: VideoWidgetSwitch) -> None:
        self.camera_switch(index=switch.index, relative=switch.relative)

    def gui_camera_switch(self) -> None:
        self.controller_publisher.publish(VideoWidgetSwitch(relative=True, index=1))

    def camera_switch(self, index: int, *, relative: bool) -> None:
        if relative:
            self.active_cam += index
        else:
            self.active_cam = index
        self.active_cam %= self.num_of_cams

        # Update Camera Description
        new_cam_description = self.camera_descriptions[self.active_cam]

        if new_cam_description.topic != self.camera_description.topic:
            GUINode().destroy_subscription(self.camera_subscriber)
            self.camera_subscriber = GUINode().create_signal_subscription(
                Image, new_cam_description.topic, self.handle_frame_signal
            )
        if self.camera_description.manager is not None:
            self.camera_description.manager.set_cam_state(on=False)
        if new_cam_description.manager is not None:
            new_cam_description.manager.set_cam_state(on=True)

        self.button.setText(new_cam_description.label)

        # Updates text for info when no frame received.
        last_pixmap = self.get_pixmap()
        self.video_frame_label.setText(f'This topic had no frame: {new_cam_description.topic}')
        self.label.setText(new_cam_description.label)

        self.camera_description = new_cam_description

        self.set_pixmap(last_pixmap)


class PauseableVideoWidget(VideoWidget):
    """A single video stream widget that can be paused and played."""

    BUTTON_WIDTH = 150
    PAUSED_TEXT = 'Play'
    PLAYING_TEXT = 'Pause'

    def __init__(self, camera_description: CameraDescription) -> None:
        super().__init__(camera_description)

        self.button = QPushButton(self.PLAYING_TEXT)
        self.button.setMaximumWidth(self.BUTTON_WIDTH)
        self.button.clicked.connect(self.toggle)

        layout = self.layout()
        if isinstance(layout, QVBoxLayout):
            layout.addWidget(self.button, alignment=Qt.AlignmentFlag.AlignCenter)
        else:
            GUINode().get_logger().error('Missing Layout')

        self.is_paused = False

    @pyqtSlot(Image)
    def handle_frame(self, frame: Image) -> None:
        if not self.is_paused:
            super().handle_frame(frame)

    def toggle(self) -> None:
        """Toggle whether this widget is paused or playing."""
        self.is_paused = not self.is_paused
        self.button.setText(self.PAUSED_TEXT if self.is_paused else self.PLAYING_TEXT)


class SaveableVideoWidget(VideoWidget):
    """A video stream widget that can save screenshots and record video clips."""

    def __init__(
        self,
        camera_description: CameraDescription,
        image_prefix: str = 'screenshot_',
        image_ext: str = 'png',
        video_prefix: str = 'recording_',
        video_ext: str = 'mp4',
        fps: float = 30.0,
    ) -> None:
        super().__init__(camera_description)

        self.image_prefix = image_prefix
        self.image_ext = image_ext.lstrip('.')
        self.video_prefix = video_prefix
        self.video_ext = video_ext.lstrip('.')
        self.fps = fps

        self.last_frame: MatLike | None = None
        self.is_recording = False
        self.video_writer: cv2.VideoWriter | None = None
        self.video_size: tuple[int, int] = (0, 0)

        button_layout = QHBoxLayout()

        self.save_img_button = QPushButton('Save Image')
        self.save_img_button.clicked.connect(self.save_image)
        button_layout.addWidget(self.save_img_button)

        self.record_button = QPushButton('Record Video')
        self.record_button.clicked.connect(self.toggle_recording)
        button_layout.addWidget(self.record_button)

        layout = self.layout()
        if isinstance(layout, QVBoxLayout):
            layout.addLayout(button_layout)
        else:
            GUINode().get_logger().error('Missing Layout')

    @pyqtSlot(Image)
    def handle_frame(self, frame: Image) -> None:
        cv_image = self.cv_bridge.imgmsg_to_cv2(frame, desired_encoding='passthrough')
        frame_to_save = cv_image
        if self.camera_description.type == CameraType.ETHERNET:
            frame_to_save = cv2.cvtColor(cv_image.astype('uint8'), cv2.COLOR_BAYER_BGGR2BGR)

        self.last_frame = frame_to_save

        if self.is_recording and self.video_writer is not None:
            h, w = frame_to_save.shape[:2]
            if (w, h) != self.video_size:
                frame_to_save = cv2.resize(frame_to_save, self.video_size)
            self.video_writer.write(frame_to_save)

        super().handle_frame(frame)

    def save_image(self) -> None:
        if self.last_frame is None:
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{self.image_prefix}{timestamp}.{self.image_ext}'

        filepath = Path(filename)
        if filepath.parent:
            filepath.parent.mkdir(parents=True, exist_ok=True)

        cv2.imwrite(str(filepath), self.last_frame)

    def toggle_recording(self) -> None:
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self) -> None:
        if self.last_frame is None:
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{self.video_prefix}{timestamp}.{self.video_ext}'

        filepath = Path(filename)
        if filepath.parent:
            filepath.parent.mkdir(parents=True, exist_ok=True)

        h, w = self.last_frame.shape[:2]
        self.video_size = (w, h)

        fourcc_code = 'mp4v' if self.video_ext.lower() == 'mp4' else 'XVID'
        fourcc = cv2.VideoWriter_fourcc(*fourcc_code)

        self.video_writer = cv2.VideoWriter(
            str(filepath), fourcc, self.fps, self.video_size
        )
        self.is_recording = True
        self.record_button.setText('Stop Recording')

    def stop_recording(self) -> None:
        self.is_recording = False
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None
        self.record_button.setText('Record Video')