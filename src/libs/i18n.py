"""
国际化模块
"""

import gettext
import os
from pathlib import Path
from typing import Optional

from src.settings import get_settings


class I18n:
    """
    国际化类
    """

    _instance: Optional["I18n"] = None
    _translations: dict[str, gettext.NullTranslations] = {}

    def __new__(cls, language: str = "zh_CN") -> "I18n":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, language: str = "zh_CN") -> None:
        """
        初始化国际化类
        Args:
            language (str): 语言代码，例如 zh_CN, en_US
        """
        if not hasattr(self, "language"):
            self.language = language
            self._ = None
            self.load_translations()

    def load_translations(self) -> None:
        """
        加载翻译
        """
        try:
            # 获取项目根目录
            root_dir = Path(__file__).parent.parent
            locale_dir = os.path.join(root_dir, "locale")
            # 确保翻译目录存在
            if not os.path.exists(locale_dir):
                raise FileNotFoundError(f"翻译目录不存在: {locale_dir}")

            # 如果该语言的翻译已加载，直接使用缓存
            if self.language in self._translations:
                self.translations = self._translations[self.language]
            else:
                self.translations = gettext.translation(
                    "messages", locale_dir, languages=[self.language], fallback=True
                )
                self._translations[self.language] = self.translations

            self.translations.install()
            self._ = self.translations.gettext

        except Exception as e:
            print(f"加载翻译文件失败: {e}")
            # 使用空翻译作为后备方案
            self.translations = gettext.NullTranslations()
            self._ = self.translations.gettext

    def gettext(self, message: str) -> str:
        """
        获取翻译
        Args:
            message (str): 消息
        Returns:
            str: 翻译后的文本
        """
        if self._ is None:
            print("加载翻译失败")
            return message
        return self._(message)

    @classmethod
    def change_language(cls, language: str) -> None:
        """
        切换语言
        Args:
            language (str): 新的语言代码
        """
        if cls._instance:
            cls._instance.language = language
            cls._instance.load_translations()


# 初始化国际化类
i18n = I18n(get_settings().lang)
