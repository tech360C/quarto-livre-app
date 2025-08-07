# Arquivo: app.py
import streamlit as st
import os
import sqlite3
from datetime import datetime, date, timedelta
import pandas as pd
import bcrypt
from streamlit_calendar import calendar
import smtplib
from email.mime.text import MIMEText
import plotly.express as px
import json
import base64
import requests # NOVO: Importa a biblioteca requests

# --- URL DO BACKEND ---
# ATENÇÃO: SUBSTITUA ESTA URL PELA URL REAL DO SEU SERVIÇO DE BACKEND NO RENDER
# Exemplo: https://seu-backend-aqui.onrender.com
BACKEND_URL = "https://quarto-livre-backend.onrender.com"

# --- Configuração da Página Streamlit ---
st.set_page_config(
    page_title="Quarto Livre",
    page_icon="🏰",
    layout="wide"
)

# --- Estilos CSS Personalizados ---
st.markdown(
    """
    <style>
    /* Remove padding default para usar a largura total */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    /* Estilo para a imagem de cabeçalho com altura fixa */
    .header-image {
        width: 100%; /* Largura total */
        max-height: 250px; /* Altura máxima aumentada para aproximadamente 25cm (250px) */
        object-fit: cover; /* Recorta a imagem para preencher o espaço sem distorção */
    }

    /* Remove a "tarja" e usa o cabeçalho nativo */
    #root > div:nth-child(1) > div.with-header > div > div > div > section.main > div:nth-child(1) {
        display: none;
    }
    
    .st-emotion-cache-1c7y33h {
        padding-top: 0px !important;
        padding-bottom: 0px !important;
        padding-left: 0px !important;
        padding-right: 0px !important;
    }

    /* NOVO ESTILO: Container para os botões do menu superior */
    .top-menu-buttons {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        width: 100%;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    
    /* ESTILO ATUALIZADO: Classe para os botões do menu superior */
    .top-menu-buttons .stButton > button {
        width: 80px; /* Largura fixa aproximada de 2cm */
        height: 30px; /* Altura fixa para o botão ficar pequeno */
        padding: 2px 5px; /* Diminui drasticamente o padding */
        font-size: 10px; /* Diminui a fonte para caber no botão */
        margin: 0 2px; /* Diminui o espaçamento entre os botões */
        overflow: hidden; /* Garante que o texto não "vaze" */
        text-overflow: ellipsis; /* Adiciona '...' se o texto for muito longo */
        white-space: nowrap; /* Impede quebra de linha do texto */
    }

    /* Outros estilos permanecem para melhor UX */
    .stButton > button {
        background: linear-gradient(90deg, #1a73e8, #4a90e2);
        color: white;
        font-weight: 500;
        padding: 10px 20px;
        border-radius: 5px;
        border: none;
        transition: transform 0.2s;
    }
    .stButton > button:hover {
        transform: scale(1.05);
        background: linear-gradient(90deg, #1557b0, #357abd);
    }
    .stButton.logout-button > button {
        background: linear-gradient(90deg, #dc3545, #c82333);
        color: white;
        font-weight: 500;
        padding: 10px 20px;
        border-radius: 5px;
        border: none;
        transition: transform 0.2s;
    }
    .stButton.logout-button > button:hover {
        transform: scale(1.05);
        background: linear-gradient(90deg, #b02a37, #a71d2a);
    }
    .stButton.cancel-button > button {
        background: linear-gradient(90deg, #dc3545, #c82333);
        color: white;
        font-weight: 500;
        padding: 10px 20px;
        border-radius: 5px;
        border: none;
        transition: transform 0.2s;
    }
    .stButton.cancel-button > button:hover {
        transform: scale(1.05);
        background: linear-gradient(90deg, #b02a37, #a71d2a);
    }

    .login-form-container {
        width: 100%;
        display: flex;
        justify-content: center;
        margin: 20px 0;
    }
    .login-form-content {
        background-color: #ffffff;
        padding: 20px 40px;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        max-width: 500px;
        width: 100%;
    }
    .card {
        background: #ffffff;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 15px;
    }
    .notification {
        background: #28a745;
        color: white;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
        animation: fadeIn 0.5s;
        margin-bottom: 15px;
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    /* Adicionando estilos de centralização para a reserva */
    .reservation-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
    }
    .reservation-content {
        max-width: 900px;
        width: 100%;
        background-color: #f0f2f6; /* Fundo cinza claro */
        padding: 20px;
        border-radius: 10px;
    }
    .stDateInput div[data-testid="stDateInput"] {
        width: 100%;
    }

    .room-card {
        background-color: #ffffff;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        height: 100%;
        transition: transform 0.2s;
        cursor: pointer;
    }
    .room-card:hover {
        transform: translateY(-5px);
    }
    .room-card img {
        width: 100%;
        height: 180px;
        object-fit: cover;
        border-bottom: 1px solid #eee;
    }
    .room-card-content {
        padding: 15px;
        flex-grow: 1;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .room-card-title {
        font-size: 1.3em;
        font-weight: 600;
        color: #333;
        margin-bottom: 5px;
    }
    .room-card-price {
        font-size: 1.5em;
        font-weight: 700;
        color: #1a73e8;
        margin-top: 10px;
        margin-bottom: 15px;
    }
    .homepage-message {
        text-align: center;
        color: royalblue;
        padding: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Conversores e Funções de Banco de Dados ---
def adapt_date(date_obj):
    return date_obj.isoformat()

def convert_date(val):
    if val is None:
        return None
    if isinstance(val, bytes):
        val = val.decode('utf-8')
    elif isinstance(val, date):
        return val
    try:
        return datetime.fromisoformat(val).date()
    except (ValueError, TypeError):
        return None

sqlite3.register_adapter(datetime.date, adapt_date)
sqlite3.register_converter("DATE", convert_date)

def init_db():
    conn = None
    try:
        conn = sqlite3.connect("quarto_livre.db", detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()
        
        # Tabela de Usuários
        c.execute("CREATE TABLE IF NOT EXISTS users ("
                  "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                  "username TEXT UNIQUE,"
                  "password TEXT," # Agora armazena o hash da senha
                  "role TEXT,"
                  "security_question TEXT,"
                  "security_answer TEXT"
                  ")")

        # Tabela de Hotéis
        c.execute("CREATE TABLE IF NOT EXISTS hotels ("
                  "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                  "hotel_name TEXT,"
                  "owner_id INTEGER,"
                  "status TEXT,"
                  "hotel_email TEXT,"
                  "state TEXT,"
                  "city TEXT,"
                  "address TEXT,"
                  "phone TEXT,"
                  "website TEXT,"
                  "plan_type TEXT,"
                  "contract_start_date DATE,"
                  "contract_duration_months INTEGER DEFAULT 0,"
                  "FOREIGN KEY (owner_id) REFERENCES users(id)"
                  ")")

        # Tabela de Quartos
        c.execute("CREATE TABLE IF NOT EXISTS rooms ("
                  "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                  "hotel_id INTEGER,"
                  "room_type TEXT,"
                  "room_description TEXT,"
                  "price REAL,"
                  "available_dates TEXT," # Armazena JSON de datas ocupadas
                  "room_images TEXT," # Armazena JSON de URLs/Base64 de imagens
                  "FOREIGN KEY (hotel_id) REFERENCES hotels(id)"
                  ")")
        
        # Tabela de Reservas
        c.execute("CREATE TABLE IF NOT EXISTS reservations ("
                  "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                  "room_id INTEGER,"
                  "guest_name TEXT,"
                  "check_in DATE,"
                  "check_out DATE,"
                  "status TEXT DEFAULT 'pending'," # pending, active, rejected
                  "confirmation_method TEXT,"
                  "guest_email TEXT,"
                  "guest_contact TEXT,"
                  "confirmed_by_owner INTEGER DEFAULT 0," # 0=False, 1=True
                  "notified_owner INTEGER DEFAULT 0," # 0=False, 1=True
                  "payment_link TEXT," # Link de pagamento gerado pelo hotel
                  "FOREIGN KEY (room_id) REFERENCES rooms(id)"
                  ")")

        # Tabela de Configurações do Site
        c.execute("CREATE TABLE IF NOT EXISTS site_config ("
                  "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                  "config_name TEXT UNIQUE,"
                  "config_value TEXT"
                  ")")

        # Tabela para Solicitações de Upgrade de Plano
        c.execute("CREATE TABLE IF NOT EXISTS upgrade_requests ("
                  "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                  "hotel_id INTEGER,"
                  "owner_id INTEGER,"
                  "current_plan TEXT,"
                  "requested_plan TEXT,"
                  "request_date DATE,"
                  "status TEXT DEFAULT 'pending',"
                  "FOREIGN KEY (hotel_id) REFERENCES hotels(id),"
                  "FOREIGN KEY (owner_id) REFERENCES users(id)"
                  ")")

        # --- VERIFICAÇÃO E ADIÇÃO DE COLUNAS EXISTENTES (IMPORTANTE PARA ATUALIZAÇÕES) ---
        # Adiciona colunas que podem ter sido adicionadas em versões anteriores
        # (Se você já rodou o app e o DB foi criado, estas linhas garantem compatibilidade)

        # Colunas para 'hotels'
        c.execute("PRAGMA table_info(hotels)")
        columns = [col[1] for col in c.fetchall()]
        if "hotel_email" not in columns: c.execute("ALTER TABLE hotels ADD COLUMN hotel_email TEXT")
        if "state" not in columns: c.execute("ALTER TABLE hotels ADD COLUMN state TEXT")
        if "city" not in columns: c.execute("ALTER TABLE hotels ADD COLUMN city TEXT")
        if "address" not in columns: c.execute("ALTER TABLE hotels ADD COLUMN address TEXT")
        if "phone" not in columns: c.execute("ALTER TABLE hotels ADD COLUMN phone TEXT")
        if "website" not in columns: c.execute("ALTER TABLE hotels ADD COLUMN website TEXT")
        if "plan_type" not in columns: c.execute("ALTER TABLE hotels ADD COLUMN plan_type TEXT DEFAULT 'Gold'")
        if "contract_start_date" not in columns: c.execute("ALTER TABLE hotels ADD COLUMN contract_start_date DATE")
        if "contract_duration_months" not in columns: c.execute("ALTER TABLE hotels ADD COLUMN contract_duration_months INTEGER DEFAULT 0")

        # Colunas para 'rooms'
        c.execute("PRAGMA table_info(rooms)")
        columns = [col[1] for col in c.fetchall()]
        if "room_image" in columns: c.execute("ALTER TABLE rooms RENAME COLUMN room_image TO room_images") # Renomeia se existir
        if "room_images" not in columns and "room_image" not in columns: c.execute("ALTER TABLE rooms ADD COLUMN room_images TEXT")
        if "room_description" not in columns: c.execute("ALTER TABLE rooms ADD COLUMN room_description TEXT")
        if "price" not in columns: c.execute("ALTER TABLE rooms ADD COLUMN price REAL") # Garante que 'price' exista

        # Colunas para 'reservations'
        c.execute("PRAGMA table_info(reservations)")
        columns = [col[1] for col in c.fetchall()]
        if "confirmation_method" not in columns: c.execute("ALTER TABLE reservations ADD COLUMN confirmation_method TEXT")
        if "guest_email" not in columns: c.execute("ALTER TABLE reservations ADD COLUMN guest_email TEXT")
        if "guest_contact" not in columns: c.execute("ALTER TABLE reservations ADD COLUMN guest_contact TEXT")
        if "confirmed_by_owner" not in columns: c.execute("ALTER TABLE reservations ADD COLUMN confirmed_by_owner INTEGER DEFAULT 0")
        if "notified_owner" not in columns: c.execute("ALTER TABLE reservations ADD COLUMN notified_owner INTEGER DEFAULT 0")
        if "payment_link" not in columns: c.execute("ALTER TABLE reservations ADD COLUMN payment_link TEXT")
        if "status" not in columns: c.execute("ALTER TABLE reservations ADD COLUMN status TEXT DEFAULT 'pending'") # Garante que 'status' exista

        # Adicionar usuário administrador padrão se não existir
        c.execute("SELECT COUNT(*) FROM users WHERE username = ?", ("quartolivre",))
        if c.fetchone()[0] == 0:
            hashed_password = bcrypt.hashpw("Quartolivre2025".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            c.execute(
                "INSERT INTO users (username, password, role, security_question, security_answer) VALUES (?, ?, ?, ?, ?)",
                ("quartolivre", hashed_password, "admin", "Qual é o nome do seu primeiro animal de estimação?", "admin")
            )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Erro ao inicializar o banco de dados: {e}")
    finally:
        if conn:
            conn.close()

init_db() # Chame para garantir que o DB existe ao iniciar o frontend

# --- CONSTANTES ---
PLAN_PRICES = {
    "Gold": 250.00,
    "Platinum": 350.00,
    "Black": 499.99
}

# --- CONFIGURAÇÃO DE E-MAIL (PARA O FRONTEND, SE NECESSÁRIO) ---
# A maior parte do envio de e-mails de reserva foi movida para o backend.
# Mantenha aqui apenas se alguma função do frontend ainda precisar enviar e-mail.
EMAIL_SENDER = "quartolivre.reservas@gmail.com"
EMAIL_PASSWORD = "pkawwfdpxdnsyupo"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
ADMIN_EMAIL = "quartolivre.reservas@gmail.com"

# Som de notificação codificado em Base64
NOTIFICATION_SOUND_BASE64 = "data:audio/wav;base64,UklGRl9uAABXQVZFZm10IBAAAAABAAEARKwAAIhYAABBZGF0YUlsAABBAIAAAJAEgACQBIAAAEEAAAQAAAEAAAQAAAEAAAAAAAAAAAAAAAgAEgACQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJAEgACQBIAAAEEAAAQAAAEAAAQAAAEAAAAAAAAAAAAAAAgAEgACQAAAAAAAAAAAAAAJAEgACQAAAAAAAAAAAAAAEEAAAQAAAEAAAQAAAAABAAAAAAAAAAAAAAgAEgACQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJAEgACQBIAAAEEAAAQAAAEAAAQAAAEAAAAAAAAAAAAAAAgAEgACQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJAEgACQBIAAAEEAAAQAAAEAAAQAAAEAAAAAAAAAAAAAAAgAEgACQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

def play_notification_sound():
    st.markdown(
        f"""
        <audio autoplay controls style="display:none;">
            <source src="{NOTIFICATION_SOUND_BASE64}" type="audio/wav">
            Seu navegador não suporta o elemento de áudio.
        </audio>
        """,
        unsafe_allow_html=True,
    )

def send_email(recipient_email, subject, body):
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        st.error("Configuração de e-mail ausente ou incompleta. O envio de e-mails está desativado.")
        return False

    msg = MIMEText(body, 'html')
    msg['Subject'] = subject
    msg['From'] = EMAIL_SENDER
    msg['To'] = recipient_email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, recipient_email, msg.as_string())
        return True
    except smtplib.SMTPAuthenticationError:
        st.error("Erro de Autenticação SMTP. As credenciais do e-mail estão incorretas.")
        return False
    except smtplib.SMTPException as e:
        st.error(f"Erro SMTP ao enviar o e-mail: {e}")
        return False
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao enviar o e-mail: {e}")
        return False

# --- Funções Auxiliares (do Frontend) ---
def get_header_image():
    conn = sqlite3.connect("quarto_livre.db", detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    c.execute("SELECT config_value FROM site_config WHERE config_name = 'header_image_base64'")
    image_data = c.fetchone()
    conn.close()

    if image_data and image_data[0]:
        return image_data[0]
    return None

def get_homepage_message():
    conn = sqlite3.connect("quarto_livre.db", detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    c.execute("SELECT config_value FROM site_config WHERE config_name = 'homepage_message'")
    message_data = c.fetchone()
    conn.close()

    if message_data and message_data[0]:
        return message_data[0]
    return "## Fazer Reserva"

def get_image_as_base64(room_id):
    conn = sqlite3.connect("quarto_livre.db", detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    c.execute("SELECT room_images FROM rooms WHERE id = ?", (room_id,))
    images_json = c.fetchone()[0]
    conn.close()

    if images_json:
        try:
            images = json.loads(images_json)
            if images:
                return images[0] # Retorna apenas a primeira imagem
        except json.JSONDecodeError:
            pass
    return "https://via.placeholder.com/300x180?text=Sem+Foto"

def load_image_from_db_or_placeholder(room_id):
    image_data = get_image_as_base64(room_id)
    if image_data:
        return image_data
    return "https://via.placeholder.com/300x180?text=Sem+Foto"

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def update_occupied_dates(conn, room_id, check_in, check_out):
    c = conn.cursor()
    c.execute("SELECT available_dates FROM rooms WHERE id = ?", (room_id,))
    available_dates_json = c.fetchone()[0]
    
    occupied_dates_data = {}
    if available_dates_json:
        try:
            occupied_dates_data = json.loads(available_dates_json)
        except json.JSONDecodeError:
            st.warning(f"Erro ao decodificar JSON para room_id {room_id}. Reiniciando dados de ocupação.")
            occupied_dates_data = {}
    
    occupied_list = occupied_dates_data.get("occupied", [])
    
    current_date = check_in
    while current_date < check_out:
        date_str = current_date.isoformat()
        if date_str not in occupied_list:
            occupied_list.append(date_str)
        current_date += timedelta(days=1)
    
    occupied_dates_data["occupied"] = sorted(list(set(occupied_list)))
    
    c.execute("UPDATE rooms SET available_dates = ? WHERE id = ?", (json.dumps(occupied_dates_data), room_id))
    conn.commit()

def clear_occupied_dates(conn, room_id, check_in, check_out):
    c = conn.cursor()
    c.execute("SELECT available_dates FROM rooms WHERE id = ?", (room_id,))
    available_dates_json = c.fetchone()[0]
    
    occupied_dates_data = {}
    if available_dates_json:
        try:
            occupied_dates_data = json.loads(available_dates_json)
        except json.JSONDecodeError:
            st.warning("Erro ao decodificar JSON. Ignorando limpeza de dados corrompidos.")
            return
    
    occupied_list = occupied_dates_data.get("occupied", [])
    
    current_date = check_in
    while current_date < check_out:
        date_str = current_date.isoformat()
        if date_str in occupied_list:
            occupied_list.remove(date_str)
        current_date += timedelta(days=1)
    
    occupied_dates_data["occupied"] = sorted(list(set(occupied_list)))
    
    c.execute("UPDATE rooms SET available_dates = ? WHERE id = ?", (json.dumps(occupied_dates_data), room_id))
    conn.commit()

# --- Função de Reserva de Hóspede (Simplificada) ---
def guest_reservation_page(): # Renomeada para evitar conflito com a função que chama o backend
    header_image = get_header_image()
    if header_image:
        st.markdown(f'<img src="{header_image}" class="header-image">', unsafe_allow_html=True)
    
    homepage_message = get_homepage_message()
    st.markdown(f'<div class="homepage-message">{homepage_message}</div>', unsafe_allow_html=True)

    st.markdown("---")

    try:
        conn = sqlite3.connect("quarto_livre.db", detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()
        
        # Obter estados e cidades de hotéis aprovados e NÃO expirados
        c.execute("SELECT DISTINCT state FROM hotels WHERE status = 'approved' ORDER BY state")
        states = [s[0] for s in c.fetchall()]
        
        if not states:
            st.warning("Nenhum hotel aprovado disponível no momento.")
            conn.close()
            return

        col_filters_1, col_filters_2 = st.columns(2)
        with col_filters_1:
            selected_state = st.selectbox("Selecione o Estado", states, key="res_state_filter")
        
        cities = []
        if selected_state:
            c.execute("SELECT DISTINCT city FROM hotels WHERE status = 'approved' AND state = ? ORDER BY city", (selected_state,))
            cities = [c[0] for c in c.fetchall()]
            
        with col_filters_2:
            selected_city = st.selectbox("Selecione a Cidade", cities, key="res_city_filter")

        if not selected_city:
            st.warning("Selecione uma cidade para ver os hotéis disponíveis.")
            conn.close()
            return
        
        # Obter IDs dos hotéis aprovados na cidade selecionada
        c.execute("SELECT id, hotel_name FROM hotels WHERE status = 'approved' AND state = ? AND city = ?", (selected_state, selected_city))
        hotels = c.fetchall()
        hotel_ids = [h[0] for h in hotels]
        hotel_names = {h[0]: h[1] for h in hotels}

        if not hotel_ids:
            st.warning(f"Nenhum hotel encontrado em {selected_city}.")
            conn.close()
            return

        st.markdown("---")
        
        st.subheader("Selecione as Datas de Interesse")
        today = date.today()
        col_dates_1, col_dates_2 = st.columns(2)
        with col_dates_1:
            check_in_global = st.date_input("Data de Check-in", value=today, min_value=today, key="res_check_in_global")
        with col_dates_2:
            default_check_out_global = check_in_global + timedelta(days=1)
            check_out_global = st.date_input("Data de Check-out", value=default_check_out_global, min_value=check_in_global + timedelta(days=1), key="res_check_out_global")
        
        st.markdown("---")
        st.subheader(f"Quartos Disponíveis em {selected_city}")

        # Obter quartos dos hotéis selecionados
        placeholders = ', '.join('?' for _ in hotel_ids)
        query = f"SELECT id, hotel_id, room_type, price, room_description FROM rooms WHERE hotel_id IN ({placeholders})"
        c.execute(query, hotel_ids)
        rooms = c.fetchall()
        
        if not rooms:
            st.warning("Nenhum quarto disponível nesta cidade.")
            conn.close()
            return

        cols_per_row = 3
        
        # Iterar sobre os hotéis e seus quartos
        for hotel_id in hotel_ids:
            hotel_name = hotel_names[hotel_id]
            st.markdown(f"### Quartos do Hotel: {hotel_name}")
            
            hotel_rooms = [r for r in rooms if r[1] == hotel_id]
            
            if not hotel_rooms:
                st.info("Nenhum quarto disponível neste hotel.")
                continue

            room_cols = st.columns(min(cols_per_row, len(hotel_rooms)))
            
            for i, room in enumerate(hotel_rooms):
                room_id, _, room_type, price, room_description = room
                
                c.execute("SELECT available_dates FROM rooms WHERE id = ?", (room_id,))
                room_dates_json = c.fetchone()[0] or "{}"
                occupied_dates_data = json.loads(room_dates_json)
                occupied_list = occupied_dates_data.get("occupied", [])
                
                is_available = True
                current_checking_date = check_in_global
                while current_checking_date < check_out_global:
                    if current_checking_date.isoformat() in occupied_list:
                        is_available = False
                        break
                    current_checking_date += timedelta(days=1)
                
                image_url = load_image_from_db_or_placeholder(room_id)

                with room_cols[i % cols_per_row]:
                    st.markdown(f"""
                    <div class="room-card" id="room_card_{room_id}">
                        <img src="{image_url}" alt="{room_type}">
                        <div class="room-card-content">
                            <div class="room-card-title">{room_type} (ID: {room_id})</div>
                            <div class="room-card-description">
                                {room_description if room_description else 'Espaçoso, confortável e com as melhores comodidades. Perfeito para sua estadia!'}
                            </div>
                            <div class="room-card-price">R$ {price:.2f} / noite</div>
                    """, unsafe_allow_html=True)

                    if is_available:
                        if st.button(f"Reservar Quarto {room_id}", key=f"reserve_room_{room_id}"):
                            st.session_state.selected_room_for_booking = room_id
                            st.session_state.booking_check_in = check_in_global
                            st.session_state.booking_check_out = check_out_global
                            st.session_state.show_booking_form = True
                            st.rerun()
                    else:
                        st.warning("Indisponível para as datas selecionadas.")
                    
                    st.markdown("</div></div>", unsafe_allow_html=True)
            st.markdown("---")


        if st.session_state.get("show_booking_form", False):
            st.markdown("---")
            st.subheader("Finalizar sua Reserva")
            st.info(f"Você está reservando o Quarto ID: **{st.session_state.selected_room_for_booking}** "
                    f"de **{st.session_state.booking_check_in.strftime('%d/%m/%Y')}** "
                    f"até **{st.session_state.booking_check_out.strftime('%d/%m/%Y')}**.")

            guest_name_final = st.text_input("Seu Nome Completo", key="final_guest_name")
            guest_email_final = st.text_input("Seu Melhor E-mail", key="final_guest_email")
            guest_contact_final = st.text_input("Seu Telefone/WhatsApp (opcional)", key="final_guest_contact")

            if st.button("Confirmar Reserva Final", key="final_reservation_btn"):
                if guest_name_final and guest_email_final:
                    # NOVO CÓDIGO: Envia a reserva para o backend
                    reservation_data = {
                        "room_id": st.session_state.selected_room_for_booking,
                        "guest_name": guest_name_final,
                        "check_in": st.session_state.booking_check_in.isoformat(),
                        "check_out": st.session_state.booking_check_out.isoformat(),
                        "guest_email": guest_email_final,
                        "guest_contact": guest_contact_final,
                    }

                    try:
                        response = requests.post(f"{BACKEND_URL}/api/create_reservation", json=reservation_data)
                        
                        if response.status_code == 201:
                            st.success("Sua reserva foi solicitada! O hotel foi notificado e irá enviar o link de pagamento. Monitore seu e-mail para a confirmação final.")
                        else:
                            st.error(f"Erro ao criar a reserva. Status: {response.status_code} - {response.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Erro de conexão com o servidor do hotel. Por favor, tente novamente mais tarde. Erro: {e}")

                    # Limpa o estado da sessão e reinicia a página
                    st.session_state.show_booking_form = False
                    if 'selected_room_for_booking' in st.session_state: del st.session_state['selected_room_for_booking']
                    if 'booking_check_in' in st.session_state: del st.session_state['booking_check_in']
                    if 'booking_check_out' in st.session_state: del st.session_state['booking_check_out']
                    st.rerun()
                else:
                    st.error("Por favor, preencha seu nome e e-mail para finalizar a reserva.")

        conn.close()
    except sqlite3.Error as e:
        st.error(f"Erro ao acessar o banco de dados: {e}")

# --- Funções de Autenticação e Gerenciamento de Usuários ---
def register_hotel_owner():
    st.subheader("Cadastro de Dono de Hotel")
    username = st.text_input("Usuário", key="register_username")
    password = st.text_input("Senha", type="password", key="register_password")
    
    st.markdown("---")
    st.subheader("Informações do Hotel")
    hotel_name = st.text_input("Nome do Hotel", key="register_hotel_name")
    hotel_email = st.text_input("E-mail para Receber Reservas", key="register_hotel_email")
    hotel_address = st.text_input("Endereço Completo", key="register_hotel_address")
    hotel_phone = st.text_input("Telefone de Contato", key="register_hotel_phone")
    hotel_website = st.text_input("Site do Hotel (Opcional)", key="register_hotel_website")
    hotel_state = st.text_input("Estado (Ex: MG)", key="register_hotel_state")
    hotel_city = st.text_input("Cidade (Ex: Belo Horizonte)", key="register_hotel_city")

    st.markdown("---")
    st.subheader("Planos de Assinatura")
    plan_type = st.selectbox(
        "Selecione um Plano",
        ["Gold", "Platinum", "Black"],
        key="plan_type_select",
        format_func=lambda x: f"{x} - R$ {PLAN_PRICES.get(x, 0.0):.2f} mensal",
        help="""
        * **Plano Gold**: 1 quarto, 3 fotos por quarto.
        * **Plano Platinum**: 3 quartos, 3 fotos por quarto.
        * **Plano Black**: Quartos ilimitados, 5 fotos por quarto.
        """
    )

    st.markdown("---")
    st.subheader("Recuperação de Senha")
    security_question = st.selectbox(
        "Pergunta de Segurança",
        [
            "Qual é o nome do seu primeiro animal de estimação?",
            "Qual é a cidade onde você nasceu?",
            "Qual é o nome do seu melhor amigo de infância?"
        ],
        key="security_question_select"
    )
    security_answer = st.text_input("Resposta de Segurança", key="security_answer_input")
    
    if st.button("Cadastrar Hotel", key="register_hotel_btn"):
        if username and password and hotel_name and hotel_email and hotel_address and hotel_phone and hotel_state and hotel_city and security_answer:
            try:
                conn = sqlite3.connect("quarto_livre.db", detect_types=sqlite3.PARSE_DECLTYPES)
                c = conn.cursor()
                hashed_password = hash_password(password)
                c.execute(
                    "INSERT INTO users (username, password, role, security_question, security_answer) VALUES (?, ?, ?, ?, ?)",
                    (username, hashed_password, "owner", security_question, security_answer.lower())
                )
                user_id = c.lastrowid
                c.execute(
                    "INSERT INTO hotels (hotel_name, owner_id, status, hotel_email, state, city, address, phone, website, plan_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (hotel_name, user_id, "pending", hotel_email, hotel_state, hotel_city, hotel_address, hotel_phone, hotel_website, plan_type)
                )
                conn.commit()
                st.success(f"Hotel '{hotel_name}' cadastrado com sucesso! Aguarde aprovação do administrador.")
            except sqlite3.IntegrityError:
                st.error("Usuário já existe! Escolha outro nome de usuário.")
            except sqlite3.Error as e:
                st.error(f"Erro ao cadastrar: {e}")
            finally:
                if conn:
                    conn.close()
        else:
            st.error("Preencha todos os campos obrigatórios!")

def reset_password():
    st.subheader("Redefinir Senha")
    username = st.text_input("Usuário", key="reset_username_input")
    
    if st.button("Buscar Pergunta de Segurança", key="buscar_pergunta_btn"):
        if username:
            try:
                conn = sqlite3.connect("quarto_livre.db", detect_types=sqlite3.PARSE_DECLTYPES)
                c = conn.cursor()
                c.execute("SELECT security_question, security_answer FROM users WHERE username = ?", (username,))
                user = c.fetchone()
                
                if user:
                    st.session_state.reset_user_found = True
                    st.session_state.reset_security_question = user[0]
                    st.session_state.reset_security_answer = user[1]
                    st.session_state.reset_username_temp = username
                    st.success(f"Pergunta de Segurança encontrada para '{username}'.")
                else:
                    st.session_state.reset_user_found = False
                    st.error("Usuário não encontrado.")
            except sqlite3.Error as e:
                st.error(f"Erro ao buscar usuário: {e}")
            finally:
                if conn:
                    conn.close()
        else:
            st.error("Por favor, digite o nome de usuário para buscar a pergunta de segurança.")

    if st.session_state.get("reset_user_found"):
        st.write(f"Pergunta de Segurança: **{st.session_state.reset_security_question}**")
        answer = st.text_input("Sua Resposta", key="reset_answer_input")
        new_password = st.text_input("Nova Senha", type="password", key="reset_new_password_input")
        confirm_password = st.text_input("Confirmar Nova Senha", type="password", key="reset_confirm_password_input")
        
        if st.button("Redefinir Senha", key="reset_password_btn"):
            if answer and new_password and confirm_password:
                if answer.lower() == st.session_state.reset_security_answer.lower():
                    if new_password == confirm_password:
                        try:
                            conn = sqlite3.connect("quarto_livre.db", detect_types=sqlite3.PARSE_DECLTYPES)
                            c = conn.cursor()
                            hashed_password = hash_password(new_password)
                            c.execute(
                                "UPDATE users SET password = ? WHERE username = ?",
                                (hashed_password, st.session_state.reset_username_temp)
                            )
                            conn.commit()
                            st.success("Senha redefinida com sucesso! Você já pode fazer login com a nova senha.")
                            
                            # Limpa o estado da sessão para evitar reexecução
                            for key in ["reset_user_found", "reset_security_question", "reset_security_answer", "reset_username_temp"]:
                                if key in st.session_state:
                                    del st.session_state[key]
                            st.rerun()
                        except sqlite3.Error as e:
                            st.error(f"Erro ao atualizar a senha: {e}")
                        finally:
                            if conn:
                                conn.close()
                    else:
                        st.error("As senhas não coincidem. Por favor, digite a mesma senha nos dois campos.")
                else:
                    st.error("Resposta de segurança incorreta.")
            else:
                st.error("Por favor, preencha todos os campos para redefinir a senha.")

def login():
    st.markdown('<div class="login-form-container">', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="login-form-content">', unsafe_allow_html=True)
        st.subheader("Login")
        username = st.text_input("Usuário", key="login_username")
        password = st.text_input("Senha", type="password", key="login_password")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Entrar", key="login_btn"):
                if username and password:
                    try:
                        conn = sqlite3.connect("quarto_livre.db", detect_types=sqlite3.PARSE_DECLTYPES)
                        c = conn.cursor()
                        c.execute("SELECT id, password, role FROM users WHERE username = ?", (username,))
                        user = c.fetchone()
                        if user and check_password(password, user[1]):
                            st.session_state.logged_in = True
                            st.session_state.user_id = user[0]
                            st.session_state.user_role = user[2]
                            st.session_state.username = username
                            st.success(f"Bem-vindo(a), {username}!")
                            st.rerun()
                        else:
                            st.error("Usuário ou senha incorretos.")
                    except sqlite3.Error as e:
                        st.error(f"Erro de banco de dados: {e}")
                    finally:
                        if conn:
                            conn.close()
                else:
                    st.error("Preencha usuário e senha.")
        with col2:
            if st.button("Esqueceu a senha?", key="forgot_password_btn"):
                st.session_state.forgot_password = True
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def logout():
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_role = None
    st.session_state.page = "home"
    st.success("Você saiu da sua conta.")
    st.rerun()

def get_current_hotel():
    conn = sqlite3.connect("quarto_livre.db", detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    c.execute("SELECT id, hotel_name, status, hotel_email, state, city, address, phone, website, plan_type, contract_start_date, contract_duration_months FROM hotels WHERE owner_id = ?", (st.session_state.user_id,))
    hotel_info = c.fetchone()
    conn.close()
    return hotel_info

def is_hotel_owner_approved():
    hotel_info = get_current_hotel()
    if hotel_info and hotel_info[2] == 'approved':
        return True
    return False

def check_and_update_subscription_status(hotel_id, contract_start_date, contract_duration_months):
    if contract_start_date and contract_duration_months and contract_duration_months > 0:
        expiration_date = contract_start_date + timedelta(days=contract_duration_months * 30)
        if date.today() > expiration_date:
            conn = sqlite3.connect("quarto_livre.db", detect_types=sqlite3.PARSE_DECLTYPES)
            c = conn.cursor()
            c.execute("UPDATE hotels SET status = 'expired' WHERE id = ?", (hotel_id,))
            conn.commit()
            conn.close()
            return True
    return False

# --- Páginas da Aplicação (Dashboard) ---
def admin_dashboard():
    st.title("Painel de Administração")
    
    conn = sqlite3.connect("quarto_livre.db", detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()

    # NOVO: Gerenciar solicitações de upgrade
    st.header("Solicitações de Upgrade de Plano")
    c.execute(
        "SELECT ur.id, h.hotel_name, u.username, ur.current_plan, ur.requested_plan, ur.request_date FROM upgrade_requests ur "
        "JOIN hotels h ON ur.hotel_id = h.id "
        "JOIN users u ON ur.owner_id = u.id "
        "WHERE ur.status = 'pending'"
    )
    upgrade_requests = c.fetchall()

    if upgrade_requests:
        for request in upgrade_requests:
            req_id, hotel_name, owner_username, current_plan, requested_plan, request_date = request
            with st.container(border=True):
                st.write(f"**Hotel:** {hotel_name} (Proprietário: {owner_username})")
                st.write(f"**Solicitação:** Upgrade do plano **{current_plan}** para **{requested_plan}**")
                st.write(f"**Data da Solicitação:** {request_date}")
                
                col_up_buttons = st.columns(2)
                with col_up_buttons[0]:
                    if st.button(f"Aprovar Upgrade", key=f"approve_upgrade_{req_id}", type="primary"):
                        c.execute("UPDATE hotels SET plan_type = ? WHERE hotel_name = ?", (requested_plan, hotel_name))
                        c.execute("UPDATE upgrade_requests SET status = 'approved' WHERE id = ?", (req_id,))
                        conn.commit()
                        st.success(f"Upgrade do hotel '{hotel_name}' para o plano {requested_plan} aprovado!")
                        # Enviar e-mail para o dono do hotel sobre a aprovação
                        c.execute("SELECT hotel_email FROM hotels WHERE hotel_name = ?", (hotel_name,))
                        hotel_email = c.fetchone()[0]
                        if hotel_email:
                            subject = f"Upgrade de Plano Aprovado - {hotel_name}"
                            body = f"""
                            Olá {owner_username},
                            
                            Sua solicitação de upgrade para o plano **{requested_plan}** no hotel **{hotel_name}** foi aprovada!
                            Você já pode aproveitar os benefícios do novo plano.

                            Atenciosamente,
                            Equipe Quarto Livre
                            """
                            send_email(hotel_email, subject, body)
                        st.rerun()
                with col_up_buttons[1]:
                    if st.button(f"Rejeitar Upgrade", key=f"reject_upgrade_{req_id}"):
                        c.execute("UPDATE upgrade_requests SET status = 'rejected' WHERE id = ?", (req_id,))
                        conn.commit()
                        st.warning(f"Upgrade do hotel '{hotel_name}' rejeitado.")
                        # Enviar e-mail para o dono do hotel sobre a rejeição
                        c.execute("SELECT hotel_email FROM hotels WHERE hotel_name = ?", (hotel_name,))
                        hotel_email = c.fetchone()[0]
                        if hotel_email:
                            subject = f"Upgrade de Plano Rejeitado - {hotel_name}"
                            body = f"""
                            Olá {owner_username},
                            
                            Sua solicitação de upgrade para o plano **{requested_plan}** no hotel **{hotel_name}** foi rejeitada.
                            Caso tenha dúvidas, entre em contato com o suporte.

                            Atenciosamente,
                            Equipe Quarto Livre
                            """
                            send_email(hotel_email, subject, body)
                        st.rerun()
    else:
        st.info("Nenhuma solicitação de upgrade pendente.")

    st.markdown("---")

    st.subheader("Gerenciar Hotéis e Donos")

    # Hotéis Pendentes
    st.header("Hotéis Pendentes de Aprovação")
    c.execute("SELECT h.id, h.hotel_name, u.username, h.state, h.city FROM hotels h JOIN users u ON h.owner_id = u.id WHERE h.status = 'pending'")
    pending_hotels = c.fetchall()

    if pending_hotels:
        for hotel in pending_hotels:
            hotel_id, hotel_name, username, state, city = hotel
            with st.container(border=True):
                st.write(f"ID: {hotel_id}")
                st.write(f"Hotel: **{hotel_name}** (Proprietário: {username})")
                st.write(f"Local: {city}, {state}")
                
                with st.form(key=f"approve_form_{hotel_id}"):
                    contract_duration = st.number_input("Duração do Contrato (meses)", min_value=1, value=12, key=f"contract_months_{hotel_id}")
                    col_buttons = st.columns(2)
                    with col_buttons[0]:
                        if st.form_submit_button(f"Aprovar Hotel {hotel_name}", type="primary"):
                            c.execute(
                                "UPDATE hotels SET status = 'approved', contract_start_date = ?, contract_duration_months = ? WHERE id = ?",
                                (date.today(), contract_duration, hotel_id)
                            )
                            conn.commit()
                            st.success(f"Hotel '{hotel_name}' aprovado com sucesso para {contract_duration} meses!")
                            st.rerun()
                    with col_buttons[1]:
                        if st.form_submit_button(f"Rejeitar Hotel {hotel_name}"):
                            c.execute("UPDATE hotels SET status = 'rejected' WHERE id = ?", (hotel_id,))
                            conn.commit()
                            st.warning(f"Hotel '{hotel_name}' rejeitado.")
                            st.rerun()
    else:
        st.info("Nenhum hotel pendente de aprovação.")

    st.markdown("---")

    # Hotéis Aprovados e Inativos (Reprovados e Expirados)
    st.header("Hotéis Ativos e Inativos")
    c.execute("SELECT h.id, h.hotel_name, u.username, h.status, h.state, h.city, h.contract_start_date, h.contract_duration_months FROM hotels h JOIN users u ON h.owner_id = u.id WHERE h.status IN ('approved', 'rejected', 'expired')")
    all_hotels = c.fetchall()

    if all_hotels:
        for hotel in all_hotels:
            hotel_id, hotel_name, username, status, state, city, contract_start_date, contract_duration_months = hotel
            
            status_text = ""
            status_emoji = ""
            if status == "approved":
                status_emoji = "✅"
                status_text = "Aprovado"
            elif status == "rejected":
                status_emoji = "❌"
                status_text = "Reprovado"
            elif status == "expired":
                status_emoji = "⏳"
                status_text = "Expirado"

            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([0.5, 2, 1, 1])
                with col1:
                    st.write(f"ID: {hotel_id}")
                with col2:
                    st.write(f"Hotel: **{hotel_name}** ({username})")
                    st.write(f"Local: {city}, {state}")
                    # CORREÇÃO: Adicionar verificação para evitar erro de NoneType
                    if status in ["approved", "expired"] and contract_start_date:
                        expiration_date = contract_start_date + timedelta(days=contract_duration_months * 30)
                        st.caption(f"Contrato até: {expiration_date.strftime('%d/%m/%Y')}")
                    else:
                        st.caption("Contrato não definido")
                with col3:
                    st.write(f"{status_emoji} {status_text}")
                
                with col4:
                    if status == "approved":
                        if st.button(f"Reprovar {hotel_name}", key=f"reject_{hotel_id}"):
                            c.execute("UPDATE hotels SET status = 'rejected' WHERE id = ?", (hotel_id,))
                            conn.commit()
                            st.warning(f"Hotel '{hotel_name}' reprovado.")
                            st.rerun()
                    else: # 'rejected' ou 'expired'
                        if st.button(f"Reativar {hotel_name}", key=f"reapprove_{hotel_id}", type="primary"):
                            with st.form(key=f"reactivate_form_{hotel_id}"):
                                new_duration = st.number_input("Duração do Novo Contrato (meses)", min_value=1, value=12, key=f"new_duration_{hotel_id}")
                                if st.form_submit_button("Confirmar Reativação"):
                                    c.execute(
                                        "UPDATE hotels SET status = 'approved', contract_start_date = ?, contract_duration_months = ? WHERE id = ?",
                                        (date.today(), new_duration, hotel_id)
                                    )
                                    conn.commit()
                                    st.success(f"Hotel '{hotel_name}' reativado por mais {new_duration} meses.")
                                    st.rerun()
    else:
        st.info("Nenhum hotel aprovado ou reprovado.")
        
    st.markdown("---")

    # Configurações do Site
    st.header("Configurações do Site")
    st.subheader("Alterar Imagem de Cabeçalho")
    uploaded_file = st.file_uploader("Escolha uma imagem de cabeçalho (PNG, JPEG)", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        base64_image = f"data:image/png;base64,{base64.b64encode(file_bytes).decode()}"
        st.image(uploaded_file, caption="Prévia da Imagem de Cabeçalho", use_container_width=True)
        if st.button("Salvar Imagem de Cabeçalho"):
            c.execute("INSERT OR REPLACE INTO site_config (config_name, config_value) VALUES (?, ?)", ('header_image_base64', base64_image))
            conn.commit()
            st.success("Imagem de cabeçalho salva com sucesso!")
            st.rerun()
    
    st.subheader("Alterar Mensagem da Página Inicial")
    current_message = get_homepage_message().replace('## ', '')
    new_message = st.text_area("Digite a nova mensagem (use Markdown para formatação)", value=current_message, height=100)
    if st.button("Salvar Mensagem"):
        final_message = f"## {new_message}"
        c.execute("INSERT OR REPLACE INTO site_config (config_name, config_value) VALUES (?, ?)", ('homepage_message', final_message))
        conn.commit()
        st.success("Mensagem da página inicial salva com sucesso!")
        st.rerun()

    conn.close()

def owner_dashboard():
    hotel_info = get_current_hotel()
    if not hotel_info:
        st.error("Nenhum hotel associado a este usuário.")
        return
    
    hotel_id, hotel_name, status, hotel_email, state, city, address, phone, website, plan_type, contract_start_date, contract_duration_months = hotel_info

    # Verificação de expiração do contrato
    if status == 'approved' and check_and_update_subscription_status(hotel_id, contract_start_date, contract_duration_months):
        status = 'expired'
        st.rerun()

    st.title(f"Painel do Hotel: {hotel_name}")
    st.subheader(f"Status do Hotel: **{status.capitalize()}**")

    if status == 'pending':
        st.warning("Seu hotel está aguardando aprovação do administrador.")
        return
    if status == 'expired':
        st.error("Seu contrato de assinatura expirou. Entre em contato com o administrador para reativar.")
        return
    
    # NOVO: Verificar e mostrar status da solicitação de upgrade
    conn = sqlite3.connect("quarto_livre.db", detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    c.execute("SELECT requested_plan, status FROM upgrade_requests WHERE hotel_id = ? AND status = 'pending'", (hotel_id,))
    pending_upgrade = c.fetchone()
    
    if pending_upgrade:
        requested_plan, upgrade_status = pending_upgrade
        st.info(f"Você tem uma solicitação de upgrade para o plano **{requested_plan}** pendente. Aguardando aprovação do administrador.")
    else:
        st.info(f"Seu plano atual é: **{plan_type.capitalize()}** (R$ {PLAN_PRICES.get(plan_type, 0.0):.2f} / mês)")

    st.markdown("---")

    # NOVO: Seção para solicitar upgrade
    st.header("Upgrade de Plano")
    if not pending_upgrade:
        available_plans = ["Gold", "Platinum", "Black"]
        plan_index = available_plans.index(plan_type)
        upgrade_plans = available_plans[plan_index+1:]

        if upgrade_plans:
            with st.form("upgrade_plan_form"):
                st.write(f"Seu plano atual é **{plan_type}**. Você pode fazer upgrade para os seguintes planos:")
                selected_upgrade = st.radio(
                    "Selecione o plano de destino:",
                    upgrade_plans,
                    format_func=lambda x: f"{x} - R$ {PLAN_PRICES.get(x, 0.0):.2f} mensal"
                )
                if st.form_submit_button("Solicitar Upgrade"):
                    try:
                        c.execute(
                            "INSERT INTO upgrade_requests (hotel_id, owner_id, current_plan, requested_plan, request_date, status) VALUES (?, ?, ?, ?, ?, ?)",
                            (hotel_id, st.session_state.user_id, plan_type, selected_upgrade, date.today(), 'pending')
                        )
                        conn.commit()
                        st.success(f"Solicitação de upgrade para o plano {selected_upgrade} enviada com sucesso! Aguarde a aprovação do administrador.")
                        
                        # Enviar notificação por e-mail para o administrador
                        subject_admin = f"Nova Solicitação de Upgrade de Plano - {hotel_name}"
                        body_admin = f"""
                        Olá Administrador,

                        Uma nova solicitação de upgrade de plano foi feita por um hotel.

                        - Hotel: **{hotel_name}**
                        - Dono: {st.session_state.username}
                        - Plano Atual: {plan_type}
                        - Plano Solicitado: **{selected_upgrade}**
                        - Data da Solicitação: {date.today().strftime('%d/%m/%Y')}

                        Acesse o painel de administração para aprovar ou rejeitar esta solicitação.
                        """
                        if send_email(ADMIN_EMAIL, subject_admin, body_admin):
                            st.info("O administrador foi notificado por e-mail.")
                        else:
                            st.warning("Ocorreu um erro ao notificar o administrador por e-mail.")
                        
                        st.rerun()
                    except sqlite3.Error as e:
                        st.error(f"Erro ao registrar solicitação: {e}")
        else:
            st.info("Você já possui o plano mais alto (Black).")

    st.markdown("---")
    
    # Gerenciamento de Quartos
    st.header("Gerenciamento de Quartos")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Adicionar Novo Quarto")
        
        # Lógica de limites baseada no plano
        c.execute("SELECT COUNT(*) FROM rooms WHERE hotel_id = ?", (hotel_id,))
        current_room_count = c.fetchone()[0]

        room_limit = 0
        photo_limit = 0
        if plan_type == "Gold":
            room_limit = 1
            photo_limit = 3
        elif plan_type == "Platinum":
            room_limit = 3
            photo_limit = 3
        elif plan_type == "Black":
            room_limit = float('inf')
            photo_limit = 5
        
        can_add_room = current_room_count < room_limit or plan_type == "Black"
        
        if not can_add_room:
            st.warning(f"Você atingiu o limite de {room_limit} quarto(s) para o seu plano **{plan_type}**.")
        else:
            with st.form("add_room_form", clear_on_submit=True):
                room_type = st.text_input("Tipo de Quarto")
                room_description = st.text_area("Descrição do Quarto (Opcional)") # NOVO: Campo de descrição
                price = st.number_input("Preço por Noite (R$)", min_value=0.0, format="%.2f")
                uploaded_room_images = st.file_uploader(
                    f"Upload de até {photo_limit} fotos do Quarto",
                    type=["png", "jpg", "jpeg"],
                    accept_multiple_files=True
                )
                
                submitted = st.form_submit_button("Adicionar Quarto")
                if submitted:
                    if not room_type or not price > 0:
                        st.error("Por favor, preencha o tipo e o preço do quarto.")
                    elif uploaded_room_images and len(uploaded_room_images) > photo_limit:
                        st.error(f"Você só pode enviar até {photo_limit} fotos para o seu plano **{plan_type}**.")
                    else:
                        try:
                            images_base64 = []
                            if uploaded_room_images:
                                for uploaded_file in uploaded_room_images:
                                    file_bytes = uploaded_file.read()
                                    images_base64.append(f"data:image/{uploaded_file.type.split('/')[-1]};base64,{base64.b64encode(file_bytes).decode()}")
                            
                            images_json = json.dumps(images_base64)

                            c.execute(
                                "INSERT INTO rooms (hotel_id, room_type, room_description, price, room_images, available_dates) VALUES (?, ?, ?, ?, ?, ?)",
                                (hotel_id, room_type, room_description, price, images_json, "{}")
                            )
                            conn.commit()
                            st.success(f"Quarto '{room_type}' adicionado com sucesso!")
                            st.rerun()
                        except sqlite3.Error as e:
                            st.error(f"Erro ao adicionar quarto: {e}")

    with col2:
        st.subheader("Quartos Existentes")
        c.execute("SELECT id, room_type, room_description, price, room_images FROM rooms WHERE hotel_id = ?", (hotel_id,))
        rooms = c.fetchall()

        if rooms:
            for room in rooms:
                room_id, room_type, room_description, price, room_images_json = room
                with st.expander(f"Quarto ID: {room_id} - {room_type}", expanded=False):
                    
                    st.write("Fotos Atuais:")
                    images = []
                    if room_images_json:
                        try:
                            images = json.loads(room_images_json)
                        except json.JSONDecodeError:
                            images = []
                    
                    if images:
                        image_cols = st.columns(len(images))
                        for idx, img_base64 in enumerate(images):
                            with image_cols[idx]:
                                st.image(img_base64, use_container_width=True)
                                # LÓGICA CORRIGIDA: Botão fora do formulário para remover imagens
                                if st.button("Remover", key=f"remove_img_{room_id}_{idx}"):
                                    images.pop(idx)
                                    updated_images_json = json.dumps(images)
                                    c.execute("UPDATE rooms SET room_images = ? WHERE id = ?", (updated_images_json, room_id))
                                    conn.commit()
                                    st.success("Imagem removida com sucesso!")
                                    st.rerun()
                    else:
                        st.info("Nenhuma imagem cadastrada.")

                    st.markdown("---")

                    with st.form(key=f"edit_room_form_{room_id}"):
                        new_room_type = st.text_input("Novo Tipo de Quarto", value=room_type, key=f"new_room_type_{room_id}")
                        new_room_description = st.text_area("Nova Descrição do Quarto", value=room_description, key=f"new_room_description_{room_id}")
                        new_price = st.number_input("Novo Preço por Noite (R$)", min_value=0.0, value=float(price), format="%.2f", key=f"new_price_{room_id}")
                        
                        uploaded_new_images = st.file_uploader(
                            f"Adicionar mais fotos (limite de {photo_limit} fotos no total)",
                            type=["png", "jpg", "jpeg"],
                            accept_multiple_files=True,
                            key=f"add_images_{room_id}"
                        )
                        
                        total_images_after_upload = len(images) + len(uploaded_new_images)
                        
                        col_edit_buttons = st.columns(2)
                        with col_edit_buttons[0]:
                            if st.form_submit_button("Atualizar Quarto"):
                                if total_images_after_upload > photo_limit:
                                    st.error(f"O número total de fotos ({total_images_after_upload}) excede o limite do seu plano ({photo_limit}).")
                                elif new_room_type and new_price > 0:
                                    try:
                                        if uploaded_new_images:
                                            for new_file in uploaded_new_images:
                                                file_bytes = new_file.read()
                                                images.append(f"data:image/{new_file.type.split('/')[-1]};base64,{base64.b64encode(file_bytes).decode()}")
                                        
                                        updated_images_json = json.dumps(images)
                                        
                                        c.execute(
                                            "UPDATE rooms SET room_type = ?, room_description = ?, price = ?, room_images = ? WHERE id = ?",
                                            (new_room_type, new_room_description, new_price, updated_images_json, room_id)
                                        )
                                        conn.commit()
                                        st.success("Quarto atualizado com sucesso!")
                                        st.rerun()
                                    except sqlite3.Error as e:
                                        st.error(f"Erro ao atualizar quarto: {e}")
                                else:
                                    st.error("Por favor, preencha o tipo e o preço do quarto.")
                        with col_edit_buttons[1]:
                             if st.form_submit_button("Remover Quarto"):
                                try:
                                    c.execute("DELETE FROM rooms WHERE id = ?", (room_id,))
                                    conn.commit()
                                    st.success("Quarto removido com sucesso.")
                                    st.rerun()
                                except sqlite3.Error as e:
                                    st.error(f"Erro ao remover quarto: {e}")
        else:
            st.info("Nenhum quarto cadastrado para este hotel.")
        

    st.markdown("---")

    # Atualizar dados do hotel
    st.header("Atualizar Dados do Hotel")
    with st.form("update_hotel_form"):
        st.write(f"**Dados Atuais:**")
        st.write(f"Nome: {hotel_name}")
        st.write(f"E-mail: {hotel_email}")
        st.write(f"Estado: {state}")
        st.write(f"Cidade: {city}")
        st.write(f"Endereço: {address}")
        st.write(f"Telefone: {phone}")
        st.write(f"Site: {website}")
        st.write(f"Plano: {plan_type}")

        st.markdown("---")
        st.write("**Novos Dados:**")
        new_hotel_name = st.text_input("Novo Nome do Hotel", value=hotel_name, key="new_hotel_name")
        new_hotel_email = st.text_input("Novo E-mail para Receber Reservas", value=hotel_email, key="new_hotel_email")
        new_hotel_address = st.text_input("Novo Endereço Completo", value=address, key="new_hotel_address")
        new_hotel_phone = st.text_input("Novo Telefone de Contato", value=phone, key="new_hotel_phone")
        new_hotel_website = st.text_input("Novo Site do Hotel", value=website, key="new_hotel_website")
        new_hotel_state = st.text_input("Novo Estado (Ex: MG)", value=state, key="new_hotel_state")
        new_hotel_city = st.text_input("Nova Cidade (Ex: Belo Horizonte)", value=city, key="new_hotel_city")

        update_submitted = st.form_submit_button("Atualizar Cadastro")
        if update_submitted:
            if new_hotel_name and new_hotel_email and new_hotel_state and new_hotel_city and new_hotel_address and new_hotel_phone:
                try:
                    c.execute(
                        "UPDATE hotels SET hotel_name = ?, hotel_email = ?, state = ?, city = ?, address = ?, phone = ?, website = ? WHERE id = ?",
                        (new_hotel_name, new_hotel_email, new_hotel_state, new_hotel_city, new_hotel_address, new_hotel_phone, new_hotel_website, hotel_id)
                    )
                    conn.commit()
                    st.success("Cadastro do hotel atualizado com sucesso!")
                    st.rerun()
                except sqlite3.Error as e:
                    st.error(f"Erro ao atualizar cadastro: {e}")
            else:
                st.error("Por favor, preencha todos os campos obrigatórios para atualizar o cadastro.")
    conn.close()


def view_reservations():
    hotel_info = get_current_hotel()
    if not hotel_info or hotel_info[2] != 'approved':
        st.error("Seu hotel não está aprovado. Por favor, aguarde a aprovação do administrador.")
        return

    hotel_id, hotel_name, _, hotel_email, _, _, _, _, _, _, _, _ = hotel_info

    st.title("Ver e Gerenciar Reservas")

    conn = sqlite3.connect("quarto_livre.db", detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()

    # Obter reservas pendentes
    c.execute(
        "SELECT r.id, r.room_id, r.guest_name, r.check_in, r.check_out, rm.room_type, rm.price, r.guest_email, r.guest_contact, r.confirmed_by_owner, r.notified_owner FROM reservations r "
        "JOIN rooms rm ON r.room_id = rm.id "
        "WHERE rm.hotel_id = ? AND r.status = 'pending'", (hotel_id,))
    pending_reservations = c.fetchall()
    
    # Obter reservas confirmadas
    c.execute(
        "SELECT r.id, r.room_id, r.guest_name, r.check_in, r.check_out, rm.room_type, r.guest_email, r.guest_contact FROM reservations r "
        "JOIN rooms rm ON r.room_id = rm.id "
        "WHERE rm.hotel_id = ? AND r.status = 'active'", (hotel_id,))
    active_reservations = c.fetchall()

    st.subheader("Reservas Pendentes")
    if pending_reservations:
        for res in pending_reservations:
            res_id, room_id, guest_name, check_in, check_out, room_type, price, guest_email, guest_contact, _, notified_owner = res
            
            # NOVO: Calculando o valor total
            duration = (check_out - check_in).days
            total_price = duration * price
            
            with st.expander(f"ID: {res_id} - Hóspede: {guest_name} ({room_type})", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Datas:** {check_in.strftime('%d/%m/%Y')} - {check_out.strftime('%d/%m/%Y')}")
                    st.write(f"**Quarto:** {room_type}")
                    st.write(f"**E-mail:** {guest_email}")
                with col2:
                    st.write(f"**Contato:** {guest_contact if guest_contact else 'Não informado'}")
                    st.write(f"**Valor Total:** R$ {total_price:.2f}")

                st.markdown("---")
                
                st.info("Sua reserva está pendente. Compartilhe o link de pagamento diretamente com o hóspede e aguarde a confirmação automática.")
                
                payment_link = st.text_input("Cole o link de pagamento aqui e envie para o hóspede.", key=f"payment_link_{res_id}")
                
                col_buttons = st.columns(2)
                with col_buttons[0]:
                    # O botão "Aprovar Reserva" foi removido pois a confirmação é automática via webhook
                    st.write("Aguardando confirmação de pagamento via webhook...")
                
                with col_buttons[1]:
                    if st.button("Rejeitar Reserva", key=f"reject_form_{res_id}"):
                        try:
                            c.execute("UPDATE reservations SET status = 'rejected' WHERE id = ?", (res_id,))
                            conn.commit()
                            st.warning("Reserva rejeitada.")
                            
                            # Enviar e-mail para o hóspede sobre a rejeição
                            subject_guest = f"Atualização sobre sua Reserva no {hotel_name}"
                            body_guest = f"""
                            Olá {guest_name},

                            Infelizmente, a sua reserva para o hotel **{hotel_name}** foi rejeitada.
                            Lamentamos o inconveniente e esperamos que você encontre outra opção adequada.

                            Atenciosamente,
                            Equipe {hotel_name}
                            """
                            if guest_email and send_email(guest_email, subject_guest, body_guest):
                                st.info("E-mail de rejeição enviado ao hóspede.")
                            else:
                                st.warning("Não foi possível enviar o e-mail de rejeição ao hóspede.")
                            
                            st.rerun()
                        except sqlite3.Error as e:
                            st.error(f"Erro ao rejeitar reserva: {e}")

            # Lógica para notificar o dono do hotel
            if not notified_owner and hotel_email:
                play_notification_sound()
                c.execute("UPDATE reservations SET notified_owner = 1 WHERE id = ?", (res_id,))
                conn.commit()
                st.info(f"Você tem uma nova reserva pendente do hóspede {guest_name}. Uma notificação foi enviada para o seu e-mail de contato.")
    else:
        st.info("Nenhuma reserva pendente no momento.")
        
    st.markdown("---")

    st.subheader("Reservas Confirmadas")
    if active_reservations:
        for res in active_reservations:
            res_id, room_id, guest_name, check_in, check_out, room_type, guest_email, guest_contact = res
            
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([1, 2, 2, 2])
                with col1:
                    st.write(f"ID: {res_id}")
                with col2:
                        st.write(f"**Hóspede:** {guest_name}")
                with col3:
                        st.write(f"**Datas:** {check_in.strftime('%d/%m/%Y')} - {check_out.strftime('%d/%m/%Y')}")
                with col4:
                        st.write(f"**Quarto:** {room_type}")
                st.write(f"**E-mail:** {guest_email}")
                st.write(f"**Contato:** {guest_contact if guest_contact else 'Não informado'}")

                if st.button("Cancelar Reserva", key=f"cancel_active_{res_id}", help="Cancela esta reserva e libera as datas.", type="primary"):
                    try:
                        # Limpar datas ocupadas
                        clear_occupied_dates(conn, room_id, check_in, check_out)
                        
                        # Atualizar status da reserva
                        c.execute("UPDATE reservations SET status = 'rejected' WHERE id = ?", (res_id,))
                        conn.commit()
                        st.success(f"Reserva {res_id} cancelada com sucesso!")
                        
                        # Enviar e-mail de cancelamento para o hóspede
                        subject_guest = f"Sua Reserva foi Cancelada - {hotel_name}"
                        body_guest = f"""
                        Olá {guest_name},

                        Informamos que a sua reserva no hotel **{hotel_name}** foi cancelada.
                        
                        Detalhes da reserva:
                        - Hotel: {hotel_name}
                        - Check-in: {check_in.strftime('%d/%m/%Y')}
                        - Check-out: {check_out.strftime('%d/%m/%Y')}
                        - Quarto: {room_type}
                        - Número da Reserva: {res_id}

                        Se precisar de ajuda ou tiver alguma dúvida, por favor, entre em contato com o hotel.

                        Atenciosamente,
                        Equipe {hotel_name}
                        """
                        if guest_email and send_email(guest_email, subject_guest, body_guest):
                            st.info("E-mail de cancelamento enviado ao hóspede.")
                        else:
                            st.warning("Não foi possível enviar o e-mail de cancelamento ao hóspede.")
                            
                        st.rerun()
                    except sqlite3.Error as e:
                        st.error(f"Erro ao cancelar reserva: {e}")

    else:
        st.info("Nenhuma reserva confirmada no momento.")

    conn.close()

def my_calendar():
    hotel_info = get_current_hotel()
    if not hotel_info or hotel_info[2] != 'approved':
        st.error("Seu hotel não está aprovado. Por favor, aguarde a aprovação do administrador.")
        return

    hotel_id, hotel_name, _, _, _, _, _, _, _, _, _, _ = hotel_info
    
    st.title(f"Calendário de Reservas - {hotel_name}")
    
    conn = sqlite3.connect("quarto_livre.db", detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    c.execute(
        "SELECT r.id, r.guest_name, r.check_in, r.check_out, rm.room_type, r.status FROM reservations r "
        "JOIN rooms rm ON r.room_id = rm.id "
        "WHERE rm.hotel_id = ? AND r.status IN ('active', 'pending') AND r.check_out > DATE('now')", (hotel_id,))
    reservations = c.fetchall()
    conn.close()

    events = []
    for res in reservations:
        res_id, guest_name, check_in, check_out, room_type, status = res
        color = "green" if status == "active" else "orange"
        events.append({
            "title": f"Reserva {res_id}: {room_type} - {guest_name}",
            "start": check_in.isoformat(),
            "end": check_out.isoformat(),
            "color": color
        })

    calendar_options = {
        "editable": "false",
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,timeGridDay",
        },
        "initialView": "dayGridMonth",
    }
    
    st_calendar = calendar.st_calendar(events=events, options=calendar_options, key="my_calendar")

def reservation_report():
    hotel_info = get_current_hotel()
    if not hotel_info or hotel_info[2] != 'approved':
        st.error("Seu hotel não está aprovado. Por favor, aguarde a aprovação do administrador.")
        return
    
    hotel_id, hotel_name, _, _, _, _, _, _, _, _, _, _ = hotel_info
    
    st.title("Relatórios de Reservas")
    
    conn = sqlite3.connect("quarto_livre.db", detect_types=sqlite3.PARSE_DECLTYPES)
    df_reservations = pd.read_sql_query(
        "SELECT r.id, r.check_in, r.check_out, r.status, rm.room_type, rm.price FROM reservations r "
        "JOIN rooms rm ON r.room_id = rm.id "
        "WHERE rm.hotel_id = ? AND r.status = 'active'", conn, params=(hotel_id,))
    conn.close()

    if df_reservations.empty:
        st.info("Nenhuma reserva ativa para gerar relatórios.")
        return

    # Convertendo datas e calculando duração
    df_reservations['Check-in'] = pd.to_datetime(df_reservations['check_in'])
    df_reservations['Check-out'] = pd.to_datetime(df_reservations['check_out'])
    df_reservations['Duracao_Noites'] = (df_reservations['Check-out'] - df_reservations['Check-in']).dt.days
    df_reservations['Receita_Total'] = df_reservations['Duracao_Noites'] * df_reservations['price']

    st.markdown("---")
    st.subheader("Análise Mensal de Receita")
    df_reservations['Mes_Ano'] = df_reservations['Check-in'].dt.to_period('M').astype(str)
    monthly_revenue = df_reservations.groupby('Mes_Ano')['Receita_Total'].sum().reset_index()
    fig = px.bar(monthly_revenue, x='Mes_Ano', y='Receita_Total', title="Receita Mensal", labels={'Mes_Ano': 'Mês', 'Receita_Total': 'Receita Total (R$)'})
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.subheader("Distribuição de Reservas por Tipo de Quarto")
    room_distribution = df_reservations['room_type'].value_counts().reset_index()
    room_distribution.columns = ['Tipo de Quarto', 'Número de Reservas']
    fig = px.pie(room_distribution, values='Número de Reservas', names='Tipo de Quarto', title="Distribuição de Reservas por Tipo de Quarto")
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.subheader("Tabela de Dados das Reservas Ativas")
    st.dataframe(df_reservations[['id', 'room_type', 'Check-in', 'Check-out', 'Duracao_Noites', 'Receita_Total']].rename(columns={
        'id': 'ID da Reserva',
        'room_type': 'Tipo de Quarto',
        'Duracao_Noites': 'Noites',
        'Receita_Total': 'Receita Total (R$)'
    }), use_container_width=True)


# --- Lógica de Navegação e Estado da Sessão ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "home"
if "forgot_password" not in st.session_state:
    st.session_state.forgot_password = False

# Layout da página principal
st.image("https://github.com/Quarto-Livre/quarto_livre/blob/main/imagens/logo.png?raw=true", use_container_width=False)

if st.session_state.logged_in:
    # Menu de usuário logado
    st.markdown('<div class="top-menu-buttons">', unsafe_allow_html=True)
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    with col1:
        st.write(f"Bem-vindo(a), **{st.session_state.username}**!")
    with col5:
        if st.button("Sair", key="logout_btn", use_container_width=False):
            logout()
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")

    if st.session_state.user_role == 'admin':
        if st.button("Painel de Administração", use_container_width=True):
            st.session_state.page = "admin_dashboard"
        
    if st.session_state.user_role == 'owner':
        hotel_info = get_current_hotel()
        # Verificar o status do hotel antes de renderizar o menu
        if hotel_info and (hotel_info[2] == 'pending' or hotel_info[2] == 'expired'):
             if st.button("Gerenciar Hotel", use_container_width=True):
                st.session_state.page = "owner_dashboard"
        elif hotel_info:
            col_owner_nav = st.columns(4)
            with col_owner_nav[0]:
                if st.button("Gerenciar Hotel", use_container_width=True):
                    st.session_state.page = "owner_dashboard"
            with col_owner_nav[1]:
                if st.button("Ver Reservas", use_container_width=True):
                    st.session_state.page = "view_reservations"
            with col_owner_nav[2]:
                if st.button("Calendário de Reservas", use_container_width=True):
                    st.session_state.page = "my_calendar"
            with col_owner_nav[3]:
                if st.button("Relatórios", use_container_width=True):
                    st.session_state.page = "reservation_report"
            
            # Contagem de reservas pendentes
            try:
                conn_sidebar = sqlite3.connect("quarto_livre.db", detect_types=sqlite3.PARSE_DECLTYPES)
                c_sidebar = conn_sidebar.cursor()
                c_sidebar.execute(
                    "SELECT COUNT(*) FROM reservations r JOIN rooms rm ON r.room_id = rm.id WHERE rm.hotel_id = ? AND r.status = 'pending'",
                    (hotel_info[0],)
                )
                pending_count = c_sidebar.fetchone()[0]
                conn_sidebar.close()
                
                if pending_count > 0:
                    st.info(f"Você tem {pending_count} reserva(s) pendente(s).")
                    play_notification_sound()
            except Exception as e:
                st.error(f"Erro ao contar reservas: {e}")

else:
    # Menu de usuário não logado
    st.markdown('<div class="top-menu-buttons">', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Entrar", key="login_nav_btn", use_container_width=False):
            st.session_state.page = "login"
    with col2:
        if st.button("Cadastrar Hotel", key="register_nav_btn", use_container_width=False):
            st.session_state.page = "register"
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")

if st.session_state.page == "home":
    guest_reservation_page()
elif st.session_state.page == "login":
    if st.session_state.get("forgot_password", False):
        reset_password()
    else:
        login()
elif st.session_state.page == "register":
    register_hotel_owner()
elif st.session_state.page == "admin_dashboard" and st.session_state.logged_in and st.session_state.user_role == "admin":
    admin_dashboard()
elif st.session_state.page == "owner_dashboard" and st.session_state.logged_in and st.session_state.user_role == "owner":
    owner_dashboard()
elif st.session_state.page == "view_reservations" and st.session_state.logged_in and st.session_state.user_role == "owner":
    view_reservations()
elif st.session_state.page == "my_calendar" and st.session_state.logged_in and st.session_state.user_role == "owner":
    my_calendar()
elif st.session_state.page == "reservation_report" and st.session_state.logged_in and st.session_state.user_role == "owner":
    reservation_report()
else:
    st.session_state.page = "home"

    st.rerun()
