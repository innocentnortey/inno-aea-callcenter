# API-shaped fakes

Drop point for fake HTTP response bodies that a backend test or journey needs (AEA-59).

- Name: `<operationId>.<status>.<name>.json`, the response body only, synthetic values.
- `tests/contract/test_openapi_fixtures.py::test_api_fixtures_match` validates every file here through
  `assert_response_matches`. A file naming an unknown operationId, or a status the operation does not document, fails.
- No secrets, verification codes, card-like numbers or full phone numbers.

The folder is empty today: AEA-11's doubles are model, clock, index and trace fakes, not API bodies.
