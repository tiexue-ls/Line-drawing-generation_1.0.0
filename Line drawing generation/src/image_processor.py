# image_processor.py
import cv2
import numpy as np
from typing import Optional


class ImageProcessor:
    """图像处理核心类，封装所有线稿生成算法"""

    def __init__(self):
        self.current_algorithm = "Canny Edge Detection"

    def load_image(self, file_path: str) -> Optional[np.ndarray]:
        """加载图片文件"""
        try:
            image = cv2.imread(file_path)
            if image is None:
                raise ValueError("Failed to read image")
            return image
        except Exception as e:
            print(f"Error loading image: {e}")
            return None

    def save_image(self, image: np.ndarray, file_path: str) -> bool:
        """保存图片文件"""
        try:
            return cv2.imwrite(file_path, image)
        except Exception as e:
            print(f"Error saving image: {e}")
            return False

    def convert(self, image: np.ndarray, algorithm: str, param: float) -> np.ndarray:
        """根据指定的算法和参数转换图片"""
        if algorithm == "Canny Edge Detection":
            return self._canny_edge(image, int(param))
        elif algorithm == "Pencil Sketch":
            return self._pencil_sketch(image, int(param))
        elif algorithm == "Adaptive Threshold":
            return self._adaptive_threshold(image, int(param))
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

    def _canny_edge(self, image: np.ndarray, low_threshold: int) -> np.ndarray:
        """Canny 边缘检测"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 1.0)
        high_threshold = low_threshold * 2
        edges = cv2.Canny(blurred, low_threshold, high_threshold)
        return edges

    def _pencil_sketch(self, image: np.ndarray, blur_ksize: int) -> np.ndarray:
        """铅笔素描效果"""
        if blur_ksize % 2 == 0:
            blur_ksize += 1  # 确保为奇数
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        inverted = 255 - gray
        blurred = cv2.GaussianBlur(inverted, (blur_ksize, blur_ksize), 0)
        sketch = cv2.divide(gray, 255 - blurred, scale=256.0)
        return sketch

    def _adaptive_threshold(self, image: np.ndarray, block_size: int) -> np.ndarray:
        """自适应阈值二值化"""
        if block_size % 2 == 0:
            block_size += 1
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY, block_size, 2
        )
        return edges