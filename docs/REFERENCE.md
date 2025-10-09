# API Reference

Questa documentazione riassume le classi principali del progetto. Le docstring di
ciascun componente sono state aggiornate per offrire indicazioni puntuali
sull'utilizzo.

## Modulo `data_providers`

- **`VesselDataProvider`**: classe base astratta per tutti i provider AIS; espone
  il metodo `fetch_vessels` e l'hook `from_env` utilizzato dal registro dinamico.
- **`provider_registry`**: registro centrale che permette di individuare e
  istanziare provider tramite pattern factory. Supporta discovery automatica dei
  moduli in `data_providers/`.
- **`OpenAisFileProvider`**, **`OpenAisApiProvider`**, **`AisHubApiProvider`** e
  **`MarineTrafficApiProvider`**: implementazioni concrete registrate
  dinamicamente. Ogni modulo descrive nei docstring i parametri supportati e il
  comportamento in caso di errori di rete.
- **`SampleDataProvider`**: generatore deterministico utilizzato come fallback
  e per test offline.

## Modulo `marine_traffic_client`

- **`MarineTrafficClient`**: gestisce la catena di provider e applica la cache
  trasparente. I metodi principali sono:
  - `get_vessels_in_port_area`: recupera (o rilegge dalla cache) i vettori
    attivi per un porto.
  - `get_port_traffic_statistics`: calcola statistiche aggregate partendo dai
    dati correnti.

## Modulo `marine_traffic_monitor`

- **`MarineTrafficMonitor`**: orchestratore di alto livello che integra client,
  predittore e clusterizzazione. Offre i metodi `build_data_provider_from_env`
  e `build_data_provider_from_config` per creare provider basandosi su variabili
  d'ambiente o impostazioni GUI.

## Altri Componenti

- **`docs/architecture.md`**: descrive il flusso dati complessivo.
- **`api/server.py`**: scheletro FastAPI con rotte documentate (`/vessels`,
  `/ports`, `/stats`) pronte per essere collegate alla logica del monitor.

Per generare nuovamente questa documentazione è sufficiente riesaminare le
sezioni "Docstring" dei moduli: le descrizioni sono scritte in formato Markdown
compatibile con Sphinx.
