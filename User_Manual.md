# MedCore EMR - User Manual

## 1. Introduction
Welcome to **MedCore**, a decentralized, AES-256 encrypted Electronic Medical Record (EMR) system. MedCore is designed to maximize data security by physically isolating employee credentials from sensitive patient medical histories across multiple databases.

## 2. Roles and Access Levels
MedCore utilizes strict Role-Based Access Control (RBAC). The available roles are:
*   **Superadmin (MedCore Admin):** Global system overseer. Manages hospitals and clinic administrators.
*   **Clinic Admin:** Manages employees (Doctors, Lab Techs, Registrars) within their specific hospital.
*   **Registry (Регистратура):** Registers new patients and updates demographic information.
*   **Doctor (Врач):** Conducts patient consultations, diagnoses illnesses, assigns lab tests, and manages AES-256 encrypted records.
*   **Lab Technician (Лаборант):** Conducts assigned lab tests and uploads structured results/images.
*   **Patient (Пациент):** Views their own medical history using their PINFL and Passport (Read-only access).

---

## 3. Getting Started
### 3.1 Logging In
1. Navigate to the main login page.
2. Select your role (Employee or Patient).
3. **Employees:** Enter your assigned Email and Password.
4. **Patients:** Enter your 14-digit PINFL and Passport series/number.

---

## 4. Superadmin (MedCore Admin) Dashboard
*Access: Global*
*   **Add Hospital:** Click "Добавить клинику", enter the hospital name, address, and generate a unique API Key.
*   **Add Clinic Admin:** Select a hospital, enter the admin's email and password. This admin will now have full control over that specific hospital's staff.
*   **System Logs:** View real-time system processing logs tracking employee actions across all branches.

---

## 5. Clinic Admin Dashboard
*Access: Hospital-Specific*
*   **Manage Staff:** Add new Doctors, Registrars, or Lab Techs to your hospital branch.
*   **Update Schedules:** Edit working hours and shift types (Morning/Evening) for doctors.
*   **Audit Logs:** Monitor employee login times and system actions for security auditing.

---

## 6. Registry Dashboard
*Access: Hospital-Specific*
*   **Search Patient:** Enter a 14-digit PINFL to search for an existing patient across the global network.
*   **Create Patient:** If the patient does not exist, fill in the registration form (Full Name, Passport, Birth Date, Blood Group, etc.). 
    * *Note: The system will automatically block duplicate PINFLs or Passports to maintain data integrity.*
*   **Update Info:** Modify phone numbers or chronic disease records for existing patients.

---

## 7. Doctor Dashboard
*Access: Hospital-Specific*
*   **Search Patient:** Enter the patient's PINFL to securely retrieve their records.
*   **Create Record:** 
    1. Enter the Disease Name.
    2. Fill out Symptoms, Diagnosis, and Treatment Plans.
    3. Click "Save". The system will instantly encrypt your input using AES-256 before saving it to the database.
*   **View History:** Click "Расшифровать" (Decrypt) on a past record. The system temporarily decrypts the payload for viewing. *Note: For security, closing the session or logging out will instantly wipe the decrypted data from the server's memory.*
*   **Assign Lab Tests:** While viewing a patient, select a test type (e.g., Blood Test, X-Ray) and assign it to the laboratory queue.

---

## 8. Lab Technician Dashboard
*Access: Hospital-Specific*
*   **Task Queue:** View pending lab tests assigned by doctors.
*   **Process Test:**
    1. Click "Взять в работу" (Start).
    2. Input structured test results (e.g., Hemoglobin levels) based on the test schema.
    3. Upload images or scan files if necessary (e.g., MRI scans).
    4. Click "Отправить врачу" (Send to Doctor). The results will instantly appear in the doctor's encrypted payload.

---

## 9. Patient Portal
*Access: Read-Only (Global)*
*   **Login:** Enter your 14-digit PINFL and Passport number.
*   **Dashboard:** View a timeline of your hospital visits.
*   **Export Data:** Click the PDF export button to securely download an official, formatted report of your medical history and lab results.
