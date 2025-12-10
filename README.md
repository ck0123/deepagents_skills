# Deep Agents 代码助手

基于 `deepagents` 库实现的智能代码助手，具备文件操作、代码生成和数据分析三种核心技能。

## 功能特性

- **文件操作 (file_ops)**: 读取、写入、搜索和管理文件
- **代码生成 (code_gen)**: 生成、解释、重构代码，提供错误修复建议
- **数据分析 (data_analysis)**: 数据加载、统计分析和可视化

## 快速开始


### 1. 激活虚拟环境

```bash
conda activate deepagents
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 LLM API

设置环境变量（二选一）：

```bash
# 使用 Anthropic Claude (推荐)
export ANTHROPIC_API_KEY="your-api-key"

# 或使用 OpenAI
export OPENAI_API_KEY="your-api-key"
```

### 4. 运行代码助手

```bash
python main.py
```

## 项目结构

```
deepagents_skills/
├── config.yaml           # Agent 配置文件
├── main.py               # 主程序入口
├── requirements.txt      # Python 依赖
├── README.md             # 项目说明
└── skills/               # 技能目录
    ├── file_ops/         # 文件操作技能
    │   └── SKILL.md
    ├── code_gen/         # 代码生成技能
    │   └── SKILL.md
    └── data_analysis/    # 数据分析技能
        └── SKILL.md
```

## 使用示例

启动后，可以使用自然语言与助手交互：

```
你: 帮我读取 config.yaml 文件
助手: [显示文件内容]

你: 写一个 Python 快速排序函数
助手: [生成代码并解释]

你: 分析 data.csv 文件的统计信息
助手: [显示数据统计]
```

## 自定义技能

在 `skills/` 目录下创建新的技能文件夹，添加 `SKILL.md` 定义技能元数据和工作流程。

## 许可证

MIT License

