# User Manual – MedCore Electronic Medical Record System

## 1. Introduction
MedCore is a secure, decentralized web-based Electronic Medical Record (EMR) system that utilizes AES-256 encryption and a multi-database architecture to protect sensitive patient data. The system features three main interfaces:
*   **Patient Portal** – for patients to securely view their medical history and download official PDF reports.
*   **Employee Portal** – for hospital staff (Doctors, Registrars, Lab Technicians, Clinic Admins) to manage patient data, conduct encrypted consultations, process lab tests, and manage local hospital operations.
*   **MedCore Control (Superadmin)** – a global administrative dashboard to manage the entire network of hospital branches and monitor system-wide processing logs.

The system is designed to be deployed live at:
*   **Main Portal:** `https://<your-render-url>.onrender.com`

---

## 2. Patient Portal – User Guide
### 2.1 Login
1. Open the main portal URL.
2. Click **Login as Patient** on the landing page.
3. Enter your **14-digit PINFL** and **Passport Series/Number**.
4. Click **Login**. You will be securely authenticated and redirected to your "Health Mirror" dashboard.

### 2.2 Dashboard – Viewing Medical History
*   After logging in, your profile information (Full Name, Date of Birth, Blood Group) is displayed at the top.
*   Below, you will see a chronological timeline of all your hospital visits across the MedCore network.
*   Each visit card displays the Hospital Name, Doctor's Name, Date, Diagnosis, Symptoms, and Treatment Plan.
*   Lab test results associated with the visit are also displayed natively within the card.

### 2.3 Exporting Medical Records
1. On your dashboard, locate the specific medical record you wish to download.
2. Click the **Export to PDF** button on the record card.
3. The system will dynamically generate and download an official PDF document containing the clinic's details, the doctor's signature field, and your encrypted medical data.

---

## 3. Employee Portal – User Guide
### 3.1 Doctor Workflow
**Login:**
1. Open the portal and click **Login as Employee**.
2. Enter your assigned email address and password.
3. Click **Login**. You will be routed to the Doctor Dashboard.

**Searching for a Patient:**
1. On the dashboard, enter the patient's 14-digit PINFL in the search bar.
2. Click **Find Patient**. The search panel remains visible so you can easily switch to a new patient later.
3. The patient's basic demographic data will appear.

**Creating a New Record (AES-256 Encryption):**
1. Once a patient is selected, scroll to the "New Consultation" form.
2. Fill in the fields: Disease Name, Symptoms, Diagnosis, and Treatment.
3. Click **Save Record**. The system instantly encrypts this payload using AES-256 before saving it to the `Global DB`.

**Decrypting & Viewing History:**
1. Scroll to the patient's medical history section.
2. To read a past record, click the **Decrypt (Расшифровать)** button next to it.
3. The server temporarily decrypts the data into memory (`temp_db`) and displays it on your screen.

**Assigning Lab Tests:**
1. Below the patient's active record, locate the **Assign Lab Test** section.
2. Select the required test type (e.g., Blood Test, MRI) from the dropdown.
3. Click **Assign**. The task is instantly sent to the Laboratory queue.

**Secure Logout:**
*   Click **Logout** in the navigation bar. The system will automatically purge any temporarily decrypted records associated with your session from the database, ensuring zero data leakage.

### 3.2 Registry Workflow
**Registering a New Patient:**
1. Log in using a Registry account.
2. Search for the patient using their PINFL to ensure they are not already in the system.
3. If not found, fill out the Registration Form (Full Name, PINFL, Passport, Birth Date, Gender, Phone, Address).
4. Click **Register Patient**.
5. *Note: If you attempt to register a patient with a PINFL or Passport that already exists, the system will reject the request and display an `IntegrityError` warning.*

### 3.3 Lab Technician Workflow
**Processing Lab Tests:**
1. Log in using a Lab Technician account.
2. Your dashboard displays a real-time queue of tests assigned by doctors.
3. Locate a pending test and click **Take into work (Взять в работу)**.
4. Input the structured test results (e.g., specific biomarker levels).
5. (Optional) Upload an image or document (e.g., X-ray scan).
6. Click **Send to Doctor**. The status updates to `Completed`, and the results are attached to the doctor's encrypted record.

---

## 4. Admin Panel – User Guide
### 4.1 Clinic Admin
*   **Managing Staff:** Log in to view your specific hospital's staff roster. Click **Add Employee** to create new accounts for Doctors, Registrars, or Lab Technicians.
*   **Audit Logging:** Navigate to the Audit tab to view a secure log of all employee logins and actions within your hospital branch.

### 4.2 Superadmin (MedCore Control)
**Global Management:**
1. Navigate to `/medcore/login/`.
2. Log in with Superadmin credentials.
3. You will see a global overview of all hospital branches connected to the decentralized network.

**Adding a New Hospital:**
1. Click **Add Clinic**.
2. Enter the clinic's name and address. The system generates a unique API Key for that branch.
3. Create an initial Clinic Admin account for that hospital so they can begin hiring staff.

**Global Logs:**
*   Click on **Processing Logs** to monitor real-time, system-wide actions across the entire `Global DB`. This tracks patient registrations, record decryptions, and cross-branch data access.
