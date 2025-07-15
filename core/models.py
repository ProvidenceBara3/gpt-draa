from django.db import models

class UploadedDocument(models.Model):
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    language = models.CharField(max_length=10, choices=[
        ('en', 'English'),
        ('fr', 'Français'),
        ('sw', 'Swahili'),
        ('am', 'Amharic')
    ])

    def __str__(self):
        return self.file.name
