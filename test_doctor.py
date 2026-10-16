import requests

BASE_URL = "http://127.0.0.1:8000"

print("=== 1. REGISTERING & LOGGING IN AS DOCTOR ===")
# Register doctor (safe if already registered)
requests.post(f"{BASE_URL}/auth/register", json={
    "email": "dr.smith@hospital.com", 
    "password": "doctorpassword123", 
    "role": "doctor"
})

# Login as doctor
doc_login_res = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "dr.smith@hospital.com", 
    "password": "doctorpassword123"
})

if doc_login_res.status_code != 200:
    print("Doctor Login Failed:", doc_login_res.text)
    exit()

doctor_token = doc_login_res.json().get("access_token")
doctor_headers = {"Authorization": f"Bearer {doctor_token}"}
print("Doctor Logged In Successfully! Token Acquired.")


# NOTE: Change this to an existing processed report ID from your database (e.g., uploaded by a patient)
REPORT_ID = 1  
PATIENT_ID = 1


print(f"\n=== 2. DOCTOR REVIEWING REPORT {REPORT_ID} (AI SUMMARY & EXTRACTIONS) ===")
ext_res = requests.get(f"{BASE_URL}/reports/{REPORT_ID}/extraction", headers=doctor_headers)

if ext_res.status_code != 200:
    print("Failed to fetch report extraction. Make sure a patient has uploaded and processed report ID", REPORT_ID)
    print("Response:", ext_res.text)
    exit()

ext_data = ext_res.json()
print("Original File Path:", ext_data.get("file_path"))
print("AI-Generated Summary:\n-->", ext_data.get("ai_summary"))
extractions = ext_data.get("extractions", [])
print(f"Found {len(extractions)} extracted lab values to review.")


if len(extractions) > 0:
    first_ext_id = extractions[0]["id"]
    test_name = extractions[0]["test_name"]
    
    print(f"\n=== 3. DOCTOR VERIFYING VALUE (ID: {first_ext_id} - {test_name}) & ADDING CLINICAL NOTES ===")
    
    verify_payload = {
        "verifications": [
            {
                "extraction_id": first_ext_id,
                "is_verified": True,
                "corrected_value": None # Or provide a corrected string if AI misread it
            }
        ],
        "clinical_notes": "Reviewed report alongside AI summary. Mild anemia noted. Patient advised on dietary changes."
    }
    
    verify_res = requests.post(f"{BASE_URL}/reports/{REPORT_ID}/verify", headers=doctor_headers, json=verify_payload)
    print("Verification Status Code:", verify_res.status_code)
    print("Verification Response:", verify_res.json())


print(f"\n=== 4. FETCHING TRUSTED PATIENT RECORDS FOR PATIENT {PATIENT_ID} ===")
records_res = requests.get(f"{BASE_URL}/patients/{PATIENT_ID}/records", headers=doctor_headers)
print("Records Status Code:", records_res.status_code)
print("Trusted Patient Record History:", records_res.json())