from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import email

app = FastAPI(title="Smartmail API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(email.router, prefix="/api/v1", tags=["emails"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Smartmail API",
        "version": "1.0.0",
        "docs_url": "/docs"
    } 