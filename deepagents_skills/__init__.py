"""DeepAgents Skills - 智能体技能和记忆系统

让智能体能够动态发现、加载和执行特定任务的专业指令集。

主要功能:
- Skills: 技能发现、加载、匹配和执行
- Memory: 持久化记忆存储
- Agent: 串联 Skills 和 Memory 的智能体
- Chain: 技能链式调用和流水线

Example:
    >>> from deepagents_skills import SkillAgent, Config
    >>> 
    >>> # 加载配置并创建智能体
    >>> config = Config.load("config.json")
    >>> agent = SkillAgent(config)
    >>> 
    >>> # 列出可用技能
    >>> skills = agent.list_skills()
    >>> for skill in skills:
    ...     print(f"{skill['name']}: {skill['description']}")
    >>> 
    >>> # 处理用户请求（自动匹配技能）
    >>> response = agent.process("帮我研究量子计算的最新进展")
    >>> 
    >>> # 手动执行技能
    >>> result = agent.execute_skill("web-research")
    >>> 
    >>> # 执行技能链
    >>> results = agent.execute_chain(["web-research", "summarize", "save-report"])
"""

from deepagents_skills.config import Config
from deepagents_skills.agent.core import SkillAgent, create_skill_agent
from deepagents_skills.skills.model import Skill, SkillMetadata, SkillSource
from deepagents_skills.skills.registry import SkillRegistry
from deepagents_skills.skills.discovery import SkillDiscovery, discover_skills
from deepagents_skills.skills.executor import SkillExecutor, ExecutionContext, ExecutionResult
from deepagents_skills.skills.chain import SkillChain, SkillPipeline, ChainResult
from deepagents_skills.skills.loader import load_skill, load_skill_from_directory
from deepagents_skills.memory.store import MemoryStore, MemoryEntry
from deepagents_skills.memory.middleware import MemoryMiddleware, create_memory_middleware

__version__ = "0.1.0"

__all__ = [
    # 版本
    "__version__",
    
    # 配置
    "Config",
    
    # 智能体
    "SkillAgent",
    "create_skill_agent",
    
    # 技能模型
    "Skill",
    "SkillMetadata",
    "SkillSource",
    
    # 技能系统
    "SkillRegistry",
    "SkillDiscovery",
    "discover_skills",
    "SkillExecutor",
    "ExecutionContext",
    "ExecutionResult",
    
    # 技能链
    "SkillChain",
    "SkillPipeline",
    "ChainResult",
    
    # 技能加载
    "load_skill",
    "load_skill_from_directory",
    
    # 记忆系统
    "MemoryStore",
    "MemoryEntry",
    "MemoryMiddleware",
    "create_memory_middleware",
]
