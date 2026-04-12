# Example Submission: AITestFlow

**Title:** LLM-based Dynamic Black-box Testing for REST APIs Using OpenAPI, Equivalence Partitioning, and Boundary Value Analysis

---

## 1. Input

**System Overview:**  
The system under test is a **REST API** exposed over HTTP. Internal implementation (service code, database, infrastructure) is **not** assumed to be visible. Testing is **black-box**: behavior is inferred from a machine-readable **OpenAPI 3.x** description (paths, operations, parameters, request bodies, schemas, and declared status codes). This specification plays the role of **testable requirements** for the API’s externally observable behavior.

**Functional / Behavioral Specification (excerpt — Petstore-style sample):**  
The tool accepts a full OpenAPI document (YAML or JSON). An illustrative fragment:

- **R1. Resource discovery.** `GET /pets` supports listing pets with optional query parameters, e.g. `limit` (integer, bounded) and `status` (enumeration such as available / pending / sold).
- **R2. Single-resource access.** `GET /pets/{petId}` retrieves one pet by path parameter `petId`.
- **R3. Mutations.** `POST`, `PUT`, `DELETE` (and others if present) define creatable/updatable fields and expected success/error responses as described in the spec.

*Note for course alignment:* The assignment text allows “system requirements” as input; for API-centric systems, **OpenAPI is treated as structured requirements** (contract-based black-box specification). The tool does not currently ingest free-text narratives or a generic “test code repository” as its primary input.

---

## 2. Tool Artifact

**LLM Used:** Configurable via environment (e.g. `LLM_MODEL`, default `gpt-4`; compatible OpenAI-style endpoints via `LLM_BASE_URL`).

**Prompts Used (multi-stage pipeline):**  
The implementation uses separate prompt templates under `src/prompts/`, including:

1. **Condition generation (`gen_conditions.txt`)** — Instructs the model to derive **Equivalence Partitioning (EP)** and **Boundary Value Analysis (BVA)** style **test conditions** per endpoint: valid / invalid / boundary partitions for path, query, and body fields matching the OpenAPI definition. Output is structured (e.g. JSON with `id`, `parameter`, `partition_type`, `description`, `values`).

2. **Scenario generation (`gen_scenarios.txt`)** — Composes **concrete test cases** (`test_id`, `endpoint`, `method`, `payload`, `expected_status`, `covered_condition_ids`) from the generated conditions.

3. **Code generation (`gen_code.txt`)** — Produces executable **pytest** code that issues HTTP requests (e.g. via `requests`) against a configurable `BASE_URL`.

**Representative prompt excerpt (condition stage — paraphrased structure):**

```
You are a test designer. For the following API endpoint specification, identify
test conditions using Equivalence Partitioning and Boundary Value Analysis.
Use only parameters that exist in the spec. For each condition, output:
id, parameter, partition_type (valid|invalid|boundary), description, values.

Endpoint specification:
{ENDPOINT_OPENAPI_FRAGMENT}
```

*(The repository contains the full verbatim templates.)*

---

## 3. Generated Output

**Clarification — “Condition” vs “Test case”:**  
A single **condition** (e.g. `limit_boundary_3`) is **not** the same as a full **test case**. Conditions are **EP/BVA design units** per parameter. A **test case** combines concrete HTTP details (method, path, query/body, expected status) and **references** one or more condition IDs for **traceability**. The final **pytest** file is the executable realization of those test cases.

### 3.1 Equivalence Partitioning (illustrative — `GET /pets`)

| ID | Description | Partition | Representative values / intent |
|----|-------------|-----------|----------------------------------|
| EP-LIM-1 | `limit` within allowed valid range | valid | e.g. 1, 50, 100 |
| EP-LIM-2 | `limit` below minimum | invalid | e.g. 0 |
| EP-LIM-3 | `limit` above maximum | invalid | e.g. 101 |
| EP-LIM-4 | `limit` wrong type | invalid | e.g. string `"abc"` |
| EP-STAT-1 | `status` in allowed enum | valid | `available`, `pending`, `sold` |
| EP-STAT-2 | `status` not in enum | invalid | e.g. `active`, `invalid_status` |

*(Actual IDs in generated artifacts follow project naming, e.g. `limit_valid_1`, `status_invalid_2`.)*

### 3.2 Boundary Value Analysis (illustrative — integer `limit`)

| Boundary | Values (examples) |
|----------|-------------------|
| Minimum / just below | 0, 1 |
| Maximum / just above | 100, 101 |
| Typical interior | 50 |

### 3.3 Sample Test Cases (logical — as produced by scenario + code stages)

| Test Case | Scenario | Expected Result |
|-----------|----------|-----------------|
| TC001 | `GET /pets?limit=50&status=available` | HTTP 200; list response per API contract |
| TC_BVA | `GET /pets?limit=1` | HTTP 200; exercises lower valid boundary |
| TC_NEG | `GET /pets?limit=0` | HTTP 4xx (per spec / implementation) |
| TC_NEG | `GET /pets?limit=101` | HTTP 4xx |
| TC_NEG | `GET /pets?limit=abc` | HTTP 4xx or client validation path |

**Machine-readable outputs:**  
- `output/test_api.py` — generated pytest suite  
- `output/coverage_report.json` — condition-level coverage summary  
- `output/workflow_log.txt` — pipeline trace  

---

## 4. Experimental Analysis

### 4.1 Coverage of EP/BVA and test cases  
Report **condition coverage**: fraction of generated condition IDs that are **covered** by at least one passing test after mock/pytest validation, optionally refined over **feedback iterations** (`coverage_threshold`, `max_iter`). Compare coverage **before vs after** prompt or threshold changes.

### 4.2 Missing-item analysis  
Document gaps: undocumented error behaviors in OpenAPI, auth headers not modeled, complex inter-parameter constraints, or LLM hallucinated parameters. List **false positives/negatives** in generated tests.

### 4.3 Refining prompts for coverage, accuracy, and generalizability  
Examples: stricter “use only spec parameters,” explicit BVA rules for strings/dates, few-shot examples per parameter type, post-validation JSON repair, and iteration prompts that target **uncovered condition IDs**.

---

## 5. Project Report (outline for written submission)

### 5.1 Comparison to traditional non-AI-based techniques — pros and cons  
**Pros:** Scales to large OpenAPIs; combines EP/BVA guidance with LLM flexibility; automated pytest output.  
**Cons:** Non-determinism; dependency on spec quality; cost/latency; may need human review of edge cases.

### 5.2 Analytical report — limitations of AI and improvements  
Discuss hallucinations, weak specs, flaky expected status codes, and mitigation (schema validation of LLM output, retries, structured outputs, human-in-the-loop).

### 5.3 Summary  
Restate goal: **contract-driven black-box test generation** with **EP/BVA** and **measurable condition coverage**, aligned with dynamic API testing practice.

---

*This document mirrors the structure of “Example Submission Ex1” for course packaging. Replace illustrative tables with rows exported from your actual run on your chosen OpenAPI file before PDF submission.*
