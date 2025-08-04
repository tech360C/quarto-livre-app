import streamlit as st
import json
import os
from datetime import date

st.set_page_config(page_title="Galeria - Quarto Livre", layout="wide")
st.title("🛏️ Galeria de Quartos - Quarto Livre")

# --- Arquivos necessários ---
HOTEL_FILE = "hoteis.json"
QUARTOS_FILE = "quartos.json"
RESERVAS_FILE = "reservas.json"
UPLOAD_DIR = "uploads"

def carregar_json(caminho):
    if not os.path.exists(caminho):
        return {}
    with open(caminho, "r") as f:
        return json.load(f)

def salvar_json(caminho, dados):
    with open(caminho, "w") as f:
        json.dump(dados, f, indent=4)

# --- Carregar dados ---
hoteis = carregar_json(HOTEL_FILE)
quartos = carregar_json(QUARTOS_FILE)
reservas = carregar_json(RESERVAS_FILE)

# --- Filtrar hotéis aprovados ---
hoteis_aprovados = {k: v for k, v in hoteis.items() if v.get("status") == "aprovado"}

# --- Filtros ---
st.sidebar.header("🔎 Filtros")

todos_nomes = [v["nome"] for v in hoteis_aprovados.values()]
filtro_nome = st.sidebar.selectbox("Nome do Hotel", options=["Todos"] + todos_nomes)

filtro_endereco = st.sidebar.text_input("Cidade ou Endereço contém:")

# --- Aplicar filtros ---
hoteis_filtrados = {}
for hotel_id, dados in hoteis_aprovados.items():
    nome_ok = (filtro_nome == "Todos") or (dados["nome"] == filtro_nome)
    endereco_ok = filtro_endereco.lower() in dados.get("endereco", "").lower()

    if nome_ok and endereco_ok:
        hoteis_filtrados[hotel_id] = dados

# --- Exibir resultados ---
if not hoteis_filtrados:
    st.warning("Nenhum hotel encontrado com os filtros selecionados.")
else:
    for hotel_id, hotel in hoteis_filtrados.items():
        st.markdown(f"### 🏨 {hotel['nome']}")
        st.write(f"📍 {hotel.get('endereco', 'Endereço não informado')}")
        st.write(f"📝 {hotel.get('descricao', 'Sem descrição')}")

        quartos_do_hotel = quartos.get(hotel_id, {})

        if not quartos_do_hotel:
            st.warning("Este hotel ainda não cadastrou quartos.")
        else:
            for q_id, q in quartos_do_hotel.items():
                with st.expander(f"{q['nome']} - R$ {q['preco']:.2f}"):
                    st.write(q["descricao"])
                    for img in q["fotos"]:
                        try:
                            st.image(img, width=300)
                        except:
                            st.warning(f"Erro ao carregar imagem: {img}")

                    with st.form(f"reserva_{hotel_id}_{q_id}"):
                        st.markdown("**📅 Reservar este quarto:**")
                        nome = st.text_input("Seu nome completo")
                        email = st.text_input("Seu e-mail")
                        checkin = st.date_input("Data de entrada", min_value=date.today())
                        checkout = st.date_input("Data de saída", min_value=checkin)

                        reservar = st.form_submit_button("Confirmar Reserva")

                        if reservar:
                            nova_reserva = {
                                "nome": nome,
                                "email": email,
                                "checkin": checkin.strftime("%Y-%m-%d"),
                                "checkout": checkout.strftime("%Y-%m-%d")
                            }

                            if hotel_id not in reservas:
                                reservas[hotel_id] = {}
                            if q_id not in reservas[hotel_id]:
                                reservas[hotel_id][q_id] = []

                            reservas[hotel_id][q_id].append(nova_reserva)
                            salvar_json(RESERVAS_FILE, reservas)

                            st.success("Reserva confirmada com sucesso!")
