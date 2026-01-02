"""
LUT 生成工具 - 創建各種風格的 .cube 濾鏡檔案
可生成：Identity、Warm、Cool、Vintage、Cinematic 等風格
"""

import os
import math


def create_identity_lut(output_path, name="Identity", size=16):
    """
    創建 Identity LUT（不改變顏色）
    這是最基本的 LUT，適合測試
    """
    with open(output_path, 'w') as f:
        f.write(f'TITLE "{name}"\n')
        f.write(f'LUT_3D_SIZE {size}\n\n')
        
        for b in range(size):
            for g in range(size):
                for r in range(size):
                    rv = r / (size - 1.0)
                    gv = g / (size - 1.0)
                    bv = b / (size - 1.0)
                    f.write(f"{rv:.6f} {gv:.6f} {bv:.6f}\n")
    
    print(f"✅ 創建完成: {output_path}")


def create_warm_lut(output_path, name="Warm_Tone", size=16):
    """
    創建暖色調 LUT
    增加紅色和黃色，減少藍色
    """
    with open(output_path, 'w') as f:
        f.write(f'TITLE "{name}"\n')
        f.write(f'LUT_3D_SIZE {size}\n\n')
        
        for b in range(size):
            for g in range(size):
                for r in range(size):
                    rv = r / (size - 1.0)
                    gv = g / (size - 1.0)
                    bv = b / (size - 1.0)
                    
                    # 暖色調調整
                    rv = min(1.0, rv * 1.15)  # 增加紅色
                    gv = min(1.0, gv * 1.05)  # 略增綠色
                    bv = bv * 0.85            # 減少藍色
                    
                    f.write(f"{rv:.6f} {gv:.6f} {bv:.6f}\n")
    
    print(f"✅ 創建完成: {output_path}")


def create_cool_lut(output_path, name="Cool_Tone", size=16):
    """
    創建冷色調 LUT
    增加藍色，減少紅色和黃色
    """
    with open(output_path, 'w') as f:
        f.write(f'TITLE "{name}"\n')
        f.write(f'LUT_3D_SIZE {size}\n\n')
        
        for b in range(size):
            for g in range(size):
                for r in range(size):
                    rv = r / (size - 1.0)
                    gv = g / (size - 1.0)
                    bv = b / (size - 1.0)
                    
                    # 冷色調調整
                    rv = rv * 0.85            # 減少紅色
                    gv = min(1.0, gv * 1.0)   # 保持綠色
                    bv = min(1.0, bv * 1.2)   # 增加藍色
                    
                    f.write(f"{rv:.6f} {gv:.6f} {bv:.6f}\n")
    
    print(f"✅ 創建完成: {output_path}")


def create_vintage_lut(output_path, name="Vintage_Film", size=16):
    """
    創建復古膠片 LUT
    降低飽和度，增加對比度，輕微褪色效果
    """
    with open(output_path, 'w') as f:
        f.write(f'TITLE "{name}"\n')
        f.write(f'LUT_3D_SIZE {size}\n\n')
        
        for b in range(size):
            for g in range(size):
                for r in range(size):
                    rv = r / (size - 1.0)
                    gv = g / (size - 1.0)
                    bv = b / (size - 1.0)
                    
                    # 轉換到亮度
                    luma = 0.299 * rv + 0.587 * gv + 0.114 * bv
                    
                    # 降低飽和度（混合原色和亮度）
                    desaturation = 0.3
                    rv = rv * (1 - desaturation) + luma * desaturation
                    gv = gv * (1 - desaturation) + luma * desaturation
                    bv = bv * (1 - desaturation) + luma * desaturation
                    
                    # 輕微褪色（提高黑階）
                    fade = 0.05
                    rv = rv * (1 - fade) + fade
                    gv = gv * (1 - fade) + fade
                    bv = bv * (1 - fade) + fade
                    
                    # 暖色調偏移
                    rv = min(1.0, rv * 1.05)
                    bv = bv * 0.95
                    
                    f.write(f"{rv:.6f} {gv:.6f} {bv:.6f}\n")
    
    print(f"✅ 創建完成: {output_path}")


def create_cinematic_lut(output_path, name="Cinematic_Teal_Orange", size=16):
    """
    創建電影感 LUT
    經典的青橙色調（Teal & Orange）
    """
    with open(output_path, 'w') as f:
        f.write(f'TITLE "{name}"\n')
        f.write(f'LUT_3D_SIZE {size}\n\n')
        
        for b in range(size):
            for g in range(size):
                for r in range(size):
                    rv = r / (size - 1.0)
                    gv = g / (size - 1.0)
                    bv = b / (size - 1.0)
                    
                    # 計算亮度
                    luma = 0.299 * rv + 0.587 * gv + 0.114 * bv
                    
                    # 青橙色調調整
                    if luma > 0.5:  # 亮部偏橙色
                        rv = min(1.0, rv * 1.1)
                        gv = min(1.0, gv * 1.05)
                        bv = bv * 0.9
                    else:  # 暗部偏青色
                        rv = rv * 0.9
                        gv = min(1.0, gv * 1.05)
                        bv = min(1.0, bv * 1.15)
                    
                    # 增加對比度
                    contrast = 1.1
                    rv = ((rv - 0.5) * contrast + 0.5)
                    gv = ((gv - 0.5) * contrast + 0.5)
                    bv = ((bv - 0.5) * contrast + 0.5)
                    
                    # 確保在 0-1 範圍內
                    rv = max(0.0, min(1.0, rv))
                    gv = max(0.0, min(1.0, gv))
                    bv = max(0.0, min(1.0, bv))
                    
                    f.write(f"{rv:.6f} {gv:.6f} {bv:.6f}\n")
    
    print(f"✅ 創建完成: {output_path}")


def create_high_contrast_bw_lut(output_path, name="High_Contrast_BW", size=16):
    """
    創建高對比黑白 LUT
    """
    with open(output_path, 'w') as f:
        f.write(f'TITLE "{name}"\n')
        f.write(f'LUT_3D_SIZE {size}\n\n')
        
        for b in range(size):
            for g in range(size):
                for r in range(size):
                    rv = r / (size - 1.0)
                    gv = g / (size - 1.0)
                    bv = b / (size - 1.0)
                    
                    # 轉換為灰階
                    gray = 0.299 * rv + 0.587 * gv + 0.114 * bv
                    
                    # 增強對比度
                    contrast = 1.3
                    gray = ((gray - 0.5) * contrast + 0.5)
                    gray = max(0.0, min(1.0, gray))
                    
                    # S 曲線調整（增加對比）
                    if gray < 0.5:
                        gray = gray * gray * 2
                    else:
                        gray = 1 - (1 - gray) * (1 - gray) * 2
                    
                    f.write(f"{gray:.6f} {gray:.6f} {gray:.6f}\n")
    
    print(f"✅ 創建完成: {output_path}")


def create_fuji_classic_chrome_lut(output_path, name="Fuji_Classic_Chrome", size=16):
    """
    模擬 Fujifilm Classic Chrome 風格
    特色：降低飽和度、增加對比、柔和色調
    """
    with open(output_path, 'w') as f:
        f.write(f'TITLE "{name}"\n')
        f.write(f'LUT_3D_SIZE {size}\n\n')
        
        for b in range(size):
            for g in range(size):
                for r in range(size):
                    rv = r / (size - 1.0)
                    gv = g / (size - 1.0)
                    bv = b / (size - 1.0)
                    
                    # 轉換到亮度
                    luma = 0.299 * rv + 0.587 * gv + 0.114 * bv
                    
                    # Classic Chrome 特色：降低飽和度
                    desaturation = 0.25
                    rv = rv * (1 - desaturation) + luma * desaturation
                    gv = gv * (1 - desaturation) + luma * desaturation
                    bv = bv * (1 - desaturation) + luma * desaturation
                    
                    # 輕微偏綠色調（Chrome 特色）
                    gv = min(1.0, gv * 1.03)
                    
                    # 增加對比度
                    contrast = 1.15
                    rv = ((rv - 0.5) * contrast + 0.5)
                    gv = ((gv - 0.5) * contrast + 0.5)
                    bv = ((bv - 0.5) * contrast + 0.5)
                    
                    # 柔和高光（降低白階）
                    if luma > 0.7:
                        factor = (luma - 0.7) / 0.3
                        rv = rv * (1 - factor * 0.1)
                        gv = gv * (1 - factor * 0.1)
                        bv = bv * (1 - factor * 0.1)
                    
                    # 確保範圍
                    rv = max(0.0, min(1.0, rv))
                    gv = max(0.0, min(1.0, gv))
                    bv = max(0.0, min(1.0, bv))
                    
                    f.write(f"{rv:.6f} {gv:.6f} {bv:.6f}\n")
    
    print(f"✅ 創建完成: {output_path}")


def create_all_sample_luts(output_dir="luts"):
    """
    一次性創建所有範例 LUT
    """
    # 確保輸出目錄存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"📁 創建目錄: {output_dir}")
    
    print("\n🎨 開始生成範例 LUT 檔案...\n")
    
    # 創建各種 LUT
    create_identity_lut(os.path.join(output_dir, "Identity.cube"))
    create_warm_lut(os.path.join(output_dir, "Warm_Tone.cube"))
    create_cool_lut(os.path.join(output_dir, "Cool_Tone.cube"))
    create_vintage_lut(os.path.join(output_dir, "Vintage_Film.cube"))
    create_cinematic_lut(os.path.join(output_dir, "Cinematic_Teal_Orange.cube"))
    create_high_contrast_bw_lut(os.path.join(output_dir, "High_Contrast_BW.cube"))
    create_fuji_classic_chrome_lut(os.path.join(output_dir, "Fuji_Classic_Chrome.cube"))
    
    print(f"\n🎉 完成！共生成 7 個 LUT 檔案於 {output_dir}/ 資料夾")
    print("\n可用的 LUT:")
    print("  1. Identity.cube - 原始色彩（測試用）")
    print("  2. Warm_Tone.cube - 暖色調")
    print("  3. Cool_Tone.cube - 冷色調")
    print("  4. Vintage_Film.cube - 復古膠片")
    print("  5. Cinematic_Teal_Orange.cube - 電影感青橙")
    print("  6. High_Contrast_BW.cube - 高對比黑白")
    print("  7. Fuji_Classic_Chrome.cube - Fuji 經典鉻片")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # 指定輸出目錄
        output_dir = sys.argv[1]
        create_all_sample_luts(output_dir)
    else:
        # 預設目錄
        create_all_sample_luts()
