import streamlit as st
import pandas as pd
import requests
import google.generativeai as genai
import json
import re

st.set_page_config(page_title="Radar Jurídico IA", layout="wide")

st.title("⚖️ Radar de Notícias Jurídicas sobre IA")
st.subheader("Powered by Google Gemini + Advoco Brasil")

# 🔑 Carrega chaves dos secrets
NEWS_API_KEY = st.secrets["newsapi_key"]
GEMINI_API_KEY = st.secrets["gemini_key"]

# 🔗 Configura Google Gemini
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
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
Você é um analista jurídico. Classifique e resuma a seguinte notícia do contexto jurídico brasileiro sobre inteligência artificial:

Título: {artigo['title']}
Fonte: {artigo['source']['name']}
Descrição: {artigo.get('description', '')}
Link: {artigo['url']}

Siga estes critérios:
- Categorize a notícia em uma das opções:
  1. Implementação de IA em escritórios de advocacia e tribunais brasileiros
  2. Novas legislações e regulamentações sobre IA no direito brasileiro
  3. Casos de uso bem-sucedidos de IA por advogados no Brasil
  4. Controvérsias ou uso inadequado de IA por profissionais jurídicos brasileiros
  5. Desafios éticos da IA na prática jurídica no contexto do Brasil

Devolva como JSON:
{{
  "data": "{pd.Timestamp(artigo['publishedAt']).strftime('%d/%m/%Y')}",
  "titulo": "{artigo['title']}",
  "fonte": "{artigo['source']['name']}",
  "link": "{artigo['url']}",
  "categoria": "categoria aqui",
  "resumo": "resumo aqui"
}}
"""
    try:
        response = model.generate_content(prompt)
        result = response.text.strip()
        result = re.sub(r"^```json", "", result)
        result = re.sub(r"```$", "", result)
        return json.loads(result)
    except Exception as e:
        st.error(f"❌ Erro no processamento Gemini: {e}")
        return None

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
                df = pd.DataFrame(resultados)
                st.dataframe(df, use_container_width=True)

                st.download_button(
                    label="💾 Baixar CSV",
                    data=df.to_csv(index=False).encode('utf-8'),
                    file_name='noticias_juridicas_ia.csv',
                    mime='text/csv'
                )
            else:
                st.warning("Nenhuma notícia relevante encontrada.")

        except Exception as e:
            st.error(f"❌ Erro: {e}")
