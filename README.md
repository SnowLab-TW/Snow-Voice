# Snow Lab

## SnowVoice Ver 1.2 🎙️

Windows push-to-talk dictation for Traditional Chinese (Taiwan).

按住 **Ctrl + Alt + F12** 錄音 → 放開後送至 OpenAI → 複製文字 → **Ctrl + V** 貼上。

**Preview：尚待 Windows 實機驗收。** 目前提供 Python 原始碼與安裝器，沒有簽章 EXE。

## Ver 1.2 功能

- 空白詞庫，移除個人與公司預設詞彙、私人圖像及舊版資料移轉。
- 保留正常句尾標點、系統匣、繁中轉換與自訂詞庫。
- 獨立設定、金鑰、安裝目錄與開機啟動項。
- 預設只複製；自動貼上須自行啟用，前景視窗改變時跳過貼上。
- 每次錄音最長約 120 秒，API timeout 設為 60 秒，不自動重試。

## 安裝（Windows 10 / 11）

1. 安裝 [Python](https://www.python.org/downloads/windows/) 3.11 以上，包含 Launcher、pip、Tkinter。
2. 下載儲存庫 ZIP 並**完整解壓縮**。
3. 雙擊 `install.bat`。需要網路，依賴從 PyPI 安裝。
4. 在設定視窗填入自己的 OpenAI **Secret Key**（`sk-` 開頭），不要填 `key_` Tracking ID。
5. 在 Windows 隱私設定允許桌面應用程式使用麥克風。
6. 按住快捷鍵說話，放開後稍候，完成後手動貼上。

不需要管理員權限。程式與獨立虛擬環境位於 `%LOCALAPPDATA%\SnowVoicePure\App`。

預設不新增開機啟動；需要時可在解壓縮資料夾執行：

```bat
install.bat --startup
```

用 `start_snowvoice.bat` 開啟設定。關閉設定只會隱藏，請從系統匣選「結束」關閉。
更新前先關閉此版本，再重新安裝。此版本與原版**快捷鍵相同，請勿同時執行**。

內部儲存識別沿用 `SnowVoicePure`，以相容先前安裝的設定與金鑰。

## API、費用與資料

- 需要自己的 [OpenAI API 帳號與額度](https://platform.openai.com/)。ChatGPT 訂閱不包含此工具的 API 費用。
- 預設模型 `gpt-transcribe`；設定欄可輸入其他有權使用的轉錄模型，見 [官方文件](https://developers.openai.com/api/docs/guides/speech-to-text)。
- 錄音與自訂詞彙傳送至 `https://api.openai.com/v1/audio/transcriptions`；不是離線辨識。
- 金鑰由 `keyring` 儲存至 Windows Credential Manager，服務 `SnowVoicePure_OpenAI`、使用者 `default`。
- 「已儲存」僅表示本機保存，並不表示已通過線上驗證；此專案不附帶任何金鑰。
- 設定和精簡日誌位於 `%APPDATA%\SnowVoicePure`，不主動記錄逐字稿或完整 API 錯誤回應。
- WAV 位於系統暫存資料夾；轉錄完成或失敗後會嘗試刪除，強制結束與斷電可能留下檔案。
- 成功後會取代剪貼簿內容，也可能進入系統的剪貼簿歷程。

## 移除

從**解壓縮的下載資料夾**執行 `uninstall_snowvoice.bat`。只移除此版本程式與開機項，保留設定及金鑰。
完整清除時，自行刪除 `%APPDATA%\SnowVoicePure`，並從 Windows「認證管理員」刪除 `SnowVoicePure_OpenAI` 對應項目。

## 開發與驗收

```bat
python -m unittest discover -s tests -v
python -m compileall -q .
```

離線測試不需要金鑰，不呼叫 API。GitHub Actions 在 Windows 執行語法和離線測試。
依賴指定最低版本，尚未提供鎖定檔，實際安裝版本可能隨 PyPI 更新。

待 Windows 實機確認：

- [ ] 首次安裝、重裝、系統匣與設定保存。
- [ ] 麥克風、快捷鍵、120 秒錄音上限。
- [ ] 實際轉錄與無效金鑰、斷線、用量限制。
- [ ] 手動貼上、自動貼上、切換視窗與系統管理員視窗。
- [ ] 開機啟動與解除安裝。

自動貼上只檢查前景視窗，不能確認同一視窗內的游標，也不能完全排除檢查後切換視窗的競態；手動貼上是預設。

## 授權

目前尚未指定開源授權。公開可見不代表允許自由再散布；確定授權後再加入 LICENSE。
