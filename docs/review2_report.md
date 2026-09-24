# Online Learning Portal – A Hybrid MongoDB and Neo4j NoSQL Database System
## Review 2 Implementation & Verification Report

---

### Project Metadata
* **Course:** Database Management Systems (NoSQL Project Lab)
* **Review Stage:** Review 2 (Implementation, CRUD, Advanced Features, & Demonstration)
* **GitHub Repository:** [https://github.com/gulshan720/DBMS_project.git](https://github.com/gulshan720/DBMS_project.git)
* **Architecture:** Polyglot Persistence (Document Store: MongoDB + Graph Store: Neo4j)

---

## 1. Executive Summary & Review 2 Rubric Mapping

Review 2 marks the completion of the database implementation, data seeding, CRUD operations, advanced NoSQL features, and interactive intermediate demonstration for the **Online Learning Portal**. The implementation combines **MongoDB** (document-oriented store for curriculum, student records, multimedia metadata, assessments, and transactional progress) and **Neo4j** (property graph store for prerequisite dependency resolution, collaborative filtering recommendations, skill acquisition tracking, and academic network traversals).

The entire system was verified end-to-end against local instances of MongoDB 7.0.14 (Replica Set `rs0`) and Neo4j Community Server 5.26.0.

### Rubric-to-Implementation Mapping Table

| Rubric Component | Max Marks | Implementation Module | Verified Metrics / Status |
| :--- | :---: | :--- | :--- |
| **Database Implementation** | 2 | `mongo/schema_design.py`<br>`neo4j_db/schema_setup.py` | • 6 MongoDB collections with JSON Schema validation<br>• 5 Neo4j node labels, 5 uniqueness constraints, 2 range indexes |
| **CRUD Operations** | 3 | `mongo/crud_operations.py`<br>`neo4j_db/crud_operations.py` | • Full CRUD on MongoDB (Create, Read, Update, Delete, Enroll, Progress)<br>• Full CRUD on Neo4j (Node/relationship create, traversal read, property update, cascade delete) |
| **Advanced NoSQL Features** | 5 | `mongo/aggregation.py`<br>`mongo/indexing.py`<br>`mongo/transactions.py`<br>`neo4j_db/graph_traversal.py`<br>`neo4j_db/advanced_queries.py` | • 5 MongoDB Aggregation pipelines<br>• Indexing with execution plan verification (`COLLSCAN` → `IXSCAN`)<br>• Multi-document ACID transactions using sessions on `rs0`<br>• 5 Graph traversal algorithms (variable-length paths, `shortestPath`)<br>• 6 Advanced Cypher analytics queries |
| **Dataset Scale** | — | `mongo/seed_data.py`<br>`neo4j_db/seed_data.py` | • **MongoDB:** 57 sample documents (exceeds 50 requirement)<br>• **Neo4j:** 52 nodes, 72 relationships (exceeds 50 requirement) |
| **Intermediate Demonstration** | — | `demo/run_demo.py` | • Fully working menu-driven CLI demo (Option [1], [2], [3] Full Demo verified) |
| **Source Code Repository** | — | GitHub: `gulshan720/DBMS_project` | • Clean, modular git repository with CI-ready configuration and zero credential leaks |

---

## 2. System Architecture & Polyglot Persistence

The application employs a **Polyglot Persistence** pattern where each NoSQL paradigm addresses specific operational characteristics:

```
                          +-------------------------------------+
                          |   Online Learning Portal App / CLI  |
                          +------------------+------------------+
                                             |
                     +-----------------------+-----------------------+
                     |                                               |
                     v                                               v
        +-------------------------+                     +-------------------------+
        |     MongoDB (Document)  |                     |      Neo4j (Graph)      |
        +-------------------------+                     +-------------------------+
        | • Course Catalog        |                     | • Prerequisite Chains   |
        | • User Credentials      |                     | • Skill Dependency Tree |
        | • Quizzes & Questions   |                     | • Recommendation Engine |
        | • Learning Materials    |                     | • Instructor Networks   |
        | • ACID Transactions     |                     | • Social/Peer Cohorts   |
        +-------------------------+                     +-------------------------+
```

### Why MongoDB?
1. **Schema Validation & Polymorphic Data:** Learning materials vary by type (`video`, `pdf`, `article`) with heterogeneous attributes. MongoDB's JSON Schema validation enforces structural integrity while allowing flexible metadata.
2. **Hierarchical Document Nesting:** Quizzes contain embedded arrays of questions and multiple-choice options, eliminating multi-table joins.
3. **High-Throughput Analytics:** Aggregation framework enables real-time reporting of revenues, quiz performances, and completion rates.
4. **ACID Transaction Guarantees:** Multi-document ACID transactions allow atomic enrollments and transfers across `students` and `progress`.

### Why Neo4j?
1. **Index-Free Adjacency:** Traversing deeply nested prerequisite chains ($O(k)$ complexity where $k$ is number of connections, rather than relational recursive joins).
2. **Collaborative Recommendations:** Real-time query execution for `(:Student)-[:ENROLLED_IN]->(:Course)<-[:ENROLLED_IN]-(:Student)` peer cohorts.
3. **Graph Algorithms:** Path discovery (`shortestPath()`) to generate personalized learning curriculums for students.

---

## 3. MongoDB Implementation Details

### 3.1 Collections & JSON Schema Validation
Six collections were created with strict JSON Schema validators (`$jsonSchema`) in `mongo/schema_design.py`:

1. **`students`**: Validates `student_id` (regex `^S[0-9]{3,}$`), `name`, `email` (valid email regex), `phone`, `enrollment_date`, and array of `courses_enrolled`.
2. **`courses`**: Validates `course_id` (regex `^C[0-9]{3,}$`), `title`, `category`, `difficulty_level` (enum: `Beginner`, `Intermediate`, `Advanced`), `duration_hours`, `price` (minimum 0), and `instructor_id`.
3. **`instructors`**: Validates `instructor_id` (regex `^I[0-9]{3,}$`), `name`, `email`, `specialization`, and `rating` (range 0.0 to 5.0).
4. **`learning_materials`**: Validates `material_id` (regex `^M[0-9]{3,}$`), `course_id`, `title`, `type` (enum: `video`, `pdf`, `article`), and `content_url`.
5. **`quizzes`**: Validates `quiz_id` (regex `^Q[0-9]{3,}$`), `course_id`, `title`, `total_points`, and nested `questions` array.
6. **`progress`**: Validates `student_id`, `course_id`, `completion_percentage` (range 0.0 to 100.0), `status` (enum: `not_started`, `in_progress`, `completed`), `last_accessed`, and nested `quiz_scores` array.

### 3.2 Verified Baseline Document Counts

| Collection | Baseline Documents Seeded | Description |
| :--- | :---: | :--- |
| `students` | 10 | Diverse student profiles with enrollment history |
| `courses` | 10 | Full curriculum spanning 5 technical disciplines |
| `instructors` | 5 | Subject matter experts with ratings |
| `learning_materials` | 17 | Multi-format content (videos, PDFs, articles) |
| `quizzes` | 5 | Multi-question assessments with point weightings |
| `progress` | 10 | Granular progress logs with completion percentages |
| **Total** | **57** | **Exceeds the 50 sample document requirement** |

### 3.3 CRUD Operations (`mongo/crud_operations.py`)
All core CRUD primitives were implemented and verified:
* **Create:** `create_student(doc)` inserts documents adhering to schema rules.
* **Read:** `get_student(student_id)` retrieves by business key; `get_courses_by_category(category)` retrieves filtered subsets.
* **Update:** `update_student_email(student_id, email)` modifies attributes; `update_progress(student_id, course_id, pct)` updates percentages and transitions status flags (`completed` if >= 100%).
* **Delete:** `delete_student(student_id)` and `delete_quiz(quiz_id)` safely remove records.

### 3.4 Aggregation Pipelines (`mongo/aggregation.py`)
Five complex pipelines were implemented and executed:

1. **Average Completion Percentage Per Course:**
   ```javascript
   db.progress.aggregate([
     { $group: { _id: "$course_id", avg_completion: { $avg: "$completion_percentage" } } },
     { $lookup: { from: "courses", localField: "_id", foreignField: "course_id", as: "course" } },
     { $unwind: "$course" },
     { $project: { course_id: "$_id", title: "$course.title", average_completion: { $round: ["$avg_completion", 1] } } },
     { $sort: { average_completion: -1 } }
   ])
   ```
   *Execution Output:*
   * `C007 (Ethical Hacking 101)`: 100.0%
   * `C001 (Data Science Fundamentals)`: 95.0%
   * `C004 (React Masterclass)`: 80.0%
   * `C003 (JavaScript for Beginners)`: 75.0%
   * `C005 (AWS Solutions Architect)`: 60.0%

2. **Top Students by Completed Courses:**
   Filters `completion_percentage == 100`, groups by student ID, joins `students`, sorts descending, and limits to top 3.
   *Execution Output:* Aarav Joshi (1), Diya Iyer (1), Aditya Verma (1).

3. **Course Revenue Analysis:**
   Computes enrollment counts per course, joins catalog price, multiplies `price * enrolled_students`, and sorts descending.
   *Execution Output:*
   * `Advanced Machine Learning (C002)`: 2 enrolled × 299.99 = 599.98
   * `Data Science Fundamentals (C001)`: 3 enrolled × 199.99 = 599.97
   * `AWS Solutions Architect (C005)`: 2 enrolled × 249.99 = 499.98

4. **Quiz Performance Analysis:**
   Unwinds student quiz score arrays, computes average scores and attempt volumes per quiz.

5. **Learning Materials Count by Type:**
   Groups content by enum type: `video` (7), `pdf` (5), `article` (5).

### 3.5 Indexing & Query Execution Plans (`mongo/indexing.py`)
To prevent costly full-collection table scans, five indexes were established:
1. `students.email` (Unique Single Field)
2. `courses.category` (Single Field)
3. `courses.instructor_id` (Single Field)
4. `progress.(student_id, course_id)` (Compound Index)
5. `quizzes.course_id` (Single Field)

**Verified Explain Plan Demonstration:**
* **Without Index on `category`:**
  * Winning Plan Stage: **`COLLSCAN`** (scanned entire collection sequentially)
* **With Index `category_1`:**
  * Winning Plan Stage: **`FETCH`** → Input Stage: **`IXSCAN`**
  * Index Used: `category_1` (drastic reduction in execution time and examine ratio)

### 3.6 Multi-Document ACID Transactions (`mongo/transactions.py`)
Configured MongoDB single-node replica set `rs0` to enable transactional semantics.
1. **Enrollment Transaction:**
   * Opens explicit transaction session via `client.start_session()`.
   * Atomically adds `course_id` to `students.courses_enrolled` array (`$addToSet`).
   * Atomically creates initial `progress` document with status `in_progress`.
   * Automatically commits or executes rollback if any constraint or communication error occurs.
2. **Course Transfer Transaction:**
   * Atomically unenrolls student from source course (`$pull`), archives/removes old progress.
   * Enrolls student in target course (`$addToSet`) and creates fresh progress record.

---

## 4. Neo4j Implementation Details

### 4.1 Graph Data Model
The portal graph was designed with 5 Node Labels and 7 Relationship Types:

```
 (Student)-[:ENROLLED_IN]->(Course)-[:BELONGS_TO]->(Category)
     |                         |
     |[:HAS_SKILL]             |[:PREREQUISITE_OF]
     v                         v
  (Skill)<--[:REQUIRES_SKILL]-(Course)<--[:TEACHES]-(Instructor)
     ^                                                 |
     +-----------------[:HAS_SKILL]--------------------+
```

### 4.2 Constraints & Indexes (`neo4j_db/schema_setup.py`)
* **5 Uniqueness Constraints:**
  1. `unique_student_id` ON `(s:Student) ASSERT s.student_id IS UNIQUE`
  2. `unique_course_id` ON `(c:Course) ASSERT c.course_id IS UNIQUE`
  3. `unique_instructor_id` ON `(i:Instructor) ASSERT i.instructor_id IS UNIQUE`
  4. `unique_skill_id` ON `(sk:Skill) ASSERT sk.skill_id IS UNIQUE`
  5. `unique_category_name` ON `(cat:Category) ASSERT cat.name IS UNIQUE`
* **2 Range Performance Indexes:**
  1. `idx_course_category` ON `(c:Course(category))`
  2. `idx_student_email` ON `(s:Student(email))`

### 4.3 Verified Graph Dataset Scale

| Entity / Relationship | Count | Description / Role |
| :--- | :---: | :--- |
| **Student** | 16 | Registered students with enrollment records |
| **Course** | 12 | Curriculum catalog across categories |
| **Instructor** | 5 | Faculty and course authors |
| **Skill** | 14 | Technical proficiencies and competencies |
| **Category** | 5 | Course domain groupings |
| **TOTAL NODES** | **52** | **Exceeds the 50+ graph node requirement** |
| `ENROLLED_IN` | 15 | Active course enrollments |
| `COMPLETED` | 5 | Course completions with grades |
| `HAS_SKILL` | 15 | Student and instructor skill proficiencies |
| `TEACHES` | 12 | Faculty assignments to courses |
| `PREREQUISITE_OF` | 5 | Directed prerequisite dependencies |
| `BELONGS_TO` | 12 | Course-to-Category mappings |
| `REQUIRES_SKILL` | 8 | Course prerequisite skill requirements |
| **TOTAL RELATIONSHIPS**| **72** | **Rich interconnected graph topology** |

### 4.4 Graph Traversal Queries (`neo4j_db/graph_traversal.py`)
1. **Course Prerequisite Chain Discovery (Variable-Length Path):**
   ```cypher
   MATCH path = (prereq:Course)-[:PREREQUISITE_OF*1..]->(target:Course {course_id: $cid})
   RETURN prereq.course_id, prereq.title, length(path) AS depth
   ORDER BY depth DESC
   ```
   *Verified Output for `C004 (Machine Learning A-Z)`:*
   Depth 3: `C001 (Python Fundamentals)` → Depth 2: `C002 (Advanced Python)` → Depth 1: `C003 (Data Science with Python)`.

2. **Learning Path Generator (`shortestPath`):**
   Discovers optimal curriculum between two distinct courses:
   `[C001] Python Fundamentals → [C002] Advanced Python → [C003] Data Science → [C004] Machine Learning`.

3. **Collaborative Filtering Course Recommendations:**
   Recommends new courses based on peer enrollment overlap:
   Student `S001` received recommendations for `C010 (Cybersecurity Fundamentals)` and `C005 (Web Development with Django)`.

4. **Peer Cohort Discovery:**
   Identifies students taking shared courses (e.g., Priya Patel `S002` and Sneha Reddy `S006` shared `C001` with `S001`).

5. **Instructor Network Traversal:**
   Traverses from instructors across courses taught to discover the extended reach of students.

### 4.5 Advanced Cypher Queries (`neo4j_db/advanced_queries.py`)
1. **Course Popularity Ranking:**
   Aggregates both `ENROLLED_IN` and `COMPLETED` relationships with `COUNT(DISTINCT)`.
   *Top Course:* `C001 (Python Fundamentals)` with 6 total students.
2. **Skill Gap Analysis:**
   Identifies skills required by a student's enrolled courses that the student does not currently possess.
   *Verified Result for S001:* Missing `SK005 (Data Analysis)` required by `C003 (Data Science with Python)`.
3. **Instructor Workload & Student Reach:**
   Aggregates course count and distinct students reached per instructor.
   *Verified Result:* Dr. Rajesh Kumar teaches 2 courses with 5 students.
4. **Category Statistics:**
   Computes course counts, average duration, and enrolled students grouped by category.
5. **Prerequisite Chain Depth:**
   Computes maximum chain depth across all courses using `coalesce(max(length(path)), 0)`.
6. **Student Completion Rates:**
   Calculates student completion ratios ($completed / (enrolled + completed) \times 100\%$).

---

## 5. Intermediate Demonstration Execution

The interactive demo CLI (`demo/run_demo.py`) provides an interactive interface to run all Review 2 features.

### How to Run the Demo:
```powershell
# 1. Ensure Python dependencies are installed
pip install -r requirements.txt

# 2. Verify .env file points to running instances:
#    MONGO_URI=mongodb://127.0.0.1:27017/?directConnection=true
#    MONGO_DB_NAME=online_learning_portal
#    NEO4J_URI=bolt://localhost:7687
#    NEO4J_USER=neo4j
#    NEO4J_PASSWORD=<password>

# 3. Launch Demo CLI
python demo/run_demo.py
```

### Menu Structure:
* **`[1]` MongoDB Operations:**
  * Schema setup & validation
  * Data seeding (57 documents)
  * CRUD operations demo
  * 5 Aggregation pipelines
  * Indexing & execution plan comparison
  * Multi-document ACID transactions
  * Full sequential MongoDB demo
* **`[2]` Neo4j Operations:**
  * Schema constraints & range indexes
  * Data seeding (52 nodes, 72 relationships)
  * CRUD operations demo
  * Graph traversal queries
  * Advanced Cypher queries
  * Full sequential Neo4j demo
* **`[3]` Full Project Demo (MongoDB + Neo4j):**
  * Executes all 11 operations sequentially end-to-end.

---

## 6. Security, Reproducibility & Integrity Safeguards

1. **Zero Secret Exposure:**
   * All credentials, passwords, and connection strings are managed via `.env`.
   * `.env` and `.env.*` are excluded in `.gitignore` (verified via `git status --ignored`).
   * A clean template [`.env.example`](../.env.example) is provided for evaluation.
2. **Repository Cleanliness:**
   * No compiled binaries (`mongod.exe`, `mongosh.exe`), database log files, or raw database storage directories (`data/`, `dump/`) are tracked.
3. **Hardware & Resource Optimization:**
   * WiredTiger cache was configured to `cacheSizeGB: 0.25` (256 MB) to prevent out-of-memory thrashing alongside the Neo4j JVM.

---

## 7. Conclusion

Review 2 successfully validates the hybrid NoSQL architecture:
* **MongoDB** delivers structured, schema-validated document management with indexing, aggregation analytics, and ACID transactions.
* **Neo4j** provides high-performance graph traversals for prerequisite resolution, personalized collaborative recommendations, and skill gap identification.

All requirements for Review 2 (database implementation, CRUD operations, advanced features, 50+ sample records/nodes, and intermediate demonstration) are satisfied and verified.

---
*DBMS NoSQL Project – Online Learning Portal (Review 2)*
