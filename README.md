# AITestFlow

AITestFlow 是一个面向 OpenAPI 的黑盒测试生成仓库。  
它通过 LLM 生成测试条件、测试场景与 pytest 代码，并输出设计报告和覆盖率报告，支持在本地以脚本或 Web 页面运行。

## 仓库定位

- 输入：OpenAPI 3.x 规范（YAML/JSON）
- 处理：解析接口 -> 生成 EP/BVA 条件 -> 组合场景 -> 生成测试代码
- 输出：`output/test_api.py`、覆盖率报告、设计报告、流程日志
- 运行方式：`Streamlit` 页面 + Python 脚本

## 目录结构

```text
AITESTFLOW/
├── app.py                          # Streamlit 入口
├── requirements.txt                # 依赖列表
├── README.md
├── input/
│   └── sample_petstore.yaml        # 示例 OpenAPI
├── output/                         # 运行产物目录
│   ├── test_api.py                 # 生成的 pytest 脚本
│   ├── coverage_report.json        # mock 验证口径覆盖率
│   ├── design_report.md            # 设计报告（EP/BVA + 样例用例）
│   └── workflow_log.txt            # 工作流日志
├── docs/
│   ├── Example_Submission_AITestFlow.md
│   └── Mock_API_测试方法与等价类说明.md
├── scripts/
│   └── run_pipeline_once.py        # 单次流水线运行脚本
├── src/
│   ├── coordinator.py              # 流程编排与产物写入
│   ├── llm_client.py               # LLM 调用封装
│   ├── models.py                   # 数据模型
│   ├── validator.py                # pytest mock 校验
│   ├── design_report.py            # 设计报告渲染
│   ├── prompts/                    # 各阶段提示词
│   │   ├── parse_api.txt
│   │   ├── gen_conditions.txt
│   │   ├── gen_scenarios.txt
│   │   └── gen_code.txt
│   └── skills/                     # 分阶段实现
│       ├── api_parser.py
│       ├── condition_gen.py
│       ├── scenario_gen.py
│       ├── code_gen.py
│       └── evaluator.py
├── tools/
│   ├── mock_petstore_server.py     # 本地模拟 API（含内置覆盖追踪与 /__coverage）
│   └── petstore_分层覆盖对照表.md   # 人工对照覆盖统计表
└── tests/
    └── test_integration.py
```

## 工作流概览

1. 解析 OpenAPI，提取端点、参数、约束、响应。
2. 为每个端点生成 EP/BVA 条件（`conditions`）。
3. 将条件组合为可执行场景（`test_cases`）。
4. 生成 pytest 代码并合并为 `output/test_api.py`。
5. 进行 mock 校验并输出 `coverage_report.json`。
6. 可选：启动本地模拟 API 执行 `output/test_api.py`，通过 `GET /__coverage` 获取真实执行覆盖率，并用 `tools/petstore_分层覆盖对照表.md` 复核。

## 环境要求

- Python 3.10+
- 可用的 LLM API（OpenAI 兼容接口）

## 安装与配置

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

在项目根目录创建 `.env`：

```env
OPENAI_API_KEY=your-api-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4
```

## 运行方式

### 方式一：Web 界面

```bash
streamlit run app.py
```

默认访问：`http://localhost:8501`

### 方式二：脚本运行

```bash
python scripts/run_pipeline_once.py
```

或直接在 Python 中调用：

```python
import yaml
from src.coordinator import WorkflowCoordinator

with open("input/sample_petstore.yaml", "r", encoding="utf-8") as f:
    spec = yaml.safe_load(f)

coordinator = WorkflowCoordinator(
    coverage_threshold=0.85,
    max_iter=3,
    output_dir="output",
)

test_code, coverage = coordinator.run_full_pipeline(spec)
print(coverage.coverage_rate)
```

## 输出文件说明

- `output/test_api.py`  
  自动生成的 pytest 测试模块。

- `output/coverage_report.json`  
  基于 mock 校验的覆盖率报告，包含总条件数、覆盖条件数、端点级覆盖率等。

- `output/design_report.md`  
  EP/BVA 条件与示例测试用例表格，便于文档化提交。

- `output/workflow_log.txt`  
  流程执行日志，包含每个端点处理与迭代记录。

- `tools/petstore_分层覆盖对照表.md`（推荐）  
  输入/输出分层对照表，用于对 `mock_petstore_server.py` 的覆盖统计结果做人工复核与误差定位。

## 真实覆盖率评估（mock 内置统计 + 对照表复核）

若需要执行真实请求验证（使用仓库内 mock API）：

1. 启动本地模拟服务（`tools/mock_petstore_server.py`）。
2. （可选）重置覆盖计数：`POST http://127.0.0.1:8000/__coverage/reset`。
3. 执行 `python -m pytest output/test_api.py -v`。
4. 查看覆盖结果：`GET http://127.0.0.1:8000/__coverage`（返回总数、已覆盖、覆盖率、缺失 C-ID、忽略 500 条目）。
5. 将缺失 C-ID 回查到 `tools/petstore_分层覆盖对照表.md`，定位缺口来源并指导下一轮提示词迭代。

## 常用命令

```bash
# 运行集成测试
python -m pytest tests/test_integration.py -v

# 运行已生成测试（需要目标服务可访问）
python -m pytest output/test_api.py -v
```

## 文档索引

- `docs/Example_Submission_AITestFlow.md`：示例提交文档
- `docs/Mock_API_测试方法与等价类说明.md`：mock API 测试方法与等价类说明

## 许可证

本项目采用 MIT License（见 `LICENSE`）。
