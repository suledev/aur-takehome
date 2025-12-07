import requests
from sqlmodel import SQLModel, Session, select, create_engine
from datetime import datetime
from aurora.data import defs as data_defs
from aurora.data.models import Message


def init_db():
    engine = create_engine(data_defs.DATABASE_URL)
    SQLModel.metadata.create_all(engine)

    with engine.connect() as conn:
        conn.exec_driver_sql(
            """
                CREATE VIRTUAL TABLE IF NOT EXISTS message_fts
                USING fts5(
                    message,
                    user_name,
                    id UNINDEXED
                );
            """
        )


def retrieve_messages():
    all_items = []
    skip = 0

    while True:
        response = requests.get(
            data_defs.SOURCE_URL,
            params={
                "skip": skip,
                "limit": data_defs.FETCH_LIMIT
            }
        )
        try:
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching messages: {e}")
            raise

        data = response.json()

        items = data.get("items", [])
        if not items:
            break

        all_items.extend(items)
        skip += len(items)

        if len(items) < data_defs.FETCH_LIMIT:
            break

    return all_items

def populate_db():
    messages = retrieve_messages()
    if not messages:
        print("No messages to populate.")
        return

    engine = create_engine(data_defs.DATABASE_URL)
    with Session(engine) as session:
        for msg in messages:
            # Check if message already exists
            exists = session.exec(select(Message).where(Message.id == msg["id"])).first()
            if exists:
                continue

            entry = Message(
                id=msg["id"],
                user_id=msg["user_id"],
                user_name=msg["user_name"],
                timestamp=datetime.fromisoformat(msg["timestamp"]),
                message=msg["message"]
            )
            session.add(entry)

        session.commit()
    
    with engine.begin() as conn:
        conn.exec_driver_sql(
            """
                INSERT INTO message_fts(message, user_name, id)
                SELECT message, user_name, id
                FROM message
                WHERE id NOT IN (SELECT id FROM message_fts);
            """
        )