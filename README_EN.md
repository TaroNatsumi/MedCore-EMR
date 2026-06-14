# MedCore - Decentralized Electronic Medical Record System

MedCore is an innovative Electronic Medical Record (EMR) platform that unites clinics, doctors, and patients into a single secure network. The project is designed with a strong focus on cryptographic data protection, multi-database routing, and strict Role-Based Access Control (RBAC).

## 🌟 Key Features

- **Medical Data Encryption (AES-256):** All diagnoses, symptoms, and medical prescriptions are encrypted before being saved to the database. Decryption is only possible using a unique token combined with the patient's PINFL.
- **Multi-Level Database Architecture:** The project utilizes several isolated SQLite databases (`db.sqlite3`, `employees.sqlite3`, `temp.sqlite3`) with automatic query routing to enhance security and distribute load.
- **Role-Based Access Control (RBAC):**
  - **MedCore Control (Superadmin):** Global management of hospital branches.
  - **Clinic Admin:** Staff management and security auditing (tracking access to medical records).
  - **Doctor:** Viewing medical history via PINFL, adding new encrypted records, and prescribing lab tests.
  - **Registry:** Patient registration and cryptographic key generation.
  - **Patient:** Personal portal ("Health Mirror") with access to their medical records and PDF export capabilities.
- **Modern UI/UX:** Responsive design built with Tailwind CSS, featuring Glassmorphism and smooth micro-animations.

## 🛠 Technology Stack

- **Backend:** Python 3, Django 5.0
- **Frontend:** HTML5, Tailwind CSS, JavaScript (Vanilla)
- **Database:** SQLite (with custom multi-db routing)
- **Security:** Integrated encryption algorithms (AES-256 via `cryptography`)
- **Export:** PDF report generation (ReportLab)

## 🚀 Installation and Setup (Local)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/medcore.git
   cd medcore
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # For Windows:
   venv\Scripts\activate
   # For Linux/Mac:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *(If `requirements.txt` is missing, run: `pip install django djangorestframework drf-spectacular reportlab cryptography`)*

4. **Apply migrations (databases will be created automatically):**
   ```bash
   python manage.py migrate
   python manage.py migrate --database=employees_db
   python manage.py migrate --database=temp_db
   ```

5. **Run the local server:**
   ```bash
   python manage.py runserver
   ```
   Open your browser and navigate to: `http://127.0.0.1:8000/`

## 🌍 Deployment Preparation (Production)

When publishing the project on a hosting server (e.g., Render, Railway, PythonAnywhere), pay attention to the following settings in `hospital_system/settings.py`:

1. **Security:**
   - Replace the `SECRET_KEY` with a new, complex key and do not expose it in the public repository.
   - Set `DEBUG = False`.
2. **Hosts:**
   - Add your server's domain to `ALLOWED_HOSTS = ['yourdomain.com', 'localhost']`.
   - Update `CSRF_TRUSTED_ORIGINS` to include your domain (e.g., `https://*.yourdomain.com`).
3. **Static Files:**
   - Configure static file collection (`STATIC_ROOT`) and run `python manage.py collectstatic` before starting the server.

---
*This project was developed as a university thesis.*
