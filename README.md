# 🚴‍♂️ CICLOPINHAL

An e-commerce platform built with Django for hands-on learning of professional web development, focusing on scalability, performance, and clean code practices.

---

## 🚀 Project Goals

* Build a Django-based e-commerce platform with PostgreSQL
* Host using a scalable and sustainable service (Render - free tier initially)
* Explore optional Stripe integration and technical SEO
* Apply modular code architecture and best development practices

---

## 🧰 Tech Stack

### ✅ Currently Used

* Python 3.12
* Django 5.x
* SQLite (local, PostgreSQL planned for production)
* Git + GitHub
* HTML, basic CSS
* Virtual Environment (`venv`) external to the project
* `psycopg2-binary`, `gunicorn`, `whitenoise`, `dj-database-url`, `python-dotenv`

### 🔄 Planned for Future Phases

* PostgreSQL in production
* Render for deployment
* Tailwind CSS
* JavaScript and React
* Stripe integration
* Google Analytics + SEO tools

---

## 🔧 Running the Project Locally

1. **Clone the repository**

```bash
git clone https://github.com/your-username/ciclopinhal.git
cd ciclopinhal
```

2. **Create and activate a virtual environment (outside the project folder)**

```bash
cd ~/CiclopinhalApp
python3.12 -m venv venv-ciclopinhal
source venv-ciclopinhal/bin/activate
```

3. **Navigate to the project and install dependencies**

```bash
cd CICLOPINHAL
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
dj-database-url>=0.5
```

> Update this file regularly with: `pip freeze > requirements.txt`

---

## 📂 Project Structure

```text
CICLOPINHAL/
├── ciclopinhal/        # Django settings module
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

* Homepage
* Product listing
* Product detail pages
* Session-based shopping cart
* PostgreSQL and Render setup preparation

---

## 🔮 Next Steps

* Refactor into modular Django apps (`products`, `orders`, `users`, etc.)
* Optional: integrate Stripe (can be mocked for practice)
* Implement technical SEO features and analytics
* Add user authentication and account dashboard
