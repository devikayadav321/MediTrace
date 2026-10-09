from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import auth_router, report_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI-Assisted Medical Report Verification Backend",
    version="1.0.0"
)

# Enable CORS for Frontend Connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(report_router.router)

@app.get("/")
def root():
    return {"message": "Medical Platform Backend is running successfully!"}