from fastapi import FastAPI

app = FastAPI()

@app.get("/price")
def get_price():
    return {"price": 42.0}
