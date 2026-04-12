# AITestFlow — Test Design Report

*Generated: 2026-04-12T21:51:03*

## GET `/pets`

### Equivalence partitioning

| ID | Parameter | Description | Outcome |
|----|-----------|-------------|---------|
| limit_valid_1 | `limit` | Typical valid value within range | valid |
| limit_valid_2 | `limit` | Minimum valid value | valid |
| limit_valid_3 | `limit` | Maximum valid value | valid |
| limit_invalid_type_string | `limit` | Wrong type - string instead of integer | invalid |
| limit_invalid_type_float | `limit` | Wrong type - float instead of integer | invalid |
| limit_invalid_negative | `limit` | Negative value below minimum | invalid |
| limit_invalid_zero | `limit` | Zero value below minimum | invalid |
| limit_invalid_above_max | `limit` | Value above maximum | invalid |
| status_valid_available | `status` | Valid enum value: available | valid |
| status_valid_pending | `status` | Valid enum value: pending | valid |
| status_valid_sold | `status` | Valid enum value: sold | valid |
| status_invalid_enum | `status` | Invalid enum value not in allowed list | invalid |
| status_invalid_type_number | `status` | Wrong type - number instead of string | invalid |
| status_invalid_empty | `status` | Empty string value | invalid |
| limit_declared_500 | `limit` | Documents the OpenAPI 500 response for contract completeness (implementation-dependent) | valid |

### Boundary value analysis

| ID | Parameter | Description | Values |
|----|-----------|-------------|--------|
| limit_boundary_1 | `limit` | Boundary: min-1 | 0 |
| limit_boundary_2 | `limit` | Boundary: min | 1 |
| limit_boundary_3 | `limit` | Boundary: max | 100 |
| limit_boundary_4 | `limit` | Boundary: max+1 | 101 |

### Sample test cases

| Test case | Scenario | Expected result |
|-----------|----------|-----------------|
| TC001 | GET `/pets` | HTTP 200 |
| TC002 | GET `/pets` — query `{"limit": 50, "status": "available"}` | HTTP 200 *(conditions: limit_valid_1, status_valid_available)* |
| TC003 | GET `/pets` — query `{"limit": 1, "status": "pending"}` | HTTP 200 *(conditions: limit_valid_2, limit_boundary_2, status_valid_pending)* |
| TC004 | GET `/pets` — query `{"limit": 100, "status": "sold"}` | HTTP 200 *(conditions: limit_valid_3, limit_boundary_3, status_valid_sold)* |
| TC_NEG_001 | GET `/pets` — query `{"limit": "ten"}` | HTTP 400 *(conditions: limit_invalid_type_string)* |
| TC_NEG_002 | GET `/pets` — query `{"limit": 10.5}` | HTTP 400 *(conditions: limit_invalid_type_float)* |
| TC_NEG_003 | GET `/pets` — query `{"limit": -5}` | HTTP 400 *(conditions: limit_invalid_negative)* |
| TC_NEG_004 | GET `/pets` — query `{"limit": 0}` | HTTP 400 *(conditions: limit_invalid_zero, limit_boundary_1)* |
| TC_NEG_005 | GET `/pets` — query `{"limit": 101}` | HTTP 400 *(conditions: limit_invalid_above_max, limit_boundary_4)* |
| TC_NEG_006 | GET `/pets` — query `{"status": "adopted"}` | HTTP 400 *(conditions: status_invalid_enum)* |
| TC_NEG_007 | GET `/pets` — query `{"status": 123}` | HTTP 400 *(conditions: status_invalid_type_number)* |
| TC_NEG_008 | GET `/pets` — query `{"status": ""}` | HTTP 400 *(conditions: status_invalid_empty)* |
| TC_500_001 | GET `/pets` — query `{"limit": 10}` | HTTP 500 *(conditions: limit_declared_500)* |

## POST `/pets`

### Equivalence partitioning

| ID | Parameter | Description | Outcome |
|----|-----------|-------------|---------|
| name_valid_1 | `name` | Valid name with minimum length | valid |
| name_valid_2 | `name` | Valid name with typical length | valid |
| name_valid_3 | `name` | Valid name with maximum length | valid |
| name_invalid_empty | `name` | Empty string violates minLength constraint | invalid |
| name_invalid_too_long | `name` | String exceeds maxLength of 50 characters | invalid |
| name_invalid_type | `name` | Wrong data type for name field | invalid |
| status_valid_available | `status` | Valid enum value 'available' | valid |
| status_valid_pending | `status` | Valid enum value 'pending' | valid |
| status_valid_sold | `status` | Valid enum value 'sold' | valid |
| status_invalid_enum | `status` | Invalid enum value not in allowed list | invalid |
| status_invalid_type | `status` | Wrong data type for status field | invalid |
| category_valid_1 | `category` | Valid string category | valid |
| category_valid_2 | `category` | Valid string category with spaces | valid |
| category_invalid_type | `category` | Wrong data type for category field | invalid |
| price_valid_mid | `price` | Typical valid price value | valid |
| price_invalid_type | `price` | Wrong data type for price field | invalid |
| name_declared_500 | `name` | Valid name to document OpenAPI 500 response for contract completeness (implementation-dependent) | valid |

### Boundary value analysis

| ID | Parameter | Description | Values |
|----|-----------|-------------|--------|
| price_valid_min | `price` | Minimum valid price value | 0 |
| price_valid_max | `price` | Maximum valid price value | 10000 |
| price_boundary_below_min | `price` | Price just below minimum (negative value) | -1 |
| price_boundary_above_max | `price` | Price just above maximum | 10001 |

### Sample test cases

| Test case | Scenario | Expected result |
|-----------|----------|-----------------|
| TC001 | POST `/pets` — body `{"name": "a", "status": "available", "category": "Dog", "price": 500}` | HTTP 201 *(conditions: name_valid_1, status_valid_available, category_valid_1, price_valid_mid)* |
| TC002 | POST `/pets` — body `{"name": "Fluffy", "status": "pending", "category": "Golden Retriever", "price": 0}` | HTTP 201 *(conditions: name_valid_2, status_valid_pending, category_valid_2, price_valid_min)* |
| TC003 | POST `/pets` — body `{"name": "ThisIsAVeryLongPetNameThatExactlyFiftyCharactersLong", "status": "sold", "category": "Dog", "price": 10000}` | HTTP 201 *(conditions: name_valid_3, status_valid_sold, price_valid_max)* |
| TC_NEG_001 | POST `/pets` — body `{"name": "", "status": "available", "category": "Dog", "price": 500}` | HTTP 400 *(conditions: name_invalid_empty)* |
| TC_NEG_002 | POST `/pets` — body `{"name": "ThisPetNameIsWayTooLongAndExceedsTheMaximumAllowedLengthOfFiftyCharacters", "status": "available", "category": "Dog", "price": 500}` | HTTP 400 *(conditions: name_invalid_too_long)* |
| TC_NEG_003 | POST `/pets` — body `{"name": 123, "status": "available", "category": "Dog", "price": 500}` | HTTP 400 *(conditions: name_invalid_type)* |
| TC_NEG_004 | POST `/pets` — body `{"name": "Fluffy", "status": "adopted", "category": "Dog", "price": 500}` | HTTP 400 *(conditions: status_invalid_enum)* |
| TC_NEG_005 | POST `/pets` — body `{"name": "Fluffy", "status": true, "category": "Dog", "price": 500}` | HTTP 400 *(conditions: status_invalid_type)* |
| TC_NEG_006 | POST `/pets` — body `{"name": "Fluffy", "status": "available", "category": 42, "price": 500}` | HTTP 400 *(conditions: category_invalid_type)* |
| TC_BVA_001 | POST `/pets` — body `{"name": "Fluffy", "status": "available", "category": "Dog", "price": -1}` | HTTP 400 *(conditions: price_boundary_below_min)* |
| TC_BVA_002 | POST `/pets` — body `{"name": "Fluffy", "status": "available", "category": "Dog", "price": 10001}` | HTTP 400 *(conditions: price_boundary_above_max)* |
| TC_NEG_007 | POST `/pets` — body `{"name": "Fluffy", "status": "available", "category": "Dog", "price": "expensive"}` | HTTP 400 *(conditions: price_invalid_type)* |
| TC_ERR_001 | POST `/pets` — body `{"name": "TestPet", "status": "available", "category": "Dog", "price": 500}` | HTTP 500 *(conditions: name_declared_500)* |

## GET `/pets/{petId}`

### Equivalence partitioning

| ID | Parameter | Description | Outcome |
|----|-----------|-------------|---------|
| petId_valid_1 | `petId` | Typical valid pet ID within the valid range | valid |
| petId_valid_2 | `petId` | Another typical valid pet ID | valid |
| petId_invalid_type_string | `petId` | Wrong type - string instead of integer | invalid |
| petId_invalid_type_float | `petId` | Wrong type - float instead of integer | invalid |
| petId_invalid_negative | `petId` | Negative integer value (out of range) | invalid |
| petId_not_found_404 | `petId` | Syntactically valid pet ID for non-existent resource to test 404 response | valid |
| petId_declared_500 | `petId` | Normal valid pet ID to document OpenAPI 500 response for contract completeness | valid |

### Boundary value analysis

| ID | Parameter | Description | Values |
|----|-----------|-------------|--------|
| petId_boundary_1 | `petId` | Minimum valid boundary value (min=1) | 1 |
| petId_boundary_2 | `petId` | Just below minimum boundary (min-1) | 0 |

### Sample test cases

| Test case | Scenario | Expected result |
|-----------|----------|-----------------|
| TC001 | GET `/pets/100` | HTTP 200 *(conditions: petId_valid_1, petId_valid_2)* |
| TC_BVA_001 | GET `/pets/1` | HTTP 200 *(conditions: petId_boundary_1)* |
| TC_NEG_001 | GET `/pets/0` | HTTP 400 *(conditions: petId_boundary_2)* |
| TC_NEG_002 | GET `/pets/abc` | HTTP 400 *(conditions: petId_invalid_type_string)* |
| TC_NEG_003 | GET `/pets/3.14` | HTTP 400 *(conditions: petId_invalid_type_float)* |
| TC_NEG_004 | GET `/pets/-10` | HTTP 400 *(conditions: petId_invalid_negative)* |
| TC_404 | GET `/pets/999999999` | HTTP 404 *(conditions: petId_not_found_404)* |
| TC_500 | GET `/pets/42` | HTTP 500 *(conditions: petId_declared_500)* |

## DELETE `/pets/{petId}`

### Equivalence partitioning

| ID | Parameter | Description | Outcome |
|----|-----------|-------------|---------|
| petId_valid_1 | `petId` | Typical valid positive integer within range | valid |
| petId_valid_2 | `petId` | Another typical valid positive integer | valid |
| petId_invalid_type_1 | `petId` | Negative integer (out of range) | invalid |
| petId_invalid_type_2 | `petId` | Zero (out of range) | invalid |
| petId_invalid_type_3 | `petId` | Non-integer numeric (float) | invalid |
| petId_invalid_type_4 | `petId` | String instead of integer | invalid |

### Boundary value analysis

| ID | Parameter | Description | Values |
|----|-----------|-------------|--------|
| petId_boundary_1 | `petId` | Minimum allowed value (min=1) | 1 |
| petId_boundary_2 | `petId` | Just below minimum (min-1) | 0 |

### Sample test cases

| Test case | Scenario | Expected result |
|-----------|----------|-----------------|
| TC001 | DELETE `/pets/100` | HTTP 204 *(conditions: petId_valid_1)* |
| TC002 | DELETE `/pets/999` | HTTP 204 *(conditions: petId_valid_2)* |
| TC_BVA_001 | DELETE `/pets/1` | HTTP 204 *(conditions: petId_boundary_1)* |
| TC_BVA_002 | DELETE `/pets/0` | HTTP 400 *(conditions: petId_boundary_2, petId_invalid_type_2)* |
| TC_NEG_001 | DELETE `/pets/-5` | HTTP 400 *(conditions: petId_invalid_type_1)* |
| TC_NEG_002 | DELETE `/pets/3.14` | HTTP 400 *(conditions: petId_invalid_type_3)* |
| TC_NEG_003 | DELETE `/pets/abc` | HTTP 400 *(conditions: petId_invalid_type_4)* |

## POST `/pets/{petId}/vaccinations`

### Equivalence partitioning

| ID | Parameter | Description | Outcome |
|----|-----------|-------------|---------|
| petid_valid_1 | `petId` | Typical valid pet ID within range | valid |
| petid_invalid_type | `petId` | Pet ID with wrong data type (string instead of integer) | invalid |
| petid_invalid_1 | `petId` | Pet ID below minimum constraint | invalid |
| vaccine_name_valid_1 | `vaccine_name` | Typical valid vaccine name | valid |
| vaccine_name_valid_2 | `vaccine_name` | Valid vaccine name with special characters | valid |
| vaccine_name_invalid_type | `vaccine_name` | Vaccine name with wrong data type (number instead of string) | invalid |
| vaccine_name_invalid_1 | `vaccine_name` | Vaccine name with null value (field not marked as nullable) | invalid |
| date_valid_1 | `date` | Typical valid date in YYYY-MM-DD format | valid |
| date_valid_2 | `date` | Valid date with leap year | valid |
| date_invalid_type | `date` | Date with wrong data type (number instead of string) | invalid |
| date_invalid_1 | `date` | Invalid date format (not YYYY-MM-DD) | invalid |
| date_invalid_2 | `date` | Invalid date (non-existent date) | invalid |
| date_invalid_3 | `date` | Date with null value (field not marked as nullable) | invalid |

### Boundary value analysis

| ID | Parameter | Description | Values |
|----|-----------|-------------|--------|
| petid_boundary_1 | `petId` | Minimum valid pet ID (min=1) | 1 |

### Sample test cases

| Test case | Scenario | Expected result |
|-----------|----------|-----------------|
| TC001 | POST `/pets/100/vaccinations` — body `{"vaccine_name": "Rabies Vaccine", "date": "2024-03-15"}` | HTTP 201 *(conditions: petid_valid_1, vaccine_name_valid_1, date_valid_1)* |
| TC002 | POST `/pets/1/vaccinations` — body `{"vaccine_name": "DHPPi-L (4-in-1)", "date": "2024-02-29"}` | HTTP 201 *(conditions: petid_boundary_1, vaccine_name_valid_2, date_valid_2)* |
| TC_NEG_001 | POST `/pets/abc/vaccinations` — body `{"vaccine_name": "Rabies Vaccine", "date": "2024-03-15"}` | HTTP 400 *(conditions: petid_invalid_type)* |
| TC_NEG_002 | POST `/pets/0/vaccinations` — body `{"vaccine_name": "Rabies Vaccine", "date": "2024-03-15"}` | HTTP 400 *(conditions: petid_invalid_1)* |
| TC_NEG_003 | POST `/pets/100/vaccinations` — body `{"vaccine_name": 123, "date": "2024-03-15"}` | HTTP 400 *(conditions: vaccine_name_invalid_type)* |
| TC_NEG_004 | POST `/pets/100/vaccinations` — body `{"vaccine_name": null, "date": "2024-03-15"}` | HTTP 400 *(conditions: vaccine_name_invalid_1)* |
| TC_NEG_005 | POST `/pets/100/vaccinations` — body `{"vaccine_name": "Rabies Vaccine", "date": 20240315}` | HTTP 400 *(conditions: date_invalid_type)* |
| TC_NEG_006 | POST `/pets/100/vaccinations` — body `{"vaccine_name": "Rabies Vaccine", "date": "15/03/2024"}` | HTTP 400 *(conditions: date_invalid_1)* |
| TC_NEG_007 | POST `/pets/100/vaccinations` — body `{"vaccine_name": "Rabies Vaccine", "date": "2024-13-45"}` | HTTP 400 *(conditions: date_invalid_2)* |
| TC_NEG_008 | POST `/pets/100/vaccinations` — body `{"vaccine_name": "Rabies Vaccine", "date": null}` | HTTP 400 *(conditions: date_invalid_3)* |
