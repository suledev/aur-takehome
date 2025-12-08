from aurora.data.models import Message
from sqlalchemy import text
from sqlmodel import create_engine
from aurora.data.defs import DATABASE_URL

engine = create_engine(DATABASE_URL)

def search_messages(
    query_text: str, 
    limit: int = 10, 
    offset: int = 0,
  ):
    # Sanitize the query for FTS MATCH: replace hyphens (and similar) with spaces
    safe_query = query_text.replace("-", " ").strip()

    query = text(
        f"""
          SELECT m.*
          FROM message AS m
          JOIN message_fts AS f
            ON m.id = f.id
          WHERE f.message MATCH :query
          ORDER BY m.timestamp DESC
          LIMIT {limit} OFFSET {offset}
        """
    )

    with engine.connect() as conn:
        result = conn.execute(
            query,
            {"query": safe_query, "limit": limit, "offset": offset}
        )
        return [dict(row) for row in result]