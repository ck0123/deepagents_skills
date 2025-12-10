from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Sequence

from langchain_core.documents import Document

SKILLS_SYSTEM_PROMPT = """
## Skills System
You have access to a skills library that provides specialized capabilities and domain knowledge.



{skills_locations}



**Available Skills:**



{skills_list}



**How to Use Skills (Progressive Disclosure):**



Skills follow a **progressive disclosure** pattern - you know they exist (name + description above), but you only read the full instructions when needed:



1. **Recognize when a skill applies**: Check if the user's task matches any skill's description

2. **Read the skill's full instructions**: The skill list above shows the exact path to use with read_file

3. **Follow the skill's instructions**: SKILL.md contains step-by-step workflows, best practices, and examples

4. **Access supporting files**: Skills may include Python scripts, configs, or reference docs - use absolute paths



**When to Use Skills:**

- When the user's request matches a skill's domain (e.g., "research X" → web-research skill)

- When you need specialized knowledge or structured workflows

- When a skill provides proven patterns for complex tasks



**Skills are Self-Documenting:**

- Each SKILL.md tells you exactly what the skill does and how to use it

- The skill list above shows the full path for each skill's SKILL.md file



**Executing Skill Scripts:**

Skills may contain Python scripts or other executable files. Always use absolute paths from the skill list.



**Example Workflow:**



User: "Can you research the latest developments in quantum computing?"



1. Check available skills above → See "web-research" skill with its full path

2. Read the skill using the path shown in the list

3. Follow the skill's research workflow (search → organize → synthesize)

4. Use any helper scripts with absolute paths



Remember: Skills are tools to make you more capable and consistent. When in doubt, check if a skill exists for the task!
"""


def build_metadata_prompt(metadata_list: Sequence[dict], skills_root: Path | str = "skills") -> str:
    skills_root_path = Path(skills_root)
    skills_locations = f"Skills root: {skills_root_path.resolve()}"
    lines: List[str] = []
    for skill in metadata_list:
        name = skill.get("name", "(unknown)")
        description = skill.get("description", "")
        path = skill.get("path", "")
        lines.append(f"- **{name}**: {description}")
        lines.append(f"  → Read {path} for full instructions")
    skills_list = "\n".join(lines)
    return SKILLS_SYSTEM_PROMPT.format(skills_locations=skills_locations, skills_list=skills_list)


class SkillContextLoader:
    def __init__(self, skills_root: Path | str = "skills") -> None:
        self.skills_root = Path(skills_root)

    def _resolve_path(self, path: str | Path) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.skills_root / candidate
        return candidate

    def load(self, path: str | Path) -> Document:
        resolved = self._resolve_path(path)
        content = resolved.read_text(encoding="utf-8")
        return Document(page_content=content, metadata={"path": str(resolved)})

    def load_many(self, paths: Iterable[str | Path]) -> List[Document]:
        return [self.load(path) for path in paths]


def inject_context(chain, documents: Sequence[Document]):
    """Helper to invoke a chain with concatenated skill documents as context."""

    context = "\n\n".join(doc.page_content for doc in documents)
    return chain.invoke({"context": context})


__all__ = [
    "SKILLS_SYSTEM_PROMPT",
    "build_metadata_prompt",
    "SkillContextLoader",
    "inject_context",
]
