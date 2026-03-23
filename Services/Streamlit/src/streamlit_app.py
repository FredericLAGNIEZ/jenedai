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

    # Parser les ServicesNames (format CSV) et conserver uniquement les services renseignés
    services_names = [s.strip() for s in services_names_str.split(",") if s.strip()]

    # Charger les icones et les config JSON de service/external/api
    @st.cache_data
    def load_json_file(filename, default=None):
        # .config dans le même dossier que streamlit_app.py (Services/Streamlit/src/.config)
        config_path = os.path.join(script_dir, ".config", filename)
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return default if default is not None else {}

    SERVICES_CONFIG = load_json_file("services_config.json", {"services": []})
    EXTERNAL_SERVICES_CONFIG = load_json_file("external_services_config.json", {"external_services": []})
    APIS_CONFIG = load_json_file("apis_config.json", {"apis": []})

    # Charger les APIs depuis la configuration JSON uniquement
    api_items = APIS_CONFIG.get("apis", [])

    # Préparer les ressources externes depuis la configuration JSON
    external_sources = []
    for cfg in EXTERNAL_SERVICES_CONFIG.get("external_services", []):
        env_url = os.getenv(cfg.get("env_key", ""), "")
        url = env_url or cfg.get("url", "")
        if url:
            external_sources.append({
                "name": cfg.get("name", ""),
                "url": url,
                "icon": cfg.get("icon", "https://cdn.simpleicons.org/link"),
                "description": cfg.get("description", "")
            })

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
            external_count = len(external_sources)
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
            icon_url = service_cfg.get("icon", "")
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

    if not external_sources:
        st.info("❌ Aucune ressource externe configurée dans .env ou external_services_config.json")
    else:
        cols = st.columns(min(4, len(external_sources)))
        for idx, service in enumerate(external_sources):
            col = cols[idx % len(cols)]
            with col:
                st.markdown(f"""
                <div style="
                    padding: 14px;
                    border-radius: 10px;
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    color: white;
                    text-align: center;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                ">
                    <img src="{service['icon']}" alt="Icône {service['name']}" style="width: 24px; height: 24px; margin-bottom: 6px;" />
                    <h5 style="margin: 6px 0 4px; font-size: 14px;">{service['name']}</h5>
                    <p style="font-size: 11px; word-break: break-all; margin-bottom: 8px;">{service['description']}</p>
                    <a href="{service['url']}" target="_blank" role="button" aria-label="Ouvrir {service['name']}" style="
                        display: inline-flex;
                        align-items: center;
                        justify-content: center;
                        padding: 6px 12px;
                        background-color: white;
                        color: #f5576c;
                        text-decoration: none;
                        border-radius: 6px;
                        font-weight: 700;
                        font-size: 11px;
                    ">Ouvrir ↗</a>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    # Section APIs (fichier de config apis_config.json)
    st.subheader("🧩 APIs disponibles")

    if not api_items:
        st.info("ℹ️ Aucune API configurée dans apis_config.json")
    else:
        for api in api_items:
            icon = api.get('icon', 'https://cdn.simpleicons.org/api')
            name = api.get('name', '')
            url = api.get('url', '')
            desc = api.get('description', '')
            st.markdown(f"""
            <div style="
                display: flex;
                flex-direction: column;
                gap: 10px;
                padding: 14px;
                border-radius: 12px;
                background: linear-gradient(135deg, #43c6ac 0%, #191654 100%);
                color: white;
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                margin-bottom: 10px;
                transition: transform 0.2s;
            " onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1)'">
                <div style="display: flex; align-items: center; gap: 10px; min-width: 0;">
                    <img src="{icon}" alt="Icône de {name}" aria-hidden="false" style="width: 24px; height: 24px;" />
                    <div style="min-width: 0;">
                        <div style="font-size: 14px; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{name}</div>
                        <div style="font-size: 12px; opacity: 0.95; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{desc}</div>
                        <div style="font-size: 10px; opacity: 0.8; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{url}</div>
                    </div>
                </div>
                <a href="{url}" target="_blank" role="button" aria-label="Ouvrir {name}" style="
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    gap: 6px;
                    padding: 8px 14px;
                    background: white;
                    color: #191654;
                    text-decoration: none;
                    border-radius: 8px;
                    font-size: 12px;
                    font-weight: 700;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
                    width: fit-content;
                ">Ouvrir ↗</a>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")