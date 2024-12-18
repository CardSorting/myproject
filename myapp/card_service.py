import random
import json
import logging
import re
from typing import Dict, Any, Tuple
from tenacity import retry, stop_after_attempt, wait_random_exponential
# from myapp.config.openai_config import openai_client # Removed OpenAI import
from cardgenerator.card_data_utils import standardize_card_data, validate_card_data, get_rarity
from cardgenerator.prompt_utils import generate_card_prompt
from myapp.models import Rarity
from django.db import transaction
from django.conf import settings

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_SET_NAME = 'GEN'
CARD_NUMBER_LIMIT = 999

def get_next_set_name_and_number() -> Tuple[str, int, int]:
    """Get the next set name, set number, and card number."""
    set_number = random.randint(1, 10)
    return DEFAULT_SET_NAME, set_number, random.randint(1, CARD_NUMBER_LIMIT)

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
def generate_card(rarity: str = None) -> Dict[str, Any]:
    """Generate a card with optional rarity."""
    prompt = generate_card_prompt(rarity)
    max_attempts = 3
    
    for attempt in range(max_attempts):
        try:
            # Log that we're generating card data (not image)
            logger.info("Generating card data with Gemini...")
            
            # Initialize Google Gen AI client
            from google import genai
            client = genai.Client(api_key=settings.GOOGLE_API_KEY)
            
            response = client.models.generate_content(
                model='gemini-2.0-flash-exp', contents=prompt
            )
            
            card_data_str = response.text
            logger.debug(f"Raw card data from Gemini (attempt {attempt + 1}): {card_data_str}")

            if not card_data_str:
                logger.error(f"Gemini API returned an empty response (attempt {attempt + 1})")
                if attempt < max_attempts - 1:
                    continue
                raise ValueError("Gemini API returned an empty response after multiple attempts")
            
            # Remove ```json and ``` if present
            card_data_str = re.sub(r'```(json)?', '', card_data_str).strip()
            
            try:
                card_data = json.loads(card_data_str)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response (attempt {attempt + 1}): {e}. Raw response: {card_data_str}")
                if attempt < max_attempts - 1:
                    continue
                raise ValueError("Failed to generate valid card data after multiple attempts")
            
            # Get themed elements based on colors
            if 'color' in card_data:
                from cardgenerator.prompt_utils import get_themed_elements
                colors = card_data['color'] if isinstance(card_data['color'], list) else [card_data['color']]
                card_data['themes'] = get_themed_elements(colors)
            
            standardize_card_data(card_data)
            
            is_valid, error_message = validate_card_data(card_data)
            if not is_valid:
                if attempt < max_attempts - 1:
                    logger.warning(f"Invalid card data on attempt {attempt + 1}, retrying... Error: {error_message}")
                    continue
                raise ValueError(f"Failed to generate valid card data after multiple attempts. Error: {error_message}")
            
            set_name, set_number, card_number = get_next_set_name_and_number()
            
            if not rarity:
                card_rarity = get_rarity(set_number, card_number)
                card_data['rarity'] = card_rarity.value
            
            card_data['set_name'] = set_name
            card_data['card_number'] = card_number
            
            # Log successful card data generation
            logger.info("Card data generated successfully")
            logger.debug(f"Final card data: {json.dumps(card_data, indent=2)}")
            
            return card_data
                
        except Exception as e:
            logger.error(f"Error generating card data (attempt {attempt + 1}): {e}")
            if attempt < max_attempts - 1:
                continue
            raise ValueError(f"Failed to generate card after {max_attempts} attempts: {str(e)}")

def generate_card_wrapper(rarity: str = None) -> Dict[str, Any]:
    """Generate a card with optional rarity."""
    return generate_card(rarity)