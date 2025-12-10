# deepagents-skills

一个用于“技能”渐进式加载的 Python 库，帮助代理在知道技能存在的前提下，按需读取对应的 SKILL.md 并注入上下文。内置工具可解析技能元数据、生成提示词片段，并加载技能文档为 LangChain `Document`，便于在大模型链路中复用。

## 特性
- 支持从 `skills/*/SKILL.md` 读取 YAML Frontmatter 元数据（名称、描述、路径）。
- 生成“技能列表 + 渐进式披露”系统提示词，指引模型在需要时再深入阅读技能说明。
- 提供 `SkillContextLoader` 将技能文件加载为 `Document`，便于拼接上下文。
- 简单的辅助函数 `inject_context` 将多个技能文档内容注入到链式调用。

## 安装
- 已发布版本：`pip install deepagents-skills`
- 本地开发：在仓库根目录执行 `pip install -e .`（可选安装开发依赖：`pip install -e .[dev]`）

## 目录结构（默认）
```
skills/
  web-research/
    SKILL.md
  summarize/
    SKILL.md
src/deepagents_skills/
  parser.py          # 解析技能元数据
  ai_integration.py  # 提示词构建与上下文加载
```

## SKILL.md 约定
- 顶部必须有 YAML Frontmatter，至少包含：
  - `name`: 技能名
  - `description`: 简要描述
- 建议还可以包含 `version`、`tags`、`author` 等信息。
- Frontmatter 之后是技能说明正文，可包含工作流、示例、脚本指引等。

示例（摘自仓库自带技能）：
```
---
name: summarize
description: "Summarize content into concise takeaways with traceable notes."
version: "1.0.0"
tags: [summarization, synthesis]
author: "DeepAgents"
---

# Summarize Skill
...
```

## 快速开始
```python
from pathlib import Path
from deepagents_skills import (
    load_all_skill_metadata,
    build_metadata_prompt,
    SkillContextLoader,
    inject_context,
)

skills_root = Path("skills")

# 1) 扫描技能元数据（只要 name/description 存在就会返回）
metas = load_all_skill_metadata(skills_root)

# 2) 构建“渐进式披露”提示词片段，拼进你的系统 prompt
metadata_prompt = build_metadata_prompt(metas, skills_root)

# 3) 在需要时按路径读取技能正文
loader = SkillContextLoader(skills_root)
docs = loader.load_many([
    "web-research/SKILL.md",
    "summarize/SKILL.md",
])

# 4) 将技能内容注入到链路
class DummyChain:
    def invoke(self, payload):
        return payload

chain = DummyChain()
result = inject_context(chain, docs)
print(result["context"][:200])  # 已拼接的技能说明片段
```

## 开发与测试
- 依赖：`python>=3.9`，核心依赖 `pyyaml`、`langchain`。
- 运行测试（如需）：`pytest`（需要先安装 `.[dev]` 依赖）。

