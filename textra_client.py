import asyncio
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
from config import settings
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

_access_token: str | None = None
_token_expires_at: float = 0.0

async def get_access_token() -> str:
    """Textra API のアクセストークンを取得またはキャッシュから返します。

    キャッシュが存在し、有効期限内であればキャッシュを返します。
    それ以外の場合はAPIから取得し、キャッシュを更新します。

    Returns:
        str: アクセストークン。

    Raises:
        ValueError: 設定値 (`TEXTRA_API_KEY`, `TEXTRA_API_SECRET`, `TEXTRA_TOKEN_URL`) が不足している場合。
        Exception: APIからのトークン取得に失敗した場合。
    """
    global _access_token, _token_expires_at

    current_time = asyncio.get_running_loop().time()

    if _access_token and current_time < _token_expires_at:
        logger.info(f"Using cached access token (valid until {_token_expires_at:.0f}).")
        return _access_token

    logger.info("Cached token expired or not found. Fetching new token...")

    if not all([settings.TEXTRA_API_KEY, settings.TEXTRA_API_SECRET, settings.TEXTRA_TOKEN_URL]):
        logger.error("API Key, Secret, or Token URL is not configured.")
        raise ValueError("API Key, Secret, or Token URL must be configured.")

    def _fetch_token_sync():
        """同期的にトークンを取得するヘルパー関数"""
        try:
            client = BackendApplicationClient(client_id=settings.TEXTRA_API_KEY)
            oauth = OAuth2Session(client=client)
            token_data = oauth.fetch_token(
                token_url=settings.TEXTRA_TOKEN_URL,
                client_id=settings.TEXTRA_API_KEY,
                client_secret=settings.TEXTRA_API_SECRET
            )
            return token_data
        except Exception as sync_e:
            logger.error(f"Error in _fetch_token_sync: {sync_e}", exc_info=True)
            raise sync_e

    try:
        token_data = await asyncio.to_thread(_fetch_token_sync)

        _access_token = token_data.get('access_token')
        expires_in = token_data.get('expires_in', 3600)
        _token_expires_at = current_time + expires_in - 60

        if not _access_token:
            logger.error("Failed to retrieve access token from response.")
            raise Exception("Failed to retrieve access token from response.")

        logger.info(f"Successfully obtained new access token. Expires around: {_token_expires_at}")
        return _access_token

    except Exception as e:
        logger.error(f"Error fetching access token: {e}", exc_info=True)
        _access_token = None
        _token_expires_at = 0.0
        # 例外を連鎖させるために 'from e' を使用
        raise Exception(f"Failed to fetch access token: {e}") from e

async def translate_ja_to_en(text: str) -> str:
    """日本語テキストを英語に翻訳します。

    内部で `get_access_token` を呼び出して認証を行い、Textra翻訳APIにリクエストを送信します。
    `requests` ライブラリを使用するため、非同期実行には `asyncio.to_thread` を使用します。

    Args:
        text: 翻訳する日本語テキスト。

    Returns:
        str: 翻訳された英語テキスト。

    Raises:
        ValueError: 設定値 (`TEXTRA_JA_EN_API_URL`, `TEXTRA_USER_NAME`, `TEXTRA_API_KEY`) が不足している場合。
        Exception: アクセストークンの取得失敗、ネットワークエラー、または翻訳API自体のエラーが発生した場合。
    """
    import requests

    if not all([settings.TEXTRA_JA_EN_API_URL, settings.TEXTRA_USER_NAME, settings.TEXTRA_API_KEY]):
        logger.error("API URL, User Name, or API Key is not configured.")
        raise ValueError("API URL, User Name, and API Key must be configured.")
    
    try:
        access_token = await get_access_token()
        
        params = {
            'access_token': access_token,
            'key': settings.TEXTRA_API_KEY,
            'name': settings.TEXTRA_USER_NAME,
            'type': 'json',
            'text': text
        }
        
        logger.info(f"Sending translation request to {settings.TEXTRA_JA_EN_API_URL}")
        
        response = await asyncio.to_thread(
            requests.post,
            settings.TEXTRA_JA_EN_API_URL,
            data=params
        )

        response_data = response.json()
        logger.info(f"Received API response data: {response_data}")

        resultset = response_data.get('resultset', {})
        result_code = resultset.get('code')
        logger.info(f"API result code: {result_code} (type: {type(result_code)})")

        if str(result_code) != '0':
            error_message = resultset.get('message', 'Unknown error')
            logger.error(f"Translation API error: {error_message} (code: {result_code})")
            raise Exception(f"Translation API error: {error_message} (code: {result_code})")

        result = resultset.get('result', {})
        translated_text = result.get('text', '')

        if not translated_text:
            logger.warning("Translation result is empty")
        else:
            logger.info("Translation successful")
            
        return translated_text
        
    except Exception as e:
        if isinstance(e, requests.exceptions.RequestException):
            logger.error(f"Network error during translation: {e}", exc_info=True)
            raise Exception(f"Network error during translation: {e}")
        elif "Translation API error" in str(e):
            raise
        else:
            logger.error(f"Error during translation: {e}", exc_info=True)
            raise Exception(f"Error during translation: {e}")
