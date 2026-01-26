-- Query C: Mean PM2.5 and VPM2.5 per station for ALL data at 08:00
--
-- Note: This query scans the full table because we are filtering
-- by Hour across all years.

SELECT
    s.Station_Name,
    AVG(r.PM2_5) AS AVG_PM2_5,
    AVG(r.VPM2_5) AS AVG_VPM2_5
FROM
    reading AS r
JOIN
    station AS s ON r.Site_ID = s.Site_ID
WHERE
    -- Convert Integer Timestamp to DateTime to check the Hour
    HOUR(FROM_UNIXTIME(r.Date_Time)) = 8
GROUP BY
    s.Site_ID, s.Station_Name
ORDER BY
    s.Station_Name;