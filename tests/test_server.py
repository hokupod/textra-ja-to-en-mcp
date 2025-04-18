import pytest
from fastmcp import Client, FastMCP, Context
from fastmcp.exceptions import ClientError
from mcp.types import TextContent
import asyncio
import sys
from pathlib import Path
import httpx

# server.py をインポート (存在しない場合は ImportError になる)
try:
    from server import mcp as mcp_app
    SERVER_EXISTS = True
except ImportError:
    mcp_app = None
    SERVER_EXISTS = False

@pytest.mark.asyncio
async def test_list_tools_contains_translate_ja_to_en():
    """サーバーが 'translate_ja_to_en' ツールを提供することを確認します。"""
    if not SERVER_EXISTS or mcp_app is None:
        pytest.skip("server.py or 'mcp' instance not found, skipping server tests.")

    client = Client(mcp_app)

    async with client:
        tools = await client.list_tools()

        assert "translate_ja_to_en" in [tool.name for tool in tools], \
            f"'translate_ja_to_en' tool not found in {tools}"

@pytest.mark.asyncio
async def test_call_translate_ja_to_en_calls_client(mocker):
    """'translate_ja_to_en' ツールが内部で textra_client.translate_ja_to_en を
    正しい引数で呼び出すことを確認します。
    """
    if not SERVER_EXISTS or mcp_app is None:
        pytest.skip("server.py or 'mcp' instance not found, skipping server tests.")

    mock_translate = mocker.patch(
        "server.textra_client.translate_ja_to_en",
        return_value="Mocked translation"
    )

    client = Client(mcp_app)

    input_text = "こんにちは"
    expected_args = {"text": input_text}

    async with client:
        await client.call_tool("translate_ja_to_en", expected_args)

    mock_translate.assert_called_once_with(input_text)

@pytest.mark.asyncio
async def test_call_translate_ja_to_en_returns_translation(mocker):
    """'translate_ja_to_en' ツールが textra_client から返された翻訳結果を
    正しく TextContent として返すことを確認します。
    """
    if not SERVER_EXISTS or mcp_app is None:
        pytest.skip("server.py or 'mcp' instance not found, skipping server tests.")

    expected_translation = "Hello"
    mocker.patch(
        "server.textra_client.translate_ja_to_en",
        return_value=expected_translation
    )

    client = Client(mcp_app)

    input_text = "こんにちは"
    args = {"text": input_text}

    async with client:
        result = await client.call_tool("translate_ja_to_en", args)

    assert isinstance(result, list)
    assert len(result) == 1
    content = result[0]
    assert isinstance(content, TextContent)
    assert content.type == "text"
    assert content.text == expected_translation


# エラーハンドリングのテストをパラメータ化
@pytest.mark.parametrize(
    "exception_to_raise, expected_error_message_part",
    [
        (ValueError("Missing config"), "Translation failed due to a configuration issue."),
        (httpx.HTTPStatusError("API Error", request=httpx.Request('POST', 'http://test'), response=httpx.Response(status_code=500, text="Internal Server Error")), "Translation failed due to an API error (Status: 500)."),
        (httpx.RequestError("Network Error", request=httpx.Request('POST', 'http://test')), "Translation failed due to a network issue."),
        (Exception("Some other error"), "An unexpected error occurred during translation."),
    ],
    ids=["ValueError", "HTTPStatusError", "RequestError", "GenericException"]
)
@pytest.mark.asyncio
async def test_call_translate_ja_to_en_returns_specific_error_message(
    mocker, exception_to_raise, expected_error_message_part
):
    """'translate_ja_to_en' ツールが各種例外発生時に適切なエラーメッセージを返すことを確認します。"""
    if not SERVER_EXISTS or mcp_app is None:
        pytest.skip("server.py or 'mcp' instance not found, skipping server tests.")

    mocker.patch(
        "server.textra_client.translate_ja_to_en",
        side_effect=exception_to_raise
    )

    client = Client(mcp_app)

    input_text = "エラーテスト"
    args = {"text": input_text}

    async with client:
        result = await client.call_tool("translate_ja_to_en", args)

    assert isinstance(result, list)
    assert len(result) == 1
    content = result[0]
    assert isinstance(content, TextContent)
    assert content.type == "text"
    assert expected_error_message_part in content.text
