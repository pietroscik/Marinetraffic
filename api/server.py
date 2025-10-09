"""FastAPI skeleton exposing cached AIS data endpoints."""
from __future__ import annotations

from typing import Dict, List

from fastapi import FastAPI

app = FastAPI(title="Marine Traffic Monitor API", version="0.1.0")


@app.get("/vessels", summary="Elenco dei vettori correnti")
def list_vessels() -> Dict[str, List[Dict]]:
    """Restituisce un placeholder con i vettori disponibili.

    In una futura integrazione questo endpoint potrà leggere i dati dalla cache
    JSON (`data/cache/`) oppure eseguire una query live tramite il
    `MarineTrafficClient`.
    """

    return {
        "source": "cache",
        "vessels": [],
    }


@app.get("/ports", summary="Porti monitorati")
def list_ports() -> Dict[str, List[str]]:
    """Placeholder con l'elenco dei porti configurati."""

    return {
        "ports": ["Naples", "Salerno", "Civitavecchia"],
    }


@app.get("/stats", summary="Statistiche di traffico")
def stats() -> Dict[str, Dict]:
    """Statistiche aggregate basate sui dati presenti nella cache."""

    return {
        "metadata": {
            "note": "Endpoint da collegare alla pipeline analytics",
        },
        "stats": {},
    }
