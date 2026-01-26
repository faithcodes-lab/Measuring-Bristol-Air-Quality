-- Query B: Mean PM2.5 and VPM2.5 per station for 2022 at 08:00
--
-- OPTIMISATIONS:
-- 1. The Date_Time index is used first to narrow down rows to 2022.
-- 2. FROM_UNIXTIME() converts the integer to a datetime so HOUR() can work.

SELECT
    s.Station_Name,
    AVG(r.PM2_5) AS AVG_PM2_5,
    AVG(r.VPM2_5) AS AVG_VPM2_5
FROM
    reading AS r
JOIN
    station AS s ON r.Site_ID = s.Site_ID
WHERE
    -- Fast Integer Range Filter (Uses Index)
    r.Date_Time >= UNIX_TIMESTAMP('2022-01-01 00:00:00')
    AND r.Date_Time < UNIX_TIMESTAMP('2023-01-01 00:00:00')
    -- Hour Filter (Calculated)
    AND HOUR(FROM_UNIXTIME(r.Date_Time)) = 8
GROUP BY
    s.Site_ID, s.Station_Name
ORDER BY
    s.Station_Name;