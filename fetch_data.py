import requests
import json
import os
from datetime import datetime

def get_afet_verileri():
    dashboard_data = {
        "son_guncelleme": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "features": []
    }
    
    # 1. NASA EONET API - Aktif Yangınlar ve Volkanlar
    try:
        nasa_url = "https://eonet.gsfc.nasa.gov/api/v3/events?status=open&days=3"
        response = requests.get(nasa_url, timeout=10)
        if response.status_code == 200:
            events = response.json().get("events", [])
            for e in events:
                geom = e["geometry"][-1]
                if geom["type"] == "Point":
                    dashboard_data["features"].append({
                        "type": "Feature",
                        "properties": {
                            "title": e["title"],
                            "type": e["categories"][0]["id"], # "wildfires" veya "volcanoes"
                            "link": e.get("link", ""),
                            "date": geom["date"]
                        },
                        "geometry": {
                            "type": "Point",
                            "coordinates": geom["coordinates"]
                        }
                    })
    except Exception as e:
        print(f"NASA Hatası: {e}")

    # 2. GDACS API - Seller ve Kasırgalar
    try:
        gdacs_url = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/json"
        response = requests.get(gdacs_url, timeout=10)
        if response.status_code == 200:
            events = response.json().get("features", [])
            for e in events:
                props = e["properties"]
                if props.get("eventtype") in ["TC", "FL"]: 
                    dashboard_data["features"].append({
                        "type": "Feature",
                        "properties": {
                            "title": props.get("eventname"),
                            "type": "flood" if props.get("eventtype") == "FL" else "cyclone",
                            "link": props.get("url", {}).get("geometry", ""),
                            "date": props.get("fromdate")
                        },
                        "geometry": e["geometry"]
                    })
    except Exception as e:
        print(f"GDACS Hatası: {e}")

    # Dosyayı diske yaz
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    get_afet_verileri()
