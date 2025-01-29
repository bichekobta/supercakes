import streamlit as st
from openai import OpenAI
import json
from datetime import datetime, timedelta
import pandas as pd
import os

# Configuración inicial de Streamlit
st.set_page_config(page_title="Supercakes - Asistente Virtual", page_icon="🎂")

# Inicialización de variables en session_state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_order' not in st.session_state:
    st.session_state.current_order = {
        'design': None,
        'portions': None,
        'flavor': None,
        'delivery_date': None,
        'price': None
    }

# Configuración de datos
FLAVORS = ['Chocolate', 'Vainilla', 'Fresa', 'Red Velvet']
PRICES = {
    'base': 30000,
    'per_portion': 5000,
    'custom_design': 20000
}

# Configuración de OpenAI
api_key = st.secrets["OPENAI_API_KEY"]  # Cambiamos la API key hardcodeada por una variable
client = OpenAI(api_key=api_key)

def get_bot_response(messages):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": """
                Eres un asistente virtual para Supercakes, una pastelería personalizada.
                
                REGLAS ESTRICTAS DE FORMATO:
                - Usa solo texto plano sin formato
                - No uses cursivas, negritas ni otros formatos especiales
                - Al mencionar precios, usa este formato exacto: "$X pesos"
                - No uses caracteres especiales ni símbolos decorativos
                - No expliques cálculos ni desgloses de precios
                - Da respuestas directas y concisas

                Guía al cliente por estos pasos:
                1. Solicitar detalles del diseño del pastel
                2. Preguntar número de porciones
                3. Seleccionar sabor
                4. Confirmar fecha de entrega
                5. Dar precio final

                Sabores disponibles: 
                - Chocolate
                - Vainilla
                - Fresa
                - Red Velvet

                Precios:
                - Precio base del pastel: $30.000
                - Precio por porción: $5.000
                - Diseño personalizado: $20.000

                Formas de pago:
                1. Transferencia Bancolombia
                   - Cuenta corriente: 20725996629
                   - NIT: 830082679
                   - Nombre: Super Cakes
                2. Nequi: 3165319719

                EJEMPLO DE RESPUESTA CORRECTA:
                "Perfecto, tu pastel estará listo mañana. El total de tu orden es $520.000 pesos."

                EJEMPLO DE RESPUESTA INCORRECTA:
                "El total incluye el precio base más el costo por porciones..."
                """}, 
                *messages
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error al obtener respuesta: {str(e)}")
        return "Lo siento, hubo un error al procesar tu solicitud. Por favor, intenta de nuevo."

def calculate_price(portions, custom_design=True):
    return PRICES['base'] + (portions * PRICES['per_portion']) + (PRICES['custom_design'] if custom_design else 0)

def update_order_details(prompt):
    # Actualizar porciones
    if "porciones" in prompt.lower():
        try:
            portions = int(''.join(filter(str.isdigit, prompt)))
            st.session_state.current_order['portions'] = portions
            st.session_state.current_order['price'] = calculate_price(portions)
        except:
            pass
    
    # Actualizar sabor
    if any(flavor.lower() in prompt.lower() for flavor in FLAVORS):
        for flavor in FLAVORS:
            if flavor.lower() in prompt.lower():
                st.session_state.current_order['flavor'] = flavor
                break

def main():
    st.title("🎂 Supercakes - Asistente Virtual")
    
    # Sidebar con información del pedido
    with st.sidebar:
        st.subheader("📋 Detalles del Pedido")
        for key, value in st.session_state.current_order.items():
            if value:
                if key == 'price':
                    st.write(f"{key.title()}: ${value}")
                else:
                    st.write(f"{key.title()}: {value}")

    # Chat interface
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input del usuario
    if prompt := st.chat_input("¿En qué puedo ayudarte?"):
        # Mostrar mensaje del usuario
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Obtener y mostrar respuesta del bot
        with st.chat_message("assistant"):
            bot_response = get_bot_response(st.session_state.messages)
            st.markdown(bot_response)
            st.session_state.messages.append({"role": "assistant", "content": bot_response})

        # Actualizar detalles del pedido
        update_order_details(prompt)

if __name__ == "__main__":
    main()
