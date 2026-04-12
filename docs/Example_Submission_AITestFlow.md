# Example Submission: AITestFlow

**Title:** LLM-based Dynamic Black-box Testing for REST APIs Using OpenAPI, Equivalence Partitioning, and Boundary Value Analysis

---

## 1. Input

**System Overview:**  
The system under test is a **REST API** exposed over HTTP (e.g. a pet-store style service). The internal application code, persistence layer, and infrastructure are **not** visible to the tester. Testing is **black-box**: only **externally observable behavior** is considered, as specified by a machine-readable **OpenAPI 3.x** document (paths, operations, parameters, request bodies, schemas, and declared responses).

**Functional Requirements (contract-level, excerpt — sample Petstore API):**

- **R1.** **List resources.** `GET /pets` supports listing pets with optional query parameters `limit` (bounded integer) and `status` (enumeration, e.g. available, pending, sold).

- **R2.** **Single resource access.** `GET /pets/{petId}` returns one pet; `petId` is a path parameter.

- **R3.** **Create resource.** `POST /pets` accepts a JSON body with fields such as `name`, `category`, `status`, `price`, and related constraints as defined in the schema.

- **R4.** **Sub-resource mutation.** `POST /pets/{petId}/vaccinations` records a vaccination with body fields such as vaccine name and date, subject to the declared schema.

**Input artifact for this run:** `input/sample_petstore.yaml`.

---

## 2. Tool Artifact

**LLM Used:**  
As configured in the project environment when the run was executed (e.g. `LLM_MODEL`, `LLM_BASE_URL`, `OPENAI_API_KEY` in `.env`). The implementation uses the OpenAI-compatible chat API with `response_format={"type": "json_object"}` where supported (`src/llm_client.py`).

**Prompts Used (multi-stage; full text in `src/prompts/`):**

**Stage A — Test conditions (EP / BVA), `gen_conditions.txt`:**  

```text
You are a test designer. Generate test conditions for ONE API endpoint using
Equivalence Partitioning (EP) and Boundary Value Analysis (BVA).

Endpoint specification (JSON):
<ENDPOINT_METADATA_FROM_OPENAPI>

Rules: use ONLY parameters that appear in the specification; output a JSON object
with key "conditions" whose value is an array of objects:
id, parameter, partition_type (valid|invalid|boundary), description, values.
```

**Stage B — Executable scenarios, `gen_scenarios.txt`:**  
Maps conditions to concrete cases with `test_id`, `endpoint`, `method`, `query`, `payload`, `expected_status`, and `covered_condition_ids` (JSON object with key `test_cases`).

**Stage C — Pytest code, `gen_code.txt`:**  
Emits a JSON object `{"python_code": "..."}` containing a pytest module that calls the API (e.g. via `requests`) using `query` / `payload` and `expected_status`.

**Model-generated outputs (this run):**

- `output/test_api.py` — header timestamp **2026-04-12T20:32:39.816268**  
- `output/design_report.md` — **auto-generated** EP / BVA / sample-case tables per endpoint (`src/design_report.py`)

---

## 3. Generated Output

**Data source:** Metrics and tables below match:

- `output/coverage_report.json` — **timestamp** `2026-04-12T20:32:39.819188`  
- `output/test_api.py` — first-occurrence `test_scenarios` blocks per endpoint  
- `output/design_report.md` — same conditions / test cases in long-form tables  

### 3.0 Aggregate coverage report (`coverage_report.json`)

| Field | Value |
|-------|--------|
| `coverage_definition` | Weighted **mock pytest** validation: **Σ validated_covered_count_i / Σ total_conditions_i** per endpoint (see JSON for full text). |
| `total_conditions` | **69** |
| `validated_covered_count` | **69** |
| `coverage_rate` | **1.0** (100%) |
| `covered_condition_ids` | **62** strings (**global union** of IDs still present after validation; same text reused on different endpoints appears once). |
| `failed_test_cases` | **[]** |
| `iteration` | **2** |
| `endpoints_processed` | **5** (matches OpenAPI operations processed) |

**Related metric (different definition):** **Contract-level response coverage** — fraction of **OpenAPI-declared operation–status pairs** that appear as **`expected_status`** in generated tests — is **~66.7%** for this spec (**§3.4**). This is **not** the same as `coverage_rate` in the JSON.

**Per-endpoint snapshot (abbreviated):**

| Method | Path | `total_conditions` | `validated_covered_count` | `coverage_rate` |
|--------|------|-------------------|---------------------------|-----------------|
| GET | `/pets` | 18 | 18 | 1.0 |
| POST | `/pets` | 23 | 23 | 1.0 |
| GET | `/pets/{petId}` | 8 | 8 | 1.0 |
| DELETE | `/pets/{petId}` | 7 | 7 | 1.0 |
| POST | `/pets/{petId}/vaccinations` | 13 | 13 | 1.0 |

### 3.1 Equivalence partitioning — condition IDs (global union)

The **62** IDs in `covered_condition_ids` are listed in `coverage_report.json`. By **keyword** (for quick EP/BVA discussion):

| Bucket | Count | Interpretation |
|--------|-------|----------------|
| IDs containing `boundary` | **12** | Boundary-oriented partitions |
| IDs containing `invalid` | **31** | Invalid type / range / enum / semantic |
| Neither (treated as **valid-class** here) | **19** | Valid partitions |

*(For submission-style rows with descriptions, use **`output/design_report.md`**, built from each `EPCondition`’s `description` and `partition_type`.)*

### 3.2 Boundary value analysis — values exercised in `test_api.py`

**Query `limit` (`GET /pets`) — examples from generated scenarios:**

| Role | Values |
|------|--------|
| Valid / interior | `50`, `10`, `1`, `100` (with various `status`) |
| Out of range | `0`, `101`, `1000` |
| Wrong type / sign | `"ten"`, `5.5`, `-10` |

**Path `petId` (`GET /pets/{petId}`):**

| Role | Path segment |
|------|----------------|
| Valid | `5`, `999999` |
| Boundary | `1`, `0` (expected `400` for `0`) |
| Invalid | `-5`, `3.14`, `abc` |

**`POST /pets/{petId}/vaccinations` (excerpt):**

| Role | Example |
|------|---------|
| Valid body | `vaccine_name` + `date` e.g. `"2024-03-15"` |
| Path variants | `/pets/100`, `/pets/1`, `/pets/abc`, `/pets/-5`, `/pets/0` |
| Invalid body | numeric `vaccine_name`, wrong `date` formats (see file) |

### 3.3 Sample test cases (verbatim from `output/test_api.py`)

**`GET /pets` (excerpt)**

| Test Case | Scenario (query) | Expected | `covered_condition_ids` |
|-----------|------------------|----------|-------------------------|
| TC001 | `limit=50`, `status=available` | 200 | `limit_valid_1`, `status_valid_1` |
| TC002 | `limit=10`, `status=pending` | 200 | `limit_valid_2`, `status_valid_2` |
| TC003 | `limit=1`, `status=sold` | 200 | `limit_boundary_1`, `status_valid_3` |
| TC004 | `limit=100` | 200 | `limit_boundary_2` |
| TC_NEG_001 | `limit=0` | 400 | `limit_boundary_3` |
| TC_NEG_003 | `limit="ten"` | 400 | `limit_invalid_type_string` |
| TC_NEG_004 | `limit=5.5` | 400 | `limit_invalid_type_float` |
| TC_NEG_007 | `status="adopted"` | 400 | `status_invalid_1` |

**`GET /pets/{petId}`**

| Test Case | Endpoint | Expected | `covered_condition_ids` |
|-----------|----------|----------|-------------------------|
| TC001 | `/pets/5` | 200 | `petId_valid_1` |
| TC002 | `/pets/999999` | 200 | `petId_valid_2` |
| TC_BVA_001 | `/pets/1` | 200 | `petId_boundary_1` |
| TC_BVA_002 | `/pets/0` | 400 | `petId_boundary_2`, `petId_invalid_type_2` |
| TC_NEG_001 | `/pets/-5` | 400 | `petId_invalid_type_1` |
| TC_NEG_002 | `/pets/3.14` | 400 | `petId_invalid_type_3` |
| TC_NEG_003 | `/pets/abc` | 400 | `petId_invalid_type_4` |

**`POST /pets/{petId}/vaccinations` (excerpt)**

| Test Case | Endpoint | Payload (abbrev.) | Expected | `covered_condition_ids` |
|-----------|----------|-------------------|----------|-------------------------|
| TC001 | `/pets/100/vaccinations` | Rabies + `2024-03-15` | 201 | `petid_valid_1`, `vaccine_name_valid_1`, `date_valid_1` |
| TC002 | `/pets/1/vaccinations` | Flu + date | 201 | `petid_boundary_1`, `vaccine_name_valid_2`, `date_valid_1` |
| TC_NEG_003 | `/pets/100/vaccinations` | `vaccine_name=123` | 400 | `vaccine_name_invalid_type_number` |

### 3.4 Contract-level response coverage (OpenAPI vs generated `expected_status`)

The **100%** figure in §3.0 counts **EP/BVA conditions** validated under **mock pytest**. A separate question is whether every **HTTP status** that the **OpenAPI document explicitly lists** for an operation is represented by at least one generated scenario (`expected_status` in `output/test_api.py`). If a status is declared but no test expects it, that is a **contract response gap** (incomplete coverage of the published contract surface), independent of mock condition coverage.

**Declared vs exercised (artifact: `input/sample_petstore.yaml`; exercised set verified: no `404` or `500` appears in `output/test_api.py`).**

| Operation | Status codes in OpenAPI | Status codes present in generated tests |
|-----------|-------------------------|----------------------------------------|
| `GET /pets` | 200, 400, **500** | 200, 400 |
| `POST /pets` | 201, 400, **500** | 201, 400 |
| `GET /pets/{petId}` | 200, **404**, **500** | 200, 400 |
| `DELETE /pets/{petId}` | 204, **404**, **500** | 204, 400 |
| `POST /pets/{petId}/vaccinations` | 201, 400, **404** | 201, 400 |

**Counts (treating each operation–status pair once):**

- **Declared pairs:** **15** (sum of the five row counts above).
- **Pairs with ≥1 matching `expected_status`:** **10**.
- **Declared pairs never targeted:** **7** — all **500** where the spec lists them (**4** operations), plus **404** on `GET`/`DELETE` `/{petId}` and **404** on `POST .../vaccinations` (**3** operations).

**Contract response coverage (declared statuses that have a test expectation):** **10 / 15 ≈ 66.7%**.

**Additional design gaps (not separate status rows but relevant to “full” black-box breadth):**

- **`GET /pets`:** query parameters are optional; the design tables show scenarios that always include at least one query parameter—**no explicit “no query string”** happy-path row.
- **`POST /pets`:** `requestBody` is required and `name` is the only required field in `PetInput`; the sample matrix does not highlight **empty body**, **missing `name`**, or **minimal valid body** as first-class rows (may or may not appear in code; they are not emphasized in `design_report.md`).

---

## 4. Experimental Analysis

### 4.1 Coverage of EP/BVA and test cases

- **Primary metric (assignment-friendly):** `coverage_rate` = **validated_covered_count / total_conditions** = **69/69 = 100%** for this run. Each term is summed **per endpoint** after **mock pytest**: condition IDs are removed from the “covered” set when mapped tests **fail** (`src/validator.py` + `src/coordinator.py`).
- **`per_endpoint_coverage`** in `coverage_report.json` supports **§4.1** tables: for each operation you can report EP/BVA condition counts and whether mock validation kept full coverage.
- **`covered_condition_ids` (62)** is the **sorted union** of ID strings still covered somewhere; **69 − 62 = 7** reflects **reuse of the same id text on more than one endpoint** (e.g. `petId_boundary_1` on both GET and DELETE), not failed tests.
- **Do not conflate with contract coverage:** **§3.4** shows that **mock condition coverage can be 100%** while **OpenAPI-declared response codes** are only partially represented (**~66.7%** for this spec).
- **Human-readable EP/BVA/TC tables:** `output/design_report.md` aligns with coursework-style “Equivalence partitioning / BVA / sample test cases” presentation.

### 4.2 Missing-item analysis

- **Contract responses:** Missing expectations for **404** (resource not found) and **500** (server error) where the spec lists them—see **§3.4**. Improving prompts or post-processing to **enumerate declared responses per operation** and require at least one scenario (or an explicit “not testable without fault injection” note) would close this gap in reporting and design.
- **Naming:** Mixed **`petId` / `petid`** in IDs persists; hurts traceability when merging reports.
- **Merged `test_api.py`:** Duplicate **`make_request`** blocks and repeated **`test_scenarios`** sections remain a **static-quality** issue for reviewers (not reflected in mock `failed_test_cases`).
- **Spec vs implementation:** Even where **400** is expected, a live service might return **404** or **422**; contract-level tables still help separate “what we asserted” from “what the spec promised.”
- **Windows / pytest:** Subprocess decoding was hardened (`encoding="utf-8", errors="replace"`) so pytest output parsing is more reliable on non-UTF-8 consoles.

### 4.3 Refining prompts for improving coverage, accuracy, and generalizability

- **Stable IDs:** Prefix condition ids with **method + path** to reduce accidental reuse across endpoints.
- **Merge / codegen:** Single `make_request`, optional dedupe pass on merged file.
- **Prompts:** Few-shots for dates, floats in query strings, and auth headers if added to OpenAPI.
- **Evaluation:** Keep **`design_report.md` + `coverage_report.json`** as the standard **4.1** artifacts for the course write-up.

---

## 5. Project Report

### 5.1 Comparison to traditional non-AI-based technique, pros and cons  

**Traditional (manual or rule-based from OpenAPI):** predictable and auditable, no model cost, but heavy manual effort on large APIs and easy to miss edge combinations.  

**LLM-assisted (this tool):** scales to many operations and encodes EP/BVA in prompts; produces runnable tests and **exportable design tables**; non-deterministic, sensitive to spec and model quality, and incurs API cost and latency.

### 5.2 Analytical report: limitations of AI and the ways to improve the tool  

Limitations include naming drift, merged-code duplication, mock-only validation, and **incomplete mapping from OpenAPI response lists to test expectations** (§3.4). Improvements: namespaced IDs, cleaner merge, prompt or pipeline steps that **enumerate declared status codes per operation**, and tighter JSON/code repair.

### 5.3 Summary  

On **`input/sample_petstore.yaml`**, this run produced **69** conditions (summed across **5** endpoints), **100% weighted validated coverage** under mock pytest, **62** distinct condition-id strings in the global union, **no failed test records** in `coverage_report.json`, **`output/design_report.md`** for coursework-style tables, and merged **`output/test_api.py`** with traceable **`covered_condition_ids`**. Separately, **§3.4** records **~66.7% contract-level response coverage** (10 of 15 declared operation–status pairs have a matching `expected_status`), highlighting **404** and **500** as the main omitted expectations.

---

*After any new pipeline run, refresh `output/*` and update timestamps / tables in Sections 2–3 if they change.*
