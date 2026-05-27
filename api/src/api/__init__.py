from .main import app


def main() -> None:
    import uvicorn

    uvicorn.run('api.main:app', host='127.0.0.1', port=8000, reload=True)
