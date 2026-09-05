import math
from typing import Any, Dict, List
from sqlalchemy.orm import Query


def paginate_query(query: Query, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
    """
    Standard pagination utility for SQLAlchemy queries.
    Returns items and pagination metadata.
    """
    total = query.count()
    total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 1
    page = max(1, min(page, total_pages))
    
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    
    start_idx = (page - 1) * page_size + 1 if total > 0 else 0
    end_idx = min(page * page_size, total)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "start_idx": start_idx,
        "end_idx": end_idx,
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "prev_page": page - 1,
        "next_page": page + 1,
    }

