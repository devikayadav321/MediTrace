import requests

BASE_URL = "http://127.0.0.1:8000"

print("=== 1. REGISTERING USERS ===")
# Register Patient
requests.post(f"{BASE_URL}/auth/register", json={"email": "patient_test@gmail.com", "password": "password123", "role": "patient"})
# Register Doctor
requests.post(f"{BASE_URL}/auth/register", json={"email": "doctor_test@gmail.com", "password": "password123", "role": "doctor"})

print("\n=== 2. LOGGING IN AS PATIENT ===")
res = requests.post(f"{BASE_URL}/auth/login", json={"email": "patient_test@gmail.com", "password": "password123"})
print(f"Login Status: {res.status_code}")
if res.status_code != 200:
    print("Login Error Response:", res.text)
    exit()

patient_token = res.json().get("access_token")
print("Patient Token Acquired Successfully.")

print("\n=== 3. UPLOADING MEDICAL REPORT ===")
patient_headers = {"Authorization": f"Bearer {patient_token}"}
files = {"file": ("requirements.txt", "Patient Hemoglobin: 11.2 g/dL (Ref: 13.5 - 17.5). Glucose: 98 mg/dL.")}
upload_res = requests.post(f"{BASE_URL}/reports/upload", headers=patient_headers, files=files)

print(f"Upload Status Code: {upload_res.status_code}")
print(f"Upload Response Text: {upload_res.text}")

if upload_res.status_code != 200:
    print("Upload failed! Check server console for traceback.")
    exit()

report_id = upload_res.json().get("report_id")
print(f"Report Uploaded Successfully! Report ID: {report_id}")

print("\n=== 4. PROCESSING REPORT (AI & OCR PIPELINE) ===")
process_res = requests.post(f"{BASE_URL}/reports/{report_id}/process", headers=patient_headers)
print("Process Response:", process_res.json())

print("\n=== 5. VIEWING REPORT EXTRACTION & AI SUMMARY ===")
ext_res = requests.get(f"{BASE_URL}/reports/{report_id}/extraction", headers=patient_headers)
ext_data = ext_res.json()
print("AI Summary:", ext_data.get("ai_summary"))
print("Extracted Values Count:", len(ext_data.get("extractions")))

print("\n=== 6. LOGGING IN AS DOCTOR ===")
doc_res = requests.post(f"{BASE_URL}/auth/login", json={"email": "doctor_test@gmail.com", "password": "password123"})
doctor_token = doc_res.json().get("access_token")
doctor_headers = {"Authorization": f"Bearer {doctor_token}"}
print("Doctor Token Acquired Successfully.")

print("\n=== 7. DOCTOR VERIFYING REPORT & ADDING NOTES ===")
first_extraction_id = ext_data.get("extractions")[0]["id"]
verify_payload = {
    "verifications": [
        {
            "extraction_id": first_extraction_id,
            "is_verified": True,
            "corrected_value": None
        }
    ],
    "clinical_notes": "Patient shows mild microcytic tendency. Advised dietary iron review."
}
verify_res = requests.post(f"{BASE_URL}/reports/{report_id}/verify", headers=doctor_headers, json=verify_payload)
print("Verification Response:", verify_res.json())

print("\n=== 8. FETCHING TRUSTED PATIENT RECORDS ===")
records_res = requests.get(f"{BASE_URL}/patients/1/records", headers=doctor_headers)
print("Trusted Patient Records:", records_res.json())