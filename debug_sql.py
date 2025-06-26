#!/usr/bin/env python3
# Test the SQL calculation logic
from datetime import datetime, timedelta
import mysql.connector
from src.config import Config

# Connect to database
conn = mysql.connector.connect(**Config.get_database_config())
cursor = conn.cursor()

# Test the calculation with the specific booking
cursor.execute("""
SELECT 
    s.date, 
    s.starttime, 
    m.duration,
    TIMESTAMP(s.date, SEC_TO_TIME(s.starttime)) as start_timestamp,
    DATE_ADD(TIMESTAMP(s.date, SEC_TO_TIME(s.starttime)), INTERVAL m.duration MINUTE) as end_time_mysql,
    NOW() as current_time
FROM booking b
JOIN showing s ON b.showing_id = s.id
JOIN movie m ON s.movie_id = m.id
WHERE b.id = 28
""")

result = cursor.fetchone()
print('Database calculation:')
print(f'Date: {result[0]}')
print(f'Start time: {result[1]}')
print(f'Duration: {result[2]} minutes')
print(f'Start timestamp: {result[3]}')
print(f'End time (MySQL): {result[4]}')
print(f'Current time: {result[5]}')

# Manual calculation
start_seconds = result[1].total_seconds()
start_hours = int(start_seconds // 3600)
start_minutes = int((start_seconds % 3600) // 60)
print(f'\nManual calculation:')
print(f'Start time in HH:MM: {start_hours:02d}:{start_minutes:02d}')

# Calculate end time manually
start_datetime = datetime.combine(result[0], datetime.min.time()) + timedelta(seconds=start_seconds)
end_datetime = start_datetime + timedelta(minutes=result[2])
print(f'Manual end time: {end_datetime}')

# Test what's going wrong with TIMESTAMP function
cursor.execute("""
SELECT 
    SEC_TO_TIME(s.starttime) as time_converted,
    TIMESTAMP(s.date, SEC_TO_TIME(s.starttime)) as timestamp_result
FROM showing s
WHERE s.id = (SELECT showing_id FROM booking WHERE id = 28)
""")

result2 = cursor.fetchone()
print(f'\nTimestamp function test:')
print(f'SEC_TO_TIME result: {result2[0]}')
print(f'TIMESTAMP result: {result2[1]}')

cursor.close()
conn.close()
