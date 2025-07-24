from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from scraper.models import Prediction
from scraper.models import CleanedData, ScrapedData, InferenceLog
from transformers import pipeline
import requests
import os
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import string


class PredictionsAPIView(APIView):
    def get(self, request):
        predictions = Prediction.objects.select_related(
            'cleaned__scraped').all()
        data = []
        for p in predictions:
            data.append({
                "title": p.cleaned.scraped.review_title,
                "raw_text": p.cleaned.scraped.raw_text,
                "cleaned_text": p.cleaned.cleaned_text,
                "sentiment": p.sentiment,
            })
        return Response(data)


class AskGeminiAPIView(APIView):
    def post(self, request):
        question = request.data.get('question')
        if not question:
            return Response({'error': 'No question provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        cleaned_and_preds = Prediction.objects.select_related('cleaned__scraped').all()

        context_lines = []
        for p in cleaned_and_preds:
            context_lines.append(
                f"- {p.cleaned.cleaned_text[:50]}... | Sentiment: {p.sentiment}"
            )

        context = "\n".join(context_lines)

        # ✅ Compose the full prompt for Gemini
        prompt = f"""
        You are an assistant analyzing movie reviews.

        Context:
        Here is the list of cleaned reviews with predicted sentiments:
        {context}

        Question:
        {question}
        """


        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

        payload = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ]
        }
        res = requests.post(url, json=payload)

        if res.status_code == 200:
            answer = res.json()['candidates'][0]['content']['parts'][0]['text']
            InferenceLog.objects.create(
                question=question,
                answer=answer
            )
            return Response({"answer": answer})
        else:
            return Response({"error": "Gemini API error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PredictTextAPIView(APIView):
    def post(self, request):
        text = request.data.get('text')
        if not text:
            return Response({'error': 'No text provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Preprocess with NLTK
        lemmatizer = WordNetLemmatizer()
        stop_words = set(stopwords.words('english'))

        text_clean = text.lower()
        text_clean = text_clean.translate(
            str.maketrans('', '', string.punctuation))
        tokens = word_tokenize(text_clean)
        tokens = [lemmatizer.lemmatize(word)
                  for word in tokens if word not in stop_words]
        cleaned_text = " ".join(tokens)

        # Save to DB for traceability
        scraped = ScrapedData.objects.create(
            source_url='manual',
            review_title='Manual Input',
            raw_text=text
        )
        cleaned = CleanedData.objects.create(
            scraped=scraped,
            cleaned_text=cleaned_text
        )

        # Run BERT
        classifier = pipeline('sentiment-analysis')
        result = classifier(cleaned_text[:512])
        sentiment = result[0]['label']

        Prediction.objects.create(
            cleaned=cleaned,
            sentiment=sentiment
        )

        return Response({
            "cleaned_text": cleaned_text,
            "sentiment": sentiment
        })
