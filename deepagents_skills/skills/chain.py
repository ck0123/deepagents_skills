"""技能链和流水线

支持技能的链式调用和条件分支执行。
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable

from deepagents_skills.skills.executor import ExecutionContext, ExecutionResult
from deepagents_skills.skills.model import Skill

if TYPE_CHECKING:
    from deepagents_skills.skills.executor import SkillExecutor


class ChainMode(Enum):
    """链式执行模式"""
    SEQUENTIAL = "sequential"  # 串行执行
    PARALLEL = "parallel"      # 并行执行


@dataclass
class ChainStep:
    """链式执行步骤
    
    Attributes:
        skill_name: 技能名称
        condition: 执行条件（可选）
        transform: 结果转换函数（可选）
    """
    skill_name: str
    condition: Callable[[ExecutionContext], bool] | None = None
    transform: Callable[[Any, ExecutionContext], Any] | None = None
    
    def should_execute(self, context: ExecutionContext) -> bool:
        """检查是否应该执行此步骤"""
        if self.condition is None:
            return True
        return self.condition(context)
    
    def transform_result(self, result: Any, context: ExecutionContext) -> Any:
        """转换执行结果"""
        if self.transform is None:
            return result
        return self.transform(result, context)


@dataclass
class ChainResult:
    """链式执行结果
    
    Attributes:
        steps: 各步骤的执行结果
        success: 是否全部成功
        final_output: 最终输出
    """
    steps: list[ExecutionResult] = field(default_factory=list)
    success: bool = True
    final_output: Any = None
    skipped: list[str] = field(default_factory=list)  # 跳过的步骤
    
    def add_result(self, result: ExecutionResult) -> None:
        """添加步骤结果"""
        self.steps.append(result)
        if not result.success:
            self.success = False
    
    def add_skipped(self, skill_name: str) -> None:
        """添加跳过的步骤"""
        self.skipped.append(skill_name)


class SkillChain:
    """技能链
    
    定义技能的执行序列，支持条件执行和结果转换。
    
    Example:
        >>> chain = SkillChain(executor)
        >>> chain.add("web-research")
        >>> chain.add("summarize", condition=lambda ctx: len(ctx.results) > 0)
        >>> chain.add("save-report")
        >>> result = chain.execute(context)
    """
    
    def __init__(self, executor: "SkillExecutor"):
        """初始化技能链
        
        Args:
            executor: 技能执行器
        """
        self.executor = executor
        self._steps: list[ChainStep] = []
    
    def add(
        self,
        skill_name: str,
        condition: Callable[[ExecutionContext], bool] | None = None,
        transform: Callable[[Any, ExecutionContext], Any] | None = None,
    ) -> "SkillChain":
        """添加执行步骤
        
        Args:
            skill_name: 技能名称
            condition: 执行条件
            transform: 结果转换函数
            
        Returns:
            self，支持链式调用
        """
        self._steps.append(ChainStep(
            skill_name=skill_name,
            condition=condition,
            transform=transform,
        ))
        return self
    
    def clear(self) -> None:
        """清空步骤"""
        self._steps.clear()
    
    def execute(self, context: ExecutionContext | None = None) -> ChainResult:
        """执行技能链
        
        按顺序执行所有步骤。
        
        Args:
            context: 执行上下文
            
        Returns:
            链式执行结果
        """
        if context is None:
            context = ExecutionContext()
        
        chain_result = ChainResult()
        
        for step in self._steps:
            # 检查执行条件
            if not step.should_execute(context):
                chain_result.add_skipped(step.skill_name)
                continue
            
            # 获取技能
            skill = self.executor.registry.get(step.skill_name)
            if skill is None:
                chain_result.add_result(ExecutionResult(
                    skill=Skill(
                        metadata=None,
                        content="",
                        instructions="",
                        path=None,
                        source=None,
                    ),
                    success=False,
                    error=f"技能 '{step.skill_name}' 不存在",
                ))
                chain_result.success = False
                break
            
            # 执行技能
            result = self.executor.execute(skill, context)
            
            # 转换结果
            if result.success and step.transform:
                result.output = step.transform_result(result.output, context)
                context.set_result(skill.name, result.output)
            
            chain_result.add_result(result)
            
            # 如果失败，停止执行
            if not result.success:
                break
        
        # 设置最终输出
        if chain_result.steps:
            chain_result.final_output = chain_result.steps[-1].output
        
        return chain_result
    
    @classmethod
    def from_list(
        cls,
        executor: "SkillExecutor",
        skill_names: list[str],
    ) -> "SkillChain":
        """从技能名称列表创建链
        
        Args:
            executor: 技能执行器
            skill_names: 技能名称列表
            
        Returns:
            技能链实例
        """
        chain = cls(executor)
        for name in skill_names:
            chain.add(name)
        return chain


class SkillPipeline:
    """技能流水线
    
    支持更复杂的执行模式，包括并行执行和条件分支。
    
    Example:
        >>> pipeline = SkillPipeline(executor)
        >>> 
        >>> # 添加并行步骤
        >>> pipeline.add_parallel(["skill-a", "skill-b"])
        >>> 
        >>> # 添加条件分支
        >>> pipeline.add_branch(
        ...     condition=lambda ctx: ctx.get_variable("type") == "research",
        ...     if_true="web-research",
        ...     if_false="local-search",
        ... )
        >>> 
        >>> result = await pipeline.execute_async(context)
    """
    
    def __init__(self, executor: "SkillExecutor"):
        """初始化流水线
        
        Args:
            executor: 技能执行器
        """
        self.executor = executor
        self._stages: list[dict[str, Any]] = []
    
    def add_sequential(self, skill_names: list[str]) -> "SkillPipeline":
        """添加串行执行阶段
        
        Args:
            skill_names: 技能名称列表
            
        Returns:
            self
        """
        self._stages.append({
            "mode": ChainMode.SEQUENTIAL,
            "skills": skill_names,
        })
        return self
    
    def add_parallel(self, skill_names: list[str]) -> "SkillPipeline":
        """添加并行执行阶段
        
        Args:
            skill_names: 技能名称列表
            
        Returns:
            self
        """
        self._stages.append({
            "mode": ChainMode.PARALLEL,
            "skills": skill_names,
        })
        return self
    
    def add_branch(
        self,
        condition: Callable[[ExecutionContext], bool],
        if_true: str | list[str],
        if_false: str | list[str] | None = None,
    ) -> "SkillPipeline":
        """添加条件分支
        
        Args:
            condition: 条件函数
            if_true: 条件为真时执行的技能
            if_false: 条件为假时执行的技能
            
        Returns:
            self
        """
        self._stages.append({
            "mode": "branch",
            "condition": condition,
            "if_true": if_true if isinstance(if_true, list) else [if_true],
            "if_false": (if_false if isinstance(if_false, list) else [if_false]) if if_false else [],
        })
        return self
    
    def execute(self, context: ExecutionContext | None = None) -> ChainResult:
        """同步执行流水线
        
        Args:
            context: 执行上下文
            
        Returns:
            执行结果
        """
        if context is None:
            context = ExecutionContext()
        
        chain_result = ChainResult()
        
        for stage in self._stages:
            mode = stage["mode"]
            
            if mode == ChainMode.SEQUENTIAL:
                for skill_name in stage["skills"]:
                    skill = self.executor.registry.get(skill_name)
                    if skill is None:
                        chain_result.add_skipped(skill_name)
                        continue
                    
                    result = self.executor.execute(skill, context)
                    chain_result.add_result(result)
                    
                    if not result.success:
                        return chain_result
            
            elif mode == ChainMode.PARALLEL:
                # 同步模式下，并行执行退化为串行
                for skill_name in stage["skills"]:
                    skill = self.executor.registry.get(skill_name)
                    if skill is None:
                        chain_result.add_skipped(skill_name)
                        continue
                    
                    result = self.executor.execute(skill, context)
                    chain_result.add_result(result)
            
            elif mode == "branch":
                condition = stage["condition"]
                skills_to_run = stage["if_true"] if condition(context) else stage["if_false"]
                
                for skill_name in skills_to_run:
                    skill = self.executor.registry.get(skill_name)
                    if skill is None:
                        chain_result.add_skipped(skill_name)
                        continue
                    
                    result = self.executor.execute(skill, context)
                    chain_result.add_result(result)
                    
                    if not result.success:
                        return chain_result
        
        if chain_result.steps:
            chain_result.final_output = chain_result.steps[-1].output
        
        return chain_result
    
    async def execute_async(self, context: ExecutionContext | None = None) -> ChainResult:
        """异步执行流水线
        
        支持真正的并行执行。
        
        Args:
            context: 执行上下文
            
        Returns:
            执行结果
        """
        if context is None:
            context = ExecutionContext()
        
        chain_result = ChainResult()
        
        for stage in self._stages:
            mode = stage["mode"]
            
            if mode == ChainMode.SEQUENTIAL:
                for skill_name in stage["skills"]:
                    skill = self.executor.registry.get(skill_name)
                    if skill is None:
                        chain_result.add_skipped(skill_name)
                        continue
                    
                    result = self.executor.execute(skill, context)
                    chain_result.add_result(result)
                    
                    if not result.success:
                        return chain_result
            
            elif mode == ChainMode.PARALLEL:
                # 并行执行
                async def execute_skill(skill_name: str) -> ExecutionResult | None:
                    skill = self.executor.registry.get(skill_name)
                    if skill is None:
                        return None
                    return self.executor.execute(skill, context)
                
                tasks = [execute_skill(name) for name in stage["skills"]]
                results = await asyncio.gather(*tasks)
                
                for i, result in enumerate(results):
                    if result is None:
                        chain_result.add_skipped(stage["skills"][i])
                    else:
                        chain_result.add_result(result)
            
            elif mode == "branch":
                condition = stage["condition"]
                skills_to_run = stage["if_true"] if condition(context) else stage["if_false"]
                
                for skill_name in skills_to_run:
                    skill = self.executor.registry.get(skill_name)
                    if skill is None:
                        chain_result.add_skipped(skill_name)
                        continue
                    
                    result = self.executor.execute(skill, context)
                    chain_result.add_result(result)
                    
                    if not result.success:
                        return chain_result
        
        if chain_result.steps:
            chain_result.final_output = chain_result.steps[-1].output
        
        return chain_result
    
    def clear(self) -> None:
        """清空流水线"""
        self._stages.clear()

