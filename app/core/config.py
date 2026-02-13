from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/ar_portal"
    
    # JWT Settings
    SECRET_KEY: str = "CHANGE_ME_SUPER_SECRET"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours
    
    # Microsoft Azure AD / Graph API
    AZURE_CLIENT_ID: str
    AZURE_TENANT_ID: str
    AZURE_CLIENT_SECRET: str
    AZURE_REDIRECT_URI: str = "http://localhost:8000/auth/microsoft/callback"
    AZURE_AUTHORITY: Optional[str] = None
    AZURE_SCOPE: str = "User.Read Mail.Read Mail.Send Mail.ReadWrite"
    
    # Chartmetric API Configuration
    CHARTMETRIC_API_KEY: str = ""
    CHARTMETRIC_REFRESH_TOKEN: str = ""
    CHARTMETRIC_BASE_URL: str = "https://api.chartmetric.com/api"
    
    # Spotify Web API Configuration
    SPOTIFY_CLIENT_ID: str = ""
    SPOTIFY_CLIENT_SECRET: str = ""
    
    # Chartex API Configuration (Historical Streaming Data)
    CHARTEX_APP_ID: str = ""
    CHARTEX_APP_TOKEN: str = ""
    CHARTEX_BASE_URL: str = "https://api.chartex.com"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def authority(self) -> str:
        """Returns the Azure authority URL"""
        if self.AZURE_AUTHORITY:
            return self.AZURE_AUTHORITY
        return f"https://login.microsoftonline.com/{self.AZURE_TENANT_ID}"

settings = Settings()
