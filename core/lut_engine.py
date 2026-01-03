import os
import PIL.Image
import PIL.ImageOps
import PIL.ImageEnhance
import numpy as np
from pillow_lut import load_cube_file
from functools import lru_cache
from collections import defaultdict
import difflib
from scipy.interpolate import PchipInterpolator
from core.logger import Logger


class LUTEngine:
    def __init__(self, lut_dir="luts"):
        self.lut_dir = lut_dir
        self.lut_index = defaultdict(list)
        self.usage_history = defaultdict(int)
        self._build_index()

    def _build_index(self):
        self.lut_index.clear()
        if not os.path.exists(self.lut_dir): return
        Logger.info("正在建立 LUT 索引...")
        for root, _, files in os.walk(self.lut_dir):
            for f in files:
                if f.lower().endswith('.cube'):
                    full_path = os.path.join(root, f)
                    self.lut_index[f.lower()].append(full_path)

    def list_luts(self):
        all_paths = []
        for paths in self.lut_index.values():
            all_paths.extend(paths)
        return all_paths

    @lru_cache(maxsize=32)
    def _get_lut_object(self, lut_path):
        return load_cube_file(lut_path)

    def _generate_spline_curve(self, img, points):
        if not points or len(points) < 2: return img
        # ... (保留 v15 的曲線邏輯) ...
        points.sort(key=lambda x: x[0])
        x_points, y_points = zip(*points)
        interp = PchipInterpolator(x_points, y_points)
        x_axis = np.arange(256)
        y_axis = np.clip(interp(x_axis), 0, 255).astype(np.uint8)
        table = y_axis.tolist() * 3
        return img.point(table)

    def _find_lut_path(self, lut_name):
        """輔助函式：尋找 LUT 路徑"""
        if not lut_name: return None
        if os.path.exists(lut_name): return lut_name

        lookup = os.path.basename(lut_name).lower()
        candidates = self.lut_index.get(lookup)
        if candidates: return candidates[0]

        # 模糊搜尋
        all_keys = list(self.lut_index.keys())
        matches = difflib.get_close_matches(lookup, all_keys, n=1, cutoff=0.6)
        if matches: return self.lut_index[matches[0]][0]
        return None

    def _simulate_log_curve(self, img):
        # ... (保留 v14 的 Log 模擬) ...
        img = PIL.ImageEnhance.Contrast(img).enhance(0.6)
        img = PIL.ImageEnhance.Color(img).enhance(0.7)
        img = PIL.ImageEnhance.Brightness(img).enhance(1.1)
        return img

    def _adjust_white_balance(self, img, temp_val, tint_val):
        # ... (保留 v14 的白平衡) ...
        if temp_val == 0 and tint_val == 0: return img
        r, g, b = img.split()
        r_factor = 1.0 + (temp_val * 0.25)
        b_factor = 1.0 - (temp_val * 0.25)
        g_factor = 1.0 - (tint_val * 0.25)
        r = r.point(lambda i: int(min(255, max(0, i * r_factor))))
        g = g.point(lambda i: int(min(255, max(0, i * g_factor))))
        b = b.point(lambda i: int(min(255, max(0, i * b_factor))))
        return PIL.Image.merge("RGB", (r, g, b))

    def apply_lut(self, image_path, lut_name_or_path, intensity=1.0,
                  brightness=1.0, saturation=1.0, temperature=0.0, tint=0.0,
                  contrast=1.0, curve_points=None, sharpness=1.0,
                  simulate_log=False,
                  secondary_lut=None, mix_ratio=0.0):  # [v16 新增混合參數]
        try:
            with PIL.Image.open(image_path) as im:
                img = PIL.ImageOps.exif_transpose(im).convert("RGB")

            # --- Step 0: Log Simulation ---
            if simulate_log:
                img = self._simulate_log_curve(img)

            # --- Step 1: Pre-processing ---
            if brightness != 1.0:
                img = PIL.ImageEnhance.Brightness(img).enhance(brightness)
            if temperature != 0 or tint != 0:
                img = self._adjust_white_balance(img, temperature, tint)

            # --- Step 2: Advanced Curve ---
            if curve_points and isinstance(curve_points, list):
                img = self._generate_spline_curve(img, curve_points)
            elif contrast != 1.0:
                img = PIL.ImageEnhance.Contrast(img).enhance(contrast)

            if saturation != 1.0:
                img = PIL.ImageEnhance.Color(img).enhance(saturation)

            # --- Step 3: LUT Mixing (Alchemy) [v16 核心] ---
            # 找出主 LUT
            path_a = self._find_lut_path(lut_name_or_path)

            # 找出副 LUT (若有)
            path_b = self._find_lut_path(secondary_lut) if (secondary_lut and mix_ratio > 0) else None

            processed_img = img  # 預設

            if path_a:
                self.usage_history[os.path.basename(path_a)] += 1
                try:
                    lut_a = self._get_lut_object(path_a)
                    img_a = img.filter(lut_a)

                    # 混合邏輯
                    if path_b:
                        Logger.info(
                            f"🧪 執行 LUT 煉金術: {os.path.basename(path_a)} + {os.path.basename(path_b)} (Mix: {mix_ratio})")
                        lut_b = self._get_lut_object(path_b)
                        img_b = img.filter(lut_b)
                        # 混合 A 和 B
                        blended_lut_result = PIL.Image.blend(img_a, img_b, alpha=mix_ratio)

                        # 再根據 intensity 與原圖混合
                        if intensity < 1.0:
                            processed_img = PIL.Image.blend(img, blended_lut_result, intensity)
                        else:
                            processed_img = blended_lut_result
                    else:
                        # 單一 LUT
                        if intensity < 1.0:
                            processed_img = PIL.Image.blend(img, img_a, intensity)
                        else:
                            processed_img = img_a

                except Exception as e:
                    Logger.error(f"LUT 應用失敗: {e}")
                    return img, f"LUT Error: {e}"
            else:
                if lut_name_or_path != "AI_Generated_LUT":
                    Logger.warn(f"找不到主 LUT: {lut_name_or_path}，僅執行基礎調色")

            # --- Step 4: Sharpness ---
            if sharpness != 1.0:
                processed_img = PIL.ImageEnhance.Sharpness(processed_img).enhance(sharpness)

            return processed_img, "成功"

        except Exception as e:
            Logger.error(f"Engine Error: {e}")
            return None, str(e)