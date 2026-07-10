import os
import json
import streamlit as st
from dotenv import load_dotenv

# Configuration de la page
st.set_page_config(page_title="Infrastructure Dashboard", layout="wide")

# Charger le fichier .env avec chemin absolu
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
env_path = os.path.join(parent_dir, ".env")

# En développement local, fallback vers la racine du projet
if not os.path.exists(env_path):
    # Cherche 3 niveaux au-dessus (Services/Streamlit/src -> Services/Streamlit -> Services -> MLOps)
    root_env = os.path.join(os.path.dirname(parent_dir), "..", ".env")
    root_env = os.path.abspath(root_env)
    if os.path.exists(root_env):
        env_path = root_env

# Vérifie finalement si le .env existe avant de le charger
if not os.path.exists(env_path):
    st.error(f"❌ .env non trouvé")
    st.divider()
else:

    # Récupérer les variables d'environnement depuis le .env
    load_dotenv(env_path, override=True)
    project_name = os.getenv("ProjectName")
    environment = os.getenv("Environment")
    services_names_str = os.getenv("ServicesNames")
    github_url = os.getenv("GitHubURL")
    s3_urls = os.getenv("S3URLs")
    database_urls = os.getenv("DatabaseURLs")

    # Parser les ServicesNames (format CSV)
    services_names = [s.strip() for s in services_names_str.split(",") if s.strip()]

    # Charger les icones depuis icons.json
    @st.cache_data
    def load_service_icons():
        """Charger les icones depuis le fichier icons.json"""
        icons_path = os.path.join(os.path.dirname(parent_dir), "icons.json")
        try:
            with open(icons_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Fallback si icons.json n'existe pas
            return {
                "Airflow": "https://airflow.apache.org/images/feature-image.png",
                "MLflow": "https://mlflow.org/docs/latest/_static/MLflow-logo.png",
                "JupyterLab": "https://jupyter.org/assets/logos/rectanglelogo-greytext-orangedot-invertnull.svg",
                "Streamlit": "https://streamlit.io/images/brand/streamlit-logo-secondary-coloredDark.png",
                "n8n": "https://n8n.io/favicon.ico",
                "Gradio": "https://huggingface.co/front/assets/gradio-logo.svg",
                "EvidentlyAI": "https://raw.githubusercontent.com/evidentlyai/evidently/master/docs/assets/logo.svg",
                "ClickHouse": "https://clickhouse.com/images/logo.svg"
            }

    SERVICE_ICONS = load_service_icons()

    # En-tête
    st.title("🚀 Infrastructure Dashboard")
    st.markdown(f"**Project:** {project_name} | **Environment:** {environment}")
    st.markdown("---")

    # Section Configuration
    with st.expander("⚙️ Configuration Générale", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Project", project_name)
        with col2:
            st.metric("Environment", environment)
        with col3:
            st.metric("Services", len(services_names))
        with col4:
            external_count = sum([bool(x) for x in [github_url, s3_urls, database_urls]])
            st.metric("Ressources Ext.", external_count)

    # Section Services avec icones officielles
    st.subheader("📦 Services Disponibles")

    if services_names:
        cols = st.columns(4)
        for idx, service in enumerate(services_names):
            col = cols[idx % 4]
            with col:
                hf_url = f"https://huggingface.co/spaces/{project_name}/{service}/tree/main"
                hf_space_url = f"https://{project_name}-{service}.hf.space/"
                icon_url = SERVICE_ICONS.get(service, "")
                
                # Bouton avec icone officielle
                st.markdown(f"""
                <div style="
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    padding: 20px;
                    border-radius: 12px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-align: center;
                    margin-bottom: 15px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    transition: transform 0.2s;
                " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                    <div style="width: 60px; height: 60px; margin-bottom: 10px; display: flex; align-items: center; justify-content: center;">
                        <img src="{icon_url}" style="max-width: 100%; max-height: 100%; object-fit: contain; filter: brightness(0) invert(1);">
                    </div>
                    <h4 style="margin: 10px 0; font-size: 16px;">{service}</h4>
                    <p style="margin: 5px 0; font-size: 12px; opacity: 0.9;"><a href="{hf_url}" target="_blank" style="color: white; text-decoration: underline;">HuggingFace Space</a></p>
                    <a href="{hf_space_url}" target="_blank" style="
                        display: inline-block;
                        padding: 8px 16px;
                        background-color: white;
                        color: #667eea;
                        text-decoration: none;
                        border-radius: 6px;
                        font-weight: bold;
                        font-size: 12px;
                        margin-top: 10px;
                    ">Accéder →</a>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    # Section Ressources Externes
    st.subheader("🔐 Ressources Externes")

    col1, col2, col3 = st.columns(3)

    if github_url:
        with col1:
            st.markdown(f"""
            <div style="
                padding: 20px;
                border-radius: 12px;
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                color: white;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            ">
                <h4 style="margin-top: 0;">🐙 GitHub</h4>
                <p style="font-size: 12px; word-break: break-all;">{github_url}</p>
                <a href="{github_url}" target="_blank" style="
                    display: inline-block;
                    padding: 8px 16px;
                    background-color: white;
                    color: #f5576c;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 12px;
                ">Ouvrir →</a>
            </div>
            """, unsafe_allow_html=True)

    if s3_urls:
        with col2:
            st.markdown(f"""
            <div style="
                padding: 20px;
                border-radius: 12px;
                background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                color: white;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            ">
                <h4 style="margin-top: 0;">🪣 S3/MinIO</h4>
                <p style="font-size: 12px; word-break: break-all;">{s3_urls}</p>
                <a href="{s3_urls}" target="_blank" style="
                    display: inline-block;
                    padding: 8px 16px;
                    background-color: white;
                    color: #00f2fe;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 12px;
                ">Ouvrir →</a>
            </div>
            """, unsafe_allow_html=True)

    if database_urls:
        with col3:
            st.markdown(f"""
            <div style="
                padding: 20px;
                border-radius: 12px;
                background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
                color: white;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            ">
                <h4 style="margin-top: 0;">🗄️ PostgreSQL</h4>
                <p style="font-size: 12px; word-break: break-all;">{database_urls}</p>
                <a href="{database_urls}" target="_blank" style="
                    display: inline-block;
                    padding: 8px 16px;
                    background-color: white;
                    color: #38f9d7;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 12px;
                ">Ouvrir →</a>
            </div>
            """, unsafe_allow_html=True)

    if not any([github_url, s3_urls, database_urls]):
        st.info("❌ Aucune ressource externe configurée (GitHub, S3, PostgreSQL)")

    st.markdown("---")