# Mock API 测试方法与覆盖统计说明（当前版）

本文描述当前保留方案：使用 `tools/mock_petstore_server.py` 提供模拟 API，执行 `output/test_api.py`，并由模拟服务在响应过程中自动记录覆盖条件。

---

## 1. 当前方案概述

- **被测对象**：`tools/mock_petstore_server.py`
- **测试执行**：`python -m pytest output/test_api.py -v`
- **覆盖统计来源**：模拟服务内置覆盖跟踪
- **统计口径**：基于 `tools/petstore_分层覆盖对照表.md` 的 `C01..C47`
- **特殊规则**：所有输出为 `500` 的条件默认不纳入覆盖率分母

忽略的 `500` 条件：

- `C04`、`C08`、`C14`、`C18`、`C21`、`C25`、`C30`、`C35`

---

## 2. 如何执行

在项目根目录执行：

```bash
python tools/mock_petstore_server.py
```

新开终端执行测试：

```bash
python -m pytest output/test_api.py -v
```

查看覆盖统计：

```bash
curl http://127.0.0.1:8000/__coverage
```

重置覆盖记录（可选）：

```bash
curl -X POST http://127.0.0.1:8000/__coverage/reset
```

---

## 3. 覆盖统计输出说明

`GET /__coverage` 返回 JSON，关键字段如下：

- `total_conditions_excluding_500`：分母（已剔除 500 条件）
- `covered_conditions_excluding_500`：已覆盖条目数
- `coverage_rate`：覆盖率
- `covered_condition_ids`：已覆盖条件 ID 列表
- `missing_condition_ids`：未覆盖条件 ID 列表
- `ignored_500_condition_ids`：被忽略的 500 条件 ID

---

## 4. 与对照表的关系

`tools/petstore_分层覆盖对照表.md` 中：

- A/B 是人工分层视图（输入与输出）
- C 是输入输出组合条件（`C01..C47`）

当前 mock 覆盖统计直接对应 C 表条目，可用于：

1. 快速定位未覆盖组合条件
2. 与人工复核结果互相校验
3. 为后续补充测试用例提供明确目标

---

## 5. 当前方案注意事项

- `DELETE /pets/{petId}` 对种子数据做了稳定性处理，避免测试之间相互污染。
- 统计口径默认不考核 500 分支（按当前项目约定）。
- 若后续要恢复 500 分支考核，只需把对应 ID 从忽略列表移除，并补充可稳定触发 500 的测试机制。

# Mock API 测试方法与等价类说明

本文用于说明 `tools/mock_petstore_server.py` 的测试口径，帮助判断当前测试是否完备。

## 1. 测试目标与范围

- 被测对象：`tools/mock_petstore_server.py` 提供的本地模拟 API。
- 规范来源：`input/sample_petstore.yaml`。
- 执行入口：`tools/mock_petstore_server.py` + `python -m pytest output/test_api.py -v`。
- 覆盖率定义（真实口径）：**按 `tools/petstore_分层覆盖对照表.md` 人工勾选条目数 / 对照表条目总数**。

说明：该覆盖率反映“测试是否在真实 HTTP 调用下通过”，不是静态声明覆盖。

## 2. 如何执行

在项目根目录按以下步骤执行：

```bash
python tools/mock_petstore_server.py
# 新开终端
python -m pytest output/test_api.py -v
```

统计依据：

- `tools/petstore_分层覆盖对照表.md`
  - 输入分层与输出分层分别勾选“是否已测”
  - 以“已勾选 / 总条目”计算覆盖率
  - 可附 pytest 通过/失败结果作为证据

## 3. Mock API 行为模型

服务默认监听 `127.0.0.1:8000`，初始内置数据包含 petId：`1`、`5`、`100`。

实现接口：

- `GET /pets`
- `POST /pets`
- `GET /pets/{petId}`
- `DELETE /pets/{petId}`
- `POST /pets/{petId}/vaccinations`

状态相关逻辑：

- `DELETE /pets/{petId}` 删除后，该 id 再访问会进入“资源不存在”分支。
- `POST /pets/{petId}/vaccinations` 依赖目标宠物存在，否则返回 `404`。

## 4. 等价类与边界类清单（按接口）

以下清单即“应被测试文档覆盖”的目标集合。

### 4.1 `GET /pets`

参数：`limit`（1~100 整数）、`status`（`available|pending|sold`）

- `limit` 有效等价类
  - 正常整数且在区间内（如 50）
  - 下边界（1）
  - 上边界（100）
- `limit` 无效等价类
  - 小于最小值（0、负数）
  - 大于最大值（101）
  - 类型非法（字符串、浮点、布尔）
- `status` 有效等价类
  - `available` / `pending` / `sold`
- `status` 无效等价类
  - 非枚举值（如 `adopted`）
  - 空字符串
  - 类型非法（数字、布尔）
- 组合类
  - 两参数均合法（返回 `200`）
  - 任一参数非法（返回 `400`）

### 4.2 `POST /pets`

参数：`name`（字符串，长度 1~50，必填），`status`（枚举），`category`（字符串），`price`（0~10000 数值）

- `name` 有效等价类
  - 合法普通字符串
  - 下边界长度（1）
  - 上边界长度（50）
- `name` 无效等价类
  - 空字符串
  - 超长（51）
  - 类型非法（数字/布尔/null）
- `status` 有效/无效等价类
  - 有效枚举：`available|pending|sold`
  - 无效枚举、非法类型
- `category` 有效/无效等价类
  - 合法字符串（可空）
  - 非字符串类型
- `price` 有效等价类
  - 正常值（如 99.99）
  - 下边界（0）
  - 上边界（10000）
- `price` 无效等价类
  - 小于 0
  - 大于 10000
  - 类型非法（字符串/布尔/null）

### 4.3 `GET /pets/{petId}`

参数：`petId`（路径参数，正整数）

- 有效等价类
  - 正整数且资源存在（`200`）
  - 正整数但资源不存在（`404`）
- 无效等价类
  - 0 或负数（`400`）
  - 非整数格式（如 `abc`、`3.14`，`400`）

### 4.4 `DELETE /pets/{petId}`

参数同上（正整数）

- 有效等价类
  - 正整数且资源存在（`204`）
  - 正整数但资源不存在（`404`）
- 无效等价类
  - 0/负数（`400`）
  - 非整数格式（`400`）

### 4.5 `POST /pets/{petId}/vaccinations`

参数：`petId`（正整数，且资源存在）、body 字段 `vaccine_name`、`date`（`YYYY-MM-DD`）

- `petId` 有效/无效等价类
  - 合法且存在（`201`）
  - 合法但不存在（`404`）
  - 非法格式或非正整数（`400`）
- `vaccine_name` 有效/无效等价类
  - 非空字符串（有效）
  - 空字符串、非字符串（无效）
- `date` 有效/无效等价类
  - 合法日期格式（如 `2024-01-15`）
  - 非字符串
  - 错误格式（如 `15-01-2024`）
  - 语义非法日期（如 `2024-02-30`）
  - 空字符串

## 5. 完备性检查表（评审时建议逐项勾选）

- 是否覆盖了 OpenAPI 的全部操作（5 个接口操作是否都被触达）。
- 每个输入参数是否至少包含：1 个有效类 + 1 个无效类 + 边界类（如适用）。
- 是否覆盖了状态相关分支（存在/不存在、删除后再访问）。
- 是否覆盖了典型响应码分支（200/201/204/400/404）。
- 失败用例是否主要集中在“前置状态未准备”而非“参数类遗漏”。

## 6. 对当前结果的解读建议

- 若接口触达为 100% 但人工覆盖率 <100%，通常表示：
  - 用例设计覆盖了接口，但部分等价类在真实执行中未通过（例如资源前置状态不满足）。
- 优先修复顺序：
  1. 先修复状态依赖失败（创建/删除顺序、目标 id 是否存在）；
  2. 再补充缺失的等价类；
  3. 最后重跑 pytest 并更新 `tools/petstore_分层覆盖对照表.md` 验证是否收敛到目标覆盖率。

