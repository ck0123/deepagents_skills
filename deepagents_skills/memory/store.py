"""记忆存储

提供持久化记忆存储，支持用户级和项目级记忆。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from deepagents_skills.config import Config


@dataclass
class MemoryEntry:
    """记忆条目
    
    Attributes:
        key: 记忆键
        content: 记忆内容
        metadata: 元数据
        created_at: 创建时间
        updated_at: 更新时间
    """
    key: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "key": self.key,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryEntry":
        """从字典创建"""
        return cls(
            key=data["key"],
            content=data["content"],
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
        )


class MemoryStore:
    """记忆存储
    
    提供持久化记忆存储，支持用户级和项目级记忆。
    记忆以 Markdown 文件形式存储。
    
    Example:
        >>> store = MemoryStore(config)
        >>> 
        >>> # 保存记忆
        >>> store.save("agent", "# Agent Memory\\n\\nThis is my memory.")
        >>> 
        >>> # 读取记忆
        >>> content = store.load("agent")
        >>> 
        >>> # 列出所有记忆
        >>> memories = store.list_all()
    """
    
    def __init__(self, config: "Config"):
        """初始化记忆存储
        
        Args:
            config: 配置实例
        """
        self.config = config
        self._user_dir = config.memory.user_dir
        self._project_dir = config.memory.project_dir
    
    def _get_user_path(self, key: str) -> Path:
        """获取用户级记忆文件路径"""
        return self._user_dir / f"{key}.md"
    
    def _get_project_path(self, key: str) -> Path:
        """获取项目级记忆文件路径"""
        return self._project_dir / f"{key}.md"
    
    def save_user(self, key: str, content: str) -> Path:
        """保存用户级记忆
        
        Args:
            key: 记忆键（文件名，不含扩展名）
            content: 记忆内容
            
        Returns:
            保存的文件路径
        """
        self._user_dir.mkdir(parents=True, exist_ok=True)
        path = self._get_user_path(key)
        path.write_text(content, encoding="utf-8")
        return path
    
    def save_project(self, key: str, content: str) -> Path:
        """保存项目级记忆
        
        Args:
            key: 记忆键
            content: 记忆内容
            
        Returns:
            保存的文件路径
        """
        self._project_dir.mkdir(parents=True, exist_ok=True)
        path = self._get_project_path(key)
        path.write_text(content, encoding="utf-8")
        return path
    
    def load_user(self, key: str) -> str | None:
        """加载用户级记忆
        
        Args:
            key: 记忆键
            
        Returns:
            记忆内容，不存在则返回 None
        """
        path = self._get_user_path(key)
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None
    
    def load_project(self, key: str) -> str | None:
        """加载项目级记忆
        
        Args:
            key: 记忆键
            
        Returns:
            记忆内容，不存在则返回 None
        """
        path = self._get_project_path(key)
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None
    
    def load(self, key: str) -> str | None:
        """加载记忆（项目级优先）
        
        Args:
            key: 记忆键
            
        Returns:
            记忆内容，不存在则返回 None
        """
        # 项目级优先
        content = self.load_project(key)
        if content is not None:
            return content
        return self.load_user(key)
    
    def delete_user(self, key: str) -> bool:
        """删除用户级记忆
        
        Args:
            key: 记忆键
            
        Returns:
            是否删除成功
        """
        path = self._get_user_path(key)
        if path.exists():
            path.unlink()
            return True
        return False
    
    def delete_project(self, key: str) -> bool:
        """删除项目级记忆
        
        Args:
            key: 记忆键
            
        Returns:
            是否删除成功
        """
        path = self._get_project_path(key)
        if path.exists():
            path.unlink()
            return True
        return False
    
    def list_user(self) -> list[str]:
        """列出所有用户级记忆键
        
        Returns:
            记忆键列表
        """
        if not self._user_dir.exists():
            return []
        return [
            f.stem for f in self._user_dir.iterdir()
            if f.is_file() and f.suffix == ".md"
        ]
    
    def list_project(self) -> list[str]:
        """列出所有项目级记忆键
        
        Returns:
            记忆键列表
        """
        if not self._project_dir.exists():
            return []
        return [
            f.stem for f in self._project_dir.iterdir()
            if f.is_file() and f.suffix == ".md"
        ]
    
    def list_all(self) -> dict[str, list[str]]:
        """列出所有记忆
        
        Returns:
            包含 user 和 project 键的字典
        """
        return {
            "user": self.list_user(),
            "project": self.list_project(),
        }
    
    def get_agent_memory(self, agent_name: str = "agent") -> str | None:
        """获取智能体记忆（agent.md）
        
        Args:
            agent_name: 智能体名称
            
        Returns:
            智能体记忆内容
        """
        return self.load(agent_name)
    
    def save_agent_memory(self, content: str, agent_name: str = "agent", project: bool = False) -> Path:
        """保存智能体记忆
        
        Args:
            content: 记忆内容
            agent_name: 智能体名称
            project: 是否保存为项目级
            
        Returns:
            保存的文件路径
        """
        if project:
            return self.save_project(agent_name, content)
        return self.save_user(agent_name, content)
    
    def append_to_memory(self, key: str, content: str, project: bool = False) -> str:
        """追加内容到记忆
        
        Args:
            key: 记忆键
            content: 要追加的内容
            project: 是否追加到项目级记忆
            
        Returns:
            更新后的完整内容
        """
        existing = self.load_project(key) if project else self.load_user(key)
        new_content = f"{existing}\n\n{content}" if existing else content
        
        if project:
            self.save_project(key, new_content)
        else:
            self.save_user(key, new_content)
        
        return new_content
    
    def search(self, query: str, include_user: bool = True, include_project: bool = True) -> list[tuple[str, str, str]]:
        """搜索记忆
        
        Args:
            query: 搜索查询
            include_user: 是否搜索用户级记忆
            include_project: 是否搜索项目级记忆
            
        Returns:
            匹配的记忆列表，每项为 (source, key, content) 元组
        """
        results: list[tuple[str, str, str]] = []
        query_lower = query.lower()
        
        if include_user:
            for key in self.list_user():
                content = self.load_user(key)
                if content and query_lower in content.lower():
                    results.append(("user", key, content))
        
        if include_project:
            for key in self.list_project():
                content = self.load_project(key)
                if content and query_lower in content.lower():
                    results.append(("project", key, content))
        
        return results

