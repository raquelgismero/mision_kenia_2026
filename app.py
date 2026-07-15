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

# 2. Estructura de datos GLOBAL (Mejorada según tus peticiones)
class Palabra(BaseModel):
    palabra_local: str
    pronunciacion_figurada: str
    espanol: str
    ejemplo_uso: str # Cambiado: Antes era contexto_cultural

class Dia(BaseModel): # Cambiado: Antes era Modulo
    titulo: str
    descripcion: str
    vocabulario: list[Palabra]

class Temario(BaseModel):
    idioma_detectado: str # Añadido: Para que la IA nos diga exactamente qué idioma es
    dias: list[Dia] # Cambiado: Lista de días en vez de módulos

# 3. Configuración visual de la web
st.set_page_config(page_title="Vocabulario de Misión", page_icon="🌍", layout="centered")

# Título y frase bíblica
st.title("✝️ En misión con Cristo")
st.markdown("*«Tenía entonces toda la tierra una sola lengua y unas mismas palabras.»* — Génesis 11:1")

# --- BARRA LATERAL (SIDEBAR): AUTORÍA Y DONACIONES ---
with st.sidebar:
    st.header("🙌 Sobre este proyecto")
    st.write("Esta herramienta ha sido desarrollada con mucho cariño por **Raquel** y un grupo de voluntarios que nos vamos de misión a Kenia este verano.")
    
    st.write("Si valoras este trabajo y quieres apoyarnos a llevar esperanza (y muchas ganas), ¡toda ayuda suma!")
    
    st.info("¿Nos ayudas con nuestra misión?")
    st.markdown("[👉 **Conoce el proyecto y haz tu donación aquí**](https://misionkenia.lovable.app/#) 💙")
    
    st.markdown("[📸 **Síguenos en Instagram y conócenos mejor: @to_kenya_4jesus**](https://www.instagram.com/to_kenya_4jesus)")
    
    st.divider()
    st.caption("Hecho con ❤️ y de la mano de Dios.")

tab_aprender, tab_comunidad, tab_viaje = st.tabs(["📚 Aprender", "💬 Comunidad", "✈️ Guía de Viaje"])

# --- PESTAÑA 1: APRENDER (Con IA Integrada) ---
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
            st.warning("⚠️ Por favor, rellena todos los campos (País, Región y Enfoque).")
        else:
            with st.spinner(f"Contactando con comunidades en {region_final} ({pais_final})..."):
                
                # Prompt Dinámico GLOBAL actualizado
                prompt = f"""
                Actúa como un lingüista y cooperante experto internacional. 
                Genera un temario de supervivencia del idioma o dialecto local más hablado para voluntarios hispanohablantes.
                Destino: {region_final}, {pais_final}.
                Enfoque: {', '.join(mision)}.
                Duración de estudio: {dias} días.

                Instrucción especial:
                1. Detecta cuál es el idioma principal necesario (ej. Suajili, Tagalo) y devuélvelo en 'idioma_detectado'.
                2. Estructura el temario en {dias} días (usa la palabra 'Día', nunca 'Módulo').
                3. Para 'pronunciacion_figurada', indica cómo debe leerlo un español de forma fonética.
                4. Para 'ejemplo_uso', proporciona una frase de ejemplo o la respuesta esperada en una conversación real.
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
                    idioma_real = datos.get("idioma_detectado", "Idioma Local")
                    
                    st.success(f"¡Temario generado con éxito! 🥳 Vamos a aprender **{idioma_real}**")
                    
                    for dia in datos["dias"]:
                        st.subheader(dia["titulo"])
                        st.write(dia["descripcion"])
                        
                        # --- NUEVO DISEÑO ESTILO DUOLINGO ---
                        for pal in dia["vocabulario"]:
                            with st.container(border=True): # Crea una caja bonita para cada palabra
                                cols = st.columns([3, 1]) # Divide la caja en texto a la izq y audio a la der
                                with cols[0]:
                                    st.markdown(f"### 🌍 **{pal['palabra_local']}**  →  {pal['espanol']}")
                                    st.write(f"🗣️ **Se pronuncia:** `{pal['pronunciacion_figurada']}`")
                                    st.write(f"💡 **Ejemplo / Respuesta:** {pal['ejemplo_uso']}")
                                with cols[1]:
                                    try:
                                        # Lógica sencilla para que el audio suene en el idioma correcto
                                        lang_code = 'en' # Por defecto usa fonética inglesa
                                        if 'suajili' in idioma_real.lower() or 'swahili' in idioma_real.lower(): lang_code = 'sw'
                                        elif 'filipino' in idioma_real.lower() or 'tagalo' in idioma_real.lower(): lang_code = 'tl'
                                        elif 'hindi' in idioma_real.lower(): lang_code = 'hi'
                                        
                                        # Genera el audio
                                        tts = gTTS(text=pal['palabra_local'], lang=lang_code)
                                        fp = io.BytesIO()
                                        tts.write_to_fp(fp)
                                        st.audio(fp, format='audio/mp3')
                                    except Exception:
                                        st.caption("Audio no disponible")
                        
                        st.divider() 

                    # --- BOTÓN DE DESCARGA OFFLINE ACTUALIZADO ---
                    texto_descarga = f"TEMARIO DE MISIÓN: {region_final}, {pais_final}\n"
                    texto_descarga += f"IDIOMA: {idioma_real}\n"
                    texto_descarga += "="*50 + "\n\n"
                    
                    for dia in datos["dias"]:
                        texto_descarga += f"{dia['titulo'].upper()}\n"
                        texto_descarga += f"{dia['descripcion']}\n\n"
                        for pal in dia["vocabulario"]:
                            texto_descarga += f"- {pal['palabra_local']} (Pronunciación: {pal['pronunciacion_figurada']}) -> {pal['espanol']}\n"
                            texto_descarga += f"  Ejemplo: {pal['ejemplo_uso']}\n\n"
                        texto_descarga += "-"*50 + "\n\n"
                    
                    st.download_button(
                        label="⬇️ Descargar Temario (Modo Offline)",
                        data=texto_descarga,
                        file_name=f"Temario_{idioma_real.replace(' ', '_')}_{region_final.replace(' ', '_')}.txt",
                        mime="text/plain"
                    )
                        
                except Exception as e:
                    st.error(f"Hubo un problema de conexión. Inténtalo de nuevo. Error técnico: {e}")

# --- PESTAÑA 2: COMUNIDAD ---
with tab_comunidad:
    st.header("Foro de Voluntarios")
    st.info("Próximamente (Este verano): Un espacio para compartir vivencias, dudas y conectar con otros misioneros.")

# --- PESTAÑA 3: VIAJE ---
with tab_viaje:
    st.header("Preparativos del Viaje")
    st.info("Próximamente (Este verano): Checklist de equipaje, visados y recomendaciones de seguridad.")
