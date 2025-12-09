"""记忆中间件

提供 LangChain Agent 的记忆中间件集成。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from deepagents_skills.config import Config
    from deepagents_skills.memory.store import MemoryStore


# 记忆系统提示词模板
MEMORY_SYSTEM_PROMPT = """
## 长期记忆系统

你有一个持久化的记忆系统，可以在会话之间保存和加载信息。

**用户级记忆目录**: `{user_memory_dir}`
**项目级记忆目录**: `{project_memory_dir}`

### 记忆内容

<user_memory>
{user_memory}
</user_memory>

<project_memory>
{project_memory}
</project_memory>

### 记忆使用指南

**何时检查记忆：**
- 在开始新会话时
- 当用户询问"你知道关于X什么?"或"如何做Y?"时
- 当用户引用过去的工作时

**何时更新记忆：**
- 当用户明确要求你记住某事时
- 当出现需要记住的模式或偏好时
- 在完成重要工作后，保存上下文以便未来会话使用

**记忆优先级：**
- 项目级记忆优先于用户级记忆
- 保存的知识优先于一般知识

### 记忆文件操作

**用户记忆：**
- 列出: `ls {user_memory_dir}`
- 读取: `read_file('{user_memory_dir}/[filename].md')`
- 保存: `write_file('{user_memory_dir}/[filename].md', content)`

**项目记忆：**
- 列出: `ls {project_memory_dir}`
- 读取: `read_file('{project_memory_dir}/[filename].md')`
- 保存: `write_file('{project_memory_dir}/[filename].md', content)`
"""


class MemoryMiddleware:
    """记忆中间件
    
    为 LangChain Agent 提供记忆功能。
    
    Example:
        >>> middleware = MemoryMiddleware(config, memory_store)
        >>> system_prompt = middleware.build_system_prompt()
        >>> # 或者注入到现有提示词
        >>> enhanced_prompt = middleware.inject_memory(base_prompt)
    """
    
    def __init__(
        self,
        config: "Config",
        memory_store: "MemoryStore",
        agent_name: str = "agent",
    ):
        """初始化中间件
        
        Args:
            config: 配置实例
            memory_store: 记忆存储实例
            agent_name: 智能体名称
        """
        self.config = config
        self.memory_store = memory_store
        self.agent_name = agent_name
        
        self._user_memory_dir = str(config.memory.user_dir)
        self._project_memory_dir = str(config.memory.project_dir)
    
    def load_user_memory(self) -> str:
        """加载用户级记忆
        
        Returns:
            用户记忆内容
        """
        content = self.memory_store.load_user(self.agent_name)
        return content or "(无用户记忆)"
    
    def load_project_memory(self) -> str:
        """加载项目级记忆
        
        Returns:
            项目记忆内容
        """
        content = self.memory_store.load_project(self.agent_name)
        return content or "(无项目记忆)"
    
    def build_memory_prompt(self) -> str:
        """构建记忆提示词
        
        Returns:
            格式化的记忆系统提示词
        """
        user_memory = self.load_user_memory()
        project_memory = self.load_project_memory()
        
        return MEMORY_SYSTEM_PROMPT.format(
            user_memory_dir=self._user_memory_dir,
            project_memory_dir=self._project_memory_dir,
            user_memory=user_memory,
            project_memory=project_memory,
        )
    
    def inject_memory(self, base_prompt: str) -> str:
        """将记忆注入到基础提示词
        
        Args:
            base_prompt: 基础系统提示词
            
        Returns:
            增强后的系统提示词
        """
        memory_prompt = self.build_memory_prompt()
        return f"{memory_prompt}\n\n{base_prompt}"
    
    def save_memory(self, content: str, project: bool = False) -> None:
        """保存记忆
        
        Args:
            content: 记忆内容
            project: 是否保存为项目级记忆
        """
        self.memory_store.save_agent_memory(content, self.agent_name, project)
    
    def append_memory(self, content: str, project: bool = False) -> None:
        """追加记忆
        
        Args:
            content: 要追加的内容
            project: 是否追加到项目级记忆
        """
        self.memory_store.append_to_memory(self.agent_name, content, project)
    
    def get_memory_context(self) -> dict[str, Any]:
        """获取记忆上下文
        
        Returns:
            包含记忆信息的上下文字典
        """
        return {
            "user_memory": self.load_user_memory(),
            "project_memory": self.load_project_memory(),
            "user_memory_dir": self._user_memory_dir,
            "project_memory_dir": self._project_memory_dir,
            "all_user_memories": self.memory_store.list_user(),
            "all_project_memories": self.memory_store.list_project(),
        }


def create_memory_middleware(config: "Config", agent_name: str = "agent") -> MemoryMiddleware:
    """创建记忆中间件的便捷函数
    
    Args:
        config: 配置实例
        agent_name: 智能体名称
        
    Returns:
        记忆中间件实例
    """
    from deepagents_skills.memory.store import MemoryStore
    
    memory_store = MemoryStore(config)
    return MemoryMiddleware(config, memory_store, agent_name)

