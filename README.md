# peas-agent-tools

PEAS Agent 內建 LangChain tools：檔案讀寫、shell `exec`、web 搜尋／抓取，以及路徑解析 helper。

## 安裝

```bash
uv add git+https://github.com/mz038197/peas-agent-tools.git --tag v0.1.1
uv add langchain-openai
```

## 用法

在專案目錄執行 agent 時，相對路徑會自動以 repo 根（`.git` / `pyproject.toml` / `uv.lock`）解析，**無需** `configure()`：

```python
from peas_agent_tools import get_builtin_tools

tools = get_builtin_tools()
llm_tools = llm.bind_tools(tools)
```

### 選擇要的工具（workshop 分階段）

```python
tools = get_builtin_tools(include=["read_file", "write_file", "list_dir"])
```

- 不傳 `include` → 全套內建 tool
- `include=[]` → 不要任何內建 tool
- 合法名稱：`add_numbers`, `read_file`, `read_image`, `write_file`, `edit_file`, `list_dir`, `exec`, `web_search`, `web_fetch`

若需 vision 的 `read_image`：

```python
tools = get_builtin_tools(include=["read_file", "read_image"], vision_analyzer=my_fn)
```

### Web 搜尋 provider（選修）

預設 DuckDuckGo（免 API key）。Tavily / Brave 請用 `configure_web()` 或 core 的 `config.json`（見 `tools.web.search`）。

## 進階

- `configure(ToolSettings(...))` — 明確指定 project root / workspace
- `PEAS_AGENT_PROJECT_ROOT` — 環境變數覆寫專案根
- `discover_project_root()` — 手動偵測 repo 根
