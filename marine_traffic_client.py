"""Client per l'interrogazione di dati AIS.

Il client mantiene la compatibilità con l'API proprietaria di Marine Traffic ma
introduce provider alternativi (open-data o simulati) per alimentare il sistema
anche in contesti privi di licenza commerciale.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from datetime import datetime

import requests

from data_providers import (
    MarineTrafficApiProvider,
    SampleDataProvider,
    VesselDataProvider,
)


class MarineTrafficClient:
    """Client per l'API di Marine Traffic o per fonti alternative"""

    BASE_URL = "https://services.marinetraffic.com/api"

    def __init__(
        self,
        api_key: str,
        *,
        data_provider: Optional[VesselDataProvider] = None,
        session: Optional[requests.Session] = None,
    ) -> None:
        """
        Inizializza il client Marine Traffic.

        Args:
            api_key: Chiave API di Marine Traffic (può rimanere fittizia per le
                fonti open-data).
            data_provider: Provider alternativo per il recupero dei dati.
            session: Sessione HTTP riutilizzabile.
        """
        self.api_key = api_key
        self.session = session or requests.Session()
        self.data_provider = data_provider
        self._fallback_provider = SampleDataProvider()
        self._api_provider = None

        if data_provider is None or not isinstance(data_provider, MarineTrafficApiProvider):
            try:
                self._api_provider = MarineTrafficApiProvider(
                    api_key,
                    session=self.session,
                )
            except ValueError:
                self._api_provider = None
        else:
            self._api_provider = data_provider

    def get_vessels_in_port_area(self, port_name: str, radius: int = 50) -> List[Dict]:
        """
        Recupera i vettori nell'area di un porto

        Args:
            port_name: Nome del porto
            radius: Raggio di ricerca in km

        Returns:
            Lista di vettori attivi nell'area
        """
        providers_chain: List[VesselDataProvider] = []

        if self.data_provider is not None:
            providers_chain.append(self.data_provider)
        elif self._api_provider is not None:
            providers_chain.append(self._api_provider)

        if self._api_provider is not None and self._api_provider not in providers_chain:
            providers_chain.append(self._api_provider)

        providers_chain.append(self._fallback_provider)

        last_error: Optional[Exception] = None

        for provider in providers_chain:
            try:
                vessels = provider.fetch_vessels(port_name, radius)
                if vessels:
                    return vessels
            except Exception as exc:
                last_error = exc
                print(
                    "Warning: impossibile recuperare i dati da "
                    f"{provider.__class__.__name__}: {exc}"
                )

        if last_error and providers_chain[-1] is self._fallback_provider:
            print("Info: utilizzo dati simulati come fallback")

        try:
            return self._fallback_provider.fetch_vessels(port_name, radius)
        except Exception:
            return []
    
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
    
    def get_port_traffic_statistics(
        self, port_name: str, days: int = 7, *, vessels: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Calcola statistiche sul traffico portuale

        Args:
            port_name: Nome del porto
            days: Numero di giorni per le statistiche
            vessels: Lista di vettori già recuperata (per evitare chiamate ripetute)

        Returns:
            Statistiche sul traffico
        """
        if vessels is None:
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
        now = datetime.now()

        for vessel in vessels:
            eta_str = vessel.get('eta')
            if eta_str:
                try:
                    eta = datetime.fromisoformat(eta_str)
                    hours_to_arrival = (eta - now).total_seconds() / 3600
                    if hours_to_arrival > 0:
                        total_hours += hours_to_arrival
                        count += 1
                except:
                    continue
        
        return round(total_hours / count, 2) if count > 0 else 0.0
