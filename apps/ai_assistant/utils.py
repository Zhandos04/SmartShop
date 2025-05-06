import google.generativeai as genai
from django.conf import settings
from .models import AISearchQuery
import json

# Инициализация Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)

def get_gemini_model():
    """Получение модели Gemini"""
    return genai.GenerativeModel('gemini-pro')

def generate_ai_product_description(product_name, attributes):
    """Генерация описания товара с помощью ИИ"""
    model = get_gemini_model()
    
    # Создание запроса к модели
    prompt = f"""
    Создай подробное и привлекательное описание для товара "{product_name}" на основе следующих характеристик:
    
    {json.dumps(attributes, indent=2, ensure_ascii=False)}
    
    Описание должно быть привлекательным для покупателей, подчеркивать преимущества товара 
    и включать информацию о характеристиках. Используй маркетинговый стиль, 
    но будь честным и точным. Пиши на русском языке, 3-4 абзаца текста.
    """
    
    response = model.generate_content(prompt)
    return response.text

def chat_with_ai_assistant(user, message, conversation_history=None):
    """Взаимодействие с ИИ-ассистентом AISha"""
    model = get_gemini_model()
    
    # Сохранение запроса пользователя
    AISearchQuery.objects.create(user=user, query=message)
    
    # Создание системного сообщения для определения контекста
    system_message = """
    Ты AISha - умный ассистент маркетплейса. Твоя задача - помогать пользователям находить нужные товары,
    отвечать на их вопросы и давать рекомендации. Говори на русском языке, будь дружелюбной,
    полезной и информативной. Если ты не можешь ответить на вопрос, предложи связаться с продавцом
    или поддержкой. Старайся быть краткой, но исчерпывающей.
    """
    
    # Подготовка историй сообщений
    if not conversation_history:
        conversation_history = []
    
    # Формирование запроса с историей диалога
    messages = [{"role": "system", "content": system_message}]
    
    for msg in conversation_history:
        role = "user" if msg.role == "user" else "model"
        messages.append({"role": role, "content": msg.content})
    
    messages.append({"role": "user", "content": message})
    
    response = model.generate_content(messages)
    return response.text

def search_products_with_ai(query, user=None):
    """Поиск товаров с помощью ИИ"""
    model = get_gemini_model()
    
    # Если есть пользователь, сохраняем запрос
    if user and user.is_authenticated:
        AISearchQuery.objects.create(user=user, query=query)
    
    # Создание запроса к модели для анализа поискового запроса
    prompt = f"""
    Проанализируй поисковый запрос пользователя: "{query}"
    
    Определи:
    1. Категории товаров, которые могут подойти
    2. Ключевые характеристики, которые важны для пользователя
    3. Возможный ценовой диапазон (если указан)
    4. Другие важные параметры для фильтрации
    
    Ответ дай в формате JSON:
    {{
        "categories": ["категория1", "категория2"],
        "keywords": ["ключевое_слово1", "ключевое_слово2"],
        "price_range": {{"min": минимальная_цена, "max": максимальная_цена}},
        "filters": {{"параметр1": "значение1", "параметр2": "значение2"}}
    }}
    
    Если какой-то параметр не удалось определить, оставь его пустым или null.
    """
    
    response = model.generate_content(prompt)
    
    try:
        search_params = json.loads(response.text)
        return search_params
    except Exception:
        # В случае ошибки разбора JSON, возвращаем базовый поиск по ключевым словам
        return {
            "categories": [],
            "keywords": query.split(),
            "price_range": {"min": None, "max": None},
            "filters": {}
        }