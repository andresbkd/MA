
import streamlit as st
import pandas as pd
import requests
import google.generativeai as genai
import json
import re
import streamlit.components.v1 as components

st.set_page_config(page_title="Radar Jurídico IA", layout="wide")

st.title("Radar de Notícias Jurídicas sobre IA")
st.subheader("Powered by Google Gemini + Advoco Brasil")

# 🔑 Carrega chaves dos secrets
NEWS_API_KEY = st.secrets["newsapi_key"]
GEMINI_API_KEY = st.secrets["gemini_key"]

# 🔗 Configura Google Gemini
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
    st.success("✅ API Gemini configurada com sucesso!")
except Exception as e:
    st.error(f"❌ Erro na configuração do Gemini: {e}")
    st.stop()

# 🔍 Função busca na NewsAPI
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

# 🧠 Função processa com Gemini
def processar_com_gemini(artigo):
    prompt = f"""
Você é um especialista em direito e tecnologia.

Sua tarefa é classificar, resumir e categorizar a seguinte notícia, sempre avaliando se ela está relacionada diretamente ao uso da Inteligência Artificial no contexto jurídico brasileiro.

⚠️ Se a notícia NÃO for sobre IA aplicada ao direito, ao judiciário, à advocacia, a tribunais ou à regulamentação no Brasil, descarte.

Se for relevante, siga estes critérios:

1️⃣ Categorize a notícia em UMA das opções:
- Implementação de IA em escritórios de advocacia ou tribunais brasileiros
- Novas legislações e regulamentações sobre IA no direito brasileiro
- Casos de uso bem-sucedidos de IA por advogados no Brasil
- Controvérsias ou uso inadequado de IA no ambiente jurídico brasileiro
- Desafios éticos da IA na prática jurídica no Brasil

2️⃣ Crie um resumo objetivo, de até 2 linhas, claro e informativo.

3️⃣ Entregue o resultado no formato JSON:
{{
  "data": "{pd.Timestamp(artigo['publishedAt']).strftime('%d/%m/%Y')}",
  "titulo": "{artigo['title']}",
  "fonte": "{artigo['source']['name']}",
  "link": "{artigo['url']}",
  "categoria": "Categoria",
  "resumo": "Resumo objetivo"
}}

⚠️ Se a notícia não for sobre IA no contexto jurídico brasileiro, responda apenas:
{{
  "descartar": "Notícia irrelevante para IA no direito"
}}
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
    except Exception as e:
        st.error(f"❌ Erro no processamento Gemini: {e}")
        return None

# 🎨 Função gerar HTML estilizado
def gerar_html_noticias(lista_noticias):
    html = """
    <div style='font-family: Arial, sans-serif; max-width: 1000px; margin: auto;'>
    """
    for noticia in lista_noticias:
        html += f"""
        <div style='border:1px solid #ddd; border-radius:10px; padding:20px; margin-bottom:15px; box-shadow:0 2px 6px rgba(0,0,0,0.1);'>
          <div style='font-size:14px; color:#666;'>🗓️ {noticia['data']} | <strong>{noticia['fonte']}</strong> | <span style='color:#0066cc;'>{noticia['categoria']}</span></div>
          <h3 style='margin-top:5px; margin-bottom:10px;'>
            <a href='{noticia['link']}' target='_blank' style='text-decoration:none; color:#003366;'>
              {noticia['titulo']}
            </a>
          </h3>
          <p style='font-size:15px; color:#333;'>
            {noticia['resumo']}
          </p>
        </div>
        """
    html += "</div>"
    return html

# 🚀 Execução
if st.button("🔎 Buscar Notícias Reais"):
    with st.spinner("Consultando APIs..."):
        try:
            artigos = buscar_noticias_newsapi()
            resultados = []
            for artigo in artigos:
                processado = processar_com_gemini(artigo)
                if processado:
                    resultados.append(processado)

            if resultados:
                html_resultado = gerar_html_noticias(resultados)
                components.html(html_resultado, height=700 + len(resultados) * 150, scrolling=True)
            else:
                st.warning("Nenhuma notícia relevante encontrada.")

        except Exception as e:
            st.error(f"❌ Erro: {e}")
