from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    secret_key: str 
    algorithm: str
    access_token_expire_minutes: int
    sso_client_url: str
    refresh_secret_key: str

    model_config = SettingsConfigDict(env_file="../.env")
