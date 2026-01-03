import os
import sys
import asyncio
import time
import subprocess
import google.generativeai as genai
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.markdown import Markdown
from rich.progress import track

# 匯入 v5 核心模組
from core.lut_engine import LUTEngine
from core.rag_core import KnowledgeBase
from core.smart_planner import SmartPlanner

# ==========================================
# 🔧 系統設定與編碼修正
# ==========================================
# 強制 Windows 使用 UTF-8，避免輸出中文時崩潰
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
    console.print("[red]❌ 錯誤: 請在 .env 設定 GEMINI_API_KEY[/]")
    sys.exit(1)


# ==========================================
# 🔧 工具函式
# ==========================================
def execute_terminal_command(command: str):
    """執行 Windows 終端機指令"""
    try:
        console.print(f"[dim]💻 正在執行: {command}[/]")
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8'  # 防止中文亂碼
        )
        if result.returncode == 0:
            return f"✅ 執行成功:\n{result.stdout}"
        else:
            return f"❌ 執行失敗:\n{result.stderr}"
    except Exception as e:
        return f"⚠️ 系統錯誤: {str(e)}"


def create_chat_session():
    """建立對話 Session"""
    genai.configure(api_key=API_KEY)
    tools = [execute_terminal_command]
    model = genai.GenerativeModel(
        model_name='gemini-3-pro-preview',
        tools=tools,
        system_instruction="""
        你是一個強大的 AI 助理 (Gemini 3 Pro)。
        1. 如果使用者輸入路徑或要求修圖，請引導他們使用圖片模式。
        2. 如果使用者輸入系統指令（如 git, dir, mkdir），請使用 execute_terminal_command 工具執行。
        3. 回答請簡潔有力，使用繁體中文。
        """
    )
    return model.start_chat(enable_automatic_function_calling=True)


def get_input_safe(prompt_text):
    """安全輸入，防止 Ctrl+C 崩潰"""
    while True:
        try:
            user_in = console.input(prompt_text)
            if not user_in.strip(): continue
            return user_in.strip()
        except (KeyboardInterrupt, EOFError):
            return None


def select_files_from_directory(dir_path):
    """資料夾選單"""
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


# ==========================================
# 🚀 主程式 (不死鳥版)
# ==========================================
async def main():
    console.clear()
    console.print(Panel.fit("[bold cyan]🤖 Gemini Agent v7 (Bulletproof)[/]", border_style="cyan"))

    # 1. 初始化
    with console.status("[bold green]正在啟動系統...[/]"):
        try:
            engine = LUTEngine()
            rag = KnowledgeBase()
            planner = SmartPlanner(API_KEY, rag)
            all_luts = engine.list_luts()
            if all_luts: rag.index_luts(all_luts)
            chat_session = create_chat_session()
        except KeyboardInterrupt:
            return

    console.print(f"[dim]✅ 系統就緒：已載入 {len(all_luts)} 個濾鏡 | 雙核大腦已連線[/]\n")

    while True:
        # [保護層 1] 全局錯誤攔截：確保 loop 永遠不會因為 Exception 而停止
        try:
            console.print("\n[dim]──────────────────────────────────────────────────[/]")
            user_input = get_input_safe("[yellow]請輸入 [bold white]圖片路徑[/] 或 [bold white]指令/聊天[/]: [/]")

            # 處理 Ctrl+C (回傳 None)
            if user_input is None:
                if Confirm.ask("\n[bold yellow]要離開程式嗎？[/]"): break
                continue  # 否則回到開頭

            if user_input.lower() in ["exit", "quit"]: break

            # 處理路徑
            raw_input = user_input.replace('"', '').replace("'", "")
            target_path = raw_input
            if not os.path.exists(target_path):
                check_input = os.path.join("input", target_path)
                if os.path.exists(check_input): target_path = check_input

            # 🔀 分流邏輯
            if os.path.exists(target_path):
                # === 🖼️ 視覺模式 ===
                console.print("[bold cyan]🖼️ 偵測到圖片，進入視覺模式[/]")
                target_files = []
                if os.path.isdir(target_path):
                    target_files = select_files_from_directory(target_path)
                    if not target_files: continue
                else:
                    target_files = [target_path]

                count = len(target_files)
                style_req = get_input_safe("[green]🎨 請描述風格: [/]")
                if not style_req: continue  # 如果按 Ctrl+C 取消風格輸入，回到主選單

                console.print(f"\n[bold cyan]🚀 Smart Planner 思考中... (按 Ctrl+C 可中斷)[/]")
                try:
                    iterator = track(target_files, description="修圖進度") if count > 1 else target_files
                    for img_path in iterator:
                        plan = await asyncio.to_thread(planner.generate_plan, img_path, style_req)

                        if plan and plan.get('selected_lut'):
                            if count == 1:
                                console.print(
                                    Panel(f"策略: {plan['reasoning']}\nLUT: {plan['selected_lut']}", title="AI 決策"))

                            final_img, msg = engine.apply_lut(img_path, plan['selected_lut'],
                                                              plan.get('intensity', 1.0))
                            if final_img:
                                if not os.path.exists("output"): os.makedirs("output")
                                save_path = f"output/v6_{os.path.basename(img_path)}"
                                final_img.save(save_path)
                                console.print(f"   [green]✅ 儲存: {save_path}[/]")
                except KeyboardInterrupt:
                    console.print("\n[bold yellow]🛑 視覺任務已暫停，回到主選單[/]")

            else:
                # === 💬 對話模式 ===
                try:
                    with console.status("[bold magenta]🧠 Gemini 思考中... (按 Ctrl+C 可中斷)[/]", spinner="dots"):
                        # 使用 wait_for 讓 task 可以被取消
                        task = asyncio.create_task(asyncio.to_thread(chat_session.send_message, user_input))
                        try:
                            response = await task
                            console.print(Panel(
                                Markdown(response.text),
                                title="🤖 Gemini Assistant",
                                border_style="magenta"
                            ))
                        except asyncio.CancelledError:
                            raise KeyboardInterrupt  # 轉拋給外層

                except KeyboardInterrupt:
                    console.print("\n[bold yellow]🛑 對話已取消[/]")
                except Exception as e:
                    console.print(f"[red]❌ 對話發生錯誤: {e}[/]")

        except KeyboardInterrupt:
            # 這是最後一道防線，捕捉所有未預期的 Ctrl+C
            console.print("\n[bold yellow]⚠️ (已攔截中斷訊號) 回到主選單...[/]")
            continue

        except Exception as e:
            # [關鍵] 捕捉所有崩潰，讓程式活下去！
            console.print(f"\n[bold red]💥 發生未預期的系統錯誤: {e}[/]")
            console.print("[dim]系統正在自動恢復，請稍候...[/]")
            await asyncio.sleep(1)  # 休息一下避免無窮迴圈刷屏
            continue


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程式結束。")