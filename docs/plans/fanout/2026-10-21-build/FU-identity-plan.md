
## Deviations

1. **`test_wp6_no_due_is_booked_window_start` query fixed (owned test file).** The test joined `actions.record_id` to `appointments.appointment_id`, but a BOOKED action's `record_id` is the **slot** id (`agent/tools/scheduling.py`; the appointment id is in `records`). The join landed on an unrelated seeded appointment (2026-10-20 16:00) instead of the booked slot (2026-10-19 08:00), so no correct implementation could pass. Changed the query to join `appointment_slots s ON s.slot_id = a.record_id`; assertion unchanged.
2. **Base moved** to main `ff6a130`; no conflicts with the plan.
3. **Journey record** is dated 2026-10-22 (the recorder named it 2026-10-21 from the wall clock; renamed). Fields corrected by hand as the plan asks.
4. **Gate result:** the full non-journey suite had 3 reds: `test_wf15_reset_script`, `test_no_journey_yet_prints_zero_and_exits_0` (known) and `test_export_never_blocks_hanging_exporter` (a `-n 2` timing flake; passes alone, 22/22 in its file).
