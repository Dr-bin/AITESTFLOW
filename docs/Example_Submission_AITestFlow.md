# Example Submission: AITestFlow

**Title:** LLM-based Dynamic Black-box Testing for REST APIs Using OpenAPI, Equivalence Partitioning, and Boundary Value Analysis

---

## 1. Input

**System Overview:**  
The system under test is a REST API exposed over HTTP. Internal implementation details are not visible. The testing strategy is black-box and contract-driven, using OpenAPI 3.x as the only authoritative interface artifact.

**Functional scope in this run (`input/sample_petstore.yaml`):**

- `GET /pets` (query: `limit`, `status`)
- `POST /pets`
- `GET /pets/{petId}`
- `DELETE /pets/{petId}`
- `POST /pets/{petId}/vaccinations`

---

## 2. Tool Artifact

### 2.1 LLM and pipeline

The pipeline uses an OpenAI-compatible chat API via `src/llm_client.py`.  
Three prompt stages are used (`src/prompts/`):

- `gen_conditions.txt` for EP/BVA condition generation
- `gen_scenarios.txt` for executable scenario synthesis
- `gen_code.txt` for pytest module generation

### 2.2 Output files for this revision

- `output/test_api.py` (timestamp `2026-04-13T17:35:02.094785`)
- `output/design_report.md` (generated tables for EP/BVA/sample cases)
- `output/coverage_report.json` (mock-validation coverage)
- `output/real_coverage_report.json` (real execution coverage on mock API)

### 2.3 Real-evaluation harness added in this revision

- `tools/mock_petstore_server.py`: local executable Petstore mock service
- `tools/evaluate_real_coverage.py`: start mock server -> run `pytest output/test_api.py` -> compute validated condition coverage

---

## 3. Generated Output and Metrics

### 3.1 Design-side (mock validation) coverage

Source: `output/coverage_report.json`

| Field | Value |
|-------|-------|
| `total_conditions` | 57 |
| `validated_covered_count` | 57 |
| `coverage_rate` | 1.0 (100%) |
| `endpoints_processed` | 5 |
| `failed_test_cases` | [] |

Per-endpoint snapshot:

| Method | Path | Total conditions | Validated covered | Coverage |
|-------|------|------------------|-------------------|----------|
| GET | `/pets` | 13 | 13 | 1.0 |
| POST | `/pets` | 18 | 18 | 1.0 |
| GET | `/pets/{petId}` | 7 | 7 | 1.0 |
| DELETE | `/pets/{petId}` | 8 | 8 | 1.0 |
| POST | `/pets/{petId}/vaccinations` | 11 | 11 | 1.0 |

Interpretation: prompt-level EP/BVA mapping is internally complete under the existing mock validator definition.

### 3.2 Real execution coverage (new)

Source: `output/real_coverage_report.json` + local server `tools/mock_petstore_server.py`

| Metric | Value |
|--------|-------|
| `pytest` result | 37 passed, 5 failed |
| `real_active_coverage` | 0.833333 (83.33%) |
| `validated_condition_total` | 40 |
| `active_condition_total` | 48 |
| `spec_endpoint_coverage` | 1.0 (5/5 operations) |

Interpretation:

- Operation-level reachability is complete (all 5 operations are exercised).
- Condition-level real pass coverage is partial (83.33%), mainly reduced by state-dependent failures.

### 3.3 Failure pattern from real execution

Dominant mismatch in `pytest.output_excerpt`:

- Expected `201`, actual `404`, message `"pet not found"` on several cases.

This indicates **resource precondition/state dependency** issues rather than pure parameter partition issues:

- Some tests assume a resource exists before mutation (e.g., vaccination records).
- Actual execution order/data state causes missing-resource branches.

### 3.4 Structural quality of generated test module (improved)

Current merged code structure in `output/test_api.py`:

- One global `make_request` definition.
- Namespaced scenario/function blocks (`test_scenarios_1...5`, `test_api_scenario_1...5`).

This fixes the earlier duplicate-definition collision problem in merged modules.

---

## 4. Experimental Analysis

### 4.1 Is this run "complete"?

**Partially complete.**

- **Complete on interface-operation coverage:** 5/5 operations exercised.
- **Complete on mock design coverage:** 57/57 under internal mock metric.
- **Not complete on real pass coverage:** 40/48 condition IDs validated by passing tests.

Conclusion: the generated suite is strong in EP/BVA breadth, but still not fully robust to stateful execution semantics.

### 4.2 Gap diagnosis (why 83.33%, not 100%)

Primary causes:

- Missing explicit modeling of data preconditions in scenario design.
- Scenarios with correct partitions but incorrect assumed world state.
- Prompt currently emphasizes parameter correctness and coverage IDs, but not setup/teardown contracts.

Secondary observations:

- Naming consistency still has minor drift (`petId` vs `petid` in condition IDs), which can affect traceability.

### 4.3 Recommended improvements

1. Add **state-aware scenario constraints** in prompts:
   - mark scenarios requiring existing resource
   - mark scenarios requiring non-existing resource
2. Add **optional setup hooks** in generated code:
   - create resource before dependent mutation tests
   - isolate destructive tests
3. Keep dual metrics as standard:
   - design coverage (`coverage_report.json`)
   - real validated coverage (`real_coverage_report.json`)
4. Keep namespaced merge strategy (already implemented) to prevent symbol collisions.

---

## 5. Project Report

### 5.1 Comparison with traditional non-AI testing

Traditional rule/manual methods are deterministic and auditable, but costly for broad EP/BVA exploration.  
The LLM-assisted pipeline scales scenario generation quickly and preserves traceability through `covered_condition_ids`, but needs stronger control of stateful assumptions.

### 5.2 Limitations and practical next steps

Current limitations:

- State-precondition modeling is weak in prompts.
- Real pass coverage lags behind design coverage.
- Condition naming normalization is not fully enforced.

Next steps:

- encode precondition tags in scenario generation;
- add setup/teardown templates for stateful endpoints;
- normalize condition naming convention globally.

### 5.3 Summary

For `input/sample_petstore.yaml`, this revision demonstrates:

- 57 generated design conditions over 5 operations;
- 100% mock-validation coverage (`57/57`);
- 83.33% real validated condition coverage (`40/48`);
- 37 passed / 5 failed tests in real execution;
- 100% operation coverage (`5/5`) against the OpenAPI surface.

The current tool is effective for broad black-box EP/BVA generation and executable test synthesis, and now includes a practical real-execution evaluation loop. The main remaining risk is stateful precondition handling, not parameter partition breadth.

---

*After each new run, refresh metrics from `output/coverage_report.json` and `output/real_coverage_report.json`.*
