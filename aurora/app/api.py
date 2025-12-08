import time
from fastapi import FastAPI, Query, HTTPException, Request
from aurora.data import client, db
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    db.populate_db()
    yield

app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get("/search")
def search_endpoint(
    q: str = Query(..., min_length=1, description="Search query text"),
    limit: int = Query(10, ge=1, le=100, description="Max number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    if limit > 100:
        raise HTTPException(status_code=422, detail="Limit cannot exceed 100")
    try:
        results = client.search_messages(q, limit=limit, offset=offset)
        return {"count": len(results), "results": results}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred, please try again later."
        ) from e
