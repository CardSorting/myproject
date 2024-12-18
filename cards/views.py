from django.shortcuts import render, redirect
from .forms import CardForm
from .models import Card
from myapp.card_service import generate_card_wrapper

def create_card(request, initial_data=None):
    if request.method == 'POST':
        form = CardForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('card_list')  # Redirect to card list view after successful submission
    else:
        form = CardForm(initial=initial_data)
    return render(request, 'cards/create_card.html', {'form': form})

def card_list(request):
    cards = Card.objects.all()
    
    if request.GET.get('generate_card'):
        card_data = generate_card_wrapper()
        return redirect('create_card', initial_data=card_data)
    
    return render(request, 'cards/card_list.html', {'cards': cards})
