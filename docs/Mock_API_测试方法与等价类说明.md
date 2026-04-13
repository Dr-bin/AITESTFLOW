# Mock API 测试方法与等价类说明

本文用于说明 `tools/mock_petstore_server.py` 的测试口径，帮助判断当前测试是否完备。

## 1. 测试目标与范围

- 被测对象：`tools/mock_petstore_server.py` 提供的本地模拟 API。
- 规范来源：`input/sample_petstore.yaml`。
- 执行入口：`tools/evaluate_real_coverage.py`，会启动 mock 服务并执行 `output/test_api.py`。
- 覆盖率定义（真实口径）：**通过用例所覆盖的条件数 / 条件总数**。

说明：该覆盖率反映“测试是否在真实 HTTP 调用下通过”，不是静态声明覆盖。

## 2. 如何执行

在项目根目录执行：

```bash
python tools/evaluate_real_coverage.py
```

输出文件：

- `output/real_coverage_report.json`
  - `coverage.real_active_coverage`：真实覆盖率（主指标）
  - `pytest.passed_test_ids` / `pytest.failed_test_ids`：通过/失败用例
  - `spec_endpoint_coverage.coverage_rate`：接口操作覆盖率

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

- 是否覆盖了 OpenAPI 的全部操作（`spec_endpoint_coverage` 是否为 100%）。
- 每个输入参数是否至少包含：1 个有效类 + 1 个无效类 + 边界类（如适用）。
- 是否覆盖了状态相关分支（存在/不存在、删除后再访问）。
- 是否覆盖了典型响应码分支（200/201/204/400/404）。
- 失败用例是否主要集中在“前置状态未准备”而非“参数类遗漏”。

## 6. 对当前结果的解读建议

- 若 `spec_endpoint_coverage=100%` 但 `real_active_coverage<100%`，通常表示：
  - 用例设计覆盖了接口，但部分等价类在真实执行中未通过（例如资源前置状态不满足）。
- 优先修复顺序：
  1. 先修复状态依赖失败（创建/删除顺序、目标 id 是否存在）；
  2. 再补充缺失的等价类；
  3. 最后复跑 `tools/evaluate_real_coverage.py` 验证是否收敛到目标覆盖率。

