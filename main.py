import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import track

# 匯入 v17 核心
from core.style_engine import StyleEngine  # 改用 StyleEngine
from core.logic_planner import LogicPlanner
from core.logger import Logger

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

console = Console()
Logger.info("正在啟動 v17 Pure Math Edition (No LUTs)...")

# 初始化
style_engine = StyleEngine()
planner = LogicPlanner(style_engine)


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


def main():
    console.clear()
    console.print(Panel.fit("[bold magenta]✨ v17 Pure Math (參數化運算版)[/]", border_style="magenta"))

    while True:
        try:
            console.print("\n[dim]──────────────────────────────────────────────────[/]")
            user_input = get_input_safe("[yellow]請輸入 [bold white]圖片路徑[/] (輸入 q 離開): [/]")

            if user_input is None or user_input.lower() in ["exit", "quit", "q"]:
                break

            target_path = user_input.replace('"', '').replace("'", "")
            if not os.path.exists(target_path):
                check_input = os.path.join("input", target_path)
                if os.path.exists(check_input):
                    target_path = check_input
                else:
                    Logger.error("找不到路徑")
                    continue

            target_files = []
            if os.path.isdir(target_path):
                target_files = select_files_from_directory(target_path)
                if not target_files: continue
            else:
                target_files = [target_path]

            count = len(target_files)
            style_req = get_input_safe("[green]🎨 請輸入關鍵字 (如: 日系, 柯達, 賽博, 黑白): [/]")
            if not style_req: continue

            try:
                iterator = track(target_files, description="⚡ 數學運算中...") if count > 1 else target_files

                for img_path in iterator:
                    # 1. 邏輯決策
                    plan = planner.generate_plan(img_path, style_req)

                    # 2. 執行數學引擎
                    # 注意：這裡的參數傳遞方式變了
                    final_img, msg = style_engine.apply_style(
                        img_path,
                        style_name=plan['selected_style'],
                        intensity=plan['intensity'],
                        # 傳遞動態修正參數 (Overrides)
                        brightness=plan.get('brightness'),
                        contrast=plan.get('contrast'),
                        temp=plan.get('temperature')
                    )

                    if final_img:
                        if not os.path.exists("output"): os.makedirs("output")
                        save_path = f"output/v17_{os.path.basename(img_path)}"
                        final_img.save(save_path)

                        if count == 1:
                            console.print(Panel(
                                f"風格: {plan['selected_style']}\n"
                                f"修正: Bright {plan.get('brightness')} / Temp {plan.get('temperature')}",
                                title="v17 運算結果"
                            ))
                            Logger.success(f"已儲存: {save_path}")
                    else:
                        Logger.error(f"運算失敗: {msg}")

            except KeyboardInterrupt:
                Logger.warn("任務已暫停")

        except KeyboardInterrupt:
            break
        except Exception as e:
            Logger.error(f"未預期錯誤: {e}")
            continue


if __name__ == "__main__":
    main()