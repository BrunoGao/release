USE test;
SELECT device_sn, COUNT(*) as user_count FROM sys_user 
WHERE device_sn IS NOT NULL AND device_sn != '' AND device_sn != '-' 
GROUP BY device_sn 
LIMIT 100;