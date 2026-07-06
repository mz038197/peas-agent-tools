# peas-agent-tools

PEAS Agent 內建 LangChain tools：檔案讀寫、shell `exec`、web 搜尋／抓取、VCR 生圖，以及路徑解析 helper。

## 安裝

```bash
uv add git+https://github.com/mz038197/peas-agent-tools.git --tag v0.1.2
uv add langchain-openai
```

## 學生專案快速開始

```bash
uv add peas-agent-tools
uv run peas-tools-init
# 編輯 peas-tools.json：tools.image.apiKey、（可選）tools.web.search.apiKey
```

```python
from peas_agent_tools import get_builtin_tools

tools = get_builtin_tools(vision_analyzer=my_vision_fn)  # 自動讀專案根 peas-tools.json
llm.bind_tools(tools)
```

`get_builtin_tools()` 首次呼叫時會自動載入 `{project_root}/peas-tools.json`。不必手動 `configure_tools()`。

進階：明確覆寫設定 → `configure_tools(cfg)`（須在首次 `get_builtin_tools()` 前，或之後再呼叫以更新）。測試可設 `PEAS_AGENT_NO_AUTO_CONFIG=1` 關閉自動載入。

## peas-tools.json 範本

`peas-tools-init` 產生的檔案含：

| 區塊 | 用途 |
|------|------|
| `tools.web` | `enable`；`search.provider`（duckduckgo / tavily / brave）、`apiKey`、`maxResults` |
| `tools.web.fetch` | `useJinaReader`、`maxChars` |
| `tools.image` | `enable`、`apiKey`（VCR `vcr_sk_...`）、`baseUrl`、`timeout` |
| `tools.exec` | `execDefaultTimeout` |

`tools.image.enable: false` 或 `apiKey` 為空 → 預設工具清單不含 `generate_image`。`tools.web.enable: false` → 不含 `web_search` / `web_fetch`。

含真實 key 的 `peas-tools.json` 勿 commit；可 `.gitignore` 並提供 `peas-tools.example.json`。

## 用法

```python
from peas_agent_tools import get_builtin_tools

tools = get_builtin_tools()
llm_tools = llm.bind_tools(tools)
```

### 選擇要的工具（workshop 分階段）

```python
tools = get_builtin_tools(include=["read_file", "write_file", "list_dir"])
```

合法名稱：`add_numbers`, `read_file`, `read_image`, `generate_image`, `write_file`, `edit_file`, `list_dir`, `exec`, `web_search`, `web_fetch`

### read_image（vision_analyzer）

`read_image` 需注入多模態 callback；`generate_image` 生圖後可用 `read_image` 自我驗證：

```python
from langchain_core.messages import HumanMessage
from peas_agent_tools import get_builtin_tools, image_bytes_to_data_url

def my_vision_analyzer(path: str, question: str, data: bytes, media_type: str) -> str:
    response = llm.invoke([
        HumanMessage(content=[
            {"type": "text", "text": question},
            {"type": "image_url", "image_url": {"url": image_bytes_to_data_url(data, media_type)}},
        ])
    ])
    return str(getattr(response, "content", response))

tools = get_builtin_tools(vision_analyzer=my_vision_analyzer)
```

### generate_image

Agent 呼叫範例（key 來自 `peas-tools.json` 的 `tools.image.apiKey` 或環境變數 `VSROUTER_API_KEY`）：

- `preset`: `icon` | `ui_mockup` | `photo`
- `reference_paths`: 本機參考圖路徑列表（改圖）

## 進階

- `configure(ToolSettings(...))` — 明確指定 project root / workspace
- `PEAS_AGENT_PROJECT_ROOT` — 環境變數覆寫專案根
- `discover_project_root()` — 手動偵測 repo 根
