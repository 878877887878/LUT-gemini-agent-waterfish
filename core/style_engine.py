import numpy as np
from PIL import Image, ImageEnhance, ImageOps
from core.logger import Logger


class StyleEngine:
    def __init__(self):
        # 🧪 v17 數學配方庫 (Parametric Recipes)
        self.styles = {
            "standard": {},  # 原圖

            "fuji_classic": {  # 日系冷白 / 富士感
                "saturation": 0.9,  # 修正：稍微回調，避免太淡
                "contrast": 1.05,
                "brightness": 1.05,
                "temp": -12,  # 偏冷 (藍)
                "tint": -5,  # 偏綠
                "curve": "s_curve_soft",
                "channel_mixer": {"r": 1.0, "g": 1.02, "b": 1.05}
            },

            "kodak_portra": {  # 溫暖復古 / 柯達感
                "saturation": 1.1,
                "contrast": 1.05,
                "brightness": 1.0,
                "temp": 15,  # 偏暖 (黃)
                "tint": 8,  # 偏洋紅
                "curve": "lifted_shadows",
                "channel_mixer": {"r": 1.05, "g": 1.0, "b": 0.9}
            },

            "cyberpunk": {  # 賽博龐克
                "saturation": 1.4,
                "contrast": 1.25,
                "brightness": 1.0,
                "temp": -25,
                "tint": 25,
                "curve": "hard_contrast",
                "channel_mixer": {"r": 0.8, "g": 0.9, "b": 1.3}
            },

            "monochrome_high": {  # 高對比黑白
                "saturation": 0.0,
                "contrast": 1.3,
                "brightness": 1.05,
                "curve": "hard_contrast",
                "channel_mixer": {"r": 0.3, "g": 0.59, "b": 0.11}
            },

            "soft_dream": {  # 柔焦夢幻
                "saturation": 0.9,
                "contrast": 0.9,
                "brightness": 1.1,
                "temp": 5,
                "curve": "linear",
                "sharpness": 0.5
            }
        }

    def get_available_styles(self):
        return list(self.styles.keys())

    def apply_style(self, image_path, style_name="standard", intensity=1.0, **overrides):
        try:
            with Image.open(image_path) as img:
                img = img.convert("RGB")

                recipe = self.styles.get(style_name, {}).copy()

                # 融合動態參數
                for key, value in overrides.items():
                    if value is not None:
                        if key in recipe and isinstance(recipe[key], (int, float)):
                            recipe[key] *= value
                        else:
                            recipe[key] = value

                Logger.info(f"🎨 套用數學風格: {style_name}")

                # [A] 基礎調整
                if "saturation" in recipe:
                    factor = 1.0 + (recipe["saturation"] - 1.0) * intensity
                    img = ImageEnhance.Color(img).enhance(factor)

                if "contrast" in recipe:
                    factor = 1.0 + (recipe["contrast"] - 1.0) * intensity
                    img = ImageEnhance.Contrast(img).enhance(factor)

                if "brightness" in recipe:
                    factor = 1.0 + (recipe["brightness"] - 1.0) * intensity
                    img = ImageEnhance.Brightness(img).enhance(factor)

                if "sharpness" in recipe:
                    factor = 1.0 + (recipe["sharpness"] - 1.0) * intensity
                    img = ImageEnhance.Sharpness(img).enhance(factor)

                # [B] 色溫/色調矩陣
                temp = recipe.get("temp", 0) * intensity
                tint = recipe.get("tint", 0) * intensity
                if temp != 0 or tint != 0:
                    img = self._apply_color_balance(img, temp, tint)

                # [C] 通道混合
                mixer = recipe.get("channel_mixer")
                if mixer:
                    img = self._apply_channel_mixer(img, mixer, intensity)

                # [D] 曲線調整
                curve_type = recipe.get("curve")
                if curve_type and curve_type != "linear":
                    img = self._apply_curve(img, curve_type, intensity)

                return img, "成功"

        except Exception as e:
            Logger.error(f"數學運算失敗: {e}")
            return None, str(e)

    def _apply_color_balance(self, img, temp, tint):
        """v17 色溫演算法"""
        r, g, b = img.split()
        scale = 0.02

        r_factor = 1.0 + (temp * scale) + (tint * scale)
        g_factor = 1.0 - (tint * scale)
        b_factor = 1.0 - (temp * scale)

        r = r.point(lambda i: int(min(255, max(0, i * r_factor))))
        g = g.point(lambda i: int(min(255, max(0, i * g_factor))))
        b = b.point(lambda i: int(min(255, max(0, i * b_factor))))

        return Image.merge("RGB", (r, g, b))

    def _apply_channel_mixer(self, img, mixer, intensity):
        """RGB 通道權重混合"""
        r, g, b = img.split()

        def mix(val): return 1.0 + (val - 1.0) * intensity

        r = r.point(lambda i: int(min(255, max(0, i * mix(mixer.get("r", 1.0))))))
        g = g.point(lambda i: int(min(255, max(0, i * mix(mixer.get("g", 1.0))))))
        b = b.point(lambda i: int(min(255, max(0, i * mix(mixer.get("b", 1.0))))))
        return Image.merge("RGB", (r, g, b))

    def _apply_curve(self, img, curve_type, intensity):
        """[Fix] 修正曲線數學公式"""
        x = np.arange(256)

        if curve_type == "s_curve_soft":
            # 經典 S 型: 255 / (1 + exp) 已經產生 0-255 的值了
            y = 255 / (1 + np.exp(-0.025 * (x - 128)))
            # 修正：移除多餘的 * 255
            y = x * (1 - intensity) + y * intensity

        elif curve_type == "lifted_shadows":
            # 褪色復古
            y = x + (25 - x * 0.1) * np.exp(-0.02 * x) * intensity

        elif curve_type == "hard_contrast":
            # 強烈對比
            y = 255 / (1 + np.exp(-0.04 * (x - 128)))
            # 修正：移除多餘的 * 255
            y = x * (1 - intensity) + y * intensity

        else:
            return img

        # 確保數值在 0-255 並轉為整數
        table = np.clip(y, 0, 255).astype(np.uint8).tolist()
        return img.point(table * 3)