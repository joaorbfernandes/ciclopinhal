# 🌲 CICLOPINHAL

An e-commerce platform built with Django for hands-on learning of professional web development, focusing on scalability, performance, and clean code practices.

---

## 🚀 Project Goals

- Build a Django-based e-commerce platform with PostgreSQL
- Host using a scalable and sustainable service (Render - free tier initially)
- Explore optional Stripe integration and technical SEO
- Apply modular code architecture and best development practices

---

## 🧰 Tech Stack

- Python 3.12
- Django 5.x
- PostgreSQL (planned for production)
- Render (planned for deployment)
- Git + GitHub
- HTML, CSS (JavaScript, Tailwind, and React planned for future phases)

---

## 🔧 Running the Project Locally

1. **Clone the repository**
```bash
git clone https://github.com/your-username/ciclopinhal.git
cd ciclopinhal
```

2. **Create and activate a virtual environment**
```bash
python3.12 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Apply migrations and run the development server**
```bash
python manage.py migrate
python manage.py runserver
```

---

## 📦 Dependencies (`requirements.txt`)

```text
Django>=5.0
psycopg2-binary>=2.9
gunicorn>=21.2
whitenoise>=6.6
python-dotenv>=1.0
```

> Update this file regularly with: `pip freeze > requirements.txt`

---

## 🗂️ Project Structure

```text
ciclopinhal/
├── website/            # Main Django app
├── templates/
├── static/
├── media/
├── manage.py
├── requirements.txt
└── README.md
```

---

## 📌 Current Status

> In early development. Initial MVP includes:
- Homepage
- Product listing
- Product detail pages
- Session-based shopping cart
- PostgreSQL and Render setup preparation

---

## 🔮 Next Steps

- Refactor into modular Django apps (`products`, `orders`, `users`, etc.)
- Optional: integrate Stripe (can be mocked for practice)
- Implement technical SEO features and analytics
- Add user authentication and account dashboard

---