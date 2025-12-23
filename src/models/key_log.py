from dataclasses import dataclass

@dataclass
class KeyLog:
    id: int
    road_card_id: int
    action: str
    timestamp: str
