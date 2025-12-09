"""动态发现服务

扫描配置中指定的目录，自动发现所有可用技能。
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from deepagents_skills.skills.loader import list_skills_in_directory
from deepagents_skills.skills.model import Skill, SkillSource

if TYPE_CHECKING:
    from deepagents_skills.config import Config


class SkillDiscovery:
    """技能发现服务
    
    扫描用户级和项目级目录，发现所有可用技能。
    项目级技能会覆盖同名的用户级技能。
    
    Example:
        >>> from deepagents_skills import Config
        >>> config = Config.load("config.json")
        >>> discovery = SkillDiscovery(config)
        >>> skills = discovery.discover_all()
        >>> for skill in skills:
        ...     print(f"{skill.name}: {skill.description}")
    """
    
    def __init__(self, config: "Config"):
        """初始化发现服务
        
        Args:
            config: 配置实例
        """
        self.config = config
        self._user_skills_dir = config.skills.user_dir
        self._project_skills_dir = config.skills.project_dir
    
    def discover_user_skills(self) -> list[Skill]:
        """发现用户级技能
        
        Returns:
            用户级技能列表
        """
        return list_skills_in_directory(self._user_skills_dir, SkillSource.USER)
    
    def discover_project_skills(self) -> list[Skill]:
        """发现项目级技能
        
        Returns:
            项目级技能列表
        """
        return list_skills_in_directory(self._project_skills_dir, SkillSource.PROJECT)
    
    def discover_all(self) -> list[Skill]:
        """发现所有技能
        
        项目级技能会覆盖同名的用户级技能。
        
        Returns:
            合并后的技能列表
        """
        # 用字典存储，用于去重（项目级覆盖用户级）
        skills_dict: dict[str, Skill] = {}
        
        # 先加载用户级技能
        for skill in self.discover_user_skills():
            skills_dict[skill.name] = skill
        
        # 再加载项目级技能（覆盖同名用户级技能）
        for skill in self.discover_project_skills():
            skills_dict[skill.name] = skill
        
        return list(skills_dict.values())
    
    def discover_from_directory(self, directory: Path | str, source: SkillSource = SkillSource.USER) -> list[Skill]:
        """从指定目录发现技能
        
        Args:
            directory: 技能目录路径
            source: 技能来源
            
        Returns:
            技能列表
        """
        return list_skills_in_directory(Path(directory), source)
    
    def refresh(self) -> list[Skill]:
        """刷新技能列表
        
        重新扫描所有目录，返回最新的技能列表。
        
        Returns:
            最新的技能列表
        """
        return self.discover_all()


def discover_skills(
    *,
    user_skills_dir: Path | None = None,
    project_skills_dir: Path | None = None,
) -> list[Skill]:
    """发现技能的便捷函数
    
    Args:
        user_skills_dir: 用户级技能目录
        project_skills_dir: 项目级技能目录
        
    Returns:
        合并后的技能列表
    """
    skills_dict: dict[str, Skill] = {}
    
    if user_skills_dir:
        for skill in list_skills_in_directory(user_skills_dir, SkillSource.USER):
            skills_dict[skill.name] = skill
    
    if project_skills_dir:
        for skill in list_skills_in_directory(project_skills_dir, SkillSource.PROJECT):
            skills_dict[skill.name] = skill
    
    return list(skills_dict.values())

