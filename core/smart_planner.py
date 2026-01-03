import json
import os
import re
import random
import google.generativeai as genai
from PIL import Image
from core.logger import Logger
from core.feedback_manager import FeedbackManager
from core.smart_filter import SmartFilter
from core.gemini_client import GeminiClient


class SmartPlanner:
    def __init__(self, api_key, rag_engine, lut_engine):
        self.client = GeminiClient(api_key)
        self.rag = rag_engine
        self.lut_engine = lut_engine
        self.feedback = FeedbackManager()

    def _extract_json(self, text):
        try:
            clean_text = re.sub(r'```json\s*', '', text)
            clean_text = re.sub(r'```', '', clean_text)
            match = re.search(r'\{.*\}', clean_text, re.DOTALL)
            if match: return json.loads(match.group(0))
        except:
            pass
        return None

    def generate_plan(self, image_path, user_request):
        Logger.info(f"開始策劃修圖 (Target: Gemini 3 Pro): {user_request}")

        if not os.path.isfile(image_path):
            return {"selected_lut": None, "reasoning": "找不到圖片"}

        # [Step 1] 影像體質分析
        img_type, contrast_val = SmartFilter.analyze_image_type(image_path)
        Logger.info(f"🔍 影像分析: 類型=[{img_type.upper()}] (對比度 StdDev: {contrast_val:.2f})")

        # [Step 2] RAG 檢索
        raw_candidates = self.rag.search(user_request, n_results=60)

        # 初步過濾：嘗試找出符合體質的安全 LUT
        safe_candidates = SmartFilter.filter_luts(raw_candidates, img_type)

        # [Fix] 絕地求生與保底機制
        # 如果候選名單過少 (< 3)，代表 RAG 沒找到，或都被 Filter 殺光了
        if len(safe_candidates) < 3:
            all_real_luts = self.lut_engine.get_all_lut_names()

            if not all_real_luts:
                Logger.error("❌ 嚴重錯誤：luts 資料夾是空的！系統無 LUT 可用。")
            else:
                # 1. 先試著從本地隨機抽樣並過濾
                sample_pool = random.sample(all_real_luts, min(15, len(all_real_luts)))
                filtered_pool = SmartFilter.filter_luts(sample_pool, img_type)

                if filtered_pool:
                    # A計畫：有找到安全的，補進去
                    safe_candidates.extend(filtered_pool[:5])
                    Logger.debug(f"已從本地資料庫補充 {len(filtered_pool[:5])} 個安全 LUT")

                elif not safe_candidates:
                    # B計畫 (絕地求生)：
                    # 如果連補貨都濾不到 (代表你全是 Log LUT)，且目前手上一張牌都沒有
                    # 強制啟用「相容模式」：塞入不安全的 Log LUT，但在後續參數做限制
                    Logger.warn("⚠️ 警告：無適用 LUT (全為 Log 類)。強制啟用「相容模式」。")
                    safe_candidates.extend(sample_pool[:5])  # 強制塞 5 個

                safe_candidates = list(set(safe_candidates))

        # [Step 3] Prompt
        rl_context = self.feedback.get_learning_context(user_request)
        prompt = f"""
        你是一位 DI 專業調色師 (Powered by Gemini 3 Pro)。
        需求: "{user_request}" (類型: {img_type.upper()})
        {rl_context}
        可用 LUT: {safe_candidates}

        請回傳 JSON 包含: selected_lut, secondary_lut, mix_ratio, simulate_log, intensity, curve_points 等參數。
        若清單為空，請將 selected_lut 設為 null。
        """

        try:
            temp_thumb = "temp_analysis_thumb.jpg"
            with Image.open(image_path) as img:
                img.thumbnail((1024, 1024))
                img.save(temp_thumb, quality=85)

            response = self.client.generate_content(
                prompt=prompt,
                image=genai.upload_file(temp_thumb)
            )

            plan = self._extract_json(response.text)

            # [Step 4] 防呆與安全鎖
            if plan:
                if 'secondary_lut' not in plan: plan['secondary_lut'] = None
                if 'mix_ratio' not in plan: plan['mix_ratio'] = 0.0

                sel_lut = str(plan.get('selected_lut', ''))

                # 安全鎖檢查：如果圖片是 Standard，但 AI 選了 Log LUT (可能是因為我們B計畫強制塞給它的)
                if img_type == "standard" and sel_lut and sel_lut != "None":
                    if not SmartFilter.filter_luts([sel_lut], "standard"):
                        # 觸發！這是 Log LUT 用在標準圖上
                        Logger.warn(f"⚠️ 檢測到 Log LUT ({sel_lut}) 用於標準照片")

                        # 強制壓低強度，避免核爆
                        current_intensity = float(plan.get('intensity', 1.0))
                        # 如果原本強度很高，強制壓到 0.35 以下
                        if current_intensity > 0.35:
                            new_intensity = 0.30
                            plan['intensity'] = new_intensity
                            Logger.info(f"🛡️ 安全鎖介入：強度已從 {current_intensity} 壓制為 {new_intensity} (避免過曝)")

            return plan

        except Exception as e:
            Logger.error(f"Planner Error: {e}")
            return {"selected_lut": None, "reasoning": str(e)}

    def learn_from_result(self, user_req, plan, score):
        self.feedback.record_feedback(user_req, plan, score)