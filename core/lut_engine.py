import os
import PIL.Image
import PIL.ImageOps
import PIL.ImageEnhance
from pillow_lut import load_cube_file
from functools import lru_cache
from collections import defaultdict
import difflib
from core.logger import Logger  # [新增]


class LUTEngine:
    def __init__(self, lut_dir="luts"):
        self.lut_dir = lut_dir
        self.lut_index = defaultdict(list)
        self._build_index()

    def _build_index(self):
        self.lut_index.clear()
        if not os.path.exists(self.lut_dir):
            Logger.warn(f"LUT 目錄不存在: {self.lut_dir}")
            return

        Logger.info(f"正在建立 LUT 索引 (目錄: {self.lut_dir})...")
        count = 0
        for root, _, files in os.walk(self.lut_dir):
            for f in files:
                if f.lower().endswith('.cube'):
                    full_path = os.path.join(root, f)
                    self.lut_index[f.lower()].append(full_path)
                    count += 1
        Logger.success(f"LUT 索引建立完成，共索引 {count} 個檔案")

    def list_luts(self):
        all_paths = []
        for paths in self.lut_index.values():
            all_paths.extend(paths)
        return all_paths

    @lru_cache(maxsize=32)
    def _get_lut_object(self, lut_path):
        Logger.debug(f"載入 LUT 檔案 (Cache Miss): {os.path.basename(lut_path)}")
        return load_cube_file(lut_path)

    def _adjust_white_balance(self, img, temp_val, tint_val):
        """v12 專業白平衡演算法"""
        if temp_val == 0 and tint_val == 0: return img

        Logger.debug(f"執行白平衡修正: Temp={temp_val}, Tint={tint_val}")

        r, g, b = img.split()
        r_factor = 1.0 + (temp_val * 0.25)
        b_factor = 1.0 - (temp_val * 0.25)
        g_factor = 1.0 - (tint_val * 0.25)

        r = r.point(lambda i: int(min(255, max(0, i * r_factor))))
        g = g.point(lambda i: int(min(255, max(0, i * g_factor))))
        b = b.point(lambda i: int(min(255, max(0, i * b_factor))))

        return PIL.Image.merge("RGB", (r, g, b))

    def apply_lut(self, image_path, lut_name_or_path, intensity=1.0,
                  brightness=1.0, saturation=1.0, temperature=0.0, tint=0.0, contrast=1.0):
        Logger.info(f"開始處理圖片: {os.path.basename(image_path)}")
        Logger.debug(f"參數: I={intensity}, B={brightness}, S={saturation}, T={temperature}, Tint={tint}, C={contrast}")

        try:
            with PIL.Image.open(image_path) as im:
                img = PIL.ImageOps.exif_transpose(im).convert("RGB")

            # --- Step 1: Pre-processing ---
            if brightness != 1.0:
                img = PIL.ImageEnhance.Brightness(img).enhance(brightness)

            if temperature != 0 or tint != 0:
                img = self._adjust_white_balance(img, temperature, tint)

            if contrast != 1.0:
                img = PIL.ImageEnhance.Contrast(img).enhance(contrast)

            if saturation != 1.0:
                img = PIL.ImageEnhance.Color(img).enhance(saturation)

            # --- Step 2: LUT Search ---
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
                    if matches:
                        target_path = self.lut_index[matches[0]][0]
                        Logger.warn(f"模糊比對修正: {lut_name_or_path} -> {os.path.basename(target_path)}")

            if not target_path:
                Logger.error(f"找不到 LUT: {lut_name_or_path}")
                return None, f"找不到 LUT: {lut_name_or_path}"

            # --- Step 3: LUT Application ---
            intensity = max(0.0, min(1.0, float(intensity)))
            try:
                lut = self._get_lut_object(target_path)
            except Exception as e:
                Logger.error(f"LUT 讀取失敗: {e}")
                return None, f"LUT 檔案損壞: {e}"

            filtered_img = img.filter(lut)

            if intensity < 1.0:
                final_img = PIL.Image.blend(img, filtered_img, intensity)
            else:
                final_img = filtered_img

            Logger.success("圖片處理完成")
            return final_img, "成功"

        except Exception as e:
            Logger.error(f"處理過程發生例外: {e}")
            return None, str(e)