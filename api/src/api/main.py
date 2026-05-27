from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.config import DATA_DIR
from api.routers import analysis, annotations, frames, results, videos

app = FastAPI(title='AI Climbing API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.mount("/static", StaticFiles(directory=DATA_DIR), name="static")

app.include_router(videos.router, prefix='/api/videos', tags=['videos'])
app.include_router(frames.router, prefix='/api/videos', tags=['frames'])
app.include_router(annotations.router, prefix='/api/videos', tags=['annotations'])
app.include_router(analysis.router, prefix='/api/videos', tags=['analysis'])
app.include_router(results.router, prefix='/api/videos', tags=['results'])


@app.get('/api/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}
