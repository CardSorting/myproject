from django.db import models

class Card(models.Model):
    name = models.CharField(max_length=200)
    manaCost = models.CharField(max_length=200, blank=True, null=True)
    type = models.CharField(max_length=200)
    abilities = models.TextField(blank=True, null=True)
    flavorText = models.TextField(blank=True, null=True)
    rarity = models.CharField(max_length=50)
    set_name = models.CharField(max_length=50)
    card_number = models.IntegerField()
    powerToughness = models.CharField(max_length=20, blank=True, null=True)
    local_image_path = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
