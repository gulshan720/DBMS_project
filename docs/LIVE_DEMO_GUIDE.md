# Live Demonstration Guide — Online Learning Portal
**Hybrid MongoDB + Neo4j NoSQL Database System**

This practical guide provides the exact step-by-step commands to launch, verify, demonstrate, and clean up the project during an evaluation.

---

## 1. Quick Startup & Verification Commands (Windows PowerShell)

Open PowerShell in the project root directory: `C:\Users\ASUS\OneDrive\Desktop\DBMS_project_2026`

### A. Start Database Engines (if not already running)
```powershell
# 1. Start MongoDB (configured with single-node replica set 'rs0' for ACID transactions)
& "C:\Users\ASUS\mongodb\bin\mongod.exe" --config "C:\Users\ASUS\mongodb\mongod.cfg"

# 2. Start Neo4j Community Server
$env:JAVA_HOME = "C:\Program Files\Java\jdk-21"
$env:PATH = "C:\Program Files\Java\jdk-21\bin;" + $env:PATH
& "C:\Users\ASUS\neo4j\neo4j-community-5.26.0\bin\neo4j.bat" console
```

### B. Verify Connectivity & Ports
```powershell
# Test TCP ports: 27017 (MongoDB) and 7687 (Neo4j Bolt)
Test-NetConnection -ComputerName 127.0.0.1 -Port 27017
Test-NetConnection -ComputerName 127.0.0.1 -Port 7687
```

### C. Seed Baseline Data (Idempotent)
```powershell
# Initialize MongoDB schemas ($jsonSchema), seed documents (57 docs), and indexes (IXSCAN)
python mongo/schema_design.py
python mongo/seed_data.py
python mongo/indexing.py

# Initialize Neo4j uniqueness constraints, range indexes, and property graph (52 nodes, 72 rels)
python neo4j_db/schema_setup.py
python neo4j_db/seed_data.py
```

### D. Start FastAPI Web Application
```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- **Web Portal URL:** `http://127.0.0.1:8000`
- **Interactive OpenAPI Documentation:** `http://127.0.0.1:8000/docs`
- **Neo4j Browser:** `http://localhost:7474` (connect via `bolt://localhost:7687`)

---

## 2. Safe Demonstration Sequence

### Step 1: System Telemetry & Dashboard Overview (`#dashboard`)
1. Open `http://127.0.0.1:8000/#dashboard`.
2. **Observe Header Badges:** Green connected indicator dots for both MongoDB (`rs0`) and Neo4j with sub-5ms latency.
3. **Observe KPI Cards:**
   - MongoDB Counts: `10` Students, `10` Courses, `5` Instructors, `17` Materials.
   - Neo4j Graph Counts: `52` Nodes, `72` Relationships.
   - Progress Summary: Completed vs In-Progress distribution and overall completion average.
4. **Recent Activity Table:** Live MongoDB `$lookup` joining students, course titles, and progress bars.

### Step 2: Student Management & Dual-Write Sync (`#students`)
1. Click **Students** in the navigation bar.
2. **Search Filter:** Type `Aarav` or `S001` to show real-time regex filtering.
3. **Register New Student:**
   - Click **+ Register Student**.
   - Student ID: `S999`, Name: `Demo Student`, Email: `demo.student@portal.edu`, Phone: `9876543210`.
   - Click **Register Student**.
   - **Outcome:** Toast displays success. A new Student document is created in MongoDB AND synchronized as a `:Student` node in Neo4j.
4. **View Details & Dual-Database Skills:**
   - Click **Details** on `S999`.
   - Note course progress rendered from MongoDB and acquired skills rendered from Neo4j graph traversal (`MATCH (st)-[:HAS_SKILL]->(sk)`).
5. **Inline Enrollment:**
   - Under *Enroll in New Course*, enter `C001` and click **Enroll**.
   - **Outcome:** MongoDB updates student's `courses_enrolled` array and creates a progress document; Neo4j creates an `[:ENROLLED_IN]` relationship.
6. **Cleanup:** Click the **Delete** (trash) icon on `S999` to remove the temporary record from both databases.

### Step 3: Course Catalog & Prerequisite Linking (`#courses`)
1. Click **Courses** in the navigation bar.
2. **Category & Difficulty Filters:** Filter by `Data Science` and `Beginner`.
3. **Create Course:**
   - Click **+ Create Course**.
   - Course ID: `C999`, Title: `Cloud-Native Databases`, Category: `Cloud Computing`, Difficulty: `Intermediate`, Instructor: `I003`, Duration: `35`, Price: `1499`.
   - Click **Save Course**.
   - **Outcome:** Dual-writes to MongoDB `courses` and creates `:Course` node linked to `:Category` and `:Instructor` in Neo4j via `[:BELONGS_TO]` and `[:TEACHES]`.
4. **Course Details Modal:** Click the info icon on `C004` (React Masterclass) to view learning materials, quizzes, and Neo4j prerequisite graph dependencies.
5. **Cleanup:** Delete `C999` to trigger cascade deletion and referential `$pull` cleanups.

### Step 4: Learning Materials & Assessments (`#materials` & `#quizzes`)
1. Click **Learning Materials**: Filter by `video`, `pdf`, or `article`.
2. Click **Quizzes & Progress**:
   - Inspect quizzes and expand **View Questions** to see nested embedded questions.
   - View student progress records, quiz score attempt histories, and last-accessed timestamps.

### Step 5: MongoDB Analytics & Index Explain Plan (`#analytics`)
1. Click **MongoDB Analytics** in the navigation bar.
2. **Review 5 Aggregation Pipelines:**
   - **Pipeline 1:** Average course completion percentage with `$lookup` and `$round`.
   - **Pipeline 2:** Top students by completed courses (`$match` completed, `$group`, `$sort`).
   - **Pipeline 3:** Catalog revenue estimates (`$unwind` courses_enrolled, `$multiply` price).
   - **Pipeline 4:** Quiz average scores and attempt counts.
   - **Pipeline 5:** Distribution of learning materials by format (`video`, `pdf`, `article`).
3. **Index Usage Explain Comparison:**
   - Switch to the **Index Performance** tab.
   - Notice the visual comparison: Unindexed query produces `COLLSCAN` (full sequential scan); Indexed query on `courses.category` produces `FETCH -> IXSCAN` utilizing `category_1`.

### Step 6: Neo4j Graph Insights & Traversals (`#graph`)
1. Click **Graph Insights** in the navigation bar.
2. **Variable-Length Prerequisite Chain:**
   - Select Course `C004` (React Masterclass) and click **Explore Prerequisites**.
   - Cypher variable-length traversal (`[:PREREQUISITE_OF*1..]`) outputs dependency chain with depth levels.
3. **Shortest Learning Path:**
   - Start Course: `C001`, Destination: `C004`.
   - Click **Find Shortest Path**.
   - Cypher `shortestPath((start)-[:PREREQUISITE_OF*]->(end))` computes the exact course sequence.
4. **Collaborative Filtering Recommendations:**
   - Select student `S001` and click **Get Recommendations**.
   - Cypher peer-similarity query (`MATCH (s)-[:ENROLLED_IN]->(c)<-[:ENROLLED_IN]-(peer)-[:ENROLLED_IN]->(rec)`) returns courses recommended by similar learners.
5. **Skill Gap Analysis:**
   - Select `S001` and click **Analyze Skill Gaps**.
   - Identifies skills required by enrolled courses that the student has not yet mastered.

---

## 3. Post-Demo Reset & Cleanup Command

To ensure the database is left in a pristine state after any ad-hoc demonstration:
```powershell
python mongo/seed_data.py
python neo4j_db/seed_data.py
```
This guarantees the baseline is exactly **57 MongoDB documents** and **52 Neo4j nodes with 72 relationships**.

---

## 4. Troubleshooting & Recovery Procedures

| Issue / Error | Root Cause | Exact Recovery Command |
| :--- | :--- | :--- |
| `[WinError 10061] No connection could be made` on port 27017 | MongoDB daemon is not running | Run `& "C:\Users\ASUS\mongodb\bin\mongod.exe" --config "C:\Users\ASUS\mongodb\mongod.cfg"` |
| `NotYetInitialized: Replication has not yet been configured` | Replica set `rs0` was not initiated | In `mongosh`, execute: `rs.initiate({_id: "rs0", members: [{_id: 0, host: "127.0.0.1:27017"}]})` |
| `ServiceUnavailable: Couldn't connect to localhost:7687` | Neo4j server is stopped or Java environment missing | Set `$env:JAVA_HOME = "C:\Program Files\Java\jdk-21"` and launch `& "C:\Users\ASUS\neo4j\neo4j-community-5.26.0\bin\neo4j.bat" console` |
| Port 8000 already in use | Previous Uvicorn instance is running in background | Run `Get-Process python | Stop-Process` or specify `--port 8001` |
