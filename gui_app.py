import gradio as gr
import os
import sys
import warnings
from dotenv import load_dotenv
from PIL import Image

# 忽略警告
warnings.filterwarnings("ignore")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 匯入 v16.2 核心組件
from core.lut_engine import LUTEngine
from core.rag_core import KnowledgeBase
from core.smart_planner import SmartPlanner
from core.memory_manager import MemoryManager
from core.security import execute_safe_command
from core.logger import Logger
from core.gemini_client import GeminiClient  # [v16.2 New]

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("❌ 錯誤: 請在 .env 設定 GEMINI_API_KEY")
    sys.exit(1)

Logger.info("正在啟動 GUI (v16.2 Unified Memory)...")

# 初始化
memory_mgr = MemoryManager()
lut_engine = LUTEngine()
rag = KnowledgeBase()

try:
    all_luts = lut_engine.list_luts()
    if all_luts:
        rag.index_luts(all_luts)
except Exception:
    pass

# [v16.2] 傳入 lut_engine 與初始化 GeminiClient
planner = SmartPlanner(API_KEY, rag, lut_engine)
client = GeminiClient(API_KEY)

# 用於儲存回饋狀態的 Global 變數
current_context = {}


# ================= 工具函式 =================

def remember_user_preference(info: str):
    Logger.info(f"GUI 記憶: {info}")
    return memory_mgr.add_preference(info)


def check_available_luts(keyword: str = ""):
    all_names = list(lut_engine.lut_index.keys())
    if keyword:
        filtered = [n for n in all_names if keyword.lower() in n]
        if not filtered: return "無相關濾鏡。"
        return f"找到 {len(filtered)} 個..."

    # 隨機展示一些，避免塞爆畫面
    import random
    sample_size = min(len(all_names), 30)
    sample = random.sample(all_names, sample_size) if all_names else []
    return f"共 {len(all_names)} 個濾鏡。包含: {', '.join(sample)}..."


def get_current_memory():
    mem = memory_mgr._load_memory()
    prefs = mem.get("user_preferences", [])
    if not prefs: return "無資料"
    return "\n".join([f"- {p}" for p in prefs])


# ================= 對話邏輯 (Unified Memory) =================

def get_or_create_session(session_state):
    """
    確保 session 存在。使用 UnifiedChatSession 以支援模型輪詢。
    """
    if session_state is None:
        tools = [execute_safe_command, remember_user_preference, check_available_luts]
        base_prompt = """
        你是一個強大的 AI 助理 (Gemini 3 Pro)。
        【能力】修圖、查詢濾鏡、記憶偏好。
        請用繁體中文回答。
        """
        dynamic_context = memory_mgr.get_system_prompt_addition()

        # 建立
        session_state = client.create_unified_chat(
            tools=tools,
            system_instruction=base_prompt + dynamic_context
        )
        Logger.info("GUI: 已建立新的 Unified Chat Session")

    return session_state


def chat_response(user_message, history, session_state):
    # 取得或建立 Session
    session = get_or_create_session(session_state)

    try:
        Logger.debug(f"GUI 對話: {user_message}")
        # 發送訊息 (自動輪詢模型)
        response = session.send_message(user_message)

        # Gradio 的 history 格式通常是 List of [user, bot]
        # 但這裡我們使用 append 方式更新
        history.append((user_message, response.text))
        return "", history, session

    except Exception as e:
        Logger.error(f"GUI 對話錯誤: {e}")
        history.append((user_message, f"❌ 錯誤: {str(e)}"))
        return "", history, session


# ================= 視覺邏輯 =================

def process_image_smartly(image, user_req):
    Logger.info(f"GUI 修圖需求: {user_req}")
    if image is None: return None, "❌ 請先上傳圖片"
    if not user_req: user_req = "自動調整"

    # 存暫存檔給 AI 看
    temp_path = "temp_gui_input.jpg"
    image.save(temp_path)

    # 呼叫 Planner (內部使用 GeminiClient 自動輪詢)
    plan = planner.generate_plan(temp_path, user_req)

    if not plan or not plan.get('selected_lut'):
        return None, f"⚠️ AI 思考失敗: {plan.get('reasoning', '未知錯誤')}"

    # 更新 Context 以供回饋使用
    global current_context
    current_context = {"req": user_req, "plan": plan}

    # 執行調色
    final_img, msg = lut_engine.apply_lut(
        temp_path,
        plan['selected_lut'],
        intensity=plan.get('intensity', 1.0),
        brightness=plan.get('brightness', 1.0),
        saturation=plan.get('saturation', 1.0),
        temperature=plan.get('temperature', 0.0),
        tint=plan.get('tint', 0.0),
        contrast=plan.get('contrast', 1.0),
        curve_points=plan.get('curve_points'),
        sharpness=plan.get('sharpness', 1.0),
        simulate_log=plan.get('simulate_log', False),
        secondary_lut=plan.get('secondary_lut'),
        mix_ratio=plan.get('mix_ratio', 0.0)
    )

    # 產生報告
    mix_info = ""
    if plan.get('secondary_lut'):
        mix_info = f"<br>➕ 混合: `{plan.get('secondary_lut')}` ({plan.get('mix_ratio')})"

    curve_status = 'Custom' if plan.get('curve_points') else 'Linear'

    report = f"""### 🧪 決策報告 (v16.2)
**策略**: {plan.get('style_strategy', '無')}

| 參數 | 設定 |
| :--- | :--- |
| **LUT** | `{plan.get('selected_lut')}` {mix_info} |
| **強度** | {plan.get('intensity', 1.0)} |
| **WB** | T:{plan.get('temperature')} / Tint:{plan.get('tint')} |
| **Curve** | {curve_status} |

> {plan.get('caption', '完成')}
"""
    return final_img, report


def send_feedback(is_positive):
    global current_context
    if not current_context: return "⚠️ 無紀錄"
    score = 1 if is_positive else -1
    planner.learn_from_result(current_context['req'], current_context['plan'], score)
    return "✅ 已記錄" if is_positive else "❎ 已記錄"


# ================= GUI 建構 =================

with gr.Blocks(title="Gemini Agent v16.2", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🤖 Gemini Agent v16.2 (Unified Memory)")

    # 這裡儲存我們的 UnifiedChatSession 物件 (跨請求持久化)
    chat_state = gr.State(None)

    with gr.Tabs():
        # Tab 1: 修圖
        with gr.TabItem("👁️ 智能修圖"):
            with gr.Row():
                with gr.Column(scale=1):
                    input_img = gr.Image(type="pil", label="輸入圖片")
                    style_input = gr.Textbox(label="風格需求", placeholder="例如：日系冷白、膠片感、高對比...")
                    btn_process = gr.Button("🚀 開始煉金", variant="primary")

                    gr.Markdown("### 📝 結果回饋")
                    with gr.Row():
                        btn_good = gr.Button("👍 滿意 (學習)")
                        btn_bad = gr.Button("👎 不滿意 (避雷)")
                    feedback_msg = gr.Label(show_label=False)

                with gr.Column(scale=1):
                    output_img = gr.Image(label="修圖結果", type="pil")
                    output_info = gr.Markdown()

            btn_process.click(
                process_image_smartly,
                inputs=[input_img, style_input],
                outputs=[output_img, output_info]
            )
            btn_good.click(lambda: send_feedback(True), outputs=feedback_msg)
            btn_bad.click(lambda: send_feedback(False), outputs=feedback_msg)

        # Tab 2: 對話
        with gr.TabItem("💬 核心大腦"):
            chatbot = gr.Chatbot(height=500, label="Gemini 3 Pro")
            msg_input = gr.Textbox(label="輸入訊息", placeholder="聊聊天，或查詢濾鏡...")

            msg_input.submit(
                chat_response,
                inputs=[msg_input, chatbot, chat_state],
                outputs=[msg_input, chatbot, chat_state]
            )

        # Tab 3: 記憶
        with gr.TabItem("🧠 記憶庫"):
            memory_display = gr.Textbox(label="長期記憶", value=get_current_memory(), lines=10)
            gr.Button("🔄 刷新記憶").click(get_current_memory, outputs=memory_display)

if __name__ == "__main__":
    app.queue().launch(inbrowser=True, server_name="127.0.0.1")