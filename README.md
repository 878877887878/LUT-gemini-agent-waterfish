# Gemini Windows Agent v3.0 - 完整使用指南

## 🚀 全新功能

### 1. AI 自我更新系統 🤖
Agent 現在可以修改自己的源碼！

**核心能力：**
- ✅ AI 分析並修改程式碼
- ✅ 自動建立備份保護
- ✅ Git 版本控制整合
- ✅ 可還原到任何歷史版本

**使用範例：**
```
User: 幫我加入一個新功能：支援批次重新命名檔案
AI: [分析當前程式碼]
    [生成修改後的程式碼]
    程式碼修改摘要:
      原始長度: 28000 字元
      修改後長度: 29500 字元
      變化: +1500 字元
    
    是否確認套用此更新？ [y/N]

User: y
AI: ✅ 更新成功！備份於: backups/backup_v3.0.0_20260102_120530_user_request.py
    請重新啟動程式以套用變更。
```

---

### 2. 多重 LUT 濾鏡系統 🎨
支援各大相機廠牌的專業調色風格！

**支援的品牌：**
- 📷 **Fujifilm** - Classic Chrome, Pro Neg, Velvia 等電影模擬
- 📷 **Sony** - S-Gamut3.Cine, S-Log3 等創意風格
- 📷 **Canon** - Neutral, Cinema 等色彩風格
- 🎨 **免費精選包** - Vintage, Cinematic, Black & White

**LUT 管理功能：**
```python
# 1. 查看 LUT 資料庫
User: 顯示所有可用的 LUT
AI: [顯示完整的 LUT 樹狀結構]

# 2. 下載特定廠牌的 LUT
User: 下載 Fujifilm 的所有濾鏡
AI: 📥 開始下載 Fujifilm 電影模擬 系列...
    ✅ Fuji_Classic_Chrome 下載完成
    ✅ Fuji_Pro_Neg_Std 下載完成
    ✅ Fuji_Velvia 下載完成
    ✅ 成功: 3 | ❌ 失敗: 0

# 3. 選擇要使用的 LUT
User: 我要用 Fuji Classic Chrome 濾鏡
AI: ✅ 已選擇 LUT: Fuji_Classic_Chrome.cube

# 4. 套用 LUT 處理照片
User: 用這個濾鏡處理 input 資料夾的照片
AI: 🎨 開始批次處理 'input' 資料夾...
    🎨 使用濾鏡: Fuji_Classic_Chrome.cube
    [處理過程...]
```

---

### 3. Git 版本控制整合 📦
完整的版本管理系統

**功能：**
- 初始化 Git 倉庫
- 自動提交變更
- 查看歷史日誌
- 檢查文件狀態

**使用範例：**
```
User: 初始化 Git 倉庫
AI: ✅ Git 倉庫初始化成功

User: 提交所有變更，訊息是：新增 LUT 管理功能
AI: ✅ 變更已提交

User: 顯示 Git 日誌
AI: Git 日誌:
    a1b2c3d AI update: 新增 LUT 管理功能
    d4e5f6g Initial commit
```

---

## 📦 安裝指南

### 必要套件
```bash
pip install pillow pillow-lut google-generativeai python-dotenv rich requests
```

### 資料夾結構
```
your_project/
├── gemini_agent_v3_advanced.py  # 主程式
├── .env                          # API Key
├── version.json                  # 版本資訊（自動生成）
├── input/                        # 要處理的照片
├── output/                       # 處理結果
├── luts/                         # LUT 濾鏡庫（自動生成）
└── backups/                      # 程式碼備份（自動生成）
```

---

## 🎯 功能詳解

### 功能 1: AI 自我更新

#### 如何使用
```
User: 幫我加入一個新功能：[描述功能]
User: 優化現有的照片處理速度
User: 修正某個 bug：[描述問題]
```

#### 運作流程
1. 🧠 AI 分析當前程式碼
2. ✍️ AI 生成修改後的完整程式碼
3. 📊 顯示修改摘要
4. 🤔 詢問使用者確認
5. 💾 建立自動備份
6. ✅ 套用更新
7. 📝 記錄到 Git（如果有）

#### 安全機制
- ✅ 每次更新前自動備份
- ✅ 需要使用者明確確認
- ✅ 完整的版本歷史記錄
- ✅ 可隨時還原到任何版本

---

### 功能 2: LUT 濾鏡管理

#### 2.1 查看 LUT 資料庫
```
User: 顯示 LUT 資料庫
User: 有哪些濾鏡可以用
```

輸出範例：
```
🎨 LUT 濾鏡資料庫
├── 💾 本地 LUT (5)
│   ├── Fuji_Classic_Chrome.cube ← 當前使用
│   ├── Fuji_Pro_Neg_Std.cube
│   ├── Sony_SGamut3Cine.cube
│   ├── Vintage_Warm.cube
│   └── Cinematic_Teal.cube
└── ☁️ 可下載的 LUT
    ├── Fujifilm 電影模擬 (3)
    │   ├── Fuji_Classic_Chrome
    │   ├── Fuji_Pro_Neg_Std
    │   └── Fuji_Velvia
    ├── Sony 創意風格 (2)
    ├── Canon 色彩風格 (2)
    └── 免費精選包 (3)
```

#### 2.2 下載 LUT
```
# 下載整個廠牌系列
User: 下載 Fujifilm 的 LUT
User: 我要 Sony 的所有濾鏡

# 下載免費包
User: 下載免費精選包
```

#### 2.3 選擇 LUT
```
# 方式 1: 直接指定
User: 使用 Fuji_Classic_Chrome 濾鏡

# 方式 2: 自然語言
User: 我想要復古的感覺
AI: [自動選擇 Vintage_Warm.cube]

# 方式 3: 互動選擇
User: 選擇濾鏡
AI: 可用的 LUT 濾鏡:
    1. Fuji_Classic_Chrome.cube
    2. Sony_SGamut3Cine.cube
    3. Vintage_Warm.cube
    請選擇 LUT 編號: 
```

#### 2.4 處理照片時指定 LUT
```
User: 用 Fuji Classic Chrome 處理照片
User: 套用電影感的濾鏡處理 input 資料夾
User: 幫我的旅遊照片加上復古風格
```

---

### 功能 3: 版本控制

#### 3.1 查看版本資訊
```
User: 顯示版本資訊
User: 我的程式更新過幾次

輸出：
📦 Gemini Agent v3.0.0
├── ℹ️ 版本資訊
│   ├── 當前版本: 3.0.0
│   ├── 最後更新: 2026-01-02T12:05:30
│   └── 更新次數: 5
├── 📜 更新歷史
│   ├── 2026-01-02 12:05:30 - 新增 LUT 管理功能
│   ├── 2026-01-02 11:30:15 - AI 自我更新系統
│   └── 2026-01-02 10:00:00 - 初始版本
└── 💾 備份檔案 (5)
    ├── backup_v3.0.0_20260102_120530_user_request.py
    └── backup_v3.0.0_20260102_113015_ai_update.py
```

#### 3.2 建立備份
```
User: 建立備份
User: 先備份一下當前版本
```

#### 3.3 還原備份
```
# 列出備份
User: 顯示所有備份

# 還原特定備份
User: 還原到 backup_v3.0.0_20260102_120530_user_request.py
```

#### 3.4 Git 操作
```
# 初始化
User: 初始化 Git 倉庫

# 提交變更
User: 提交變更，訊息：新增批次重命名功能

# 查看日誌
User: 顯示 Git 日誌

# 查看狀態
User: 檢查 Git 狀態
```

---

## 💡 實用案例

### 案例 1: 批次處理旅遊照片
```
User: 下載 Fujifilm 的 LUT
AI: ✅ 下載完成

User: 我想要日系膠片的感覺
AI: ✅ 已選擇 LUT: Fuji_Classic_Chrome.cube

User: 處理 input 資料夾的照片
AI: 🎨 開始處理...
    ✅ 10 張照片處理完成
    🎨 使用濾鏡: Fuji_Classic_Chrome.cube
    📄 報告已生成
```

### 案例 2: AI 自動優化程式
```
User: 我覺得照片處理太慢了，能優化一下嗎？
AI: 🤖 開始分析程式碼...
    我發現可以通過以下方式優化：
    1. 使用多線程處理
    2. 預先載入 LUT 到記憶體
    3. 批次處理 API 請求
    
    是否確認套用此更新？

User: 確認
AI: ✅ 更新成功！預期速度提升 40%
    請重新啟動程式
```

### 案例 3: 建立自訂工作流程
```
User: 幫我加入一個新命令：/quick-process
     功能是：快速用預設 LUT 處理照片，不需要每次都選擇

AI: 🤖 理解您的需求，開始修改...
    將新增 quick_process() 函數
    並整合到 AI 工具列表中
    
    是否確認？

User: 確認
AI: ✅ 完成！現在可以使用：
    User: /quick-process
    來快速處理照片
```

---

## ⚙️ 進階設定

### 自訂 LUT 來源
編輯程式中的 `LUT_SOURCES` 字典：
```python
LUT_SOURCES = {
    "my_custom": {
        "name": "我的自訂濾鏡包",
        "luts": [
            {"name": "My_Custom_LUT", "url": "https://your-url.com/lut.cube"},
        ]
    }
}
```

### 調整 AI 更新安全性
```python
# 在 self_update_code() 函數中
# 預設需要使用者確認
if Confirm.ask("是否確認套用此更新？", default=False):
    # 改為 default=True 以減少確認步驟（不建議）
```

### 更改備份策略
```python
# 在 VersionManager 類別中調整
def create_backup(self, reason="manual"):
    # 自訂備份命名規則
    # 自訂備份保留天數
    pass
```

---

## 🔧 疑難排解

### 問題 1: LUT 下載失敗
**原因：** 示例 URL 需替換為真實 LUT 下載連結

**解決方案：**
1. 從以下網站獲取真實 LUT：
   - https://www.rocketstock.com/free-luts/
   - https://filtergrade.com/free-luts/
   - https://luts.iwltbap.com/

2. 更新 `LUT_SOURCES` 中的 URL

3. 或者手動將 `.cube` 檔案放入 `luts/` 資料夾

### 問題 2: AI 更新後程式無法運行
**解決方案：**
```
User: 還原到上一個備份
AI: [顯示備份列表]

User: 還原到 backup_v3.0.0_[最新時間].py
AI: ✅ 已還原，請重新啟動
```

### 問題 3: Git 功能不可用
**原因：** 未安裝 Git

**解決方案：**
1. 下載 Git: https://git-scm.com/downloads
2. 安裝後重新啟動終端機
3. 執行：`User: 初始化 Git 倉庫`

### 問題 4: LUT 效果不明顯
**原因：** 某些 LUT 是為特定色彩空間設計

**解決方案：**
- 嘗試不同的 LUT
- 確保照片是 RGB 格式
- 使用專為攝影設計的 LUT（非影片 Log LUT）

---

## 📊 效能基準

### 處理速度（含 LUT）
- 單張照片（2MB）：~10 秒
- 10 張照片：~100 秒
- 100 張照片：~1000 秒（約 17 分鐘）

### LUT 效能
- 第一次載入：~1 秒
- 快取載入：<0.1 秒
- 套用到圖片：~0.5 秒

### AI 更新效能
- 程式碼分析：~10 秒
- 生成修改：~15 秒
- 總計：~25 秒

---

## 🔐 安全性

### 自我更新安全機制
1. ✅ 所有更新前自動備份
2. ✅ 需要使用者明確確認
3. ✅ AI 無法執行危險系統指令
4. ✅ 版本歷史完整記錄
5. ✅ 可隨時還原

### 系統指令安全
- 危險指令黑名單
- 30 秒超時保護
- 拒絕刪除、格式化等操作

---

## 🚀 未來規劃

v3.1 可能功能：
- [ ] 自動從線上 LUT 商店下載
- [ ] LUT 效果即時預覽
- [ ] 自訂 LUT 強度調整
- [ ] 影片濾鏡套用
- [ ] AI 推薦最適合的 LUT
- [ ] 雲端同步 LUT 庫
- [ ] 批次比較不同 LUT 效果

---

## 📞 技術支援

遇到問題？
1. 查看本文件的疑難排解章節
2. 檢查 `version.json` 查看更新歷史
3. 使用 `User: 顯示版本資訊` 診斷
4. 還原到最近的備份

---

## 📜 更新日誌

### v3.0.0 (2026-01-02)
- ✨ **重大更新** - AI 自我更新系統
- ✨ **重大更新** - 多重 LUT 濾鏡管理
- ✨ 新增 Git 版本控制整合
- ✨ 新增自動備份系統
- ✨ LUT 快取機制
- 🎨 改進的 UI 介面
- 📊 增強的 HTML 報告

### v2.0.0
- 智能重試機制
- 動態延遲系統
- Rich 進度條
- HTML 報告生成

### v1.0.0
- 基本照片處理
- AI 文案生成
- 系統指令執行

---

**享受 v3.0 的強大功能！** 🎉

如有任何問題或建議，請使用 AI 自我更新功能不斷改進程式！
