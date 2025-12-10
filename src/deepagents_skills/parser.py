from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, TypedDict

import yaml

MAX_SKILL_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class SkillParseError(Exception):
    """Raised when a skill file cannot be parsed."""


class SkillMetadata(TypedDict):
    name: str
    description: str
    path: str


@dataclass
class _FrontmatterSplit:
    yaml_text: str
    markdown_text: str


def _scan_skill_files(skills_root: Path) -> List[Path]:
    if not skills_root.exists():
        raise SkillParseError(f"skills root not found: {skills_root}")
    if not skills_root.is_dir():
        raise SkillParseError(f"skills root is not a directory: {skills_root}")
    return list(skills_root.glob("*/SKILL.md"))


def _check_size(path: Path, limit: int = MAX_SKILL_FILE_SIZE) -> None:
    size = path.stat().st_size
    if size > limit:
        raise SkillParseError(f"skill file too large (> {limit} bytes): {path}")


def _split_frontmatter(raw_text: str) -> _FrontmatterSplit:
    if not raw_text.startswith("---"):
        raise SkillParseError("missing YAML frontmatter start delimiter '---'")

    lines = raw_text.splitlines()
    try:
        end_idx = lines[1:].index("---") + 1
    except ValueError as exc:
        raise SkillParseError("missing YAML frontmatter end delimiter '---'") from exc

    yaml_text = "\n".join(lines[1:end_idx]).strip()
    markdown_text = "\n".join(lines[end_idx + 1 :]).lstrip()
    return _FrontmatterSplit(yaml_text=yaml_text, markdown_text=markdown_text)


def _parse_yaml(yaml_text: str) -> dict:
    try:
        data = yaml.safe_load(yaml_text) or {}
    except yaml.YAMLError as exc:
        raise SkillParseError(f"failed to parse YAML frontmatter: {exc}") from exc
    if not isinstance(data, dict):
        raise SkillParseError("YAML frontmatter must be a mapping")
    return data


def _normalize_metadata(meta: dict, path: Path) -> Optional[SkillMetadata]:
    name = meta.get("name")
    description = meta.get("description")
    if not name or not description:
        return None
    return SkillMetadata(name=str(name), description=str(description), path=str(path))


def parse_skill_metadata(path: Path) -> Optional[SkillMetadata]:
    if not path.exists():
        raise SkillParseError(f"skill file not found: {path}")
    _check_size(path)
    raw_text = path.read_text(encoding="utf-8")
    split = _split_frontmatter(raw_text)
    meta = _parse_yaml(split.yaml_text)
    return _normalize_metadata(meta, path)


def load_all_skill_metadata(skills_root: Path | str = "skills") -> List[SkillMetadata]:
    root_path = Path(skills_root)
    skill_paths = _scan_skill_files(root_path)
    metadatas: List[SkillMetadata] = []
    for skill_file in skill_paths:
        try:
            meta = parse_skill_metadata(skill_file)
        except SkillParseError as exc:
            raise SkillParseError(f"{skill_file}: {exc}") from exc
        if meta is not None:
            metadatas.append(meta)
    return metadatas


__all__ = [
    "SkillParseError",
    "SkillMetadata",
    "MAX_SKILL_FILE_SIZE",
    "parse_skill_metadata",
    "load_all_skill_metadata",
]
