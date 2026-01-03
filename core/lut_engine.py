import os
import PIL.Image
import PIL.ImageOps
import PIL.ImageEnhance
from pillow_lut import load_cube_file
from functools import lru_cache
from collections import defaultdict
import difflib
import numpy as np
from core.logger import Logger


class LUTEngine:
    def __init__(self, lut_dir="luts"):
        self.lut_dir = lut_dir
        self.lut_index = defaultdict(list)
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

    def _simulate_log_curve(self, img):
        """
        v14 關鍵技術：將 Rec.709 照片「洗白」成偽 Log
        透過降低對比、提亮暗部、壓縮高光，創造適合 Log LUT 的灰底。
        """
        Logger.debug("執行 Log 模擬 (將照片變灰以適配 Log LUT)...")

        # 1. 大幅降低對比 (變平)
        img = PIL.ImageEnhance.Contrast(img).enhance(0.6)

        # 2. 降低飽和度 (Log 通常飽和度低)
        img = PIL.ImageEnhance.Color(img).enhance(0.7)

        # 3. 提升亮度 (Log 的暗部通常是灰的不是黑的)
        img = PIL.ImageEnhance.Brightness(img).enhance(1.1)

        # 4. Gamma 修正 (讓中間調更灰)
        # 這裡用簡單的曲線模擬 Log 的 lift
        r, g, b = img.split()
        lift_curve = lambda x: int(x * 0.9 + 15)  # 簡單的線性提亮
        r = r.point(lift_curve)
        g = g.point(lift_curve)
        b = b.point(lift_curve)

        return PIL.Image.merge("RGB", (r, g, b))

    def _adjust_white_balance(self, img, temp_val, tint_val):
        if temp_val == 0 and tint_val == 0: return img
        r, g, b = img.split()
        r_factor = 1.0 + (temp_val * 0.25)
        b_factor = 1.0 - (temp_val * 0.25)
        g_factor = 1.0 - (tint_val * 0.25)
        r = r.point(lambda i: int(min(255, max(0, i * r_factor))))
        g = g.point(lambda i: int(min(255, max(0, i * g_factor))))
        b = b.point(lambda i: int(min(255, max(0, i * b_factor))))
        return PIL.Image.merge("RGB", (r, g, b))

    def _apply_curve(self, img, curve_type):
        if curve_type == "Linear" or not curve_type: return img
        # (保留 v13 的曲線邏輯)
        x = np.arange(256)
        if curve_type == "S-Curve":
            factor = 5
            y = 255 / (1 + np.exp(-factor * (x / 255 - 0.5)))
            y = (y - y.min()) * 255 / (y.max() - y.min())
        elif curve_type == "Soft-High":
            y = np.where(x < 128, x, 128 + (x - 128) * 0.8)
        elif curve_type == "Lift-Shadow":
            y = np.where(x > 64, x, x + (64 - x) * 0.3)
        else:
            return img
        table = y.astype(np.uint8).tolist() * 3
        return img.point(table)

    def apply_lut(self, image_path, lut_name_or_path, intensity=1.0,
                  brightness=1.0, saturation=1.0, temperature=0.0, tint=0.0,
                  contrast=1.0, curve="Linear", sharpness=1.0,
                  simulate_log=False):  # [v14 新增參數]
        try:
            with PIL.Image.open(image_path) as im:
                img = PIL.ImageOps.exif_transpose(im).convert("RGB")

            # --- Step 0: Log Simulation (v14 新增) ---
            # 如果 AI 判斷這是一個 Log LUT，我們先把照片變灰！
            if simulate_log:
                img = self._simulate_log_curve(img)

            # --- Step 1: Pre-processing ---
            if brightness != 1.0:
                img = PIL.ImageEnhance.Brightness(img).enhance(brightness)
            if temperature != 0 or tint != 0:
                img = self._adjust_white_balance(img, temperature, tint)
            if contrast != 1.0:
                img = PIL.ImageEnhance.Contrast(img).enhance(contrast)
            if saturation != 1.0:
                img = PIL.ImageEnhance.Color(img).enhance(saturation)

            # --- Step 2: Curve ---
            img = self._apply_curve(img, curve)

            # --- Step 3: LUT ---
            target_path = None
            if os.path.exists(lut_name_or_path):
                target_path = lut_name_or_path
            else:
                lookup_name = os.path.basename(lut_name_or_path).lower()
                candidates = self.lut_index.get(lookup_name)
                if candidates:
                    target_path = candidates[0]
                else:
                    all_keys = list(self.lut_index.keys())
                    matches = difflib.get_close_matches(lookup_name, all_keys, n=1, cutoff=0.6)
                    if matches: target_path = self.lut_index[matches[0]][0]

            if not target_path:
                return img, "找不到 LUT，僅執行基礎修圖"

            intensity = max(0.0, min(1.0, float(intensity)))
            try:
                lut = self._get_lut_object(target_path)
                filtered_img = img.filter(lut)
            except Exception as e:
                return None, f"LUT 檔案損壞: {e}"

            if intensity < 1.0:
                final_img = PIL.Image.blend(img, filtered_img, intensity)
            else:
                final_img = filtered_img

            # --- Step 4: Post-processing ---
            if sharpness != 1.0:
                final_img = PIL.ImageEnhance.Sharpness(final_img).enhance(sharpness)

            return final_img, "成功"

        except Exception as e:
            Logger.error(f"Engine Error: {e}")
            return None, str(e)