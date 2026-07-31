"""
config/settings.py - 配置管理器
"""
import os

# 项目根目录
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings:
    """配置管理器"""

    def __init__(self, config_path: str = None):
        """
        加载配置。
        config_path: 用户指定的配置文件路径（--config 参数）。
                     None 则使用默认查找逻辑。
        """
        self._config: dict = {}
        self._load(config_path)

    def _load(self, config_path: str = None) -> None:
        """加载配置文件"""
        # 1. 加载默认配置
        default_path = os.path.join(_PROJECT_ROOT, "config", "default.yaml")
        self._config = self._load_yaml(default_path) or {}

        # 2. 加载用户配置（覆盖默认）
        if config_path:
            user_config = self._load_yaml(config_path)
        else:
            # 默认查找程序同目录下的 config.yaml
            user_path = os.path.join(_PROJECT_ROOT, "config.yaml")
            user_config = self._load_yaml(user_path) if os.path.exists(user_path) else None

        if user_config:
            self._merge(self._config, user_config)

    def _load_yaml(self, path: str) -> dict | None:
        """加载 YAML 文件"""
        if not path or not os.path.exists(path):
            return None
        try:
            import yaml
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except ImportError:
            # PyYAML 未安装，返回 None
            return None
        except Exception:
            return None

    def _merge(self, base: dict, override: dict) -> None:
        """递归合并配置（override 覆盖 base）"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge(base[key], value)
            else:
                base[key] = value

    def is_display_enabled(self, category: str) -> bool:
        """某类别是否启用显示"""
        return self._config.get("display", {}).get(category, True)

    def get_color_mode(self) -> str:
        """返回颜色模式: 'auto' / 'always' / 'never'"""
        return self._config.get("output", {}).get("color", "auto")

    def get_unicode_mode(self) -> str:
        """返回 Unicode 模式: 'auto' / 'always' / 'never'"""
        return self._config.get("output", {}).get("unicode", "auto")

    def get_timeout(self) -> int:
        """返回单模块超时秒数"""
        return self._config.get("collect", {}).get("timeout", 10)

    def is_parallel(self) -> bool:
        """是否并行采集"""
        return self._config.get("collect", {}).get("parallel", True)

    def apply_cli_overrides(self, args) -> None:
        """将命令行参数覆盖到配置中"""
        if getattr(args, "no_color", False):
            self._config.setdefault("output", {})["color"] = "never"
