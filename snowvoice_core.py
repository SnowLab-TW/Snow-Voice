"""Platform-independent validation and safe presentation helpers."""
import re


def valid_key_shape(key):
    """A local shape check only, never proof of server-side validity."""
    return bool(re.fullmatch(r"sk-[A-Za-z0-9_-]{16,}", key))


def format_transcript(text):
    """Keep ordinary punctuation; do not impose a personal ending style."""
    return text.strip()


def error_message(exc):
    status = getattr(exc, "status_code", None)
    if status == 401:
        return "API Key 驗證失敗。請確認使用完整 Secret Key，而非 Tracking ID。"
    if status == 429:
        return "API 額度或速率受限。請到 OpenAI 平台確認用量、帳務與限制。"
    if status in (400, 403, 404):
        return "請求或存取權限有問題。請確認模型名稱、金鑰權限與專案設定。"
    return "轉錄或複製失敗。請檢查網路、麥克風及剪貼簿後重試。（" + type(exc).__name__ + "）"
