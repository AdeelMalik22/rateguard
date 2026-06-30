from fastapi import FastAPI, Request

from decorators.decorator import limit


app = FastAPI()


@limit(
    requests=3,
    window=10,
)
def hello(request: Request):

    return {
        "message": "hello"
    }


@app.get("/hello")
def hello_route(request: Request):

    return hello(request)