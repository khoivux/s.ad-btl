from django.db import models

class Staff(models.Model):
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    role = models.CharField(max_length=50, default='staff')

    def __str__(self):
        return self.username
