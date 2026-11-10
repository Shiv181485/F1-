# Database schema

`datasets`: provider, dataset, season, event/session keys, provenance status, source URL, retrieval timestamp, JSON payload. Composite uniqueness is enforced over the natural dataset identity. NULL key components are normalized (`season=-1`, text keys empty) to avoid SQLite allowing duplicate NULL-containing unique keys.

`sync_logs`: provider, start/finish timestamps, status, record count and bounded diagnostic message.

Connections use a 30-second busy timeout, foreign-key enforcement and `BEGIN IMMEDIATE` for serialized upserts. SQLite is local-first; use managed PostgreSQL for durable cloud persistence (adapter not yet implemented).
