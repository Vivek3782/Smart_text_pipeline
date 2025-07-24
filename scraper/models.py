from django.db import models

class ScrapedData(models.Model):
    source_url = models.URLField()
    review_title = models.CharField(max_length=255, blank=True)
    raw_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class CleanedData(models.Model):
    scraped = models.ForeignKey(ScrapedData, on_delete=models.CASCADE)
    cleaned_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Prediction(models.Model):
    cleaned = models.ForeignKey(CleanedData, on_delete=models.CASCADE)
    sentiment = models.CharField(max_length=50)
    model_name = models.CharField(max_length=50, default='bert-base-uncased')
    created_at = models.DateTimeField(auto_now_add=True)

class InferenceLog(models.Model):
    question = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
