---
name: 实现 SKILLS 渐进式加载功能
overview: 实现一个 Python 库，支持从 skills/ 目录按技能子目录加载 SKILL.md 文件（YAML frontmatter + Markdown），实现渐进式加载（元数据优先、按需加载内容）、搜索匹配、LangChain 集成以及缓存。
todos:
  - id: setup_project
    content: 创建项目结构与 pyproject.toml
    status: pending
  - id: implement_parser
    content: 实现 parser.py：扫描、大小限制、frontmatter 解析，返回 SkillMetadata 列表
    status: pending
  - id: implement_ai
    content: 实现 ai_integration.py：元数据 prompt 注入与按需正文上下文加载
    status: pending
  - id: implement_api
    content: 实现 __init__.py：导出解析与集成功能
    status: pending
  - id: create_examples
    content: 在 skills/ 下添加示例技能子目录及 SKILL.md
    status: pending
  - id: write_tests
    content: 编写单元测试覆盖解析与 LangChain 集成
    status: pending
---

# SKILLS 渐进式加载功能实现计划（精简：仅解析器 + LangChain 集成）

## 项目结构

```
deepagents_skills/
├── skills/                # 技能根目录（每个技能一子目录，含 SKILL.md）
│   ├── skill_a/
│   │   └── SKILL.md
│   └── ...
├── src/
│   └── deepagents_skills/
│       ├── __init__.py
│       ├── parser.py      # frontmatter + Markdown 解析
│       └── ai_integration.py # LangChain 集成
├── docs/
├── tests/
├── README.md
└── pyproject.toml
```

## 技能文件格式定义

- **位置**: `skills/<skill_id>/SKILL.md`
- **结构**: YAML frontmatter（`---` 分隔） + Markdown 正文
- **frontmatter 必需字段**: `name`, `description`（均不可省略）
- **frontmatter 可选字段**: `version`, `tags`, `author`, `created_at`, `updated_at`
- **Markdown 正文**: 技能说明、步骤、示例

## 解析器模块 (`src/deepagents_skills/parser.py`)

- **核心类型**: `class SkillMetadata(TypedDict)`：`name: str`, `description: str`, `path: str`
- **输入/输出**:
  - 根路径 `skills_root`（默认 `skills/`）。
  - 扫描子目录，收集存在 `SKILL.md` 的路径。
  - 输出 `List[SkillMetadata]`。
- **frontmatter 约束**: 必须包含 `name` 和 `description`，缺任意一个跳过。
- **内部拆分**:
  - `_scan_skill_files(skills_root) -> List[Path]`: 找到 `*/SKILL.md`。
  - `_check_size(path, limit=MAX_SKILL_FILE_SIZE=10*1024*1024)`: 超过阈值不读。
  - `_split_frontmatter(raw_text) -> (yaml_str, markdown_str)`: 提取 frontmatter 与正文。
  - `_parse_yaml(yaml_str) -> dict`: `yaml.safe_load`。
  - `_normalize_metadata(meta, path) -> SkillMetadata | None`: 仅返回 `{name, description, path}`，必填缺失则返回 None。
- **公开函数**:
  - `parse_skill_metadata(path: Path) -> SkillMetadata | None`: 解析单个 frontmatter 的 `name` 和 `description`，缺失任一返回 None。
  - `load_all_skill_metadata(skills_root: Path) -> List[SkillMetadata]`: 扫描根路径并汇总有效元数据。
- **错误处理**: `SkillParseError`；文件过大/无 frontmatter/YAML 错误均给出明确消息。

## LangChain 集成与系统 Prompt 构建 (`src/deepagents_skills/ai_integration.py`)

- `build_metadata_prompt(metadata_list, skills_root: Path) -> str`: 使用给定技能根路径与元数据列表构建系统 prompt。
  - 模版 `SKILLS_SYSTEM_PROMPT`（固定多行字符串，包含占位符 `{skills_locations}` 与 `{skills_list}`）。
  - `skills_locations` 由输入的 `skills_root` 填充。
  - `skills_list` 通过遍历 `metadata_list` 构建：
    - 对每个 `skill` 追加两行：`- **{skill['name']}**: {skill['description']}`，`  → Read `{skill['path']} `for full instructions`，行与行之间用 `"\n"` 连接。
- 实际匹配流程为“模型驱动”：
  - 会话开始即将“可用技能清单”和“使用方法”附加到系统提示。
  - 模型阅读系统提示，遇到用户 query 时依据“名称+描述”做语义判断；仅当任务相关时才调用文件工具读取清单中给出的 SKILL.md 路径。
  - 整个“query→技能选择”无硬编码匹配函数，依赖模型理解与系统提示引导。
- `SkillContextLoader` 仅提供按需读取指定路径（供模型指令触发）和将 Markdown 转为 LangChain `Document` 的封装；不负责决策逻辑。
- `inject_context(chain, documents)`: 将技能正文注入 LangChain chain。
- 工作流：启动时用 `load_all_skill_metadata` 结果生成系统 prompt；模型在对话中自行选择是否读取对应 SKILL.md，再由 `SkillContextLoader` 提供读取与封装。

## 主 API (`src/deepagents_skills/__init__.py`)

- 导出解析器与 LangChain 集成的对外接口。

## 实现步骤

1) 项目结构与 `pyproject.toml`

2) 解析器：扫描、大小限制、frontmatter 解析、元数据归一化

3) LangChain 集成：元数据注入 + 按需正文上下文

4) API 封装

5) 测试与示例技能

## 技术选型

- `pyyaml` 或 `python-frontmatter`
- LangChain：`langchain-core` `Document`

## 使用示例

```python
from deepagents_skills import parser
from deepagents_skills.ai_integration import build_metadata_prompt, SkillContextLoader

metas = parser.load_all_skill_metadata("./skills")
meta_prompt = build_metadata_prompt(metas)

system_prompt = f"你可以使用以下技能：\n{meta_prompt}"
context_loader = SkillContextLoader(skills_root="./skills")
user_query = "我需要数据清洗"
ctx_docs = context_loader.maybe_load_context(user_query)
# 将 ctx_docs 注入 LangChain chain
```