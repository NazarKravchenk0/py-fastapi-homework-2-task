from datetime import date, timedelta
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]

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


class MovieCreateSchema(BaseModel):
    name: str = Field(max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str
    status: str
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str  # tests use "US"
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @validator("date")
    def validate_date(cls, value: date) -> date:
        if value > date.today() + timedelta(days=365):
            raise ValueError("Date cannot be more than one year in the future")
        return value


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(default=None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = Field(default=None, ge=0)
    revenue: Optional[float] = Field(default=None, ge=0)


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
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


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date
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
