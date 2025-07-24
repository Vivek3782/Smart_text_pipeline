from django.core.management.base import BaseCommand
from scraper.models import ScrapedData, CleanedData
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import string

class Command(BaseCommand):
    help = 'Cleans raw reviews and saves them to CleanedData'

    def handle(self, *args, **kwargs):
        lemmatizer = WordNetLemmatizer()
        stop_words = set(stopwords.words('english'))
        count = 0

        scraped_reviews = ScrapedData.objects.all()

        for scraped in scraped_reviews:
            text = scraped.raw_text

            # Lowercase
            text = text.lower()

            # Remove punctuation
            text = text.translate(str.maketrans('', '', string.punctuation))

            # Tokenize
            tokens = word_tokenize(text)

            # Remove stop words & lemmatize
            tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words]

            cleaned = " ".join(tokens)

            # Save cleaned text
            CleanedData.objects.create(
                scraped=scraped,
                cleaned_text=cleaned
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully cleaned and saved {count} reviews.'))
