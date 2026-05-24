
import os
import yaml
from typing import Dict, Any


class Config:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self._config = self._load_config()

    def _load_config(self) -&gt; Dict[str, Any]:
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    # --- LangChain 配置 ---
    @property
    def LANGCHAIN_TRACING_V2(self) -&gt; bool:
        return self._config.get('langchain', {}).get('tracing_v2', False)

    @property
    def LANGCHAIN_PROJECT(self) -&gt; str:
        return self._config.get('langchain', {}).get('project', '')

    @property
    def LANGCHAIN_API_KEY(self) -&gt; str:
        return self._config.get('langchain', {}).get('api_key', '')

    # --- ARK API 配置 ---
    @property
    def ARK_API_KEY(self) -&gt; str:
        return self._config.get('ark', {}).get('api_key', '')

    # --- 数据库配置 ---
    @property
    def MYSQL_MASTER_URL(self) -&gt; str:
        return self._config.get('database', {}).get('master_url', '')

    @property
    def MYSQL_SLAVE_URL(self) -&gt; str:
        return self._config.get('database', {}).get('slave_url', self.MYSQL_MASTER_URL)

    # --- 服务配置 ---
    @property
    def HOST(self) -&gt; str:
        return self._config.get('server', {}).get('host', '127.0.0.1')

    @property
    def PORT(self) -&gt; int:
        return self._config.get('server', {}).get('port', 8001)

    @property
    def RELOAD(self) -&gt; bool:
        return self._config.get('server', {}).get('reload', False)

    # --- 代理配置 ---
    @property
    def HTTP_PROXY(self) -&gt; str:
        return self._config.get('proxy', {}).get('http', '')

    @property
    def HTTPS_PROXY(self) -&gt; str:
        return self._config.get('proxy', {}).get('https', '')


# 全局配置实例
config = Config()

