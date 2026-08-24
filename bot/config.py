from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Pass24 API
    pass24_base_url: str = "https://mobile-api.pass24online.ru/v1"
    # The Pass24 Mobile API expects this phone number in its `email` field.
    pass24_phone: str
    pass24_password: str
    pass24_address_id: int = 0  # 0 = автообнаружение при старте
    pass24_tenant_id: int = 0   # 0 = автообнаружение при старте
    pass24_vehicle_type: int = 404


settings = Settings()
