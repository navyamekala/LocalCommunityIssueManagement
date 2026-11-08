"""
Machine Learning and Model Analytics Endpoints.
Serves real-time DistilBERT predictions, genuine evaluation metrics,
training history metadata, generated diagnostic plots, and universal village geocoding.
"""

import os
import json
import urllib.request
import urllib.parse
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from ..schemas.schemas import PredictionRequest, PredictionResponse
from ..ml.predict import DistilBERTIssuePredictor
from ..ml.evaluate import get_evaluation_metrics

router = APIRouter(prefix="/api/ml", tags=["Machine Learning"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PLOTS_DIR = os.path.join(BASE_DIR, "ml_artifacts", "evaluation_plots")


@router.post("/predict", response_model=PredictionResponse)
def predict_issue(payload: PredictionRequest):
    """Real-time inference endpoint using the fine-tuned DistilBERT model."""
    predictor = DistilBERTIssuePredictor.get_instance()
    res = predictor.predict(payload.title, payload.description)
    return res


@router.get("/metrics")
def get_model_metrics():
    """Returns genuine test-set metrics calculated after DistilBERT fine-tuning."""
    data = get_evaluation_metrics()
    if not data["metrics"]:
        raise HTTPException(
            status_code=404,
            detail="Model metrics not available yet. Training may still be running."
        )
    return data["metrics"]


@router.get("/training-info")
def get_model_training_info():
    """Returns model training hyperparameters, dataset partition numbers, and history."""
    data = get_evaluation_metrics()
    if not data["training_report"]:
        raise HTTPException(
            status_code=404,
            detail="Training report not available yet."
        )
    return data["training_report"]


@router.get("/plots/{plot_name}")
def get_evaluation_plot(plot_name: str):
    """Serves generated Matplotlib/Seaborn diagnostic plot images."""
    safe_name = os.path.basename(plot_name)
    file_path = os.path.join(PLOTS_DIR, safe_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Plot '{safe_name}' not found.")
    return FileResponse(file_path, media_type="image/png")


@router.get("/geocode")
def geocode_place(query: str = Query(..., min_length=2)):
    """
    Universal geocoder for ALL villages, towns, mandals, and panchayats.
    Uses multi-stage fallback matching (raw query -> AP regional context -> National India context)
    so even the smallest rural gram panchayats are located reliably.
    """
    clean_query = query.strip()
    
    # Try different search variants to guarantee finding any village
    search_variants = [
        clean_query,
        f"{clean_query}, Andhra Pradesh, India",
        f"{clean_query}, India"
    ]
    
    results = []
    headers = {"User-Agent": "GramSetuUniversalVillageApp/2.0"}

    for q in search_variants:
        try:
            encoded = urllib.parse.quote(q)
            url = f"https://nominatim.openstreetmap.org/search?format=json&q={encoded}&limit=5"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode())
                if data:
                    for item in data:
                        results.append({
                            "lat": float(item["lat"]),
                            "lng": float(item["lon"]),
                            "display_name": item.get("display_name", "")
                        })
                    break # Stop if results found
        except Exception:
            continue

    # Fallback to Photon engine if Nominatim returned empty
    if not results:
        for q in [clean_query, f"{clean_query} Andhra Pradesh", f"{clean_query} India"]:
            try:
                url_photon = f"https://photon.komoot.io/api/?q={urllib.parse.quote(q)}&limit=5"
                with urllib.request.urlopen(url_photon, timeout=4) as resp2:
                    data2 = json.loads(resp2.read().decode())
                    for feat in data2.get("features", []):
                        coords = feat["geometry"]["coordinates"]
                        props = feat.get("properties", {})
                        name_parts = [props.get("name", ""), props.get("district", ""), props.get("state", "")]
                        full_name = ", ".join([p for p in name_parts if p])
                        results.append({
                            "lat": float(coords[1]),
                            "lng": float(coords[0]),
                            "display_name": full_name or props.get("name", clean_query)
                        })
                    if results:
                        break
            except Exception:
                continue

    return {"results": results}
