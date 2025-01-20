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
if 'reference_images' not in st.session_state:
    st.session_state.reference_images = []

# Configuración de datos
FLAVORS = ['Chocolate', 'Vainilla', 'Fresa', 'Red Velvet']
PRICES = {
    'base': 30,
    'per_portion': 5,
    'custom_design': 20
}

# Configuración de OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def generate_cake_image(prompt):
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=f"Un pastel realista y profesional con el siguiente diseño: {prompt}. El pastel debe verse apetitoso y fotográfico.",
            size="1024x1024",
            quality="standard",
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        st.error(f"Error al generar la imagen: {str(e)}")
        return None

def get_bot_response(messages):
    try:
        # Convertir las imágenes de referencia en texto descriptivo
        image_context = ""
        if st.session_state.reference_images:
            image_context = "\nEl cliente ha proporcionado imágenes de referencia para el diseño del pastel."

        response = client.chat.completions.create(
            model="gpt-4.0",
            messages=[
                {"role": "system", "content": f"""
                Eres un asistente virtual para Supercakes, una pastelería personalizada.
                Debes ser amable y profesional. Guía al cliente por estos pasos:
                1. Solicitar detalles del diseño del pastel y ofrecer generar una imagen de ejemplo
                2. Preguntar número de porciones
                3. Seleccionar sabor
                4. Confirmar fecha de entrega
                5. Dar precio final y opciones de pago
                
                Sabores disponibles: Chocolate, Vainilla, Fresa, Red Velvet
                Precio base: $30 + $5 por porción + $20 por diseño personalizado
                
                Si el cliente sube imágenes de referencia, agradece y confirma que las has recibido.
                Si el cliente solicita ver un ejemplo del pastel, ofrece generar una imagen.
                {image_context}
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
    
    # Sidebar con información del pedido y carga de imágenes
    with st.sidebar:
        st.subheader("📋 Detalles del Pedido")
        for key, value in st.session_state.current_order.items():
            if value:
                if key == 'price':
                    st.write(f"{key.title()}: ${value}")
                else:
                    st.write(f"{key.title()}: {value}")
        
        # Sección para subir imágenes de referencia
        st.subheader("📎 Subir Imagen de Referencia")
        uploaded_file = st.file_uploader(
            "Sube una imagen de referencia para tu pastel",
            type=['png', 'jpg', 'jpeg'],
            key="reference_upload"
        )
        
        if uploaded_file:
            # Mostrar la imagen subida
            st.image(uploaded_file, caption="Imagen de referencia")
            
            # Agregar la imagen al historial si no está ya
            if uploaded_file not in st.session_state.reference_images:
                st.session_state.reference_images.append(uploaded_file)
                # Agregar mensaje al chat sobre la imagen subida
                st.session_state.messages.append({
                    "role": "user",
                    "content": "He subido una imagen de referencia para el diseño del pastel.",
                    "image": uploaded_file
                })
                # Obtener respuesta del bot sobre la imagen
                bot_response = get_bot_response(st.session_state.messages)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": bot_response
                })
        
        # Mostrar imágenes de referencia previas
        if st.session_state.reference_images:
            st.subheader("🖼️ Imágenes de Referencia")
            for img in st.session_state.reference_images:
                st.image(img, width=150)

    # Chat interface
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # Mostrar imagen si existe en el mensaje
            if "image" in message:
                st.image(message["image"], caption="Imagen de referencia")
            if "image_url" in message:
                st.image(message["image_url"], caption="Diseño sugerido del pastel")

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
            
            # Generar imagen si se menciona ver o mostrar el diseño
            if any(keyword in prompt.lower() for keyword in ["muestra", "imagen", "diseño", "ejemplo", "ver"]):
                with st.spinner('Generando imagen del pastel...'):
                    image_url = generate_cake_image(prompt)
                    if image_url:
                        st.image(image_url, caption="Diseño sugerido del pastel")
                        # Guardar la URL de la imagen en el mensaje
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": bot_response,
                            "image_url": image_url
                        })
            else:
                st.session_state.messages.append({"role": "assistant", "content": bot_response})

        # Actualizar detalles del pedido
        update_order_details(prompt)

if __name__ == "__main__":
    main()
