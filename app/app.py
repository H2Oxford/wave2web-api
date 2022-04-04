import datetime as dt
import os
import secrets

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from .data import get_levels, get_reservoir_list, get_prediction, get_historic
from .models import Message, Level, Prediction, Historic, ReservoirPred


app = FastAPI()

security = HTTPBasic()

origins = [
    "http://localhost:3000",
    "https://h2ox.org/",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware)

USERNAME = os.environ["USERNAME"]
PASSWORD = os.environ["PASSWORD"]


def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, USERNAME)
    correct_password = secrets.compare_digest(credentials.password, PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True


requires_auth = [Depends(authenticate)]
other_responses = {401: {"model": Message}, 400: {"model": Message}}


@app.get("/", response_model=Message)
def index() -> str:
    return "API is running"


@app.get(
    "/api/levels",
    dependencies=requires_auth,
    response_model=list[Level],
    responses=other_responses,
)
async def levels():
    try:
        data = get_levels()
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get(
    "/api/predictions",
    dependencies=requires_auth,
    response_model=list[ReservoirPred],
)
async def predictions(date: str):
    try:
        date = dt.datetime.strptime(date, "%Y-%m-%d")
        reservoirs = get_reservoir_list()
        data = [
            ReservoirPred(reservoir=res, prediction=get_prediction(reservoir=res, date=date))
            for res in reservoirs
        ]
        return data
    except ValueError:
        raise HTTPException(status_code=400, detail="specify a date as YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get(
    "/api/prediction",
    dependencies=requires_auth,
    response_model=list[Prediction],
    responses=other_responses,
)
async def prediction(reservoir: str, date: str):
    try:
        date = dt.datetime.strptime(date, "%Y-%m-%d")
        data = get_prediction(reservoir=reservoir, date=date)
        return data
    except ValueError:
        raise HTTPException(status_code=400, detail="specify a date as YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get(
    "/api/historic",
    dependencies=requires_auth,
    response_model=list[Historic],
    responses=other_responses,
)
async def historic(reservoir: str, date: str):
    try:
        date = dt.datetime.strptime(date, "%Y-%m-%d")
        data = get_historic(reservoir=reservoir, date=date)
        return data
    except ValueError:
        raise HTTPException(status_code=400, detail="specify a date as YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
