import streamlit_authenticator as stauth

# Senhas em texto puro
hashed_passwords = stauth.Hasher(["admin123", "hotel123"]).generate()

# Dicionário de usuários
users = {
    "admin": {
        "name": "Administrador",
        "password": hashed_passwords[0]
    },
    "hotel1": {
        "name": "Hotel Vila Mar",
        "password": hashed_passwords[1]
    }
}
