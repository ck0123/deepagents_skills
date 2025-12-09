import os
from pathlib import Path

import pytest
from deepagents_skills import SkillAgent, Config


def _write_skill(dir_path: Path, name: str, description: str, triggers: list[str], priority: int, instructions: str) -> None:
    skill_dir = dir_path / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    content = (
        "---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        "triggers:\n" + "".join([f'  - "{t}"\n' for t in triggers]) +
        "dependencies: []\n"
        f"priority: {priority}\n"
        "---\n\n" +
        instructions.strip() + "\n"
    )
    (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")


@pytest.fixture
def configured_agent(tmp_path: Path) -> SkillAgent:
    user_skills = tmp_path / "skills_user"
    project_skills = tmp_path / "skills_project"
    user_skills.mkdir()
    project_skills.mkdir()

    _write_skill(
        project_skills,
        name="web-research",
        description="结构化的网络研究方法",
        triggers=["研究", "调查", "搜索资料"],
        priority=10,
        instructions="# 网络研究技能\n请进行结构化的网络研究。"
    )
    _write_skill(
        project_skills,
        name="summarize",
        description="将长文本内容进行结构化总结",
        triggers=["总结", "摘要", "概括"],
        priority=5,
        instructions="# 文本总结技能\n请对内容进行结构化总结。"
    )

    config = Config.default()
    config.skills.user_dir = user_skills
    config.skills.project_dir = project_skills

    return SkillAgent(config)


def test_agent_end_to_end(configured_agent: SkillAgent):
    agent = configured_agent

    skills = agent.list_skills()
    names = {s["name"] for s in skills}
    assert {"web-research", "summarize"} <= names

    response = agent.process("帮我研究量子计算")
    matched_names = {s["name"] for s in response["matched_skills"]}
    assert "web-research" in matched_names
    assert response["executed"] is False
    assert response["execution_results"] == []

    chain_result = agent.execute_chain(["web-research", "summarize"])
    assert chain_result["success"] is True
    assert [step["skill"] for step in chain_result["steps"]] == ["web-research", "summarize"]
    assert chain_result["final_output"].startswith("# 文本总结技能")

    single_exec = agent.execute_skill("web-research")
    assert single_exec is not None
    assert single_exec.success is True
    assert str(single_exec.output).startswith("# 网络研究技能")


def test_usage_snippet_like(configured_agent: SkillAgent):
    agent = configured_agent

    skills = agent.list_skills()
    assert any(s["name"] == "web-research" for s in skills)

    response = agent.process("帮我研究量子计算")
    assert any(s["name"] == "web-research" for s in response["matched_skills"])

    results = agent.execute_chain(["web-research", "summarize"])
    assert results["success"] is True
    assert len(results["steps"]) == 2

if __name__ == "__main__":
    pytest.main()