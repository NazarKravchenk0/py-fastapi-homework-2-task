from __future__ import annotations

import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str] = None

    class Config:
        orm_mode = True


class GenreSchema(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class ActorSchema(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class LanguageSchema(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    class Config:
        orm_mode = True


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: datetime.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    date: Optional[datetime.date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountrySchema
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]

    class Config:
        orm_mode = True
