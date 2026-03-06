"""
AI services for POS: upsell suggestions, best sellers, ask (market tips / best sellers list).
Uses OPENAI_API_KEY or AI_API_URL (e.g. Ollama). If not set, suggestions/ask return empty or friendly message.
"""
import os
import json
import requests
from django.db.models import Sum


def _get_api_key():
    return os.environ.get('OPENAI_API_KEY', '').strip()


def _get_api_url():
    """Ollama ဆိုရင် http://localhost:11434/v1/chat/completions"""
    return os.environ.get('AI_API_URL', 'https://api.openai.com/v1/chat/completions').rstrip('/')


def _is_configured():
    url = _get_api_url()
    if 'openai.com' in url:
        return bool(_get_api_key())
    return True  # Ollama etc. may not need key


def _call_llm(messages, max_tokens=800):
    """Generic chat completion call (OpenAI-compatible). Returns assistant content or None."""
    api_key = _get_api_key()
    api_url = _get_api_url()
    if not api_url:
        return None
    headers = {'Content-Type': 'application/json'}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    payload = {
        'model': os.environ.get('AI_MODEL', 'gpt-4o-mini'),
        'messages': messages,
        'max_tokens': max_tokens,
    }
    try:
        r = requests.post(api_url, json=payload, headers=headers, timeout=30)
        if r.status_code != 200:
            return None
        data = r.json()
        choice = data.get('choices', [{}])[0]
        return (choice.get('message') or {}).get('content', '').strip()
    except Exception:
        return None


def get_best_sellers(limit=15):
    """အရောင်းရဆုံး ပစ္စည်းစာရင်း (approved sales မှ)"""
    from inventory.models import SaleItem
    qs = (
        SaleItem.objects.filter(sale_transaction__status='approved')
        .values('product_id', 'product__name', 'product__sku')
        .annotate(total_quantity=Sum('quantity'))
        .order_by('-total_quantity')[:limit]
    )
    return [
        {
            'product_id': x['product_id'],
            'product_name': x['product__name'] or '',
            'sku': x['product__sku'] or '',
            'total_quantity': int(x['total_quantity']),
            'rank': i + 1,
        }
        for i, x in enumerate(qs)
    ]


def get_sales_context_text():
    """AI ကို context ပေးမယ့် စာသား (အရောင်းရဆုံး + ယနေ့အရောင်း စသည်)"""
    from django.utils import timezone
    from inventory.models import SaleItem, SaleTransaction
    best = get_best_sellers(10)
    lines = ['အရောင်းရဆုံး ပစ္စည်းများ:']
    for b in best:
        lines.append(f"  {b['rank']}. {b['product_name']} (SKU: {b['sku']}) - ရောင်းရေအင်း {b['total_quantity']}")
    today = timezone.now().date()
    today_sales = SaleTransaction.objects.filter(
        status='approved', created_at__date=today
    ).aggregate(s=Sum('total_amount'))['s'] or 0
    today_count = SaleTransaction.objects.filter(status='approved', created_at__date=today).count()
    lines.append(f'\nယနေ့ ({today}) အရောင်း: စုစုပေါင်း {today_count} ဘောက်ချာ, ငွေစုစုပေါင်း {today_sales:.0f} MMK။')
    return '\n'.join(lines)


def suggest_upsell(product_ids=None, product_names=None):
    """
    Cart ထဲက ပစ္စည်းတွေအပေါ် အခြေခံပြီး "ဒါလေးရောမလိုဘူးလား" အကြံပြုချက်။
    Returns list of { product_id, product_name, reason } (reason in Burmese).
    """
    product_ids = product_ids or []
    product_names = product_names or []
    from inventory.models import Product, SaleItem
    # Already best sellers that are NOT in cart
    best = get_best_sellers(20)
    best_ids = {b['product_id'] for b in best}
    cart_ids = set(product_ids)
    candidates = [b for b in best if b['product_id'] not in cart_ids][:5]
    if not _is_configured():
        # No API: return top sellers not in cart as simple suggestions
        return [
            {'product_id': c['product_id'], 'product_name': c['product_name'], 'reason': 'အရောင်းရဆုံး စာရင်းမှ ဖြစ်ပါသည်။'}
            for c in candidates[:3]
        ]
    cart_desc = ', '.join(product_names[:10]) if product_names else f'product ids: {list(cart_ids)[:5]}'
    product_list = list(Product.objects.filter(id__in=[b['product_id'] for b in candidates]).values_list('name', flat=True))
    prompt = f"""You are a helpful POS assistant for a Myanmar retail shop. The customer's cart currently has: {cart_desc}.
Suggest 2 to 3 products from this list that often go well together or are commonly bought together. Reply in JSON array only, no other text.
Product list to suggest from: {product_list}
Format each item: {{"product_name": "<exact name from list>", "reason": "<short reason in Burmese, e.g. ဒါလေးရောမလိုဘူးလား or ဒီပစ္စည်းနဲ့ တွဲသုံးလို့ကောင်းပါတယ်>"}}"""
    out = _call_llm([{'role': 'user', 'content': prompt}], max_tokens=400)
    if not out:
        return [
            {'product_id': c['product_id'], 'product_name': c['product_name'], 'reason': 'အရောင်းရဆုံး စာရင်းမှ ဖြစ်ပါသည်။'}
            for c in candidates[:3]
        ]
    try:
        # Extract JSON array from output
        text = out.strip()
        if '```' in text:
            text = text.split('```')[1].replace('json', '').strip()
        arr = json.loads(text)
        result = []
        for item in arr[:3]:
            name = (item.get('product_name') or '').strip()
            reason = (item.get('reason') or 'ဒါလေးရောမလိုဘူးလား').strip()
            match = next((b for b in candidates if b['product_name'] == name), None)
            if match:
                result.append({'product_id': match['product_id'], 'product_name': name, 'reason': reason})
        return result if result else [
            {'product_id': c['product_id'], 'product_name': c['product_name'], 'reason': 'ဒါလေးရောမလိုဘူးလား'}
            for c in candidates[:3]
        ]
    except Exception:
        return [
            {'product_id': c['product_id'], 'product_name': c['product_name'], 'reason': 'အရောင်းရဆုံး စာရင်းမှ ဖြစ်ပါသည်။'}
            for c in candidates[:3]
        ]


def ask(question):
    """
    မေးခွန်းမေးမြန်းခြင်း — ဥပမာ "အရောင်းရဆုံးစာရင်းပြပါ", "ဈေးကွက်မှာ အကောင်းဆုံးဖြစ်အောင် ဘယ်လိုလုပ်သင့်သလဲ"
    Context မှာ best sellers + today sales ထည့်ပေးမယ်။
    """
    context = get_sales_context_text()
    if not _is_configured():
        if 'အရောင်းရဆုံး' in question or 'best' in question.lower():
            lines = [f"{b['rank']}. {b['product_name']} — ရောင်းရေအင်း {b['total_quantity']}" for b in get_best_sellers(10)]
            return 'အရောင်းရဆုံး ပစ္စည်းများ:\n\n' + '\n'.join(lines) + '\n\n(AI ချိတ်ဆက်မထားသေးပါ။ စာရင်းသာ ပြသထားပါသည်။)'
        return 'AI ကို မချိတ်ဆက်ရသေးပါ။ OPENAI_API_KEY သို့မဟုတ် AI_API_URL သတ်မှတ်ပါ။'
    prompt = f"""You are a helpful business assistant for a Myanmar POS/shop. Use the following store data to answer the user's question. Reply in Burmese, concise and practical.

Store data:
{context}

User question: {question}"""
    out = _call_llm([{'role': 'user', 'content': prompt}], max_tokens=600)
    return out or 'အဖြေရယူ၍မရပါ။ နောက်မှ ထပ်ကြိုးစားပါ။'


def get_sale_auto_tips(product_ids=None, product_names=None):
    """
    Sale အတွက် အကြံပြုချက် — prompt မလိုပါ။ Cart context ပေးရင် ဒါလေးရောမလိုဘူးလား + ဈေးအကြံပြု + ပရိုမိုးရှင်းအကြံပြု ပြန်မယ်။
    """
    suggestions = suggest_upsell(product_ids=product_ids or [], product_names=product_names or [])
    price_tip = None
    promotion_tip = None
    try:
        from inventory.models import GlobalSetting
        gs = GlobalSetting.objects.filter(key='usd_exchange_rate').first()
        rate = float(gs.value_decimal) if gs and gs.value_decimal else None
        if rate and rate > 0:
            price_tip = 'ယနေ့ဒေါ်လာဈေးနှုန်းနဲ့ ကိုက်အောင် ဈေးအနည်းငယ်တင်ရောင်းရန် စဉ်းစားပါ။'
    except Exception:
        pass
    best = get_best_sellers(5)
    if best:
        names = [b['product_name'] for b in best[:2]]
        promotion_tip = f'အရောင်းရဆုံး ပစ္စည်း ({", ".join(names)}) ကို ပရိုမိုးရှင်းလုပ်ရန် အကြံပြုပါသည်။'
    if _is_configured() and (product_names or product_ids):
        cart_desc = ', '.join((product_names or [])[:5]) or 'cart'
        prompt = f"""Myanmar shop POS. Customer cart has: {cart_desc}. Write ONE very short marketing tip in Burmese (e.g. တွဲရောင်းလျှင် အနည်းငယ်လျှော့ပေးပါ or ယနေ့ဈေးနှုန်း စဉ်းစားပါ). One sentence only, no quotes."""
        extra = _call_llm([{'role': 'user', 'content': prompt}], max_tokens=60)
        if extra and not promotion_tip:
            promotion_tip = extra.strip()
    return {
        'suggestions': suggestions,
        'price_tip': price_tip or '',
        'promotion_tip': promotion_tip or '',
    }


def get_marketing_insights_for_owner():
    """
    Owner အတွက် marketing အကြံပြုချက် — prompt မလိုပါ။ ဒေတာအခြေခံ (အရောင်းရဆုံး၊ လက်ကျန်) နဲ့ ထုတ်မယ်။
    """
    tips = []
    try:
        best = get_best_sellers(5)
        if best:
            names = [b['product_name'] for b in best[:2]]
            tips.append(f'အရောင်းရဆုံး ပစ္စည်း ({", ".join(names)}) ကို ဒီအပတ် ကြော်ငြာ/ပရိုမိုးရှင်းလုပ်ရန် အကြံပြုပါသည်။')
        from inventory.models import Product
        from django.db.models import Sum
        from django.utils import timezone
        from datetime import timedelta
        today = timezone.now().date()
        since = today - timedelta(days=7)
        from inventory.models import SaleItem
        velocity = (
            SaleItem.objects.filter(sale_transaction__status='approved', sale_transaction__created_at__date__gte=since)
            .values('product_id').annotate(total_qty=Sum('quantity')).order_by('-total_qty')[:5]
        )
        low_velocity_names = []
        for v in velocity:
            try:
                p = Product.objects.get(pk=v['product_id'])
                if p.total_stock_qty <= 5 and v['total_qty']:
                    low_velocity_names.append(p.name)
            except Exception:
                continue
        if low_velocity_names:
            tips.append(f'လက်ကျန် နည်းပါးသော ပစ္စည်း ({", ".join(low_velocity_names[:2])}) ကို ဈေးချပြီး ရောင်းချရန် စဉ်းစားပါ။')
        if _is_configured() and tips:
            prompt = f"""Myanmar shop owner. Marketing tips so far: {" | ".join(tips)}. Add ONE more short actionable marketing sentence in Burmese (same style). One sentence only."""
            extra = _call_llm([{'role': 'user', 'content': prompt}], max_tokens=80)
            if extra:
                tips.append(extra.strip())
    except Exception:
        pass
    return tips


def get_smart_business_insights():
    """
    Analyze sales + USD rate history; return short actionable Burmese insights for Bento card.
    - Price: suggest raising price if USD trend up (avoid loss from inflation).
    - Reorder: products with high sales velocity and low stock.
    """
    from django.utils import timezone
    from django.db.models import Sum
    from decimal import Decimal

    insights = []
    today = timezone.now().date()

    # --- 1. Profit Margin Analysis (P&L) - Check if shrinking due to USD inflation ---
    try:
        from accounting.services import analyze_profit_margin_shrinkage
        margin_analysis = analyze_profit_margin_shrinkage()
        
        if margin_analysis['is_shrinking'] and margin_analysis['usd_rising']:
            # Critical: Profit margin shrinking + USD rising = suggest price increase
            insights.append(margin_analysis['suggestion'])
        elif margin_analysis['is_shrinking']:
            # Margin shrinking but not due to USD - still suggest review
            insights.append(margin_analysis['suggestion'])
        elif margin_analysis['usd_rising']:
            # USD rising but margin OK - preventive suggestion
            insights.append(margin_analysis['suggestion'])
    except Exception:
        # Fallback to old USD rate check if accounting module not available
        try:
            from inventory.models import GlobalSetting, ExchangeRateLog
            gs = GlobalSetting.objects.filter(key='usd_exchange_rate').first()
            current_rate = float(gs.value_decimal) if gs and gs.value_decimal else None
            logs = list(
                ExchangeRateLog.objects.filter(date__lt=today).order_by('-date')[:7].values_list('rate', flat=True)
            )
            if current_rate is not None and logs:
                from decimal import Decimal
                avg_past = sum(float(r) for r in logs) / len(logs)
                if current_rate > avg_past * 1.02:
                    insights.append(
                        'ဒေါ်လာဈေးတက်နိုင်သဖြင့် ဈေးအနည်းငယ်တင်ရောင်းရန် အကြံပြုပါသည်။'
                    )
                elif current_rate < avg_past * 0.98:
                    insights.append('ဒေါ်လာဈေးကျသွားပါက ယှဉ်ပြိုင်ဈေးနှုန်း ချပြီး ရောင်းနိုင်ပါသည်။')
            elif current_rate is not None:
                insights.append('ယနေ့ဒေါ်လာဈေးနှုန်းကို စစ်ဆေးပြီး ဈေးတင်ရောင်းရန် စဉ်းစားပါ။')
        except Exception:
            pass

    # --- 2. Reorder: high velocity + low stock ---
    try:
        from inventory.models import SaleItem, Product
        from datetime import timedelta
        since = today - timedelta(days=7)
        velocity = (
            SaleItem.objects.filter(
                sale_transaction__status='approved',
                sale_transaction__created_at__date__gte=since,
            )
            .values('product_id')
            .annotate(total_qty=Sum('quantity'))
            .order_by('-total_qty')[:15]
        )
        reorder_added = 0
        for v in velocity:
            if reorder_added >= 3:
                break
            try:
                p = Product.objects.get(pk=v['product_id'])
                stock = p.total_stock_qty
                if stock <= 10 and v['total_qty'] and v['total_qty'] > 0:
                    insights.append(f'ပစ္စည်း "{p.name}" ကို ပြန်မှာသင့်ပါပြီ။ (ရောင်းရေအင်း များ၍ လက်ကျန် နည်းပါသည်။)')
                    reorder_added += 1
            except (Product.DoesNotExist, Exception):
                continue
    except Exception:
        pass

    # --- 2.5 လအလိုက် discount အကြံပြုချက် (နောက်ဆုံး ၆၀ ရက် အရောင်းရဆုံး ပစ္စည်းများကို လျှော့ဈေး အကြံပြု) ---
    try:
        from inventory.models import SaleItem
        from datetime import timedelta
        since = today - timedelta(days=60)
        top_sold = (
            SaleItem.objects.filter(
                sale_transaction__status='approved',
                sale_transaction__created_at__date__gte=since,
            )
            .values('product_id', 'product__name')
            .annotate(total_qty=Sum('quantity'))
            .order_by('-total_qty')[:5]
        )
        top_names = [row.get('product__name') or '' for row in top_sold if row.get('product__name')]
        if top_names:
            names_str = ', '.join(top_names[:2]) if len(top_names) >= 2 else top_names[0]
            insights.append(
                f'လအလိုက် ပရိုမိုးရှင်း: အရောင်းရဆုံး ပစ္စည်းများ ({names_str}) ကို အနည်းငယ် လျှော့ဈေး ပေးပြီး ရောင်းသင့်ပါသည်။'
            )
    except Exception:
        pass

    # --- 2.6 ဆေးသက်တမ်းကုန်ခါနီး / Expiry warning (Pharmacy/Clinic) ---
    try:
        from inventory.models import Product
        from datetime import timedelta
        expiry_cutoff = today + timedelta(days=30)
        expiring = Product.objects.filter(
            expiry_date__isnull=False,
            expiry_date__lte=expiry_cutoff,
            expiry_date__gte=today,
        ).order_by('expiry_date')[:10]
        if expiring.exists():
            names = list(expiring.values_list('name', flat=True)[:3])
            names_str = ', '.join(names) if len(names) <= 2 else (names[0] + ' စသည်')
            insights.append(
                f'ဆေးသက်တမ်းကုန်ခါနီး ပစ္စည်းများ ရှိပါသည်။ ကြိုတင်မှာယူပါ။ ({names_str})'
            )
        # Already expired
        expired_count = Product.objects.filter(expiry_date__isnull=False, expiry_date__lt=today).count()
        if expired_count > 0:
            insights.append(
                f'သက်တမ်းကုန်ပြီး ပစ္စည်း {expired_count} မျိုး ရှိပါသည်။ စစ်ဆေးဖယ်ရှားပါ။'
            )
    except Exception:
        pass

    # --- 3. Owner marketing advice (no prompt) ---
    insights.extend(get_marketing_insights_for_owner())

    # --- 4. Optional: LLM one-liner summary (Gemini/OpenAI) ---
    if _is_configured() and insights:
        summary = ' | '.join(insights[:3])
        prompt = f"""Based on these short business insights for a Myanmar shop, write ONE extra short actionable sentence in Burmese (same style). Only output that one sentence, no quotes. Insights: {summary}"""
        extra = _call_llm([{'role': 'user', 'content': prompt}], max_tokens=80)
        if extra and extra not in insights:
            insights.append(extra.strip())
    elif not insights:
        insights.append('ဒေတာ စုစည်းပြီး နောက်ထပ် အကြံပြုချက်များြသမည်။')

    return insights
