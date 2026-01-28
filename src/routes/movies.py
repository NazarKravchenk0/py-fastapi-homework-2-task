from __future__ import annotations

import datetime
from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db
from database.models import (
    ActorModel,
    CountryModel,
    GenreModel,
    LanguageModel,
    MovieModel,
    MovieStatusEnum,
)
from schemas.movies import (
    MovieCreateSchema,
    MovieDetailSchema,
    MovieListResponseSchema,
    MovieUpdateSchema,
    ALLOWED_STATUSES,
)

router = APIRouter(prefix="/movies", tags=["movies"])


def _page_url(request: Request, page: int, per_page: int) -> str:
    path = request.url.path
    if path.startswith("/api/v1"):
        path = path[len("/api/v1"):]
    return f"{path}?page={page}&per_page={per_page}"


def _validate_movie_fields_for_create(payload: MovieCreateSchema) -> None:
    if payload.date > (datetime.date.today() + datetime.timedelta(days=365)):
        raise HTTPException(status_code=400, detail="Invalid input data.")

    if payload.score < 0 or payload.score > 100:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    if payload.budget < 0 or payload.revenue < 0:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    # Extra safety (even though schema validates)
    if payload.status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    if len(payload.country) != 3 or not payload.country.isalpha():
        raise HTTPException(status_code=400, detail="Invalid input data.")


def _validate_movie_fields_for_update(data: dict) -> None:
    if "score" in data and data["score"] is not None:
        if data["score"] < 0 or data["score"] > 100:
            raise HTTPException(status_code=400, detail="Invalid input data.")

    if "budget" in data and data["budget"] is not None and data["budget"] < 0:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    if "revenue" in data and data["revenue"] is not None and data["revenue"] < 0:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    if "date" in data and data["date"] is not None:
        if data["date"] > (datetime.date.today() + datetime.timedelta(days=365)):
            raise HTTPException(status_code=400, detail="Invalid input data.")

    if "status" in data and data["status"] is not None:
        if data["status"] not in ALLOWED_STATUSES:
            raise HTTPException(status_code=400, detail="Invalid input data.")


@router.get("/", response_model=MovieListResponseSchema)
async def get_movies(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    count_stmt = select(func.count(MovieModel.id))
    total_items = (await db.execute(count_stmt)).scalar_one()

    offset = (page - 1) * per_page

    stmt = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    movies = (await db.execute(stmt)).scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = ceil(total_items / per_page) if total_items else 0

    prev_page: Optional[str] = None
    next_page: Optional[str] = None

    if page > 1:
        prev_page = _page_url(request, page - 1, per_page)

    if page < total_pages:
        next_page = _page_url(request, page + 1, per_page)

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post("/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(movie: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    _validate_movie_fields_for_create(movie)

    dup_stmt = select(MovieModel).where(
        MovieModel.name == movie.name,
        MovieModel.date == movie.date,
    )
    dup = (await db.execute(dup_stmt)).scalars().first()
    if dup:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.",
        )

    country_stmt = select(CountryModel).where(CountryModel.code == movie.country)
    country = (await db.execute(country_stmt)).scalars().first()
    if not country:
        country = CountryModel(code=movie.country)
        db.add(country)
        await db.flush()

    genres = []
    for name in movie.genres:
        stmt = select(GenreModel).where(GenreModel.name == name)
        genre = (await db.execute(stmt)).scalars().first()
        if not genre:
            genre = GenreModel(name=name)
            db.add(genre)
            await db.flush()
        genres.append(genre)

    actors = []
    for name in movie.actors:
        stmt = select(ActorModel).where(ActorModel.name == name)
        actor = (await db.execute(stmt)).scalars().first()
        if not actor:
            actor = ActorModel(name=name)
            db.add(actor)
            await db.flush()
        actors.append(actor)

    languages = []
    for name in movie.languages:
        stmt = select(LanguageModel).where(LanguageModel.name == name)
        language = (await db.execute(stmt)).scalars().first()
        if not language:
            language = LanguageModel(name=name)
            db.add(language)
            await db.flush()
        languages.append(language)

    # IMPORTANT: handle invalid status => 400, not 500
    try:
        status_enum = MovieStatusEnum(movie.status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=status_enum,
        budget=movie.budget,
        revenue=movie.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    db.add(new_movie)
    await db.commit()

    stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == new_movie.id)
    )
    created = (await db.execute(stmt)).scalars().first()
    return created


@router.get("/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    movie = (await db.execute(stmt)).scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return movie


@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.get(MovieModel, movie_id)

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()
    return None


@router.patch("/{movie_id}/")
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    movie = await db.get(MovieModel, movie_id)

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    data = movie_data.dict(exclude_unset=True)
    _validate_movie_fields_for_update(data)

    for field, value in data.items():
        if field == "status" and value is not None:
            try:
                value = MovieStatusEnum(value)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid input data.")
        setattr(movie, field, value)

    await db.commit()
    return {"detail": "Movie updated successfully."}
