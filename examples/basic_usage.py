from fastapi import FastAPI, Request
from requestguard import Algorithm, RateLimitExceeded, limit
from requestguard.integrations.fastapi import rate_limit_exception_handler

app = FastAPI()

app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)

@app.get("/hello")
@limit(requests=5, window=60, algorithm=Algorithm.SLIDING_WINDOW_COUNTER)
async def hello(request: Request):
    return {"message": "Hello!"}
