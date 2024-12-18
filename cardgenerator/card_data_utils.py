import logging
from typing import Dict, Any
from myapp.models import Rarity
from django.conf import settings

# Logging configuration
logger = logging.getLogger(__name__)

def standardize_card_data(card_data: Dict[str, Any]) -> None:
    """Standardize card data."""
    if 'name' in card_data:
        card_data['name'] = card_data['name'].strip()
    if 'type' in card_data:
        card_data['type'] = card_data['type'].strip()
    if 'text' in card_data:
        card_data['text'] = card_data['text'].strip()
    if 'flavor_text' in card_data:
        card_data['flavor_text'] = card_data['flavor_text'].strip()
    if 'color' in card_data and isinstance(card_data['color'], str):
        card_data['color'] = [card_data['color'].strip()]
    if 'cost' in card_data:
        card_data['cost'] = str(card_data['cost']).strip()
    if 'power' in card_data:
        card_data['power'] = str(card_data['power']).strip()
    if 'toughness' in card_data:
        card_data['toughness'] = str(card_data['toughness']).strip()

def validate_card_data(card_data: Dict[str, Any]) -> bool:
    """Validate card data."""
    required_keys = ['name', 'type', 'text', 'color', 'cost']
    for key in required_keys:
        if key not in card_data:
            logger.error(f"Missing required key: {key}")
            return False
    return True

def get_rarity(set_number: int, card_number: int) -> Rarity:
    """Get the rarity of a card based on set and card number."""
    if (set_number + card_number) % 10 == 0:
        return Rarity.MYTHIC
    elif (set_number + card_number) % 5 == 0:
        return Rarity.RARE
    elif (set_number + card_number) % 3 == 0:
        return Rarity.UNCOMMON
    else:
        return Rarity.COMMON