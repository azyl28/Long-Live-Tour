from dataclasses import dataclass

@dataclass
class Trip:
    id: int
    road_card_id: int
    origin: str
    destination: str
    purpose: str
    start_time: str
    end_time: str
