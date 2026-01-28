from __future__ import annotations

import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator


ALLOWED_STATUSES = {"Released", "Post Production", "In Production"}


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

    @validator("status")
    def validate_status(cls, value: str) -> str:
        if value not in ALLOWED_STATUSES:
            raise ValueError("Invalid input data.")
        return value

    @validator("country")
    def validate_country(cls, value: str) -> str:
        # ISO 3166-1 alpha-3: 3 letters
        if not isinstance(value, str) or len(value) != 3 or not value.isalpha():
            raise ValueError("Invalid input data.")
        return value.upper()


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    date: Optional[datetime.date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None

    @validator("status")
    def validate_status(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if value not in ALLOWED_STATUSES:
            raise ValueError("Invalid input data.")
        return value


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
