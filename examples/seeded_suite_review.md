# Test Design Review: SauceDemo

**Verdict: ⛔ MAJOR REWORK**: Do not use these test cases yet: fix the major findings below and review again.

18 test cases for 13 requirements. This is a static review of the test design; no tests were executed against the application.

## Review checks

| Check | Value | Threshold | Severity | Result |
|---|---|---|---|---|
| Requirements covered by at least one test | 92% | ≥ 100% | major | ⛔ major finding |
| Tests that reference only existing requirements | 94% | ≥ 100% | major | ⛔ major finding |
| High-priority requirements with a negative/boundary test | 62% | ≥ 100% | major | ⛔ major finding |
| Tests whose steps all have an action and an expected result | 100% | ≥ 95% | major | ✅ ok |
| Share of negative and boundary tests | 39% | ≥ 25% | minor | ✅ ok |
| Share of tests that are near-duplicates | 11% | ≤ 5% | minor | 🛠️ minor finding |

## Findings

- **major** (requirement_coverage): REQ-NAV-01 has no test case
- **major** (traceability): TC-016 references unknown requirement(s): REQ-CART-99
- **major** (high_priority_negative_coverage): REQ-INV-01 (high priority) has no negative or boundary test
- **major** (high_priority_negative_coverage): REQ-CHK-02 (high priority) has no negative or boundary test
- **major** (high_priority_negative_coverage): REQ-CHK-03 (high priority) has no negative or boundary test
- **minor** (duplicate_rate): TC-001 and TC-002 are 93% similar

## Traceability matrix

| Requirement | Priority | Test cases |
|---|---|---|
| REQ-LOGIN-01: Successful login | high | TC-001, TC-002, TC-003 |
| REQ-LOGIN-02: Invalid credentials are rejected | high | TC-003, TC-004 |
| REQ-LOGIN-03: Locked-out user cannot log in | high | TC-005 |
| REQ-LOGIN-04: Required login fields | medium | TC-006, TC-007 |
| REQ-INV-01: Product list | high | TC-008 |
| REQ-INV-02: Product sorting | medium | TC-009, TC-010 |
| REQ-CART-01: Add to cart | high | TC-011, TC-012 |
| REQ-CART-02: Remove from cart | medium | TC-013 |
| REQ-CART-03: Cart page | medium | TC-014 |
| REQ-CHK-01: Checkout information is required | high | TC-015, TC-018 |
| REQ-CHK-02: Order overview totals | high | TC-016 |
| REQ-CHK-03: Order completion | high | TC-017 |
| REQ-NAV-01: Logout and protected pages | medium | **none** |

## Test cases

| ID | Title | Requirements | Type | Priority | Steps |
|---|---|---|---|---|---|
| TC-001 | Login with valid credentials | REQ-LOGIN-01 | positive | high | 2 |
| TC-002 | Login with valid credentials as standard user | REQ-LOGIN-01 | positive | high | 2 |
| TC-003 | Login with a wrong password is rejected | REQ-LOGIN-01, REQ-LOGIN-02 | negative | high | 1 |
| TC-004 | Login with an unknown username is rejected | REQ-LOGIN-02 | negative | high | 1 |
| TC-005 | Locked-out user cannot log in | REQ-LOGIN-03 | negative | high | 1 |
| TC-006 | Empty username shows a required-field error | REQ-LOGIN-04 | boundary | medium | 1 |
| TC-007 | Empty password shows a required-field error | REQ-LOGIN-04 | boundary | medium | 1 |
| TC-008 | Products page lists six products with full details | REQ-INV-01 | positive | high | 2 |
| TC-009 | Sort products by name Z to A | REQ-INV-02 | positive | medium | 2 |
| TC-010 | Sort products by price in both directions | REQ-INV-02 | positive | medium | 2 |
| TC-011 | Adding a product updates the cart badge and button | REQ-CART-01 | positive | high | 1 |
| TC-012 | Adding all six products shows 6 on the badge | REQ-CART-01 | boundary | high | 1 |
| TC-013 | Removing a product from the Products page | REQ-CART-02 | positive | medium | 1 |
| TC-014 | Cart page lists added products | REQ-CART-03 | positive | medium | 2 |
| TC-015 | Checkout information fields are required | REQ-CHK-01 | negative | high | 3 |
| TC-016 | Order overview total equals item total plus tax | REQ-CHK-02, REQ-CART-99 | positive | high | 3 |
| TC-017 | Finishing an order empties the cart | REQ-CHK-03 | positive | high | 2 |
| TC-018 | Complete checkout information continues to the overview | REQ-CHK-01 | positive | high | 1 |
