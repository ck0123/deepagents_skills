"""Agent 专用工具

提供与技能系统交互的工具函数。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from deepagents_skills.skills.executor import SkillExecutor
    from deepagents_skills.skills.registry import SkillRegistry


def create_skill_tools(registry: "SkillRegistry", executor: "SkillExecutor") -> dict[str, callable]:
    """创建技能工具集
    
    Args:
        registry: 技能注册表
        executor: 技能执行器
        
    Returns:
        工具函数字典
    """
    
    def list_skills() -> list[dict[str, Any]]:
        """列出所有可用技能
        
        Returns:
            技能摘要列表，每项包含 name, description, triggers, source, priority
        """
        return executor.list_available_skills()
    
    def read_skill(skill_name: str) -> dict[str, Any]:
        """读取技能的完整内容
        
        Args:
            skill_name: 技能名称
            
        Returns:
            包含技能详细信息的字典，或错误信息
        """
        skill = registry.get(skill_name)
        if skill is None:
            return {"error": f"技能 '{skill_name}' 不存在"}
        
        return {
            "name": skill.name,
            "description": skill.description,
            "instructions": skill.instructions,
            "triggers": skill.triggers,
            "dependencies": skill.dependencies,
            "source": skill.source.value,
            "path": str(skill.path),
            "directory": str(skill.directory),
            "supporting_files": [str(f) for f in skill.list_supporting_files()],
        }
    
    def match_skills(query: str) -> list[dict[str, Any]]:
        """根据查询匹配合适的技能
        
        Args:
            query: 用户查询文本
            
        Returns:
            匹配的技能摘要列表
        """
        matched = executor.match(query)
        return [
            {
                "name": skill.name,
                "description": skill.description,
                "triggers": skill.triggers,
                "source": skill.source.value,
                "priority": skill.priority,
            }
            for skill in matched
        ]
    
    def get_skill_instructions(skill_name: str) -> str:
        """获取技能的指令文本
        
        Args:
            skill_name: 技能名称
            
        Returns:
            技能指令文本，或错误信息
        """
        instructions = executor.get_skill_instructions(skill_name)
        if instructions is None:
            return f"错误: 技能 '{skill_name}' 不存在"
        return instructions
    
    def execute_skill_chain(skill_names: list[str], query: str = "") -> dict[str, Any]:
        """执行技能链
        
        Args:
            skill_names: 要执行的技能名称列表
            query: 用户查询（可选）
            
        Returns:
            执行结果
        """
        from deepagents_skills.skills.chain import SkillChain
        from deepagents_skills.skills.executor import ExecutionContext
        
        chain = SkillChain.from_list(executor, skill_names)
        context = ExecutionContext(query=query)
        result = chain.execute(context)
        
        return {
            "success": result.success,
            "steps": [
                {
                    "skill": step.skill.name if step.skill.metadata else "unknown",
                    "success": step.success,
                    "output": step.output,
                    "error": step.error,
                }
                for step in result.steps
            ],
            "skipped": result.skipped,
            "final_output": result.final_output,
        }
    
    return {
        "list_skills": list_skills,
        "read_skill": read_skill,
        "match_skills": match_skills,
        "get_skill_instructions": get_skill_instructions,
        "execute_skill_chain": execute_skill_chain,
    }


class SkillTools:
    """技能工具类
    
    封装技能系统的工具方法。
    
    Example:
        >>> tools = SkillTools(registry, executor)
        >>> skills = tools.list_skills()
        >>> instructions = tools.read_skill("web-research")
    """
    
    def __init__(self, registry: "SkillRegistry", executor: "SkillExecutor"):
        """初始化工具类
        
        Args:
            registry: 技能注册表
            executor: 技能执行器
        """
        self.registry = registry
        self.executor = executor
        self._tools = create_skill_tools(registry, executor)
    
    def list_skills(self) -> list[dict[str, Any]]:
        """列出所有可用技能"""
        return self._tools["list_skills"]()
    
    def read_skill(self, skill_name: str) -> dict[str, Any]:
        """读取技能的完整内容"""
        return self._tools["read_skill"](skill_name)
    
    def match_skills(self, query: str) -> list[dict[str, Any]]:
        """根据查询匹配合适的技能"""
        return self._tools["match_skills"](query)
    
    def get_skill_instructions(self, skill_name: str) -> str:
        """获取技能的指令文本"""
        return self._tools["get_skill_instructions"](skill_name)
    
    def execute_skill_chain(self, skill_names: list[str], query: str = "") -> dict[str, Any]:
        """执行技能链"""
        return self._tools["execute_skill_chain"](skill_names, query)
    
    def get_tools_dict(self) -> dict[str, callable]:
        """获取工具函数字典"""
        return self._tools

