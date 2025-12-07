from datetime import datetime
from sqlmodel import SQLModel, create_engine, Session
import aurora.data.client as client_mod
from aurora.data.models import Message


def _setup_temp_db(tmp_path):
    db_file = tmp_path / "test.db"
    db_url = f"sqlite:///{db_file}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})

    SQLModel.metadata.create_all(engine)

    with engine.begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS message_fts
            USING fts5(
                id UNINDEXED,
                message,
                user_name,
                content='message',
                content_rowid='id'
            );
            """
        )

    return engine


def _insert_message(engine, id, user_id, user_name, timestamp, message_text):
    with Session(engine) as session:
        msg = Message(
            id=str(id),
            user_id=user_id,
            user_name=user_name,
            timestamp=timestamp,
            message=message_text,
        )
        session.add(msg)
        session.commit()

    with engine.begin() as conn:
        conn.exec_driver_sql(
            "INSERT INTO message_fts(rowid, id, user_name, message) VALUES (?, ?, ?, ?)",
            (int(id), str(id), user_name, message_text),
        )


def test_search_messages_returns_matching(tmp_path, monkeypatch):
    engine = _setup_temp_db(tmp_path)
    monkeypatch.setattr(client_mod, "engine", engine)

    _insert_message(engine, 1, "u1", "alice", datetime.fromisoformat("2020-01-01T00:00:00"), "hello world")
    _insert_message(engine, 2, "u2", "bob", datetime.fromisoformat("2020-01-02T00:00:00"), "other message")

    results = client_mod.search_messages("hello")
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["id"] == "1"
    assert results[0]["message"] == "hello world"


def test_search_pagination_respects_limit_and_offset(tmp_path, monkeypatch):
    engine = _setup_temp_db(tmp_path)
    monkeypatch.setattr(client_mod, "engine", engine)

    _insert_message(engine, 1, "u1", "alice", datetime.fromisoformat("2020-01-01T00:00:00"), "hello a")
    _insert_message(engine, 2, "u2", "bob", datetime.fromisoformat("2020-01-02T00:00:00"), "hello b")
    _insert_message(engine, 3, "u3", "carol", datetime.fromisoformat("2020-01-03T00:00:00"), "hello c")

    results = client_mod.search_messages("hello", limit=1, offset=1)
    assert len(results) == 1
    assert results[0]["id"] == "2"


def test_search_no_matches_returns_empty(tmp_path, monkeypatch):
    engine = _setup_temp_db(tmp_path)
    monkeypatch.setattr(client_mod, "engine", engine)

    _insert_message(engine, 1, "u1", "alice", datetime.fromisoformat("2020-01-01T00:00:00"), "foo bar")

    results = client_mod.search_messages("nomatch")
    assert results == []
