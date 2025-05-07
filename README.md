
# CICLOPINHAL – E-commerce Project

CICLOPINHAL is a professional and educational Django-based e-commerce platform under development.  
This project is structured for scalability, clean architecture, technical SEO, and analytics integration.

---

## 🚀 Tech Stack

- Python 3.12
- Django 5.x
- PostgreSQL (Render)
- HTML + Tailwind CSS (future)
- Render (deployment)
- GitHub (public portfolio)

---

## ⚙️ Local Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/ciclopinhal.git
cd ciclopinhal
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file based on the `.env.example` provided:

```bash
cp .env.example .env
```

Fill in your secret key and DB credentials (if using PostgreSQL).

---

### 5. Run the development server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` to see the app in action.

---

## 📂 Project Structure

```
ciclopinhal/
├── ciclopinhal/         ← Django project
│   └── settings/        ← Modular settings (base, dev, prod)
├── website/             ← Main Django app
├── templates/           ← HTML templates
├── static/              ← Static files (CSS, JS, images)
├── media/               ← Uploaded files (images from admin)
├── .env.example         ← Template for environment config
├── manage.py
```

---

## 🧠 Learning Objectives

This project is part of a full learning journey:
- Understand Django architecture and best practices
- Prepare for secure deployment
- Integrate SEO and analytics
- Manage performance and database monitoring

---

## ✅ Credits

Maintained by [Your Name].  
For educational and portfolio purposes.
