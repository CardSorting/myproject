import logging
import re
from typing import Dict, Any, Tuple
from myapp.models import Rarity
from django.conf import settings

# Logging configuration
logger = logging.getLogger(__name__)

def validate_mana_cost(cost: str) -> bool:
    """Validate mana cost format."""
    # Check if cost contains valid mana symbols in curly braces
    # Valid formats: {W}, {U}, {B}, {R}, {G}, {1}, {2}, etc.
    pattern = r'^(\{[WUBRG\d]\})*$'
    return bool(re.match(pattern, cost.replace(' ', '')))

def validate_name(name: str) -> bool:
    """Validate card name."""
    # Name should be 1-40 characters and contain only letters, numbers, spaces, and basic punctuation
    if not name or len(name) > 40:
        return False
    pattern = r'^[a-zA-Z0-9\s\',\-]+$'
    return bool(re.match(pattern, name))

def validate_color(color: Any) -> bool:
    """Validate card color."""
    valid_colors = {'White', 'Blue', 'Black', 'Red', 'Green'}
    if isinstance(color, str):
        return color in valid_colors
    elif isinstance(color, list):
        return all(c in valid_colors for c in color)
    return False

def standardize_card_data(card_data: Dict[str, Any]) -> None:
    """Standardize card data."""
    # Name
    if 'name' in card_data:
        card_data['name'] = card_data['name'].strip().title()

    # Type
    if 'type' in card_data:
        card_data['type'] = card_data['type'].strip().title()

    # Abilities
    if 'abilities' in card_data:
        # Ensure ability text starts with a capital letter and ends with a period
        if isinstance(card_data['abilities'], list):
            abilities = [ability.strip() for ability in card_data['abilities']]
            abilities = [ability + '.' if ability and not ability.endswith('.') else ability for ability in abilities]
            card_data['abilities'] = abilities
        elif isinstance(card_data['abilities'], str):
            text = card_data['abilities'].strip()
            if text and not text.endswith('.'):
                text += '.'
            card_data['abilities'] = text

    # Flavor Text
    if 'flavorText' in card_data:
        # Ensure flavor text starts with a capital letter and ends with appropriate punctuation
        text = card_data['flavorText'].strip()
        if text and not any(text.endswith(p) for p in '.!?'):
            text += '.'
        card_data['flavorText'] = text

    # Color
    if 'color' in card_data:
        if isinstance(card_data['color'], str):
            card_data['color'] = [card_data['color'].strip().title()]
        else:
            card_data['color'] = [c.strip().title() for c in card_data['color']]

    # Cost
    if 'manaCost' in card_data:
        # Remove spaces and ensure proper formatting of mana symbols
        cost = card_data['manaCost'].strip().upper()
        if not cost.startswith('{'):
            cost = '{' + cost
        if not cost.endswith('}'):
            cost += '}'
        card_data['manaCost'] = cost.replace('}{', '} {')

    # Power/Toughness
    if 'power' in card_data and 'toughness' in card_data:
        card_data['power'] = str(card_data['power']).strip()
        card_data['toughness'] = str(card_data['toughness']).strip()

def validate_card_data(card_data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate card data and return (is_valid, error_message)."""
    required_keys = ['name', 'type', 'abilities', 'color', 'manaCost']
    
    # Check required keys
    for key in required_keys:
        if key not in card_data:
            return False, f"Missing required field: {key}"
        if not card_data[key]:
            return False, f"Empty required field: {key}"

    # Validate name
    if not validate_name(card_data['name']):
        return False, "Invalid card name format or length (max 40 characters)"

    # Validate color
    if not validate_color(card_data['color']):
        return False, "Invalid color value"

    # Validate mana cost
    if not validate_mana_cost(card_data['manaCost']):
        return False, "Invalid mana cost format"

    # Validate power/toughness for creatures
    if 'Creature' in card_data['type']:
        if 'power' not in card_data or 'toughness' not in card_data:
            return False, "Creature cards must have power and toughness"
        try:
            int(card_data['power'])
            int(card_data['toughness'])
        except ValueError:
            return False, "Power and toughness must be numeric values"

    return True, ""

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