import traceback
import httpx
from fastmcp import Context, FastMCP
import textra_client

mcp = FastMCP("Textra Japanese to English Translator")

@mcp.tool("translate_ja_to_en")
async def _translate_ja_to_en_impl(text: str, ctx: Context) -> str:
    """
    Translates Japanese text to English using the Textra API.
    If the user provides instructions or questions in Japanese, use this tool first to translate the text into English before processing it with other tools or functions.

    Args:
        text: The Japanese text to translate.

    Returns:
        str: The translated English text. Returns an error message if an error occurs. Treat the returned English text as the user's original request for further processing.
    """
    try:
        # textra_client の翻訳関数を呼び出す
        translated_text = await textra_client.translate_ja_to_en(text)
        ctx.info(f"Successfully translated text: '{text}' -> '{translated_text}'")
        return translated_text
    except ValueError as e:
        # 設定値不足などの内部設定エラー
        error_message = f"Translation configuration error: {e}"
        ctx.error(f"{error_message}\n{traceback.format_exc()}")
        return f"Translation failed due to a configuration issue. Please check the server setup."
    except httpx.HTTPStatusError as e:
        # Textra APIからのエラーレスポンス
        error_message = f"Textra API error: {e.response.status_code} - {e.response.text}"
        ctx.error(f"{error_message}\n{traceback.format_exc()}")
        # クライアントには汎用的なAPIエラーメッセージを返す
        return f"Translation failed due to an API error (Status: {e.response.status_code}). Please try again later."
    except httpx.RequestError as e:
        # ネットワーク関連のエラー (接続タイムアウトなど)
        error_message = f"Network error while contacting Textra API: {e}"
        ctx.error(f"{error_message}\n{traceback.format_exc()}")
        return f"Translation failed due to a network issue. Please check your connection or try again later."
    except Exception as e:
        # その他の予期せぬ例外
        error_message = f"An unexpected error occurred during translation: {type(e).__name__}: {e}"
        ctx.error(f"{error_message}\n{traceback.format_exc()}")
        return f"An unexpected error occurred during translation. Please try again."

# サーバーを直接実行する場合のエントリーポイント
if __name__ == "__main__":
    mcp.run()
