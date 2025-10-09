#!/usr/bin/env python3
"""
Marine Traffic Monitor - Applicazione principale
Sistema di monitoraggio in tempo reale del traffico marittimo con predizione arrivi e clustering operativo
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional

from dotenv import load_dotenv

from data_providers import (
    AisHubApiProvider,
    MarineTrafficApiProvider,
    OpenAisApiProvider,
    OpenAisFileProvider,
    SampleDataProvider,
    VesselDataProvider,
)
from marine_traffic_client import MarineTrafficClient
from arrival_predictor import ArrivalPredictor
from vessel_clustering import VesselClusterer


def _parse_positive_int(value: Optional[str], default: int) -> int:
    try:
        parsed = int(str(value))
        return parsed if parsed > 0 else default
    except (TypeError, ValueError):
        return default


class MarineTrafficMonitor:
    """Monitor principale per il sistema Marine Traffic"""
    
    def __init__(
        self,
        api_key: str,
        target_ports: List[str],
        *,
        data_provider: Optional[VesselDataProvider] = None,
        enable_projections: bool = False,
        projection_horizon_hours: int = 48,
        projection_interval_hours: int = 6,
    ):
        """
        Inizializza il monitor
        
        Args:
            api_key: Chiave API Marine Traffic
            target_ports: Lista dei porti da monitorare
        """
        self.client = MarineTrafficClient(api_key, data_provider=data_provider)
        self.predictor = ArrivalPredictor()
        self.clusterer = VesselClusterer()
        self.target_ports = target_ports
        self.enable_projections = enable_projections
        self.projection_horizon_hours = projection_horizon_hours
        self.projection_interval_hours = projection_interval_hours

    @staticmethod
    def _parse_env_mapping(value: Optional[str], env_name: str) -> Optional[Dict[str, str]]:
        if not value:
            return None

        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            print(f"Warning: variabile {env_name} non è un JSON valido: {exc}")
            return None

        if isinstance(parsed, dict):
            return {str(k): str(v) for k, v in parsed.items()}

        print(f"Warning: variabile {env_name} deve essere un oggetto JSON (dizionario)")
        return None

    @classmethod
    def build_data_provider_from_env(cls) -> Optional[VesselDataProvider]:
        """Crea un provider di dati AIS basato sulle variabili d'ambiente."""

        mode = os.getenv('DATA_PROVIDER_MODE', '').lower()

        if mode == 'commercial':
            api_key = os.getenv('MARINETRAFFIC_API_KEY')
            if api_key:
                try:
                    return MarineTrafficApiProvider(api_key)
                except Exception as exc:
                    print(f"Warning: impossibile inizializzare MarineTrafficApiProvider: {exc}")
        elif mode == 'aishub':
            username = os.getenv('AIS_HUB_USERNAME', '').strip()
            if username:
                api_key = os.getenv('AIS_HUB_API_KEY', '').strip() or None
                extra_params = cls._parse_env_mapping(
                    os.getenv('AIS_HUB_EXTRA_PARAMS'),
                    'AIS_HUB_EXTRA_PARAMS',
                )
                output_format = os.getenv('AIS_HUB_OUTPUT', 'json').strip() or 'json'
                message_format = os.getenv('AIS_HUB_MESSAGE_FORMAT', '1').strip() or '1'
                compress = os.getenv('AIS_HUB_COMPRESS', '0').lower() in {'1', 'true', 'yes'}
                try:
                    return AisHubApiProvider(
                        username=username,
                        api_key=api_key,
                        output_format=output_format,
                        message_format=message_format,
                        compress=compress,
                        extra_params=extra_params,
                    )
                except Exception as exc:
                    print(f"Warning: impossibile inizializzare AisHubApiProvider: {exc}")
        elif mode == 'open_file':
            open_data_file = os.getenv('AIS_OPEN_DATA_FILE')
            if open_data_file:
                try:
                    return OpenAisFileProvider(open_data_file)
                except Exception as exc:
                    print(f"Warning: impossibile utilizzare AIS_OPEN_DATA_FILE: {exc}")
        elif mode == 'open_http':
            open_data_url = os.getenv('AIS_OPEN_DATA_URL')
            if open_data_url:
                headers = cls._parse_env_mapping(os.getenv('AIS_OPEN_DATA_HEADERS'), 'AIS_OPEN_DATA_HEADERS')
                params = cls._parse_env_mapping(os.getenv('AIS_OPEN_DATA_PARAMS'), 'AIS_OPEN_DATA_PARAMS')
                port_param = os.getenv('AIS_OPEN_DATA_PORT_PARAM')
                try:
                    return OpenAisApiProvider(
                        open_data_url,
                        headers=headers,
                        params=params,
                        port_query_param=port_param,
                    )
                except Exception as exc:
                    print(f"Warning: impossibile utilizzare AIS_OPEN_DATA_URL: {exc}")
        elif mode == 'simulated':
            return SampleDataProvider()

        username = os.getenv('AIS_HUB_USERNAME')
        if username:
            api_key = os.getenv('AIS_HUB_API_KEY', '').strip() or None
            extra_params = cls._parse_env_mapping(
                os.getenv('AIS_HUB_EXTRA_PARAMS'),
                'AIS_HUB_EXTRA_PARAMS',
            )
            output_format = os.getenv('AIS_HUB_OUTPUT', 'json').strip() or 'json'
            message_format = os.getenv('AIS_HUB_MESSAGE_FORMAT', '1').strip() or '1'
            compress = os.getenv('AIS_HUB_COMPRESS', '0').lower() in {'1', 'true', 'yes'}
            try:
                return AisHubApiProvider(
                    username=username.strip(),
                    api_key=api_key,
                    output_format=output_format,
                    message_format=message_format,
                    compress=compress,
                    extra_params=extra_params,
                )
            except Exception as exc:
                print(f"Warning: impossibile inizializzare AisHubApiProvider: {exc}")

        open_data_file = os.getenv('AIS_OPEN_DATA_FILE')
        if open_data_file:
            try:
                return OpenAisFileProvider(open_data_file)
            except Exception as exc:
                print(f"Warning: impossibile utilizzare AIS_OPEN_DATA_FILE: {exc}")

        open_data_url = os.getenv('AIS_OPEN_DATA_URL')
        if open_data_url:
            headers = cls._parse_env_mapping(os.getenv('AIS_OPEN_DATA_HEADERS'), 'AIS_OPEN_DATA_HEADERS')
            params = cls._parse_env_mapping(os.getenv('AIS_OPEN_DATA_PARAMS'), 'AIS_OPEN_DATA_PARAMS')
            port_param = os.getenv('AIS_OPEN_DATA_PORT_PARAM')

            try:
                return OpenAisApiProvider(
                    open_data_url,
                    headers=headers,
                    params=params,
                    port_query_param=port_param,
                )
            except Exception as exc:
                print(f"Warning: impossibile utilizzare AIS_OPEN_DATA_URL: {exc}")

        return None

    @classmethod
    def build_data_provider_from_config(
        cls, config: Dict[str, object]
    ) -> Optional[VesselDataProvider]:
        """Crea un provider in base alla configurazione proveniente dalla GUI."""

        mode = str(config.get('data_mode', '')).lower()

        if mode == 'commercial':
            api_key = str(config.get('api_key') or '')
            if api_key:
                try:
                    return MarineTrafficApiProvider(api_key)
                except Exception as exc:
                    print(
                        "Warning: impossibile utilizzare la chiave API commerciale: "
                        f"{exc}"
                    )
            return None

        if mode == 'aishub':
            username = str(config.get('ais_hub_username') or '').strip()
            if not username:
                print("Warning: è necessario specificare username per AISHub")
                return None

            api_key = str(config.get('ais_hub_api_key') or '').strip() or None
            raw_params = config.get('ais_hub_extra_params') or {}
            if isinstance(raw_params, dict):
                extra_params = {str(k): str(v) for k, v in raw_params.items()}
            else:
                extra_params = {}

            output_format = str(config.get('ais_hub_output') or 'json').strip() or 'json'
            message_format = (
                str(config.get('ais_hub_message_format') or '1').strip() or '1'
            )
            compress = bool(config.get('ais_hub_compress', False))

            try:
                return AisHubApiProvider(
                    username=username,
                    api_key=api_key,
                    output_format=output_format,
                    message_format=message_format,
                    compress=compress,
                    extra_params=extra_params,
                )
            except Exception as exc:
                print(f"Warning: impostazioni AISHub non valide: {exc}")
            return None

        if mode == 'open_file':
            file_path = config.get('open_data_file')
            if file_path:
                try:
                    return OpenAisFileProvider(str(file_path))
                except Exception as exc:
                    print(f"Warning: file open-data non valido: {exc}")
            return None

        if mode == 'open_http':
            endpoint = config.get('open_data_url')
            if endpoint:
                raw_headers = config.get('open_data_headers') or {}
                raw_params = config.get('open_data_params') or {}
                headers = (
                    {str(k): str(v) for k, v in raw_headers.items()}
                    if isinstance(raw_headers, dict)
                    else {}
                )
                params = (
                    {str(k): str(v) for k, v in raw_params.items()}
                    if isinstance(raw_params, dict)
                    else {}
                )
                port_param = config.get('open_data_port_param')
                try:
                    return OpenAisApiProvider(
                        str(endpoint),
                        headers=headers,
                        params=params,
                        port_query_param=(str(port_param) if port_param else None),
                    )
                except Exception as exc:
                    print(f"Warning: endpoint open-data non valido: {exc}")
            return None

        if mode == 'simulated':
            return SampleDataProvider()

        return None

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

        total_steps = 5 if self.enable_projections else 4
        current_step = 1

        # Recupera vettori attivi
        print(
            f"\n[{current_step}/{total_steps}] Recupero vettori attivi nell'area di {port_name}..."
        )
        vessels = self.client.get_vessels_in_port_area(port_name)
        print(f"✓ Trovati {len(vessels)} vettori attivi")

        current_step += 1

        # Predizione arrivi
        print(f"\n[{current_step}/{total_steps}] Calcolo predizioni di arrivo in tempo reale...")
        predictions = self.predictor.predict_bulk_arrivals(vessels)
        arrival_windows = self.predictor.calculate_arrival_windows(predictions)
        priority_arrivals = self.predictor.get_priority_arrivals(predictions, hours_threshold=12)
        print(f"✓ Generate {len(predictions)} predizioni")
        print(f"✓ Identificati {len(priority_arrivals)} arrivi prioritari (prossime 12 ore)")

        current_step += 1

        # Clustering
        print(f"\n[{current_step}/{total_steps}] Clustering vettori per analisi operativa...")
        cluster_summary = self.clusterer.get_cluster_summary(vessels)
        capacity_analysis = self.clusterer.analyze_port_capacity(vessels)
        print(f"✓ Clustering completato")
        print(f"✓ Utilizzo porto: {capacity_analysis['overall_utilization']}%")

        current_step += 1

        # Statistiche
        print(f"\n[{current_step}/{total_steps}] Calcolo statistiche traffico portuale...")
        statistics = self.client.get_port_traffic_statistics(port_name, vessels=vessels)
        print(f"✓ Statistiche calcolate")

        series_projection: Optional[Dict] = None

        if self.enable_projections:
            current_step += 1
            print(
                f"\n[{current_step}/{total_steps}] Generazione proiezioni serie temporali arrivi..."
            )
            try:
                series_projection = self.predictor.generate_time_series_projection(
                    predictions,
                    horizon_hours=self.projection_horizon_hours,
                    interval_hours=self.projection_interval_hours,
                )
                print(
                    "✓ Proiezioni generate su "
                    f"{self.projection_horizon_hours} ore (passo {self.projection_interval_hours}h)"
                )
            except Exception as exc:
                print(f"Warning: impossibile generare le proiezioni delle serie temporali: {exc}")

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
            'statistics': statistics,
            'series_projection': series_projection,
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
            projection = data.get('series_projection') or {}

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

            buckets = projection.get('buckets') or []
            if buckets:
                print(f"\n  Proiezioni arrivi (prime finestre):")
                for bucket in buckets[:3]:
                    start = datetime.fromisoformat(bucket['window_start'])
                    end = datetime.fromisoformat(bucket['window_end'])
                    print(
                        f"    • {start.strftime('%d/%m %H:%M')} - {end.strftime('%H:%M')}: "
                        f"{bucket['expected_arrivals']} arrivi previsti"
                    )
                trendline = projection.get('trendline')
                if trendline:
                    print(
                        "  • Trend stimato: "
                        f"{trendline['description']} (slope {trendline['slope']:.2f})"
                    )

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
    target_ports = [port.strip() for port in target_ports_str.split(',') if port.strip()]

    projection_horizon_hours = _parse_positive_int(
        os.getenv('PROJECTION_HORIZON_HOURS'), 48
    )
    projection_interval_hours = _parse_positive_int(
        os.getenv('PROJECTION_INTERVAL_HOURS'), 6
    )
    enable_projections = os.getenv('ENABLE_SERIES_PROJECTIONS', 'false').lower() in {
        '1',
        'true',
        'yes',
    }

    data_provider = MarineTrafficMonitor.build_data_provider_from_env()

    config = None
    use_gui = os.getenv('MARINETRAFFIC_NO_GUI', 'false').lower() not in {
        '1',
        'true',
        'yes',
    }

    aishub_extra_params_env = MarineTrafficMonitor._parse_env_mapping(
        os.getenv('AIS_HUB_EXTRA_PARAMS'), 'AIS_HUB_EXTRA_PARAMS'
    ) or {}

    aishub_defaults = {
        'username': os.getenv('AIS_HUB_USERNAME', '').strip(),
        'api_key': os.getenv('AIS_HUB_API_KEY', '').strip(),
        'output': os.getenv('AIS_HUB_OUTPUT', 'json').strip() or 'json',
        'message_format': os.getenv('AIS_HUB_MESSAGE_FORMAT', '1').strip() or '1',
        'compress': os.getenv('AIS_HUB_COMPRESS', '0').lower() in {'1', 'true', 'yes'},
        'extra_params': aishub_extra_params_env,
    }

    if use_gui:
        if isinstance(data_provider, OpenAisFileProvider):
            default_mode = 'open_file'
        elif isinstance(data_provider, OpenAisApiProvider):
            default_mode = 'open_http'
        elif isinstance(data_provider, AisHubApiProvider):
            default_mode = 'aishub'
        elif isinstance(data_provider, SampleDataProvider):
            default_mode = 'simulated'
        else:
            default_mode = 'commercial'

        try:
            from monitor_gui import launch_configuration_gui

            config = launch_configuration_gui(
                default_api_key=api_key,
                default_ports=target_ports,
                default_mode=default_mode,
                enable_projections=enable_projections,
                projection_horizon=projection_horizon_hours,
                projection_interval=projection_interval_hours,
                default_aishub_username=aishub_defaults['username'],
                default_aishub_api_key=aishub_defaults['api_key'],
                default_aishub_output=aishub_defaults['output'],
                default_aishub_message_format=aishub_defaults['message_format'],
                default_aishub_compress=aishub_defaults['compress'],
                default_aishub_extra_params=aishub_defaults['extra_params'],
            )
        except Exception as exc:
            print(f"Warning: interfaccia grafica non disponibile ({exc})")
            config = None

    if config:
        if config.get('cancelled'):
            print("\nMonitoraggio annullato dall'utente.")
            return

        api_key = config.get('api_key') or api_key
        selected_ports = config.get('ports')
        if selected_ports:
            target_ports = [port for port in selected_ports if port]

        provider_from_gui = MarineTrafficMonitor.build_data_provider_from_config(config)
        if provider_from_gui is not None or config.get('data_mode') == 'simulated':
            data_provider = provider_from_gui

        enable_projections = bool(config.get('enable_projections', enable_projections))
        projection_horizon_hours = _parse_positive_int(
            config.get('projection_horizon_hours'), projection_horizon_hours
        )
        projection_interval_hours = _parse_positive_int(
            config.get('projection_interval_hours'), projection_interval_hours
        )

    if not target_ports:
        print("✗ Nessun porto configurato. Uscita.")
        return

    if data_provider is None:
        data_source_label = "API MarineTraffic (commerciale) con fallback automatici"
    elif isinstance(data_provider, AisHubApiProvider):
        data_source_label = "AISHub API (open-data)"
    elif isinstance(data_provider, SampleDataProvider):
        data_source_label = "dati simulati (SampleDataProvider)"
    else:
        data_source_label = data_provider.__class__.__name__

    print(f"\n✓ Fonte dati AIS: {data_source_label}")

    monitor = MarineTrafficMonitor(
        api_key,
        target_ports,
        data_provider=data_provider,
        enable_projections=enable_projections,
        projection_horizon_hours=projection_horizon_hours,
        projection_interval_hours=projection_interval_hours,
    )

    # Esegui monitoraggio
    results = monitor.monitor_all_ports()

    # Stampa report
    monitor.print_summary_report(results)
    
    # Salva risultati
    monitor.save_results(results)
    
    print("\n✓ Monitoraggio completato con successo!\n")


if __name__ == '__main__':
    main()
