import numpy as np
from PIL import Image


class ImageAnalyzer:
    @staticmethod
    def analyze(image_path):
        """
        純數學分析圖片特徵
        回傳: dict 包含亮度、對比、色溫傾向、飽和度
        """
        try:
            with Image.open(image_path) as img:
                # 轉為 RGB 陣列
                img_rgb = img.convert('RGB')
                data = np.array(img_rgb)

                # 1. 亮度 (Luminance)
                # 使用 Rec.709 權重: R*0.2126 + G*0.7152 + B*0.0722
                luminance = np.dot(data[..., :3], [0.2126, 0.7152, 0.0722])
                avg_brightness = np.mean(luminance)

                # 2. 對比度 (Standard Deviation of Luminance)
                contrast = np.std(luminance)

                # 3. 色溫傾向 (Red / Blue Ratio)
                # R/B > 1 為暖調，R/B < 1 為冷調
                r_mean = np.mean(data[:, :, 0])
                b_mean = np.mean(data[:, :, 2])
                wb_ratio = r_mean / (b_mean + 1e-5)  # 避免除以 0

                # 4. 飽和度 (Saturation in HSV)
                img_hsv = img.convert('HSV')
                hsv_data = np.array(img_hsv)
                avg_saturation = np.mean(hsv_data[:, :, 1])

                return {
                    "brightness": avg_brightness,  # 0~255
                    "contrast": contrast,  # 0~127+
                    "wb_ratio": wb_ratio,  # >1 Warm, <1 Cold
                    "saturation": avg_saturation  # 0~255
                }
        except Exception as e:
            print(f"分析失敗: {e}")
            return None