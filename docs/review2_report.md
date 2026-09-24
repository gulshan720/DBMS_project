# Review 2 Report – Online Learning Portal
## A Hybrid MongoDB and Neo4j NoSQL Database System

---

## 1. Introduction

This report documents Review 2 of the Online Learning Portal project, covering the actual database implementation, CRUD operations, and advanced NoSQL features using MongoDB and Neo4j.

## 2. Implementation Summary

### 2.1 Technology Stack

| Component | Technology | Version |
|---|---|---|
| Language | Python | 3.12 |
| Document Database | MongoDB | 7.x / Atlas |
| Graph Database | Neo4j | 5.x / Aura |
| MongoDB Driver | pymongo | 4.18+ |
| Neo4j Driver | neo4j (Python) | 5.19+ |
| Configuration | python-dotenv | 1.0+ |

### 2.2 MongoDB Implementation

**Collections Created (6):**
1. `students` – 10 documents with validation
2. `courses` – 10 documents with category/difficulty constraints
3. `instructors` – 5 documents with rating validation
4. `learning_materials` – 15 documents with type enum
5. `quizzes` – 5 documents with embedded question arrays
6. `progress` – 10 documents with status tracking

**Total: 55 sample documents**

**Advanced Features:**
- JSON Schema validation on all collections
- 5 aggregation pipelines (revenue analysis, student rankings, quiz performance, material stats, completion rates)
- 5 indexes (unique, single-field, compound)
- Multi-document ACID transactions (enrollment workflow, course transfer)

### 2.3 Neo4j Implementation

**Nodes Created (40+):**
- 10 Students, 10 Courses, 5 Instructors, 10 Skills, 5 Categories

**Relationships Created (60+):**
- ENROLLED_IN, COMPLETED, HAS_SKILL, TEACHES, PREREQUISITE_OF, BELONGS_TO, REQUIRES_SKILL

**Advanced Features:**
- Uniqueness constraints and indexes
- Variable-length path traversal
- Shortest path algorithms
- Collaborative filtering recommendations
- Skill gap analysis
- Instructor workload analytics

## 3. CRUD Operations

### MongoDB CRUD
- **Create**: Insert students, courses, instructors
- **Read**: Find by ID, filter by category, list all
- **Update**: Modify emails, update progress percentages
- **Delete**: Remove quizzes, unenroll students

### Neo4j CRUD
- **Create**: Create nodes and relationships
- **Read**: Retrieve students with enrolled courses
- **Update**: Modify node properties
- **Delete**: Remove nodes with cascading relationship cleanup

## 4. Advanced Features

### 4.1 MongoDB Aggregation Pipelines

1. **Average Completion per Course** – `$lookup` + `$group` + `$avg`
2. **Top Students by Completions** – `$match` + `$group` + `$sort` + `$limit`
3. **Course Revenue Analysis** – `$lookup` + `$multiply` + `$sort`
4. **Quiz Performance** – `$unwind` + `$group` + `$avg`
5. **Materials by Type** – `$group` + `$count`

### 4.2 MongoDB Indexing

| Index | Collection | Type | Purpose |
|---|---|---|---|
| email_1 | students | Unique | Fast email lookups |
| category_1 | courses | Single | Filter by category |
| instructor_id_1 | courses | Single | Join with instructors |
| student_id_1_course_id_1 | progress | Compound | Progress lookups |
| course_id_1 | quizzes | Single | Quiz-course association |

### 4.3 MongoDB Transactions

- **Enrollment Transaction**: Atomically creates progress record + updates student's enrolled courses
- **Transfer Transaction**: Atomically unenrolls from one course and enrolls in another

### 4.4 Neo4j Graph Traversal

1. **Prerequisite Chain Discovery** – Variable-length paths `[:PREREQUISITE_OF*]`
2. **Learning Path Finder** – `shortestPath()` between courses
3. **Course Recommendations** – Collaborative filtering via shared enrollments
4. **Student Similarity** – Common course analysis
5. **Instructor Network** – Multi-hop teacher-student relationships

### 4.5 Neo4j Advanced Queries

1. Course popularity ranking
2. Skill gap analysis for students
3. Instructor workload with COLLECT
4. Category statistics with OPTIONAL MATCH
5. Prerequisite chain depth analysis
6. Student completion rate calculation

## 5. How to Run the Demo

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure .env with your database credentials
cp .env.example .env

# 3. Run the interactive demo
python demo/run_demo.py
```

## 6. Observations and Learnings

### MongoDB Strengths
- Flexible schema with optional validation
- Powerful aggregation framework for analytics
- Transaction support for data consistency
- Rich indexing options for performance

### Neo4j Strengths
- Natural representation of relationships
- Efficient graph traversal algorithms
- Expressive Cypher query language
- Ideal for recommendation and path-finding scenarios

### Hybrid Approach Benefits
- MongoDB handles structured data storage efficiently
- Neo4j excels at relationship queries and recommendations
- Combined system provides comprehensive data management
- Each database plays to its strengths

## 7. Conclusion

The hybrid MongoDB + Neo4j approach successfully demonstrates how different NoSQL databases can complement each other in a real-world application. MongoDB provides robust document storage with powerful aggregation and transaction capabilities, while Neo4j enables sophisticated graph queries for recommendations, path finding, and relationship analytics.

---

*Report generated for DBMS NoSQL Project – Review 2*
