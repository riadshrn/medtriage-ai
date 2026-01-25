from fastapi import FastAPI

app = FastAPI(title="RedFlag API - Vierge")

@app.get("/")
def read_root():
    return {"status": "online", "message": "Backend prêt à recevoir la logique"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}