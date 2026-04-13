# AITestFlow — Test Design Report

*Generated: 2026-04-13T17:35:02*

## GET `/pets`

### Equivalence partitioning

| ID | Parameter | Description | Outcome |
|----|-----------|-------------|---------|
| limit_valid_1 | `limit` | Typical valid integer within range | valid |
| limit_valid_2 | `limit` | Minimum valid value | valid |
| limit_valid_3 | `limit` | Maximum valid value | valid |
| limit_invalid_type | `limit` | Non-integer value | invalid |
| limit_invalid_1 | `limit` | Below minimum bound | invalid |
| limit_invalid_2 | `limit` | Above maximum bound | invalid |
| status_valid_1 | `status` | Valid enum value 'available' | valid |
| status_valid_2 | `status` | Valid enum value 'pending' | valid |
| status_valid_3 | `status` | Valid enum value 'sold' | valid |
| status_invalid_1 | `status` | Invalid enum value | invalid |
| status_invalid_type | `status` | Non-string value | invalid |

### Boundary value analysis

| ID | Parameter | Description | Values |
|----|-----------|-------------|--------|
| limit_boundary_1 | `limit` | Just below minimum | 0 |
| limit_boundary_2 | `limit` | Just above maximum | 101 |

### Sample test cases

| Test case | Scenario | Expected result |
|-----------|----------|-----------------|
| TC001 | GET `/pets` — query `{"limit": 50, "status": "available"}` | HTTP 200 *(conditions: limit_valid_1, status_valid_1)* |
| TC002 | GET `/pets` — query `{"limit": 1, "status": "pending"}` | HTTP 200 *(conditions: limit_valid_2, status_valid_2)* |
| TC003 | GET `/pets` — query `{"limit": 100, "status": "sold"}` | HTTP 200 *(conditions: limit_valid_3, status_valid_3)* |
| TC_NEG_001 | GET `/pets` — query `{"limit": "ten"}` | HTTP 400 *(conditions: limit_invalid_type)* |
| TC_NEG_002 | GET `/pets` — query `{"limit": 0}` | HTTP 400 *(conditions: limit_invalid_1, limit_boundary_1)* |
| TC_NEG_003 | GET `/pets` — query `{"limit": 101}` | HTTP 400 *(conditions: limit_invalid_2, limit_boundary_2)* |
| TC_NEG_004 | GET `/pets` — query `{"status": "adopted"}` | HTTP 400 *(conditions: status_invalid_1)* |
| TC_NEG_005 | GET `/pets` — query `{"status": 123}` | HTTP 400 *(conditions: status_invalid_type)* |

## POST `/pets`

### Equivalence partitioning

| ID | Parameter | Description | Outcome |
|----|-----------|-------------|---------|
| name_valid_1 | `name` | Valid name with minimum length | valid |
| name_valid_2 | `name` | Valid name with maximum length | valid |
| name_invalid_type | `name` | Name with wrong type (number) | invalid |
| status_valid_1 | `status` | Valid status enum value | valid |
| status_valid_2 | `status` | Another valid status enum value | valid |
| status_valid_3 | `status` | Third valid status enum value | valid |
| status_invalid_1 | `status` | Invalid status enum value | invalid |
| status_invalid_type | `status` | Status with wrong type (number) | invalid |
| category_valid_1 | `category` | Valid category string | valid |
| category_invalid_type | `category` | Category with wrong type (number) | invalid |
| price_valid_1 | `price` | Valid price at minimum | valid |
| price_valid_2 | `price` | Valid price at maximum | valid |
| price_valid_3 | `price` | Valid price in middle range | valid |
| price_invalid_type | `price` | Price with wrong type (string) | invalid |

### Boundary value analysis

| ID | Parameter | Description | Values |
|----|-----------|-------------|--------|
| name_boundary_1 | `name` | Name below minimum length (empty string) | "" |
| name_boundary_2 | `name` | Name above maximum length | "Lorem ipsum dolor sit amet, consectetur adipiscing elit." |
| price_boundary_1 | `price` | Price below minimum | -1 |
| price_boundary_2 | `price` | Price above maximum | 10001 |

### Sample test cases

| Test case | Scenario | Expected result |
|-----------|----------|-----------------|
| TC001 | POST `/pets` — body `{"name": "a", "status": "available", "category": "dog", "price": 0}` | HTTP 201 *(conditions: name_valid_1, status_valid_1, category_valid_1, price_valid_1)* |
| TC002 | POST `/pets` — body `{"name": "Lorem ipsum dolor sit amet, consectetur adipiscing elit", "status": "pending", "category": "dog", "price": 10000}` | HTTP 201 *(conditions: name_valid_2, status_valid_2, category_valid_1, price_valid_2)* |
| TC003 | POST `/pets` — body `{"name": "a", "status": "sold", "category": "dog", "price": 5000}` | HTTP 201 *(conditions: name_valid_1, status_valid_3, category_valid_1, price_valid_3)* |
| TC_BVA_001 | POST `/pets` — body `{"name": "", "status": "available", "category": "dog", "price": 0}` | HTTP 400 *(conditions: name_boundary_1)* |
| TC_BVA_002 | POST `/pets` — body `{"name": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.", "status": "available", "category": "dog", "price": 0}` | HTTP 400 *(conditions: name_boundary_2)* |
| TC_NEG_001 | POST `/pets` — body `{"name": 123, "status": "available", "category": "dog", "price": 0}` | HTTP 400 *(conditions: name_invalid_type)* |
| TC_NEG_002 | POST `/pets` — body `{"name": "a", "status": "invalid_status", "category": "dog", "price": 0}` | HTTP 400 *(conditions: status_invalid_1)* |
| TC_NEG_003 | POST `/pets` — body `{"name": "a", "status": 123, "category": "dog", "price": 0}` | HTTP 400 *(conditions: status_invalid_type)* |
| TC_NEG_004 | POST `/pets` — body `{"name": "a", "status": "available", "category": 123, "price": 0}` | HTTP 400 *(conditions: category_invalid_type)* |
| TC_BVA_003 | POST `/pets` — body `{"name": "a", "status": "available", "category": "dog", "price": -1}` | HTTP 400 *(conditions: price_boundary_1)* |
| TC_BVA_004 | POST `/pets` — body `{"name": "a", "status": "available", "category": "dog", "price": 10001}` | HTTP 400 *(conditions: price_boundary_2)* |
| TC_NEG_005 | POST `/pets` — body `{"name": "a", "status": "available", "category": "dog", "price": "not_a_number"}` | HTTP 400 *(conditions: price_invalid_type)* |

## GET `/pets/{petId}`

### Equivalence partitioning

| ID | Parameter | Description | Outcome |
|----|-----------|-------------|---------|
| petId_valid_1 | `petId` | Typical valid positive integer within range | valid |
| petId_valid_2 | `petId` | Another typical valid positive integer | valid |
| petId_invalid_type_string | `petId` | Wrong type - string instead of integer | invalid |
| petId_invalid_type_float | `petId` | Wrong type - float instead of integer | invalid |
| petId_invalid_negative | `petId` | Negative integer (violates min=1 constraint) | invalid |

### Boundary value analysis

| ID | Parameter | Description | Values |
|----|-----------|-------------|--------|
| petId_boundary_1 | `petId` | Minimum allowed value (min=1) | 1 |
| petId_boundary_2 | `petId` | Just below minimum (min-1) | 0 |

### Sample test cases

| Test case | Scenario | Expected result |
|-----------|----------|-----------------|
| TC001 | GET `/pets/100` | HTTP 200 *(conditions: petId_valid_1)* |
| TC002 | GET `/pets/999` | HTTP 200 *(conditions: petId_valid_2)* |
| TC_BVA_001 | GET `/pets/1` | HTTP 200 *(conditions: petId_boundary_1)* |
| TC_BVA_002 | GET `/pets/0` | HTTP 400 *(conditions: petId_boundary_2)* |
| TC_NEG_001 | GET `/pets/abc` | HTTP 400 *(conditions: petId_invalid_type_string)* |
| TC_NEG_002 | GET `/pets/1.5` | HTTP 400 *(conditions: petId_invalid_type_float)* |
| TC_NEG_003 | GET `/pets/-5` | HTTP 400 *(conditions: petId_invalid_negative)* |

## DELETE `/pets/{petId}`

### Equivalence partitioning

| ID | Parameter | Description | Outcome |
|----|-----------|-------------|---------|
| petId_valid_1 | `petId` | Typical valid integer within the valid range | valid |
| petId_valid_2 | `petId` | Another typical valid integer within the valid range | valid |
| petId_invalid_type_1 | `petId` | Invalid type - string instead of integer | invalid |
| petId_invalid_type_2 | `petId` | Invalid type - float instead of integer | invalid |
| petId_invalid_1 | `petId` | Negative integer (out of range) | invalid |
| petId_invalid_2 | `petId` | Zero (out of range since min=1) | invalid |

### Boundary value analysis

| ID | Parameter | Description | Values |
|----|-----------|-------------|--------|
| petId_boundary_1 | `petId` | Minimum valid boundary value (min=1) | 1 |
| petId_boundary_2 | `petId` | Just below minimum boundary (min-1) | 0 |

### Sample test cases

| Test case | Scenario | Expected result |
|-----------|----------|-----------------|
| TC001 | DELETE `/pets/100` | HTTP 204 *(conditions: petId_valid_1)* |
| TC002 | DELETE `/pets/5000` | HTTP 204 *(conditions: petId_valid_2)* |
| TC_BVA_001 | DELETE `/pets/1` | HTTP 204 *(conditions: petId_boundary_1)* |
| TC_BVA_002 | DELETE `/pets/0` | HTTP 400 *(conditions: petId_boundary_2, petId_invalid_2)* |
| TC_NEG_001 | DELETE `/pets/abc` | HTTP 400 *(conditions: petId_invalid_type_1)* |
| TC_NEG_002 | DELETE `/pets/1.5` | HTTP 400 *(conditions: petId_invalid_type_2)* |
| TC_NEG_003 | DELETE `/pets/-10` | HTTP 400 *(conditions: petId_invalid_1)* |

## POST `/pets/{petId}/vaccinations`

### Equivalence partitioning

| ID | Parameter | Description | Outcome |
|----|-----------|-------------|---------|
| petid_valid_1 | `petId` | Typical valid pet ID within range | valid |
| petid_invalid_type_1 | `petId` | Non-integer value for pet ID | invalid |
| vaccine_name_valid_1 | `vaccine_name` | Typical valid vaccine name string | valid |
| vaccine_name_valid_2 | `vaccine_name` | Single character vaccine name | valid |
| vaccine_name_invalid_type_1 | `vaccine_name` | Non-string value for vaccine name | invalid |
| date_valid_1 | `date` | Valid date in YYYY-MM-DD format | valid |
| date_invalid_format_1 | `date` | Invalid date format (not YYYY-MM-DD) | invalid |
| date_invalid_format_2 | `date` | Invalid date (non-existent date) | invalid |
| date_invalid_type_1 | `date` | Non-string value for date | invalid |

### Boundary value analysis

| ID | Parameter | Description | Values |
|----|-----------|-------------|--------|
| petid_boundary_1 | `petId` | Minimum valid pet ID (min=1) | 1 |
| petid_boundary_2 | `petId` | Below minimum pet ID (min-1) | 0 |

### Sample test cases

| Test case | Scenario | Expected result |
|-----------|----------|-----------------|
| TC001 | POST `/pets/100/vaccinations` — body `{"vaccine_name": "Rabies Vaccine", "date": "2024-01-15"}` | HTTP 201 *(conditions: petid_valid_1, vaccine_name_valid_1, date_valid_1)* |
| TC002 | POST `/pets/1/vaccinations` — body `{"vaccine_name": "A", "date": "2024-01-15"}` | HTTP 201 *(conditions: petid_boundary_1, vaccine_name_valid_2, date_valid_1)* |
| TC_NEG_001 | POST `/pets/0/vaccinations` — body `{"vaccine_name": "Rabies Vaccine", "date": "2024-01-15"}` | HTTP 400 *(conditions: petid_boundary_2)* |
| TC_NEG_002 | POST `/pets/abc/vaccinations` — body `{"vaccine_name": "Rabies Vaccine", "date": "2024-01-15"}` | HTTP 400 *(conditions: petid_invalid_type_1)* |
| TC_NEG_003 | POST `/pets/100/vaccinations` — body `{"vaccine_name": 123, "date": "2024-01-15"}` | HTTP 400 *(conditions: vaccine_name_invalid_type_1)* |
| TC_NEG_004 | POST `/pets/100/vaccinations` — body `{"vaccine_name": "Rabies Vaccine", "date": "01/15/2024"}` | HTTP 400 *(conditions: date_invalid_format_1)* |
| TC_NEG_005 | POST `/pets/100/vaccinations` — body `{"vaccine_name": "Rabies Vaccine", "date": "2024-02-30"}` | HTTP 400 *(conditions: date_invalid_format_2)* |
| TC_NEG_006 | POST `/pets/100/vaccinations` — body `{"vaccine_name": "Rabies Vaccine", "date": 20240115}` | HTTP 400 *(conditions: date_invalid_type_1)* |
