from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import requests
import google.generativeai as genai
import json
import re
import os

app = FastAPI()

# 🚀 Permitir acesso de qualquer site (WordPress, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔑 Carregar API Keys
NEWS_API_KEY = os.getenv("newsapi_key")
GEMINI_API_KEY = os.getenv("gemini_key")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# 🔍 Buscar na NewsAPI
def buscar_noticias_newsapi():
    url = "https://newsapi.org/v2/everything"
    params = {
        'q': 'inteligência artificial AND (advocacia OR direito OR tribunais OR CNJ OR OAB)',
        'from': pd.Timestamp.now() - pd.Timedelta(days=10),
        'sortBy': 'relevancy',
        'language': 'pt',
        'pageSize': 10,
        'apiKey': NEWS_API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    if data.get("status") != "ok":
        raise Exception(data.get("message", "Erro na NewsAPI"))
    return data.get("articles", [])

# 🧠 Processar com Gemini
def processar_com_gemini(artigo):
    prompt = f"""
Você é um especialista em direito e tecnologia.

Sua tarefa é classificar, resumir e categorizar a seguinte notícia, avaliando se ela está relacionada diretamente ao uso da Inteligência Artificial no contexto jurídico brasileiro.

Se não for sobre IA no contexto jurídico brasileiro, descarte.

Se for relevante, siga estes critérios:

1. Categoria (UMA):
- Implementação de IA em escritórios ou tribunais brasileiros
- Novas legislações e regulamentações sobre IA no direito brasileiro
- Casos de uso de IA por advogados no Brasil
- Controvérsias ou uso inadequado de IA no meio jurídico brasileiro
- Desafios éticos da IA na prática jurídica no Brasil

2. Crie um resumo de até 2 linhas.

Formato JSON:
{{
  "data": "{pd.Timestamp(artigo['publishedAt']).strftime('%d/%m/%Y')}",
  "titulo": "{artigo['title']}",
  "fonte": "{artigo['source']['name']}",
  "link": "{artigo['url']}",
  "categoria": "Categoria",
  "resumo": "Resumo objetivo"
}}

Se irrelevante:
{{ "descartar": "Notícia irrelevante" }}
"""
    try:
        response = model.generate_content(prompt)
        result = response.text.strip()
        result = re.sub(r"^```json", "", result)
        result = re.sub(r"```$", "", result)
        data = json.loads(result)
        if "descartar" in data:
            return None
        return data
    except:
        return None

# 🚀 Criar endpoint da API
@app.get("/noticias")
def get_noticias():
    artigos = buscar_noticias_newsapi()
    resultados = []
    for artigo in artigos:
        processado = processar_com_gemini(artigo)
        if processado:
            resultados.append(processado)
    return {"noticias": resultados}
