from enum import Enum
from dataclasses import dataclass
import string
from uuid import UUID, uuid4

class Rarity(Enum):
    COMMON = 0
    UNCOMMON = 1
    RARE = 2
    MYTHIC_RARE = 3

    def cardmarketRarityToEnum(str):
        switcher = {
            "Common": 0,
            "Uncommon" : 1,
            "Rare" : 2,
            "Mythic" : 3
        }
        return Rarity(switcher(str))


@dataclass
class MTGCardData:

    def __init__(self) -> None:
        card_name: string
        rarity: Rarity
        available_count: int
        version_count: int
        set_number: int #unique ID
        lowest_price: float
        price_trend: float
        average_price_30_day: float
        average_price_7_day: float
        average_price_1_day: float
        record_uuid: UUID = uuid4
    