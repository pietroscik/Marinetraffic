"""
Vessel Clustering
Modulo per il clustering dei vettori per valutazione dei tempi di operatività
"""

from collections import defaultdict
from datetime import datetime
from typing import Dict, List

import numpy as np


class VesselClusterer:
    """Clustering dei vettori per analisi operativa"""
    
    def __init__(self):
        """Inizializza il clusterer"""
        self.clusters = {}
        
    def cluster_by_ship_type(self, vessels: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Raggruppa i vettori per tipo
        
        Args:
            vessels: Lista di vettori
            
        Returns:
            Dizionario con cluster per tipo
        """
        clusters: Dict[str, List[Dict]] = defaultdict(list)

        for vessel in vessels:
            ship_type = vessel.get('ship_type', 'Unknown')
            clusters[ship_type].append(vessel)

        return dict(clusters)
    
    def cluster_by_arrival_time(self, vessels: List[Dict], time_window_hours: int = 6) -> Dict[str, List[Dict]]:
        """
        Raggruppa i vettori per finestra temporale di arrivo
        
        Args:
            vessels: Lista di vettori
            time_window_hours: Dimensione della finestra temporale in ore
            
        Returns:
            Dizionario con cluster per finestra temporale
        """
        clusters: Dict[str, List[Dict]] = defaultdict(list)
        now = datetime.now()

        for vessel in vessels:
            eta_str = vessel.get('eta')
            if not eta_str:
                continue

            try:
                eta = datetime.fromisoformat(eta_str)
                hours_to_arrival = (eta - now).total_seconds() / 3600

                if hours_to_arrival < 0:
                    continue

                window_index = int(hours_to_arrival // time_window_hours)
                window_start = window_index * time_window_hours
                window_end = (window_index + 1) * time_window_hours
                window_key = f"{window_start}-{window_end}h"

                clusters[window_key].append(vessel)
            except Exception:
                continue

        return dict(clusters)
    
    def cluster_by_size(self, vessels: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Raggruppa i vettori per dimensione (piccoli, medi, grandi)
        
        Args:
            vessels: Lista di vettori
            
        Returns:
            Dizionario con cluster per dimensione
        """
        clusters = {
            'small': [],      # < 150m
            'medium': [],     # 150-250m
            'large': []       # > 250m
        }
        
        for vessel in vessels:
            length = vessel.get('length', 0)
            
            if length < 150:
                clusters['small'].append(vessel)
            elif length < 250:
                clusters['medium'].append(vessel)
            else:
                clusters['large'].append(vessel)
        
        return clusters
    
    def estimate_operational_times(self, vessels: List[Dict]) -> Dict[str, Dict]:
        """
        Stima i tempi operativi per ciascun vettore
        
        Args:
            vessels: Lista di vettori
            
        Returns:
            Dizionario con stime dei tempi operativi
        """
        # Tempi operativi medi per tipo di nave (in ore)
        base_operational_times = {
            'Container Ship': 24,
            'Cargo': 18,
            'Tanker': 20,
            'Bulk Carrier': 22,
            'Passenger Ship': 8,
            'Unknown': 16
        }
        
        estimates = {}
        
        for vessel in vessels:
            vessel_id = vessel.get('mmsi', 'unknown')
            ship_type = vessel.get('ship_type', 'Unknown')
            length = vessel.get('length', 200)
            
            # Tempo base
            base_time = base_operational_times.get(ship_type, 16)
            
            # Aggiustamento per dimensione
            size_factor = 1.0
            if length < 150:
                size_factor = 0.8
            elif length > 250:
                size_factor = 1.3
            
            estimated_time = base_time * size_factor
            
            estimates[vessel_id] = {
                'vessel_name': vessel.get('ship_name', 'Unknown'),
                'ship_type': ship_type,
                'estimated_operational_hours': round(estimated_time, 1),
                'estimated_operational_days': round(estimated_time / 24, 1),
                'length': length,
                'confidence': 0.75
            }
        
        return estimates
    
    def analyze_port_capacity(self, vessels: List[Dict], max_berths: int = 10) -> Dict:
        """
        Analizza la capacità portuale e il carico operativo
        
        Args:
            vessels: Lista di vettori in arrivo
            max_berths: Numero massimo di ormeggi disponibili
            
        Returns:
            Analisi della capacità portuale
        """
        # Cluster per finestra temporale
        time_clusters = self.cluster_by_arrival_time(vessels, time_window_hours=12)
        
        # Analizza ogni finestra temporale
        capacity_analysis = {
            'max_berths': max_berths,
            'time_windows': [],
            'overall_utilization': 0.0,
            'potential_congestion': False,
            'utilization_std_dev': 0.0,
            'peak_utilization': 0.0
        }
        
        window_utilizations = []
        
        def sort_key(window_key: str) -> int:
            try:
                return int(window_key.split('-')[0])
            except (ValueError, IndexError):
                return 0

        for window_key in sorted(time_clusters.keys(), key=sort_key):
            window_vessels = time_clusters[window_key]
            vessels_count = len(window_vessels)
            utilization = (vessels_count / max_berths) * 100

            capacity_analysis['time_windows'].append({
                'window': window_key,
                'arriving_vessels': vessels_count,
                'utilization_percent': round(utilization, 1),
                'is_congested': vessels_count > max_berths,
                'vessel_types': self._count_types(window_vessels)
            })
            
            window_utilizations.append(utilization)

        if window_utilizations:
            mean_utilization = float(np.mean(window_utilizations))
            capacity_analysis['overall_utilization'] = round(mean_utilization, 1)
            capacity_analysis['utilization_std_dev'] = round(
                float(np.std(window_utilizations, ddof=0)), 1
            )
            capacity_analysis['peak_utilization'] = round(
                float(np.max(window_utilizations)), 1
            )
            capacity_analysis['potential_congestion'] = any(
                w['is_congested'] for w in capacity_analysis['time_windows']
            )

        return capacity_analysis
    
    def _count_types(self, vessels: List[Dict]) -> Dict[str, int]:
        """Conta i vettori per tipo"""
        type_counts = {}
        for vessel in vessels:
            ship_type = vessel.get('ship_type', 'Unknown')
            type_counts[ship_type] = type_counts.get(ship_type, 0) + 1
        return type_counts
    
    def get_cluster_summary(self, vessels: List[Dict]) -> Dict:
        """
        Genera un riepilogo completo dei cluster
        
        Args:
            vessels: Lista di vettori
            
        Returns:
            Riepilogo dei cluster
        """
        return {
            'total_vessels': len(vessels),
            'by_type': self.cluster_by_ship_type(vessels),
            'by_arrival_time': self.cluster_by_arrival_time(vessels),
            'by_size': self.cluster_by_size(vessels),
            'operational_estimates': self.estimate_operational_times(vessels),
            'capacity_analysis': self.analyze_port_capacity(vessels)
        }
