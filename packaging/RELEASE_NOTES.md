## Snow Voice Ver 1.2 · Windows x64 Preview

**下載 `SnowVoice-Setup-v1.2-x64.exe`，雙擊安裝，不需要另外安裝 Python。**

1. 安裝完成後開啟 Snow Voice。
2. 設定自己的 OpenAI Secret Key（`sk-` 開頭）；API 用量由各使用者負擔。
3. 按住 **Ctrl + Alt + F12** 說話，放開後轉錄，完成後按 **Ctrl + V** 貼上。
4. 右下角系統匣圖示按右鍵，可以開啟設定或結束程式。

- 支援 Windows 10 / 11 x64；不需要管理員權限。
- 開機啟動、桌面捷徑為選用；預設手動貼上。
- 已安裝 Python 版者，先從系統匣結束並移除舊版，再安裝 EXE，避免舊開機項同時啟動。設定與金鑰保留。
- Windows「設定 → 應用程式」可移除；設定與金鑰會保留。
- `SHA256SUMS.txt` 提供下載檔案的 SHA-256 校驗值。
- GitHub 的 **Source code (zip)** 是原始碼，**不是安裝包**。

**測試範圍：** GitHub Windows runner 執行離線測試、打包相依套件檢查、Tkinter 視窗啟動、靜默安裝與移除。麥克風、快捷鍵、Logi Options+ 與實際 API 轉錄仍待實機確認。此版本尚未數位簽章，Windows 可能顯示 SmartScreen 提醒；請先確認下載來源。

[完整圖文教學](https://github.com/eericni/Snow-Voice#第一次使用圖文操作教學)
