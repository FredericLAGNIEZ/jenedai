FROM clickhouse/clickhouse-server:latest

# Changer le port HTTP vers 7860
RUN sed -i 's/<http_port>8123<\/http_port>/<http_port>7860<\/http_port>/' /etc/clickhouse-server/config.xml

# Créer dossier pour fichiers utilisateurs
RUN mkdir -p /etc/clickhouse-server/users.d

# Créer fichier XML avec mot de passe sécurisé
# RUN echo '<clickhouse><users><default><password>CHANGE_ME_STRONG_PASSWORD</password><networks><ip>::/0</ip></networks></default></users></clickhouse>' > /etc/clickhouse-server/users.d/security.xml
RUN echo '<clickhouse><users><default><networks><ip>::/0</ip></networks></default></users></clickhouse>' > /etc/clickhouse-server/users.d/security.xml

EXPOSE 7860