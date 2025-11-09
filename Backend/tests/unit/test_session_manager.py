from app.session_manager import SessionRegistry


def test_session_lifecycle():
    registry = SessionRegistry()

    session_id, replaced = registry.start_session("alice")
    assert replaced is False
    assert registry.validate("alice", session_id) is True

    new_session, replaced = registry.start_session("alice")
    assert replaced is True
    assert new_session != session_id
    assert registry.validate("alice", new_session) is True
    assert registry.validate("alice", session_id) is False

    assert registry.end_session("alice") is True
    assert registry.validate("alice", new_session) is False
    assert registry.end_session("alice") is False


def test_validate_unknown_user_returns_false():
    registry = SessionRegistry()
    assert registry.validate("ghost", "anything") is False
