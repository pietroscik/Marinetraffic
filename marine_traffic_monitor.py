#!/usr/bin/env python3
"""
Marine Traffic Monitor - Applicazione principale
Sistema di monitoraggio in tempo reale del traffico marittimo con predizione arrivi e clustering operativo
"""

import os
import sys
import json
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv

from marine_traffic_client import MarineTrafficClient
from arrival_predictor import ArrivalPredictor
from vessel_clustering import VesselClusterer


class MarineTrafficMonitor:
    """Monitor principale per il sistema Marine Traffic"""
    
    def __init__(self, api_key: str, target_ports: List[str]):
        """
        Inizializza il monitor
        
        Args:
            api_key: Chiave API Marine Traffic
            target_ports: Lista dei porti da monitorare
        """
        self.client = MarineTrafficClient(api_key)
        self.predictor = ArrivalPredictor()
        self.clusterer = VesselClusterer()
        self.target_ports = target_ports
        
    def monitor_port(self, port_name: str) -> Dict:
        """
        Monitora un singolo porto
        
        Args:
            port_name: Nome del porto
            
        Returns:
            Dati completi del monitoraggio
        """
        print(f"\n{'='*80}")
        print(f"MONITORAGGIO PORTO: {port_name}")
        print(f"{'='*80}")
        
        # Recupera vettori attivi
        print(f"\n[1/4] Recupero vettori attivi nell'area di {port_name}...")
        vessels = self.client.get_vessels_in_port_area(port_name)
        print(f"✓ Trovati {len(vessels)} vettori attivi")
        
        # Predizione arrivi
        print(f"\n[2/4] Calcolo predizioni di arrivo in tempo reale...")
        predictions = self.predictor.predict_bulk_arrivals(vessels)
        arrival_windows = self.predictor.calculate_arrival_windows(predictions)
        priority_arrivals = self.predictor.get_priority_arrivals(predictions, hours_threshold=12)
        print(f"✓ Generate {len(predictions)} predizioni")
        print(f"✓ Identificati {len(priority_arrivals)} arrivi prioritari (prossime 12 ore)")
        
        # Clustering
        print(f"\n[3/4] Clustering vettori per analisi operativa...")
        cluster_summary = self.clusterer.get_cluster_summary(vessels)
        capacity_analysis = self.clusterer.analyze_port_capacity(vessels)
        print(f"✓ Clustering completato")
        print(f"✓ Utilizzo porto: {capacity_analysis['overall_utilization']}%")
        
        # Statistiche
        print(f"\n[4/4] Calcolo statistiche traffico portuale...")
        statistics = self.client.get_port_traffic_statistics(port_name)
        print(f"✓ Statistiche calcolate")
        
        return {
            'port': port_name,
            'timestamp': datetime.now().isoformat(),
            'vessels': vessels,
            'predictions': predictions,
            'arrival_windows': arrival_windows,
            'priority_arrivals': priority_arrivals,
            'clustering': {
                'by_type': {k: len(v) for k, v in cluster_summary['by_type'].items()},
                'by_size': {k: len(v) for k, v in cluster_summary['by_size'].items()},
                'operational_estimates': len(cluster_summary['operational_estimates'])
            },
            'capacity_analysis': capacity_analysis,
            'statistics': statistics
        }
    
    def monitor_all_ports(self) -> Dict[str, Dict]:
        """
        Monitora tutti i porti configurati
        
        Returns:
            Dizionario con dati per ogni porto
        """
        results = {}
        
        print("\n" + "="*80)
        print("SISTEMA DI MONITORAGGIO TRAFFICO MARITTIMO")
        print("Autorità Portuale Tirreno Centrale")
        print("="*80)
        print(f"\nPorti monitorati: {', '.join(self.target_ports)}")
        print(f"Data/Ora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        for port in self.target_ports:
            try:
                results[port] = self.monitor_port(port)
            except Exception as e:
                print(f"\n✗ Errore nel monitoraggio di {port}: {e}")
                results[port] = {'error': str(e)}
        
        return results
    
    def print_summary_report(self, results: Dict[str, Dict]):
        """
        Stampa un report riassuntivo
        
        Args:
            results: Risultati del monitoraggio
        """
        print("\n" + "="*80)
        print("REPORT RIASSUNTIVO")
        print("="*80)
        
        total_vessels = 0
        total_priority = 0
        
        for port, data in results.items():
            if 'error' in data:
                continue
                
            vessels_count = len(data.get('vessels', []))
            priority_count = len(data.get('priority_arrivals', []))
            capacity = data.get('capacity_analysis', {})
            
            total_vessels += vessels_count
            total_priority += priority_count
            
            print(f"\n{port.upper()}:")
            print(f"  • Vettori attivi: {vessels_count}")
            print(f"  • Arrivi prioritari (12h): {priority_count}")
            print(f"  • Utilizzo porto: {capacity.get('overall_utilization', 0)}%")
            
            if capacity.get('potential_congestion'):
                print(f"  ⚠ ATTENZIONE: Possibile congestione rilevata")
            
            # Mostra arrivi prioritari
            if priority_count > 0:
                print(f"\n  Prossimi arrivi:")
                for arr in data['priority_arrivals'][:3]:  # Primi 3
                    print(f"    - {arr['vessel_name']} ({arr['ship_type']})")
                    print(f"      ETA: {arr['hours_to_arrival']:.1f} ore, Confidenza: {arr['confidence']*100:.0f}%")
        
        print(f"\n{'='*80}")
        print(f"TOTALE VETTORI MONITORATI: {total_vessels}")
        print(f"TOTALE ARRIVI PRIORITARI: {total_priority}")
        print(f"{'='*80}\n")
    
    def save_results(self, results: Dict[str, Dict], output_dir: str = "data"):
        """
        Salva i risultati su file
        
        Args:
            results: Risultati del monitoraggio
            output_dir: Directory di output
        """
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{output_dir}/marine_traffic_report_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Risultati salvati in: {filename}")


def main():
    """Funzione principale"""
    # Carica configurazione
    load_dotenv()
    
    api_key = os.getenv('MARINETRAFFIC_API_KEY', 'demo_key')
    target_ports_str = os.getenv('TARGET_PORTS', 'Naples,Salerno,Civitavecchia')
    target_ports = [port.strip() for port in target_ports_str.split(',')]
    
    # Inizializza monitor
    monitor = MarineTrafficMonitor(api_key, target_ports)
    
    # Esegui monitoraggio
    results = monitor.monitor_all_ports()
    
    # Stampa report
    monitor.print_summary_report(results)
    
    # Salva risultati
    monitor.save_results(results)
    
    print("\n✓ Monitoraggio completato con successo!\n")


if __name__ == '__main__':
    main()
