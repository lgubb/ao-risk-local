from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    auth_routes,
    protected,
    upload_routes,
    query_routes,
    viewer_routes,
)



app = FastAPI(
    title="AO Risk | API",
    description="API d'analyse DCE et détection de clauses critiques",
    version="1.0.0",
    root_path="/api",
)

# CORS: autoriser le front Next.js en dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return {"message": "AO Risk est prêt."}

# Routes existantes
app.include_router(auth_routes.router)
app.include_router(protected.router)
app.include_router(upload_routes.router)
app.include_router(query_routes.router)
app.include_router(viewer_routes.router)
