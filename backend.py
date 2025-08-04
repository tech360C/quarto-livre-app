# Arquivo: backend.py
import os
import sqlite3
from flask import Flask, request, jsonify
from datetime import datetime, date, timedelta
import json
import smtplib
from email.mime.text import MIMEText
import requests

# Inicializa o Flask para criar a API
app = Flask(__name__)

# --- CONFIGURAÇÃO DE E-MAIL ---
# ATENÇÃO: Substitua pelos seus dados de e-mail
EMAIL_SENDER = "quartolivre.reservas@gmail.com"
EMAIL_PASSWORD = "pkawwfdpxdnsyupo"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
ADMIN_EMAIL = "quartolivre.reservas@gmail.com"

# --- FUNÇÃO DE E-MAIL ---
def send_email(recipient_email, subject, body):
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        print("Configuração de e-mail ausente ou incompleta.")
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
    except Exception as e:
        print(f"Ocorreu um erro inesperado ao enviar o e-mail: {e}")
        return False

# --- FUNÇÃO DE INICIALIZAÇÃO DO BANCO DE DADOS ---
# Certifique-se de que esta função reflete todas as suas tabelas e colunas!
def init_db():
    conn = None
    try:
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
    except sqlite3.Error as e:
        print(f"Erro ao inicializar o banco de dados no backend: {e}")
    finally:
        if conn:
            conn.close()

# Chame a função para garantir que o DB existe ao iniciar o backend
init_db()

# --- ENDPOINT 1: RECEBER NOVA RESERVA DO STREAMLIT ---
@app.route('/api/create_reservation', methods=['POST'])
def create_reservation():
    try:
        data = request.json
        room_id = data.get('room_id')
        guest_name = data.get('guest_name')
        check_in = datetime.strptime(data.get('check_in'), '%Y-%m-%d').date()
        check_out = datetime.strptime(data.get('check_out'), '%Y-%m-%d').date()
        guest_email = data.get('guest_email')
        guest_contact = data.get('guest_contact')

        conn = sqlite3.connect("quarto_livre.db", detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()

        c.execute(
            "INSERT INTO reservations (room_id, guest_name, check_in, check_out, guest_email, guest_contact, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (room_id, guest_name, check_in, check_out, guest_email, guest_contact, 'pending')
        )
        reservation_id = c.lastrowid

        c.execute("SELECT h.hotel_email, h.hotel_name FROM hotels h JOIN rooms rm ON h.id = rm.hotel_id WHERE rm.id = ?", (room_id,))
        result = c.fetchone()
        hotel_email, hotel_name_booking = result if result else (None, None)
        conn.close()

        if hotel_email:
            subject_owner = f"Nova Reserva Pendente - {hotel_name_booking}"
            body_owner = f"""
            Olá,
            Uma nova reserva foi solicitada para o seu hotel **{hotel_name_booking}**.
            - Hóspede: {guest_name}
            - ID da Reserva: **{reservation_id}**
            - E-mail do Hóspede: {guest_email}
            - Contato do Hóspede: {guest_contact if guest_contact else 'Não informado'}
            - Check-in: {check_in.strftime('%d/%m/%Y')}
            - Check-out: {check_out.strftime('%d/%m/%Y')}
            <br>
            Acesse o painel do hotel para gerar o link de pagamento.
            """
            send_email(hotel_email, subject_owner, body_owner)

        return jsonify({"message": "Reserva criada com sucesso.", "reservation_id": reservation_id}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# --- ENDPOINT 2: RECEBER O WEBHOOK ---
@app.route('/api/payment_webhook', methods=['POST'])
def handle_payment_webhook():
    try:
        data = request.json
        print("Webhook recebido:", data)

        # LÓGICA DE EXEMPLO! Você precisa adaptá-la para a sua plataforma (Mercado Pago, PagSeguro, etc.)
        payment_status = data.get('status')
        reservation_id = data.get('external_reference')

        if payment_status == "approved" and reservation_id:
            conn = sqlite3.connect("quarto_livre.db", detect_types=sqlite3.PARSE_DECLTYPES)
            c = conn.cursor()

            c.execute("UPDATE reservations SET status = 'active' WHERE id = ?", (reservation_id,))
            conn.commit()

            # TODO: Enviar e-mail de confirmação FINAL para o hóspede
            # Busque os dados da reserva no banco para montar o e-mail
            # c.execute("SELECT ... FROM reservations WHERE id = ?", (reservation_id,))
            # ...
            
            conn.close()
            return jsonify({"message": "Reserva confirmada com sucesso."}), 200
        else:
            return jsonify({"message": "Webhook recebido, mas status não é de aprovação."}), 200

    except Exception as e:
        print(f"Erro no webhook: {e}")
        return jsonify({"error": str(e)}), 400

# Endpoint de saúde para o Render
@app.route('/')
def health_check():
    return 'Backend is running!', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)