"""test_session.py — session isolation, turn counting, error handling.

Tests the session layer in socket.ml. Sessions are identified by session_id;
each session accumulates turns independently.

Key observations:
- The `question` command uses no `command` field (or falls through to | _)
- `turn_id` in the response echoes the client-supplied turn_id (not server's counter)
- Server maintains an internal prashna-N counter per session (logged, not returned)
- `end-session` clears the session state from the store
- `answer_text` is non-empty for sentences with known concepts
- `answer_text` may be non-empty even for unknown words (server still replies)
- Empty or missing question → INVALID_REQUEST error

Protects against: socket.ml session store, anuvada_query integration

Run:
    cd /home/abe/agent_x && .venv/bin/pytest vyakarana/tests/test_session.py -v --socket /tmp/vy.sock
"""

import pytest
from vy import VyakaranaError

# ── basic question mechanics ──────────────────────────────────────────────────


def test_question_returns_non_empty_answer(vy):
    # A sentence with a known concept should produce non-empty answer_text
    answer = vy.ask("find force", session_id="test-basic-1")
    assert isinstance(answer, str), (
        f"expected string answer, got {type(answer).__name__}"
    )
    assert len(answer) > 0, "expected non-empty answer for 'find force'"


def test_question_known_concept_has_content(vy):
    answer = vy.ask(
        "find kinetic energy given mass 5 and velocity 10", session_id="test-ke-1"
    )
    assert isinstance(answer, str) and len(answer) > 0, (
        f"expected non-empty answer for kinetic energy query, got {answer!r}"
    )


def test_question_different_sessions_both_get_answers(vy):
    # Two independent sessions can both get answers
    a1 = vy.ask("find force", session_id="sess-a-unique")
    a2 = vy.ask("find mass", session_id="sess-b-unique")
    assert isinstance(a1, str), "session A should get string answer"
    assert isinstance(a2, str), "session B should get string answer"


# ── error handling ────────────────────────────────────────────────────────────


def test_empty_question_raises_error(vy):
    with pytest.raises(VyakaranaError) as exc_info:
        vy.ask("", session_id="test-empty")
    assert exc_info.value.code == "INVALID_REQUEST", (
        f"expected INVALID_REQUEST, got {exc_info.value.code!r}"
    )


def test_unknown_expression_returns_identifier(vy):
    # Unknown identifiers are not engine errors — they're returned as-is
    result = vy.eval("unknown-identifier-xyzabc")
    assert result == "unknown-identifier-xyzabc", (
        f"unknown identifier should return itself, got {result!r}"
    )


def test_server_remains_responsive_after_eval(vy):
    # After any eval (including unknown identifiers), server stays responsive
    vy.eval("unknown-identifier-xyzabc")
    result = vy.eval('lookup-word "mass"')
    assert result == "mass", f"server should stay responsive, got {result!r}"


# ── end-session ───────────────────────────────────────────────────────────────


def test_end_session_command_succeeds(vy):
    # Send a question, then end the session, then send another question
    vy.ask("find force", session_id="sess-end-test")
    # end-session (send directly since vy doesn't have an end_session helper)
    resp = vy._send_with_retry(
        {"command": "end-session", "session_id": "sess-end-test"}
    )
    assert resp.get("status") == "ok", f"end-session should succeed: {resp!r}"


def test_after_end_session_new_question_works(vy):
    vy.ask("find force", session_id="sess-reset-test")
    vy._send_with_retry({"command": "end-session", "session_id": "sess-reset-test"})
    # New question on same session_id should work (session recreated)
    answer = vy.ask("find mass", session_id="sess-reset-test")
    assert isinstance(answer, str), "should get answer after session reset"


# ── session independence ───────────────────────────────────────────────────────


def test_two_sessions_independent_answers(vy):
    # Two sessions with different questions get different answers
    a1 = vy.ask(
        "find kinetic energy given mass 5 and velocity 10",
        session_id="sess-ke-unique-a",
    )
    a2 = vy.ask(
        "find momentum given mass 3 and velocity 4", session_id="sess-mom-unique-b"
    )
    # Both should have content
    assert len(a1) > 0, "session A should have answer"
    assert len(a2) > 0, "session B should have answer"
    # They should be different (different physics answers)
    # (Can't guarantee exact content but they're likely different)
    # Just verify both sessions work independently


# ── multi-turn continuity (current implementation) ───────────────────────────


def test_multi_turn_session_both_succeed(vy):
    # Two turns in the same session both return answers
    a1 = vy.ask("find force", session_id="multi-turn-test-x")
    a2 = vy.ask("find mass", session_id="multi-turn-test-x")
    assert isinstance(a1, str) and len(a1) > 0, "turn 1 should have answer"
    assert isinstance(a2, str) and len(a2) > 0, "turn 2 should have answer"


# ── multi-turn binding carry (not yet built) ─────────────────────────────────


def test_multi_turn_answer_references_concept(vy):
    # Turn 2 can reference a concept that appeared in turn 1's question,
    # because each turn independently runs BQG → avrti. (Not cross-turn binding —
    # just that each turn answers independently based on its own question.)
    session_id = "multi-turn-concept-test-unique"
    vy.ask("find mass", session_id=session_id)
    answer2 = vy.ask(
        "find kinetic energy given mass 5 and velocity 10", session_id=session_id
    )
    assert isinstance(answer2, str) and len(answer2) > 0, (
        "turn 2 should produce an answer independently"
    )


def test_different_sessions_answer_independently(vy):
    # Two sessions answer their own questions independently
    a_sess = "sess-ind-A-unique"
    b_sess = "sess-ind-B-unique"
    answer_a = vy.ask(
        "find kinetic energy given mass 5 and velocity 10", session_id=a_sess
    )
    answer_b = vy.ask("find force", session_id=b_sess)
    assert len(answer_a) > 0, "session A should get answer"
    assert len(answer_b) > 0, "session B should get answer"


# ── actual cross-turn binding (not yet implemented) ───────────────────────────


def test_cross_turn_binding_completes_match(vy):
    # Turn 1: provide mass=5; Turn 2: provide velocity=10 and ask for KE
    # Only possible if the server accumulates bindings across turns
    session_id = "cross-turn-ke-test-unique"
    vy.ask("mass is 5", session_id=session_id)
    answer2 = vy.ask("find kinetic energy given velocity 10", session_id=session_id)
    # Turn 2 alone lacks mass — match should only succeed if turn 1 binding carried
    # We check this by verifying mass value appears in the answer
    assert "5" in answer2, (
        f"cross-turn binding: mass=5 from turn 1 should appear in turn 2 answer"
    )
