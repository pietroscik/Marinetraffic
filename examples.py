#!/usr/bin/env python3
"""
Esempio di utilizzo dei moduli del sistema Marine Traffic
"""

from marine_traffic_client import MarineTrafficClient
from arrival_predictor import ArrivalPredictor
from vessel_clustering import VesselClusterer


def example_basic_usage():
    """Esempio di utilizzo base"""
    print("="*80)
    print("ESEMPIO 1: Utilizzo Base")
    print("="*80)
    
    # Inizializza il client
    client = MarineTrafficClient(api_key="demo_key")
    
    # Recupera vettori per un porto
    print("\n1. Recupero vettori per Napoli...")
    vessels = client.get_vessels_in_port_area("Naples")
    print(f"   Trovati {len(vessels)} vettori")
    
    # Mostra primo vettore
    if vessels:
        v = vessels[0]
        print(f"\n   Esempio vettore:")
        print(f"   - Nome: {v['ship_name']}")
        print(f"   - Tipo: {v['ship_type']}")
        print(f"   - Velocità: {v['speed']} knots")
        print(f"   - ETA: {v['eta']}")


def example_predictions():
    """Esempio di predizioni arrivi"""
    print("\n" + "="*80)
    print("ESEMPIO 2: Predizioni Arrivi")
    print("="*80)
    
    # Inizializza moduli
    client = MarineTrafficClient(api_key="demo_key")
    predictor = ArrivalPredictor()
    
    # Recupera vettori
    vessels = client.get_vessels_in_port_area("Salerno")
    
    # Calcola predizioni
    print(f"\n1. Calcolo predizioni per {len(vessels)} vettori...")
    predictions = predictor.predict_bulk_arrivals(vessels)
    
    # Mostra predizioni
    print(f"\n2. Predizioni generate:")
    for pred in predictions[:3]:  # Prime 3
        print(f"\n   {pred['vessel_name']} ({pred['ship_type']})")
        print(f"   - ETA predetto: {pred['hours_to_arrival']:.1f} ore")
        print(f"   - Confidenza: {pred['confidence']*100:.0f}%")
        print(f"   - Velocità: {pred['current_speed']} knots")
    
    # Arrivi prioritari
    priority = predictor.get_priority_arrivals(predictions, hours_threshold=12)
    print(f"\n3. Arrivi prioritari (prossime 12 ore): {len(priority)}")


def example_clustering():
    """Esempio di clustering"""
    print("\n" + "="*80)
    print("ESEMPIO 3: Clustering Operativo")
    print("="*80)
    
    # Inizializza moduli
    client = MarineTrafficClient(api_key="demo_key")
    clusterer = VesselClusterer()
    
    # Recupera vettori
    vessels = client.get_vessels_in_port_area("Civitavecchia")
    
    # Clustering per tipo
    print(f"\n1. Clustering per tipo di nave:")
    by_type = clusterer.cluster_by_ship_type(vessels)
    for ship_type, ships in by_type.items():
        print(f"   - {ship_type}: {len(ships)} navi")
    
    # Clustering per dimensione
    print(f"\n2. Clustering per dimensione:")
    by_size = clusterer.cluster_by_size(vessels)
    for size, ships in by_size.items():
        print(f"   - {size}: {len(ships)} navi")
    
    # Stima tempi operativi
    print(f"\n3. Stima tempi operativi:")
    estimates = clusterer.estimate_operational_times(vessels)
    for vessel_id, estimate in list(estimates.items())[:3]:  # Primi 3
        print(f"   - {estimate['vessel_name']}:")
        print(f"     Tipo: {estimate['ship_type']}")
        print(f"     Tempo operativo: {estimate['estimated_operational_hours']}h")
        print(f"                     ({estimate['estimated_operational_days']} giorni)")
    
    # Analisi capacità
    print(f"\n4. Analisi capacità portuale:")
    capacity = clusterer.analyze_port_capacity(vessels, max_berths=10)
    print(f"   - Ormeggi disponibili: {capacity['max_berths']}")
    print(f"   - Utilizzo medio: {capacity['overall_utilization']}%")
    print(f"   - Congestione rilevata: {capacity['potential_congestion']}")


def example_statistics():
    """Esempio di statistiche"""
    print("\n" + "="*80)
    print("ESEMPIO 4: Statistiche Traffico")
    print("="*80)
    
    # Inizializza client
    client = MarineTrafficClient(api_key="demo_key")
    
    # Statistiche per porto
    print(f"\n1. Statistiche per Napoli:")
    stats = client.get_port_traffic_statistics("Naples")
    
    print(f"   - Vettori attuali: {stats['current_vessels']}")
    print(f"   - ETA medio: {stats['average_eta_hours']} ore")
    print(f"\n   - Distribuzione per tipo:")
    for ship_type, count in stats['vessel_types'].items():
        print(f"     • {ship_type}: {count}")


if __name__ == '__main__':
    print("\n" + "="*80)
    print("ESEMPI DI UTILIZZO - SISTEMA MARINE TRAFFIC")
    print("="*80 + "\n")
    
    # Esegui esempi
    example_basic_usage()
    example_predictions()
    example_clustering()
    example_statistics()
    
    print("\n" + "="*80)
    print("ESEMPI COMPLETATI")
    print("="*80 + "\n")
