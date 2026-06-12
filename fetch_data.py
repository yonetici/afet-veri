import requests
import json
from datetime import datetime, timedelta

def get_afet_verileri():
    dashboard_data = {
        "son_guncelleme": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "features": []
    }
    
    # 1. NASA EONET API - KÜRESEL DOĞAL AFETLER (Genişletilmiş ve Sınırsız Mod)
    # days=7 parametresi ile uyduların küresel senkronizasyon kaçırmalarını engelliyoruz
    try:
        nasa_url = "https://eonet.gsfc.nasa.gov/api/v3/events?status=open&days=7"
        response = requests.get(nasa_url, timeout=15)
        if response.status_code == 200:
            events = response.json().get("events", [])
            for e in events:
                if not e.get("geometry"):
                    continue
                geom = e["geometry"][-1] # En güncel konum katmanı
                
                # Sadece tekil nokta (Point) olanları değil, Poligon merkezlerini de hesaplayıp ekliyoruz
                coords = None
                if geom["type"] == "Point":
                    coords = geom["coordinates"]
                elif geom["type"] == "Polygon" and geom["coordinates"]:
                    # Poligonlar için basit bir merkez noktası (Centroid) hesaplama
                    poly_coords = geom["coordinates"][0]
                    avg_lng = sum(pt[0] for pt in poly_coords) / len(poly_coords)
                    avg_lat = sum(pt[1] for pt in poly_coords) / len(poly_coords)
                    coords = [avg_lng, avg_lat]

                if coords:
                    dashboard_data["features"].append({
                        "type": "Feature",
                        "properties": {
                            "title": e["title"],
                            "type": e["categories"][0]["id"], # "wildfires", "volcanoes" vb.
                            "link": e.get("link", ""),
                            "date": geom["date"]
                        },
                        "geometry": {
                            "type": "Point",
                            "coordinates": coords
                        }
                    })
    except Exception as e:
        print(f"NASA Küresel Veri Hatası: {e}")

    # 2. GDACS API - GERÇEK ZAMANLI KÜRESEL KRİZLER (BM ve Avrupa Komisyonu Canlı Akışı)
    # GDACS doğrudan dünya genelindeki yüksek ve orta riskli aktif selleri ve siklonları verir.
    try:
        gdacs_url = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/json"
        response = requests.get(gdacs_url, timeout=15)
        if response.status_code == 200:
            events = response.json().get("features", [])
            for e in events:
                props = e["properties"]
                # Sadece aktif olayları filtrele
                if props.get("isactive") == True or props.get("eventtype") in ["TC", "FL", "EQ"]: 
                    hazard_type = "flood"
                    if props.get("eventtype") == "TC": hazard_type = "cyclone"
                    if props.get("eventtype") == "EQ": hazard_type = "volcanoes" # Sismik şokları volkanik/tektonik sınıfa eşliyoruz

                    dashboard_data["features"].append({
                        "type": "Feature",
                        "properties": {
                            "title": props.get("eventname") + " (" + props.get("country", "Global") + ")",
                            "type": hazard_type,
                            "link": f"https://www.gdacs.org/report.aspx?eventid={props.get('eventid')}&eventtype={props.get('eventtype')}",
                            "date": props.get("fromdate")
                        },
                        "geometry": e["geometry"]
                    })
    except Exception as e:
        print(f"GDACS Küresel Veri Hatası: {e}")

    # Dosyayı yaz
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    get_afet_verileri()
