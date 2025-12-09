"""技能注册表

统一管理所有已发现的技能，提供按名称、触发词、优先级索引的能力。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterator

from deepagents_skills.skills.model import Skill, SkillSource

if TYPE_CHECKING:
    from deepagents_skills.config import Config
    from deepagents_skills.skills.discovery import SkillDiscovery


class SkillRegistry:
    """技能注册表
    
    统一管理所有已发现的技能，提供多种索引方式。
    
    Example:
        >>> registry = SkillRegistry()
        >>> registry.register(skill)
        >>> skill = registry.get("web-research")
        >>> matched = registry.match("帮我研究一下量子计算")
    """
    
    def __init__(self):
        """初始化注册表"""
        self._skills: dict[str, Skill] = {}
        self._trigger_index: dict[str, list[str]] = {}  # trigger -> [skill_names]
    
    def register(self, skill: Skill) -> None:
        """注册技能
        
        如果已存在同名技能，会根据来源和优先级决定是否覆盖：
        - 项目级技能总是覆盖用户级技能
        - 同级别下，高优先级覆盖低优先级
        
        Args:
            skill: 要注册的技能
        """
        existing = self._skills.get(skill.name)
        
        if existing:
            # 决定是否覆盖
            should_replace = False
            
            # 项目级覆盖用户级
            if skill.source == SkillSource.PROJECT and existing.source == SkillSource.USER:
                should_replace = True
            # 同级别下，高优先级覆盖
            elif skill.source == existing.source and skill.priority > existing.priority:
                should_replace = True
            
            if not should_replace:
                return
            
            # 移除旧技能的触发词索引
            self._remove_trigger_index(existing)
        
        # 注册新技能
        self._skills[skill.name] = skill
        self._add_trigger_index(skill)
    
    def _add_trigger_index(self, skill: Skill) -> None:
        """添加触发词索引"""
        for trigger in skill.triggers:
            trigger_lower = trigger.lower()
            if trigger_lower not in self._trigger_index:
                self._trigger_index[trigger_lower] = []
            if skill.name not in self._trigger_index[trigger_lower]:
                self._trigger_index[trigger_lower].append(skill.name)
    
    def _remove_trigger_index(self, skill: Skill) -> None:
        """移除触发词索引"""
        for trigger in skill.triggers:
            trigger_lower = trigger.lower()
            if trigger_lower in self._trigger_index:
                if skill.name in self._trigger_index[trigger_lower]:
                    self._trigger_index[trigger_lower].remove(skill.name)
                if not self._trigger_index[trigger_lower]:
                    del self._trigger_index[trigger_lower]
    
    def unregister(self, name: str) -> Skill | None:
        """取消注册技能
        
        Args:
            name: 技能名称
            
        Returns:
            被移除的技能，如果不存在则返回 None
        """
        skill = self._skills.pop(name, None)
        if skill:
            self._remove_trigger_index(skill)
        return skill
    
    def get(self, name: str) -> Skill | None:
        """按名称获取技能
        
        Args:
            name: 技能名称
            
        Returns:
            技能实例，不存在则返回 None
        """
        return self._skills.get(name)
    
    def get_all(self) -> list[Skill]:
        """获取所有技能
        
        Returns:
            技能列表，按优先级降序排序
        """
        return sorted(
            self._skills.values(),
            key=lambda s: (-s.priority, s.name)
        )
    
    def match(self, query: str) -> list[Skill]:
        """根据查询匹配技能
        
        使用触发词进行匹配，返回按优先级排序的结果。
        
        Args:
            query: 用户查询文本
            
        Returns:
            匹配的技能列表，按优先级降序排序
        """
        matched_names: set[str] = set()
        query_lower = query.lower()
        
        # 检查每个触发词
        for trigger, skill_names in self._trigger_index.items():
            if trigger in query_lower:
                matched_names.update(skill_names)
        
        # 获取技能并排序
        matched_skills = [
            self._skills[name]
            for name in matched_names
            if name in self._skills
        ]
        
        return sorted(
            matched_skills,
            key=lambda s: (-s.priority, s.name)
        )
    
    def match_by_triggers(self, triggers: list[str]) -> list[Skill]:
        """根据触发词列表匹配技能
        
        Args:
            triggers: 触发词列表
            
        Returns:
            匹配的技能列表
        """
        matched_names: set[str] = set()
        
        for trigger in triggers:
            trigger_lower = trigger.lower()
            if trigger_lower in self._trigger_index:
                matched_names.update(self._trigger_index[trigger_lower])
        
        matched_skills = [
            self._skills[name]
            for name in matched_names
            if name in self._skills
        ]
        
        return sorted(
            matched_skills,
            key=lambda s: (-s.priority, s.name)
        )
    
    def filter_by_source(self, source: SkillSource) -> list[Skill]:
        """按来源筛选技能
        
        Args:
            source: 技能来源
            
        Returns:
            筛选后的技能列表
        """
        return [
            skill for skill in self._skills.values()
            if skill.source == source
        ]
    
    def clear(self) -> None:
        """清空注册表"""
        self._skills.clear()
        self._trigger_index.clear()
    
    def load_from_discovery(self, discovery: "SkillDiscovery") -> int:
        """从发现服务加载技能
        
        Args:
            discovery: 技能发现服务
            
        Returns:
            加载的技能数量
        """
        skills = discovery.discover_all()
        for skill in skills:
            self.register(skill)
        return len(skills)
    
    def refresh(self, discovery: "SkillDiscovery") -> int:
        """刷新注册表
        
        清空现有技能并重新加载。
        
        Args:
            discovery: 技能发现服务
            
        Returns:
            加载的技能数量
        """
        self.clear()
        return self.load_from_discovery(discovery)
    
    def __len__(self) -> int:
        return len(self._skills)
    
    def __contains__(self, name: str) -> bool:
        return name in self._skills
    
    def __iter__(self) -> Iterator[Skill]:
        return iter(self._skills.values())
    
    def __repr__(self) -> str:
        return f"SkillRegistry(skills={len(self._skills)})"

