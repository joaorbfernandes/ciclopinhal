# 🚲 Projeto Ciclopinhal

Este é o projeto do site da loja de bicicletas Ciclopinhal, feito com Django.

---

## ⚙️ Setup do Projeto

### 1. Clonar o repositório (ou extrair o ZIP)

```bash

cd CICLOPINHAL

```

### 2. Criar e ativar o ambiente virtual

```bash

1. python3 -m venv venv

2. source venv/bin/activate  # Mac/Linux

2. venv\Scripts\activate   # Windows

```

### 3. Instalar dependências

```bash

pip install -r requirements.txt
```

### 4. Fazer migrações da base de dados

```bash

python3 manage.py migrate

```

### 5. Correr o servidor

```bash

python3 manage.py runserver

```

---

## 🗂 Estrutura

- `ciclopinhal/` → configuração principal Django (settings, urls)
- `website/` → aplicação com as views e templates do site
- `venv/` → ambiente virtual 
- `manage.py` → ponto de entrada do Django

---

## 🧠 Notas para o futuro

- Comenta o código à medida que vais percebendo o que cada parte faz.
- Lembra-te de manter os requisitos atualizados com `pip freeze > requirements.txt` após instalar pacotes novos.
