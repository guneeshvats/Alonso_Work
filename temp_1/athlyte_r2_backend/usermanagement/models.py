from django.db import models

# Create your models here.
class User:
    def __init__(self, user_id, username, email):
        self.id = user_id
        self.username = username
        self.email = email