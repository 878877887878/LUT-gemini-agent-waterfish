import json
import os
import re
import google.generativeai as genai
from PIL import Image
from core.logger import Logger
from core.feedback_manager import FeedbackManager


class SmartPlanner:
    def __init__(self, api_key, rag_engine):
        genai.configure(api_key=api_key)
        self.rag = rag_engine
        self.model = genai.GenerativeModel('gemini-3-pro-preview')
        self.feedback = FeedbackManager()

    def _extract_json(self, text):
        try:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match: return json.loads(match.group(0))
        except:
            pass
        return None

    def generate_plan(self, image_path, user_request):
        Logger.info(f"開始策劃修圖: {user_request}")

        # RAG 檢索
        available_luts = self.rag.search(user_request, n_results=60)
        rl_context = self.feedback.get_learning_context(user_request)

        # v16 Prompt: LUT 煉金術指令
        prompt = f"""
        你是一位 DI 專業調色師。你的目標是透過「混合」與「參數生成」來創造完美的影像，而不僅僅是套用現成濾鏡。

        【使用者需求】"{user_request}"
        {rl_context}

        【 🧪 LUT 倉庫 (用於解析與重組) 】
        {available_luts}

        【 🛠️ v16 煉金術決策 (Alchemy Strategy) 】
        1. **LUT 混合 (Hybrid Generation)**:
           - 如果單一 LUT 無法滿足需求（例如：想要 ETERNA 的質感但要 Kodak 的暖色），請使用混合模式。
           - `selected_lut`: 主風格 (Base)
           - `secondary_lut`: 副風格 (Tint/Atmosphere)，可從清單中選一個互補的。
           - `mix_ratio`: 混合比例 (0.0~1.0)。例如 0.3 代表 30% 副風格 + 70% 主風格。

        2. **曲線生成 (Curve Baking)**:
           - 分析現有 LUT 的缺點 (例如: 暗部太黑)，利用 `curve_points` 修正它。
           - 範例: `[[0,10], [50,55], [255,255]]` (提亮黑位，製造消光感)。

        3. **Log 防呆**: (同 v14, 遇 Log LUT 開啟模擬)

        請回傳 JSON：
        {{
            "technical_analysis": "...",
            "style_strategy": "解析發現單用 ETERNA 太冷，決定混合 30% Portra 400 來增加聖誕暖度...",
            "selected_lut": "主LUT檔名.cube",
            "secondary_lut": "副LUT檔名.cube", 
            "mix_ratio": 0.3,
            "simulate_log": false,
            "intensity": 0.8,
            "brightness": 1.0,
            "saturation": 1.0,
            "temperature": 0.0,
            "tint": 0.0,
            "curve_points": [[0,0], [255,255]],
            "sharpness": 1.0,
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

            # v16 參數防呆
            if plan:
                # 確保混合參數存在
                if 'secondary_lut' not in plan: plan['secondary_lut'] = None
                if 'mix_ratio' not in plan: plan['mix_ratio'] = 0.0

                # Log 防呆
                lut_name = str(plan.get('selected_lut', '')).lower()
                is_log = any(x in lut_name for x in ['log', 'raw', 'flat'])
                if is_log and not plan.get('simulate_log'):
                    Logger.warn("v16 自動修正: 強制啟用 Log 模擬")
                    plan['simulate_log'] = True
                    plan['intensity'] = 1.0

            return plan

        except Exception as e:
            Logger.error(f"Planner Error: {e}")
            return {"selected_lut": None, "reasoning": str(e)}

    def learn_from_result(self, user_req, plan, score):
        self.feedback.record_feedback(user_req, plan, score)