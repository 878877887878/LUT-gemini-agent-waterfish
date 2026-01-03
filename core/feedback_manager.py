import json
import os
import uuid
from datetime import datetime
from core.logger import Logger

class FeedbackManager:
    def __init__(self, feedback_file="core/rl_feedback.json"):
        self.feedback_file = feedback_file
        self.data = self._load_data()

    def _load_data(self):
        # 確保目錄存在
        os.makedirs(os.path.dirname(self.feedback_file), exist_ok=True)
        
        if os.path.exists(self.feedback_file):
            try:
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"positive": [], "negative": []}
        return {"positive": [], "negative": []}

    def save_data(self):
        with open(self.feedback_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def record_feedback(self, user_req, plan, score, img_stats=None):
        """
        記錄回饋
        score: 1 (Positive), -1 (Negative)
        """
        entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "request": user_req,
            "plan_snapshot": plan,
            # 未來可擴充：加入圖片特徵向量
        }
        
        if score > 0:
            self.data["positive"].append(entry)
            # 限制數量避免 Token 爆炸 (只留最近 30 筆)
            if len(self.data["positive"]) > 30: self.data["positive"].pop(0)
            Logger.success(f"已記錄正向樣本 (ID: {entry['id'][:8]})")
        else:
            self.data["negative"].append(entry)
            if len(self.data["negative"]) > 30: self.data["negative"].pop(0)
            Logger.warn(f"已記錄負向樣本 (ID: {entry['id'][:8]})")
        
        self.save_data()

    def get_learning_context(self, current_req):
        """
        RAG 檢索：找出過去的成功/失敗經驗
        目前使用簡易關鍵字比對，未來可升級為向量搜尋
        """
        context = ""
        
        # 1. 檢索正向經驗
        relevant_pos = [item for item in self.data["positive"] if self._is_relevant(current_req, item['request'])]
        if relevant_pos:
            context += "\n【 🧠 強化學習經驗 (RLHF History) 】\n"
            context += "以下是你過去獲得「高分評價」的成功策略，請參考：\n"
            for item in relevant_pos[-3:]: # 取最近 3 筆
                p = item['plan_snapshot']
                lut_name = p.get('selected_lut', 'Unknown')
                curve = p.get('curve', 'Linear')
                context += f"- 需求 '{item['request']}': 使用了 LUT='{lut_name}', Mix={p.get('mix_ratio', 0)}, Curve='{curve}'\n"
        
        # 2. 檢索負向經驗 (避雷針)
        relevant_neg = [item for item in self.data["negative"] if self._is_relevant(current_req, item['request'])]
        if relevant_neg:
            if not context: context += "\n【 🧠 強化學習經驗 (RLHF History) 】\n"
            context += "⚠️ 避雷針 (過去失敗的設定，請避免重犯)：\n"
            for item in relevant_neg[-3:]:
                p = item['plan_snapshot']
                lut_name = p.get('selected_lut', 'Unknown')
                context += f"- 需求 '{item['request']}': 用戶拒絕了 LUT='{lut_name}' 搭配 Temp={p.get('temperature')}\n"
                
        return context

    def _is_relevant(self, req1, req2):
        """簡單的關聯性判斷 (未來可用 Embedding)"""
        # 如果需求有關鍵字重疊，視為相關
        keywords1 = set(req1.split())
        keywords2 = set(req2.split())
        return not keywords1.isdisjoint(keywords2) or len(req1) < 5 # 短指令放寬標準