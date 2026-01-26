-- Query A: Highest NOx value in 2022
--
-- OPTIMISATIONS:
-- 1. Uses UNIX_TIMESTAMP() to generate the integer boundaries for 2022.
--    This allows MySQL to use the 'idx_Date_Time' index directly (Range Scan).
-- 2. Filters for NOT NULL to ensure data quality.

SELECT
    FROM_UNIXTIME(r.Date_Time) AS Human_Readable_Date,
    s.Station_Name,
    r.NOx AS Highest_NOx_Reading
FROM
    reading AS r
JOIN
    station AS s ON r.Site_ID = s.Site_ID
WHERE
    -- Filter for 2022 using Integer Timestamps
    r.Date_Time >= UNIX_TIMESTAMP('2022-01-01 00:00:00')
    AND r.Date_Time < UNIX_TIMESTAMP('2023-01-01 00:00:00')
    AND r.NOx IS NOT NULL
ORDER BY
    r.NOx DESC
LIMIT 1;

