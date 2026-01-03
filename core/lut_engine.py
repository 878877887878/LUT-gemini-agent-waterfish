import os
import PIL.Image
import PIL.ImageOps
import PIL.ImageEnhance
import numpy as np
from pillow_lut import load_cube_file
from functools import lru_cache
from collections import defaultdict
import difflib
from core.logger import Logger

try:
    from scipy.interpolate import PchipInterpolator

    HAS_SCIPY = True
except ImportError:
    Logger.warn("未檢測到 Scipy，將使用簡易線性插值。建議 pip install scipy")
    HAS_SCIPY = False


class LUTEngine:
    def __init__(self, lut_dir="luts"):
        self.lut_dir = lut_dir
        self.lut_index = defaultdict(list)
        self.usage_history = defaultdict(int)
        self._build_index()

    def _build_index(self):
        self.lut_index.clear()
        if not os.path.exists(self.lut_dir):
            try:
                os.makedirs(self.lut_dir)
            except:
                pass
            return

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

    # [New] 新增這個函式：回傳所有真實存在的 LUT 檔名
    def get_all_lut_names(self):
        names = set()
        for paths in self.lut_index.values():
            for p in paths:
                names.add(os.path.basename(p))
        return list(names)

    @lru_cache(maxsize=32)
    def _get_lut_object(self, lut_path):
        if not os.path.exists(lut_path): return None
        return load_cube_file(lut_path)

    # ... (以下 _generate_spline_curve, _find_lut_path 等函式保持不變) ...
    def _generate_spline_curve(self, img, points):
        if not points or len(points) < 2: return img
        if not HAS_SCIPY: return img
        try:
            points.sort(key=lambda x: x[0])
            x_points, y_points = zip(*points)
            interp = PchipInterpolator(x_points, y_points)
            x_axis = np.arange(256)
            y_axis = np.clip(interp(x_axis), 0, 255).astype(np.uint8)
            if img.mode != 'RGB': img = img.convert('RGB')
            table = y_axis.tolist() * 3
            return img.point(table)
        except Exception as e:
            Logger.warn(f"曲線生成失敗: {e}")
            return img

    def _find_lut_path(self, lut_name):
        if not lut_name: return None
        if os.path.exists(str(lut_name)): return lut_name
        lookup = os.path.basename(str(lut_name)).lower()
        candidates = self.lut_index.get(lookup)
        if candidates: return candidates[0]
        all_keys = list(self.lut_index.keys())
        matches = difflib.get_close_matches(lookup, all_keys, n=1, cutoff=0.6)
        if matches: return self.lut_index[matches[0]][0]
        return None

    def _simulate_log_curve(self, img):
        img = PIL.ImageEnhance.Contrast(img).enhance(0.6)
        img = PIL.ImageEnhance.Color(img).enhance(0.7)
        img = PIL.ImageEnhance.Brightness(img).enhance(1.1)
        return img

    def _adjust_white_balance(self, img, temp_val, tint_val):
        if temp_val == 0 and tint_val == 0: return img
        r, g, b = img.split()
        r_factor = 1.0 + (temp_val * 0.2)
        b_factor = 1.0 - (temp_val * 0.2)
        g_factor = 1.0 - (tint_val * 0.2)
        r = r.point(lambda i: int(min(255, max(0, i * r_factor))))
        g = g.point(lambda i: int(min(255, max(0, i * g_factor))))
        b = b.point(lambda i: int(min(255, max(0, i * b_factor))))
        return PIL.Image.merge("RGB", (r, g, b))

    def apply_lut(self, image_path, lut_name_or_path, intensity=1.0,
                  brightness=1.0, saturation=1.0, temperature=0.0, tint=0.0,
                  contrast=1.0, curve_points=None, sharpness=1.0,
                  simulate_log=False,
                  secondary_lut=None, mix_ratio=0.0):
        try:
            if not os.path.exists(image_path):
                return None, "找不到圖片檔案"

            with PIL.Image.open(image_path) as im:
                img = PIL.ImageOps.exif_transpose(im).convert("RGB")

            if simulate_log:
                img = self._simulate_log_curve(img)

            if brightness != 1.0:
                img = PIL.ImageEnhance.Brightness(img).enhance(brightness)
            if temperature != 0 or tint != 0:
                img = self._adjust_white_balance(img, temperature, tint)

            if curve_points and isinstance(curve_points, list):
                img = self._generate_spline_curve(img, curve_points)
            elif contrast != 1.0:
                img = PIL.ImageEnhance.Contrast(img).enhance(contrast)

            if saturation != 1.0:
                img = PIL.ImageEnhance.Color(img).enhance(saturation)

            path_a = self._find_lut_path(lut_name_or_path)
            path_b = self._find_lut_path(secondary_lut) if (secondary_lut and mix_ratio > 0) else None

            processed_img = img

            if path_a:
                self.usage_history[os.path.basename(path_a)] += 1
                try:
                    lut_a = self._get_lut_object(path_a)
                    if lut_a:
                        img_a = img.filter(lut_a)
                        if path_b:
                            Logger.info(
                                f"🧪 混合 LUT: {os.path.basename(path_a)} + {os.path.basename(path_b)} ({mix_ratio})")
                            lut_b = self._get_lut_object(path_b)
                            if lut_b:
                                img_b = img.filter(lut_b)
                                blended_lut_result = PIL.Image.blend(img_a, img_b, alpha=mix_ratio)
                                if intensity < 1.0:
                                    processed_img = PIL.Image.blend(img, blended_lut_result, intensity)
                                else:
                                    processed_img = blended_lut_result
                            else:
                                processed_img = PIL.Image.blend(img, img_a, intensity) if intensity < 1.0 else img_a
                        else:
                            if intensity < 1.0:
                                processed_img = PIL.Image.blend(img, img_a, intensity)
                            else:
                                processed_img = img_a
                except Exception as e:
                    Logger.error(f"LUT 套用過程錯誤: {e}")
                    return img, f"Error: {e}"
            else:
                if lut_name_or_path and str(lut_name_or_path).lower() != "none":
                    Logger.warn(f"找不到 LUT: {lut_name_or_path}，僅執行基礎調色")

            if sharpness != 1.0:
                processed_img = PIL.ImageEnhance.Sharpness(processed_img).enhance(sharpness)

            return processed_img, "成功"

        except Exception as e:
            Logger.error(f"Engine Critical Error: {e}")
            return None, str(e)