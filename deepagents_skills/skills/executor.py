"""技能执行器

根据用户请求自动匹配和执行技能，支持依赖解析。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

from deepagents_skills.skills.model import Skill

if TYPE_CHECKING:
    from deepagents_skills.skills.registry import SkillRegistry


@dataclass
class ExecutionContext:
    """技能执行上下文
    
    包含执行技能所需的上下文信息。
    
    Attributes:
        query: 用户原始查询
        variables: 执行变量（可在技能之间传递）
        results: 已执行技能的结果
        metadata: 额外的元数据
    """
    query: str = ""
    variables: dict[str, Any] = field(default_factory=dict)
    results: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def set_result(self, skill_name: str, result: Any) -> None:
        """设置技能执行结果"""
        self.results[skill_name] = result
    
    def get_result(self, skill_name: str) -> Any | None:
        """获取技能执行结果"""
        return self.results.get(skill_name)
    
    def set_variable(self, name: str, value: Any) -> None:
        """设置变量"""
        self.variables[name] = value
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """获取变量"""
        return self.variables.get(name, default)


@dataclass
class ExecutionResult:
    """技能执行结果
    
    Attributes:
        skill: 执行的技能
        success: 是否成功
        output: 执行输出
        error: 错误信息（如果失败）
    """
    skill: Skill
    success: bool
    output: Any = None
    error: str | None = None


# 技能处理器类型：接收技能和上下文，返回输出
SkillHandler = Callable[[Skill, ExecutionContext], Any]


class SkillExecutor:
    """技能执行器
    
    负责技能的匹配、依赖解析和执行。
    
    Example:
        >>> executor = SkillExecutor(registry)
        >>> 
        >>> # 匹配技能
        >>> skills = executor.match("帮我研究量子计算")
        >>> 
        >>> # 执行单个技能
        >>> result = executor.execute(skill, context)
        >>> 
        >>> # 自动匹配并执行
        >>> results = executor.auto_execute("帮我研究量子计算")
    """
    
    def __init__(
        self,
        registry: "SkillRegistry",
        handler: SkillHandler | None = None,
    ):
        """初始化执行器
        
        Args:
            registry: 技能注册表
            handler: 技能处理器（如果为 None，则返回技能指令）
        """
        self.registry = registry
        self._handler = handler or self._default_handler
    
    def _default_handler(self, skill: Skill, context: ExecutionContext) -> str:
        """默认处理器：返回技能指令"""
        return skill.instructions
    
    def set_handler(self, handler: SkillHandler) -> None:
        """设置技能处理器
        
        Args:
            handler: 技能处理器函数
        """
        self._handler = handler
    
    def match(self, query: str) -> list[Skill]:
        """根据查询匹配技能
        
        Args:
            query: 用户查询文本
            
        Returns:
            匹配的技能列表，按优先级排序
        """
        return self.registry.match(query)
    
    def resolve_dependencies(self, skill: Skill, resolved: set[str] | None = None) -> list[Skill]:
        """解析技能依赖
        
        使用深度优先搜索解析依赖，处理循环依赖。
        
        Args:
            skill: 要解析依赖的技能
            resolved: 已解析的技能名称集合（用于检测循环依赖）
            
        Returns:
            按依赖顺序排列的技能列表（依赖在前）
        """
        if resolved is None:
            resolved = set()
        
        result: list[Skill] = []
        
        # 检测循环依赖
        if skill.name in resolved:
            return result
        
        resolved.add(skill.name)
        
        # 先解析依赖
        for dep_name in skill.dependencies:
            dep_skill = self.registry.get(dep_name)
            if dep_skill and dep_skill.name not in resolved:
                result.extend(self.resolve_dependencies(dep_skill, resolved))
        
        # 最后添加当前技能
        result.append(skill)
        
        return result
    
    def execute(
        self,
        skill: Skill,
        context: ExecutionContext | None = None,
    ) -> ExecutionResult:
        """执行单个技能
        
        Args:
            skill: 要执行的技能
            context: 执行上下文
            
        Returns:
            执行结果
        """
        if context is None:
            context = ExecutionContext()
        
        try:
            output = self._handler(skill, context)
            context.set_result(skill.name, output)
            return ExecutionResult(
                skill=skill,
                success=True,
                output=output,
            )
        except Exception as e:
            return ExecutionResult(
                skill=skill,
                success=False,
                error=str(e),
            )
    
    def execute_with_dependencies(
        self,
        skill: Skill,
        context: ExecutionContext | None = None,
    ) -> list[ExecutionResult]:
        """执行技能及其依赖
        
        按依赖顺序执行所有技能。
        
        Args:
            skill: 要执行的技能
            context: 执行上下文
            
        Returns:
            所有技能的执行结果列表
        """
        if context is None:
            context = ExecutionContext()
        
        # 解析依赖
        skills_to_execute = self.resolve_dependencies(skill)
        
        results: list[ExecutionResult] = []
        for s in skills_to_execute:
            result = self.execute(s, context)
            results.append(result)
            
            # 如果执行失败，停止后续执行
            if not result.success:
                break
        
        return results
    
    def auto_execute(
        self,
        query: str,
        context: ExecutionContext | None = None,
        max_skills: int = 1,
    ) -> list[ExecutionResult]:
        """自动匹配并执行技能
        
        根据查询自动匹配技能并执行。
        
        Args:
            query: 用户查询文本
            context: 执行上下文
            max_skills: 最多执行的技能数量
            
        Returns:
            执行结果列表
        """
        if context is None:
            context = ExecutionContext(query=query)
        else:
            context.query = query
        
        # 匹配技能
        matched_skills = self.match(query)
        
        if not matched_skills:
            return []
        
        # 限制执行数量
        skills_to_execute = matched_skills[:max_skills]
        
        results: list[ExecutionResult] = []
        for skill in skills_to_execute:
            # 执行技能及其依赖
            skill_results = self.execute_with_dependencies(skill, context)
            results.extend(skill_results)
        
        return results
    
    def get_skill_instructions(self, skill_name: str) -> str | None:
        """获取技能指令
        
        Args:
            skill_name: 技能名称
            
        Returns:
            技能指令文本，不存在则返回 None
        """
        skill = self.registry.get(skill_name)
        if skill:
            return skill.instructions
        return None
    
    def list_available_skills(self) -> list[dict[str, Any]]:
        """列出所有可用技能的摘要信息
        
        Returns:
            技能摘要列表
        """
        return [
            {
                "name": skill.name,
                "description": skill.description,
                "triggers": skill.triggers,
                "source": skill.source.value,
                "priority": skill.priority,
            }
            for skill in self.registry.get_all()
        ]

