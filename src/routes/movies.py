from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db
from database.models import (
    MovieModel,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
    MovieStatusEnum,
)
from schemas.movies import (
    MovieCreateSchema,
    MovieUpdateSchema,
    MovieListResponseSchema,
    MovieDetailSchema,
)

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    # total_items
    count_stmt = select(func.count(MovieModel.id))
    count_result = await db.execute(count_stmt)
    total_items = count_result.scalar_one()

    offset = (page - 1) * per_page

    stmt = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = ceil(total_items / per_page) if total_items else 0

    prev_page = None
    next_page = None

    if page > 1:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"
    if page < total_pages:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post("/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(movie: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    # Duplicate check (name + date)
    dup_stmt = select(MovieModel).where(
        MovieModel.name == movie.name,
        MovieModel.date == movie.date,
    )
    dup_result = await db.execute(dup_stmt)
    if dup_result.scalars().first():
        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
            ),
        )

    # Country (create if not exists)
    country_stmt = select(CountryModel).where(CountryModel.code == movie.country)
    country_result = await db.execute(country_stmt)
    country = country_result.scalars().first()

    if not country:
        country = CountryModel(code=movie.country)
        db.add(country)
        await db.flush()

    # Genres (create if not exists)
    genres = []
    for genre_name in movie.genres:
        g_stmt = select(GenreModel).where(GenreModel.name == genre_name)
        g_res = await db.execute(g_stmt)
        genre = g_res.scalars().first()
        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
            await db.flush()
        genres.append(genre)

    # Actors (create if not exists)
    actors = []
    for actor_name in movie.actors:
        a_stmt = select(ActorModel).where(ActorModel.name == actor_name)
        a_res = await db.execute(a_stmt)
        actor = a_res.scalars().first()
        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)
            await db.flush()
        actors.append(actor)

    # Languages (create if not exists)
    languages = []
    for language_name in movie.languages:
        l_stmt = select(LanguageModel).where(LanguageModel.name == language_name)
        l_res = await db.execute(l_stmt)
        language = l_res.scalars().first()
        if not language:
            language = LanguageModel(name=language_name)
            db.add(language)
            await db.flush()
        languages.append(language)

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=MovieStatusEnum(movie.status),
        budget=movie.budget,
        revenue=movie.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    db.add(new_movie)
    await db.commit()

    # Reload with relations for response
    await db.refresh(new_movie)

    return new_movie


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
    result = await db.execute(stmt)
    movie = result.scalars().first()

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

    # Validation for negative values / score range already in schema, но оставим safe-check:
    if "score" in data and (data["score"] < 0 or data["score"] > 100):
        raise HTTPException(status_code=400, detail="Invalid input data.")
    if "budget" in data and data["budget"] < 0:
        raise HTTPException(status_code=400, detail="Invalid input data.")
    if "revenue" in data and data["revenue"] < 0:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    for field, value in data.items():
        if field == "status":
            value = MovieStatusEnum(value)
        setattr(movie, field, value)

    await db.commit()
    return {"detail": "Movie updated successfully."}
