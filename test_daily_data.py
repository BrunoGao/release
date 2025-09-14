#!/usr/bin/env python3
"""
Test script to check if daily data exists for the test user
"""

import requests
import json

# Test the API with the same parameters
api_url = "http://192.168.1.83:3333/proxy-default/t_user_health_data/page"
params = {
    "page": 1,
    "pageSize": 20,
    "customerId": 0,
    "orgId": "1939964806110937090",
    "userId": "1940034533382479873",
    "startDate": 1751299200000,
    "endDate": 1757865599999
}

try:
    response = requests.get(api_url, params=params)
    response.raise_for_status()
    
    data = response.json()
    
    print("API Response Status:", data.get("code"))
    print("API Response Message:", data.get("message"))
    
    if "data" in data:
        print("Total Records:", data["data"].get("total", 0))
        print("Columns Count:", len(data["data"].get("columns", [])))
        
        records = data["data"].get("records", [])
        if records:
            first_record = records[0]
            print("\nFirst Record Fields:")
            for key in sorted(first_record.keys()):
                print(f"  {key}: {first_record[key]}")
            
            # Check specifically for slow fields
            slow_fields = ["sleep", "sleepData", "work_out", "workoutData", "exercise_daily", "exercise_week"]
            found_slow_fields = [field for field in slow_fields if field in first_record]
            print(f"\nFound slow fields: {found_slow_fields}")
        
        # Print columns info
        columns = data["data"].get("columns", [])
        if columns:
            print(f"\nColumns ({len(columns)} total):")
            for i, col in enumerate(columns[:10]):  # Show first 10 columns
                title = col.get("title", "No title")
                dataIndex = col.get("dataIndex", "No dataIndex")
                print(f"  {i+1}. {title} ({dataIndex})")
            if len(columns) > 10:
                print(f"  ... and {len(columns) - 10} more columns")
    
except Exception as e:
    print(f"Error testing API: {e}")