"""
Marine Traffic API Client
Modulo per l'interazione con l'API di Marine Traffic per recuperare dati sui vettori
"""

import requests
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class MarineTrafficClient:
    """Client per l'API di Marine Traffic"""
    
    BASE_URL = "https://services.marinetraffic.com/api"
    
    def __init__(self, api_key: str):
        """
        Inizializza il client Marine Traffic
        
        Args:
            api_key: Chiave API di Marine Traffic
        """
        self.api_key = api_key
        self.session = requests.Session()
        
    def get_vessels_in_port_area(self, port_name: str, radius: int = 50) -> List[Dict]:
        """
        Recupera i vettori nell'area di un porto
        
        Args:
            port_name: Nome del porto
            radius: Raggio di ricerca in km
            
        Returns:
            Lista di vettori attivi nell'area
        """
        # Coordinati dei principali porti del Tirreno Centrale
        port_coordinates = {
            'Naples': {'lat': 40.8394, 'lon': 14.2520},
            'Salerno': {'lat': 40.6741, 'lon': 14.7697},
            'Civitavecchia': {'lat': 42.0942, 'lon': 11.7961},
            'Gaeta': {'lat': 41.2131, 'lon': 13.5722},
        }
        
        if port_name not in port_coordinates:
            print(f"Warning: Coordinate non trovate per {port_name}, usando dati simulati")
            return self._generate_sample_vessels(port_name)
        
        coords = port_coordinates[port_name]
        
        # In un'implementazione reale, qui si farebbe la chiamata all'API
        # Per ora generiamo dati di esempio
        return self._generate_sample_vessels(port_name)
    
    def _generate_sample_vessels(self, port_name: str) -> List[Dict]:
        """
        Genera dati di esempio per i vettori
        Questo metodo simula la risposta dell'API per scopi dimostrativi
        """
        import random
        
        vessel_types = ['Cargo', 'Tanker', 'Container Ship', 'Bulk Carrier', 'Passenger Ship']
        vessel_names = ['MEDITERRANEAN STAR', 'OCEAN VOYAGER', 'TYRRHENIAN EXPRESS', 
                       'ATLANTIC HORIZON', 'NEPTUNE CARRIER', 'POSEIDON TRADER',
                       'ADRIATIC QUEEN', 'ITALIA MARINE', 'BLUE WAVE', 'SEA SPIRIT']
        
        vessels = []
        num_vessels = random.randint(3, 8)
        
        for i in range(num_vessels):
            eta_hours = random.randint(1, 48)
            vessels.append({
                'mmsi': 200000000 + random.randint(1000, 9999) * 100 + i,
                'imo': 9000000 + random.randint(100000, 999999),
                'ship_name': random.choice(vessel_names),
                'ship_type': random.choice(vessel_types),
                'destination': port_name,
                'eta': (datetime.now() + timedelta(hours=eta_hours)).isoformat(),
                'speed': round(random.uniform(8.0, 18.0), 1),
                'course': random.randint(0, 360),
                'latitude': 40.5 + random.uniform(-1, 1),
                'longitude': 14.0 + random.uniform(-1, 1),
                'draught': round(random.uniform(6.0, 14.0), 1),
                'length': random.randint(100, 350),
                'width': random.randint(20, 50),
                'status': random.choice(['Under way using engine', 'At anchor', 'Moored'])
            })
        
        return vessels
    
    def get_vessel_details(self, mmsi: int) -> Optional[Dict]:
        """
        Recupera i dettagli di un vettore specifico
        
        Args:
            mmsi: Maritime Mobile Service Identity del vettore
            
        Returns:
            Dettagli del vettore
        """
        # Implementazione simulata
        return {
            'mmsi': mmsi,
            'last_updated': datetime.now().isoformat(),
            'status': 'active'
        }
    
    def get_port_traffic_statistics(self, port_name: str, days: int = 7) -> Dict:
        """
        Calcola statistiche sul traffico portuale
        
        Args:
            port_name: Nome del porto
            days: Numero di giorni per le statistiche
            
        Returns:
            Statistiche sul traffico
        """
        vessels = self.get_vessels_in_port_area(port_name)
        
        return {
            'port': port_name,
            'current_vessels': len(vessels),
            'vessel_types': self._count_vessel_types(vessels),
            'average_eta_hours': self._calculate_average_eta(vessels),
            'timestamp': datetime.now().isoformat()
        }
    
    def _count_vessel_types(self, vessels: List[Dict]) -> Dict[str, int]:
        """Conta i vettori per tipo"""
        type_counts = {}
        for vessel in vessels:
            ship_type = vessel.get('ship_type', 'Unknown')
            type_counts[ship_type] = type_counts.get(ship_type, 0) + 1
        return type_counts
    
    def _calculate_average_eta(self, vessels: List[Dict]) -> float:
        """Calcola l'ETA medio in ore"""
        if not vessels:
            return 0.0
        
        total_hours = 0
        count = 0
        
        for vessel in vessels:
            eta_str = vessel.get('eta')
            if eta_str:
                try:
                    eta = datetime.fromisoformat(eta_str)
                    hours_to_arrival = (eta - datetime.now()).total_seconds() / 3600
                    if hours_to_arrival > 0:
                        total_hours += hours_to_arrival
                        count += 1
                except:
                    continue
        
        return round(total_hours / count, 2) if count > 0 else 0.0
