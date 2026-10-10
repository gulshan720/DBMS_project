# Online Learning Portal – A Hybrid MongoDB and Neo4j NoSQL Database System

A DBMS NoSQL project implementing an **Online Learning Portal** using **MongoDB** (document store) and **Neo4j** (graph database) to demonstrate hybrid NoSQL database design, CRUD operations, and advanced features.

## 📋 Project Overview

This project builds a complete backend data layer for an online learning portal, showcasing:

- **MongoDB** for storing structured document data (students, courses, quizzes, progress)
- **Neo4j** for modeling and querying relationships (enrollments, prerequisites, skills, recommendations)

## 🏗️ Project Structure

```
DBMS_project_2026/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies (FastAPI, PyMongo, Neo4j)
├── run_app.py                         # Single command web application runner
├── .env.example                       # Environment variable template
├── .gitignore                         # Git ignore rules
│
├── app/                               # Full-stack Web Portal & REST API
│   ├── main.py                        # FastAPI entry point & route registration
│   ├── routers/                       # Modular REST API endpoints
│   │   ├── health.py                  # Database health checks (/api/health)
│   │   ├── dashboard.py               # Aggregated portal statistics (/api/dashboard)
│   │   ├── students.py                # Student CRUD & enrollment (/api/students)
│   │   ├── courses.py                 # Course catalog & filters (/api/courses)
│   │   ├── materials.py               # Learning materials manager (/api/materials)
│   │   ├── quizzes.py                 # Assessment quizzes & progress (/api/quizzes)
│   │   ├── analytics.py               # 5 MongoDB aggregations & indexing explain
│   │   └── graph.py                   # Neo4j traversals, recs & Cypher analytics
│   ├── services/                      # MongoDB & Neo4j query serialization helpers
│   ├── static/                        # CSS styles, vanilla JS views, SVG icons
│   │   ├── css/style.css              # Modern UI design system
│   │   └── js/                        # View controllers & interactive network graph
│   └── templates/
│       └── index.html                 # Single-page application UI shell
│
├── config/
│   └── db_config.py                   # Database connection helpers
│
├── mongo/
│   ├── schema_design.py               # Collection validators (JSON Schema)
│   ├── seed_data.py                   # 57 sample documents
│   ├── crud_operations.py             # Create, Read, Update, Delete
│   ├── aggregation.py                 # 5 aggregation pipelines
│   ├── indexing.py                    # Index creation & explain plans
│   └── transactions.py               # Multi-document ACID transactions
│
├── neo4j_db/
│   ├── schema_setup.py                # Constraints & indexes
│   ├── seed_data.py                   # 52 nodes, 72 relationships
│   ├── crud_operations.py             # CRUD via Cypher
│   ├── graph_traversal.py             # Path finding & recommendations
│   └── advanced_queries.py            # Pattern matching & analytics
│
├── demo/
│   └── run_demo.py                    # Interactive CLI demo
│
└── docs/
    └── review2_report.md              # Review 2 submission report
```

## 🚀 Setup Instructions

### Prerequisites

- **Python 3.10+** (tested with 3.12)
- **MongoDB** – local install or [MongoDB Atlas](https://www.mongodb.com/atlas) (free tier)
- **Neo4j** – [Neo4j Desktop](https://neo4j.com/download/) or [Neo4j Aura](https://neo4j.com/cloud/aura-free/) (free tier)

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Database Connections

```bash
# Copy the template
cp .env.example .env

# Edit .env with your connection details:
# MONGO_URI=mongodb://localhost:27017
# NEO4J_URI=bolt://localhost:7687
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=your_password
```

### 3. Start Your Databases

**MongoDB** (if running locally):
```bash
mongod --dbpath /path/to/data
```

**Neo4j**: Start via Neo4j Desktop or connect to your Aura instance.

### 4. Run the Full-Stack Web Application

Launch the portal with a single command:

```bash
python run_app.py
```

Then open your browser at:
- **Web Portal:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive REST API Docs (Swagger UI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative API Docs (ReDoc):** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 5. Run the Interactive CLI Demo

Alternatively, you can run the terminal-based interactive demo:

```bash
python demo/run_demo.py
```

Or run individual modules:

```bash
# MongoDB
python mongo/schema_design.py     # Set up collection schemas
python mongo/seed_data.py          # Seed 55+ documents
python mongo/crud_operations.py    # CRUD demo
python mongo/aggregation.py        # Aggregation pipelines
python mongo/indexing.py           # Indexing demo
python mongo/transactions.py       # Transaction demo

# Neo4j
python neo4j_db/schema_setup.py    # Create constraints/indexes
python neo4j_db/seed_data.py       # Seed 50+ nodes
python neo4j_db/crud_operations.py # CRUD demo
python neo4j_db/graph_traversal.py # Graph traversal demo
python neo4j_db/advanced_queries.py # Advanced queries demo
```

## 📊 Database Design

### MongoDB Collections

| Collection | Description | Key Fields |
|---|---|---|
| `students` | Student profiles | student_id, name, email, courses_enrolled |
| `courses` | Course catalog | course_id, title, category, instructor_id, price |
| `instructors` | Instructor profiles | instructor_id, name, specialization, rating |
| `learning_materials` | Course content | material_id, course_id, type, content_url |
| `quizzes` | Assessment quizzes | quiz_id, course_id, questions[], total_points |
| `progress` | Student progress tracking | student_id, course_id, completion_%, quiz_scores[] |

### Neo4j Graph Model

**Nodes:** Student, Course, Instructor, Skill, Category

**Relationships:**
- `(Student)-[:ENROLLED_IN]->(Course)`
- `(Student)-[:COMPLETED]->(Course)`
- `(Student)-[:HAS_SKILL]->(Skill)`
- `(Instructor)-[:TEACHES]->(Course)`
- `(Course)-[:PREREQUISITE_OF]->(Course)`
- `(Course)-[:BELONGS_TO]->(Category)`
- `(Course)-[:REQUIRES_SKILL]->(Skill)`

## ✨ Advanced Features Demonstrated

### MongoDB
- **Aggregation Pipelines**: Revenue analysis, student rankings, quiz performance
- **Indexing**: Single-field, compound, unique indexes with explain() comparison
- **Transactions**: Multi-document ACID transactions for enrollment workflows
- **Schema Validation**: JSON Schema validators on all collections

### Neo4j
- **Graph Traversal**: Variable-length paths, shortest path algorithms
- **Recommendations**: Collaborative filtering for course suggestions
- **Pattern Matching**: Complex Cypher patterns with OPTIONAL MATCH
- **Analytics**: Skill gap analysis, instructor workload, completion rates

## 📝 Sample Data

- **MongoDB**: 57 documents across 6 collections
- **Neo4j**: 52 nodes and 72 relationships
- **Theme**: Indian tech education (realistic names, tech courses)

## 👥 Team

DBMS NoSQL Project – Review 2

## 📄 License

Academic project – for educational purposes only.
