# Guida Rapida - Marine Traffic Monitor

## Avvio Rapido

### 1. Installazione
```bash
# Clone repository
git clone https://github.com/pietroscik/Marinetraffic.git
cd Marinetraffic

# Installa dipendenze
pip install -r requirements.txt

# Configura environment
cp .env.example .env
```

### 2. Esecuzione
```bash
# Esegui il monitor completo
python marine_traffic_monitor.py

# Esegui esempi di utilizzo
python examples.py
```

## Moduli Disponibili

### 1. Marine Traffic Client (`marine_traffic_client.py`)
Gestisce la comunicazione con l'API Marine Traffic.

```python
from marine_traffic_client import MarineTrafficClient

client = MarineTrafficClient(api_key="your_key")
vessels = client.get_vessels_in_port_area("Naples")
stats = client.get_port_traffic_statistics("Naples")
```

### 2. Arrival Predictor (`arrival_predictor.py`)
Calcola predizioni di arrivo in tempo reale.

```python
from arrival_predictor import ArrivalPredictor

predictor = ArrivalPredictor()
predictions = predictor.predict_bulk_arrivals(vessels)
priority = predictor.get_priority_arrivals(predictions, hours_threshold=12)
```

### 3. Vessel Clusterer (`vessel_clustering.py`)
Raggruppa e analizza vettori per operatività.

```python
from vessel_clustering import VesselClusterer

clusterer = VesselClusterer()
by_type = clusterer.cluster_by_ship_type(vessels)
capacity = clusterer.analyze_port_capacity(vessels)
estimates = clusterer.estimate_operational_times(vessels)
```

## Output

### File JSON
I report vengono salvati in `data/marine_traffic_report_YYYYMMDD_HHMMSS.json` con:
- Elenco vettori per porto
- Predizioni di arrivo
- Finestre temporali
- Analisi clustering
- Statistiche utilizzo porto

### Console
Output formattato con:
- Numero vettori attivi
- Arrivi prioritari (12h)
- Utilizzo porto in %
- Alert congestione

## Personalizzazione

### Modifica Porti
Modifica `.env`:
```env
TARGET_PORTS=Naples,Salerno,Civitavecchia,Gaeta
```

### Intervallo Aggiornamento
```env
UPDATE_INTERVAL=300  # secondi
```

### API Key
Per dati reali da Marine Traffic:
```env
MARINETRAFFIC_API_KEY=your_actual_api_key
```

## Parametri Principali

### Capacità Porto
Default: 10 ormeggi per porto
Modificabile in `marine_traffic_monitor.py`:
```python
capacity = self.clusterer.analyze_port_capacity(vessels, max_berths=15)
```

### Soglia Arrivi Prioritari
Default: 12 ore
Modificabile:
```python
priority = self.predictor.get_priority_arrivals(predictions, hours_threshold=24)
```

### Finestre Temporali Clustering
Default: 6 ore
Modificabile:
```python
windows = self.predictor.calculate_arrival_windows(predictions, window_hours=12)
```

## Troubleshooting

### Errore dipendenze
```bash
pip install --upgrade -r requirements.txt
```

### Errore API
Il sistema usa dati simulati se l'API non è disponibile.
Verifica la tua API key in `.env`.

### Errore permessi
```bash
chmod +x marine_traffic_monitor.py
chmod +x examples.py
```

## Casi d'Uso

### 1. Monitoraggio Giornaliero
```bash
python marine_traffic_monitor.py
```

### 2. Monitoraggio Singolo Porto
Modifica `.env` per includere solo un porto:
```env
TARGET_PORTS=Naples
```

### 3. Alert Congestione
Il sistema rileva automaticamente quando l'utilizzo supera la capacità.

### 4. Pianificazione Operativa
Usa le finestre temporali e i tempi operativi stimati per:
- Allocazione ormeggi
- Pianificazione personale
- Coordinamento operazioni

## Supporto

Per problemi o domande:
- Apri una issue su GitHub
- Consulta il README completo
- Verifica i log in `data/`

## Note

- I dati simulati sono per scopi dimostrativi
- Per dati reali serve una API key valida di Marine Traffic
- Il sistema supporta aggiornamenti continui (loop non implementato)
