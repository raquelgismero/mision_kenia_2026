import streamlit as st
import warnings
import json
import zipfile
import io
from google import genai
from google.genai import types
from pydantic import BaseModel
from gtts import gTTS

warnings.filterwarnings('ignore')

# 1. Configuración de la IA
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# 2. Estructura de datos GLOBAL (Adaptada a tu tabla)
class Palabra(BaseModel):
    espanol: str
    palabra_local: str
    pronunciacion_figurada: str

class Dia(BaseModel):
    titulo: str
    descripcion: str
    vocabulario: list[Palabra]

class Temario(BaseModel):
    idioma_principal: str 
    dias: list[Dia]

# 3. Configuración visual
st.set_page_config(page_title="Vocabulario de Misión", page_icon="🌍", layout="centered")

st.title("✝️ En misión con Cristo")
st.markdown("*«Tenía entonces toda la tierra una sola lengua y unas mismas palabras.»* — Génesis 11:1")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("🙌 Sobre este proyecto")
    st.write("Herramienta desarrollada con cariño por **Raquel** y un grupo de voluntarios rumbo a Kenia.")
    st.info("¿Nos ayudas con nuestra misión?")
    st.markdown("[👉 **Haz tu donación aquí**](https://misionkenia.lovable.app/#) 💙")
    st.markdown("[📸 **Instagram: @to_kenya_4jesus**](https://www.instagram.com/to_kenya_4jesus)")
    st.divider()
    st.caption("Hecho con ❤️ y de la mano de Dios.")

tab_aprender, tab_comunidad, tab_viaje = st.tabs(["📚 Aprender", "💬 Comunidad", "✈️ Guía de Viaje"])

with tab_aprender:
    st.header("1. Diseña tu temario de Misión")
    
    destinos_mundiales = {
        "Kenia": ["Huruma", "Zona Desértica", "Nairobi", "Otra"],
        "Filipinas": ["Manila", "Cebú", "Mindanao", "Otra"],
        "Perú": ["Iquitos (Amazonas)", "Cusco", "Lima", "Otra"],
        "India": ["Calcuta", "Nueva Delhi", "Tamil Nadu", "Otra"],
        "Otro País": ["Especificar ciudad o región..."]
    }
    
    pais = st.selectbox("¿A qué país vas de misión?", list(destinos_mundiales.keys()))
    
    if pais == "Otro País":
        pais_final = st.text_input("Escribe el nombre del país:")
        region_final = st.text_input("Escribe la región o ciudad:")
    else:
        pais_final = pais
        region_final = st.selectbox(f"¿A qué región de {pais} vas?", destinos_mundiales[pais])
    
    mision = st.multiselect("Enfoque de tu misión:", ["Trabajo Social", "Atención Médica", "Educación con niños", "Construcción", "Evangelización"])
    dias = st.slider("Días de estudio:", 1, 30, 14)
    
    # Inicializar memoria para que el temario no se borre al chatear
    if "datos_temario" not in st.session_state:
        st.session_state.datos_temario = None
        st.session_state.idioma_real = None
        st.session_state.zip_buffer = None
        st.session_state.chat_ia = None
        st.session_state.mensajes = []

    if st.button("Generar Temario de Misión"):
        if not mision or not pais_final or not region_final:
            st.warning("Rellena todos los campos (País, Región y Enfoque).")
        else:
            with st.spinner("Creando temario y generando audios... esto puede tardar un poquito ⏳"):
                prompt = f"""
                Actúa como experto lingüista. Genera un temario de supervivencia.
                Destino: {region_final}, {pais_final}. Enfoque: {', '.join(mision)}. Días: {dias}.
                Instrucciones:
                1. 'idioma_principal': Macrolengua o idioma principal.
                2. Estructura usando 'Día 1', 'Día 2', etc.
                3. Proporciona: espanol, palabra_local, y pronunciacion_figurada (cómo se lee fonéticamente en español, ej: / jalo /).
                """
                
                try:
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=Temario,
                        ),
                    )
                    
                    datos = json.loads(response.text)
                    idioma_real = datos.get("idioma_principal", "Idioma Local")
                    
                    # Generar audios y archivo ZIP en segundo plano
                    zip_buffer = io.BytesIO()
                    texto_descarga = f"TEMARIO DE MISIÓN: {region_final}, {pais_final}\nIDIOMA: {idioma_real.upper()}\n\n"
                    
                    lang_code = 'en'
                    if 'suajili' in idioma_real.lower() or 'swahili' in idioma_real.lower(): lang_code = 'sw'
                    elif 'filipino' in idioma_real.lower() or 'tagalo' in idioma_real.lower(): lang_code = 'tl'
                    elif 'hindi' in idioma_real.lower(): lang_code = 'hi'
                    elif 'español' in idioma_real.lower(): lang_code = 'es'

                    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                        for dia in datos["dias"]:
                            texto_descarga += f"--- {dia['titulo'].upper()} ---\n{dia['descripcion']}\n"
                            for pal in dia["vocabulario"]:
                                texto_descarga += f"{pal['espanol']} | {pal['palabra_local']} | Se lee: {pal['pronunciacion_figurada']}\n"
                                
                                # Generar audio MP3 y guardarlo en el ZIP
                                try:
                                    tts = gTTS(text=pal['palabra_local'], lang=lang_code)
                                    audio_fp = io.BytesIO()
                                    tts.write_to_fp(audio_fp)
                                    zip_file.writestr(f"audios/{pal['espanol'].replace(' ', '_')}.mp3", audio_fp.getvalue())
                                except:
                                    pass
                            texto_descarga += "\n"
                        zip_file.writestr("Temario.txt", texto_descarga)

                    # Guardar todo en la memoria de la sesión
                    st.session_state.datos_temario = datos
                    st.session_state.idioma_real = idioma_real
                    st.session_state.zip_buffer = zip_buffer.getvalue()
                    
                    # Inicializar el chat con la IA
                    instrucciones_chat = f"Eres un local muy amable de {region_final}, {pais_final}. Hablas {idioma_real} y español. Ayudas al usuario a practicar el idioma, respondes a sus saludos, corriges su pronunciación figurada si te lo pide, y mantienes conversaciones sencillas."
                    st.session_state.chat_ia = client.chats.create(
                        model="gemini-2.5-flash",
                        config=types.GenerateContentConfig(system_instruction=instrucciones_chat)
                    )
                    st.session_state.mensajes = []

                except Exception as e:
                    st.error(f"Error técnico de conexión: {e}")

    # Si hay un temario guardado en la memoria, lo mostramos
    if st.session_state.datos_temario:
        st.success(f"¡Listo! Vamos a aprender **{st.session_state.idioma_real.upper()}**")
        
        # Botón de Descarga Global (ZIP con texto y audios)
        st.download_button(
            label="📦 Descargar Temario y Audios (Modo Offline)",
            data=st.session_state.zip_buffer,
            file_name=f"Temario_{st.session_state.idioma_real}.zip",
            mime="application/zip"
        )
        st.divider()

        # Mostrar Tabla Visual
        lang_code = 'en'
        if 'suajili' in st.session_state.idioma_real.lower() or 'swahili' in st.session_state.idioma_real.lower(): lang_code = 'sw'
        
        for dia in st.session_state.datos_temario["dias"]:
            st.subheader(dia["titulo"])
            
            # Cabecera de la tabla
            cols_header = st.columns([2, 2, 2, 1])
            cols_header[0].markdown("**Español**")
            cols_header[1].markdown(f"**{st.session_state.idioma_real}**")
            cols_header[2].markdown("**Se lee**")
            cols_header[3].markdown("**Audio**")
            st.markdown("---")
            
            # Filas de la tabla
            for pal in dia["vocabulario"]:
                cols_row = st.columns([2, 2, 2, 1])
                cols_row[0].write(pal['espanol'])
                cols_row[1].write(pal['palabra_local'])
                cols_row[2].write(f"`{pal['pronunciacion_figurada']}`")
                
                with cols_row[3]:
                    try:
                        tts = gTTS(text=pal['palabra_local'], lang=lang_code)
                        fp = io.BytesIO()
                        tts.write_to_fp(fp)
                        st.audio(fp, format='audio/mp3')
                    except:
                        st.caption("No audio")
            st.write("") 

        st.divider()

        # --- SECCIÓN NUEVA: PRÁCTICA CON IA ---
        st.header("🤖 Practica con un Local (Simulador)")
        st.write(f"Escribe un saludo o una frase en {st.session_state.idioma_real} (o en español) y la IA te responderá y ayudará a mejorar.")

        # Mostrar historial del chat
        for msg in st.session_state.mensajes:
            with st.chat_message(msg["rol"]):
                st.write(msg["contenido"])

        # Input de chat
        if prompt_chat := st.chat_input("Escribe aquí para practicar..."):
            # Mostrar lo que escribe el usuario
            st.session_state.mensajes.append({"rol": "user", "contenido": prompt_chat})
            with st.chat_message("user"):
                st.write(prompt_chat)

            # Respuesta de la IA
            with st.chat_message("assistant"):
                with st.spinner("Escribiendo..."):
                    respuesta = st.session_state.chat_ia.send_message(prompt_chat)
                    st.write(respuesta.text)
                    st.session_state.mensajes.append({"rol": "assistant", "contenido": respuesta.text})


# --- PESTAÑAS RESTANTES ---
with tab_comunidad:
    st.header("Foro de Voluntarios")
    st.info("Próximamente")

with tab_viaje:
    st.header("Preparativos del Viaje")
    st.info("Próximamente")
