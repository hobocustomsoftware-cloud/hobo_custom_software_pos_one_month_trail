"""
AI API: best-sellers, suggest (upsell), ask (market tips / questions).
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .services import get_best_sellers, suggest_upsell, ask, get_smart_business_insights, get_sale_auto_tips, _is_configured


class BestSellersView(APIView):
    """အရောင်းရဆုံး စာရင်း — GET"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        limit = min(int(request.query_params.get('limit', 15)), 50)
        items = get_best_sellers(limit=limit)
        return Response({'items': items})


class SuggestUpsellView(APIView):
    """ဒါလေးရောမလိုဘူးလား — cart အပေါ် အခြေခံ အကြံပြုချက်။ POST: product_ids[], product_names[]"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_ids = request.data.get('product_ids') or []
        product_names = request.data.get('product_names') or []
        if not isinstance(product_ids, list):
            product_ids = [product_ids] if product_ids else []
        if not isinstance(product_names, list):
            product_names = [product_names] if product_names else []
        suggestions = suggest_upsell(product_ids=product_ids, product_names=product_names)
        return Response({'suggestions': suggestions, 'ai_configured': _is_configured()})


class AskView(APIView):
    """မေးခွန်းမေးမြန်းခြင်း — ဥပမာ အရောင်းရဆုံးစာရင်းပြပါ၊ ဈေးကွက်မှာ အကောင်းဆုံးဖြစ်အောင်။ POST: question"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        question = (request.data.get('question') or '').strip()
        if not question:
            return Response(
                {'error': 'question ထည့်ပါ။'},
                status=status.HTTP_400_BAD_REQUEST
            )
        answer = ask(question)
        return Response({'answer': answer, 'ai_configured': _is_configured()})


class SaleAutoTipsView(APIView):
    """Sale အတွက် အကြံပြုချက် — prompt မလိုပါ။ POST: product_ids[], product_names[] → suggestions, price_tip, promotion_tip"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_ids = request.data.get('product_ids') or []
        product_names = request.data.get('product_names') or []
        if not isinstance(product_ids, list):
            product_ids = [product_ids] if product_ids else []
        if not isinstance(product_names, list):
            product_names = [product_names] if product_names else []
        result = get_sale_auto_tips(product_ids=product_ids, product_names=product_names)
        return Response(result)


class SmartInsightsView(APIView):
    """Smart Business Insight — sales + USD rate analysis, price & reorder suggestions (Burmese)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        insights = get_smart_business_insights()
        return Response({'insights': insights})
