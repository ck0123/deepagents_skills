"""技能模块

提供技能的定义、加载、发现、注册和执行功能。
"""

from deepagents_skills.skills.model import Skill, SkillMetadata, SkillSource
from deepagents_skills.skills.loader import load_skill, load_skill_from_directory, list_skills_in_directory
from deepagents_skills.skills.discovery import SkillDiscovery, discover_skills
from deepagents_skills.skills.registry import SkillRegistry
from deepagents_skills.skills.executor import SkillExecutor, ExecutionContext, ExecutionResult
from deepagents_skills.skills.chain import SkillChain, SkillPipeline, ChainResult, ChainMode

__all__ = [
    # 模型
    "Skill",
    "SkillMetadata",
    "SkillSource",
    
    # 加载
    "load_skill",
    "load_skill_from_directory",
    "list_skills_in_directory",
    
    # 发现
    "SkillDiscovery",
    "discover_skills",
    
    # 注册表
    "SkillRegistry",
    
    # 执行
    "SkillExecutor",
    "ExecutionContext",
    "ExecutionResult",
    
    # 链
    "SkillChain",
    "SkillPipeline",
    "ChainResult",
    "ChainMode",
]
