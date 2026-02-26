import requests
import time
from typing import Optional, Tuple

def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """
    Geocode an address string to (lat, lon) using Nominatim (OpenStreetMap).
    Note: Nominatim requires a User-Agent and has a rate limit (1 request/sec).
    """
    url = "https://nominatim.openstreetmap.org/search"
    headers = {
        "User-Agent": "GovExpense-Distance-Calculator/1.0"
    }
    params = {
        "q": address,
        "format": "json",
        "limit": 1
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        data = response.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None

def get_osrm_distance(start_coord: Tuple[float, float], end_coord: Tuple[float, float]) -> Optional[float]:
    """
    Get road distance in kilometers between two coordinates using OSRM.
    """
    # OSRM expects lon,lat
    start_str = f"{start_coord[1]},{start_coord[0]}"
    end_str = f"{end_coord[1]},{end_coord[0]}"
    
    url = f"https://router.project-osrm.org/route/v1/driving/{start_str};{end_str}"
    params = {
        "overview": "false",
        "steps": "false"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data.get("code") == "Ok":
            # Distance is in meters, convert to km
            distance_km = data["routes"][0]["distance"] / 1000.0
            return round(distance_km, 2)
    except Exception as e:
        print(f"OSRM error: {e}")
    return None

def calculate_road_distance(origin: str, destination: str) -> dict:
    """
    Helper to geocode both addresses and find road distance.
    """
    res = {"distance": 0.0, "error": None, "details": ""}
    
    if not origin or not destination:
        res["error"] = "กรุณาระบุต้นทางและปลายทาง"
        return res
        
    start_coord = geocode_address(origin)
    if not start_coord:
        res["error"] = f"ไม่พบพิกัดของ: {origin}"
        return res
        
    # Respect rate limit
    time.sleep(1)
    
    end_coord = geocode_address(destination)
    if not end_coord:
        res["error"] = f"ไม่พบพิกัดของ: {destination}"
        return res
        
    dist = get_osrm_distance(start_coord, end_coord)
    if dist is not None:
        res["distance"] = dist
        res["details"] = f"ระยะทางจาก {origin} ไปยัง {destination}"
    else:
        res["error"] = "ไม่สามารถคำนวณเส้นทางได้"
        
    return res

if __name__ == "__main__":
    # Test
    test_origin = "กรมธนารักษ์ กรุงเทพ"
    test_dest = "เชียงใหม่"
    print(f"Calculating distance from '{test_origin}' to '{test_dest}'...")
    result = calculate_road_distance(test_origin, test_dest)
    print(result)
