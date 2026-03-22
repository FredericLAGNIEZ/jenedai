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
    project_name = os.getenv("ProjectName", "N/A")
    environment = os.getenv("Environment", "N/A")
    services_names_str = os.getenv("ServicesNames", "")
    github_url = os.getenv("GitHubURL", "")
    supabase_url = os.getenv("SupabaseURL", "")
    prefect_url = os.getenv("PrefectURL", "")
    neon_url = os.getenv("NeonURL", "")

    # Parser les ServicesNames (format CSV) et conserver uniquement les services renseignés
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
                "Airflow": "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/apacheairflow/apacheairflow-original.svg",
                "MLflow": "https://cdn.simpleicons.org/mlflow",
                "JupyterLab": "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/jupyter/jupyter-original.svg",
                "Streamlit": "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/streamlit/streamlit-original.svg",
                "n8n": "https://cdn.simpleicons.org/n8n",
                "Gradio": "https://cdn.simpleicons.org/gradio",
                "EvidentlyAI": "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/icons/bar-chart-fill.svg",
                "ClickHouse": "https://cdn.simpleicons.org/clickhouse",
                "Node-RED": "https://cdn.simpleicons.org/nodered/8F0000"
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
            external_count = sum([bool(x) for x in [github_url, supabase_url, prefect_url]])
            st.metric("Ressources Ext.", external_count)

    # Section Services avec icones officielles
    st.subheader("📦 Services Disponibles")

    if not services_names:
        st.info("ℹ️ Aucun service configuré dans ServicesNames du .env")
    else:
        cols_count = min(8, max(1, len(services_names)))
        cols = st.columns(cols_count)
        for idx, service in enumerate(services_names):
            col = cols[idx % cols_count]
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

    col1, col2, col3, col4 = st.columns(4)

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

    if supabase_url:
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
                <h4 style="margin-top: 0;">🗄️ Supabase</h4>
                <p style="font-size: 12px; word-break: break-all;">{supabase_url}</p>
                <a href="{supabase_url}" target="_blank" style="
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

    if prefect_url:
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
                <h4 style="margin-top: 0;">🪣 Prefect</h4>
                <p style="font-size: 12px; word-break: break-all;">{prefect_url}</p>
                <a href="{prefect_url}" target="_blank" style="
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

    if neon_url := os.getenv("NeonURL"):
        with col4:
            st.markdown(f"""
            <div style="
                padding: 20px;
                border-radius: 12px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            ">
                <h4 style="margin-top: 0;">🗄️ NeonDB</h4>
                <p style="font-size: 12px; word-break: break-all;">{neon_url}</p>
                <a href="{neon_url}" target="_blank" style="
                    display: inline-block;
                    padding: 8px 16px;
                    background-color: white;
                    color: #764ba2;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 12px;
                ">Ouvrir →</a>
            </div>
            """, unsafe_allow_html=True)

    if not any([github_url, supabase_url, prefect_url, neon_url]):
        st.info("❌ Aucune ressource externe configurée (GitHub, S3, PostgreSQL, Prefect, NeonDB)")

    st.markdown("---")