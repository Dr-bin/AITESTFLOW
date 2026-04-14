# Petstore 分层覆盖对照表（人工复核版）

用途：对照 `input/sample_petstore.yaml`，人工核查生成测试是否覆盖了各类输入/输出分层。  
建议与 `output/design_report.md`、`output/test_api.py`、pytest 执行结果一起使用。

---

## A. 输入分层（EP + BVA）

| 接口 | 参数/字段 | 有效类型 | 无效类型 | 有效范围（可行域） | 无效范围（不可行域） | 是否已测 | 备注 |
|---|---|---|---|---|---|---|---|
| `GET /pets` | `limit` | `integer` | 非 `integer`（如 `"ten"`、`5.5`） | `1 <= limit <= 100` | `<1`（0、负数）、`>100`（101） | ☐ |  |
| `GET /pets` | `status` | `string` | 非 `string`（如 `123`） | 枚举 `{available,pending,sold}` | 非枚举（如 `adopted`、`Available`） | ☐ |  |
| `POST /pets` | `name` | `string` | 非 `string`（如 `123`） | 长度 `1..50`（必填） | 空串、长度 `>50`、缺失必填 | ☐ |  |
| `POST /pets` | `status` | `string` | 非 `string` | 枚举 `{available,pending,sold}` | 非枚举 | ☐ |  |
| `POST /pets` | `category` | `string` | 非 `string`（如 `42`） | 任意字符串（含空串） | 无（仅类型非法） | ☐ |  |
| `POST /pets` | `price` | `number` | 非 `number`（如 `"expensive"`） | `0 <= price <= 10000` | `<0`、`>10000` | ☐ |  |
| `GET /pets/{petId}` | `petId` | `integer` | 非 `integer`（`abc`、`3.14`） | `petId >= 1` | `petId < 1`（0、负数） | ☐ |  |
| `DELETE /pets/{petId}` | `petId` | `integer` | 非 `integer`（`abc`、`1.5`） | `petId >= 1` | `petId < 1`（0、负数） | ☐ |  |
| `POST /pets/{petId}/vaccinations` | `petId` | `integer` | 非 `integer`（如 `abc`） | `petId >= 1` 且资源存在 | `<1`（0、负数）或资源不存在 | ☐ |  |
| `POST /pets/{petId}/vaccinations` | `vaccine_name` | `string` | 非 `string`（如 `123`） | 非空字符串 | 空字符串 | ☐ |  |
| `POST /pets/{petId}/vaccinations` | `date` | `string` | 非 `string`（如 `20240115`） | `YYYY-MM-DD` 且日期有效 | 格式错误/语义无效（如 `2024-02-30`） | ☐ |  |
    
---

## B. 输出分层（状态码分区）

| 接口 | 输出类别 | 目标状态码 | 含义 | 是否已测 | 备注 |
|---|---|---|---|---|---|
| `GET /pets` | 有效输出 | `200` | 查询成功返回列表 | ☐ |  |
| `GET /pets` | 无效输出 | `400` | 请求参数非法 | ☐ |  |
| `GET /pets` | 无效输出 | `500` | 服务端内部错误 | ☐ |  |
| `POST /pets` | 有效输出 | `201` | 创建成功返回对象 | ☐ |  |
| `POST /pets` | 无效输出 | `400` | 输入非法 | ☐ |  |
| `POST /pets` | 无效输出 | `500` | 服务端内部错误 | ☐ |  |
| `GET /pets/{petId}` | 有效输出 | `200` | 按 ID 查询成功 | ☐ |  |
| `GET /pets/{petId}` | 无效输出 | `404` | 资源不存在 | ☐ |  |
| `GET /pets/{petId}` | 无效输出 | `500` | 服务端内部错误 | ☐ |  |
| `DELETE /pets/{petId}` | 有效输出 | `204` | 删除成功（无响应体） | ☐ |  |
| `DELETE /pets/{petId}` | 无效输出 | `404` | 资源不存在 | ☐ |  |
| `DELETE /pets/{petId}` | 无效输出 | `500` | 服务端内部错误 | ☐ |  |
| `POST /pets/{petId}/vaccinations` | 有效输出 | `201` | 新增疫苗记录成功 | ☐ |  |
| `POST /pets/{petId}/vaccinations` | 无效输出 | `400` | 输入或参数非法 | ☐ |  |
| `POST /pets/{petId}/vaccinations` | 无效输出 | `404` | 目标宠物不存在 | ☐ |  |

---

## C. 输入×输出组合总表（同接口逐条匹配）

说明：以下将“输入类型”与“输入范围/取值”显式拆分；每行只表达一种明确输入条件。  
例如：类型正确但范围外、类型错误（范围列写 `-`）、资源存在/不存在等。

| 编号 | 接口 | 参数/字段 | 输入类型 | 输入范围/取值 | 输出 | 组合含义（测试意图） |
|---|---|---|---|---|---|---|
| C01 | `GET /pets` | `limit` | `integer` | `1..100` | `200` | 类型正确且取值在合法范围内，查询成功。 |
| C02 | `GET /pets` | `limit` | `integer` | `非 1..100`（如 `0`、`101`） | `400` | 类型正确但范围越界，参数非法。 |
| C03 | `GET /pets` | `limit` | `非 integer` | `-` | `400` | 类型错误，参数非法。 |
| C04 | `GET /pets` | `limit` | `integer` | `1..100` | `500` | 输入本身合法，但触发服务内部异常分支。 |
| C05 | `GET /pets` | `status` | `string` | 枚举 `{available,pending,sold}` | `200` | 类型正确且枚举值合法，查询成功。 |
| C06 | `GET /pets` | `status` | `string` | 非枚举（如 `adopted`） | `400` | 类型正确但取值不在允许枚举内。 |
| C07 | `GET /pets` | `status` | `非 string` | `-` | `400` | 类型错误，参数非法。 |
| C08 | `GET /pets` | `status` | `string` | 枚举 `{available,pending,sold}` | `500` | 输入合法，但触发服务内部异常分支。 |
| C09 | `POST /pets` | `name` | `string` | 长度 `1..50` | `201` | 类型与长度均合法，创建成功。 |
| C10 | `POST /pets` | `name` | `string` | 空串（长度 `0`） | `400` | 类型正确但低于最小长度。 |
| C11 | `POST /pets` | `name` | `string` | 长度 `>50` | `400` | 类型正确但超出最大长度。 |
| C12 | `POST /pets` | `name` | `非 string` | `-` | `400` | 类型错误，参数非法。 |
| C13 | `POST /pets` | `name` | `缺失` | `缺失必填` | `400` | 必填字段缺失。 |
| C14 | `POST /pets` | `name` | `string` | 长度 `1..50` | `500` | 输入合法，但触发服务内部异常分支。 |
| C15 | `POST /pets` | `status` | `string` | 枚举 `{available,pending,sold}` | `201` | 类型与枚举值均合法，创建成功。 |
| C16 | `POST /pets` | `status` | `string` | 非枚举 | `400` | 类型正确但枚举非法。 |
| C17 | `POST /pets` | `status` | `非 string` | `-` | `400` | 类型错误，参数非法。 |
| C18 | `POST /pets` | `status` | `string` | 枚举 `{available,pending,sold}` | `500` | 输入合法，但触发服务内部异常分支。 |
| C19 | `POST /pets` | `category` | `string` | 任意字符串（含空串） | `201` | 类型合法即可通过。 |
| C20 | `POST /pets` | `category` | `非 string` | `-` | `400` | 类型错误，参数非法。 |
| C21 | `POST /pets` | `category` | `string` | 任意字符串（含空串） | `500` | 输入合法，但触发服务内部异常分支。 |
| C22 | `POST /pets` | `price` | `number` | `0..10000` | `201` | 类型与范围均合法，创建成功。 |
| C23 | `POST /pets` | `price` | `number` | `<0` 或 `>10000` | `400` | 类型正确但数值越界。 |
| C24 | `POST /pets` | `price` | `非 number` | `-` | `400` | 类型错误，参数非法。 |
| C25 | `POST /pets` | `price` | `number` | `0..10000` | `500` | 输入合法，但触发服务内部异常分支。 |
| C26 | `GET /pets/{petId}` | `petId` | `integer` | `>=1` 且资源存在 | `200` | 类型与范围合法且资源存在。 |
| C27 | `GET /pets/{petId}` | `petId` | `integer` | `>=1` 且资源不存在 | `404` | 类型与范围合法，但资源不存在。 |
| C28 | `GET /pets/{petId}` | `petId` | `integer` | `<1` | `400` | 类型正确但范围非法。 |
| C29 | `GET /pets/{petId}` | `petId` | `非 integer` | `-` | `400` | 类型错误。 |
| C30 | `GET /pets/{petId}` | `petId` | `integer` | `>=1` | `500` | 输入合法，但触发服务内部异常分支。 |
| C31 | `DELETE /pets/{petId}` | `petId` | `integer` | `>=1` 且资源存在 | `204` | 类型与范围合法且删除成功。 |
| C32 | `DELETE /pets/{petId}` | `petId` | `integer` | `>=1` 且资源不存在 | `404` | 类型与范围合法，但删除目标不存在。 |
| C33 | `DELETE /pets/{petId}` | `petId` | `integer` | `<1` | `400` | 类型正确但范围非法。 |
| C34 | `DELETE /pets/{petId}` | `petId` | `非 integer` | `-` | `400` | 类型错误。 |
| C35 | `DELETE /pets/{petId}` | `petId` | `integer` | `>=1` | `500` | 输入合法，但触发服务内部异常分支。 |
| C36 | `POST /pets/{petId}/vaccinations` | `petId` | `integer` | `>=1` 且资源存在 | `201` | `petId` 合法且资源存在，进入成功主路径。 |
| C37 | `POST /pets/{petId}/vaccinations` | `petId` | `integer` | `>=1` 且资源不存在 | `404` | `petId` 合法但目标资源不存在。 |
| C38 | `POST /pets/{petId}/vaccinations` | `petId` | `integer` | `<1` | `400` | 类型正确但范围非法。 |
| C39 | `POST /pets/{petId}/vaccinations` | `petId` | `非 integer` | `-` | `400` | 类型错误。 |
| C40 | `POST /pets/{petId}/vaccinations` | `vaccine_name` | `string` | 非空字符串 | `201` | 字段合法（且其余关键输入合法）时新增成功。 |
| C41 | `POST /pets/{petId}/vaccinations` | `vaccine_name` | `string` | 空字符串 | `400` | 类型正确但业务取值非法。 |
| C42 | `POST /pets/{petId}/vaccinations` | `vaccine_name` | `非 string` | `-` | `400` | 类型错误。 |
| C43 | `POST /pets/{petId}/vaccinations` | `vaccine_name` | `string` | 非空字符串（pet 不存在） | `404` | 字段本身合法，但资源不存在。 |
| C44 | `POST /pets/{petId}/vaccinations` | `date` | `string` | 合法日期 `YYYY-MM-DD` | `201` | 日期合法（且其余关键输入合法）时新增成功。 |
| C45 | `POST /pets/{petId}/vaccinations` | `date` | `string` | 非法日期/格式错误 | `400` | 类型正确但格式或语义非法。 |
| C46 | `POST /pets/{petId}/vaccinations` | `date` | `非 string` | `-` | `400` | 类型错误。 |
| C47 | `POST /pets/{petId}/vaccinations` | `date` | `string` | 合法日期（pet 不存在） | `404` | 日期字段合法，但资源不存在。 |

---

## D. 使用建议（人工比对与手工统计流程）

1. 先根据 `output/design_report.md` 与 `output/test_api.py`，把已设计/已实现的测试映射到本表对应行。  
2. 启动 `tools/mock_petstore_server.py` 并执行 pytest，确认测试代码可正常运行并记录通过/失败结果。  
3. 只对“已执行且结果符合预期”的条目在本表“是否已测”勾选。  
4. 对未勾选项补充测试场景后，重复第 2~3 步。  
5. 手工计算覆盖率并记录（可按输入层、输出层分别计算）：

```bash
覆盖率 = 已勾选条目数 / 对照表总条目数
```

6. 直到输入分层和输出分层都满足预期覆盖目标。
