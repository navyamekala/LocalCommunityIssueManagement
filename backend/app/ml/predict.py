"""
Real-time DistilBERT Inference and Prediction Service.
Loads fine-tuned model and tokenizer once in memory on backend startup.
"""

import os
import json
from typing import Dict, Any, Optional
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from .severity import assess_severity


class DistilBERTIssuePredictor:
    _instance: Optional["DistilBERTIssuePredictor"] = None

    def __init__(self, model_dir: str):
        self.model_dir = model_dir
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = None
        self.model = None
        self.id2label = {}
        self.label2id = {}
        self.category_dept_map = {}
        self.is_loaded = False
        self.load_model()

    @classmethod
    def get_instance(cls, model_dir: Optional[str] = None) -> "DistilBERTIssuePredictor":
        if cls._instance is None:
            if model_dir is None:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                model_dir = os.path.join(base_dir, "model")
            cls._instance = cls(model_dir)
        return cls._instance

    def load_model(self):
        try:
            print(f"[DistilBERT Predictor] Loading model from: {self.model_dir}")
            label2id_path = os.path.join(self.model_dir, "label2id.json")
            id2label_path = os.path.join(self.model_dir, "id2label.json")
            dept_map_path = os.path.join(self.model_dir, "category_department_map.json")

            if os.path.exists(label2id_path):
                with open(label2id_path, "r", encoding="utf-8") as f:
                    self.label2id = json.load(f)
            if os.path.exists(id2label_path):
                with open(id2label_path, "r", encoding="utf-8") as f:
                    # JSON keys are strings, convert to int
                    self.id2label = {int(k): v for k, v in json.load(f).items()}
            if os.path.exists(dept_map_path):
                with open(dept_map_path, "r", encoding="utf-8") as f:
                    self.category_dept_map = json.load(f)

            if os.path.exists(os.path.join(self.model_dir, "config.json")):
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir)
                self.model = AutoModelForSequenceClassification.from_pretrained(self.model_dir)
                self.model.to(self.device)
                self.model.eval()
                self.is_loaded = True
                print(f"[DistilBERT Predictor] Model successfully loaded on {self.device}.")
            else:
                print(f"[DistilBERT Predictor] Model files not found yet in {self.model_dir}. Training in progress...")
        except Exception as e:
            print(f"[DistilBERT Predictor] Warning during model loading: {e}")

    def predict(self, title: str, description: str, confidence_threshold: float = 0.40) -> Dict[str, Any]:
        """
        Predicts category, confidence, responsible department, and severity.
        """
        # Fallback if model hasn't finished saving yet
        if not self.is_loaded:
            self.load_model()
            if not self.is_loaded:
                # Safe temporary rule-based fallback until checkpoint is written
                sev = assess_severity(title, description, "Road Damage")
                return {
                    "predicted_category": "Needs Manual Review",
                    "confidence_score": 0.0,
                    "probabilities": {},
                    "responsible_department": "Public Works Department",
                    "severity": sev["severity"],
                    "severity_reason": sev["reason"],
                    "severity_score": sev["score"],
                    "severity_method": sev["method"],
                    "needs_manual_review": True
                }

        input_text = f"{title}. {description}"
        inputs = self.tokenizer(
            input_text,
            truncation=True,
            padding="max_length",
            max_length=64,
            return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=1).squeeze(0).cpu().numpy()

        pred_idx = int(probs.argmax())
        confidence = float(probs[pred_idx])
        predicted_category = self.id2label.get(pred_idx, "Unknown")

        # Check confidence threshold for manual review requirement
        needs_manual_review = confidence < confidence_threshold

        all_probabilities = {
            self.id2label.get(i, f"Class {i}"): float(prob)
            for i, prob in enumerate(probs)
        }

        # Department routing
        responsible_dept = self.category_dept_map.get(predicted_category, "Public Works Department")

        # Severity Assessment
        sev_info = assess_severity(title, description, predicted_category)

        return {
            "predicted_category": predicted_category if not needs_manual_review else "Needs Manual Review",
            "raw_category": predicted_category,
            "confidence_score": round(confidence, 4),
            "probabilities": {k: round(v, 4) for k, v in all_probabilities.items()},
            "responsible_department": responsible_dept,
            "severity": sev_info["severity"],
            "severity_reason": sev_info["reason"],
            "severity_score": sev_info["score"],
            "severity_method": sev_info["method"],
            "needs_manual_review": needs_manual_review
        }
