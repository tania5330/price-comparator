import os
import json
import random
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..database import get_product, get_price_history

router = APIRouter()

# Manually load .env file from the root directory to populate environment variables
_backend_dir = os.path.dirname(os.path.dirname(__file__))
_root_dir = os.path.dirname(_backend_dir)
_env_path = os.path.join(_root_dir, ".env")

if os.path.exists(_env_path):
    with open(_env_path, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _val = _line.split("=", 1)
                os.environ[_key.strip()] = _val.strip()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
print("OPENAI_API_KEY cargada:", "SÍ" if OPENAI_API_KEY else "NO")



# ─── Pydantic models ────────────────────────────────────────────────────────

class AdvisorRequest(BaseModel):
    product_id: str


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    product_id: Optional[str] = None


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _build_product_context(product_id: str) -> dict:
    """Fetch product details and price history to build context for the AI."""
    product = get_product(product_id)
    history = get_price_history(product_id)

    prices = [h["price"] for h in history if h.get("price")]
    avg_price = round(sum(prices) / len(prices), 2) if prices else None
    min_price = min(prices) if prices else None
    max_price = max(prices) if prices else None
    current_price = product.get("price") if product else None

    return {
        "product": product,
        "history": history,
        "current_price": current_price,
        "avg_price": avg_price,
        "min_price": min_price,
        "max_price": max_price,
        "price_count": len(prices),
    }


def _mock_advisor_response(ctx: dict) -> dict:
    """Generate a realistic mock advisor response when OpenAI is not configured."""
    product = ctx["product"] or {}
    current = ctx["current_price"]
    avg = ctx["avg_price"]
    minimum = ctx["min_price"]

    name = product.get("name", "Este producto")

    if current and avg and minimum:
        diff_pct = round(((current - avg) / avg) * 100, 1)
        if diff_pct <= -10:
            verdict = "BUY"
            reason = (
                f"{name} está {abs(diff_pct)}% por debajo de su precio promedio histórico "
                f"(${avg}). Actualmente es de los mejores momentos para comprarlo."
            )
            tips = [
                f"El precio mínimo histórico fue ${minimum}. Estás muy cerca.",
                "Aprovechá ahora antes de que suba nuevamente.",
                "Comparar con otras tiendas puede ayudarte a encontrar un precio aún mejor.",
            ]
        elif diff_pct >= 10:
            verdict = "WAIT"
            reason = (
                f"{name} está {diff_pct}% por encima de su precio promedio histórico "
                f"(${avg}). Los datos muestran que suele bajar."
            )
            tips = [
                f"El precio mínimo registrado fue ${minimum}. Todavía hay margen de baja.",
                "Creá una alerta de precio para que te notifiquen cuando baje.",
                "Los fines de mes y durante promociones especiales suelen tener mejores precios.",
            ]
        else:
            verdict = "HOLD"
            reason = (
                f"{name} está a un precio cercano a su promedio histórico (${avg}). "
                "No es el mejor momento pero tampoco el peor."
            )
            tips = [
                "Podés esperar una baja sin perder demasiado.",
                "Activá una alerta de precio para no perder oportunidades.",
                "Compará con tiendas alternativas antes de decidir.",
            ]
    else:
        verdicts = ["BUY", "WAIT", "HOLD"]
        verdict = random.choice(verdicts)
        reason = (
            f"No hay suficiente historial de precios para {name}. "
            "Revisá el gráfico histórico para más contexto."
        )
        tips = [
            "Guardá este producto en favoritos para seguir su precio.",
            "Creá una alerta de precio para recibir notificaciones.",
            "Comparar entre varias tiendas siempre es una buena práctica.",
        ]

    return {"verdict": verdict, "reason": reason, "tips": tips}


def _mock_chat_response(messages: list[ChatMessage], ctx: dict | None) -> str:
    """Generate a realistic mock chat response when OpenAI is not configured."""
    last_user_msg = ""
    for m in reversed(messages):
        if m.role == "user":
            last_user_msg = m.content.lower()
            break

    if ctx and ctx.get("product"):
        product = ctx["product"]
        name = product.get("name", "el producto")
        price = ctx.get("current_price")
        avg = ctx.get("avg_price")
        verdict_data = _mock_advisor_response(ctx)

        if any(word in last_user_msg for word in ["conviene", "compro", "comprar", "precio", "caro", "barato"]):
            return (
                f"Basándome en el historial de precios de **{name}**, mi recomendación es: "
                f"**{verdict_data['verdict']}**.\n\n"
                f"{verdict_data['reason']}\n\n"
                + "\n".join(f"• {t}" for t in verdict_data["tips"])
            )
        if price:
            return (
                f"**{name}** actualmente cuesta **${price}**"
                + (f" (promedio histórico: ${avg})" if avg else "")
                + f". {verdict_data['reason']}"
            )

    generic_responses = [
        "Para encontrar el mejor precio, te recomiendo comparar al menos 3 tiendas diferentes y revisar el historial de precios del producto que te interesa.",
        "Una buena estrategia de ahorro es crear alertas de precio. Así te notifican automáticamente cuando el producto baja al valor que querés pagar.",
        "Los mejores momentos para comprar electrónica suelen ser durante eventos como Black Friday, Cyber Monday o liquidaciones de fin de temporada.",
        "¿Tenés un producto específico en mente? Buscálo en la app y puedo analizar su historial de precios para darte una recomendación personalizada.",
    ]
    return random.choice(generic_responses)


async def _call_openai_advisor(ctx: dict) -> dict:
    """Call OpenAI API to analyze purchase timing."""
    try:
        import httpx

        product = ctx["product"] or {}
        system_prompt = (
            "Eres un experto en compras inteligentes y análisis de precios. "
            "Tu rol es ayudar a los usuarios a decidir si es buen momento para comprar un producto. "
            "Responde siempre en español, de forma concisa y práctica. "
            "Devuelve ÚNICAMENTE un JSON válido con la estructura: "
            '{"verdict": "BUY|WAIT|HOLD", "reason": "string", "tips": ["string", ...]}'
        )

        user_content = (
            f"Producto: {product.get('name', 'Desconocido')}\n"
            f"Precio actual: ${ctx['current_price']}\n"
            f"Precio promedio histórico: ${ctx['avg_price']}\n"
            f"Precio mínimo histórico: ${ctx['min_price']}\n"
            f"Precio máximo histórico: ${ctx['max_price']}\n"
            f"Cantidad de registros históricos: {ctx['price_count']}\n\n"
            "¿Es buen momento para comprar? Analiza si el precio actual es conveniente "
            "comparado con el historial y da tu recomendación en el formato JSON indicado."
        )

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    "temperature": 0.4,
                    "max_tokens": 500,
                },
            )
            response.raise_for_status()
            data = response.json()
            raw_content = data["choices"][0]["message"]["content"].strip()

            # Strip markdown code blocks if present
            if raw_content.startswith("```"):
                raw_content = raw_content.split("```")[1]
                if raw_content.startswith("json"):
                    raw_content = raw_content[4:]
            raw_content = raw_content.strip()

            return json.loads(raw_content)
    except Exception as exc:
        print(f"OpenAI advisor error (falling back to mock): {exc}")
        return _mock_advisor_response(ctx)


async def _call_openai_chat(messages: list[ChatMessage], ctx: dict | None) -> str:
    """Call OpenAI API for the shopping assistant chat."""
    try:
        import httpx

        system_prompt = (
            "Eres un asistente experto en compras inteligentes y comparación de precios. "
            "Tu nombre es PriceBot. Ayudas a los usuarios a encontrar las mejores ofertas, "
            "analizar precios históricos y decidir cuándo comprar. "
            "Responde siempre en español, de forma amigable, práctica y concisa. "
            "Si el usuario pregunta sobre un producto específico, usa el contexto provisto. "
            "Usa formato markdown para organizar tu respuesta cuando sea conveniente."
        )

        openai_messages = [{"role": "system", "content": system_prompt}]

        # Inject product context as assistant context if available
        if ctx and ctx.get("product"):
            product = ctx["product"]
            context_info = (
                f"Contexto del producto en análisis:\n"
                f"- Nombre: {product.get('name')}\n"
                f"- Precio actual: ${ctx.get('current_price')}\n"
                f"- Promedio histórico: ${ctx.get('avg_price')}\n"
                f"- Mínimo histórico: ${ctx.get('min_price')}\n"
                f"- Tienda: {product.get('source_name')}\n"
            )
            openai_messages.append({"role": "system", "content": context_info})

        for m in messages:
            openai_messages.append({"role": m.role, "content": m.content})

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": openai_messages,
                    "temperature": 0.7,
                    "max_tokens": 800,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        print(f"OpenAI chat error (falling back to mock): {exc}")
        return _mock_chat_response(messages, ctx)


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/ai/advisor")
async def purchase_advisor(request: AdvisorRequest):
    """Analyze a product's price history and return a buy/wait/hold recommendation."""
    ctx = _build_product_context(request.product_id)

    if not OPENAI_API_KEY:
        result = _mock_advisor_response(ctx)
    else:
        result = await _call_openai_advisor(ctx)

    return result


@router.post("/ai/chat")
async def chat_assistant(request: ChatRequest):
    """Interactive shopping assistant chat powered by OpenAI."""
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages list is required")

    ctx = None
    if request.product_id:
        ctx = _build_product_context(request.product_id)

    if not OPENAI_API_KEY:
        reply = _mock_chat_response(request.messages, ctx)
    else:
        reply = await _call_openai_chat(request.messages, ctx)

    return {"reply": reply}
