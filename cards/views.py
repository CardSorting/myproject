import uuid
from django.shortcuts import render, redirect
from .forms import CardForm
from .models import Card
from myapp.config.backblaze_config import upload_image

def create_card(request):
    if request.method == 'POST':
        form = CardForm(request.POST)
        if form.is_valid():
            card = form.save(commit=False)
            image = request.FILES.get('image')
            if image:
                filename = f"{uuid.uuid4()}{image.name}"
                image_data = image.read()
                backblaze_url = upload_image(image_data, filename)
                card.backblaze_image_url = backblaze_url
            card.save()
            return redirect('card_list')  # Redirect to card list view after successful submission
    else:
        form = CardForm()
    return render(request, 'cards/create_card.html', {'form': form})

def card_list(request):
    cards = Card.objects.all()
    return render(request, 'cards/card_list.html', {'cards': cards})

def home(request):
    cards = Card.objects.all()
    return render(request, 'cards/home.html', {'cards': cards})
