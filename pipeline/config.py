"""Constantes compartidas por todas las capas del pipeline"""

import numpy as np

ID_COLUMN = "id"
TARGET = "satisfaction"
POS_LABEL = "satisfied"
TARGET_RENAME = {"neutral or dissatisfied": "not satisfied"}

DROP_COLUMNS = ["raw_id"]

# Imputación condicional de arrival_delay_in_minutes según grupo de demora de salida
DEPARTURE_DELAY_COLUMN = "departure_delay_in_minutes"
ARRIVAL_DELAY_COLUMN = "arrival_delay_in_minutes"
DEPARTURE_DELAY_BINS = [-1, 0, 15, 60, np.inf]

NUMERIC_FEATURES = [
    "age",
    "flight_distance",
    "arrival_delay_in_minutes",
]

NOMINAL_FEATURES = [
    "type_of_travel",
    "class",
    "customer_type",
]

ORDINAL_FEATURES = [
    "online_boarding",
    "inflight_wifi_service",
    "inflight_entertainment",
    "seat_comfort",
    "on_board_service",
    "leg_room_service",
    "cleanliness",
    "ease_of_online_booking",
    "baggage_handling",
    "inflight_service",
    "checkin_service",
    "food_and_drink",
]

RATED_FEATURES = [f"{col}_rated" for col in ORDINAL_FEATURES]

FEATURES = NUMERIC_FEATURES + NOMINAL_FEATURES + ORDINAL_FEATURES + RATED_FEATURES

RANDOM_STATE = 42
CV_SPLITS = 5
