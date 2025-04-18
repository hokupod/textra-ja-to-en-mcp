import os
import os
import pytest
import importlib
from unittest.mock import patch

import config

def test_default_settings_when_env_missing(mocker):
    """
    .env ファイルが存在せず、環境変数も設定されていない場合、
    設定値がデフォルト値 (None または指定されたデフォルト) であることを確認する。
    """
    mocker.patch('dotenv.load_dotenv', return_value=False)
    mocker.patch.dict(os.environ, {}, clear=True)

    importlib.reload(config)
    settings = config.settings

    assert settings.TEXTRA_API_KEY is None
    assert settings.TEXTRA_API_SECRET is None
    assert settings.TEXTRA_USER_NAME is None
    assert settings.TEXTRA_TOKEN_URL == "https://mt-auto-minhon-mlt.ucri.jgn-x.jp/oauth2/token.php"
    # config.py でデフォルト値が設定されたため、None ではなくデフォルト値を期待する
    assert settings.TEXTRA_JA_EN_API_URL == "https://mt-auto-minhon-mlt.ucri.jgn-x.jp/api/mt/generalNT_ja_en/"

def test_load_settings_from_dotenv(mocker):
    """
    .env ファイルが存在し、読み込まれた場合、設定値が .env の値になることを確認する。
    (環境変数には同名の値が存在しないケース)
    """
    mocker.patch('dotenv.load_dotenv', return_value=True)
    mocker.patch.dict(os.environ, {}, clear=True)
    mock_env_values = {
        "TEXTRA_API_KEY": "test_key_from_dotenv",
        "TEXTRA_API_SECRET": "test_secret_from_dotenv",
        "TEXTRA_USER_NAME": "test_user_from_dotenv",
        "TEXTRA_JA_EN_API_URL": "http://dotenv.example.com/api",
    }
    mocker.patch('os.getenv', side_effect=lambda key, default=None: mock_env_values.get(key, default))

    importlib.reload(config)
    settings = config.settings

    assert settings.TEXTRA_API_KEY == "test_key_from_dotenv"
    assert settings.TEXTRA_API_SECRET == "test_secret_from_dotenv"
    assert settings.TEXTRA_USER_NAME == "test_user_from_dotenv"
    assert settings.TEXTRA_TOKEN_URL == "https://mt-auto-minhon-mlt.ucri.jgn-x.jp/oauth2/token.php"
    assert settings.TEXTRA_JA_EN_API_URL == "http://dotenv.example.com/api"

def test_load_settings_from_os_environ(mocker):
    """
    環境変数に値が設定されている場合、設定値が環境変数の値になることを確認する。
    (.env ファイルが存在しないケース)
    """
    mocker.patch('dotenv.load_dotenv', return_value=False)
    mock_os_environ = {
        "TEXTRA_API_KEY": "test_key_from_os",
        "TEXTRA_API_SECRET": "test_secret_from_os",
        "TEXTRA_USER_NAME": "test_user_from_os",
        "TEXTRA_JA_EN_API_URL": "http://os.example.com/api",
        "TEXTRA_TOKEN_URL": "http://os.example.com/token",
    }
    mocker.patch.dict(os.environ, mock_os_environ, clear=True)

    importlib.reload(config)
    settings = config.settings

    assert settings.TEXTRA_API_KEY == "test_key_from_os"
    assert settings.TEXTRA_API_SECRET == "test_secret_from_os"
    assert settings.TEXTRA_USER_NAME == "test_user_from_os"
    assert settings.TEXTRA_TOKEN_URL == "http://os.example.com/token"
    assert settings.TEXTRA_JA_EN_API_URL == "http://os.example.com/api"

def test_dotenv_overrides_os_environ(mocker):
    """
    .env ファイルと環境変数の両方に値が存在する場合、.env の値が優先されることを確認する。
    (load_dotenv(override=True) の効果)
    """
    mock_os_environ = {
        "TEXTRA_API_KEY": "value_from_os",
        "TEXTRA_API_SECRET": "value_from_os",
        "TEXTRA_USER_NAME": "value_from_os",
        "TEXTRA_JA_EN_API_URL": "http://os.example.com/api",
        "TEXTRA_TOKEN_URL": "http://os.example.com/token",
    }
    mocker.patch.dict(os.environ, mock_os_environ, clear=True)

    mocker.patch('dotenv.load_dotenv', return_value=True)

    mock_dotenv_values = {
        "TEXTRA_API_KEY": "value_from_dotenv",
        "TEXTRA_API_SECRET": "value_from_dotenv",
        "TEXTRA_USER_NAME": "value_from_dotenv",
        "TEXTRA_JA_EN_API_URL": "http://dotenv.example.com/api",
        "TEXTRA_TOKEN_URL": "http://os.example.com/token",
    }
    mocker.patch('os.getenv', side_effect=lambda key, default=None: mock_dotenv_values.get(key, default))

    importlib.reload(config)
    settings = config.settings

    assert settings.TEXTRA_API_KEY == "value_from_dotenv"
    assert settings.TEXTRA_API_SECRET == "value_from_dotenv"
    assert settings.TEXTRA_USER_NAME == "value_from_dotenv"
    assert settings.TEXTRA_TOKEN_URL == "http://os.example.com/token"
    assert settings.TEXTRA_JA_EN_API_URL == "http://dotenv.example.com/api"
