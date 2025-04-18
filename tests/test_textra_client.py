import pytest
from unittest.mock import AsyncMock, patch
import asyncio
from oauthlib.oauth2.rfc6749.errors import OAuth2Error, InsecureTransportError
from requests.exceptions import RequestException
import json

pytestmark = pytest.mark.asyncio

import textra_client

@pytest.fixture(autouse=True)
def reset_client_state():
    """Resets the global token cache before each test."""
    textra_client._access_token = None
    textra_client._token_expires_at = 0.0
    yield # テストを実行


async def test_get_access_token_success(mocker):
    """
    get_access_token が成功時にアクセストークン文字列を返すことを確認する。
    """
    mocker.patch.object(textra_client.settings, 'TEXTRA_API_KEY', 'test_key')
    mocker.patch.object(textra_client.settings, 'TEXTRA_API_SECRET', 'test_secret')
    mocker.patch.object(textra_client.settings, 'TEXTRA_TOKEN_URL', 'https://example.com/token')

    # fetch_token は同期的メソッドなので、AsyncMock ではなく MagicMock を使用
    mock_session_instance = mocker.MagicMock()
    mock_session_instance.fetch_token.return_value = {
        'access_token': 'test_token',
        'expires_in': 3600,
        'token_type': 'Bearer'
    }
        
    mock_oauth2_session = mocker.patch('textra_client.OAuth2Session')
    mock_oauth2_session.return_value = mock_session_instance
        
    mock_backend_client = mocker.patch('textra_client.BackendApplicationClient')
    mocker.patch('asyncio.get_running_loop').return_value.time.return_value = 1000.0

    token = await textra_client.get_access_token()

    mock_oauth2_session.assert_called_once_with(client=mock_backend_client.return_value)
    # fetch_token は同期的メソッドなので assert_called_once_with を使用
    mock_session_instance.fetch_token.assert_called_once_with(
        token_url='https://example.com/token',
        client_id='test_key',
        client_secret='test_secret'
    )
    assert token == 'test_token'

async def test_get_access_token_api_error(mocker):
    """
    トークン取得APIがエラーレスポンスを返した場合に例外が発生することを確認する。
    (例: OAuth2Error)
    """
    mocker.patch.object(textra_client.settings, 'TEXTRA_API_KEY', 'test_key')
    mocker.patch.object(textra_client.settings, 'TEXTRA_API_SECRET', 'test_secret')
    mocker.patch.object(textra_client.settings, 'TEXTRA_TOKEN_URL', 'https://example.com/token')

    # fetch_token は同期的メソッドなので、AsyncMock ではなく MagicMock を使用
    mock_session_instance = mocker.MagicMock()
    mock_session_instance.fetch_token.side_effect = OAuth2Error("Invalid client credentials")

    mock_oauth2_session = mocker.patch('textra_client.OAuth2Session')
    mock_oauth2_session.return_value = mock_session_instance
    mocker.patch('textra_client.BackendApplicationClient')
    mocker.patch('asyncio.get_running_loop').return_value.time.return_value = 1000.0

    with pytest.raises(Exception) as excinfo:
        await textra_client.get_access_token()

    # エラーメッセージが正しく伝播されているか確認
    assert "Failed to fetch access token" in str(excinfo.value)
    # 元の例外のメッセージも含まれていることを確認
    assert "Invalid client credentials" in str(excinfo.value.__cause__) # Check the cause

async def test_get_access_token_network_error(mocker):
    """
    トークン取得時にネットワークエラーが発生した場合に例外が発生することを確認する。
    (例: requests.exceptions.RequestException)
    """
    mocker.patch.object(textra_client.settings, 'TEXTRA_API_KEY', 'test_key')
    mocker.patch.object(textra_client.settings, 'TEXTRA_API_SECRET', 'test_secret')
    mocker.patch.object(textra_client.settings, 'TEXTRA_TOKEN_URL', 'https://example.com/token')

    # fetch_token は同期的メソッドなので、AsyncMock ではなく MagicMock を使用
    mock_session_instance = mocker.MagicMock()
    mock_session_instance.fetch_token.side_effect = RequestException("Connection timed out")

    mock_oauth2_session = mocker.patch('textra_client.OAuth2Session')
    mock_oauth2_session.return_value = mock_session_instance
    mocker.patch('textra_client.BackendApplicationClient')
    mocker.patch('asyncio.get_running_loop').return_value.time.return_value = 1000.0

    with pytest.raises(Exception) as excinfo:
        await textra_client.get_access_token()

    assert "Failed to fetch access token" in str(excinfo.value)
    assert "Connection timed out" in str(excinfo.value.__cause__) # Check the cause

async def test_get_access_token_cache_valid(mocker):
    """
    取得したトークンが有効期限内であればキャッシュから返され、API呼び出しが行われないことを確認する。
    """
    mocker.patch.object(textra_client.settings, 'TEXTRA_API_KEY', 'test_key')
    mocker.patch.object(textra_client.settings, 'TEXTRA_API_SECRET', 'test_secret')
    mocker.patch.object(textra_client.settings, 'TEXTRA_TOKEN_URL', 'https://example.com/token')

    # fetch_token は同期的メソッドなので、AsyncMock ではなく MagicMock を使用
    mock_session_instance = mocker.MagicMock()
    mock_session_instance.fetch_token.return_value = {
        'access_token': 'cached_token',
        'expires_in': 3600,
        'token_type': 'Bearer'
    }
    mock_oauth2_session = mocker.patch('textra_client.OAuth2Session')
    mock_oauth2_session.return_value = mock_session_instance
    mocker.patch('textra_client.BackendApplicationClient')

    mock_time = mocker.patch('asyncio.get_running_loop').return_value.time
    mock_time.side_effect = [
        1000.0,
        1000.0,
        1000.0 + 1800.0,
    ]

    token1 = await textra_client.get_access_token()
    assert token1 == 'cached_token'
    assert mock_session_instance.fetch_token.call_count == 1

    token2 = await textra_client.get_access_token()
    assert token2 == 'cached_token'
    assert mock_session_instance.fetch_token.call_count == 1

async def test_get_access_token_cache_expired(mocker):
    """
    キャッシュされたトークンの有効期限が切れた場合、再度APIから取得することを確認する。
    """
    mocker.patch.object(textra_client.settings, 'TEXTRA_API_KEY', 'test_key')
    mocker.patch.object(textra_client.settings, 'TEXTRA_API_SECRET', 'test_secret')
    mocker.patch.object(textra_client.settings, 'TEXTRA_TOKEN_URL', 'https://example.com/token')

    # fetch_token は同期的メソッドなので、AsyncMock ではなく MagicMock を使用
    mock_session_instance = mocker.MagicMock()
    mock_session_instance.fetch_token.side_effect = [
        { 'access_token': 'first_token', 'expires_in': 3600, 'token_type': 'Bearer' },
        { 'access_token': 'second_token', 'expires_in': 3600, 'token_type': 'Bearer' },
    ]
    mock_oauth2_session = mocker.patch('textra_client.OAuth2Session')
    mock_oauth2_session.return_value = mock_session_instance
    mocker.patch('textra_client.BackendApplicationClient')

    mock_time = mocker.patch('asyncio.get_running_loop').return_value.time
    mock_time.return_value = 1000.0
    
    token1 = await textra_client.get_access_token()
    assert token1 == 'first_token'
    assert mock_session_instance.fetch_token.call_count == 1
    
    mock_time.return_value = 5000.0

    token2 = await textra_client.get_access_token()
    assert token2 == 'second_token'
    assert mock_session_instance.fetch_token.call_count == 2

async def test_translate_ja_to_en_success(mocker):
    """
    translate_ja_to_en が成功時に翻訳結果を返すことを確認する。
    """
    mock_get_token = mocker.patch('textra_client.get_access_token', new=AsyncMock())
    mock_get_token.return_value = 'test_token'
    
    mocker.patch.object(textra_client.settings, 'TEXTRA_JA_EN_API_URL', 'https://example.com/translate')
    mocker.patch.object(textra_client.settings, 'TEXTRA_USER_NAME', 'test_user')
    mocker.patch.object(textra_client.settings, 'TEXTRA_API_KEY', 'test_key')
    
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'resultset': {
            'code': '0',
            'message': 'Success',
            'result': {
                'text': 'This is a test.',
                'information': {}
            }
        }
    }
    mock_post = mocker.patch('requests.post', return_value=mock_response)
    
    result = await textra_client.translate_ja_to_en('これはテストです。')
    
    mock_get_token.assert_awaited_once()
    
    mock_post.assert_called_once_with(
        'https://example.com/translate',
        data={
            'access_token': 'test_token',
            'key': 'test_key',
            'name': 'test_user',
            'type': 'json',
            'text': 'これはテストです。'
        }
    )
    
    assert result == 'This is a test.'

async def test_translate_ja_to_en_api_error(mocker):
    """
    翻訳APIがエラーレスポンスを返した場合に例外が発生することを確認する。
    """
    mock_get_token = mocker.patch('textra_client.get_access_token', new=AsyncMock())
    mock_get_token.return_value = 'test_token'
    
    mocker.patch.object(textra_client.settings, 'TEXTRA_JA_EN_API_URL', 'https://example.com/translate')
    mocker.patch.object(textra_client.settings, 'TEXTRA_USER_NAME', 'test_user')
    mocker.patch.object(textra_client.settings, 'TEXTRA_API_KEY', 'test_key')
    
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'resultset': {
            'code': '500',
            'message': 'API key error'
        }
    }
    mocker.patch('requests.post', return_value=mock_response)
    
    with pytest.raises(Exception) as excinfo:
        await textra_client.translate_ja_to_en('これはテストです。')
    
    assert "Translation API error" in str(excinfo.value)
    assert "API key error" in str(excinfo.value)

async def test_translate_ja_to_en_network_error(mocker):
    """
    翻訳API呼び出し時にネットワークエラーが発生した場合に例外が発生することを確認する。
    """
    mock_get_token = mocker.patch('textra_client.get_access_token', new=AsyncMock())
    mock_get_token.return_value = 'test_token'
    
    mocker.patch.object(textra_client.settings, 'TEXTRA_JA_EN_API_URL', 'https://example.com/translate')
    mocker.patch.object(textra_client.settings, 'TEXTRA_USER_NAME', 'test_user')
    mocker.patch.object(textra_client.settings, 'TEXTRA_API_KEY', 'test_key')
    
    mocker.patch('requests.post', side_effect=RequestException("Connection timed out"))
    
    with pytest.raises(Exception) as excinfo:
        await textra_client.translate_ja_to_en('これはテストです。')
    
    assert "Network error during translation" in str(excinfo.value)
    assert "Connection timed out" in str(excinfo.value)

async def test_translate_ja_to_en_token_error(mocker):
    """
    get_access_token が失敗した場合に translate_ja_to_en も失敗することを確認する。
    """
    mock_get_token = mocker.patch('textra_client.get_access_token', new=AsyncMock())
    mock_get_token.side_effect = Exception("Failed to fetch access token")
    
    with pytest.raises(Exception) as excinfo:
        await textra_client.translate_ja_to_en('これはテストです。')
    
    assert "Failed to fetch access token" in str(excinfo.value)
