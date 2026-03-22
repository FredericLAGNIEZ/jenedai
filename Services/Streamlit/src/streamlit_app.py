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

    # Charger les icones et les config JSON de service/external/api
    @st.cache_data
    def load_json_file(filename, default=None):
        # .config dans Services/Streamlit
        config_dir = os.path.join(parent_dir, ".config")
        path = os.path.join(config_dir, filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Ancien comportement : recherche à la racine du projet pour rétrocompatibilité
            root_path = os.path.join(os.path.dirname(parent_dir), ".config", filename)
            try:
                with open(root_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except FileNotFoundError:
                return default if default is not None else {}

    SERVICE_ICONS = load_json_file("icons.json", {
        "Airflow": "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/apacheairflow/apacheairflow-original.svg",
        "MLflow": "https://cdn.simpleicons.org/mlflow",
        "JupyterLab": "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/jupyter/jupyter-original.svg",
        "Streamlit": "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/streamlit/streamlit-original.svg",
        "n8n": "https://cdn.simpleicons.org/n8n",
        "Gradio": "https://cdn.simpleicons.org/gradio",
        "EvidentlyAI": "https://cdn.simpleicons.org/evidentlyai",
        "ClickHouse": "https://cdn.simpleicons.org/clickhouse",
        "Node-RED": "https://cdn.simpleicons.org/nodered"
    })

    SERVICES_CONFIG = load_json_file("services_config.json", {"services": []})
    EXTERNAL_SERVICES_CONFIG = load_json_file("external_services_config.json", {"external_services": []})
    APIS_CONFIG = load_json_file("apis_config.json", {"apis": []})

    def load_apis_from_env(env_file_path):
        if not os.path.exists(env_file_path):
            return []

        apis = []
        icon_default = "https://cdn.simpleicons.org/api"
        presets = {
            "Enedis": "https://cdn.simpleicons.org/graphqL",  # icone générique
            "Vacances scolaires": "https://cdn.simpleicons.org/book",
            "Météo": "https://cdn.simpleicons.org/weather",
            "Localisation": "https://cdn.simpleicons.org/map"
        }

        with open(env_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        in_apis = False
        for line in lines:
            raw = line.strip()
            if not raw:
                continue
            if raw.startswith("#APIs"):
                in_apis = True
                continue
            if in_apis and raw.startswith("#"):
                # fin de section APIs s'il y a une autre section
                break
            if in_apis and "=" in raw:
                name, url = raw.split("=", 1)
                name = name.strip()
                url = url.strip()
                if name and url:
                    apis.append({
                        "name": name,
                        "url": url,
                        "icon": presets.get(name, icon_default),
                        "description": "API depuis .env"
                    })

        return apis

    ENV_APIS = load_apis_from_env(env_path)


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
            service_cfg = next((s for s in SERVICES_CONFIG.get("services", []) if s.get("name") == service), {})
            display_name = service_cfg.get("display_name", service)
            icon_url = service_cfg.get("icon", SERVICE_ICONS.get(service, ""))
            hf_url = service_cfg.get("repo_path_template", "https://huggingface.co/spaces/{project}/{service}/tree/main").format(project=project_name, service=service)
            hf_space_url = service_cfg.get("space_url_template", "https://{project}-{service}.hf.space/").format(project=project_name, service=service)

            col = cols[idx % cols_count]
            with col:
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
                    <h4 style="margin: 10px 0; font-size: 16px;">{display_name}</h4>
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

    external_sources = []
    for cfg in EXTERNAL_SERVICES_CONFIG.get("external_services", []):
        url = os.getenv(cfg.get("env_key", ""), "")
        if url:
            external_sources.append({
                "name": cfg.get("name", ""),
                "url": url,
                "icon": cfg.get("icon", ""),
                "description": cfg.get("description", "")
            })

    if not external_sources:
        st.info("❌ Aucune ressource externe configurée dans .env ou external_services_config.json")
    else:
        cols = st.columns(min(4, len(external_sources)))
        for idx, service in enumerate(external_sources):
            col = cols[idx % len(cols)]
            with col:
                st.markdown(f"""
                <div style="
                    padding: 20px;
                    border-radius: 12px;
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    color: white;
                    text-align: center;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                ">
                    <img src="{service['icon']}" alt="{service['name']}" style="width: 30px; height: 30px; margin-bottom: 8px;" />
                    <h4 style="margin-top: 0;">{service['name']}</h4>
                    <p style="font-size: 12px; word-break: break-all;">{service['url']}</p>
                    <a href="{service['url']}" target="_blank" style="
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

    st.markdown("---")

    # Section APIs (fichier de config apis_config.json)
    st.subheader("🧩 APIs disponibles")
    api_items = ENV_APIS if ENV_APIS else []
    if not api_items:
        for api in APIS_CONFIG.get("apis", []):
            env_key = api.get("env_key")
            api_url = os.getenv(env_key, "") if env_key else ""
            if not api_url:
                api_url = api.get("base_url", "")
            if api_url:
                api_items.append({
                    "name": api.get("name", ""),
                    "url": api_url,
                    "icon": api.get("icon", ""),
                    "description": api.get("description", "")
                })

    if not api_items:
        st.info("ℹ️ Aucune API configurée via .env ou apis_config.json")
    else:
        for api in api_items:
            st.markdown(f"""
            <div style="
                padding: 15px;
                border-radius: 12px;
                background: #f0f2f6;
                margin-bottom: 10px;
            ">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <img src="{api.get('icon', '')}" alt="{api.get('name', '')}" style="width: 24px; height: 24px;" />
                    <strong>{api.get('name', '')}</strong>
                </div>
                <div style="font-size: 12px; margin-top: 8px;">{api.get('description', '')}</div>
                <div style="font-size: 11px; color: #333; margin-top: 4px;">{api.get('url', '')}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")