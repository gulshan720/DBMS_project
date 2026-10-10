"""
Neo4j Service Helper
Provides session execution and formatting helpers for graph queries.
"""

from config.db_config import get_neo4j_driver

def execute_query(query: str, parameters: dict = None):
    """Execute a parameterized Cypher query and return list of records as dicts."""
    driver = get_neo4j_driver()
    params = parameters or {}
    results = []
    with driver.session() as session:
        result = session.run(query, **params)
        for record in result:
            results.append(dict(record))
    return results

def get_graph_counts():
    """Retrieve node and relationship totals by label and type."""
    driver = get_neo4j_driver()
    counts = {
        "nodes_by_label": {},
        "relationships_by_type": {},
        "total_nodes": 0,
        "total_relationships": 0,
    }
    with driver.session() as session:
        # Total nodes
        res = session.run("MATCH (n) RETURN count(n) AS cnt").single()
        counts["total_nodes"] = res["cnt"] if res else 0

        # Total relationships
        res = session.run("MATCH ()-[r]->() RETURN count(r) AS cnt").single()
        counts["total_relationships"] = res["cnt"] if res else 0

        # Node labels
        label_res = session.run("CALL db.labels() YIELD label RETURN label")
        for record in label_res:
            lbl = record["label"]
            cnt_res = session.run(f"MATCH (n:`{lbl}`) RETURN count(n) AS cnt").single()
            counts["nodes_by_label"][lbl] = cnt_res["cnt"] if cnt_res else 0

        # Relationship types
        rel_res = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType")
        for record in rel_res:
            rtype = record["relationshipType"]
            cnt_res = session.run(f"MATCH ()-[r:`{rtype}`]->() RETURN count(r) AS cnt").single()
            counts["relationships_by_type"][rtype] = cnt_res["cnt"] if cnt_res else 0

    return counts
