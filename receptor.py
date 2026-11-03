# ============================================================
#  Receptor de señales de TradingView -> Telegram
#  Programa con TradingView (Pine Script + webhook)
#
#  Qué hace:
#    1. TradingView dispara una alerta (COMPRA o VENTA) y la
#       manda por webhook a este programa.
#    2. El programa reenvía la señal a tu Telegram al instante.
#
#  Cómo correrlo:
#    pip install -r requirements.txt
#    TELEGRAM_BOT_TOKEN=tu_token TELEGRAM_CHAT_ID=tu_chat_id python receptor.py
#
#  Variables de entorno:
#    TELEGRAM_BOT_TOKEN : token del bot creado con @BotFather
#    TELEGRAM_CHAT_ID   : tu ID de chat de Telegram
#    WEBHOOK_TOKEN      : (opcional) clave secreta. Si la pones,
#                         la URL del webhook debe llevar
#                         ?token=TU_CLAVE al final.
#    PORT               : puerto (por defecto 5000)
# ============================================================

import json
import os

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
WEBHOOK_TOKEN = os.environ.get("WEBHOOK_TOKEN", "")


def enviar_telegram(texto):
    """Manda un mensaje con el bot de Telegram. Devuelve (código, respuesta)."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    respuesta = requests.post(
        url,
        json={"chat_id": TELEGRAM_CHAT_ID, "text": texto},
        timeout=15,
    )
    return respuesta.status_code, respuesta.text


def formatear_mensaje(cuerpo):
    """Si TradingView mandó JSON, lo ordena bonito; si no, lo pasa tal cual."""
    try:
        datos = json.loads(cuerpo)
        if isinstance(datos, dict) and "senal" in datos:
            emoji = "🟢 COMPRA" if datos["senal"] == "COMPRA" else "🔴 VENTA"
            return (
                f"{emoji} {datos.get('simbolo', '')}\n"
                f"Precio: {datos.get('precio', '')}\n"
                f"Hora: {datos.get('hora', '')}"
            )
    except Exception:
        pass
    return cuerpo


@app.route("/webhook", methods=["POST"])
def webhook():
    # Seguridad opcional: solo acepta si el token de la URL coincide
    if WEBHOOK_TOKEN and request.args.get("token") != WEBHOOK_TOKEN:
        return jsonify({"ok": False, "error": "token inválido"}), 403

    cuerpo = request.get_data(as_text=True)
    if not cuerpo.strip():
        return jsonify({"ok": False, "error": "mensaje vacío"}), 400

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "falta configurar TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID",
                }
            ),
            500,
        )

    mensaje = "📈 Señal TradingView\n" + formatear_mensaje(cuerpo)
    codigo, respuesta = enviar_telegram(mensaje)
    if codigo != 200:
        return jsonify({"ok": False, "error": respuesta}), 502
    return jsonify({"ok": True})


@app.route("/", methods=["GET"])
def salud():
    return "Receptor de señales TradingView activo ✅"


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=puerto)
