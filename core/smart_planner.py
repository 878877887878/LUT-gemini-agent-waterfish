import json
import os
import re
import google.generativeai as genai
from PIL import Image
from core.logger import Logger  # [新增]


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

        # 1. RAG
        available_luts = self.rag.search(user_request, n_results=60)
        Logger.debug(f"RAG 檢索到 {len(available_luts)} 個候選 LUT")

        # 2. Prompt (v12)
        prompt = f"""
        你是一位好萊塢等級的 DI (Digital Intermediate) 專業調色師。
        請對這張影像進行「深度技術分析」，並制定修圖參數。

        【使用者需求】
        "{user_request}"

        【 🎨 可用 LUT 資源庫 】
        {available_luts}

        【 🛠️ 思考流程 (Chain of Thought) 】
        1. **技術檢測**: 
           - 曝光: 是否過暗(Underexposed)或過曝(Overexposed)?
           - 白平衡: 是否偏黃(Too Warm)、偏藍(Too Cool)或偏綠(Tint Issue)?
           - 對比度: 畫面是否灰濛濛(Flat)或太刺眼(Harsh)?
        2. **風格配對**: 從 LUT 庫中挑選最符合「敘事氛圍」的一款。
        3. **參數微調 (Pre-processing)**: 
           - 設定 `brightness` (亮度 0.8~1.5)
           - 設定 `contrast` (對比度 0.8~1.3, 增加對比可去灰霧)
           - 設定 `temperature` (色溫 -1.0~1.0, 負值修正黃光)
           - 設定 `tint` (色調 -1.0~1.0, 負值修正綠色偏, 正值增加洋紅/膚色通透感)
           - 設定 `saturation` (飽和度 0.0~1.5)

        請回傳 **純 JSON 格式** (不要 Markdown)：
        {{
            "technical_analysis": "原圖曝光不足約 1 檔，室內光線導致膚色嚴重偏黃綠...",
            "style_strategy": "採用低飽和冷色調 LUT 來中和黃光，並提升對比度增加質感...",
            "selected_lut": "精確檔名.cube",
            "intensity": 0.85,
            "brightness": 1.2,
            "contrast": 1.1,
            "saturation": 0.9,
            "temperature": -0.3,
            "tint": 0.2,
            "caption": "..."
        }}
        """

        try:
            if not os.path.isfile(image_path):
                Logger.error(f"找不到圖片檔案: {image_path}")
                return {"selected_lut": None, "reasoning": "找不到圖片"}

            # 縮圖加速
            temp_thumb = "temp_analysis_thumb.jpg"
            with Image.open(image_path) as img:
                img.thumbnail((1024, 1024))
                img.save(temp_thumb, quality=85)

            Logger.debug("圖片已縮放並上傳至 Gemini...")
            img_file = genai.upload_file(temp_thumb)

            response = self.model.generate_content([prompt, img_file])

            # Debug: 印出原始回應的前 100 字，確認 AI 有沒有亂講話
            Logger.debug(f"AI 原始回應 (前段): {response.text[:100]}...")

            plan = self._extract_json(response.text)

            if not plan or not plan.get('selected_lut'):
                Logger.warn("AI 回傳的 JSON 格式錯誤或欄位缺失，啟動 Fallback")
                return {
                    "technical_analysis": "解析失敗",
                    "style_strategy": "Fallback",
                    "selected_lut": available_luts[0] if available_luts else None,
                    "intensity": 0.7,
                    "brightness": 1.0,
                    "contrast": 1.0,
                    "saturation": 1.0,
                    "temperature": 0.0,
                    "tint": 0.0,
                    "caption": "AI 自動修圖"
                }

            Logger.success(f"策劃完成。策略: {plan.get('style_strategy')[:50]}...")
            return plan

        except Exception as e:
            Logger.error(f"SmartPlanner 發生錯誤: {e}")
            return {"selected_lut": None, "reasoning": str(e)}