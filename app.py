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

# 1. Configuración de la IA (Mantenemos la conexión abierta)
@st.cache_resource
def iniciar_cliente_ia():
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

client = iniciar_cliente_ia()
# 2. Estructura de datos GLOBAL
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
    st.header("Sobre este proyecto")
    st.write("Esta herramienta ha sido desarrollada con mucho cariño por **Raquel** y un grupo de voluntarios que nos vamos de misión a Kenia este verano.")
    st.write("Si valoras este trabajo y quieres apoyarnos a llevar esperanza (y muchas ganas), ¡toda ayuda suma!")
    
    st.info("¿Nos ayudas con nuestra misión?")
    st.markdown("[👉 **Conoce el proyecto y haz tu donación aquí**](https://misionkenia.lovable.app/#) 💙")
    st.markdown("[📸 **Síguenos en Instagram y conocenos mejor: @to_kenya_4jesus**](https://www.instagram.com/to_kenya_4jesus)")
    st.divider()
    st.caption("Hecho con ❤️ y de la mano de Dios.")

tab_aprender, tab_comunidad, tab_viaje = st.tabs(["📚 Aprender", "💬 Comunidad", "✈️ Guía de Viaje"])

with tab_aprender:
    st.header("Diseña tu temario de Misión")
    
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
    
    mision = st.multiselect("Enfoque de tu misión:", ["Trabajo Social", "Atención Médica", "Educación con niños", "Construcción", "Evangelización", "Otro"])
    
    enfoque_final = mision.copy()
    if "Otro" in mision:
        otro_enfoque = st.text_input("Especifica el otro enfoque:")
        if otro_enfoque:
            enfoque_final.remove("Otro")
            enfoque_final.append(otro_enfoque)

    col1, col2 = st.columns(2)
    with col1:
        dias = st.number_input("¿Durante cuántos días estudiarás?", min_value=1, max_value=60, value=14)
    with col2:
        tiempo_diario = st.selectbox("Tiempo de estudio al día:", ["15 minutos", "30 minutos", "1 hora", "Más de 1 hora"])
    
    # Inicializar memoria de la sesión
    if "datos_temario" not in st.session_state:
        st.session_state.datos_temario = None
        st.session_state.idioma_real = None
        st.session_state.zip_buffer = None
        st.session_state.chat_ia = None
        st.session_state.mensajes = []

    if st.button("Generar temario de misión"):
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
                3. Proporciona: espanol, palabra_local, y pronunciacion_figurada (cómo se lee fonéticamente en español).
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
                    
                    # Identificador de idioma para el Audio
                    lang_code = 'en'
                    if 'suajili' in idioma_real.lower() or 'swahili' in idioma_real.lower(): lang_code = 'sw'
                    elif 'filipino' in idioma_real.lower() or 'tagalo' in idioma_real.lower(): lang_code = 'tl'
                    elif 'hindi' in idioma_real.lower(): lang_code = 'hi'
                    elif 'español' in idioma_real.lower(): lang_code = 'es'

                    # Generar audios y archivo ZIP
                    zip_buffer = io.BytesIO()
                    texto_descarga = f"TEMARIO DE MISIÓN: {region_final}, {pais_final}\nIDIOMA: {idioma_real.upper()}\n\n"
                    
                    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                        for dia in datos["dias"]:
                            texto_descarga += f"--- {dia['titulo'].upper()} ---\n{dia['descripcion']}\n"
                            for pal in dia["vocabulario"]:
                                texto_descarga += f"{pal['espanol']} | {pal['palabra_local']} | Se lee: {pal['pronunciacion_figurada']}\n"
                                try:
                                    tts = gTTS(text=pal['palabra_local'], lang=lang_code)
                                    audio_fp = io.BytesIO()
                                    tts.write_to_fp(audio_fp)
                                    zip_file.writestr(f"audios/{pal['espanol'].replace(' ', '_')}.mp3", audio_fp.getvalue())
                                except:
                                    pass
                            texto_descarga += "\n"
                        zip_file.writestr("Temario.txt", texto_descarga)

                    # Guardar en la memoria de la sesión
                    st.session_state.datos_temario = datos
                    st.session_state.idioma_real = idioma_real
                    st.session_state.zip_buffer = zip_buffer.getvalue()
                    
                    # Inicializar el chat de la IA
                    # Inicializar el chat de la IA con un perfil estrictamente académico y formal
                    instrucciones_chat = (
                        f"Actúa única y exclusivamente como un profesor de lingüística y tutor académico formal experto en el entorno de {region_final}, {pais_final}. "
                        f"Tu única función es enseñar el idioma {idioma_real} y resolver dudas lingüísticas de forma directa, seria y rigurosa. "
                        f"REGLAS CRÍTICAS DE COMPORTAMIENTO:\n"
                        f"1. Tono: Exclusivamente formal, neutro y académico. Sé directo y ve al grano.\n"
                        f"2. Prohibición de comentarios informales: Está estrictamente prohibido hacer chistes, bromas, comentarios subjetivos o usar lenguaje coloquial.\n"
                        f"3. Prohibición de refuerzo emocional: No incluyas bajo ningún concepto comentarios de ánimo, elogios, felicitaciones ni menciones al esfuerzo (ej. PROHIBIDO decir '¡Buen trabajo!', 'Congratulations', 'Vas por buen camino', 'Excelente esfuerzo').\n"
                        f"4. Formato de respuesta: Responde única y estrictamente a lo que se te ha preguntado, sin introducciones ni despedidas innecesarias.\n"
                        f"5. Brevedad: Dado que tu respuesta se transformará en audio, sé lo más conciso y claro posible en tus explicaciones técnicas y habla en x1.5"
                    )
                    st.session_state.chat_ia = client.chats.create(
                        model="gemini-2.5-flash",
                        config=types.GenerateContentConfig(system_instruction=instrucciones_chat)
                    )
                    st.session_state.mensajes = []

                except Exception as e:
                    st.error(f"Error técnico de conexión: {e}")

    # Si hay un temario generado, mostramos el contenido
    if st.session_state.datos_temario:
        st.success(f"¡Listo! Vamos a aprender **{st.session_state.idioma_real.upper()}**")
        
        st.download_button(
            label="Descargar temario y audios (offline)",
            data=st.session_state.zip_buffer,
            file_name=f"Temario_{st.session_state.idioma_real}.zip",
            mime="application/zip"
        )
        st.divider()

        # Mostrar Tabla de Vocabulario
        lang_code = 'en'
        if 'suajili' in st.session_state.idioma_real.lower() or 'swahili' in st.session_state.idioma_real.lower(): lang_code = 'sw'
        
        for dia in st.session_state.datos_temario["dias"]:
            st.subheader(dia["titulo"])
            cols_header = st.columns([2, 2, 2, 1])
            cols_header[0].markdown("**Español**")
            cols_header[1].markdown(f"**{st.session_state.idioma_real}**")
            cols_header[2].markdown("**Se lee**")
            cols_header[3].markdown("**Audio**")
            st.markdown("---")
            
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
                        st.caption("Error")
            st.write("") 

        st.divider()

       # --- SECCIÓN DE TUTOR DE VOZ (CHAT) ---
        st.header("Tutor de Voz: Practica con un local")
        st.write("Mantén una conversación fluida o pregunta dudas. Puedes usar el teclado o el micrófono.")
        
        modo_chat = st.radio(
            "Elige cómo quieres que te responda la IA:", 
            ["Solo Audio (Recomendado)", "Audio y Texto", "Solo Texto"], 
            horizontal=True
        )

        # 1. Contenedor para el historial (Mantiene todo en orden)
        contenedor_chat = st.container()
        
        # Mostrar historial dentro del contenedor
        with contenedor_chat:
            for msg in st.session_state.mensajes:
                with st.chat_message(msg["rol"]):
                    if msg["rol"] == "user":
                        if msg.get("tipo") == "audio":
                            st.audio(msg["contenido"], format="audio/wav")
                        else:
                            st.write(msg["contenido"])
                    else:
                        if msg.get("audio") and ("Audio" in modo_chat):
                            st.audio(msg["audio"], format="audio/mp3")
                        if "Texto" in modo_chat or not msg.get("audio"):
                            st.write(msg["contenido"])

        # 2. Contenedor para los inputs (Para que estén fijos abajo)
        if "ultimo_audio" not in st.session_state:
            st.session_state.ultimo_audio = None

        prompt_audio = st.audio_input("Envía un mensaje de voz:")
        prompt_texto = st.chat_input("Escribe tu saludo o pregunta aquí...")

        # Verificar si hay un audio NUEVO
        nuevo_audio = None
        if prompt_audio:
            if prompt_audio.getvalue() != st.session_state.ultimo_audio:
                nuevo_audio = prompt_audio.getvalue()
                st.session_state.ultimo_audio = nuevo_audio

        # 3. Procesar nuevos mensajes
        if prompt_texto or nuevo_audio:
            
            # ¡CLAVE! Mostramos los mensajes nuevos DENTRO del contenedor del chat
            with contenedor_chat: 
                # Mostrar mensaje del usuario
                if prompt_texto:
                    st.session_state.mensajes.append({"rol": "user", "tipo": "texto", "contenido": prompt_texto})
                    with st.chat_message("user"):
                        st.write(prompt_texto)
                    mensaje_para_ia = prompt_texto
                    
                elif nuevo_audio:
                    st.session_state.mensajes.append({"rol": "user", "tipo": "audio", "contenido": nuevo_audio})
                    with st.chat_message("user"):
                        st.audio(nuevo_audio, format="audio/wav")
                    mensaje_para_ia = [
                        types.Part.from_bytes(data=nuevo_audio, mime_type="audio/wav"), 
                        "Por favor, escucha este audio y respóndeme."
                    ]

                # Mostrar respuesta de la IA
                with st.chat_message("assistant"):
                    with st.spinner("Pensando y procesando..."):
                        try:
                            respuesta = st.session_state.chat_ia.send_message(mensaje_para_ia)
                            texto_ia = respuesta.text
                            
                            # Limpiar asteriscos y guiones bajos para que el audio suene natural
                            texto_limpio_para_audio = texto_ia.replace("*", "").replace("_", "").replace("#", "")
                            
                            audio_bytes_ia = None
                            if "Audio" in modo_chat:
                                try:
                                    tts_chat = gTTS(text=texto_limpio_para_audio, lang='es') 
                                    fp_chat = io.BytesIO()
                                    tts_chat.write_to_fp(fp_chat)
                                    audio_bytes_ia = fp_chat.getvalue()
                                    st.audio(audio_bytes_ia, format="audio/mp3")
                                except Exception:
                                    st.caption("Error generando el audio de respuesta.")
                            
                            if "Texto" in modo_chat:
                                st.write(texto_ia)
                            
                            st.session_state.mensajes.append({
                                "rol": "assistant", 
                                "tipo": "texto",
                                "contenido": texto_ia, 
                                "audio": audio_bytes_ia
                            })
                        except Exception as e:
                            st.error("¡Ups! Los servidores no han podido procesar este mensaje. ¡Prueba de nuevo!")
# --- PESTAÑAS RESTANTES ---
with tab_comunidad:
    st.header("Foro de Voluntarios")
    st.info("Próximamente")

with tab_viaje:
    st.header("Preparativos del Viaje")
    st.info("Próximamente")
