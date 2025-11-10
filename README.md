# Measuring Bristol Air Quality

**Module:** Data Management Fundamentals  
**Coursework Year:** 2025/26  
**Author:** Faith Olan-George  
**Institution:** University of the west of england 

---

##Component 1 – Organise and Model the Data
- Designed a normalized **Entity Relationship Diagram (ERD)** in **MySQL Workbench**.  
- Entities: `Constituency`, `Station`, and `Reading`.  
- Relationships:  
  - **One Constituency → Many Stations**  
  - **One Station → Many Readings**  
- The ERD ensures a *no-loss model* and full normalization (3NF).  

Files:  
- `component1_ERD/pollution_db.mwb` — MySQL Workbench model  
- `component1_ERD/pollution-er.png` — Screenshot of the ER diagram  

---

##  Component 2 – Forward Engineer the ER Model
- Forward engineered the ERD into a relational database schema called `pollution_db`.  
- Implemented all primary and foreign keys with appropriate data types.  
- Relationships defined with referential integrity:
  - `ON DELETE RESTRICT ON UPDATE CASCADE` (Constituency → Station)  
  - `ON DELETE CASCADE ON UPDATE CASCADE` (Station → Reading)  

 Files:  
- `component2_SQL/pollution.sql` — SQL schema definition  

---

## Next Steps
- **Component 3:** Crop and cleanse air quality dataset using Python (2015–2023 range).  
- **Component 4:** Populate MySQL database using `phpMyAdmin` or Python script (`import.py`).  

---

## 🧠 Reflection
This project demonstrates the practical application of **data normalization**, **entity-relationship modeling**, and **relational database implementation** for real-world environmental data — aligning with best practices for sustainable city monitoring systems.

---

### Repository Structure
Measuring-Bristol-Air-Quality/
│
├── component1_ERD/
├── component2_SQL/
└── README.md

---

*More components and scripts will be added as the project progresses.*

