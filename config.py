import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Settings:
    """アプリケーションの設定を保持するクラス"""
    TEXTRA_API_KEY: str | None = os.getenv("TEXTRA_API_KEY")
    TEXTRA_API_SECRET: str | None = os.getenv("TEXTRA_API_SECRET")
    TEXTRA_USER_NAME: str | None = os.getenv("TEXTRA_USER_NAME")
    TEXTRA_TOKEN_URL: str | None = os.getenv("TEXTRA_TOKEN_URL", "https://mt-auto-minhon-mlt.ucri.jgn-x.jp/oauth2/token.php")
    TEXTRA_JA_EN_API_URL: str | None = os.getenv("TEXTRA_JA_EN_API_URL", "https://mt-auto-minhon-mlt.ucri.jgn-x.jp/api/mt/generalNT_ja_en/")

settings = Settings()
