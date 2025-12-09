"""技能加载器

从 SKILL.md 文件解析技能，包括 YAML frontmatter 和 Markdown 内容。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from deepagents_skills.skills.model import Skill, SkillMetadata, SkillSource

if TYPE_CHECKING:
    pass

# SKILL.md 文件最大大小 (10MB)
MAX_SKILL_FILE_SIZE = 10 * 1024 * 1024


def _is_safe_path(path: Path, base_dir: Path) -> bool:
    """检查路径是否安全地包含在 base_dir 中
    
    防止通过符号链接或路径操作进行目录遍历攻击。
    
    Args:
        path: 要验证的路径
        base_dir: 应该包含路径的基目录
        
    Returns:
        如果路径安全地在 base_dir 中则返回 True
    """
    try:
        resolved_path = path.resolve()
        resolved_base = base_dir.resolve()
        resolved_path.relative_to(resolved_base)
        return True
    except ValueError:
        return False
    except (OSError, RuntimeError):
        return False


def _parse_yaml_frontmatter(content: str) -> tuple[dict[str, any], str] | None:
    """解析 YAML frontmatter
    
    Args:
        content: SKILL.md 文件内容
        
    Returns:
        (元数据字典, 剩余内容) 元组，解析失败返回 None
    """
    # 匹配 --- 分隔符之间的 YAML frontmatter
    frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n"
    match = re.match(frontmatter_pattern, content, re.DOTALL)
    
    if not match:
        return None
    
    frontmatter = match.group(1)
    rest_content = content[match.end():]
    
    # 简单的 YAML 解析（支持基本的键值对和列表）
    metadata: dict[str, any] = {}
    current_key = None
    current_list = None
    
    for line in frontmatter.split("\n"):
        # 跳过空行
        if not line.strip():
            continue
        
        # 检查是否是列表项
        list_match = re.match(r"^\s*-\s+(.+)$", line)
        if list_match and current_key:
            if current_list is None:
                current_list = []
                metadata[current_key] = current_list
            value = list_match.group(1).strip()
            # 移除引号
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            current_list.append(value)
            continue
        
        # 检查是否是键值对
        kv_match = re.match(r"^(\w+):\s*(.*)$", line.strip())
        if kv_match:
            key, value = kv_match.groups()
            value = value.strip()
            current_key = key
            current_list = None
            
            if value:
                # 移除引号
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                # 尝试转换为整数
                try:
                    value = int(value)
                except ValueError:
                    pass
                metadata[key] = value
            # 如果值为空，可能是列表的开始
    
    return metadata, rest_content


def load_skill(skill_md_path: Path, source: SkillSource) -> Skill | None:
    """从 SKILL.md 文件加载技能
    
    Args:
        skill_md_path: SKILL.md 文件路径
        source: 技能来源（用户级或项目级）
        
    Returns:
        Skill 实例，加载失败返回 None
    """
    try:
        # 安全检查：文件大小
        file_size = skill_md_path.stat().st_size
        if file_size > MAX_SKILL_FILE_SIZE:
            return None
        
        # 读取文件内容
        content = skill_md_path.read_text(encoding="utf-8")
        
        # 解析 frontmatter
        result = _parse_yaml_frontmatter(content)
        if result is None:
            return None
        
        metadata_dict, instructions = result
        
        # 验证必需字段
        if "name" not in metadata_dict or "description" not in metadata_dict:
            return None
        
        # 创建元数据
        metadata = SkillMetadata(
            name=metadata_dict["name"],
            description=metadata_dict["description"],
            triggers=metadata_dict.get("triggers", []),
            dependencies=metadata_dict.get("dependencies", []),
            priority=metadata_dict.get("priority", 0),
        )
        
        return Skill(
            metadata=metadata,
            content=content,
            instructions=instructions.strip(),
            path=skill_md_path,
            source=source,
        )
    
    except (OSError, UnicodeDecodeError):
        return None


def load_skill_from_directory(skill_dir: Path, source: SkillSource) -> Skill | None:
    """从技能目录加载技能
    
    技能目录应包含 SKILL.md 文件。
    
    Args:
        skill_dir: 技能目录路径
        source: 技能来源
        
    Returns:
        Skill 实例，加载失败返回 None
    """
    skill_md_path = skill_dir / "SKILL.md"
    if not skill_md_path.exists():
        return None
    return load_skill(skill_md_path, source)


def list_skills_in_directory(skills_dir: Path, source: SkillSource) -> list[Skill]:
    """列出目录中的所有技能
    
    扫描技能目录，查找包含 SKILL.md 的子目录。
    
    Args:
        skills_dir: 技能根目录
        source: 技能来源
        
    Returns:
        技能列表
    """
    skills_dir = skills_dir.expanduser()
    if not skills_dir.exists():
        return []
    
    try:
        resolved_base = skills_dir.resolve()
    except (OSError, RuntimeError):
        return []
    
    skills: list[Skill] = []
    
    for skill_dir in skills_dir.iterdir():
        # 安全检查
        if not _is_safe_path(skill_dir, resolved_base):
            continue
        
        if not skill_dir.is_dir():
            continue
        
        skill_md_path = skill_dir / "SKILL.md"
        if not skill_md_path.exists():
            continue
        
        # 安全检查 SKILL.md 路径
        if not _is_safe_path(skill_md_path, resolved_base):
            continue
        
        skill = load_skill(skill_md_path, source)
        if skill:
            skills.append(skill)
    
    return skills

