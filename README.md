# Marine Traffic - Sistema di Monitoraggio Real-Time

Sistema avanzato di monitoraggio del traffico marittimo in tempo reale, con predizione degli arrivi e clustering operativo dei vettori. L'obiettivo del progetto è fornire una chiara visione dell'affluenza dei porti italiani con particolare attenzione all'Autorità Portuale del Tirreno Centrale.

## 🎯 Funzionalità Principali

- **Rilevamento Vettori**: Integrazione con piattaforma Marine Traffic per rilevare navi e trump attivi
- **Predizione Real-Time**: Calcolo predittivo degli arrivi con stima di confidenza
- **Clustering Operativo**: Raggruppamento intelligente dei vettori per:
  - Tipo di nave (Container, Tanker, Cargo, etc.)
  - Finestra temporale di arrivo
  - Dimensione della nave
  - Tempi operativi stimati
- **Analisi Capacità Portuale**: Valutazione dell'utilizzo degli ormeggi e rilevamento congestioni
- **Report Dettagliati**: Generazione automatica di report in formato JSON

## 🚢 Porti Monitorati

Il sistema è configurato per monitorare i principali porti del Tirreno Centrale:

- **Napoli** (Naples)
- **Salerno**
- **Civitavecchia**
- **Gaeta**

## 📋 Requisiti

- Python 3.8 o superiore
- Dipendenze specificate in `requirements.txt`

## 🔧 Installazione

1. **Clone del repository**:
```bash
git clone https://github.com/pietroscik/Marinetraffic.git
cd Marinetraffic
```

2. **Installazione delle dipendenze**:
```bash
pip install -r requirements.txt
```

3. **Configurazione**:
```bash
cp .env.example .env
# Modifica .env con la tua API key di Marine Traffic
```

## 🚀 Utilizzo

### Esecuzione Base

```bash
python marine_traffic_monitor.py
```

### Configurazione Personalizzata

Modifica il file `.env` per personalizzare:

```env
# Chiave API Marine Traffic
MARINETRAFFIC_API_KEY=your_api_key_here

# Porti da monitorare (separati da virgola)
TARGET_PORTS=Naples,Salerno,Civitavecchia

# Intervallo di aggiornamento in secondi
UPDATE_INTERVAL=300
```

## 📊 Output

Il sistema genera:

1. **Output a Console**: Report dettagliato in tempo reale con:
   - Numero di vettori attivi per porto
   - Arrivi prioritari nelle prossime 12 ore
   - Percentuale di utilizzo del porto
   - Allerte per potenziali congestioni

2. **File JSON**: Report completo salvato in `data/marine_traffic_report_YYYYMMDD_HHMMSS.json`

### Esempio Output Console

```
================================================================================
SISTEMA DI MONITORAGGIO TRAFFICO MARITTIMO
Autorità Portuale Tirreno Centrale
================================================================================

Porti monitorati: Naples, Salerno, Civitavecchia
Data/Ora: 2024-01-15 14:30:00

================================================================================
MONITORAGGIO PORTO: Naples
================================================================================

[1/4] Recupero vettori attivi nell'area di Naples...
✓ Trovati 6 vettori attivi

[2/4] Calcolo predizioni di arrivo in tempo reale...
✓ Generate 6 predizioni
✓ Identificati 3 arrivi prioritari (prossime 12 ore)

[3/4] Clustering vettori per analisi operativa...
✓ Clustering completato
✓ Utilizzo porto: 60.0%

[4/4] Calcolo statistiche traffico portuale...
✓ Statistiche calcolate

================================================================================
REPORT RIASSUNTIVO
================================================================================

NAPLES:
  • Vettori attivi: 6
  • Arrivi prioritari (12h): 3
  • Utilizzo porto: 60.0%

  Prossimi arrivi:
    - MEDITERRANEAN STAR (Container Ship)
      ETA: 2.5 ore, Confidenza: 85%
    - OCEAN VOYAGER (Tanker)
      ETA: 5.8 ore, Confidenza: 80%
```

## 🏗️ Architettura

Il sistema è composto da 4 moduli principali:

### 1. `marine_traffic_client.py`
Client per l'interazione con l'API di Marine Traffic:
- Recupero dati vettori in area portuale
- Statistiche sul traffico
- Dettagli specifici delle navi

### 2. `arrival_predictor.py`
Modulo di predizione arrivi:
- Calcolo ETA corretto basato su velocità e status
- Stima di confidenza della predizione
- Identificazione arrivi prioritari
- Calcolo finestre temporali di arrivo

### 3. `vessel_clustering.py`
Sistema di clustering operativo:
- Raggruppamento per tipo di nave
- Clustering per finestra temporale
- Classificazione per dimensione
- Stima tempi operativi
- Analisi capacità portuale

### 4. `marine_traffic_monitor.py`
Applicazione principale:
- Orchestrazione dei moduli
- Generazione report
- Output formattato
- Salvataggio risultati

## 📈 Metriche e KPI

Il sistema calcola automaticamente:

- **Numero vettori attivi** per porto
- **ETA medio** in ore
- **Distribuzione per tipo** di nave
- **Utilizzo porto** in percentuale
- **Tempi operativi stimati** per vettore
- **Finestre temporali** di arrivo
- **Allerte congestione** quando l'utilizzo supera la capacità

## 🔐 API Key

Per utilizzare il sistema con dati reali, è necessaria una API key di Marine Traffic:
- Registrati su [Marine Traffic](https://www.marinetraffic.com/)
- Ottieni la tua API key
- Configurala nel file `.env`

**Nota**: Il sistema include dati simulati per scopi dimostrativi e di testing.

## 🛠️ Sviluppo Futuro

Possibili miglioramenti:

- [ ] Integrazione con database per storico
- [ ] Dashboard web interattiva
- [ ] Notifiche push per arrivi critici
- [ ] Machine learning per miglioramento predizioni
- [ ] Integrazione con sistemi di gestione portuale
- [ ] API REST per accesso dati
- [ ] Visualizzazione mappa in tempo reale

## 📝 Licenza

Questo progetto è sviluppato per l'Autorità Portuale del Tirreno Centrale.

## 👥 Contributi

Per contribuire al progetto, aprire una issue o una pull request.

## 📧 Contatti

Per informazioni: [GitHub Repository](https://github.com/pietroscik/Marinetraffic)
