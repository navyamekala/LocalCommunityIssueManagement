"""
Severity Detection Module for Citizen Complaints.

Rule-based transparent severity scoring system based on urgency keywords,
hazard indicators, public safety risk levels, and vulnerability contexts (e.g. schools, hospitals).
Designed for modular extension so that a machine learning severity model can be plugged in seamlessly.
"""

import re
from typing import Dict, Any


CRITICAL_KEYWORDS = [
    r"\belectric wire\b", r"\blive wire\b", r"\bsparking\b", r"\belectrocution\b",
    r"\broad collapse\b", r"\bsinkhole\b", r"\bcaved in\b", r"\bbridge collapse\b",
    r"\bflash flood\b", r"\bdangerous flooding\b", r"\bemergency\b", r"\bfatal\b",
    r"\blife[- ]threatening\b", r"\bmajor hazard\b", r"\bwater main burst\b",
    r"\bexplosion\b", r"\btoxic\b", r"\bgas leak\b", r"\bwall collapsed\b"
]

HIGH_KEYWORDS = [
    r"\blarge pothole\b", r"\bdeep pothole\b", r"\bsevere drainage overflow\b",
    r"\bsewage overflow\b", r"\bdirty water entering\b", r"\bflooded road\b",
    r"\bbroken water pipe\b", r"\bmanhole open\b", r"\bopen manhole\b",
    r"\bdamaged transformer\b", r"\bheavy debris\b", r"\baccident prone\b",
    r"\bsevere\b", r"\bdangerous\b", r"\bblind curve\b", r"\bhospital\b", r"\bschool\b"
]

MEDIUM_KEYWORDS = [
    r"\bpartially blocked\b", r"\bnon[- ]functional streetlight\b", r"\bdark street\b",
    r"\bdamaged footpath\b", r"\bpavement crack\b", r"\bstreetlight not working\b",
    r"\blamp post broken\b", r"\bovergrown bushes\b", r"\bblocking visibility\b",
    r"\bdriveway blocked\b", r"\bdumped furniture\b", r"\babandoned vehicle\b",
    r"\bclogged drain\b", r"\bslow drainage\b", r"\brusted playground\b"
]

LOW_KEYWORDS = [
    r"\bminor\b", r"\bsmall garbage\b", r"\blitter\b", r"\bfaded paint\b",
    r"\bweeds\b", r"\bdustbin full\b", r"\bcleaning required\b", r"\bsmall pothole\b",
    r"\bcosmetic\b", r"\btrimming needed\b", r"\bleaf pile\b"
]


def assess_severity(title: str, description: str, category: str = "") -> Dict[str, Any]:
    """
    Evaluates complaint severity and returns severity level along with explanatory reasons.
    
    Returns:
        dict: {
            "severity": "Critical" | "High" | "Medium" | "Low",
            "reason": str,
            "method": "Rule-based Keyword & Context Analysis v1.0",
            "score": float (0.0 to 1.0)
        }
    """
    text = f"{title} {description}".lower()

    # 1. Check Critical
    for pattern in CRITICAL_KEYWORDS:
        match = re.search(pattern, text)
        if match:
            return {
                "severity": "Critical",
                "reason": f"High public safety hazard detected: matched urgency indicator '{match.group(0)}'",
                "method": "Rule-based Keyword & Context Analysis v1.0",
                "score": 0.95
            }

    # Proximity to vulnerable areas with safety concerns
    if ("school" in text or "hospital" in text or "kindergarten" in text) and \
       any(k in text for k in ["overflow", "drain", "water", "accident", "broken", "danger"]):
        return {
            "severity": "Critical",
            "reason": "Hazardous community condition near sensitive public infrastructure (school/hospital)",
            "method": "Rule-based Keyword & Context Analysis v1.0",
            "score": 0.90
        }

    # 2. Check High
    for pattern in HIGH_KEYWORDS:
        match = re.search(pattern, text)
        if match:
            return {
                "severity": "High",
                "reason": f"Significant disruption or infrastructure risk detected: '{match.group(0)}'",
                "method": "Rule-based Keyword & Context Analysis v1.0",
                "score": 0.75
            }

    # 3. Check Medium
    for pattern in MEDIUM_KEYWORDS:
        match = re.search(pattern, text)
        if match:
            return {
                "severity": "Medium",
                "reason": f"Moderate public utility or civic maintenance issue: '{match.group(0)}'",
                "method": "Rule-based Keyword & Context Analysis v1.0",
                "score": 0.50
            }

    # Check Low keywords
    for pattern in LOW_KEYWORDS:
        match = re.search(pattern, text)
        if match:
            return {
                "severity": "Low",
                "reason": f"Standard routine civic maintenance required: '{match.group(0)}'",
                "method": "Rule-based Keyword & Context Analysis v1.0",
                "score": 0.25
            }

    # Category defaults if no explicit keywords matched
    category_defaults = {
        "Road Damage": ("Medium", "Road damage without explicit emergency keywords, standard repair priority"),
        "Clogging": ("Medium", "Drainage issue reported, pending field hazard assessment"),
        "Lamp Breakage": ("Medium", "Public lighting maintenance required for night safety"),
        "Invisibility": ("Medium", "Visibility obstruction reported, requiring traffic safety inspection"),
        "Facility Defect": ("Medium", "Public facility defect requiring maintenance inspection"),
        "Overgrowth": ("Low", "Roadside vegetation or plant overgrowth requiring scheduled trimming"),
        "Leaving": ("Low", "Public area cleanup or waste collection scheduled maintenance")
    }

    if category in category_defaults:
        sev, rsn = category_defaults[category]
        return {
            "severity": sev,
            "reason": rsn,
            "method": "Rule-based Keyword & Context Analysis v1.0",
            "score": 0.50 if sev == "Medium" else 0.25
        }

    return {
        "severity": "Medium",
        "reason": "Default civic issue assessment pending administrator review",
        "method": "Rule-based Keyword & Context Analysis v1.0",
        "score": 0.50
    }
