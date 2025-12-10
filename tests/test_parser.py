from pathlib import Path

import pytest

from deepagents_skills.parser import (
    MAX_SKILL_FILE_SIZE,
    SkillParseError,
    load_all_skill_metadata,
    parse_skill_metadata,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = PROJECT_ROOT / "skills"


def test_load_all_skill_metadata_success():
    metas = load_all_skill_metadata(SKILLS_ROOT)
    names = {meta["name"] for meta in metas}
    assert "web-research" in names
    assert "summarize" in names
    for meta in metas:
        assert meta["description"]
        assert meta["path"].endswith("SKILL.md")


def test_parse_skill_metadata_missing_required_fields(tmp_path: Path):
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("""---
name: only-name
---
body
""", encoding="utf-8")
    meta = parse_skill_metadata(skill_file)
    assert meta is None


def test_parse_skill_metadata_yaml_error(tmp_path: Path):
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("""---
name: [unterminated
---
body
""", encoding="utf-8")
    with pytest.raises(SkillParseError):
        parse_skill_metadata(skill_file)


def test_parse_skill_metadata_missing_frontmatter(tmp_path: Path):
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("# no frontmatter", encoding="utf-8")
    with pytest.raises(SkillParseError):
        parse_skill_metadata(skill_file)


def test_parse_skill_metadata_file_too_large(tmp_path: Path):
    skill_file = tmp_path / "SKILL.md"
    oversized = "a" * (MAX_SKILL_FILE_SIZE + 1)
    skill_file.write_text(f"---\nname: big\ndescription: big\n---\n{oversized}", encoding="utf-8")
    with pytest.raises(SkillParseError):
        parse_skill_metadata(skill_file)
