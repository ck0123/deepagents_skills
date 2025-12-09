"""系统提示词模板

包含技能系统说明和动态注入已加载技能列表。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from deepagents_skills.skills.model import Skill


# 基础系统提示词
BASE_SYSTEM_PROMPT = """你是一个智能助手，拥有强大的技能系统和记忆能力。

# 核心能力

你可以：
1. 动态发现和使用各种技能来完成任务
2. 保存和检索长期记忆
3. 执行技能链来完成复杂任务

# 工作原则

- 简洁直接地回答，除非用户要求详细说明
- 完成任务后停止，不需要解释做了什么（除非被问到）
- 遵循现有代码的风格和约定
- 使用绝对路径进行文件操作
"""

# 技能系统提示词
SKILLS_SYSTEM_PROMPT = """
## 技能系统

你有一个技能库，提供专业能力和领域知识。

**技能目录：**
- 用户级技能: `{user_skills_dir}`
- 项目级技能: `{project_skills_dir}`

**可用技能：**

{skills_list}

### 如何使用技能（渐进式披露）

技能遵循**渐进式披露**模式 - 你知道它们存在（上面显示名称和描述），但只在需要时读取完整指令：

1. **识别何时应用技能**: 检查用户的任务是否匹配某个技能的描述
2. **读取技能的完整指令**: 使用 `read_skill` 工具读取技能的详细指令
3. **遵循技能的指令**: SKILL.md 包含步骤化的工作流程、最佳实践和示例
4. **访问支持文件**: 技能可能包含 Python 脚本、配置文件或参考文档

### 何时使用技能

- 当用户请求匹配某个技能的领域时（例如，"研究 X" → web-research 技能）
- 当你需要专业知识或结构化工作流程时
- 当技能提供了复杂任务的经过验证的模式时

### 技能执行

你可以使用以下工具与技能系统交互：
- `list_skills`: 列出所有可用技能
- `read_skill`: 读取技能的完整指令
- `match_skills`: 根据查询匹配合适的技能
- `execute_skill_chain`: 执行技能链

**示例工作流程：**

用户: "帮我研究量子计算的最新进展"

1. 检查上面的可用技能 → 看到 "web-research" 技能
2. 使用 `read_skill("web-research")` 读取完整指令
3. 遵循技能的研究工作流程（搜索 → 整理 → 综合）
4. 使用绝对路径运行辅助脚本

记住: 技能是让你更有能力和一致性的工具。有疑问时，检查是否存在适合任务的技能！
"""


def format_skill_item(skill: "Skill") -> str:
    """格式化单个技能项
    
    Args:
        skill: 技能实例
        
    Returns:
        格式化的技能描述字符串
    """
    source_label = "项目" if skill.source.value == "project" else "用户"
    triggers_str = ", ".join(skill.triggers[:3]) if skill.triggers else "无"
    
    return f"""- **{skill.name}** [{source_label}]
  描述: {skill.description}
  触发词: {triggers_str}
  路径: `{skill.path}`"""


def format_skills_list(skills: list["Skill"]) -> str:
    """格式化技能列表
    
    Args:
        skills: 技能列表
        
    Returns:
        格式化的技能列表字符串
    """
    if not skills:
        return "(暂无可用技能。你可以在技能目录中创建新技能。)"
    
    # 按来源分组
    user_skills = [s for s in skills if s.source.value == "user"]
    project_skills = [s for s in skills if s.source.value == "project"]
    
    lines = []
    
    if user_skills:
        lines.append("### 用户级技能\n")
        for skill in user_skills:
            lines.append(format_skill_item(skill))
        lines.append("")
    
    if project_skills:
        lines.append("### 项目级技能\n")
        for skill in project_skills:
            lines.append(format_skill_item(skill))
    
    return "\n".join(lines)


class SkillsPromptBuilder:
    """技能系统提示词构建器
    
    构建包含技能系统说明的系统提示词。
    
    Example:
        >>> builder = SkillsPromptBuilder(config, skills)
        >>> system_prompt = builder.build()
    """
    
    def __init__(
        self,
        user_skills_dir: str,
        project_skills_dir: str,
        skills: list["Skill"] | None = None,
    ):
        """初始化构建器
        
        Args:
            user_skills_dir: 用户级技能目录
            project_skills_dir: 项目级技能目录
            skills: 可用技能列表
        """
        self._user_skills_dir = user_skills_dir
        self._project_skills_dir = project_skills_dir
        self._skills = skills or []
    
    def set_skills(self, skills: list["Skill"]) -> None:
        """设置技能列表
        
        Args:
            skills: 技能列表
        """
        self._skills = skills
    
    def build_skills_prompt(self) -> str:
        """构建技能系统提示词
        
        Returns:
            格式化的技能系统提示词
        """
        skills_list = format_skills_list(self._skills)
        
        return SKILLS_SYSTEM_PROMPT.format(
            user_skills_dir=self._user_skills_dir,
            project_skills_dir=self._project_skills_dir,
            skills_list=skills_list,
        )
    
    def build(self, base_prompt: str | None = None) -> str:
        """构建完整的系统提示词
        
        Args:
            base_prompt: 基础提示词（可选）
            
        Returns:
            完整的系统提示词
        """
        parts = []
        
        # 添加基础提示词
        if base_prompt:
            parts.append(base_prompt)
        else:
            parts.append(BASE_SYSTEM_PROMPT)
        
        # 添加技能系统提示词
        parts.append(self.build_skills_prompt())
        
        return "\n\n".join(parts)

