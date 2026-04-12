# AITestFlow — Test Design Report

*Generated: 2026-04-12T23:10:21*

## GET `/pets`

### Equivalence partitioning

| ID | Parameter | Description | Outcome |
|----|-----------|-------------|---------|
| limit_valid_1 | `limit` | Typical valid value within range | valid |
| limit_invalid_type_string | `limit` | Wrong type - string instead of integer | invalid |
| limit_invalid_negative | `limit` | Negative value outside valid range | invalid |
| status_valid_1 | `status` | Valid enum value - available | valid |
| status_valid_2 | `status` | Valid enum value - pending | valid |
| status_valid_3 | `status` | Valid enum value - sold | valid |
| status_invalid_enum | `status` | Invalid enum value not in allowed list | invalid |
| status_invalid_empty | `status` | Empty string value | invalid |
| status_invalid_type_number | `status` | Wrong type - number instead of string | invalid |

### Boundary value analysis

| ID | Parameter | Description | Values |
|----|-----------|-------------|--------|
| limit_boundary_1 | `limit` | Minimum valid boundary value | 1 |
| limit_boundary_2 | `limit` | Maximum valid boundary value | 100 |
| limit_boundary_3 | `limit` | Just below minimum boundary | 0 |
| limit_boundary_4 | `limit` | Just above maximum boundary | 101 |

### Sample test cases

| Test case | Scenario | Expected result |
|-----------|----------|-----------------|
| TC001 | GET `/pets` — query `{"limit": 50, "status": "available"}` | HTTP 200 *(conditions: limit_valid_1, status_valid_1)* |
| TC002 | GET `/pets` — query `{"limit": 1, "status": "pending"}` | HTTP 200 *(conditions: limit_boundary_1, status_valid_2)* |
| TC003 | GET `/pets` — query `{"limit": 100, "status": "sold"}` | HTTP 200 *(conditions: limit_boundary_2, status_valid_3)* |
| TC_BVA_001 | GET `/pets` — query `{"limit": 0}` | HTTP 400 *(conditions: limit_boundary_3)* |
| TC_BVA_002 | GET `/pets` — query `{"limit": 101}` | HTTP 400 *(conditions: limit_boundary_4)* |
| TC_NEG_001 | GET `/pets` — query `{"limit": "ten"}` | HTTP 400 *(conditions: limit_invalid_type_string)* |
| TC_NEG_002 | GET `/pets` — query `{"limit": -5}` | HTTP 400 *(conditions: limit_invalid_negative)* |
| TC_NEG_003 | GET `/pets` — query `{"status": "adopted"}` | HTTP 400 *(conditions: status_invalid_enum)* |
| TC_NEG_004 | GET `/pets` — query `{"status": ""}` | HTTP 400 *(conditions: status_invalid_empty)* |
| TC_NEG_005 | GET `/pets` — query `{"status": 123}` | HTTP 400 *(conditions: status_invalid_type_number)* |

## POST `/pets`

### Equivalence partitioning

| ID | Parameter | Description | Outcome |
|----|-----------|-------------|---------|
| name_valid_1 | `name` | Typical valid name within length constraints | valid |
| name_valid_2 | `name` | Minimum length name | valid |
| name_valid_3 | `name` | Maximum length name | valid |
| name_invalid_type | `name` | Wrong type for name field | invalid |
| name_invalid_empty | `name` | Empty string violates minLength constraint | invalid |
| status_valid_1 | `status` | Valid enum value 'available' | valid |
| status_valid_2 | `status` | Valid enum value 'pending' | valid |
| status_valid_3 | `status` | Valid enum value 'sold' | valid |
| status_invalid_enum | `status` | Invalid enum value not in allowed list | invalid |
| status_invalid_type | `status` | Wrong type for status field | invalid |
| category_valid_1 | `category` | Typical valid category string | valid |
| category_valid_2 | `category` | Empty string category (allowed since no constraints) | valid |
| category_invalid_type | `category` | Wrong type for category field | invalid |
| price_valid_1 | `price` | Typical valid price within range | valid |
| price_valid_2 | `price` | Minimum valid price | valid |
| price_valid_3 | `price` | Maximum valid price | valid |
| price_invalid_type | `price` | Wrong type for price field | invalid |
| price_invalid_range | `price` | Price below minimum | invalid |
| price_invalid_range_2 | `price` | Price above maximum | invalid |

### Boundary value analysis

| ID | Parameter | Description | Values |
|----|-----------|-------------|--------|
| name_boundary_1 | `name` | Below minimum length (empty string) | "" |
| name_boundary_2 | `name` | Above maximum length (51 characters) | "ThisIsExactlyFiftyOneCharactersLongNameForTestingPurposesX" |
| price_boundary_1 | `price` | Below minimum boundary | -1 |
| price_boundary_2 | `price` | Above maximum boundary | 10001 |

### Sample test cases

| Test case | Scenario | Expected result |
|-----------|----------|-----------------|
| TC001 | POST `/pets` — body `{"name": "Fluffy", "status": "available", "category": "Dog", "price": 99.99}` | HTTP 201 *(conditions: name_valid_1, status_valid_1, category_valid_1, price_valid_1)* |
| TC002 | POST `/pets` — body `{"name": "A", "status": "pending", "category": "", "price": 0}` | HTTP 201 *(conditions: name_valid_2, status_valid_2, category_valid_2, price_valid_2)* |
| TC003 | POST `/pets` — body `{"name": "ThisIsExactlyFiftyCharactersLongNameForTestingPurposes", "status": "sold", "category": "Dog", "price": 10000}` | HTTP 201 *(conditions: name_valid_3, status_valid_3, price_valid_3)* |
| TC_NEG_001 | POST `/pets` — body `{"name": 123, "status": "available", "category": "Dog", "price": 99.99}` | HTTP 400 *(conditions: name_invalid_type)* |
| TC_NEG_002 | POST `/pets` — body `{"name": "", "status": "available", "category": "Dog", "price": 99.99}` | HTTP 400 *(conditions: name_invalid_empty, name_boundary_1)* |
| TC_BVA_001 | POST `/pets` — body `{"name": "ThisIsExactlyFiftyOneCharactersLongNameForTestingPurposesX", "status": "available", "category": "Dog", "price": 99.99}` | HTTP 400 *(conditions: name_boundary_2)* |
| TC_NEG_003 | POST `/pets` — body `{"name": "Fluffy", "status": "adopted", "category": "Dog", "price": 99.99}` | HTTP 400 *(conditions: status_invalid_enum)* |
| TC_NEG_004 | POST `/pets` — body `{"name": "Fluffy", "status": true, "category": "Dog", "price": 99.99}` | HTTP 400 *(conditions: status_invalid_type)* |
| TC_NEG_005 | POST `/pets` — body `{"name": "Fluffy", "status": "available", "category": 42, "price": 99.99}` | HTTP 400 *(conditions: category_invalid_type)* |
| TC_NEG_006 | POST `/pets` — body `{"name": "Fluffy", "status": "available", "category": "Dog", "price": "expensive"}` | HTTP 400 *(conditions: price_invalid_type)* |
| TC_NEG_007 | POST `/pets` — body `{"name": "Fluffy", "status": "available", "category": "Dog", "price": -1}` | HTTP 400 *(conditions: price_invalid_range, price_boundary_1)* |
| TC_BVA_002 | POST `/pets` — body `{"name": "Fluffy", "status": "available", "category": "Dog", "price": 10001}` | HTTP 400 *(conditions: price_invalid_range_2, price_boundary_2)* |

## GET `/pets/{petId}`

### Equivalence partitioning

| ID | Parameter | Description | Outcome |
|----|-----------|-------------|---------|
| petId_valid_1 | `petId` | Typical valid positive integer within range | valid |
| petId_valid_2 | `petId` | Large positive integer within valid range | valid |
| petId_invalid_type_1 | `petId` | Invalid type - string instead of integer | invalid |
| petId_invalid_type_2 | `petId` | Invalid type - float instead of integer | invalid |
| petId_invalid_1 | `petId` | Negative integer (out of range) | invalid |
| petId_invalid_2 | `petId` | Zero (out of range, boundary-1) | invalid |

### Boundary value analysis

| ID | Parameter | Description | Values |
|----|-----------|-------------|--------|
| petId_boundary_1 | `petId` | Minimum valid boundary value (min=1) | 1 |
| petId_boundary_2 | `petId` | Just below minimum boundary (min-1) | 0 |

### Sample test cases

| Test case | Scenario | Expected result |
|-----------|----------|-----------------|
| TC001 | GET `/pets/5` | HTTP 200 *(conditions: petId_valid_1)* |
| TC002 | GET `/pets/999999` | HTTP 200 *(conditions: petId_valid_2)* |
| TC_BVA_001 | GET `/pets/1` | HTTP 200 *(conditions: petId_boundary_1)* |
| TC_BVA_002 | GET `/pets/0` | HTTP 400 *(conditions: petId_boundary_2, petId_invalid_2)* |
| TC_NEG_001 | GET `/pets/abc` | HTTP 400 *(conditions: petId_invalid_type_1)* |
| TC_NEG_002 | GET `/pets/3.14` | HTTP 400 *(conditions: petId_invalid_type_2)* |
| TC_NEG_003 | GET `/pets/-5` | HTTP 400 *(conditions: petId_invalid_1)* |

## DELETE `/pets/{petId}`

### Equivalence partitioning

| ID | Parameter | Description | Outcome |
|----|-----------|-------------|---------|
| petId_valid_1 | `petId` | Typical valid pet ID within the valid range | valid |
| petId_valid_2 | `petId` | Another typical valid pet ID within the valid range | valid |
| petId_invalid_type_string | `petId` | Wrong type - string instead of integer | invalid |
| petId_invalid_type_float | `petId` | Wrong type - float instead of integer | invalid |
| petId_invalid_negative | `petId` | Negative integer value (out of range) | invalid |
| petId_invalid_null | `petId` | Explicit null value for required parameter | invalid |

### Boundary value analysis

| ID | Parameter | Description | Values |
|----|-----------|-------------|--------|
| petId_boundary_1 | `petId` | Minimum valid boundary value (min=1) | 1 |
| petId_boundary_2 | `petId` | Just below minimum boundary (min-1) | 0 |

### Sample test cases

| Test case | Scenario | Expected result |
|-----------|----------|-----------------|
| TC001 | DELETE `/pets/100` | HTTP 204 *(conditions: petId_valid_1)* |
| TC002 | DELETE `/pets/999` | HTTP 204 *(conditions: petId_valid_2)* |
| TC_BVA_001 | DELETE `/pets/1` | HTTP 204 *(conditions: petId_boundary_1)* |
| TC_NEG_001 | DELETE `/pets/0` | HTTP 400 *(conditions: petId_boundary_2)* |
| TC_NEG_002 | DELETE `/pets/abc` | HTTP 400 *(conditions: petId_invalid_type_string)* |
| TC_NEG_003 | DELETE `/pets/1.5` | HTTP 400 *(conditions: petId_invalid_type_float)* |
| TC_NEG_004 | DELETE `/pets/-5` | HTTP 400 *(conditions: petId_invalid_negative)* |
| TC_NEG_005 | DELETE `/pets/null` | HTTP 400 *(conditions: petId_invalid_null)* |

## POST `/pets/{petId}/vaccinations`

### Equivalence partitioning

| ID | Parameter | Description | Outcome |
|----|-----------|-------------|---------|
| petid_valid_1 | `petId` | Typical valid pet ID within range | valid |
| petid_invalid_type | `petId` | Invalid type for pet ID (string instead of integer) | invalid |
| petid_invalid_1 | `petId` | Pet ID below minimum constraint | invalid |
| vaccine_name_valid_1 | `vaccine_name` | Typical valid vaccine name | valid |
| vaccine_name_valid_2 | `vaccine_name` | Another valid vaccine name | valid |
| vaccine_name_invalid_type | `vaccine_name` | Invalid type for vaccine name (number instead of string) | invalid |
| vaccine_name_invalid_1 | `vaccine_name` | Empty string for vaccine name | invalid |
| date_valid_1 | `date` | Valid date in YYYY-MM-DD format | valid |
| date_valid_2 | `date` | Another valid date | valid |
| date_invalid_type | `date` | Invalid type for date (number instead of string) | invalid |
| date_invalid_1 | `date` | Invalid date format (not YYYY-MM-DD) | invalid |
| date_invalid_2 | `date` | Invalid date (non-existent date) | invalid |
| date_invalid_3 | `date` | Empty string for date | invalid |

### Boundary value analysis

| ID | Parameter | Description | Values |
|----|-----------|-------------|--------|
| petid_boundary_1 | `petId` | Minimum valid pet ID (min=1) | 1 |
| petid_boundary_2 | `petId` | Just below minimum pet ID (min-1) | 0 |

### Sample test cases

| Test case | Scenario | Expected result |
|-----------|----------|-----------------|
| TC001 | POST `/pets/100/vaccinations` — body `{"vaccine_name": "Rabies Vaccine", "date": "2024-01-15"}` | HTTP 201 *(conditions: petid_valid_1, vaccine_name_valid_1, date_valid_1)* |
| TC002 | POST `/pets/1/vaccinations` — body `{"vaccine_name": "Distemper", "date": "2023-12-31"}` | HTTP 201 *(conditions: petid_boundary_1, vaccine_name_valid_2, date_valid_2)* |
| TC_NEG_001 | POST `/pets/abc/vaccinations` — body `{"vaccine_name": "Rabies Vaccine", "date": "2024-01-15"}` | HTTP 400 *(conditions: petid_invalid_type)* |
| TC_NEG_002 | POST `/pets/0/vaccinations` — body `{"vaccine_name": "Rabies Vaccine", "date": "2024-01-15"}` | HTTP 400 *(conditions: petid_invalid_1, petid_boundary_2)* |
| TC_NEG_003 | POST `/pets/100/vaccinations` — body `{"vaccine_name": 123, "date": "2024-01-15"}` | HTTP 400 *(conditions: vaccine_name_invalid_type)* |
| TC_NEG_004 | POST `/pets/100/vaccinations` — body `{"vaccine_name": "", "date": "2024-01-15"}` | HTTP 400 *(conditions: vaccine_name_invalid_1)* |
| TC_NEG_005 | POST `/pets/100/vaccinations` — body `{"vaccine_name": "Rabies Vaccine", "date": 20240115}` | HTTP 400 *(conditions: date_invalid_type)* |
| TC_NEG_006 | POST `/pets/100/vaccinations` — body `{"vaccine_name": "Rabies Vaccine", "date": "15-01-2024"}` | HTTP 400 *(conditions: date_invalid_1)* |
| TC_NEG_007 | POST `/pets/100/vaccinations` — body `{"vaccine_name": "Rabies Vaccine", "date": "2024-02-30"}` | HTTP 400 *(conditions: date_invalid_2)* |
| TC_NEG_008 | POST `/pets/100/vaccinations` — body `{"vaccine_name": "Rabies Vaccine", "date": ""}` | HTTP 400 *(conditions: date_invalid_3)* |
