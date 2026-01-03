import os
import sys
import asyncio
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.markdown import Markdown
from rich.progress import track
import warnings

warnings.simplefilter('ignore')

from core.lut_engine import LUTEngine
from core.rag_core import KnowledgeBase
from core.smart_planner import SmartPlanner
from core.memory_manager import MemoryManager
from core.security import execute_safe_command
from core.logger import Logger
from core.gemini_client import GeminiClient

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
console = Console()

if not API_KEY:
    Logger.error("請在 .env 設定 GEMINI_API_KEY")
    sys.exit(1)

Logger.info("正在啟動 Gemini Agent v16.2 (Unified Memory & Safe Mode)...")

memory_mgr = MemoryManager()
lut_engine = LUTEngine()
rag = KnowledgeBase()

try:
    all_luts = lut_engine.list_luts()
    if all_luts:
        rag.index_luts(all_luts)
except Exception as e:
    Logger.warn(f"索引建立警告: {e}")

planner = SmartPlanner(API_KEY, rag, lut_engine)
client = GeminiClient(API_KEY)


# ================= 工具函式 =================

def remember_user_preference(info: str):
    Logger.info(f"寫入記憶: {info}")
    return memory_mgr.add_preference(info)


def check_available_luts(keyword: str = ""):
    Logger.debug(f"查詢 LUT: {keyword}")
    all_names = list(lut_engine.lut_index.keys())
    if keyword:
        filtered = [n for n in all_names if keyword.lower() in n]
        if not filtered:
            return "沒有找到符合的濾鏡。"
        return f"找到 {len(filtered)} 個：{', '.join(filtered[:20])}..."
    return f"系統共有 {len(all_names)} 個濾鏡。"


def create_chat_session():
    tools = [execute_safe_command, remember_user_preference, check_available_luts]
    base_prompt = """
    你是一個強大的 AI 助理 (Gemini 3 Pro)。
    【能力】修圖、查詢濾鏡、記憶偏好。
    請用繁體中文回答。
    """
    dynamic_context = memory_mgr.get_system_prompt_addition()
    return client.create_unified_chat(
        tools=tools,
        system_instruction=base_prompt + dynamic_context
    )


def get_input_safe(prompt_text):
    while True:
        try:
            user_in = console.input(prompt_text)
            if not user_in.strip(): continue
            return user_in.strip()
        except (KeyboardInterrupt, EOFError):
            return None


def select_files_from_directory(dir_path):
    valid_exts = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff')
    try:
        files = [f for f in os.listdir(dir_path) if f.lower().endswith(valid_exts)]
    except Exception:
        return None
    if not files: return None

    table = Table(title=f"📂 資料夾: {dir_path}")
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("檔名", style="green")
    table.add_row("0", "🚀 [bold yellow]批次處理全部[/]")

    for idx, f in enumerate(files):
        table.add_row(str(idx + 1), f)
    console.print(table)

    while True:
        selection = get_input_safe(f"[yellow]請選擇 ID (0-{len(files)}): [/]")
        if selection is None or selection.lower() in ['q', 'exit']: return None
        try:
            idx = int(selection)
            if idx == 0: return [os.path.join(dir_path, f) for f in files]
            if 0 < idx <= len(files): return [os.path.join(dir_path, files[idx - 1])]
        except ValueError:
            pass


# [New] 安全獲取文字回應的輔助函式
def get_response_text_safe(response):
    try:
        return response.text
    except Exception:
        # 如果沒有 text part (例如只有 function call)，手動檢查 parts
        if hasattr(response, 'parts'):
            for part in response.parts:
                if hasattr(part, 'text') and part.text:
                    return part.text
        return "✅ 指令已執行 (無文字回應)"


async def main():
    console.clear()
    console.print(Panel.fit("[bold cyan]🤖 Gemini Agent v16.2 (Ultimate Edition)[/]", border_style="cyan"))

    cli_chat_session = None

    while True:
        try:
            console.print("\n[dim]──────────────────────────────────────────────────[/]")
            user_input = get_input_safe("[yellow]請輸入 [bold white]圖片路徑[/] 或 [bold white]指令/聊天[/]: [/]")

            if user_input is None:
                if Confirm.ask("\n[bold yellow]要離開程式嗎？[/]"): break
                continue
            if user_input.lower() in ["exit", "quit"]: break

            raw_input = user_input.replace('"', '').replace("'", "")
            target_path = raw_input

            if not os.path.exists(target_path):
                check_input = os.path.join("input", target_path)
                if os.path.exists(check_input): target_path = check_input

            if os.path.exists(target_path):
                # 🖼️ 進入視覺模式
                console.print("[bold cyan]🖼️ 進入視覺模式[/]")
                target_files = []
                if os.path.isdir(target_path):
                    target_files = select_files_from_directory(target_path)
                    if not target_files: continue
                else:
                    target_files = [target_path]

                count = len(target_files)
                style_req = get_input_safe("[green]🎨 請描述風格: [/]")
                if not style_req: continue

                last_plan = None

                try:
                    iterator = track(target_files, description="修圖進度") if count > 1 else target_files

                    for img_path in iterator:
                        plan = await asyncio.to_thread(planner.generate_plan, img_path, style_req)
                        last_plan = plan

                        if plan and plan.get('selected_lut'):
                            if count == 1:
                                mix_info = f" + {plan.get('secondary_lut')} ({plan.get('mix_ratio')})" if plan.get(
                                    'secondary_lut') else ""
                                console.print(Panel(
                                    f"策略: {plan.get('style_strategy', '無')}\n"
                                    f"LUT: {plan['selected_lut']}{mix_info}\n"
                                    f"曲線: {plan.get('curve_points', 'Default')}",
                                    title="AI 煉金術決策"
                                ))

                            final_img, msg = lut_engine.apply_lut(
                                img_path,
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

                            if final_img:
                                if not os.path.exists("output"): os.makedirs("output")
                                save_path = f"output/v16_{os.path.basename(img_path)}"
                                final_img.save(save_path)
                                Logger.success(f"已儲存: {save_path}")
                        else:
                            Logger.error("AI 未生成有效計畫 (無可用 LUT)")

                    if count == 1 and last_plan and last_plan.get('selected_lut'):
                        console.print("\n[bold yellow]🤔 滿意這次的結果嗎？[/]")
                        if Confirm.ask("正向樣本 (記住風格)?"):
                            planner.learn_from_result(style_req, last_plan, 1)
                            console.print("[green]✅ 已記錄！AI 記住了這個風格參數。[/]")
                        else:
                            if Confirm.ask("負向樣本 (避雷)?"):
                                planner.learn_from_result(style_req, last_plan, -1)
                                console.print("[red]❎ 已記錄避雷針！下次會避開此設定。[/]")

                except KeyboardInterrupt:
                    Logger.warn("視覺任務已暫停")

            else:
                # 💬 進入對話模式
                if cli_chat_session is None:
                    cli_chat_session = create_chat_session()

                try:
                    with console.status("[bold magenta]🧠 Gemini 3 Pro 思考中...[/]", spinner="dots"):
                        response = await asyncio.to_thread(cli_chat_session.send_message, user_input)

                        # [Fix] 使用安全函式讀取回應
                        resp_text = get_response_text_safe(response)

                        console.print(Panel(
                            Markdown(resp_text),
                            title="🤖 Gemini 3 Pro",
                            border_style="magenta"
                        ))
                except KeyboardInterrupt:
                    Logger.warn("對話已取消")
                except Exception as e:
                    Logger.error(f"對話錯誤: {e}")

        except KeyboardInterrupt:
            console.print("\n[bold yellow]⚠️ (中斷)[/]")
            continue
        except Exception as e:
            Logger.error(f"系統崩潰攔截: {e}")
            await asyncio.sleep(1)
            continue


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bye.")