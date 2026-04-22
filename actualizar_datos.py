import requests
import pandas as pd
import time
from datetime import datetime, timedelta
import os

# CREDENCIALES
API_KEY    = "oexk3vy8kiip3efgnqocb7allnn2hj8a"
API_SECRET = "idcnumtopro6cfezgmsjffl0mg9pnyqo"
STATION_ID = "98494"
ARCHIVO    = "datos_actualizados.csv"

def obtener_clima(fecha, anio):
    ts = int(time.mktime(fecha.timetuple()))
    url = f"https://api.weatherlink.com/v2/historic/{STATION_ID}"
    p = {"api-key": API_KEY, "start-timestamp": ts, "end-timestamp": ts + 86399}
    h = {"X-Api-Secret": API_SECRET}
    try:
        r = requests.get(url, params=p, headers=h)
        if r.status_code == 200:
            d = r.json()
            if 'sensors' in d and len(d['sensors']) > 11:
                s = d['sensors'][11]
                altas = [x['temp_out_hi'] for x in s.get('data', []) if x.get('temp_out_hi') is not None]
                bajas = [x['temp_out_lo'] for x in s.get('data', []) if x.get('temp_out_lo') is not None]
                if altas and bajas:
                    return {
                        "Fecha_Grafico": fecha.replace(year=2000).strftime("%Y-%m-%d"),
                        "Anio": int(anio),
                        "Max_Dia": round((max(altas)-32)*5/9, 1),
                        "Min_Dia": round((min(bajas)-32)*5/9, 1)
                    }
    except: pass
    return None

print("--- INICIANDO PROCESO ---")
if os.path.exists(ARCHIVO):
    df = pd.read_csv(ARCHIVO)
    df["Anio"] = pd.to_numeric(df["Anio"])
    df["Fecha_Grafico"] = pd.to_datetime(df["Fecha_Grafico"])
    
    ultima = df[df["Anio"] == 2026]["Fecha_Grafico"].max()
    inicio = ultima.replace(year=2026) + timedelta(days=1)
    hoy = datetime.now()
    
    nuevos = []
    while inicio.date() < hoy.date():
        print(f"Consultando: {inicio.strftime('%Y-%m-%d')}")
        res = obtener_clima(inicio, 2026)
        if res: nuevos.append(res)
        inicio += timedelta(days=1)
        time.sleep(0.5)
        
    if nuevos:
        df = pd.concat([df, pd.DataFrame(nuevos)], ignore_index=True)
        df.to_csv(ARCHIVO, index=False, encoding="utf-8-sig")
        print(f"✅ FINALIZADO: {len(nuevos)} dias agregados.")
    else:
        print("✔️ TODO AL DIA.")
else:
    print("❌ NO SE ENCONTRA EL CSV")