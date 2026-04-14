from typing import Dict

NEIGHBORHOODS: Dict[str, Dict] = {
    "dtla": {
        "name": "Downtown LA",
        "factors": {"heat": 0.70, "flood": 0.35, "fire": 0.10, "air": 0.85},
    },
    "santa_monica": {
        "name": "Santa Monica",
        "factors": {"heat": 0.35, "flood": 0.25, "fire": 0.15, "air": 0.40},
    },
    "pasadena": {
        "name": "Pasadena",
        "factors": {"heat": 0.60, "flood": 0.30, "fire": 0.45, "air": 0.55},
    },
    "echo_park": {
        "name": "Echo Park / Silver Lake",
        "factors": {"heat": 0.62, "flood": 0.40, "fire": 0.25, "air": 0.65},
    },
    "woodland_hills": {
        "name": "Woodland Hills",
        "factors": {"heat": 0.90, "flood": 0.20, "fire": 0.55, "air": 0.50},
    },
    "compton": {
        "name": "Compton",
        "factors": {"heat": 0.78, "flood": 0.45, "fire": 0.10, "air": 0.80},
    },
}