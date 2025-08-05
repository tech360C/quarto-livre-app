# Arquivo: backend.py
# Este é o novo arquivo para o "motor" do seu sistema (a API Flask)

# Importa as bibliotecas necessárias
import os
import sqlite3
from flask import Flask, request, jsonify
from datetime import datetime, date, timedelta
import json
import smtplib
from email.mime.text import MIMEText
import bcrypt # Para hash de senhas, se necessário no backend

# Inicializa o Flask para criar a API
app = Flask(__name__)

# --- CONFIGURAÇÃO DE E-MAIL (ATENÇÃO: SUBSTITUA PELOS SEUS DADOS REAIS) ---
EMAIL_SENDER = "quartolivre.reservas@gmail.com" # Seu e-mail remetente
EMAIL_PASSWORD = "pkawwfdpxdnsyupo" # Sua senha de aplicativo do Google
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
ADMIN_EMAIL = "quartolivre.reservas@gmail.com" # E-mail do administrador para notificações

# --- FUNÇÃO DE E-MAIL ---
def send_email(recipient_email, subject, body):
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        print("Configuração de e-mail ausente ou incompleta. O envio de e-mails está desativado.")
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
        print("Erro de Autenticação SMTP. As credenciais do e-mail estão incorretas.")
        return False
    except smtplib.SMTPException as e:
        print(f"Erro SMTP ao enviar o e-mail: {e}")
        return False
    except Exception as e:
        print(f"Ocorreu um erro inesperado ao enviar o e-mail: {e}")
        return False

# --- FUNÇÕES AUXILIARES DE BANCO DE DADOS ---
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

# --- FUNÇÃO DE INICIALIZAÇÃO DO BANCO DE DADOS (COMPLETA) ---
# Esta função garante que todas as tabelas e colunas estejam corretas.
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

# Chame a função para garantir que o DB existe ao iniciar o backend
init_db()

# --- ENDPOINT 1: CRIAR NOVA RESERVA (CHAMADO PELO STREAMLIT) ---
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

        # Insere a reserva no banco de dados com status 'pending'
        c.execute(
            "INSERT INTO reservations (room_id, guest_name, check_in, check_out, guest_email, guest_contact, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (room_id, guest_name, check_in, check_out, guest_email, guest_contact, 'pending')
        )
        reservation_id = c.lastrowid
        
        # Encontra o e-mail e nome do hotel para notificação
        c.execute("SELECT h.hotel_email, h.hotel_name FROM hotels h JOIN rooms rm ON h.id = rm.hotel_id WHERE rm.id = ?", (room_id,))
        result = c.fetchone()
        hotel_email, hotel_name_booking = result if result else (None, None)
        conn.close()

        # Envia e-mail de notificação para o hotel
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
        print(f"Erro ao criar reserva no backend: {e}")
        return jsonify({"error": str(e)}), 400

# --- ENDPOINT 2: RECEBER O WEBHOOK DA PLATAFORMA DE PAGAMENTO ---
@app.route('/api/payment_webhook', methods=['POST'])
def handle_payment_webhook():
    try:
        data = request.json
        print("Webhook recebido:", data) # Imprime para o log do Render para debug
        
        # AQUI VOCÊ PRECISARÁ AJUSTAR ESTA LÓGICA CONFORME A PLATAFORMA DE PAGAMENTO.
        # ESTE É UM EXEMPLO. Consulte a documentação da API do Mercado Pago/PagSeguro.
        
        # Exemplo hipotético para Mercado Pago (pode variar dependendo do tipo de webhook):
        # Geralmente, o webhook terá um 'type' (ex: 'payment') e um 'data.id' que é o ID do pagamento.
        # Você precisaria então usar o ID do pagamento para buscar a 'external_reference'
        # ou o 'metadata' que você enviou ao criar a preferência de pagamento.
        
        # Para simplificar, vamos assumir que o webhook já traz um 'reservation_id' e 'status'.
        payment_status = data.get('status')
        reservation_id = data.get('external_reference') # Ou o campo que sua plataforma usa para a referência externa

        if payment_status == "approved" and reservation_id:
            conn = sqlite3.connect("quarto_livre.db", detect_types=sqlite3.PARSE_DECLTYPES)
            c = conn.cursor()
            
            # Atualiza o status da reserva no banco de dados para 'active'
            c.execute("UPDATE reservations SET status = 'active' WHERE id = ?", (reservation_id,))
            conn.commit()
            
            # Opcional: Enviar e-mail de confirmação FINAL para o hóspede
            # Você precisaria buscar os dados da reserva no banco para montar o e-mail.
            # Exemplo:
            # c.execute("SELECT guest_email, guest_name, room_id FROM reservations WHERE id = ?", (reservation_id,))
            # res_info = c.fetchone()
            # if res_info:
            #     guest_email, guest_name, room_id = res_info
            #     c.execute("SELECT hotel_name FROM hotels h JOIN rooms r ON h.id = r.hotel_id WHERE r.id = ?", (room_id,))
            #     hotel_name = c.fetchone()[0]
            #     subject_guest = f"Sua Reserva no {hotel_name} foi Confirmada!"
            #     body_guest = f"Olá {guest_name}, seu pagamento foi aprovado e sua reserva no {hotel_name} está confirmada!"
            #     send_email(guest_email, subject_guest, body_guest)
            
            conn.close()
            return jsonify({"message": "Reserva confirmada com sucesso."}), 200
        else:
            return jsonify({"message": "Webhook recebido, mas status não é de aprovação ou ID da reserva ausente."}), 200

    except Exception as e:
        print(f"Erro no webhook: {e}")
        return jsonify({"error": str(e)}), 400

# Endpoint de saúde para o Render (ajuda a garantir que o serviço está funcionando)
@app.route('/')
def health_check():
    return 'Backend is running!', 200

# Inicia o servidor Flask
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)