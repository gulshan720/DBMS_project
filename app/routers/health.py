"""
Health & Database Connectivity Router
Provides status checks for application, MongoDB, and Neo4j.
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from config.db_config import get_mongo_client, get_neo4j_driver
import time

router = APIRouter(prefix="/api/health", tags=["Health"])

@router.get("")
def check_health():
    """Verify application health and database connections."""
    health_data = {
        "status": "healthy",
        "timestamp": time.time(),
        "databases": {
            "mongodb": {"status": "unknown"},
            "neo4j": {"status": "unknown"}
        }
    }

    # Test MongoDB
    try:
        t0 = time.time()
        client = get_mongo_client()
        ping_res = client.admin.command("ping")
        latency_ms = round((time.time() - t0) * 1000, 2)
        
        # Check replica set status if available
        repl_info = "standalone"
        try:
            status_cmd = client.admin.command("replSetGetStatus")
            repl_info = f"replica_set:{status_cmd.get('set', 'rs0')}"
        except Exception:
            pass

        health_data["databases"]["mongodb"] = {
            "status": "connected",
            "latency_ms": latency_ms,
            "mode": repl_info,
            "ok": ping_res.get("ok", 0) == 1
        }
    except Exception as e:
        health_data["status"] = "degraded"
        health_data["databases"]["mongodb"] = {
            "status": "error",
            "error": "Connection to MongoDB failed"
        }

    # Test Neo4j
    try:
        t0 = time.time()
        driver = get_neo4j_driver()
        driver.verify_connectivity()
        latency_ms = round((time.time() - t0) * 1000, 2)
        health_data["databases"]["neo4j"] = {
            "status": "connected",
            "latency_ms": latency_ms
        }
    except Exception as e:
        health_data["status"] = "degraded"
        health_data["databases"]["neo4j"] = {
            "status": "error",
            "error": "Connection to Neo4j failed"
        }

    status_code = status.HTTP_200_OK if health_data["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(content=health_data, status_code=status_code if health_data["status"] != "degraded" else status.HTTP_200_OK)
