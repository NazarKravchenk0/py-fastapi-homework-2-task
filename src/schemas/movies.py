from datetime import date, timedelta
from typing import List, Optional, Literal

from pydantic import BaseModel, Field, validator


StatusType = Literal["Released", "Post Production", "In Production"]


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


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]

    class Config:
        orm_mode = True


class NamedEntitySchema(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class MovieDetailResponseSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: StatusType
    budget: float
    revenue: float
    country: Optional[CountrySchema]
    genres: List[NamedEntitySchema]
    actors: List[NamedEntitySchema]
    languages: List[NamedEntitySchema]

    class Config:
        orm_mode = True


class MovieCreateRequestSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: StatusType
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str = Field(..., min_length=3, max_length=3)
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @validator("date")
    def date_not_too_far_in_future(cls, value: date) -> date:
        max_allowed = date.today() + timedelta(days=365)
        if value > max_allowed:
            raise ValueError("date is too far in the future")
        return value


class MovieUpdateRequestSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[StatusType] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)

    @validator("date")
    def update_date_not_too_far_in_future(cls, value: Optional[date]) -> Optional[date]:
        if value is None:
            return value
        max_allowed = date.today() + timedelta(days=365)
        if value > max_allowed:
            raise ValueError("date is too far in the future")
        return value


class MessageSchema(BaseModel):
    detail: str
