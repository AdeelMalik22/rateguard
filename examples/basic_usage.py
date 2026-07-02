from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from requestguard import limit, Algorithm
from requestguard import RateLimitExceeded

app = FastAPI()

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content=exc.detail)

@limit(max_retries=5, ttl=60,algorithm=Algorithm.TOKEN_BUCKET)
def my_endpoint(request: Request):
    return {"message": "Hello!"}

@app.get("/hello")
def hello_route(request: Request):
    return my_endpoint(request)