from pathlib import Path

from deepagents_skills.ai_integration import (
    SkillContextLoader,
    build_metadata_prompt,
    inject_context,
)
from deepagents_skills.parser import load_all_skill_metadata


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = PROJECT_ROOT / "skills"


def test_build_metadata_prompt_includes_skill_paths():
    metas = load_all_skill_metadata(SKILLS_ROOT)
    prompt = build_metadata_prompt(metas, SKILLS_ROOT)
    assert str(SKILLS_ROOT.resolve()) in prompt
    for meta in metas:
        assert meta["name"] in prompt
        assert meta["description"] in prompt
        assert meta["path"] in prompt


def test_skill_context_loader_reads_skill_file():
    loader = SkillContextLoader(SKILLS_ROOT)
    doc = loader.load("web-research/SKILL.md")
    assert "Web Research Skill" in doc.page_content
    assert str((SKILLS_ROOT / "web-research" / "SKILL.md").resolve()) in doc.metadata["path"]


def test_inject_context_invokes_chain_with_context():
    class _FakeChain:
        def __init__(self):
            self.last_payload = None

        def invoke(self, payload):
            self.last_payload = payload
            return payload

    loader = SkillContextLoader(SKILLS_ROOT)
    docs = loader.load_many(["web-research/SKILL.md", "summarize/SKILL.md"])
    chain = _FakeChain()

    result = inject_context(chain, docs)

    assert "Web Research Skill" in result["context"]
    assert "Summarize Skill" in result["context"]
    assert chain.last_payload is result
