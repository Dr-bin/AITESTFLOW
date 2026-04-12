# 🧪 AITestFlow - AI驱动的黑盒测试平台

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**基于大语言模型的智能API测试用例自动生成平台**

[English](#english) | [中文文档](#中文文档)

</div>

---

## 中文文档

### 📖 项目简介

AITestFlow 是一个创新的AI驱动测试平台，利用大语言模型（LLM）自动从OpenAPI规范生成高质量的测试用例。通过等价类划分（EP）和边界值分析（BVA）等测试技术，实现智能化的测试生成和覆盖率优化。

### ✨ 核心特性

- 🤖 **AI驱动的测试生成**：利用LLM理解API语义，自动生成测试条件
- 📊 **智能覆盖率优化**：多轮反馈循环，自动提升测试覆盖率
- 🎯 **EP/BVA测试技术**：自动应用等价类划分和边界值分析
- 🔄 **端到端自动化**：从OpenAPI规范到可执行测试代码的完整流程
- 📝 **多种输出格式**：生成pytest测试代码、覆盖率报告、工作流日志
- 🎨 **友好的Web界面**：基于Streamlit的可视化操作界面
- 🛡️ **完善的错误处理**：智能重试、降级策略、详细日志

### 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      AITestFlow 架构                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ OpenAPI Spec │───▶│ API Parser   │───▶│ Condition    │  │
│  │  (YAML/JSON) │    │              │    │ Generator    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                   │           │
│                                                   ▼           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ Test Code    │◀───│ Code         │◀───│ Scenario     │  │
│  │ (pytest)     │    │ Generator    │    │ Generator    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────┐    ┌──────────────┐                       │
│  │ Validator    │◀───│ Coverage     │                       │
│  │ (Mock Test)  │    │ Evaluator    │                       │
│  └──────────────┘    └──────────────┘                       │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Feedback Loop (迭代优化)                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 🚀 快速开始

#### 1. 环境要求

- Python 3.10 或更高版本
- OpenAI API密钥或兼容的LLM端点

#### 2. 安装依赖

```bash
# 克隆项目
git clone https://github.com/yourusername/AITestFlow.git
cd AITestFlow

# 创建虚拟环境（推荐）
python -m venv .venv
.\.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

#### 3. 配置环境变量

创建 `.env` 文件：

```env
# OpenAI API配置
OPENAI_API_KEY=your-api-key-here

# 可选：自定义LLM端点
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4
```

#### 4. 运行应用

**方式一：Web界面（推荐）**

```bash
streamlit run app.py
```

访问 http://localhost:8501 使用可视化界面。

**方式二：命令行**

```python
import yaml
from src.coordinator import WorkflowCoordinator

# 加载OpenAPI规范
with open("input/sample_petstore.yaml", "r", encoding="utf-8") as f:
    spec = yaml.safe_load(f)

# 初始化协调器
coordinator = WorkflowCoordinator(
    coverage_threshold=0.85,
    max_iter=3,
    output_dir="output"
)

# 运行完整流程
test_code, coverage = coordinator.run_full_pipeline(spec)

print(f"覆盖率: {coverage.coverage_rate:.2%}")
```

### 📁 项目结构

```
AITestFlow/
├── app.py                        # Streamlit Web 入口
├── requirements.txt              # Python依赖
├── README.md                     # 项目说明
├── .gitignore                    # Git忽略规则
├── input/                        # 输入OpenAPI规范
│   └── sample_petstore.yaml      # 示例API规范
├── output/                       # 运行生成产物
│   ├── test_api.py               # 生成的pytest测试代码
│   ├── coverage_report.json      # 覆盖率报告（mock验证口径）
│   ├── design_report.md          # EP/BVA与样例测试设计报告
│   └── workflow_log.txt          # 流水线执行日志
├── docs/                         # 文档与提交示例
│   └── Example_Submission_AITestFlow.md
├── scripts/                      # 脚本工具
│   └── run_pipeline_once.py      # 单次运行流水线脚本
├── src/                          # 核心源码
│   ├── __init__.py
│   ├── coordinator.py            # 工作流协调器
│   ├── design_report.py          # 设计报告渲染器（生成design_report.md）
│   ├── llm_client.py             # LLM调用封装
│   ├── models.py                 # Pydantic数据模型
│   ├── validator.py              # pytest mock验证与失败映射
│   ├── prompts/                  # 提示词模板
│   │   ├── parse_api.txt
│   │   ├── gen_conditions.txt
│   │   ├── gen_scenarios.txt
│   │   └── gen_code.txt
│   └── skills/                   # 流程分阶段能力模块
│       ├── __init__.py
│       ├── api_parser.py
│       ├── condition_gen.py
│       ├── scenario_gen.py
│       ├── code_gen.py
│       └── evaluator.py
└── tests/
    ├── __init__.py
    └── test_integration.py
```

### 💡 使用示例

#### 示例1：生成Petstore API测试

```python
from src.coordinator import WorkflowCoordinator
import yaml

# 加载OpenAPI规范
spec = yaml.safe_load(open("input/sample_petstore.yaml"))

# 创建协调器
coordinator = WorkflowCoordinator(
    coverage_threshold=0.85,  # 目标覆盖率85%
    max_iter=3,               # 最大迭代3次
    output_dir="output"
)

# 生成测试
test_code, coverage = coordinator.run_full_pipeline(spec)

# 查看结果
print(f"生成的测试代码行数: {len(test_code.split(chr(10)))}")
print(f"最终覆盖率: {coverage.coverage_rate:.2%}")
print(f"覆盖条件数: {len(coverage.covered_condition_ids)}")
```

#### 示例2：使用Web界面

1. 启动应用：`streamlit run app.py`
2. 上传OpenAPI规范文件（YAML或JSON格式）
3. 配置参数：
   - 覆盖率阈值：0.5 - 0.95
   - 最大迭代次数：1 - 5
4. 点击"生成测试套件"按钮
5. 查看生成的测试代码和覆盖率报告

### 📊 输出说明

#### 1. 测试代码 (test_api.py)

生成的pytest测试代码包含：
- 完整的测试场景定义
- 参数化测试函数
- HTTP请求辅助函数
- 错误处理和断言

#### 2. 覆盖率报告 (coverage_report.json)

```json
{
  "timestamp": "2026-04-07T12:30:19.758613",
  "total_conditions": 51,
  "covered_condition_ids": ["limit_valid_1", "status_valid_1", ...],
  "coverage_rate": 0.85,
  "failed_test_cases": [],
  "iteration": 3,
  "endpoints_processed": 5
}
```

#### 3. 工作流日志 (workflow_log.txt)

详细记录：
- 每个端点的处理过程
- 条件生成和场景组合
- 迭代优化过程
- 错误和警告信息

### 🔧 配置选项

#### WorkflowCoordinator 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `coverage_threshold` | float | 0.85 | 目标覆盖率阈值 (0.0-1.0) |
| `max_iter` | int | 3 | 每个端点的最大迭代次数 |
| `output_dir` | str | "output" | 输出文件目录 |

#### LLM 配置

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `OPENAI_API_KEY` | OpenAI API密钥 | 必填 |
| `LLM_BASE_URL` | LLM API端点 | https://api.openai.com/v1 |
| `LLM_MODEL` | 使用的模型 | gpt-4 |

### 🧪 运行测试

```bash
# 运行集成测试
python -m pytest tests/test_integration.py -v

# 运行生成的测试（需要启动API服务）
pytest output/test_api.py -v
```

### 📈 性能指标

基于Petstore API的测试结果：

| 指标 | 单轮迭代 | 多轮迭代（3次） | 改进 |
|------|---------|---------------|------|
| 覆盖率 | ~65% | ~85% | +20% |
| 测试用例数 | 15 | 28 | +87% |
| 执行时间 | 30s | 90s | - |
| LLM调用次数 | 3 | 9 | - |

### 🎯 测试技术

#### 等价类划分（EP）

- **有效等价类**：典型有效值、有效枚举值、范围内值
- **无效等价类**：错误类型、超出范围、无效枚举、缺失必填项

#### 边界值分析（BVA）

- 最小值、最大值
- 最小值-1、最大值+1
- 空字符串、零值
- 类型边界

### 🔍 故障排除

#### 常见问题

**Q: LLM调用失败怎么办？**

A: 检查以下项：
1. 确认 `OPENAI_API_KEY` 已正确设置
2. 检查网络连接和API端点
3. 查看日志中的详细错误信息

**Q: 生成的测试代码有语法错误？**

A: 系统会自动验证语法，但如遇问题：
1. 检查OpenAPI规范是否完整
2. 尝试降低 `temperature` 参数
3. 查看工作流日志定位问题

**Q: 覆盖率未达到预期？**

A: 尝试以下方法：
1. 增加 `max_iter` 参数
2. 降低 `coverage_threshold`
3. 检查OpenAPI规范的约束定义

### 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 📝 开发计划

- [ ] 支持更多测试框架（unittest、Robot Framework）
- [ ] 集成代码覆盖率工具（coverage.py）
- [ ] 支持性能测试和安全测试
- [ ] 添加测试用例优先级排序
- [ ] 支持测试数据生成
- [ ] 可视化测试报告

### 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

### 🙏 致谢

- [OpenAI](https://openai.com/) - 提供强大的语言模型
- [Streamlit](https://streamlit.io/) - 优秀的Web框架
- [Pytest](https://pytest.org/) - 强大的测试框架
- [Pydantic](https://pydantic-docs.helpmanual.io/) - 数据验证库

---

## English

### 📖 Introduction

AITestFlow is an innovative AI-driven testing platform that leverages Large Language Models (LLM) to automatically generate high-quality test cases from OpenAPI specifications. Through testing techniques like Equivalence Partitioning (EP) and Boundary Value Analysis (BVA), it achieves intelligent test generation and coverage optimization.

### ✨ Key Features

- 🤖 **AI-Driven Test Generation**: Leverage LLM to understand API semantics
- 📊 **Intelligent Coverage Optimization**: Multi-round feedback loop
- 🎯 **EP/BVA Testing Techniques**: Automatic equivalence partitioning and boundary analysis
- 🔄 **End-to-End Automation**: Complete workflow from OpenAPI spec to executable tests
- 📝 **Multiple Output Formats**: pytest code, coverage reports, workflow logs
- 🎨 **User-Friendly Web UI**: Streamlit-based visual interface
- 🛡️ **Robust Error Handling**: Smart retry, fallback strategies, detailed logging

### 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-api-key"

# Run web application
streamlit run app.py
```

### 📊 Performance Metrics

Based on Petstore API testing:

| Metric | Single Round | Multi-Round (3) | Improvement |
|--------|-------------|-----------------|-------------|
| Coverage | ~65% | ~85% | +20% |
| Test Cases | 15 | 28 | +87% |
| Execution Time | 30s | 90s | - |

### 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Made with ❤️ by AITestFlow Team**

[⬆ Back to Top](#-aitestflow---ai驱动的黑盒测试平台)

</div>
