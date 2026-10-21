-- AEA-10: no new booking column (cases.md 4.1 lists none); indexes for the queries scheduling and reads run.
CREATE INDEX IF NOT EXISTS ix_slots_search ON appointment_slots (zone, service_type, status, slot_date);
CREATE INDEX IF NOT EXISTS ix_appointments_customer ON appointments (customer_id);
CREATE INDEX IF NOT EXISTS ix_invoices_customer ON invoices (customer_id);
