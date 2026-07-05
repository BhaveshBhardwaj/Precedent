"""Graph route — GET /graph.

Exposes the raw knowledge graph for live visualization in the frontend.
Judges can literally watch the user's pattern graph grow and then
prune when a pattern is resolved.
"""

from fastapi import APIRouter
from app.db.models import GraphResponse
from app.cognee_client import get_graph_data

router = APIRouter(tags=["graph"])


@router.get("/graph", response_model=GraphResponse)
async def get_graph():
    """Get the raw knowledge graph for visualization.

    Returns nodes and edges from Cognee's graph engine (Kuzu by default).
    The frontend renders this as a force-directed graph using
    react-force-graph or similar.
    """
    data = await get_graph_data()
    return GraphResponse(**data)
