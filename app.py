import streamlit as st
import warnings
import json
from google import genai
from google.genai import types
from pydantic import BaseModel
from gtts import gTTS
import io

warnings.filterwarnings('ignore')

# 1. Configuración de la IA
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# 2. Estructura de datos GLOBAL (Actualizada a Respuesta Esperada e Idioma Principal)
class Palabra(BaseModel):
    palabra_local: str
    pronunciacion_figurada: str
    espanol: str
    respuesta_esperada: str

class Dia(BaseModel):
    titulo: str
    descripcion: str
    vocabulario: list[Palabra]

class Temario(BaseModel):
    idioma_principal: str 
    dias: list[Dia]

# 3. Configuración visual de la web
st.set_page_config(page_title="Vocabulario de Misión", page_icon="🌍", layout="centered")

st.title("✝️ En misión con Cristo")
st.markdown("*«Tenía entonces toda la tierra una sola lengua y unas mismas palabras.»* — Génesis 11:1")

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.header("🙌 Sobre este proyecto")
    st.write("Esta herramienta ha sido desarrollada con mucho cariño por **Raquel** y un grupo de voluntarios que nos vamos de misión a Kenia este verano.")
    st.write("Si valoras este trabajo y quieres apoyarnos a llevar esperanza (y muchas ganas), ¡toda ayuda suma!")
    
    st.info("¿Nos ayudas con nuestra misión?")
    st.markdown("[👉 **Conoce el proyecto y haz tu donación aquí**](https://misionkenia.lovable.app/#) 💙")
    st.markdown("[📸 **Síguenos en Instagram: @to_kenya_4jesus**](https://www.instagram.com/to_kenya_4jesus)")
    st.divider()
    st.caption("Hecho con ❤️ y de la mano de Dios.")

tab_aprender, tab_comunidad, tab_viaje = st.tabs(["📚 Aprender", "💬 Comunidad", "✈️ Guía de Viaje"])

# --- PESTAÑA 1: APRENDER ---
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
    
    mision = st.multiselect("¿Cuál es el enfoque principal de tu misión?", ["Trabajo Social", "Atención Médica", "Educación con niños", "Construcción", "Evangelización"])
    dias = st.slider("¿De cuántos días es tu plan de estudio?", 1, 30, 14)
    
    if st.button("Generar Temario de Misión"):
        if not mision or not pais_final or not region_final:
            st.warning("Por favor, rellena todos los campos (País, Región y Enfoque).")
        else:
            with st.spinner(f"Contactando con comunidades en {region_final} ({pais_final})..."):
                
                prompt = f"""
                Actúa como un lingüista y cooperante experto internacional. 
                Genera un temario de supervivencia lingüística para voluntarios hispanohablantes.
                Destino: {region_final}, {pais_final}.
                Enfoque: {', '.join(mision)}.
                Duración de estudio: {dias} días.

                Instrucciones de formato y contenido:
                1. 'idioma_principal': Identifica la macrolengua o idioma principal (ej. Suajili, Inglés, Español). Ignora dialectos minoritarios para facilitar el aprendizaje.
                2. Estructura el temario usando la nomenclatura 'Día 1', 'Día 2', etc. (Nunca uses la palabra Módulo).
                3. 'pronunciacion_figurada': Fonética exacta para hispanohablantes.
                4. 'respuesta_esperada': Proporciona ÚNICAMENTE la respuesta directa que el voluntario debe esperar recibir o la que debe contestar. Sé conciso y directo.
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
                    
                    st.success(f"Temario generado con éxito. Idioma principal de la región: {idioma_real.upper()}")
                    
                    for dia in datos["dias"]:
                        st.subheader(dia["titulo"])
                        st.write(dia["descripcion"])
                        
                        # Diseño de Tabla Limpia usando Columnas (Permite Audio)
                        st.markdown("---")
                        cols_header = st.columns([2, 2, 2, 3, 1])
                        cols_header[0].markdown("**Idioma Local**")
                        cols_header[1].markdown("**Pronunciación**")
                        cols_header[2].markdown("**Español**")
                        cols_header[3].markdown("**Respuesta Esperada**")
                        cols_header[4].markdown("**Audio**")
                        st.markdown("---")
                        
                        for pal in dia["vocabulario"]:
                            cols_row = st.columns([2, 2, 2, 3, 1])
                            cols_row[0].write(pal['palabra_local'])
                            cols_row[1].write(pal['pronunciacion_figurada'])
                            cols_row[2].write(pal['espanol'])
                            cols_row[3].write(pal['respuesta_esperada'])
                            
                            with cols_row[4]:
                                try:
                                    lang_code = 'en'
                                    if 'suajili' in idioma_real.lower() or 'swahili' in idioma_real.lower(): lang_code = 'sw'
                                    elif 'filipino' in idioma_real.lower() or 'tagalo' in idioma_real.lower(): lang_code = 'tl'
                                    elif 'hindi' in idioma_real.lower(): lang_code = 'hi'
                                    
                                    tts = gTTS(text=pal['palabra_local'], lang=lang_code)
                                    fp = io.BytesIO()
                                    tts.write_to_fp(fp)
                                    st.audio(fp, format='audio/mp3')
                                except Exception:
                                    st.caption("-")
                                    
                        st.write("") # Espaciado inferior
                        
                    # --- BOTÓN DE DESCARGA OFFLINE ---
                    texto_descarga = f"TEMARIO DE MISIÓN: {region_final}, {pais_final}\n"
                    texto_descarga += f"IDIOMA PRINCIPAL: {idioma_real.upper()}\n"
                    texto_descarga += "="*50 + "\n\n"
                    
                    for dia in datos["dias"]:
                        texto_descarga += f"{dia['titulo'].upper()}\n"
                        texto_descarga += f"{dia['descripcion']}\n\n"
                        for pal in dia["vocabulario"]:
                            texto_descarga += f"• {pal['palabra_local']} ({pal['pronunciacion_figurada']}) -> {pal['espanol']}\n"
                            texto_descarga += f"  Respuesta Esperada: {pal['respuesta_esperada']}\n\n"
                        texto_descarga += "-"*50 + "\n\n"
                    
                    st.download_button(
                        label="Descargar Temario (Modo Offline)",
                        data=texto_descarga,
                        file_name=f"Temario_{idioma_real.replace(' ', '_')}.txt",
                        mime="text/plain"
                    )
                        
                except Exception as e:
                    st.error(f"Error técnico de conexión. Inténtalo de nuevo. Detalles: {e}")

# --- PESTAÑA 2: COMUNIDAD ---
with tab_comunidad:
    st.header("Foro de Voluntarios")
    st.info("Próximamente (Este verano): Un espacio para compartir vivencias, dudas y conectar con otros misioneros.")

# --- PESTAÑA 3: VIAJE ---
with tab_viaje:
    st.header("Preparativos del Viaje")
    st.info("Próximamente (Este verano): Checklist de equipaje, visados y recomendaciones de seguridad.")
