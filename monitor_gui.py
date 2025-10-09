"""Interfaccia grafica per configurare il monitor di Marine Traffic."""

from __future__ import annotations

import json
from typing import Dict, List, Optional

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
except ImportError as exc:  # pragma: no cover - ambiente headless
    raise RuntimeError("Tkinter non è disponibile nell'ambiente corrente") from exc


def _parse_optional_json(value: str, field_name: str) -> Dict[str, str]:
    value = value.strip()
    if not value:
        return {}

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Il campo {field_name} deve contenere un JSON valido") from exc

    if not isinstance(parsed, dict):
        raise ValueError(f"Il campo {field_name} deve essere un oggetto JSON (dizionario)")

    return {str(k): str(v) for k, v in parsed.items()}


def launch_configuration_gui(
    *,
    default_api_key: str,
    default_ports: List[str],
    default_mode: str = 'commercial',
    enable_projections: bool = False,
    projection_horizon: int = 48,
    projection_interval: int = 6,
    default_aishub_username: str = '',
    default_aishub_api_key: str = '',
    default_aishub_output: str = 'json',
    default_aishub_message_format: str = '1',
    default_aishub_compress: bool = False,
    default_aishub_extra_params: Optional[Dict[str, str]] = None,
) -> Dict[str, object]:
    """Mostra una finestra di dialogo per configurare il monitoraggio."""

    result: Dict[str, object] = {'cancelled': True}

    root = tk.Tk()
    root.title("Marine Traffic Monitor - Configurazione")
    root.geometry("620x520")
    root.resizable(False, False)

    main_frame = ttk.Frame(root, padding=16)
    main_frame.pack(fill=tk.BOTH, expand=True)

    mode_var = tk.StringVar(value=default_mode)
    api_key_var = tk.StringVar(value=default_api_key)
    ports_var = tk.StringVar(value=", ".join(default_ports))
    file_var = tk.StringVar()
    url_var = tk.StringVar()
    port_param_var = tk.StringVar()
    headers_var = tk.StringVar()
    params_var = tk.StringVar()
    aishub_username_var = tk.StringVar(value=default_aishub_username)
    aishub_key_var = tk.StringVar(value=default_aishub_api_key)
    aishub_output_var = tk.StringVar(value=default_aishub_output)
    aishub_message_format_var = tk.StringVar(value=default_aishub_message_format)
    aishub_compress_var = tk.BooleanVar(value=default_aishub_compress)
    if default_aishub_extra_params:
        aishub_extra_params_var = tk.StringVar(
            value=json.dumps(default_aishub_extra_params)
        )
    else:
        aishub_extra_params_var = tk.StringVar()
    projections_var = tk.BooleanVar(value=enable_projections)
    horizon_var = tk.StringVar(value=str(projection_horizon))
    interval_var = tk.StringVar(value=str(projection_interval))

    # Sezioni GUI
    ttk.Label(main_frame, text="Seleziona la fonte dati AIS", font=("TkDefaultFont", 11, "bold")).pack(anchor=tk.W)

    source_frame = ttk.Frame(main_frame)
    source_frame.pack(fill=tk.X, pady=(4, 12))

    modes = [
        ("commercial", "API MarineTraffic (licenza commerciale)"),
        ("aishub", "AISHub API (open-data documentata)"),
        ("open_file", "Dataset open-data locale"),
        ("open_http", "Endpoint HTTP open-source"),
        ("simulated", "Dati simulati / demo"),
    ]

    for value, label in modes:
        ttk.Radiobutton(source_frame, text=label, value=value, variable=mode_var).pack(anchor=tk.W)

    # API commerciale
    api_frame = ttk.LabelFrame(main_frame, text="Credenziali API MarineTraffic")
    api_frame.pack(fill=tk.X, pady=6)

    ttk.Label(api_frame, text="Chiave API").grid(row=0, column=0, sticky=tk.W, padx=8, pady=6)
    api_entry = ttk.Entry(api_frame, textvariable=api_key_var, show="*")
    api_entry.grid(row=0, column=1, sticky=tk.EW, padx=8, pady=6)
    api_frame.columnconfigure(1, weight=1)

    # AISHub API
    aishub_frame = ttk.LabelFrame(main_frame, text="AISHub (open-data)")
    aishub_frame.pack(fill=tk.X, pady=6)

    ttk.Label(aishub_frame, text="Username").grid(row=0, column=0, sticky=tk.W, padx=8, pady=4)
    ttk.Entry(aishub_frame, textvariable=aishub_username_var).grid(
        row=0, column=1, sticky=tk.EW, padx=8, pady=4
    )

    ttk.Label(aishub_frame, text="API key (opzionale)").grid(
        row=1, column=0, sticky=tk.W, padx=8, pady=4
    )
    aishub_key_entry = ttk.Entry(aishub_frame, textvariable=aishub_key_var, show="*")
    aishub_key_entry.grid(row=1, column=1, sticky=tk.EW, padx=8, pady=4)

    ttk.Label(aishub_frame, text="Output").grid(row=2, column=0, sticky=tk.W, padx=8, pady=4)
    ttk.Entry(aishub_frame, textvariable=aishub_output_var).grid(
        row=2, column=1, sticky=tk.EW, padx=8, pady=4
    )

    ttk.Label(aishub_frame, text="Formato messaggi").grid(
        row=3, column=0, sticky=tk.W, padx=8, pady=4
    )
    ttk.Entry(aishub_frame, textvariable=aishub_message_format_var).grid(
        row=3, column=1, sticky=tk.EW, padx=8, pady=4
    )

    ttk.Checkbutton(
        aishub_frame,
        text="Risposte compresse",
        variable=aishub_compress_var,
    ).grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=8, pady=4)

    ttk.Label(aishub_frame, text="Parametri extra (JSON)").grid(
        row=5, column=0, sticky=tk.W, padx=8, pady=4
    )
    ttk.Entry(aishub_frame, textvariable=aishub_extra_params_var).grid(
        row=5, column=1, sticky=tk.EW, padx=8, pady=4
    )

    aishub_frame.columnconfigure(1, weight=1)

    # Open data file
    file_frame = ttk.LabelFrame(main_frame, text="Dataset locale (CSV/JSON/GeoJSON)")
    file_frame.pack(fill=tk.X, pady=6)

    ttk.Label(file_frame, text="Percorso file").grid(row=0, column=0, sticky=tk.W, padx=8, pady=6)
    file_entry = ttk.Entry(file_frame, textvariable=file_var)
    file_entry.grid(row=0, column=1, sticky=tk.EW, padx=8, pady=6)
    file_frame.columnconfigure(1, weight=1)

    def browse_file() -> None:
        path = filedialog.askopenfilename(title="Seleziona dataset AIS")
        if path:
            file_var.set(path)

    ttk.Button(file_frame, text="Sfoglia", command=browse_file).grid(row=0, column=2, padx=8, pady=6)

    # Open data endpoint
    http_frame = ttk.LabelFrame(main_frame, text="Endpoint HTTP open-source")
    http_frame.pack(fill=tk.X, pady=6)

    ttk.Label(http_frame, text="URL endpoint").grid(row=0, column=0, sticky=tk.W, padx=8, pady=4)
    url_entry = ttk.Entry(http_frame, textvariable=url_var)
    url_entry.grid(row=0, column=1, sticky=tk.EW, padx=8, pady=4)

    ttk.Label(http_frame, text="Parametro porta (opzionale)").grid(row=1, column=0, sticky=tk.W, padx=8, pady=4)
    port_param_entry = ttk.Entry(http_frame, textvariable=port_param_var)
    port_param_entry.grid(row=1, column=1, sticky=tk.EW, padx=8, pady=4)

    ttk.Label(http_frame, text="Headers (JSON)").grid(row=2, column=0, sticky=tk.W, padx=8, pady=4)
    headers_entry = ttk.Entry(http_frame, textvariable=headers_var)
    headers_entry.grid(row=2, column=1, sticky=tk.EW, padx=8, pady=4)

    ttk.Label(http_frame, text="Query params (JSON)").grid(row=3, column=0, sticky=tk.W, padx=8, pady=4)
    params_entry = ttk.Entry(http_frame, textvariable=params_var)
    params_entry.grid(row=3, column=1, sticky=tk.EW, padx=8, pady=4)

    http_frame.columnconfigure(1, weight=1)

    # Porte target
    ports_frame = ttk.LabelFrame(main_frame, text="Porti da monitorare (separati da virgola)")
    ports_frame.pack(fill=tk.X, pady=6)

    ports_entry = ttk.Entry(ports_frame, textvariable=ports_var)
    ports_entry.pack(fill=tk.X, padx=8, pady=6)

    # Proiezioni
    projections_frame = ttk.LabelFrame(main_frame, text="Analisi serie temporali")
    projections_frame.pack(fill=tk.X, pady=6)

    ttk.Checkbutton(
        projections_frame,
        text="Abilita proiezioni sugli arrivi",
        variable=projections_var,
    ).grid(row=0, column=0, columnspan=2, sticky=tk.W, padx=8, pady=6)

    ttk.Label(projections_frame, text="Orizzonte (ore)").grid(row=1, column=0, sticky=tk.W, padx=8, pady=4)
    horizon_entry = ttk.Entry(projections_frame, textvariable=horizon_var, width=6)
    horizon_entry.grid(row=1, column=1, sticky=tk.W, padx=8, pady=4)

    ttk.Label(projections_frame, text="Intervallo (ore)").grid(row=2, column=0, sticky=tk.W, padx=8, pady=4)
    interval_entry = ttk.Entry(projections_frame, textvariable=interval_var, width=6)
    interval_entry.grid(row=2, column=1, sticky=tk.W, padx=8, pady=4)

    # Pulsanti
    buttons_frame = ttk.Frame(main_frame)
    buttons_frame.pack(fill=tk.X, pady=(12, 0))

    def update_visibility(*_: object) -> None:
        mode = mode_var.get()
        state_api = tk.NORMAL if mode == 'commercial' else tk.DISABLED
        state_aishub = tk.NORMAL if mode == 'aishub' else tk.DISABLED
        state_file = tk.NORMAL if mode == 'open_file' else tk.DISABLED
        state_http = tk.NORMAL if mode == 'open_http' else tk.DISABLED

        for widget in api_frame.winfo_children():
            widget.configure(state=state_api)
        for widget in aishub_frame.winfo_children():
            widget.configure(state=state_aishub)
        for widget in file_frame.winfo_children():
            widget.configure(state=state_file)
        for widget in http_frame.winfo_children():
            widget.configure(state=state_http)

        if state_api == tk.NORMAL:
            api_entry.configure(show="*")
        else:
            api_entry.configure(show="")

        if state_aishub == tk.NORMAL:
            aishub_key_entry.configure(show="*")
        else:
            aishub_key_entry.configure(show="")

    def on_confirm() -> None:
        try:
            horizon = int(horizon_var.get())
            interval = int(interval_var.get())
            if horizon <= 0 or interval <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Valori non validi",
                "Inserisci valori numerici positivi per orizzonte e intervallo.",
            )
            return

        ports = [port.strip() for port in ports_var.get().split(',') if port.strip()]
        if not ports:
            messagebox.showerror("Porti mancanti", "Inserisci almeno un porto da monitorare.")
            return

        mode = mode_var.get()

        payload: Dict[str, object] = {
            'cancelled': False,
            'data_mode': mode,
            'api_key': api_key_var.get().strip(),
            'ports': ports,
            'enable_projections': projections_var.get(),
            'projection_horizon_hours': horizon,
            'projection_interval_hours': interval,
        }

        try:
            if mode == 'aishub':
                if not aishub_username_var.get().strip():
                    messagebox.showerror(
                        "Credenziali mancanti",
                        "Specifica almeno l'username per accedere all'API AISHub.",
                    )
                    return

                payload['ais_hub_username'] = aishub_username_var.get().strip()
                payload['ais_hub_api_key'] = aishub_key_var.get().strip() or None
                payload['ais_hub_output'] = aishub_output_var.get().strip() or 'json'
                payload['ais_hub_message_format'] = (
                    aishub_message_format_var.get().strip() or '1'
                )
                payload['ais_hub_compress'] = bool(aishub_compress_var.get())
                payload['ais_hub_extra_params'] = _parse_optional_json(
                    aishub_extra_params_var.get(), 'Parametri extra'
                )
            elif mode == 'open_file':
                if not file_var.get().strip():
                    messagebox.showerror(
                        "File mancante", "Seleziona un dataset locale per la modalità open-data."
                    )
                    return
                payload['open_data_file'] = file_var.get().strip()
            elif mode == 'open_http':
                if not url_var.get().strip():
                    messagebox.showerror(
                        "URL mancante",
                        "Inserisci l'endpoint HTTP per la modalità open-source.",
                    )
                    return
                payload['open_data_url'] = url_var.get().strip()
                payload['open_data_port_param'] = port_param_var.get().strip() or None
                payload['open_data_headers'] = _parse_optional_json(
                    headers_var.get(), 'Headers'
                )
                payload['open_data_params'] = _parse_optional_json(
                    params_var.get(), 'Query params'
                )
        except ValueError as exc:
            messagebox.showerror("Formato non valido", str(exc))
            return

        result.update(payload)
        root.destroy()

    def on_cancel() -> None:
        result['cancelled'] = True
        root.destroy()

    ttk.Button(buttons_frame, text="Annulla", command=on_cancel).pack(side=tk.RIGHT, padx=4)
    ttk.Button(buttons_frame, text="Avvia monitoraggio", command=on_confirm).pack(
        side=tk.RIGHT, padx=4
    )

    mode_var.trace_add('write', update_visibility)
    update_visibility()

    def on_close() -> None:
        result['cancelled'] = True
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

    return result

