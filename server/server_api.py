from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from subprocess import call

app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.route("/")
def root():
    return {"message": "hello world"}


@app.get("/upload")
def get_upload():
    return {"message": "this is the get upload api endpoint"}
