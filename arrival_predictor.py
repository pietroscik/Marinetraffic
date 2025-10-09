"""
Arrival Predictor
Modulo per la predizione in tempo reale degli arrivi dei vettori
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np


class ArrivalPredictor:
    """Predittore per gli arrivi dei vettori in tempo reale"""
    
    def __init__(self):
        """Inizializza il predittore"""
        self.historical_data = []
        
    def predict_arrival_time(
        self, vessel: Dict, *, reference_time: Optional[datetime] = None
    ) -> Tuple[datetime, float]:
        """
        Predice il tempo di arrivo di un vettore
        
        Args:
            vessel: Dati del vettore
            
        Returns:
            Tupla (tempo arrivo stimato, confidenza della predizione)
        """
        # Estrai ETA dichiarato
        now = reference_time or datetime.now()

        eta_declared = vessel.get('eta')
        if eta_declared:
            try:
                eta_dt = datetime.fromisoformat(eta_declared)
            except:
                eta_dt = now + timedelta(hours=24)
        else:
            eta_dt = now + timedelta(hours=24)
        
        # Fattori di correzione basati su velocità e condizioni
        speed = vessel.get('speed', 12.0)
        status = vessel.get('status', 'Under way using engine')
        
        # Calcola fattore di correzione
        correction_factor = 1.0
        confidence = 0.85
        
        # Aggiusta in base allo status
        if 'anchor' in status.lower():
            correction_factor += 0.15
            confidence -= 0.10
        elif 'moored' in status.lower():
            correction_factor += 0.25
            confidence -= 0.15
        
        # Aggiusta in base alla velocità
        if speed < 5.0:
            correction_factor += 0.20
            confidence -= 0.15
        elif speed > 15.0:
            correction_factor -= 0.05
            confidence += 0.05
        
        # Applica correzione
        hours_to_arrival = (eta_dt - now).total_seconds() / 3600
        adjusted_hours = hours_to_arrival * correction_factor

        predicted_arrival = now + timedelta(hours=max(0, adjusted_hours))
        
        return predicted_arrival, min(max(confidence, 0.0), 1.0)
    
    def predict_bulk_arrivals(self, vessels: List[Dict]) -> List[Dict]:
        """
        Predice gli arrivi per un gruppo di vettori
        
        Args:
            vessels: Lista di vettori
            
        Returns:
            Lista di predizioni con dettagli
        """
        predictions = []
        
        now = datetime.now()

        for vessel in vessels:
            predicted_time, confidence = self.predict_arrival_time(
                vessel, reference_time=now
            )

            predictions.append({
                'vessel_name': vessel.get('ship_name', 'Unknown'),
                'mmsi': vessel.get('mmsi'),
                'ship_type': vessel.get('ship_type', 'Unknown'),
                'declared_eta': vessel.get('eta'),
                'predicted_eta': predicted_time.isoformat(),
                'predicted_eta_epoch': predicted_time.timestamp(),
                'confidence': round(confidence, 2),
                'hours_to_arrival': round(
                    (predicted_time - now).total_seconds() / 3600, 1
                ),
                'current_speed': vessel.get('speed', 0),
                'status': vessel.get('status', 'Unknown')
            })
        
        # Ordina per tempo di arrivo
        predictions.sort(key=lambda x: x['predicted_eta'])
        
        return predictions
    
    def calculate_arrival_windows(self, predictions: List[Dict], window_hours: int = 6) -> Dict:
        """
        Calcola finestre temporali di arrivo per pianificazione operativa
        
        Args:
            predictions: Lista di predizioni
            window_hours: Dimensione della finestra in ore
            
        Returns:
            Dizionario con finestre temporali e vettori associati
        """
        windows = {}
        
        for pred in predictions:
            try:
                if pred.get('predicted_eta_epoch'):
                    arrival_time = datetime.fromtimestamp(pred['predicted_eta_epoch'])
                else:
                    arrival_time = datetime.fromisoformat(pred['predicted_eta'])
                window_start = arrival_time.replace(minute=0, second=0, microsecond=0)
                window_start -= timedelta(hours=window_start.hour % window_hours)
                
                window_key = window_start.strftime('%Y-%m-%d %H:00')
                
                if window_key not in windows:
                    windows[window_key] = {
                        'start': window_start.isoformat(),
                        'end': (window_start + timedelta(hours=window_hours)).isoformat(),
                        'vessels': []
                    }
                
                windows[window_key]['vessels'].append({
                    'name': pred['vessel_name'],
                    'type': pred['ship_type'],
                    'eta': pred['predicted_eta'],
                    'confidence': pred['confidence']
                })
            except:
                continue
        
        return windows
    
    def get_priority_arrivals(self, predictions: List[Dict], hours_threshold: int = 12) -> List[Dict]:
        """
        Identifica arrivi prioritari nelle prossime ore
        
        Args:
            predictions: Lista di predizioni
            hours_threshold: Soglia in ore per considerare un arrivo prioritario
            
        Returns:
            Lista di arrivi prioritari
        """
        priority_arrivals = []
        
        for pred in predictions:
            if pred['hours_to_arrival'] <= hours_threshold and pred['hours_to_arrival'] >= 0:
                priority_arrivals.append(pred)

        return priority_arrivals

    def generate_time_series_projection(
        self,
        predictions: List[Dict],
        *,
        horizon_hours: int = 48,
        interval_hours: int = 6,
    ) -> Dict:
        """Genera una proiezione aggregata degli arrivi futuri."""

        if horizon_hours <= 0 or interval_hours <= 0:
            raise ValueError(
                "I parametri horizon_hours e interval_hours devono essere positivi"
            )

        now = datetime.now()
        bucket_count = max(1, int(np.ceil(horizon_hours / interval_hours)))

        arrivals: List[datetime] = []
        for pred in predictions:
            eta_value = pred.get('predicted_eta') or pred.get('declared_eta')
            if not eta_value:
                continue
            try:
                eta_dt = datetime.fromisoformat(eta_value)
            except Exception:
                continue

            if eta_dt < now:
                continue

            arrivals.append(eta_dt)

        arrivals.sort()

        buckets: List[Dict] = []
        cumulative = 0

        for index in range(bucket_count):
            window_start = now + timedelta(hours=index * interval_hours)
            window_end = window_start + timedelta(hours=interval_hours)
            count = sum(1 for eta in arrivals if window_start <= eta < window_end)
            cumulative += count

            buckets.append(
                {
                    'window_start': window_start.isoformat(),
                    'window_end': window_end.isoformat(),
                    'expected_arrivals': count,
                    'cumulative_expected': cumulative,
                }
            )

        counts = np.array([bucket['expected_arrivals'] for bucket in buckets], dtype=float)

        trendline = None
        if len(counts) >= 2 and counts.any():
            x = np.arange(len(counts))
            slope, intercept = np.polyfit(x, counts, 1)
            trend_values = intercept + slope * x

            for idx, estimate in enumerate(trend_values):
                buckets[idx]['trend_estimate'] = max(float(estimate), 0.0)

            trendline = {
                'slope': float(slope),
                'intercept': float(intercept),
                'description': (
                    "Trend crescente"
                    if slope > 0
                    else "Trend decrescente"
                    if slope < 0
                    else "Trend stabile"
                ),
            }

        return {
            'generated_at': now.isoformat(),
            'horizon_hours': horizon_hours,
            'interval_hours': interval_hours,
            'buckets': buckets,
            'trendline': trendline,
        }
