import random
import time
from datetime import datetime, timedelta
import requests
import math



def generate_device_sn_range(start_sn, end_sn):
    """
    Generate a list of device_sn within a specified range.

    :param start_sn: The starting device_sn (e.g., CRFTQ23409001890)
    :param end_sn: The ending device_sn (e.g., CRFTQ23409001899)
    :return: A list of device_sn within the range
    """
    # Extract the numeric part of the start and end device_sn
    prefix = start_sn[:-5]  # Common prefix
    start_num = int(start_sn[-5:])  # Numeric part of the start_sn
    end_num = int(end_sn[-5:])  # Numeric part of the end_sn

    # Generate device_sn list
    device_sn_list = [f"{prefix}{str(i).zfill(5)}" for i in range(start_num, end_num + 1)]

    return device_sn_list

# Example usage



def generate_device_info(device_sn):
    # Simulate device info data
    test_device_info = {
        "System Software Version": "GLL-AL30BCN 3.0.0.900(SP51C700E106R370P324)",
        "Wifi Address": "00:1A:2B:3C:4D:5E",
        "Bluetooth Address": "00:1A:2B:3C:4D:5F",
        "IP Address": "192.168.1.1",
        "Network Access Mode": "2",
        "SerialNumber": device_sn,
        "Device Name": "Test Device",
        "IMEI": "123456789012345",
        "batteryLevel": str(random.randint(10, 99)),  # Random battery level between 10 and 99
        "wearState": str(random.choice([0, 1])),  # Random wear state between 0 and 1
        "status": "ACTIVE",
        "customerId": "9",
        "chargingStatus": random.choice(["ENABLE", "NONE"])  # Random charging status between ENABLE and NONE
    }
    return test_device_info

def generate_health_data(device_sn, start_lat=22.544703, start_lon=114.048686):
    """
    Generate health data for a single point in time with updated coordinates.

    :param device_sn: Device serial number
    :param start_lat: Starting latitude
    :param start_lon: Starting longitude
    :return: Health data with updated latitude and longitude
    """
    # Simulate random movement for latitude and longitude
    delta_lat = random.uniform(-0.0002, 0.0002)  # Small random change for latitude
    delta_lon = random.uniform(-0.0002, 0.0002)  # Small random change for longitude
    updated_lat = start_lat + delta_lat
    updated_lon = start_lon + delta_lon

    # Simulate health data
    health_data = {
        "data": {
            "heart_rate": random.randint(75, 110),
            "blood_pressure_systolic": random.randint(110, 130),  # Example range
            "blood_pressure_diastolic": random.randint(70, 85),  # Example range
            "blood_oxygen": random.randint(92, 97),
            "body_temperature": round(random.uniform(36.6, 37.2), 1),
            "cjsj": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "id": device_sn,
            "step": random.randint(10, 50),  # Example steps within 5 seconds
            "distance": round(random.uniform(0.005, 0.02), 4),  # Example distance in km
            "calorie": random.randint(1, 5),  # Example calories burned
            "latitude": round(updated_lat, 6),  # Updated latitude
            "longitude": round(updated_lon, 6),  # Updated longitude
            "altitude": random.randint(10, 50),  # Example altitude
        }
    }

    return health_data

def generate_ellipse_trajectory(center_lat, center_lon, a, b, steps):
    trajectory = []
    for step in range(steps):
        angle = 2 * math.pi * step / steps
        lat = center_lat + a * math.cos(angle)
        lon = center_lon + b * math.sin(angle)
        trajectory.append((lat, lon))
    return trajectory

def generate_linear_trajectory(start_lat, start_lon, end_lat, end_lon, steps):
    """
    Generate a linear trajectory from start to end coordinates.

    :param start_lat: Starting latitude
    :param start_lon: Starting longitude
    :param end_lat: Ending latitude
    :param end_lon: Ending longitude
    :param steps: Number of steps in the trajectory
    :return: List of (latitude, longitude) tuples
    """
    lat_step = (end_lat - start_lat) / steps
    lon_step = (end_lon - start_lon) / steps
    trajectory = [(start_lat + i * lat_step, start_lon + i * lon_step) for i in range(steps)]
    return trajectory

def main():
    start_sn = "A5GTQ24603000537"
    end_sn = "A5GTQ24603000537"
    device_sn_list = generate_device_sn_range(start_sn, end_sn)

    # Print the generated device_sn list
    print(device_sn_list)
    for device_sn in device_sn_list:
        print("device_sn", device_sn)
        # Generate device info data
        device_info_data = generate_device_info(device_sn)
        # Upload device info
        response = requests.post("http://192.168.1.9:5001/upload_device_info", json=device_info_data)

        print("device_info_data", response)

        # Generate health data
        start_lat = 22.544703  # Shenzhen latitude
        start_lon = 114.048686  # Shenzhen longitude
        end_lat = 22.5411  # Shenzhen MixC latitude
        end_lon = 114.0579  # Shenzhen MixC longitude
        steps = 1000  # Number of steps in the trajectory

        trajectory = generate_linear_trajectory(start_lat, start_lon, end_lat, end_lon, steps)

        for step, (lat, lon) in enumerate(trajectory):
            # Generate health data and update position
            health_data = generate_health_data(device_sn, lat, lon)
            print("health_data", health_data)
            response = requests.post("http://192.168.1.9:5001/upload_health_data", json=health_data)

            print(f"Step {step + 1}: {health_data}")

            # Wait for 5 seconds to simulate real-time updates
            time.sleep(5)

        print("\nSimulation complete. Generated trajectory:")
        for point in trajectory:
            print(point)

if __name__ == "__main__":
    main()
