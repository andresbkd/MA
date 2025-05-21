
import streamlit as st
import google.generativeai as genai
import datetime
import pandas as pd
import json
import re

st.set_page_config(page_title="Processador de Notícias Jurídicas com IA", layout="wide")

st.title("⚖️ Processador de Notícias Jurídicas com IA")
st.subheader("Powered by Google Gemini + Advoco Brasil")

# --- Configuração da API ---
api_key = st.text_input("🔑 Insira sua API Key do Google Gemini:", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        st.success("✅ API configurada com sucesso!")
    except Exception as e:
        st.error(f"❌ Erro ao configurar API: {e}")
        st.stop()
else:
    st.warning("⚠️ Insira sua API Key para continuar.")
    st.stop()

# --- Entrada de Dados ---
st.markdown("### 📰 Simule ou cole suas notícias abaixo:")

with st.expander("🔧 Usar notícias simuladas"):
    if st.button("➡️ Carregar Notícias Simuladas"):
        noticias = [
            {
                "data_publicacao": (datetime.date.today() - datetime.timedelta(days=1)).strftime("%d/%m/%Y"),
                "titulo": "IA Generativa Revoluciona Análise de Contratos em Escritórios Brasileiros",
                "fonte": "Portal Jurídico Tech",
                "link": "https://example.com/noticia1",
                "texto_completo": "Grandes escritórios estão adotando IA Generativa para análise de contratos..."
            },
            {
                "data_publicacao": (datetime.date.today() - datetime.timedelta(days=3)).strftime("%d/%m/%Y"),
                "titulo": "CNJ Discute Nova Resolução sobre IA no Judiciário",
                "fonte": "Notícias do Judiciário",
                "link": "https://example.com/noticia2",
                "texto_completo": "O CNJ debate resolução para IA em apoio a decisões judiciais..."
            }
        ]
    else:
        noticias = []

st.markdown("Ou insira manualmente:")

with st.form(key="formulario"):
    titulo = st.text_input("Título da Notícia")
    fonte = st.text_input("Fonte")
    link = st.text_input("Link")
    texto = st.text_area("Texto Completo")
    data = st.date_input("Data de Publicação", datetime.date.today())

    enviar = st.form_submit_button("Adicionar Notícia")

    if enviar and titulo and texto:
        nova = {
            "data_publicacao": data.strftime("%d/%m/%Y"),
            "titulo": titulo,
            "fonte": fonte,
            "link": link,
            "texto_completo": texto
        }
        noticias.append(nova)

# --- Processamento ---
def processar_noticia(noticia):
    prompt = f"""
    Analise a seguinte notícia do contexto jurídico brasileiro:

    Título: {noticia['titulo']}
    Fonte: {noticia['fonte']}
    Texto Completo: {noticia['texto_completo']}

    Com base nos critérios abaixo, forneça:
    1. Um resumo conciso da notícia em no máximo 2 linhas.
    2. A categoria principal da notícia, escolhendo UMA das seguintes opções:
        - Implementação de IA em escritórios de advocacia e tribunais brasileiros
        - Novas legislações e regulamentações sobre IA no direito brasileiro
        - Casos de uso bem-sucedidos de IA por advogados no Brasil
        - Controvérsias ou uso inadequado de IA por profissionais jurídicos brasileiros
        - Desafios éticos da IA na prática jurídica no contexto do Brasil
        - Tendências emergentes que advogados brasileiros precisam conhecer

    Formato da Resposta (JSON):
    {{
      "resumo": "Seu resumo aqui...",
      "categoria": "Categoria escolhida aqui..."
    }}
    """
    try:
        response = model.generate_content(prompt)
        result = response.text.strip()
        result = re.sub(r"^```json", "", result)
        result = re.sub(r"```$", "", result)
        data = json.loads(result)
        return {
            "Data": noticia['data_publicacao'],
            "Título": noticia['titulo'],
            "Fonte": noticia['fonte'],
            "Link": noticia['link'],
            "Categoria": data.get('categoria', 'Erro'),
            "Resumo": data.get('resumo', 'Erro')
        }
    except:
        return {
            "Data": noticia['data_publicacao'],
            "Título": noticia['titulo'],
            "Fonte": noticia['fonte'],
            "Link": noticia['link'],
            "Categoria": "Erro",
            "Resumo": "Erro ao processar"
        }

# --- Execução ---
if noticias:
    st.info(f"🔍 Processando {len(noticias)} notícias...")

    resultados = []
    for noticia in noticias:
        resultados.append(processar_noticia(noticia))

    df = pd.DataFrame(resultados)
    st.dataframe(df, use_container_width=True)

    st.download_button(
        label="💾 Baixar resultados em CSV",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name='noticias_processadas.csv',
        mime='text/csv'
    )

else:
    st.warning("⚠️ Nenhuma notícia para processar.")
