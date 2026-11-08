"""
DistilBERT Training Pipeline for Local Community Issue Classification.

Fine-tunes 'distilbert-base-uncased' on citizen complaint descriptions.
Generates genuine test evaluation metrics and plots without fabrication.
"""

import os
import json
import time
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import torch
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report
)

# Set random seeds for exact reproducibility
def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

set_seed(42)

# Department Mapping based on Research & Administrative Structure
CATEGORY_TO_DEPARTMENT = {
    "Road Damage": "Roads Department",
    "Clogging": "Drainage Department",
    "Lamp Breakage": "Electrical Department",
    "Facility Defect": "Public Works Department",
    "Overgrowth": "Gardening Department",
    "Invisibility": "Traffic and Safety Department",
    "Leaving": "Sanitation / Public Area Management"
}

class ComplaintDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length=64):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = str(self.texts[idx])
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt"
        )
        item = {key: val.squeeze(0) for key, val in encoding.items()}
        if self.labels is not None:
            item["labels"] = torch.tensor(self.labels[idx], dtype=torch.long)
        return item


def compute_metrics(preds, labels, target_names):
    accuracy = accuracy_score(labels, preds)
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(labels, preds, average="macro", zero_division=0)
    p_weighted, r_weighted, f1_weighted, _ = precision_recall_fscore_support(labels, preds, average="weighted", zero_division=0)
    p_per_class, r_per_class, f1_per_class, support = precision_recall_fscore_support(labels, preds, average=None, zero_division=0)

    per_class = {}
    for i, name in enumerate(target_names):
        per_class[name] = {
            "precision": float(p_per_class[i]),
            "recall": float(r_per_class[i]),
            "f1_score": float(f1_per_class[i]),
            "support": int(support[i])
        }

    cm = confusion_matrix(labels, preds).tolist()

    return {
        "accuracy": float(accuracy),
        "precision_macro": float(p_macro),
        "recall_macro": float(r_macro),
        "f1_macro": float(f1_macro),
        "precision_weighted": float(p_weighted),
        "recall_weighted": float(r_weighted),
        "f1_weighted": float(f1_weighted),
        "per_class": per_class,
        "confusion_matrix": cm
    }


def train_model(
    csv_path: str,
    output_dir: str,
    artifacts_dir: str,
    epochs: int = 3,
    batch_size: int = 16,
    learning_rate: float = 2e-5,
    max_length: int = 64
):
    print("="*60)
    print("DISTILBERT FINE-TUNING PIPELINE")
    print("="*60)
    start_time = time.time()

    # 1. Load Dataset
    print(f"[1/7] Loading dataset from: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"      Initial shape: {df.shape}")
    print(f"      Data source note: Synthetically generated complaints for project development.")

    # 2. Clean & Preprocess
    df = df.dropna(subset=["title", "description", "category"])
    df = df.drop_duplicates(subset=["title", "description"]).reset_index(drop=True)
    print(f"      Shape after deduplication: {df.shape}")

    # Combine title and description
    df["input_text"] = df["title"].astype(str) + ". " + df["description"].astype(str)

    # Categories
    categories = sorted(df["category"].unique().tolist())
    num_labels = len(categories)
    label2id = {c: i for i, c in enumerate(categories)}
    id2label = {i: c for i, c in enumerate(categories)}
    df["label"] = df["category"].map(label2id)

    print(f"      Identified {num_labels} classes: {categories}")
    print("      Class counts:")
    for cat, count in df["category"].value_counts().items():
        print(f"        - {cat}: {count}")

    # 3. Stratified Splitting: 70% Train, 15% Val, 15% Test
    print("\n[2/7] Splitting data: 70% Train, 15% Validation, 15% Test (Stratified)...")
    train_df, temp_df = train_test_split(
        df, test_size=0.30, random_state=42, stratify=df["label"]
    )
    val_df, test_df = train_test_split(
        temp_df, test_size=0.50, random_state=42, stratify=temp_df["label"]
    )

    print(f"      Train samples: {len(train_df)}")
    print(f"      Val samples:   {len(val_df)}")
    print(f"      Test samples:  {len(test_df)}")

    # 4. Tokenizer & Datasets
    print("\n[3/7] Loading DistilBERT tokenizer and building datasets...")
    model_name = "distilbert-base-uncased"
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    train_dataset = ComplaintDataset(train_df["input_text"].tolist(), train_df["label"].tolist(), tokenizer, max_length)
    val_dataset = ComplaintDataset(val_df["input_text"].tolist(), val_df["label"].tolist(), tokenizer, max_length)
    test_dataset = ComplaintDataset(test_df["input_text"].tolist(), test_df["label"].tolist(), tokenizer, max_length)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    # 5. Device & Model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n[4/7] Initializing model on device: {device}...")
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=num_labels,
        id2label=id2label,
        label2id=label2id
    )
    model.to(device)

    # Optimizer & Scheduler
    optimizer = AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)
    total_steps = len(train_loader) * epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=int(0.1 * total_steps),
        num_training_steps=total_steps
    )

    # 6. Training Loop with Best Checkpoint Tracking
    print(f"\n[5/7] Starting training for {epochs} epochs...")
    history = {
        "train_loss": [],
        "val_loss": [],
        "val_accuracy": [],
        "val_f1_macro": []
    }

    best_val_f1 = 0.0
    best_model_state = None

    for epoch in range(1, epochs + 1):
        epoch_start = time.time()
        model.train()
        total_train_loss = 0.0

        for step, batch in enumerate(train_loader):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            optimizer.zero_grad()
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss
            total_train_loss += loss.item()

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()

        avg_train_loss = total_train_loss / len(train_loader)

        # Validation
        model.eval()
        total_val_loss = 0.0
        val_preds = []
        val_targets = []

        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                labels = batch["labels"].to(device)

                outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
                total_val_loss += outputs.loss.item()

                logits = outputs.logits
                preds = torch.argmax(logits, dim=1).cpu().numpy()
                val_preds.extend(preds)
                val_targets.extend(labels.cpu().numpy())

        avg_val_loss = total_val_loss / len(val_loader)
        val_acc = accuracy_score(val_targets, val_preds)
        _, _, val_f1, _ = precision_recall_fscore_support(val_targets, val_preds, average="macro", zero_division=0)

        history["train_loss"].append(float(avg_train_loss))
        history["val_loss"].append(float(avg_val_loss))
        history["val_accuracy"].append(float(val_acc))
        history["val_f1_macro"].append(float(val_f1))

        elapsed = time.time() - epoch_start
        print(f"  Epoch {epoch}/{epochs} ({elapsed:.1f}s) - Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f} | Val Acc: {val_acc:.4f} | Val Macro F1: {val_f1:.4f}")

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_model_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            print(f"    * New best validation macro F1: {best_val_f1:.4f} (Saving checkpoint)")

    # Restore best weights
    if best_model_state is not None:
        model.load_state_dict({k: v.to(device) for k, v in best_model_state.items()})

    # Save fine-tuned model and tokenizer
    print(f"\n[6/7] Saving fine-tuned model and tokenizer to: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    with open(os.path.join(output_dir, "label2id.json"), "w", encoding="utf-8") as f:
        json.dump(label2id, f, indent=2)
    with open(os.path.join(output_dir, "id2label.json"), "w", encoding="utf-8") as f:
        json.dump(id2label, f, indent=2)
    with open(os.path.join(output_dir, "category_department_map.json"), "w", encoding="utf-8") as f:
        json.dump(CATEGORY_TO_DEPARTMENT, f, indent=2)

    # 7. Independent Test Evaluation
    print("\n[7/7] Evaluating final model on independent Test Set (15%)...")
    model.eval()
    test_preds = []
    test_targets = []
    test_probs = []

    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=1).cpu().numpy()
            preds = np.argmax(probs, axis=1)

            test_preds.extend(preds)
            test_targets.extend(labels.cpu().numpy())
            test_probs.extend(probs)

    metrics = compute_metrics(test_preds, test_targets, categories)
    print("\n" + "="*60)
    print("GENUINE INDEPENDENT TEST METRICS:")
    print("="*60)
    print(f"Accuracy:         {metrics['accuracy']*100:.2f}%")
    print(f"Macro Precision:  {metrics['precision_macro']*100:.2f}%")
    print(f"Macro Recall:     {metrics['recall_macro']*100:.2f}%")
    print(f"Macro F1-Score:   {metrics['f1_macro']*100:.2f}%")
    print(f"Weighted F1:      {metrics['f1_weighted']*100:.2f}%")
    print("\nPer-Category Performance:")
    for cat, p_data in metrics["per_class"].items():
        print(f"  {cat:16s} | Prec: {p_data['precision']*100:5.2f}% | Rec: {p_data['recall']*100:5.2f}% | F1: {p_data['f1_score']*100:5.2f}% | Support: {p_data['support']}")
    print("="*60)

    # Save artifacts
    reports_dir = os.path.join(artifacts_dir, "training_reports")
    plots_dir = os.path.join(artifacts_dir, "evaluation_plots")
    metrics_dir = os.path.join(artifacts_dir, "metrics")
    os.makedirs(reports_dir, exist_ok=True)
    os.makedirs(plots_dir, exist_ok=True)
    os.makedirs(metrics_dir, exist_ok=True)

    # Metadata & summary
    training_info = {
        "model_architecture": "DistilBERT (distilbert-base-uncased)",
        "num_classes": num_labels,
        "classes": categories,
        "total_dataset_size": len(df),
        "train_size": len(train_df),
        "val_size": len(val_df),
        "test_size": len(test_df),
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "max_length": max_length,
        "best_val_macro_f1": float(best_val_f1),
        "training_time_seconds": round(time.time() - start_time, 2),
        "training_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "device_used": str(device),
        "history": history
    }

    with open(os.path.join(reports_dir, "training_report.json"), "w", encoding="utf-8") as f:
        json.dump(training_info, f, indent=2)

    with open(os.path.join(metrics_dir, "test_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # Also save a copy inside backend/app/ml/ for fast serving
    with open(os.path.join(output_dir, "test_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    with open(os.path.join(output_dir, "training_report.json"), "w", encoding="utf-8") as f:
        json.dump(training_info, f, indent=2)

    # Generate Visualizations
    generate_plots(history, metrics, df, categories, plots_dir)

    print(f"\nAll artifacts successfully saved to:\n  - Model: {output_dir}\n  - Artifacts: {artifacts_dir}")
    return metrics, training_info


def generate_plots(history, metrics, df, categories, plots_dir):
    print("Generating evaluation and diagnostic plots...")
    sns.set_theme(style="whitegrid")

    # 1. Training & Validation Loss
    plt.figure(figsize=(8, 5))
    epochs_range = range(1, len(history["train_loss"]) + 1)
    plt.plot(epochs_range, history["train_loss"], marker='o', linewidth=2, label="Train Loss", color="#2563eb")
    plt.plot(epochs_range, history["val_loss"], marker='s', linewidth=2, label="Validation Loss", color="#dc2626")
    plt.title("DistilBERT Training vs Validation Loss", fontsize=14, fontweight="bold", pad=12)
    plt.xlabel("Epoch", fontsize=12)
    plt.ylabel("Cross-Entropy Loss", fontsize=12)
    plt.xticks(epochs_range)
    plt.legend(fontsize=11)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "loss_curve.png"), dpi=300)
    plt.close()

    # 2. Validation Accuracy & F1
    plt.figure(figsize=(8, 5))
    plt.plot(epochs_range, history["val_accuracy"], marker='o', linewidth=2, label="Validation Accuracy", color="#059669")
    plt.plot(epochs_range, history["val_f1_macro"], marker='^', linewidth=2, label="Validation Macro F1", color="#7c3aed")
    plt.title("Validation Accuracy & Macro F1 Score Progression", fontsize=14, fontweight="bold", pad=12)
    plt.xlabel("Epoch", fontsize=12)
    plt.ylabel("Score", fontsize=12)
    plt.xticks(epochs_range)
    plt.ylim(0, 1.05)
    plt.legend(fontsize=11)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "accuracy_curve.png"), dpi=300)
    plt.close()

    # 3. Overall Test Metrics Comparison
    plt.figure(figsize=(7, 4.5))
    overall_names = ["Accuracy", "Macro Prec", "Macro Rec", "Macro F1", "Weighted F1"]
    overall_vals = [
        metrics["accuracy"],
        metrics["precision_macro"],
        metrics["recall_macro"],
        metrics["f1_macro"],
        metrics["f1_weighted"]
    ]
    colors = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899"]
    bars = plt.bar(overall_names, overall_vals, color=colors, width=0.55)
    plt.title("DistilBERT Independent Test Performance Summary", fontsize=13, fontweight="bold", pad=12)
    plt.ylabel("Score", fontsize=11)
    plt.ylim(0, 1.15)
    for bar in bars:
        h = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., h + 0.02, f"{h*100:.1f}%", ha='center', va='bottom', fontweight='bold', fontsize=10)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "precision_recall_f1.png"), dpi=300)
    plt.close()

    # 4. Per-Class Precision, Recall, F1
    plt.figure(figsize=(11, 5.5))
    x = np.arange(len(categories))
    width = 0.25
    precisions = [metrics["per_class"][c]["precision"] for c in categories]
    recalls = [metrics["per_class"][c]["recall"] for c in categories]
    f1s = [metrics["per_class"][c]["f1_score"] for c in categories]

    plt.bar(x - width, precisions, width, label='Precision', color='#3b82f6')
    plt.bar(x, recalls, width, label='Recall', color='#10b981')
    plt.bar(x + width, f1s, width, label='F1-Score', color='#f59e0b')

    plt.title("Per-Category Classification Performance on Test Set", fontsize=14, fontweight="bold", pad=12)
    plt.xlabel("Complaint Category", fontsize=12)
    plt.ylabel("Score", fontsize=12)
    plt.xticks(x, categories, rotation=25, ha='right', fontsize=10)
    plt.ylim(0, 1.15)
    plt.legend(fontsize=11)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "per_class_metrics.png"), dpi=300)
    plt.close()

    # 5. Confusion Matrix Heatmap
    plt.figure(figsize=(8.5, 7))
    cm = np.array(metrics["confusion_matrix"])
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=categories, yticklabels=categories, cbar=True)
    plt.title("Confusion Matrix Heatmap (Independent Test Set)", fontsize=14, fontweight="bold", pad=12)
    plt.xlabel("Predicted Category", fontsize=12)
    plt.ylabel("Actual True Category", fontsize=12)
    plt.xticks(rotation=30, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "confusion_matrix.png"), dpi=300)
    plt.close()

    # 6. Category Distribution
    plt.figure(figsize=(9, 4.5))
    cat_counts = df["category"].value_counts()
    sns.barplot(x=cat_counts.index, y=cat_counts.values, palette="crest")
    plt.title("Citizen Complaint Dataset Class Distribution (Synthetic Reference)", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Category", fontsize=11)
    plt.ylabel("Number of Samples", fontsize=11)
    plt.xticks(rotation=25, ha='right')
    for i, count in enumerate(cat_counts.values):
        plt.text(i, count + 10, str(count), ha='center', va='bottom', fontsize=10, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "category_distribution.png"), dpi=300)
    plt.close()

    print("All diagnostic plots generated successfully.")


if __name__ == "__main__":
    base_dir = r"C:\Users\SUBBALAKSHMI\OneDrive\Desktop\LocalCommunityIssueManagement"
    csv_file = os.path.join(base_dir, "dataset", "local_community_complaints_5000_synthetic-3.csv")
    out_model = os.path.join(base_dir, "backend", "app", "ml", "model")
    artifacts = os.path.join(base_dir, "ml_artifacts")

    # 2 Epochs with batch_size 16 is sufficient for DistilBERT fine-tuning on 3500 short text samples
    train_model(
        csv_path=csv_file,
        output_dir=out_model,
        artifacts_dir=artifacts,
        epochs=2,
        batch_size=16,
        learning_rate=2e-5,
        max_length=64
    )
