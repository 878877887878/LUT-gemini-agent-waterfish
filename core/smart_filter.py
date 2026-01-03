import numpy as np
from PIL import Image
import logging

class SmartFilter:
    """
    v16.1 智慧濾網：防止 AI 對標準照片誤用 Log/Raw 專用 LUT。
    """
    
    # 定義「危險關鍵字」：這些 LUT 只能用於 Log 素材
    # 如果用在一般 JPG 上，會造成對比度爆炸或色偏
    LOG_KEYWORDS = [
        "flog", "slog", "vlog", "clog", "log2", "log3", 
        "gamut", "hlg", "cinema", "eterna-bb", "f-gamut", 
        "blackmagic", "arri"
    ]

    @staticmethod
    def analyze_image_type(image_path):
        """
        分析圖片的直方圖/對比度。
        Returns: 
            'log': 低對比灰片 (適合 Log LUT)
            'standard': 標準照片 (禁止 Log LUT)
        """
        try:
            with Image.open(image_path) as img:
                # 轉為灰階計算標準差
                img_gray = img.convert('L')
                img_data = np.array(img_gray)
                std_dev = np.std(img_data)
                
                # Log 素材通常極灰，標準差極低 (通常 < 30)
                # 一般手機/相機直出的 JPG 標準差通常 > 40~50
                if std_dev < 30:
                    return "log", std_dev
                else:
                    return "standard", std_dev
                    
        except Exception as e:
            logging.error(f"圖片分析失敗: {e}，預設為 standard")
            return "standard", 0

    @classmethod
    def filter_luts(cls, lut_list, image_type):
        """
        根據圖片類型，過濾掉不安全的 LUT。
        """
        if image_type == "log":
            # 如果是 Log 素材，所有 LUT 都可以用
            return lut_list
        
        # 如果是 Standard 照片，執行嚴格過濾
        safe_luts = []
        for lut in lut_list:
            is_dangerous = any(k in lut.lower() for k in cls.LOG_KEYWORDS)
            if not is_dangerous:
                safe_luts.append(lut)
        
        return safe_luts