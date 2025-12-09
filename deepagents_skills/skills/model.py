"""技能数据模型

定义技能的元数据和完整技能类。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class SkillSource(Enum):
    """技能来源"""
    USER = "user"       # 用户级技能 (~/.deepagents/skills/)
    PROJECT = "project" # 项目级技能 (.deepagents/skills/)


@dataclass
class SkillMetadata:
    """技能元数据
    
    从 SKILL.md 的 YAML frontmatter 解析得到。
    
    Attributes:
        name: 技能名称（唯一标识符）
        description: 技能描述
        triggers: 触发关键词列表，用于自动匹配
        dependencies: 依赖的其他技能名称列表
        priority: 优先级（越高越优先），默认为 0
    """
    name: str
    description: str
    triggers: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    priority: int = 0
    
    def matches(self, query: str) -> bool:
        """检查查询是否匹配此技能的触发词
        
        Args:
            query: 用户查询文本
            
        Returns:
            如果查询包含任何触发词则返回 True
        """
        query_lower = query.lower()
        for trigger in self.triggers:
            if trigger.lower() in query_lower:
                return True
        return False
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "triggers": self.triggers,
            "dependencies": self.dependencies,
            "priority": self.priority,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SkillMetadata":
        """从字典创建"""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            triggers=data.get("triggers", []),
            dependencies=data.get("dependencies", []),
            priority=data.get("priority", 0),
        )


@dataclass
class Skill:
    """完整技能类
    
    包含元数据、指令内容和文件路径。
    
    Attributes:
        metadata: 技能元数据
        content: SKILL.md 的完整内容（包括 frontmatter 后的指令部分）
        instructions: 技能指令（不包括 frontmatter 的 Markdown 内容）
        path: SKILL.md 文件的路径
        source: 技能来源（用户级或项目级）
        directory: 技能目录路径（包含 SKILL.md 和其他支持文件）
    """
    metadata: SkillMetadata
    content: str
    instructions: str
    path: Path
    source: SkillSource
    
    @property
    def name(self) -> str:
        """技能名称"""
        return self.metadata.name
    
    @property
    def description(self) -> str:
        """技能描述"""
        return self.metadata.description
    
    @property
    def directory(self) -> Path:
        """技能目录路径"""
        return self.path.parent
    
    @property
    def triggers(self) -> list[str]:
        """触发词列表"""
        return self.metadata.triggers
    
    @property
    def dependencies(self) -> list[str]:
        """依赖技能列表"""
        return self.metadata.dependencies
    
    @property
    def priority(self) -> int:
        """优先级"""
        return self.metadata.priority
    
    def matches(self, query: str) -> bool:
        """检查查询是否匹配此技能"""
        return self.metadata.matches(query)
    
    def list_supporting_files(self) -> list[Path]:
        """列出技能目录中的支持文件（除 SKILL.md 外的文件）
        
        Returns:
            支持文件路径列表
        """
        if not self.directory.exists():
            return []
        return [
            f for f in self.directory.iterdir()
            if f.is_file() and f.name != "SKILL.md"
        ]
    
    def get_supporting_file(self, filename: str) -> Path | None:
        """获取支持文件的路径
        
        Args:
            filename: 文件名
            
        Returns:
            文件路径，如果不存在则返回 None
        """
        file_path = self.directory / filename
        if file_path.exists() and file_path.is_file():
            return file_path
        return None
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            **self.metadata.to_dict(),
            "content": self.content,
            "instructions": self.instructions,
            "path": str(self.path),
            "source": self.source.value,
            "directory": str(self.directory),
        }
    
    def __repr__(self) -> str:
        return f"Skill(name={self.name!r}, source={self.source.value}, path={self.path})"

