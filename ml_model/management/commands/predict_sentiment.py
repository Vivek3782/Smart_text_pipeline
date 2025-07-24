from django.core.management.base import BaseCommand
from scraper.models import CleanedData, Prediction
from transformers import pipeline


class Command(BaseCommand):
    help = 'Predicts sentiment for cleaned text using BERT and saves to Prediction'

    def handle(self, *args, **kwargs):
        # Load sentiment analysis pipeline (Hugging Face)
        classifier = pipeline('sentiment-analysis')

        count = 0

        cleaned_reviews = CleanedData.objects.all()

        for cleaned in cleaned_reviews:
            text = cleaned.cleaned_text

            # BERT has a token limit; keep it safe
            result = classifier(text[:512])

            sentiment_label = result[0]['label']

            Prediction.objects.create(
                cleaned=cleaned,
                sentiment=sentiment_label
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Successfully predicted sentiment for {count} reviews using BERT.'))
