from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, MovieModel
from schemas import (
    MovieDetailResponseSchema,
    MovieListResponseSchema,
    MovieNotFoundSchema,
)

router = APIRouter()


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
    responses={
        404: {
            "model": MovieNotFoundSchema,
            "description": "No movies found"
        }
    }
)
async def get_movies(
        request: Request,
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(10, ge=1, le=20, description="Movies per page"),
        db: AsyncSession = Depends(get_db),
):
    total_items = await db.scalar(select(func.count()).select_from(MovieModel))

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    offset = (page - 1) * per_page
    total_pages = (total_items + per_page - 1) // per_page

    query = select(MovieModel).offset(offset).limit(per_page)
    result = await db.scalars(query)
    movies = result.all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    prev_page = str(request.url.replace_query_params(page=page - 1, per_page=per_page)) if page > 1 else None
    next_page = str(request.url.replace_query_params(page=page + 1, per_page=per_page)) if page < total_pages else None

    return MovieListResponseSchema(
        movies=[MovieDetailResponseSchema.model_validate(movie) for movie in movies],
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailResponseSchema,
    responses={
        404: {
            "model": MovieNotFoundSchema,
            "description": "No movies found"
        }
    }
)
async def get_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db),
) -> MovieDetailResponseSchema:
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )
    return MovieDetailResponseSchema.model_validate(movie)
