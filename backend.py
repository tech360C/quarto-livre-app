# Arquivo: backend.py
import os
import sqlite3
from flask import Flask, request, jsonify
from datetime import datetime, date
import json

app = Flask(__name__)

# --- Configuração do Banco de Dados ---
# A função de inicialização do DB deve ser a mesma do seu app Streamlit para garantir a estrutura
def init_db():
    try:
        conn = sqlite3.connect("quarto_livre.db", detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS users (...)") # Adicione a mesma lógica de criação de tabelas
        c.execute("CREATE TABLE IF NOT EXISTS reservations (...)")
        # etc...
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Erro ao inicializar o banco de dados: {e}")

# init_db() # Chame para garantir que o DB existe ao iniciar o backend

# --- Endpoint para criar nova reserva (chamado pelo Streamlit) ---
@app.route('/create_reservation', methods=['POST'])
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
        conn.commit()
        conn.close()

        # TODO: Adicionar lógica para gerar link de pagamento e enviá-lo ao hóspede e hotel
        # ... esta parte ainda precisaria de uma implementação personalizada.

        return jsonify({"message": "Reserva criada com sucesso.", "reservation_id": reservation_id}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# --- Endpoint para o Webhook do Pagamento ---
@app.route('/payment_webhook', methods=['POST'])
def handle_payment_webhook():
    try:
        data = request.json
        payment_status = data.get('status')
        # TODO: AQUI É O PONTO CRUCIAL
        # A lógica para validar o webhook e extrair o ID da reserva
        # Varia muito entre as plataformas (Mercado Pago, PagSeguro, etc.).
        # Você precisaria da documentação de cada uma para implementar.
        
        # Exemplo hipotético:
        reservation_id = data.get('external_reference')
        if payment_status == "approved" and reservation_id:
            conn = sqlite3.connect("quarto_livre.db", detect_types=sqlite3.PARSE_DECLTYPES)
            c = conn.cursor()
            
            # Atualizar o status da reserva no banco de dados para 'active'
            c.execute("UPDATE reservations SET status = 'active' WHERE id = ?", (reservation_id,))
            conn.commit()
            
            # TODO: Aqui você poderia enviar um e-mail de confirmação ao hóspede e ao hotel
            # usando a função de e-mail que você já tem.
            
            conn.close()
            return jsonify({"message": "Reserva confirmada com sucesso."}), 200
        else:
            return jsonify({"message": "Webhook recebido, mas status não é de aprovação."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Endpoint de saúde para o Render
@app.route('/')
def health_check():
    return 'Backend is running!', 200

if __name__ == '__main__':
    # Use um host dinâmico para o Render
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)