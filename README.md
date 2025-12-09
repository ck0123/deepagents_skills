# DeepAgents Skills

智能体技能和记忆系统 - 让智能体能够动态发现、加载和执行特定任务的专业指令集。

## 特性

- **技能系统**: 动态发现、加载和执行专业指令集
- **记忆系统**: 持久化用户级和项目级记忆
- **技能链**: 支持技能的链式调用和流水线
- **智能匹配**: 根据用户请求自动匹配合适的技能

## 安装

```bash
pip install deepagents-skills
```

## 快速开始

### 基本使用

```python
from deepagents_skills import SkillAgent, Config

# 加载配置
config = Config.load("config.json")

# 创建智能体（自动发现技能和加载记忆）
agent = SkillAgent(config)

# 列出可用技能
skills = agent.list_skills()
for skill in skills:
    print(f"{skill['name']}: {skill['description']}")

# 处理用户请求（自动匹配技能）
response = agent.process("帮我研究量子计算的最新进展")
print(f"匹配到的技能: {response['matched_skills']}")

# 手动执行技能
result = agent.execute_skill("web-research")

# 执行技能链
results = agent.execute_chain(["web-research", "summarize", "save-report"])
```

### 配置文件

创建 `config.json`:

```json
{
  "skills": {
    "user_dir": "~/.deepagents/skills",
    "project_dir": ".deepagents/skills"
  },
  "memory": {
    "user_dir": "~/.deepagents/memory",
    "project_dir": ".deepagents/memory"
  },
  "api": {
    "openai_api_key": "",
    "anthropic_api_key": ""
  },
  "agent": {
    "default_model": "gpt-4o-mini",
    "max_iterations": 10
  }
}
```

### 创建技能

在技能目录中创建子目录，包含 `SKILL.md` 文件：

```
~/.deepagents/skills/
└── my-skill/
    └── SKILL.md
```

`SKILL.md` 格式：

```markdown
---
name: my-skill
description: 我的自定义技能描述
triggers:
  - "关键词1"
  - "关键词2"
dependencies: []
priority: 10
---

# 我的技能

## 何时使用
- 场景描述

## 如何使用
1. 步骤一
2. 步骤二

## 最佳实践
- 建议一
- 建议二
```

## 核心概念

### 技能 (Skill)

技能是一组专业指令，定义了如何完成特定类型的任务。每个技能包含：

- **元数据**: 名称、描述、触发词、依赖、优先级
- **指令**: 详细的步骤和最佳实践
- **支持文件**: 可选的脚本、配置等

### 技能来源

- **用户级技能**: 存储在 `~/.deepagents/skills/`，适用于所有项目
- **项目级技能**: 存储在 `.deepagents/skills/`，仅适用于当前项目
- 项目级技能会覆盖同名的用户级技能

### 记忆 (Memory)

记忆系统提供持久化存储，支持：

- **用户级记忆**: 跨项目的个人偏好和知识
- **项目级记忆**: 项目特定的上下文和配置

## API 参考

### SkillAgent

```python
class SkillAgent:
    def __init__(self, config: Config, agent_name: str = "agent")
    def discover_skills(self) -> int
    def list_skills(self) -> list[dict]
    def match_skills(self, query: str) -> list[Skill]
    def execute_skill(self, skill_name: str) -> ExecutionResult
    def execute_chain(self, skill_names: list[str]) -> dict
    def process(self, query: str, auto_execute: bool = False) -> dict
```

### Config

```python
class Config:
    @classmethod
    def load(cls, config_path: str) -> Config
    @classmethod
    def default(cls) -> Config
```

### SkillRegistry

```python
class SkillRegistry:
    def register(self, skill: Skill) -> None
    def get(self, name: str) -> Skill | None
    def match(self, query: str) -> list[Skill]
```

## 示例技能

项目包含以下示例技能：

- **web-research**: 结构化的网络研究方法
- **code-review**: 系统化的代码审查方法
- **summarize**: 文本内容结构化总结

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码检查
ruff check .
```

## 许可证

MIT License
