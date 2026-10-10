"""
Graph Insights Router
Exposes Neo4j graph traversal, collaborative filtering recommendations, and Cypher analytics.
"""

from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional
from config.db_config import get_neo4j_driver
from app.services.neo4j_service import get_graph_counts
import neo4j_db.graph_traversal as neo_traversal
import neo4j_db.advanced_queries as neo_advanced

router = APIRouter(prefix="/api/graph", tags=["Graph Insights"])

@router.get("/summary")
def get_graph_summary():
    """Retrieve node counts, relationship counts, and schema constraints."""
    driver = get_neo4j_driver()
    counts = get_graph_counts()

    # Retrieve constraints and indexes
    constraints = []
    indexes = []
    with driver.session() as session:
        try:
            for r in session.run("SHOW CONSTRAINTS"):
                constraints.append({"name": r.get("name"), "type": r.get("type"), "entityType": r.get("entityType")})
        except Exception:
            pass
        try:
            for r in session.run("SHOW INDEXES"):
                indexes.append({"name": r.get("name"), "type": r.get("type"), "state": r.get("state")})
        except Exception:
            pass

    return {
        "metrics": counts,
        "constraints": constraints,
        "indexes": indexes
    }

@router.get("/prerequisites")
@router.get("/prerequisites/{course_id}")
def get_course_prerequisites(course_id: Optional[str] = None, course_id_query: Optional[str] = Query(None, alias="course_id")):
    """Explore variable-length prerequisite chain for a course."""
    cid = course_id or course_id_query
    if not cid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="course_id is required")
    driver = get_neo4j_driver()
    results = neo_traversal.find_course_prerequisites(driver, cid)
    return {"course_id": cid, "prerequisites": results}

@router.get("/learning-path")
def get_learning_path(
    start_course_id: str = Query(..., description="Starting Course ID (e.g., C001)"),
    end_course_id: str = Query(..., description="Target Course ID (e.g., C004)")
):
    """Calculate shortest prerequisite learning path between courses."""
    driver = get_neo4j_driver()
    path = neo_traversal.find_learning_path(driver, start_course_id, end_course_id)
    return {
        "start_course_id": start_course_id,
        "end_course_id": end_course_id,
        "path": path,
        "step_count": len(path)
    }

@router.get("/recommendations/{student_id}")
def get_course_recommendations(student_id: str, limit: int = Query(5, ge=1, le=10)):
    """Generate collaborative filtering course recommendations based on peer enrollment patterns."""
    driver = get_neo4j_driver()
    recs = neo_traversal.recommend_courses(driver, student_id)
    if isinstance(recs, list) and limit:
        recs = recs[:limit]
    return {"student_id": student_id, "recommendations": recs}

@router.get("/peer-cohort/{student_id}")
def get_peer_cohort(student_id: str):
    """Find other students sharing courses with the specified student."""
    driver = get_neo4j_driver()
    peers = neo_traversal.find_students_with_common_courses(driver, student_id)
    return {"student_id": student_id, "peers": peers}

@router.get("/instructor-network/{instructor_id}")
def get_instructor_network(instructor_id: str):
    """Traverse instructor's teaching network and student connections."""
    driver = get_neo4j_driver()
    network = neo_traversal.find_instructor_network(driver, instructor_id)
    if not network:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instructor network not found")
    return network

@router.get("/popularity")
@router.get("/analytics/popularity")
def get_course_popularity():
    """Retrieve course popularity ranking by total enrolled and completed students."""
    driver = get_neo4j_driver()
    return neo_advanced.course_popularity_ranking(driver)

@router.get("/analytics/skill-gap/{student_id}")
def get_student_skill_gap(student_id: str):
    """Identify skill gaps for enrolled courses that the student lacks."""
    driver = get_neo4j_driver()
    gaps = neo_advanced.skill_gap_analysis(driver, student_id)
    return {"student_id": student_id, "skill_gaps": gaps}

@router.get("/analytics/instructor-workload")
def get_instructor_workload():
    """Retrieve instructor course load and student reach analytics."""
    driver = get_neo4j_driver()
    return neo_advanced.instructor_workload(driver)

@router.get("/analytics/category-statistics")
def get_category_statistics():
    """Retrieve category level course counts, average hours, and enrollments."""
    driver = get_neo4j_driver()
    return neo_advanced.category_statistics(driver)

@router.get("/analytics/prerequisite-depth")
def get_prerequisite_depth():
    """Rank courses by maximum prerequisite chain depth."""
    driver = get_neo4j_driver()
    return neo_advanced.prerequisite_chain_depth(driver)

@router.get("/analytics/completion-rates")
def get_student_completion_rates():
    """Retrieve completion rates per student."""
    driver = get_neo4j_driver()
    return neo_advanced.student_completion_rate(driver)

@router.get("/network-graph")
def get_network_graph(limit: int = Query(50, ge=10, le=100)):
    """Retrieve graph nodes and relationships formatted for interactive visualization."""
    driver = get_neo4j_driver()
    query = """
        MATCH (s)-[r]->(t)
        RETURN id(s) AS source_id, labels(s)[0] AS source_label, s.name AS source_name, s.title AS source_title, s.student_id AS source_sid, s.course_id AS source_cid,
               type(r) AS rel_type,
               id(t) AS target_id, labels(t)[0] AS target_label, t.name AS target_name, t.title AS target_title, t.course_id AS target_cid, t.skill_id AS target_skid
        LIMIT $limit
    """
    nodes_dict = {}
    links = []

    with driver.session() as session:
        records = session.run(query, limit=limit)
        for rec in records:
            src_id = f"node_{rec['source_id']}"
            tgt_id = f"node_{rec['target_id']}"

            src_title = rec["source_title"] or rec["source_name"] or rec["source_sid"] or rec["source_cid"] or "Node"
            tgt_title = rec["target_title"] or rec["target_name"] or rec["target_cid"] or rec["target_skid"] or "Node"

            if src_id not in nodes_dict:
                nodes_dict[src_id] = {
                    "id": src_id,
                    "label": rec["source_label"],
                    "title": src_title
                }
            if tgt_id not in nodes_dict:
                nodes_dict[tgt_id] = {
                    "id": tgt_id,
                    "label": rec["target_label"],
                    "title": tgt_title
                }

            links.append({
                "source": src_id,
                "target": tgt_id,
                "type": rec["rel_type"]
            })

    return {
        "nodes": list(nodes_dict.values()),
        "links": links
    }
