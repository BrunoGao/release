USE test;
SELECT id, real_name, device_sn, customer_id FROM sys_user WHERE device_sn IS NOT NULL AND device_sn != '' LIMIT 50;