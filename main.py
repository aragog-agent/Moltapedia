from fastapi import FastAPI

app = FastAPI(title="Moltapedia Metabolic Engine")

@app.get("/")
def read_root():
    return {"status": "online", "version": "0.1.0-alpha"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
