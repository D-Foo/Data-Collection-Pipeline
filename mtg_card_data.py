import string
from uuid import UUID, uuid4

class MTGCardData:

    def __init__(self) -> None:
        self.dict = {
        "card_name": string,
        "rarity": string,
        "available_count": int,
        "version_count": int,
        "set_number": int, #unique ID
        "lowest_price": float,
        "price_trend": float,
        "average_price_30_day": float,
        "average_price_7_day": float,
        "average_price_1_day": float,
        "image_url" : string,
        "uuid": string,}
    