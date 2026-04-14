# main_window.py
import sys
import cv2
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QComboBox, QSlider, QStatusBar,
    QSplitter, QGroupBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QImage, QAction

from image_processor import ImageProcessor


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image to Line Art")
        self.setMinimumSize(900, 600)

        # 初始化图像处理器
        self.processor = ImageProcessor()
        self.original_image = None
        self.line_art_image = None

        self._setup_ui()
        self._setup_menu_bar()
        self._connect_signals()

    def _setup_ui(self):
        """初始化 UI 组件"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 图像显示区域（左右分栏）
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：原图显示
        self.original_group = QGroupBox("Original Image")
        original_layout = QVBoxLayout()
        self.original_label = QLabel()
        self.original_label.setAlignment(Qt.AlignCenter)
        self.original_label.setMinimumSize(400, 300)
        self.original_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        self.original_label.setText("No image loaded")
        original_layout.addWidget(self.original_label)
        self.original_group.setLayout(original_layout)

        # 右侧：线稿显示
        self.result_group = QGroupBox("Line Art Result")
        result_layout = QVBoxLayout()
        self.result_label = QLabel()
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setMinimumSize(400, 300)
        self.result_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        self.result_label.setText("Convert to see line art")
        result_layout.addWidget(self.result_label)
        self.result_group.setLayout(result_layout)

        splitter.addWidget(self.original_group)
        splitter.addWidget(self.result_group)
        splitter.setSizes([450, 450])

        main_layout.addWidget(splitter)

        # 控制按钮区域
        button_layout = QHBoxLayout()
        self.load_btn = QPushButton("Load Image")
        self.convert_btn = QPushButton("Convert to Line Art")
        self.save_btn = QPushButton("Save Result")
        button_layout.addWidget(self.load_btn)
        button_layout.addWidget(self.convert_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        # 算法选择与参数调节
        algo_layout = QHBoxLayout()
        algo_layout.addWidget(QLabel("Algorithm:"))

        self.algo_combo = QComboBox()
        self.algo_combo.addItems(["Canny Edge Detection", "Pencil Sketch", "Adaptive Threshold"])
        algo_layout.addWidget(self.algo_combo)

        algo_layout.addSpacing(20)
        algo_layout.addWidget(QLabel("Parameter:"))

        self.param_slider = QSlider(Qt.Horizontal)
        self.param_slider.setRange(0, 100)
        self.param_slider.setValue(50)
        self.param_slider.setTickPosition(QSlider.TicksBelow)
        self.param_slider.setTickInterval(10)
        algo_layout.addWidget(self.param_slider)

        self.param_label = QLabel("50")
        algo_layout.addWidget(self.param_label)

        self.apply_btn = QPushButton("Apply")
        algo_layout.addWidget(self.apply_btn)
        algo_layout.addStretch()

        main_layout.addLayout(algo_layout)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _setup_menu_bar(self):
        """设置菜单栏"""
        menubar = self.menuBar()

        # File 菜单
        file_menu = menubar.addMenu("File")
        open_action = QAction("Open Image", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.load_image)
        file_menu.addAction(open_action)

        save_action = QAction("Save Line Art", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_line_art)
        file_menu.addAction(save_action)

        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help 菜单
        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _connect_signals(self):
        """连接信号与槽"""
        self.load_btn.clicked.connect(self.load_image)
        self.convert_btn.clicked.connect(self.convert_to_line_art)
        self.save_btn.clicked.connect(self.save_line_art)
        self.apply_btn.clicked.connect(self.apply_parameters)
        self.param_slider.valueChanged.connect(self._update_param_label)

    def load_image(self):
        """加载图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.tiff)"
        )
        if file_path:
            self.original_image = self.processor.load_image(file_path)
            if self.original_image is not None:
                self._display_image(self.original_image, self.original_label)
                self.status_bar.showMessage(f"Loaded: {file_path}")
                # 自动执行一次转换
                self.convert_to_line_art()
            else:
                self.status_bar.showMessage("Failed to load image")

    def convert_to_line_art(self):
        """转换图片为线稿"""
        if self.original_image is None:
            self.status_bar.showMessage("Please load an image first")
            return

        algo = self.algo_combo.currentText()
        param = self._get_scaled_parameter()

        self.line_art_image = self.processor.convert(self.original_image, algo, param)
        self._display_image(self.line_art_image, self.result_label)
        self.status_bar.showMessage(f"Converted using {algo}")

    def _display_image(self, image: np.ndarray, label: QLabel):
        """将 OpenCV 图像显示到 QLabel"""
        if len(image.shape) == 2:
            # 灰度图
            h, w = image.shape
            bytes_per_line = w
            q_img = QImage(image.data, w, h, bytes_per_line, QImage.Format_Grayscale8)
        else:
            # 彩色图
            h, w, ch = image.shape
            bytes_per_line = ch * w
            # BGR 转 RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            q_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)

        pixmap = QPixmap.fromImage(q_img)
        scaled_pixmap = pixmap.scaled(
            label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        label.setPixmap(scaled_pixmap)

    def save_line_art(self):
        """保存线稿图"""
        if self.line_art_image is None:
            self.status_bar.showMessage("No line art to save")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Line Art", "line_art.png", "PNG (*.png);;JPEG (*.jpg);;BMP (*.bmp)"
        )
        if file_path:
            success = self.processor.save_image(self.line_art_image, file_path)
            if success:
                self.status_bar.showMessage(f"Saved to: {file_path}")
            else:
                self.status_bar.showMessage("Failed to save image")

    def apply_parameters(self):
        """应用参数调整"""
        self.convert_to_line_art()

    def _update_param_label(self, value: int):
        """更新参数显示标签"""
        self.param_label.setText(str(value))

    def _get_scaled_parameter(self) -> float:
        """将滑块值 (0-100) 映射到算法实际参数范围"""
        algo = self.algo_combo.currentText()
        raw_value = self.param_slider.value()

        if algo == "Canny Edge Detection":
            # Canny 低阈值映射到 50-250
            return 50 + raw_value * 2
        elif algo == "Pencil Sketch":
            # 模糊核大小映射到 3-51（奇数）
            return max(3, raw_value * 2 + 1) if raw_value * 2 + 1 <= 51 else 51
        else:
            # 自适应阈值块大小映射到 3-31（奇数）
            return max(3, raw_value // 5 * 2 + 3) if raw_value // 5 * 2 + 3 <= 31 else 31

    def _show_about(self):
        """显示关于对话框"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.about(
            self, "About Image to Line Art",
            "Image to Line Art v1.0.0\n\n"
            "A desktop application to convert images to line art.\n"
            "Built with Python, OpenCV, and Qt (PySide6).\n\n"
            "© 2025 Open Source Project"
        )