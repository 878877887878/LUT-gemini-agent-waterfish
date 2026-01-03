import gradio as gr
import os
import sys
import warnings
from PIL import Image

warnings.filterwarnings("ignore")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 匯入 v17 核心
from core.style_engine import StyleEngine
from core.logic_planner import LogicPlanner
from core.logger import Logger

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

Logger.info("正在啟動 GUI (v17 Pure Math Edition)...")

# 初始化
style_engine = StyleEngine()
planner = LogicPlanner(style_engine)


def process_image_v17(image, user_req):
    if image is None: return None, "❌ 請先上傳圖片"
    if not user_req: user_req = "自動調整"

    Logger.info(f"GUI 請求: {user_req}")
    temp_path = "temp_gui_input.jpg"
    image.save(temp_path)

    # 1. 邏輯決策
    plan = planner.generate_plan(temp_path, user_req)

    # 2. 執行數學引擎
    final_img, msg = style_engine.apply_style(
        temp_path,
        style_name=plan['selected_style'],
        intensity=plan['intensity'],
        brightness=plan.get('brightness'),
        contrast=plan.get('contrast'),
        temp=plan.get('temperature')
    )

    # 3. 報告
    report = f"""### ✨ v17 參數化運算報告
**風格**: `{plan['selected_style']}`

| 動態修正 | 數值 |
| :--- | :--- |
| **Brightness** | {plan.get('brightness')} |
| **Contrast** | {plan.get('contrast')} |
| **Temp Shift** | {plan.get('temperature')} |

> Mode: Pure Math (No LUTs)
"""
    return final_img, report


# 建立介面
with gr.Blocks(title="Gemini Agent v17 (Math)", theme=gr.themes.Soft()) as app:
    gr.Markdown("# ✨ v17 Pure Math Edition (參數化運算版)")
    gr.Markdown("捨棄 LUT 檔案，改用純數學演算法進行風格渲染。")

    with gr.Row():
        with gr.Column(scale=1):
            input_img = gr.Image(type="pil", label="輸入圖片")
            style_input = gr.Textbox(
                label="風格指令",
                placeholder="例如: 日系, 柯達, 賽博, 黑白, 柔和..."
            )
            btn_process = gr.Button("✨ 執行運算", variant="primary")

        with gr.Column(scale=1):
            output_img = gr.Image(label="結果", type="pil")
            output_info = gr.Markdown()

    btn_process.click(
        process_image_v17,
        inputs=[input_img, style_input],
        outputs=[output_img, output_info]
    )

if __name__ == "__main__":
    app.queue().launch(inbrowser=True, server_name="127.0.0.1")