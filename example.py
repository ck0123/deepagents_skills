"""深度代理技能库的快速使用示例。

运行前请确保已安装本地包：
  pip install -e .[dev]   # 或 pip install -e .

如需真实端到端测试，请先配置环境变量：
  export BASE_URL="https://api.deepseek.com/beta/"
  export MODEL_NAME="deepseek-chat"
  export API_KEY="sk-xxxx"
  export MODEL_ENABLE_THINK="disabled"
  export RUN_LLM_DEMO=1   # 可选，置为 1 时触发真实调用
"""

from pathlib import Path
import json
import os
import socket
import urllib.error
import urllib.request

from deepagents_skills import (
    SkillContextLoader,
    build_metadata_prompt,
    inject_context,
    load_all_skill_metadata,
)


class DemoChain:
    """示例链：将系统提示+用户请求+技能上下文拼成一段文本，模拟交给大模型。"""

    def __init__(self, system_prompt: str, user_query: str):
        self.system_prompt = system_prompt
        self.user_query = user_query
        self.last_payload = None

    def invoke(self, payload):
        self.last_payload = payload
        # payload 形如 {"context": "..."}，这里拼出最终要喂给模型的文本
        composed = (
            f"{self.system_prompt}\n\n"
            f"用户请求：{self.user_query}\n\n"
            f"技能上下文：\n{payload['context']}"
        )
        return {"composed_prompt": composed}


def call_llm(metadata_prompt: str, user_query: str, api_base: str):
    """使用 deepseek 接口做一次真实补全，便于端到端验证。"""

    api_key = os.environ.get("API_KEY")
    if not api_key:
        print("跳过真实调用：未设置 API_KEY。")
        return

    url = api_base.rstrip("/") + "/chat/completions"
    model = os.environ.get("MODEL_NAME", "deepseek-chat")
    enable_think = os.environ.get("MODEL_ENABLE_THINK", "disabled")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": metadata_prompt},
            {"role": "user", "content": user_query},
        ],
        "stream": False,
        "temperature": 0.7,
        # 部分模型需要通过 metadata/参数控制思考模式
        "metadata": {"enable_think": enable_think},
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read()
            data = json.loads(body)
    except urllib.error.HTTPError as exc:
        print(f"真实调用失败 (HTTP {exc.code}): {exc.read().decode('utf-8', 'ignore')}")
        return
    except urllib.error.URLError as exc:
        print(f"真实调用失败：{exc.reason}")
        return
    except (TimeoutError, socket.timeout):
        print("真实调用失败：读取响应超时，请稍后重试或检查网络。")
        return

    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )
    print("\n真实大模型返回（截断预览）：\n")
    print(content[:1000])


def main():
    # 自动定位 skills 目录：默认取本文件同级的 skills/
    skills_root = Path(__file__).resolve().parent / "skills"

    # 1) 扫描技能元数据
    metas = load_all_skill_metadata(skills_root)
    if not metas:
        raise SystemExit("未找到任何技能文件，请检查 skills 目录。")

    # 2) 构建“渐进式披露”系统提示片段
    metadata_prompt = build_metadata_prompt(metas, skills_root)
    print("生成的系统提示片段：\n")
    print(metadata_prompt)
    print("\n" + "-" * 80 + "\n")

    # 3) 设置用户请求
    user_query = "帮我研究并总结量子力学相关概念"

    # 4) 读取技能正文（示例：取前两个技能，足以覆盖研究+总结场景）
    skill_paths = [meta["path"] for meta in metas[:2]]
    loader = SkillContextLoader(skills_root)
    docs = loader.load_many(skill_paths)

    # 5) 将技能内容注入到链路，并拼出最终要给模型的文本
    chain = DemoChain(metadata_prompt, user_query)
    result = inject_context(chain, docs)

    composed = result["composed_prompt"]
    print("拼好的模型输入（截断预览）：\n")
    print(composed[:1000])

    # 可选：在设置了 RUN_LLM_DEMO=1 且有 API_KEY 时，触发真实大模型调用
    if os.environ.get("RUN_LLM_DEMO") == "1":
        api_base = os.environ.get("BASE_URL", "https://api.deepseek.com/beta/")
        call_llm(metadata_prompt, user_query, api_base)


if __name__ == "__main__":
    main()
