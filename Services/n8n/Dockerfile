FROM n8nio/n8n:latest

# Hugging Face impose le port 7860
ENV N8N_PORT=7860
ENV N8N_HOST=0.0.0.0
ENV WEBHOOK_URL=https://your-space-name.hf.space/

# IMPORTANT : clé fixe obligatoire
ENV N8N_ENCRYPTION_KEY=your_super_secret_key_here

EXPOSE 7860