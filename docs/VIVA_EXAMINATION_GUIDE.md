# Viva Voce Examination Guide
**Online Learning Portal — Hybrid MongoDB + Neo4j NoSQL Database System**

This guide provides direct, accurate, and confident answers in simple English for defending this DBMS project during your project evaluation.

---

### Q1. What is the problem statement and objective of this project?
**Answer:**  
Modern online learning platforms deal with two very different types of data:
1. **Hierarchical and polymorphic document data:** Detailed student profiles, course syllabi, multimedia learning materials, and nested quiz assessments with score histories.
2. **Highly connected graph relationships:** Prerequisite chains between courses, skills acquired by students, instructor teaching assignments, and collaborative student-to-student peer recommendation paths.

Relational databases struggle here because deeply nested documents cause table explosion, while multi-hop recursive queries (like variable-length prerequisite chains) lead to slow and complex recursive SQL joins.  
Our objective is to build a **Hybrid NoSQL Architecture** combining **MongoDB** (document-oriented store) and **Neo4j** (labeled property graph) to leverage the strengths of both database paradigms behind a unified **FastAPI** backend and responsive web portal.

---

### Q2. Why did you choose both MongoDB and Neo4j instead of just one?
**Answer:**  
No single NoSQL database excels at both flexible document modeling and deep graph traversal:
- **MongoDB** is designed for document storage, rapid horizontal retrieval, flexible schema evolution, and aggregation analytics across millions of records. However, finding transitive prerequisite chains of unknown depth or calculating graph centrality in MongoDB requires expensive recursive `$graphLookup` pipelines that are slow and difficult to maintain.
- **Neo4j** stores nodes and relationships as first-class graph primitives using index-free adjacency. Pointers between related records are physically stored on disk, so traversals take constant time $O(1)$ per hop regardless of total database size. But storing lengthy multimedia articles, detailed student phone records, or embedded quiz question arrays inside Neo4j node properties clutters the graph and degrades traversal cache efficiency.
- **Hybrid Synergy:** MongoDB stores rich entity documents (`students`, `courses`, `instructors`, `learning_materials`, `quizzes`, `progress`), while Neo4j stores connected topologies (`:Student`, `:Course`, `:Instructor`, `:Skill`, `:Category`) and computes graph traversals (prerequisite chains, shortest learning paths, collaborative recommendations).

---

### Q3. Exactly what data is stored in MongoDB vs. Neo4j?
**Answer:**

| Database | Data Stored | Model / Structure |
| :--- | :--- | :--- |
| **MongoDB** | Full document records across 6 collections: `students`, `courses`, `instructors`, `learning_materials`, `quizzes`, `progress`. | JSON/BSON documents with embedded sub-documents (e.g. `quizzes.questions`, `progress.quiz_scores`). |
| **Neo4j** | Graph structure across 5 node labels: `:Student`, `:Course`, `:Instructor`, `:Skill`, `:Category`. | Labeled property graph connected by relationships: `[:ENROLLED_IN]`, `[:COMPLETED]`, `[:HAS_SKILL]`, `[:TEACHES]`, `[:PREREQUISITE_OF]`, `[:BELONGS_TO]`, `[:REQUIRES_SKILL]`. |

---

### Q4. How does the system synchronize data between MongoDB and Neo4j?
**Answer:**  
Our FastAPI backend coordinates **dual-write service operations**:
1. When a student registers via `POST /api/students`, the document is first validated against MongoDB `$jsonSchema` and inserted into the `students` collection. Upon success, the backend immediately executes a parameterized Cypher query (`CREATE (:Student {student_id, name, email})`) in Neo4j.
2. When a student enrolls via `POST /api/students/{id}/enroll`, MongoDB adds the course to `courses_enrolled` and creates a `progress` record, while Neo4j creates an `[:ENROLLED_IN]` relationship.
3. If an entity is deleted (e.g. `DELETE /api/courses/{id}`), MongoDB cascades deletes across `learning_materials`, `quizzes`, `progress`, and pulls the ID from student enrollment arrays; Neo4j executes `MATCH (c:Course {course_id: $id}) DETACH DELETE c` to cleanly remove the node and its relationships.

---

### Q5. How did you implement schema validation in MongoDB?
**Answer:**  
MongoDB is schema-flexible by default, but enterprise applications require data integrity. We implemented **JSON Schema Validation** using `$jsonSchema` at the database level for all 6 collections (`mongo/schema_design.py`).
- It strictly enforces required fields, BSON data types (e.g. `bsonType: "date"` for `enrollment_date`, `bsonType: "number"` for `price`), regex format patterns (e.g. valid email patterns on `students.email`), and allowed enum values (e.g. `difficulty_level: ["Beginner", "Intermediate", "Advanced"]`).
- Any insert or update violating the schema is rejected by the MongoDB engine with a `DocumentValidationFailure`.

---

### Q6. How do indexes improve performance in MongoDB, and how did you verify it?
**Answer:**  
- **Indexes Created:** Unique index on `students.email`, range index on `courses.category`, `courses.instructor_id`, compound index on `progress(student_id, course_id)`, and `quizzes.course_id`.
- **Verification via `explain()`:**
  - Before creating the index on `courses.category`, running `find({"category": "Data Science"}).explain()` outputs stage **`COLLSCAN`** (Collection Scan), which inspects every single document sequentially.
  - After creating the index, the query planner executes **`FETCH -> IXSCAN`** utilizing the `category_1` B-Tree index, isolating matching keys in $O(\log N)$ time and avoiding full scans.

---

### Q7. What MongoDB aggregation pipelines did you implement?
**Answer:**  
We implemented five 5-stage analytical aggregation pipelines (`mongo/aggregation.py` & `/api/analytics/*`):
1. **Course Average Completion:** `$group` by `course_id` with `$avg`, joined with `courses` via `$lookup`, `$unwind`, and `$project` with `$round`.
2. **Top 5 Completing Students:** `$match` `status: "completed"`, `$group` by `student_id`, `$sort` descending, `$limit` 5, `$lookup` student names.
3. **Course Revenue Analysis:** `$unwind` `courses_enrolled`, `$group` enrollment counts, `$lookup` catalog price, `$multiply` price by count.
4. **Quiz Performance Metrics:** `$unwind` `quiz_scores`, `$group` by `quiz_id` calculating `$avg` score and attempt counts.
5. **Learning Materials Distribution:** `$group` by material `type` (`video`, `pdf`, `article`) with `$sum` count.

---

### Q8. How are multi-document transactions implemented, and what happens on failure?
**Answer:**  
In MongoDB, multi-document ACID transactions require a **Replica Set** (`rs0`).
- **Prerequisite:** In standalone mode, MongoDB only guarantees single-document atomicity. By starting MongoDB with `--replSet rs0` and calling `rs.initiate()`, MongoDB maintains an active write-ahead replication log (`oplog.rs`), enabling multi-document snapshot isolation and rollback.
- **Workflow:** In `mongo/transactions.py`, student enrollment and course transfers run inside `with client.start_session() as session: with session.start_transaction():`.
- **Rollback Proof:** We tested deliberate transaction failure (`tests/test_transaction_rollback.py`). If a failure or exception occurs before the transaction completes, MongoDB aborts the transaction and automatically restores documents to their pre-transaction snapshot, ensuring zero orphaned progress records or partial updates.

---

### Q9. What complex graph queries did you write in Neo4j Cypher?
**Answer:**  
In `neo4j_db/graph_traversal.py` and `advanced_queries.py`:
1. **Variable-Length Path Traversal:**  
   `MATCH path = (prereq:Course)-[:PREREQUISITE_OF*1..]->(target:Course {course_id: $cid}) RETURN prereq, length(path) AS depth`  
   Follows prerequisite dependency chains recursively to any depth without hardcoded joins.
2. **Shortest Learning Path:**  
   `MATCH path = shortestPath((start:Course)-[:PREREQUISITE_OF*]->(end:Course)) RETURN [n IN nodes(path) | n.title]`  
   Calculates the minimum prerequisite route a student must complete to reach an advanced topic.
3. **Collaborative Filtering Recommendations:**  
   `MATCH (s:Student {student_id: $sid})-[:ENROLLED_IN]->(c)<-[:ENROLLED_IN]-(peer)-[:ENROLLED_IN]->(rec:Course)`  
   `WHERE NOT (s)-[:ENROLLED_IN]->(rec)`  
   `RETURN rec, count(DISTINCT peer) AS score ORDER BY score DESC`  
   Recommends courses that peers with similar enrollments have taken.
4. **Skill Gap Analysis:**  
   Identifies `(:Skill)` nodes required by courses a student is enrolled in that the student does not yet possess via `[:HAS_SKILL]`.

---

### Q10. What automated testing was performed to verify the system?
**Answer:**  
We built three comprehensive automated test suites:
1. **Offline Unit & Schema Suite (`tests/test_offline_unit.py`):** 17 unit tests verifying Pydantic models, BSON serialization, boundary conditions, and OpenAPI spec. All 17 tests passed (100%).
2. **Live Integration Audit Suite (`tests/test_audit_end_to_end.py`):** 36 live assertions executing full CRUD cycles across both databases, testing dual-write synchronization, cascade deletions, and data integrity. All 36 assertions passed (100%).
3. **Real-Browser Automation Suite (`tests/test_browser_ui.py`):** Drove a headless Chromium/Edge browser through desktop and mobile viewports, performing user registrations, modal interactions, chart renders, and graph traversals. Verified 0 console errors and 0 network failures.
4. **Transaction Rollback Test (`tests/test_transaction_rollback.py`):** Confirmed snapshot rollback upon deliberate error with 0 data leaks.

---

### Q11. What limitations should be disclosed honestly?
**Answer:**  
1. **Two-Phase Commit vs. Eventual Consistency:** Dual writes across MongoDB and Neo4j are coordinated at the application service layer. In a large-scale production system with network partitions, a distributed commit protocol (2PC) or an event-driven message bus (like Apache Kafka with Change Data Capture via Debezium) would be required to guarantee eventual consistency if one database temporarily goes down mid-write.
2. **Single-Node Replica Set:** To enable MongoDB transactions in our local development environment, we run a single-node replica set (`rs0`). Production replica sets typically comprise 3 or more physical nodes for automatic failover and high availability.
3. **Local Neo4j Community Edition:** We utilized Neo4j Community Edition, which supports a single active database at a time and does not include enterprise role-based clustering.
