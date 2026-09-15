# Measuring Bristol Air Quality

An end-to-end data management project: designing a normalised relational database for 1.6 million air
quality readings from 19 Bristol monitoring stations, populating it from raw open data, querying it
with SQL, and prototyping the same data in a time-series NoSQL store to compare the two approaches.

---

## The problem

Bristol City Council publishes hourly readings from 19 air quality monitors going back to 1993:
1,603,492 rows across 19 columns, covering NOx, NO2, PM2.5, VPM2.5 and related pollutants. The raw
file is a single flat CSV with no relational structure, inconsistent timestamp formatting, negative
values where sensors failed, and no link between a monitor and the constituency it sits in.

The task was to turn that into something you can actually ask questions of.

---

## Relational design

The data was decomposed into a **"no loss" 3NF schema**, meaning the original file can be fully
reconstructed by joining the tables back together.

| Table | Holds |
|---|---|
| `constituency` | The four Bristol parliamentary constituencies |
| `station` | The 19 monitors, their coordinates, and a foreign key to constituency |
| `reading` | One row per hourly sensor reading, foreign key to station |
| `data_schema` | Field-level definitions for every measure |

Timestamps are stored as integer Unix time with an index on `Date_Time`, which lets date-range
queries run as index range scans rather than full table scans.

### Geospatial enrichment

The source data contains station coordinates but no constituency. Rather than assign these by hand,
`generate_station_sample.py` performs a **point-in-polygon spatial join** against the ONS
*Westminster Parliamentary Constituencies (July 2024) Boundaries* dataset:

1. Parse the national ONS boundary file and filter to Bristol constituencies
2. Load WKT geometries into Shapely polygons
3. Transform station coordinates from WGS84 to British National Grid via pyproj
4. Test each station point against each constituency polygon
5. Emit a station-to-constituency mapping

---

## Pipeline

```
raw CSV (1.6M rows, 1993-2023)
   |
   |  cropped.py      restrict to 2015-01-01 .. 2023-10-22, strip timezone suffixes
   v
   |  import.py       validate types, drop negative measures (except temperature),
   |                  reject malformed rows to import_skipped.csv, bulk load to MySQL
   v
MySQL (pollution_db)
   |
   |  upload_to_questdb.py    denormalised wide-table load
   v
QuestDB (time-series prototype)
```

Cleansing rules applied: `Site_ID` must be an integer, all measures except temperature must be
non-negative, and rows failing either check are written to `import_skipped.csv` rather than silently
dropped, so the rejects are auditable.

---

## Queries

Three analytical queries, in `query-a.sql` through `query-c.sql`:

**A.** Highest recorded NOx reading in 2022, with timestamp and station name.
**B.** Mean PM2.5 and VPM2.5 per station for 2022, restricted to 08:00 readings (peak traffic).
**C.** The same aggregation extended across the full date range.

A and B filter on integer timestamp boundaries so MySQL can use the `Date_Time` index. C deliberately
cannot: filtering by hour-of-day across all years forces a full scan, and the query is commented to
say so rather than hiding it.

---

## NoSQL comparison

The same data was modelled a second time in **QuestDB**, a columnar time-series database, to test
whether a denormalised store suits this workload better.

The argument, set out in `nosql.md`:

- Sensor data is an immutable time-indexed sequence, an OLAP workload, not OLTP
- Row-oriented storage reads whole rows off disk even when a query touches one column; columnar
  storage reads only the columns needed, which suits aggregations like `AVG(NOx)`
- Normalisation guarantees integrity but forces joins; QuestDB's `SYMBOL` type interns repeated
  strings to integers, giving most of the storage saving without the join cost
- Tables are partitioned by time, so date-bounded queries touch only the relevant partitions

QuestDB was chosen over a document store such as MongoDB specifically because the workload is
time-series rather than document-shaped.

---

## Repository contents

**Schema**

- [`pollution.sql`](pollution.sql): complete DDL with tables, primary and foreign keys, and indexes
- [`pollution-er.png`](images/pollution-er.png): entity relationship diagram

**Pipeline**

- [`cropped.py`](cropped.py): date-range cropping and timestamp cleanup
- [`import.py`](import.py): validation, cleansing and bulk load into MySQL
- [`generate_station_sample.py`](generate_station_sample.py): point-in-polygon spatial join of stations to constituencies
- [`upload_to_questdb.py`](upload_to_questdb.py): denormalised load into QuestDB

**Queries**

- [`query-a.sql`](query-a.sql): highest recorded NOx reading in 2022
- [`query-b.sql`](query-b.sql): mean PM2.5 and VPM2.5 per station, 2022 at 08:00
- [`query-c.sql`](query-c.sql): the same aggregation across the full date range

**Write-ups**

- [`report.md`](report.md): design decisions, engineering problems hit, and how they were resolved
- [`nosql.md`](nosql.md): NoSQL model, implementation, and comparison against the relational design

**Reference data**

- [`station.csv`](station.csv): the 19 monitoring stations and their coordinates
- [`constituency.csv`](constituency.csv): the four Bristol parliamentary constituencies
- [`data_schema.csv`](data_schema.csv): field-level definitions for every measure
- [`import_skipped.csv`](import_skipped.csv): rows rejected during validation
- [`images/`](images): ER diagram, query outputs and QuestDB screenshots

---

## Stack

Python (pandas, Shapely, pyproj), MySQL 8, MySQL Workbench, QuestDB, SQL.

---

## Data

The raw and cropped datasets are excluded from this repository for size. The source is Bristol City
Council's continuous air quality monitoring data, available as open data. The constituency boundary
file is ONS *Westminster Parliamentary Constituencies (July 2024) Boundaries UK BFC*.
