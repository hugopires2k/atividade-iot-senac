-- P4 of the traceability script: show the row that just arrived (same seq / value / timestamp as the serial monitor)
SELECT seq, ts, received_at, temperature_c, humidity_pct, light_pct, temp_valid, hum_valid, light_valid, origin
FROM readings WHERE device_id = 'esp32-lab-01' ORDER BY seq DESC LIMIT 5;

-- F1 check: no gaps in the sequence (should return 0 rows when nothing was lost)
SELECT a.seq + 1 AS missing_from
FROM readings a LEFT JOIN readings b ON b.device_id = a.device_id AND b.seq = a.seq + 1
WHERE a.device_id = 'esp32-lab-01' AND b.seq IS NULL
  AND a.seq < (SELECT MAX(seq) FROM readings WHERE device_id = 'esp32-lab-01');

-- F5 check: duplicates (must be 0)
SELECT device_id, seq, COUNT(*) FROM readings GROUP BY device_id, seq HAVING COUNT(*) > 1;

-- Data quality summary for the "Dados" layer
SELECT COUNT(*) AS total,
       SUM(CASE WHEN temp_valid THEN 0 ELSE 1 END) AS invalid_temp,
       SUM(CASE WHEN hum_valid THEN 0 ELSE 1 END) AS invalid_hum,
       SUM(CASE WHEN light_valid THEN 0 ELSE 1 END) AS invalid_light
FROM readings WHERE device_id = 'esp32-lab-01';
