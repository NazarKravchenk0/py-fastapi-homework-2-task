from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel


router = APIRouter()

@router.get("/movies/")
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db),
):
    sa = __import__("sqlalchemy")
    select = sa.select
    func = sa.func

    # Если AsyncSession — db.scalar/execute await
    total_items = await db.scalar(select(func.count()).select_from(MovieModel))
    if not total_items:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page
    offset = (page - 1) * per_page

    # сортировка по id DESC (по заданию)
    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    prev_page = None
    if page > 1:
        prev_page = (
            f"/theater/movies/?page={page - 1}"
            f"&per_page={per_page}"
        )

    next_page = None
    if page < total_pages:
        next_page = (
            f"/theater/movies/?page={page + 1}"
            f"&per_page={per_page}"
        )

    # В списке по описанию ответа нужны только: id, name, date, score, overview
    return {
        "movies": [
            {
                "id": m.id,
                "name": m.name,
                "date": m.date,
                "score": float(m.score) if m.score is not None else None,
                "overview": m.overview,
            }
            for m in movies
        ],
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }

