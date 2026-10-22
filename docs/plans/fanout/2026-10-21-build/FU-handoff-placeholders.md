
## Deviations

- `tests/graph/test_worked_pairs_api.py::_fee_bearing_checks` (WP-4 and its cancel leg) asserted
  `block["extra_lines"] == extra` (the stored lines), which encoded the defect. The plan's own AC-5 (reference line first,
  then the fee lines) makes that assertion wrong, so it now reads `[REFERENCE_LINE, *extra]`. One line, stronger assertion.
  The plan's step 4 list missed this file.
