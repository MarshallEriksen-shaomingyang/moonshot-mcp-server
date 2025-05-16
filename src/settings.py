from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用程序配置类。

    Args:
        BaseSettings (_type_): _description_
    """
    lang: str = "zh_CN"
    assistant_name: str = "AlphaCore"
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache  # 添加括号
def get_settings() -> Settings:
    """获取应用程序配置实例。

    Returns:
        Settings: 配置实例
    """
    return Settings()
