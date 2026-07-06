# peas-agent-tools

PEAS Agent 內建 LangChain tools：檔案讀寫、shell `exec`、web 搜尋／抓取，以及路徑解析 helper。

## 安裝

```bash
uv add peas-agent-tools
```

## 用法

```python
from pathlib import Path

from peas_agent_tools import ToolSettings, configure, get_builtin_tools

configure(ToolSettings(project_root=Path.cwd()))
tools = get_builtin_tools()
llm_tools = llm.bind_tools(tools)
```

若需 vision 的 `read_image`，傳入 `vision_analyzer` callback：

```python
tools = get_builtin_tools(vision_analyzer=my_analyze_fn)
```
