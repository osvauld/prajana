"""store.py — Thin proxy to upakarana2.store.tests.

All test result persistence goes through the centralized LMDB store.
This module re-exports the tests API so conftest.py can import from
upakarana2.testing.store without changing its import path.
"""

from upakarana2.store import tests as _t

begin_run = _t.begin_run
record_result = _t.record_result
finalize_run = _t.finalize_run
last_run_id = _t.last_run_id
query_by_outcome = _t.query_by_outcome
query_by_gate = _t.query_by_gate
get_trace = _t.get_trace
get_result = _t.get_result
get_run_summary = _t.get_run_summary
load_run_entries = _t.load_run_entries
load_run_entries_with_traces = _t.load_run_entries_with_traces
history = _t.history
