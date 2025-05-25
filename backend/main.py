from fastapi import FastAPI, Request, Query
from backend.api.v1.api import api_router
from backend.core.logger import logger



app = FastAPI(title="Research Connect Platform")

app.include_router(api_router, prefix="/api/v1")
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming {request.method} request to {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

@app.get("/oauth-success")
async def oauth_success(token: str = Query(...)):
    # simply return JSON with the token so tests pass
    logger.info(f"oauth_success token : {token}")
    return JSONResponse({"message": "OAuth successful", "token": token})


