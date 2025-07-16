from fastapi import FastAPI

app = FastAPI(
    title="Talktor API",
    description="API for Talktor project",
    version="0.1.0"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to Talktor API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
