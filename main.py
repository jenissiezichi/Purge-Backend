from dotenv import load_dotenv
from fastapi import FastAPI
import time
import os
from routers import auth_routes, internal_router, user_router, spam_router, rules_router
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import  RateLimitExceeded
from rate_limiter import limiter
from fastapi.middleware.cors import CORSMiddleware
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

load_dotenv()


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(auth_routes.router)
app.include_router(user_router.router)
app.include_router(spam_router.router)
app.include_router(rules_router.router)
app.include_router(internal_router.router)

@app.middleware("http")
async def middleware(request, call_next):
    start_time = time.time()
    print(f"{request.method} {request.url.path}")
    response = await call_next(request)
    duration = time.time() - start_time
    print(f"{request.method} {request.url.path} - {response.status_code} took ({duration:2f}) seconds")
    return response
@app.get("/")
def read_root():
    return {"message": "Purge backend is alive"}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)