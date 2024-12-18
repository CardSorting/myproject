from django import forms
from .models import Card

class CardForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = ['name', 'manaCost', 'type', 'abilities', 'flavorText', 'rarity', 'set_name', 'card_number', 'powerToughness', 'local_image_path']