import json
import os
import re
import google.generativeai as genai
from PIL import Image
from core.logger import Logger


class SmartPlanner:
    def __init__(self, api_key, rag_engine):
        genai.configure(api_key=api_key)
        self.rag = rag_engine
        self.model = genai.GenerativeModel('gemini-3-pro-preview')
        Logger.info("SmartPlanner (Gemini 3 Pro) 初始化完成")

    def _extract_json(self, text):
        try:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception as e:
            Logger.warn(f"JSON 提取失敗: {e}")
        return None

    def generate_plan(self, image_path, user_request):
        Logger.info(f"開始策劃修圖: {user_request}")

        available_luts = self.rag.search(user_request, n_results=60)

        # v14 Prompt: Log LUT 適配邏輯
        prompt = f"""
        你是一位好萊塢等級的 DI 調色師。
        【使用者痛點】使用者擁有大量 Log LUT (如 F-Log to ETERNA)，但輸入的圖片是手機直出 (Rec709)。直接套用會導致「烤焦」效果。
        【你的任務】分析圖片，若選用 Log LUT，必須啟用 `simulate_log` 參數來「洗白」圖片。

        【可用資源】
        {available_luts}

        【 🛠️ 決策邏輯 】
        1. **LUT 選擇**: 優先尋找符合風格的 LUT。
        2. **Log 偵測**: 
           - 如果 selected_lut 的檔名包含 "Log", "Raw", "Flat", "V-Log", "S-Log", "F-Log" 等字眼。
           - 且原圖是標準對比 (JPG)。
           - **必須設定 `simulate_log: true`**。
        3. **一般參數**:
           - `curve`: "Soft-High" (推薦用於 Log 模擬模式，柔化高光)
           - `intensity`: 若啟用 Log 模擬，強度可設為 1.0 (因為底圖已經變灰了)；若無模擬，Log LUT 強度需降至 0.3。

        請回傳 **純 JSON 格式**：
        {{
            "technical_analysis": "原圖為 Rec709，但目標風格需要使用 F-Log 專用 LUT...",
            "style_strategy": "啟用 Log 模擬模式 (Simulate Log)，將原圖轉為低對比灰片，再套用 ETERNA LUT 以獲得正確色彩。",
            "selected_lut": "XH2S_FLog_..._ETERNA.cube",
            "simulate_log": true, 
            "intensity": 1.0,
            "brightness": 1.0,
            "contrast": 1.0,
            "saturation": 1.0,
            "temperature": 0.0,
            "tint": 0.0,
            "curve": "Soft-High",
            "sharpness": 0.9,
            "caption": "..."
        }}
        """

        try:
            if not os.path.isfile(image_path):
                return {"selected_lut": None, "reasoning": "找不到圖片"}

            temp_thumb = "temp_analysis_thumb.jpg"
            with Image.open(image_path) as img:
                img.thumbnail((1024, 1024))
                img.save(temp_thumb, quality=85)

            img_file = genai.upload_file(temp_thumb)
            response = self.model.generate_content([prompt, img_file])

            plan = self._extract_json(response.text)

            # v14 雙重防呆: 如果檔名有 Log 但 AI 忘了開模擬，幫它開
            if plan and plan.get('selected_lut'):
                lut_name = plan['selected_lut'].lower()
                is_log_lut = any(x in lut_name for x in ['log', 'raw', 'flat'])

                # 如果是 Log LUT 且沒有設定模擬，強制開啟
                if is_log_lut and not plan.get('simulate_log'):
                    Logger.warn(f"偵測到 Log LUT ({lut_name})，強制啟用 Log 模擬模式！")
                    plan['simulate_log'] = True
                    plan['intensity'] = 1.0  # 恢復強度，因為底圖已經變灰了

            return plan

        except Exception as e:
            Logger.error(f"SmartPlanner 錯誤: {e}")
            return {"selected_lut": None, "reasoning": str(e)}