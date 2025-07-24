# api/urls.py

from django.urls import path
from .views import PredictionsAPIView, AskGeminiAPIView, PredictTextAPIView

urlpatterns = [
    path('predictions/', PredictionsAPIView.as_view(), name='predictions'),
    path('ask/', AskGeminiAPIView.as_view(), name='ask_gemini'),
    path('predict/', PredictTextAPIView.as_view(), name='predict_text'),
]
