FROM nodered/node-red:latest

ARG NODE_RED_CREDENTIAL_SECRET

# Installer dépendances utiles
#RUN npm install \
#    axios \
#    node-red-dashboard

# (Optionnel) Installer nodes spécifiques
#RUN npm install \
#    node-red-contrib-browser-utils

COPY data/ .

# Exposer port
ENV PORT=7860
EXPOSE 7860