import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from .routers import routes, solutions, instances, visualization


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="OptimizeRoutes API",
    description=(
        "REST API for CVRP route optimisation using neighbourhood search (2-opt*). "
        "Supports on-demand optimisation, batch streaming, metrics, comparison and GeoJSON export."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router)
app.include_router(solutions.router)
app.include_router(instances.router)
app.include_router(visualization.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}

