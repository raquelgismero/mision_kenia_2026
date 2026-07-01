import streamlit as st
import warnings
import json
from google import genai
from google.genai import types
from pydantic import BaseModel

warnings.filterwarnings('ignore')

# 1. Configuración de la IA
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# 2. Estructura de datos GLOBAL (Cambiamos 'suajili' por 'palabra_local')
class Palabra(BaseModel):
    palabra_local: str
    pronunciacion_figurada: str
    espanol: str
    contexto_cultural: str

class Modulo(BaseModel):
    titulo: str
    descripcion: str
    vocabulario: list[Palabra]

class Temario(BaseModel):
    modulos: list[Modulo]

# 3. Configuración visual de la web
st.set_page_config(page_title="Vocabulario de Misión", page_icon="🌍", layout="centered")

# Título y frase bíblica
st.title("✝️ En misión con Cristo")
st.markdown("*«Tenía entonces toda la tierra una sola lengua y unas mismas palabras.»* — Génesis 11:1")

# --- BARRA LATERAL (SIDEBAR): AUTORÍA Y DONACIONES ---
with st.sidebar:
    st.header("🙌 Sobre este proyecto")
    st.write("Esta herramienta ha sido desarrollada con mucho cariño por **Raquel**  y un grupo de voluntarios que nos vamos de misión a Kenia este verano.")
    
    st.write("Si valoras este trabajo y quieres apoyarnos a llevar esperanza (y muchas ganas), ¡toda ayuda suma!")
    
    # Recuadro destacado para la donación y la web
    st.info("¿Nos ayudas con nuestra misión?")
    st.markdown("[👉 **Conoce el proyecto y haz tu donación aquí**](https://misionkenia.lovable.app/#) 💙")
    
    # Enlace a Instagram
    st.markdown("[📸 **Síguenos en Instagram y conócenos mejor: @to_kenya_4jesus**](https://www.instagram.com/to_kenya_4jesus)")
    
    st.divider()
    st.caption("Hecho con ❤️ y de la mano de Dios.")

tab_aprender, tab_comunidad, tab_viaje = st.tabs(["📚 Aprender", "💬 Comunidad", "✈️ Guía de Viaje"])

# --- PESTAÑA 1: APRENDER (Con IA Integrada) ---
with tab_aprender:
    st.header("Diseña tu temario de Misión")
    
    # Base de datos simulada de países y regiones para el desplegable
    destinos_mundiales = {
        "Kenia": ["Huruma", "Zona Desértica", "Nairobi", "Otra"],
        "Filipinas": ["Manila", "Cebú", "Mindanao", "Otra"],
        "Perú": ["Iquitos (Amazonas)", "Cusco", "Lima", "Otra"],
        "India": ["Calcuta", "Nueva Delhi", "Tamil Nadu", "Otra"],
        "Otro País": ["Especificar ciudad o región..."]
    }
    
    # Lógica condicional: El usuario elige país, y la web adapta el segundo desplegable
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
                
                # Prompt Dinámico GLOBAL
                prompt = f"""
                Actúa como un lingüista y cooperante experto internacional. 
                Genera un temario de supervivencia del idioma o dialecto local más hablado para voluntarios hispanohablantes.
                Destino: {region_final}, {pais_final}.
                Enfoque: {', '.join(mision)}.
                Duración de estudio: {dias} días.

                Instrucción especial:
                Detecta cuál es el idioma principal necesario en esa región específica.
                Para cada palabra en 'palabra_local', incluye una 'pronunciacion_figurada' que indique cómo debe leerlo un español de forma fonética.
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
                    st.success("¡Temario generado con éxito! 🥳")
                    
                    for modulo in datos["modulos"]:
                        st.subheader(modulo["titulo"])
                        st.write(modulo["descripcion"])
                        
                        tabla = []
                        for pal in modulo["vocabulario"]:
                            tabla.append({
                                "Idioma Local": pal["palabra_local"],
                                "Pronunciación": pal["pronunciacion_figurada"],
                                "Español": pal["espanol"],
                                "Contexto": pal["contexto_cultural"]
                            })
                        
                        st.dataframe(tabla, use_container_width=True)
                        st.divider() 
			# --- NUEVO: BOTÓN DE DESCARGA OFFLINE ---
                    # 1. Preparamos el texto a descargar
                    texto_descarga = f"TEMARIO DE MISIÓN: {region_final}, {pais_final}\n"
                    texto_descarga += "="*50 + "\n\n"
                    
                    for modulo in datos["modulos"]:
                        texto_descarga += f"MÓDULO: {modulo['titulo']}\n"
                        texto_descarga += f"{modulo['descripcion']}\n\n"
                        for pal in modulo["vocabulario"]:
                            texto_descarga += f"- {pal['palabra_local']} (Se pronuncia: {pal['pronunciacion_figurada']}) -> {pal['espanol']}\n"
                            texto_descarga += f"  Contexto: {pal['contexto_cultural']}\n\n"
                        texto_descarga += "-"*50 + "\n\n"
                    
                    # 2. Creamos el botón mágico de Streamlit
                    st.download_button(
                        label="⬇️ Descargar Temario (Modo Offline)",
                        data=texto_descarga,
                        file_name=f"Temario_Misiones_{region_final.replace(' ', '_')}.txt",
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
