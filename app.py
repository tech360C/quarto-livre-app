# Arquivo: quarto_livre.py
import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, timedelta
import bcrypt
import smtplib
from email.mime.text import MIMEText
import streamlit_calendar as calendar
import plotly.express as px
import requests

# URL DO BACKEND: Esta URL será fornecida pelo Render depois
# Por enquanto, pode deixar assim.
BACKEND_URL = "https://seu-backend-aqui.onrender.com"

# --- CONFIGURAÇÃO E FUNÇÕES DE BANCO DE DADOS E E-MAIL ---
# NOTA: Estas funções foram movidas para o backend.py
# A lógica aqui no frontend serve apenas para leitura e exibição.

# Configuração de e-mail (necessária para envio de alguns e-mails)
EMAIL_SENDER = "quartolivre.reservas@gmail.com"
EMAIL_PASSWORD = "pkawwfdpxdnsyupo"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
ADMIN_EMAIL = "quartolivre.reservas@gmail.com"

def send_email(recipient_email, subject, body):
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        st.error("Configuração de e-mail ausente ou incompleta. Verifique as variáveis de ambiente.")
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
        st.success(f"E-mail enviado com sucesso para {recipient_email}!")
        return True
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao enviar o e-mail: {e}")
        return False

def init_db():
    conn = sqlite3.connect("quarto_livre.db", detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS hotels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            hotel_name TEXT NOT NULL,
            hotel_address TEXT,
            hotel_email TEXT NOT NULL,
            hotel_phone TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hotel_id INTEGER,
            room_type TEXT NOT NULL,
            capacity INTEGER,
            price_per_night REAL,
            description TEXT,
            image_url TEXT,
            FOREIGN KEY (hotel_id) REFERENCES hotels (id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER,
            guest_name TEXT NOT NULL,
            check_in DATE NOT NULL,
            check_out DATE NOT NULL,
            guest_email TEXT NOT NULL,
            guest_contact TEXT,
            status TEXT NOT NULL,
            FOREIGN KEY (room_id) REFERENCES rooms (id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS site_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_key TEXT UNIQUE NOT NULL,
            config_value TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS upgrade_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            company_name TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def login_user(username, password):
    conn = sqlite3.connect("quarto_livre.db")
    c = conn.cursor()
    c.execute("SELECT password_hash, role FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    if result and bcrypt.checkpw(password.encode('utf-8'), result[0]):
        return result[1]
    return None

def register_user(username, password):
    conn = sqlite3.connect("quarto_livre.db")
    c = conn.cursor()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    try:
        c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", (username, password_hash, 'guest'))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def get_hotel_id(username):
    conn = sqlite3.connect("quarto_livre.db")
    c = conn.cursor()
    c.execute("SELECT h.id FROM hotels h JOIN users u ON h.user_id = u.id WHERE u.username = ?", (username,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def get_rooms(hotel_id):
    conn = sqlite3.connect("quarto_livre.db", detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    c.execute("SELECT id, room_type, capacity, price_per_night, description, image_url FROM rooms WHERE hotel_id = ?", (hotel_id,))
    rooms = c.fetchall()
    conn.close()
    return rooms

def is_room_available(room_id, check_in, check_out):
    conn = sqlite3.connect("quarto_livre.db", detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    c.execute("""
        SELECT COUNT(*) FROM reservations
        WHERE room_id = ?
        AND status = 'active'
        AND NOT (check_out <= ? OR check_in >= ?)
    """, (room_id, check_in, check_out))
    count = c.fetchone()[0]
    conn.close()
    return count == 0

def get_available_rooms(check_in, check_out):
    conn = sqlite3.connect("quarto_livre.db", detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    c.execute("""
        SELECT
            r.id, r.room_type, r.capacity, r.price_per_night, r.description, r.image_url, h.hotel_name
        FROM rooms r
        JOIN hotels h ON r.hotel_id = h.id
        WHERE r.id NOT IN (
            SELECT room_id FROM reservations
            WHERE status = 'active'
            AND NOT (check_out <= ? OR check_in >= ?)
        )
    """, (check_in, check_out))
    rooms = c.fetchall()
    conn.close()
    return rooms

def get_hotel_name_by_id(hotel_id):
    conn = sqlite3.connect("quarto_livre.db")
    c = conn.cursor()
    c.execute("SELECT hotel_name FROM hotels WHERE id = ?", (hotel_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def get_hotel_info_by_room_id(room_id):
    conn = sqlite3.connect("quarto_livre.db")
    c = conn.cursor()
    c.execute("SELECT h.hotel_name, h.hotel_address, h.hotel_email FROM hotels h JOIN rooms r ON h.id = r.hotel_id WHERE r.id = ?", (room_id,))
    result = c.fetchone()
    conn.close()
    return result if result else (None, None, None)

def get_hotel_reservations(hotel_id):
    conn = sqlite3.connect("quarto_livre.db", detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    c.execute("""
        SELECT res.id, res.guest_name, res.check_in, res.check_out, res.status, res.guest_email, res.guest_contact, r.room_type
        FROM reservations res
        JOIN rooms r ON res.room_id = r.id
        WHERE r.hotel_id = ?
        ORDER BY res.check_in DESC
    """, (hotel_id,))
    reservations = c.fetchall()
    conn.close()
    return reservations

def update_reservation_status(res_id, new_status):
    conn = sqlite3.connect("quarto_livre.db")
    c = conn.cursor()
    c.execute("UPDATE reservations SET status = ? WHERE id = ?", (new_status, res_id))
    conn.commit()
    conn.close()

def delete_room(room_id):
    conn = sqlite3.connect("quarto_livre.db")
    c = conn.cursor()
    try:
        c.execute("DELETE FROM rooms WHERE id = ?", (room_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Erro ao deletar o quarto: {e}")
        return False
    finally:
        conn.close()

def update_room(room_id, room_type, capacity, price_per_night, description, image_url):
    conn = sqlite3.connect("quarto_livre.db")
    c = conn.cursor()
    try:
        c.execute("""
            UPDATE rooms
            SET room_type = ?, capacity = ?, price_per_night = ?, description = ?, image_url = ?
            WHERE id = ?
        """, (room_type, capacity, price_per_night, description, image_url, room_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Erro ao atualizar o quarto: {e}")
        return False
    finally:
        conn.close()

def get_reservation_details(reservation_id):
    conn = sqlite3.connect("quarto_livre.db", detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    c.execute("""
        SELECT res.id, res.guest_name, res.check_in, res.check_out, res.status, res.guest_email, res.guest_contact, r.room_type, h.hotel_name
        FROM reservations res
        JOIN rooms r ON res.room_id = r.id
        JOIN hotels h ON r.hotel_id = h.id
        WHERE res.id = ?
    """, (reservation_id,))
    reservation = c.fetchone()
    conn.close()
    return reservation

def add_room(hotel_id, room_type, capacity, price_per_night, description, image_url):
    conn = sqlite3.connect("quarto_livre.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO rooms (hotel_id, room_type, capacity, price_per_night, description, image_url) VALUES (?, ?, ?, ?, ?, ?)",
                  (hotel_id, room_type, capacity, price_per_night, description, image_url))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Erro ao adicionar quarto: {e}")
        return False
    finally:
        conn.close()

def add_hotel(user_id, hotel_name, hotel_address, hotel_email, hotel_phone):
    conn = sqlite3.connect("quarto_livre.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO hotels (user_id, hotel_name, hotel_address, hotel_email, hotel_phone) VALUES (?, ?, ?, ?, ?)",
                  (user_id, hotel_name, hotel_address, hotel_email, hotel_phone))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Erro ao adicionar hotel: {e}")
        return False
    finally:
        conn.close()

def get_user_info(username):
    conn = sqlite3.connect("quarto_livre.db")
    c = conn.cursor()
    c.execute("SELECT id, role FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    return result if result else (None, None)

def request_upgrade(username, email, company_name):
    conn = sqlite3.connect("quarto_livre.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO upgrade_requests (username, email, company_name, status) VALUES (?, ?, ?, ?)",
                  (username, email, company_name, 'pending'))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Erro ao solicitar upgrade: {e}")
        return False
    finally:
        conn.close()

def get_upgrade_requests():
    conn = sqlite3.connect("quarto_livre.db")
    c = conn.cursor()
    c.execute("SELECT id, username, email, company_name, status FROM upgrade_requests WHERE status = 'pending'")
    requests = c.fetchall()
    conn.close()
    return requests

def update_user_role(username, new_role):
    conn = sqlite3.connect("quarto_livre.db")
    c = conn.cursor()
    try:
        c.execute("UPDATE users SET role = ? WHERE username = ?", (new_role, username))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Erro ao atualizar o papel do usuário: {e}")
        return False
    finally:
        conn.close()

def update_request_status(request_id, new_status):
    conn = sqlite3.connect("quarto_livre.db")
    c = conn.cursor()
    try:
        c.execute("UPDATE upgrade_requests SET status = ? WHERE id = ?", (new_status, request_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Erro ao atualizar o status da solicitação: {e}")
        return False
    finally:
        conn.close()

def get_all_hotels_info():
    conn = sqlite3.connect("quarto_livre.db")
    c = conn.cursor()
    c.execute("SELECT id, hotel_name, hotel_address, hotel_email, hotel_phone FROM hotels")
    hotels = c.fetchall()
    conn.close()
    return hotels

def hotel_registration_form():
    st.subheader("Cadastro de Hotel")
    st.info("Para usar o sistema, primeiro cadastre seu hotel.")
    with st.form("hotel_form"):
        hotel_name = st.text_input("Nome do Hotel")
        hotel_address = st.text_input("Endereço do Hotel")
        hotel_email = st.text_input("E-mail do Hotel")
        hotel_phone = st.text_input("Telefone do Hotel")
        submitted = st.form_submit_button("Cadastrar Hotel")
        if submitted:
            if hotel_name and hotel_email:
                user_id, _ = get_user_info(st.session_state.username)
                if add_hotel(user_id, hotel_name, hotel_address, hotel_email, hotel_phone):
                    st.success("Hotel cadastrado com sucesso!")
                    st.session_state.hotel_id = get_hotel_id(st.session_state.username)
                    st.rerun()
                else:
                    st.error("Erro ao cadastrar hotel. Tente novamente.")
            else:
                st.warning("Nome e e-mail do hotel são obrigatórios.")

def room_management_section():
    st.subheader("Gerenciamento de Quartos")
    hotel_id = st.session_state.hotel_id
    rooms = get_rooms(hotel_id)

    st.write("### Adicionar Novo Quarto")
    with st.form("add_room_form"):
        room_type = st.text_input("Tipo do Quarto")
        capacity = st.number_input("Capacidade", min_value=1, step=1)
        price_per_night = st.number_input("Preço por Noite", min_value=0.01, step=0.01)
        description = st.text_area("Descrição")
        image_url = st.text_input("URL da Imagem")
        submitted = st.form_submit_button("Adicionar Quarto")
        if submitted:
            if room_type and capacity and price_per_night:
                if add_room(hotel_id, room_type, capacity, price_per_night, description, image_url):
                    st.success("Quarto adicionado com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao adicionar quarto.")
            else:
                st.warning("Por favor, preencha todos os campos obrigatórios.")

    if rooms:
        st.write("### Quartos Cadastrados")
        for room in rooms:
            room_id, room_type, capacity, price_per_night, description, image_url = room
            with st.expander(f"Quarto: {room_type} (ID: {room_id})", expanded=True):
                col1, col2 = st.columns([1, 2])
                with col1:
                    if image_url:
                        st.image(image_url, width=150)
                with col2:
                    st.write(f"**Tipo:** {room_type}")
                    st.write(f"**Capacidade:** {capacity} pessoas")
                    st.write(f"**Preço:** R${price_per_night:.2f} por noite")
                    st.write(f"**Descrição:** {description}")
                    st.write(f"**URL da Imagem:** {image_url}")

                edit_mode = st.button(f"Editar Quarto {room_id}", key=f"edit_btn_{room_id}")
                if edit_mode:
                    st.session_state.edit_room_id = room_id
                    st.session_state.edit_room_type = room_type
                    st.session_state.edit_room_capacity = capacity
                    st.session_state.edit_room_price = price_per_night
                    st.session_state.edit_room_description = description
                    st.session_state.edit_room_image = image_url
                    st.rerun()

                if st.button(f"Deletar Quarto {room_id}", key=f"delete_btn_{room_id}"):
                    if delete_room(room_id):
                        st.success("Quarto deletado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro ao deletar quarto.")

def edit_room_form():
    st.subheader("Editar Quarto")
    with st.form("edit_room_form_details"):
        room_type = st.text_input("Tipo do Quarto", value=st.session_state.edit_room_type)
        capacity = st.number_input("Capacidade", min_value=1, step=1, value=st.session_state.edit_room_capacity)
        price_per_night = st.number_input("Preço por Noite", min_value=0.01, step=0.01, value=st.session_state.edit_room_price)
        description = st.text_area("Descrição", value=st.session_state.edit_room_description)
        image_url = st.text_input("URL da Imagem", value=st.session_state.edit_room_image)
        submitted = st.form_submit_button("Salvar Alterações")
        if submitted:
            if update_room(st.session_state.edit_room_id, room_type, capacity, price_per_night, description, image_url):
                st.success("Quarto atualizado com sucesso!")
                del st.session_state.edit_room_id
                st.rerun()
            else:
                st.error("Erro ao atualizar quarto.")

def view_reservations():
    st.subheader("Gerenciamento de Reservas")
    hotel_id = st.session_state.hotel_id
    reservations = get_hotel_reservations(hotel_id)
    df = pd.DataFrame(reservations, columns=['ID', 'Hóspede', 'Check-in', 'Check-out', 'Status', 'E-mail', 'Contato', 'Quarto'])

    if df.empty:
        st.info("Nenhuma reserva encontrada.")
        return

    st.write("### Todas as Reservas")
    st.dataframe(df)

    st.write("---")
    st.write("### Reservas Pendentes")
    pending_reservations = df[df['Status'] == 'pending']
    if pending_reservations.empty:
        st.info("Nenhuma reserva pendente.")
    else:
        for index, res in pending_reservations.iterrows():
            res_id, guest_name, check_in, check_out, status, guest_email, guest_contact, room_type = res
            with st.expander(f"ID: {res_id} - Hóspede: {guest_name} ({room_type})", expanded=True):
                st.write(f"**ID da Reserva:** {res_id}")
                st.write(f"**Quarto:** {room_type}")
                st.write(f"**Datas:** {check_in.strftime('%d/%m/%Y')} a {check_out.strftime('%d/%m/%Y')}")
                st.write(f"**Hóspede:** {guest_name}")
                st.write(f"**E-mail:** {guest_email}")
                st.write(f"**Contato:** {guest_contact if guest_contact else 'Não informado'}")

                st.info("O hóspede precisa de um link de pagamento. Depois de recebê-lo, cole o link aqui.")
                payment_link = st.text_input("Cole o link de pagamento aqui:", key=f"payment_link_{res_id}")
                
                # Botão para enviar o link
                if st.button("Enviar Link de Pagamento", key=f"send_link_{res_id}"):
                    if payment_link:
                        # Envia e-mail para o hóspede com o link de pagamento
                        subject_guest = f"Link de Pagamento para sua reserva no hotel {get_hotel_name_by_id(hotel_id)}"
                        body_guest = f"""
                        Olá {guest_name},
                        Agradecemos por sua reserva.
                        Por favor, use o link abaixo para concluir o seu pagamento e confirmar sua estadia:
                        <br><br>
                        <a href="{payment_link}">Clique aqui para pagar sua reserva</a>
                        <br><br>
                        Seu ID de reserva é **{res_id}**.
                        """
                        if send_email(guest_email, subject_guest, body_guest):
                            st.success(f"Link de pagamento enviado para {guest_email}!")
                        else:
                            st.error(f"Erro ao enviar o e-mail para {guest_email}.")
                    else:
                        st.warning("Por favor, insira o link de pagamento antes de enviar.")

                if st.button("Rejeitar Reserva", key=f"reject_btn_{res_id}"):
                    update_reservation_status(res_id, 'rejected')
                    st.success(f"Reserva {res_id} rejeitada com sucesso!")
                    st.rerun()

    st.write("---")
    st.write("### Reservas Confirmadas")
    confirmed_reservations = df[df['Status'] == 'active']
    if confirmed_reservations.empty:
        st.info("Nenhuma reserva confirmada.")
    else:
        for index, res in confirmed_reservations.iterrows():
            res_id, guest_name, check_in, check_out, status, guest_email, guest_contact, room_type = res
            with st.expander(f"ID: {res_id} - Hóspede: {guest_name} ({room_type})", expanded=False):
                st.write(f"**ID da Reserva:** {res_id}")
                st.write(f"**Quarto:** {room_type}")
                st.write(f"**Datas:** {check_in.strftime('%d/%m/%Y')} a {check_out.strftime('%d/%m/%Y')}")
                st.write(f"**Hóspede:** {guest_name}")
                st.write(f"**E-mail:** {guest_email}")
                st.write(f"**Contato:** {guest_contact if guest_contact else 'Não informado'}")


def view_calendar():
    st.subheader("Calendário de Reservas")
    hotel_id = st.session_state.hotel_id
    reservations = get_hotel_reservations(hotel_id)
    if not reservations:
        st.info("Nenhuma reserva para exibir no calendário.")
        return

    events = []
    for res in reservations:
        res_id, guest_name, check_in, check_out, status, _, _, room_type = res
        color = '#3873C8' if status == 'active' else '#FF4B4B'
        events.append({
            "title": f"{room_type} - {guest_name}",
            "start": check_in.strftime('%Y-%m-%d'),
            "end": (check_out + timedelta(days=1)).strftime('%Y-%m-%d'),
            "color": color,
            "id": str(res_id)
        })

    calendar_options = {
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,timeGridDay",
        },
        "initialView": "dayGridMonth",
        "locale": "pt-br",
        "editable": False,
    }
    calendar_events = calendar.st_calendar(events=events, options=calendar_options, key='calendar')

    if calendar_events and calendar_events['eventClick']:
        event_id = calendar_events['eventClick']['event']['id']
        reservation = get_reservation_details(int(event_id))
        if reservation:
            res_id, guest_name, check_in, check_out, status, guest_email, guest_contact, room_type, hotel_name = reservation
            st.sidebar.markdown("---")
            st.sidebar.subheader("Detalhes da Reserva")
            st.sidebar.write(f"**ID:** {res_id}")
            st.sidebar.write(f"**Hóspede:** {guest_name}")
            st.sidebar.write(f"**Quarto:** {room_type}")
            st.sidebar.write(f"**Datas:** {check_in.strftime('%d/%m/%Y')} a {check_out.strftime('%d/%m/%Y')}")
            st.sidebar.write(f"**Status:** {status}")

def room_occupancy_chart():
    st.subheader("Gráfico de Ocupação dos Quartos")
    hotel_id = st.session_state.hotel_id
    reservations = get_hotel_reservations(hotel_id)
    df = pd.DataFrame(reservations, columns=['ID', 'Hóspede', 'Check-in', 'Check-out', 'Status', 'E-mail', 'Contato', 'Quarto'])

    if df.empty or df[df['Status'] == 'active'].empty:
        st.info("Nenhuma reserva confirmada para gerar o gráfico de ocupação.")
        return

    confirmed_reservations = df[df['Status'] == 'active'].copy()
    confirmed_reservations['Check-in'] = pd.to_datetime(confirmed_reservations['Check-in'])
    confirmed_reservations['Check-out'] = pd.to_datetime(confirmed_reservations['Check-out'])

    confirmed_reservations['duration'] = (confirmed_reservations['Check-out'] - confirmed_reservations['Check-in']).dt.days
    confirmed_reservations = confirmed_reservations.sort_values(by='Check-in')

    fig = px.timeline(confirmed_reservations,
                      x_start="Check-in",
                      x_end="Check-out",
                      y="Quarto",
                      color="Hóspede",
                      title="Ocupação dos Quartos por Período")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

def user_dashboard():
    st.title("Área do Hóspede")
    st.subheader(f"Bem-vindo(a), {st.session_state.username}!")

    st.write("---")
    st.subheader("Buscar Quartos para Reserva")
    with st.form("search_form"):
        col1, col2 = st.columns(2)
        with col1:
            check_in_date = st.date_input("Data de Check-in", value=date.today())
        with col2:
            check_out_date = st.date_input("Data de Check-out", value=date.today() + timedelta(days=1))
        submitted = st.form_submit_button("Buscar Quartos")
        if submitted:
            if check_in_date >= check_out_date:
                st.error("A data de Check-out deve ser posterior à data de Check-in.")
            elif check_in_date < date.today():
                st.error("A data de Check-in não pode ser no passado.")
            else:
                st.session_state.search_results = get_available_rooms(check_in_date, check_out_date)
                st.session_state.booking_check_in = check_in_date
                st.session_state.booking_check_out = check_out_date
                st.session_state.show_booking_form = False

    if 'search_results' in st.session_state and st.session_state.search_results:
        st.write("---")
        st.subheader("Quartos Disponíveis")
        for room in st.session_state.search_results:
            room_id, room_type, capacity, price_per_night, description, image_url, hotel_name = room
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(image_url, width=150)
            with col2:
                st.write(f"**{hotel_name}**")
                st.write(f"**Quarto:** {room_type}")
                st.write(f"**Capacidade:** {capacity} pessoas")
                st.write(f"**Preço:** R${price_per_night:.2f} por noite")
                st.write(f"**Descrição:** {description}")
                if st.button("Reservar", key=f"book_btn_{room_id}"):
                    st.session_state.show_booking_form = True
                    st.session_state.selected_room_id = room_id
                    st.session_state.selected_room_for_booking = room_id
                    st.session_state.selected_room_type = room_type
                    st.session_state.selected_hotel_name = hotel_name
                    st.rerun()
    elif 'search_results' in st.session_state and not st.session_state.search_results:
        st.warning("Nenhum quarto disponível para as datas selecionadas.")

def guest_reservation():
    st.subheader(f"Finalizar Reserva para o hotel {st.session_state.selected_hotel_name}")
    st.write(f"**Quarto Selecionado:** {st.session_state.selected_room_type}")
    st.write(f"**Datas:** {st.session_state.booking_check_in.strftime('%d/%m/%Y')} a {st.session_state.booking_check_out.strftime('%d/%m/%Y')}")

    with st.form("guest_form"):
        guest_name_final = st.text_input("Seu nome completo")
        guest_email_final = st.text_input("Seu e-mail")
        guest_contact_final = st.text_input("Seu telefone de contato (opcional)")
        
        # NOVO CÓDIGO AQUI
        if st.button("Confirmar Reserva Final", key="final_reservation_btn"):
            if guest_name_final and guest_email_final:
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
                st.session_state.show_booking_form = False
                st.session_state.booking_check_in = None
                st.session_state.booking_check_out = None
                st.session_state.selected_room_for_booking = None
                st.rerun()
            else:
                st.warning("Nome e e-mail são obrigatórios.")

# --- PÁGINA PRINCIPAL E LÓGICA DE NAVEGAÇÃO ---
st.set_page_config(layout="wide")
init_db()

if 'username' not in st.session_state:
    st.session_state.username = None
if 'role' not in st.session_state:
    st.session_state.role = None
if 'hotel_id' not in st.session_state:
    st.session_state.hotel_id = None
if 'edit_room_id' not in st.session_state:
    st.session_state.edit_room_id = None
if 'show_booking_form' not in st.session_state:
    st.session_state.show_booking_form = False

def main_page():
    st.title("Quarto Livre")
    st.header("Seu sistema de reservas para hotéis")
    if st.session_state.show_booking_form:
        guest_reservation()
    else:
        user_dashboard()

if st.session_state.username:
    st.sidebar.title("Bem-vindo(a)!")
    st.sidebar.write(f"Usuário: **{st.session_state.username}**")
    st.sidebar.write(f"Função: **{st.session_state.role}**")
    if st.sidebar.button("Logout"):
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()

    menu = ["Início"]
    if st.session_state.role == 'hotel_owner':
        if not st.session_state.hotel_id:
            hotel_id = get_hotel_id(st.session_state.username)
            if hotel_id:
                st.session_state.hotel_id = hotel_id
            else:
                hotel_registration_form()
                menu = []
        if 'edit_room_id' in st.session_state and st.session_state.edit_room_id:
            edit_room_form()
            menu = []
        else:
            menu.extend(["Gerenciar Quartos", "Ver Reservas", "Calendário", "Ocupação Gráfica"])
    elif st.session_state.role == 'admin':
        menu.extend(["Gerenciar Upgrade", "Ver Todos os Hotéis"])
    
    if menu:
        choice = st.sidebar.selectbox("Menu", menu)

        if choice == "Início":
            main_page()
        elif choice == "Gerenciar Quartos":
            room_management_section()
        elif choice == "Ver Reservas":
            view_reservations()
        elif choice == "Calendário":
            view_calendar()
        elif choice == "Ocupação Gráfica":
            room_occupancy_chart()
        elif choice == "Gerenciar Upgrade":
            st.subheader("Gerenciar Solicitações de Upgrade")
            requests = get_upgrade_requests()
            if not requests:
                st.info("Nenhuma solicitação de upgrade pendente.")
            else:
                for req_id, username, email, company_name, status in requests:
                    with st.expander(f"Solicitação ID: {req_id} - {username}"):
                        st.write(f"**Usuário:** {username}")
                        st.write(f"**E-mail:** {email}")
                        st.write(f"**Empresa:** {company_name}")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Aprovar", key=f"approve_{req_id}"):
                                update_user_role(username, 'hotel_owner')
                                update_request_status(req_id, 'approved')
                                st.success("Solicitação aprovada e usuário atualizado para 'hotel_owner'!")
                                st.rerun()
                        with col2:
                            if st.button("Rejeitar", key=f"reject_{req_id}"):
                                update_request_status(req_id, 'rejected')
                                st.warning("Solicitação rejeitada.")
                                st.rerun()
        elif choice == "Ver Todos os Hotéis":
            st.subheader("Todos os Hotéis Cadastrados")
            hotels = get_all_hotels_info()
            df_hotels = pd.DataFrame(hotels, columns=['ID', 'Nome do Hotel', 'Endereço', 'E-mail', 'Telefone'])
            st.dataframe(df_hotels)
else:
    st.sidebar.title("Login / Registro")
    if 'show_register' not in st.session_state:
        st.session_state.show_register = False

    if st.session_state.show_register:
        st.subheader("Registro de Novo Usuário")
        with st.form("register_form"):
            new_username = st.text_input("Nome de Usuário")
            new_password = st.text_input("Senha", type="password")
            confirm_password = st.text_input("Confirmar Senha", type="password")
            if st.form_submit_button("Registrar"):
                if new_password == confirm_password and len(new_password) > 0:
                    if register_user(new_username, new_password):
                        st.success("Usuário registrado com sucesso! Faça o login.")
                        st.session_state.show_register = False
                        st.rerun()
                    else:
                        st.error("Nome de usuário já existe.")
                else:
                    st.error("As senhas não coincidem ou estão vazias.")
        if st.button("Já tenho uma conta"):
            st.session_state.show_register = False
            st.rerun()
    else:
        st.subheader("Login")
        with st.form("login_form"):
            username = st.text_input("Nome de Usuário")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar")
            if submitted:
                role = login_user(username, password)
                if role:
                    st.session_state.username = username
                    st.session_state.role = role
                    st.session_state.hotel_id = get_hotel_id(username) if role == 'hotel_owner' else None
                    st.success(f"Login bem-sucedido! Bem-vindo, {username}!")
                    st.rerun()
                else:
                    st.error("Nome de usuário ou senha incorretos.")
        if st.button("Não tenho uma conta"):
            st.session_state.show_register = True
            st.rerun()

    st.write("---")
    main_page()