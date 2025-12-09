"""SkillAgent 核心类

串联 Skills 和 Memory 功能的主智能体类。
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Callable

from deepagents_skills.agent.prompt import SkillsPromptBuilder
from deepagents_skills.agent.tools import SkillTools
from deepagents_skills.config import Config
from deepagents_skills.memory.middleware import MemoryMiddleware
from deepagents_skills.memory.store import MemoryStore
from deepagents_skills.skills.discovery import SkillDiscovery
from deepagents_skills.skills.executor import ExecutionContext, ExecutionResult, SkillExecutor
from deepagents_skills.skills.registry import SkillRegistry

if TYPE_CHECKING:
    from deepagents_skills.skills.model import Skill


class SkillAgent:
    """技能智能体
    
    串联 Skills 和 Memory 功能的主智能体类。
    
    功能：
    - 自动发现和加载技能
    - 根据用户请求匹配和执行技能
    - 管理长期记忆
    - 支持技能链式调用
    
    Example:
        >>> from deepagents_skills import SkillAgent, Config
        >>> 
        >>> # 加载配置并创建智能体
        >>> config = Config.load("config.json")
        >>> agent = SkillAgent(config)
        >>> 
        >>> # 处理用户请求
        >>> response = agent.process("帮我研究量子计算的最新进展")
        >>> 
        >>> # 手动执行技能
        >>> result = agent.execute_skill("web-research")
        >>> 
        >>> # 执行技能链
        >>> results = agent.execute_chain(["web-research", "summarize"])
    """
    
    def __init__(
        self,
        config: Config | None = None,
        agent_name: str = "agent",
        auto_discover: bool = True,
    ):
        """初始化智能体
        
        Args:
            config: 配置实例，如果为 None 则使用默认配置
            agent_name: 智能体名称
            auto_discover: 是否自动发现技能
        """
        self.config = config or Config.default()
        self.agent_name = agent_name
        
        # 初始化技能系统
        self._registry = SkillRegistry()
        self._discovery = SkillDiscovery(self.config)
        self._executor = SkillExecutor(self._registry)
        
        # 初始化记忆系统
        self._memory_store = MemoryStore(self.config)
        self._memory_middleware = MemoryMiddleware(
            self.config,
            self._memory_store,
            agent_name,
        )
        
        # 初始化工具
        self._tools = SkillTools(self._registry, self._executor)
        
        # 初始化提示词构建器
        self._prompt_builder = SkillsPromptBuilder(
            user_skills_dir=str(self.config.skills.user_dir),
            project_skills_dir=str(self.config.skills.project_dir),
        )
        
        # 自动发现技能
        if auto_discover:
            self.discover_skills()
    
    @property
    def registry(self) -> SkillRegistry:
        """获取技能注册表"""
        return self._registry
    
    @property
    def executor(self) -> SkillExecutor:
        """获取技能执行器"""
        return self._executor
    
    @property
    def memory_store(self) -> MemoryStore:
        """获取记忆存储"""
        return self._memory_store
    
    @property
    def tools(self) -> SkillTools:
        """获取技能工具"""
        return self._tools
    
    def discover_skills(self) -> int:
        """发现并加载技能
        
        Returns:
            加载的技能数量
        """
        count = self._registry.load_from_discovery(self._discovery)
        self._prompt_builder.set_skills(self._registry.get_all())
        return count
    
    def refresh_skills(self) -> int:
        """刷新技能列表
        
        Returns:
            加载的技能数量
        """
        count = self._registry.refresh(self._discovery)
        self._prompt_builder.set_skills(self._registry.get_all())
        return count
    
    def get_skill(self, name: str) -> "Skill" | None:
        """获取技能
        
        Args:
            name: 技能名称
            
        Returns:
            技能实例，不存在则返回 None
        """
        return self._registry.get(name)
    
    def list_skills(self) -> list[dict[str, Any]]:
        """列出所有可用技能
        
        Returns:
            技能摘要列表
        """
        return self._tools.list_skills()
    
    def match_skills(self, query: str) -> list["Skill"]:
        """根据查询匹配技能
        
        Args:
            query: 用户查询文本
            
        Returns:
            匹配的技能列表
        """
        return self._executor.match(query)
    
    def execute_skill(
        self,
        skill_name: str,
        context: ExecutionContext | None = None,
    ) -> ExecutionResult | None:
        """执行技能
        
        Args:
            skill_name: 技能名称
            context: 执行上下文
            
        Returns:
            执行结果，技能不存在则返回 None
        """
        skill = self._registry.get(skill_name)
        if skill is None:
            return None
        return self._executor.execute(skill, context)
    
    def execute_skill_with_dependencies(
        self,
        skill_name: str,
        context: ExecutionContext | None = None,
    ) -> list[ExecutionResult]:
        """执行技能及其依赖
        
        Args:
            skill_name: 技能名称
            context: 执行上下文
            
        Returns:
            执行结果列表
        """
        skill = self._registry.get(skill_name)
        if skill is None:
            return []
        return self._executor.execute_with_dependencies(skill, context)
    
    def execute_chain(
        self,
        skill_names: list[str],
        context: ExecutionContext | None = None,
    ) -> dict[str, Any]:
        """执行技能链
        
        Args:
            skill_names: 技能名称列表
            context: 执行上下文
            
        Returns:
            执行结果
        """
        return self._tools.execute_skill_chain(skill_names, context.query if context else "")
    
    def process(
        self,
        query: str,
        auto_execute: bool = False,
        max_skills: int = 1,
    ) -> dict[str, Any]:
        """处理用户请求
        
        匹配并可选地执行相关技能。
        
        Args:
            query: 用户查询文本
            auto_execute: 是否自动执行匹配的技能
            max_skills: 最多执行的技能数量
            
        Returns:
            处理结果，包含匹配的技能和执行结果
        """
        # 匹配技能
        matched_skills = self.match_skills(query)
        
        result = {
            "query": query,
            "matched_skills": [
                {
                    "name": skill.name,
                    "description": skill.description,
                    "priority": skill.priority,
                }
                for skill in matched_skills
            ],
            "executed": False,
            "execution_results": [],
        }
        
        # 自动执行
        if auto_execute and matched_skills:
            context = ExecutionContext(query=query)
            execution_results = self._executor.auto_execute(query, context, max_skills)
            
            result["executed"] = True
            result["execution_results"] = [
                {
                    "skill": r.skill.name,
                    "success": r.success,
                    "output": r.output,
                    "error": r.error,
                }
                for r in execution_results
            ]
        
        return result
    
    def get_skill_instructions(self, skill_name: str) -> str | None:
        """获取技能指令
        
        Args:
            skill_name: 技能名称
            
        Returns:
            技能指令文本
        """
        return self._executor.get_skill_instructions(skill_name)
    
    # 记忆相关方法
    
    def load_memory(self, key: str = "agent") -> str | None:
        """加载记忆
        
        Args:
            key: 记忆键
            
        Returns:
            记忆内容
        """
        return self._memory_store.load(key)
    
    def save_memory(self, content: str, key: str = "agent", project: bool = False) -> None:
        """保存记忆
        
        Args:
            content: 记忆内容
            key: 记忆键
            project: 是否保存为项目级记忆
        """
        if project:
            self._memory_store.save_project(key, content)
        else:
            self._memory_store.save_user(key, content)
    
    def get_memory_context(self) -> dict[str, Any]:
        """获取记忆上下文
        
        Returns:
            记忆上下文字典
        """
        return self._memory_middleware.get_memory_context()
    
    # 提示词相关方法
    
    def build_system_prompt(self, base_prompt: str | None = None) -> str:
        """构建系统提示词
        
        包含技能系统和记忆系统的完整提示词。
        
        Args:
            base_prompt: 基础提示词
            
        Returns:
            完整的系统提示词
        """
        # 构建技能提示词
        skills_prompt = self._prompt_builder.build(base_prompt)
        
        # 注入记忆
        full_prompt = self._memory_middleware.inject_memory(skills_prompt)
        
        return full_prompt
    
    def get_tools_dict(self) -> dict[str, Callable]:
        """获取工具函数字典
        
        用于集成到 LangChain 等框架。
        
        Returns:
            工具函数字典
        """
        return self._tools.get_tools_dict()
    
    def set_skill_handler(self, handler: Callable[["Skill", ExecutionContext], Any]) -> None:
        """设置技能处理器
        
        自定义技能的执行方式。
        
        Args:
            handler: 技能处理器函数
        """
        self._executor.set_handler(handler)
    
    def ensure_dirs(self) -> None:
        """确保所有必要的目录存在"""
        self.config.ensure_dirs()
    
    def __repr__(self) -> str:
        return f"SkillAgent(name={self.agent_name!r}, skills={len(self._registry)})"


def create_skill_agent(
    config_path: str | None = None,
    agent_name: str = "agent",
) -> SkillAgent:
    """创建技能智能体的便捷函数
    
    Args:
        config_path: 配置文件路径
        agent_name: 智能体名称
        
    Returns:
        SkillAgent 实例
    """
    config = Config.load(config_path)
    return SkillAgent(config, agent_name)

