from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import world
from api.routes import vehicles
from api.routes import orders
from api.routes import routes
from api.routes import planning
from api.routes import traffic_tiles

app = FastAPI()

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

app.include_router(world.router)
app.include_router(vehicles.router)
app.include_router(orders.router)
app.include_router(routes.router)
app.include_router(planning.router)
app.include_router(traffic_tiles.router)
