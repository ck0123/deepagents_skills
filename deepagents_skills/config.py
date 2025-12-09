"""配置管理模块

从 config.json 加载配置，支持环境变量覆盖。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def _expand_path(path: str) -> Path:
    """展开路径中的 ~ 和环境变量"""
    return Path(os.path.expandvars(os.path.expanduser(path)))


@dataclass
class SkillsConfig:
    """技能系统配置"""
    user_dir: Path
    project_dir: Path
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SkillsConfig":
        return cls(
            user_dir=_expand_path(data.get("user_dir", "~/.deepagents/skills")),
            project_dir=_expand_path(data.get("project_dir", ".deepagents/skills")),
        )


@dataclass
class MemoryConfig:
    """记忆系统配置"""
    user_dir: Path
    project_dir: Path
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryConfig":
        return cls(
            user_dir=_expand_path(data.get("user_dir", "~/.deepagents/memory")),
            project_dir=_expand_path(data.get("project_dir", ".deepagents/memory")),
        )


@dataclass
class APIConfig:
    """API 配置，支持环境变量覆盖"""
    openai_api_key: str
    anthropic_api_key: str
    google_api_key: str
    tavily_api_key: str
    deepseek_base_url: str
    deepseek_model_name: str
    deepseek_api_key: str
    deepseek_model_enable_think: str
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "APIConfig":
        return cls(
            openai_api_key=os.environ.get("OPENAI_API_KEY", data.get("openai_api_key", "")),
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", data.get("anthropic_api_key", "")),
            google_api_key=os.environ.get("GOOGLE_API_KEY", data.get("google_api_key", "")),
            tavily_api_key=os.environ.get("TAVILY_API_KEY", data.get("tavily_api_key", "")),
            deepseek_base_url=os.environ.get("BASE_URL", data.get("deepseek_base_url", "")),
            deepseek_model_name=os.environ.get("MODEL_NAME", data.get("deepseek_model_name", "")),
            deepseek_api_key=os.environ.get("API_KEY", data.get("deepseek_api_key", "")),
            deepseek_model_enable_think=os.environ.get(
                "MODEL_ENABLE_THINK", data.get("deepseek_model_enable_think", "")
            ),
        )
    
    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key)
    
    @property
    def has_anthropic(self) -> bool:
        return bool(self.anthropic_api_key)
    
    @property
    def has_google(self) -> bool:
        return bool(self.google_api_key)
    
    @property
    def has_tavily(self) -> bool:
        return bool(self.tavily_api_key)

    @property
    def has_deepseek(self) -> bool:
        return bool(self.deepseek_api_key and self.deepseek_base_url and self.deepseek_model_name)


@dataclass
class AgentConfig:
    """智能体配置"""
    default_model: str
    max_iterations: int
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentConfig":
        return cls(
            default_model=data.get("default_model", "gpt-4o-mini"),
            max_iterations=data.get("max_iterations", 10),
        )


@dataclass
class Config:
    """主配置类
    
    从 config.json 加载配置，支持环境变量覆盖 API keys。
    
    Example:
        >>> config = Config.load("config.json")
        >>> print(config.skills.user_dir)
        >>> print(config.api.has_openai)
    """
    skills: SkillsConfig
    memory: MemoryConfig
    api: APIConfig
    agent: AgentConfig
    _config_path: Path | None = field(default=None, repr=False)
    
    @classmethod
    def load(cls, config_path: str | Path | None = None) -> "Config":
        """从配置文件加载配置
        
        Args:
            config_path: 配置文件路径，如果为 None 则使用默认配置
            
        Returns:
            Config 实例
        """
        if config_path is None:
            # 使用默认配置
            return cls.default()
        
        path = Path(config_path)
        if not path.exists():
            # 配置文件不存在，使用默认配置
            return cls.default()
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return cls(
            skills=SkillsConfig.from_dict(data.get("skills", {})),
            memory=MemoryConfig.from_dict(data.get("memory", {})),
            api=APIConfig.from_dict(data.get("api", {})),
            agent=AgentConfig.from_dict(data.get("agent", {})),
            _config_path=path,
        )
    
    @classmethod
    def default(cls) -> "Config":
        """创建默认配置"""
        return cls(
            skills=SkillsConfig(
                user_dir=_expand_path("~/.deepagents/skills"),
                project_dir=_expand_path(".deepagents/skills"),
            ),
            memory=MemoryConfig(
                user_dir=_expand_path("~/.deepagents/memory"),
                project_dir=_expand_path(".deepagents/memory"),
            ),
            api=APIConfig(
                openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
                anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
                google_api_key=os.environ.get("GOOGLE_API_KEY", ""),
                tavily_api_key=os.environ.get("TAVILY_API_KEY", ""),
                deepseek_base_url=os.environ.get("BASE_URL", "https://api.deepseek.com/beta/"),
                deepseek_model_name=os.environ.get("MODEL_NAME", "deepseek-chat"),
                deepseek_api_key=os.environ.get("API_KEY", "sk-xxxx"),
                deepseek_model_enable_think=os.environ.get("MODEL_ENABLE_THINK", "disabled"),
            ),
            agent=AgentConfig(
                default_model="gpt-4o-mini",
                max_iterations=10,
            ),
        )
    
    def save(self, config_path: str | Path | None = None) -> None:
        """保存配置到文件
        
        Args:
            config_path: 配置文件路径，如果为 None 则使用加载时的路径
        """
        path = Path(config_path) if config_path else self._config_path
        if path is None:
            raise ValueError("未指定配置文件路径")
        
        data = {
            "skills": {
                "user_dir": str(self.skills.user_dir),
                "project_dir": str(self.skills.project_dir),
            },
            "memory": {
                "user_dir": str(self.memory.user_dir),
                "project_dir": str(self.memory.project_dir),
            },
            "api": {
                "openai_api_key": self.api.openai_api_key,
                "anthropic_api_key": self.api.anthropic_api_key,
                "google_api_key": self.api.google_api_key,
                "tavily_api_key": self.api.tavily_api_key,
                "deepseek_base_url": self.api.deepseek_base_url,
                "deepseek_model_name": self.api.deepseek_model_name,
                "deepseek_api_key": self.api.deepseek_api_key,
                "deepseek_model_enable_think": self.api.deepseek_model_enable_think,
            },
            "agent": {
                "default_model": self.agent.default_model,
                "max_iterations": self.agent.max_iterations,
            },
        }
        
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def ensure_dirs(self) -> None:
        """确保所有配置的目录存在"""
        self.skills.user_dir.mkdir(parents=True, exist_ok=True)
        self.skills.project_dir.mkdir(parents=True, exist_ok=True)
        self.memory.user_dir.mkdir(parents=True, exist_ok=True)
        self.memory.project_dir.mkdir(parents=True, exist_ok=True)

