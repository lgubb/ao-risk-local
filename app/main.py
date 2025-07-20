# app/main.py

from fastapi import FastAPI
from app.routers import analyse, auth_routes, protected, vector_test

app = FastAPI(title="AO Risk | API")

@app.get("/")
async def read_root():
    return {"message": "AO Risk est prêt."}

# 🔌 Branchement des routeurs (après définition de `app`)
app.include_router(analyse.router)
app.include_router(auth_routes.router)
app.include_router(protected.router)
app.include_router(vector_test.router)

