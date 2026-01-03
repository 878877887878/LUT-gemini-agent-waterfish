from core.image_analyzer import ImageAnalyzer
from core.logger import Logger


class LogicPlanner:
    def __init__(self, style_engine):
        self.style_engine = style_engine
        # 不再需要建立 LUT 索引

    def generate_plan(self, image_path, user_request):
        Logger.info(f"⚡ v17 邏輯分析: {user_request}")

        # 1. 影像分析
        stats = ImageAnalyzer.analyze(image_path)
        if not stats: return {"selected_style": "standard", "reasoning": "分析失敗"}

        Logger.info(f"📊 特徵: 亮度={stats['brightness']:.1f}, WB={stats['wb_ratio']:.2f}")

        # 2. 初始計畫
        plan = {
            "selected_style": "standard",
            "intensity": 1.0,
            "brightness": 1.0,
            "contrast": 1.0,
            "temperature": 0.0,
            "reasoning": "預設"
        }

        # 3. 自動校正 (針對體質)
        if stats['brightness'] < 70:
            plan['brightness'] = 1.3  # 太暗補光
        elif stats['brightness'] > 220:
            plan['brightness'] = 0.9  # 太亮壓光

        if stats['wb_ratio'] > 1.25:
            plan['temperature'] = -10  # 過暖校正

        # 4. 風格選擇 (關鍵字配對)
        req = user_request.lower()

        # [日系/冷白] -> 對應 fuji_classic
        if any(k in req for k in ["冷", "藍", "日系", "fuji", "clean"]):
            plan['selected_style'] = "fuji_classic"
            if "極" in req or "super" in req:
                plan['temperature'] -= 10  # 加強冷度

        # [暖調/復古] -> 對應 kodak_portra
        elif any(k in req for k in ["暖", "黃", "復古", "kodak", "portra", "vintage"]):
            plan['selected_style'] = "kodak_portra"

        # [賽博/霓虹] -> 對應 cyberpunk
        elif any(k in req for k in ["賽博", "霓虹", "cyber", "neon", "night"]):
            plan['selected_style'] = "cyberpunk"

        # [黑白] -> 對應 monochrome_high
        elif any(k in req for k in ["黑白", "單色", "bw", "mono"]):
            plan['selected_style'] = "monochrome_high"

        # [柔和] -> 對應 soft_dream
        elif any(k in req for k in ["柔", "夢幻", "soft", "dream"]):
            plan['selected_style'] = "soft_dream"

        return plan