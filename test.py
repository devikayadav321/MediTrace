
import requests
import sys

BASE_URL = "http://127.0.0.1:8000"
PASSWORD = "password123"

PATIENT_EMAIL = "patient_test@gmail.com"
DOCTOR_EMAIL = "doctor_test@gmail.com"


def print_response(label, response):
    print(f"\n{label}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:2000]}")


def register_user(email, role):
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email,
            "password": PASSWORD,
            "role": role
        },
        timeout=30
    )

    print_response(f"Registering {role}", response)

    # Registration may fail if the account already exists.
    # Login below will determine whether it can be reused.
    return response


def login_user(email):
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": email,
            "password": PASSWORD
        },
        timeout=30
    )

    print_response(f"Logging in: {email}", response)

    if response.status_code != 200:
        print("Login failed. Check credentials and the server logs.")
        sys.exit(1)

    token = response.json().get("access_token")

    if not token:
        print("Login response did not contain access_token.")
        sys.exit(1)

    return {"Authorization": f"Bearer {token}"}


def main():
    try:
        print("=== 1. REGISTERING USERS ===")
        register_user(PATIENT_EMAIL, "patient")
        register_user(DOCTOR_EMAIL, "doctor")

        print("\n=== 2. LOGGING IN AS PATIENT ===")
        patient_headers = login_user(PATIENT_EMAIL)
        print("Patient login successful.")

        print("\n=== 3. UPLOADING MEDICAL REPORT ===")

        report_text = (
            "Patient Hemoglobin: 11.2 g/dL (Reference: 13.5 - 17.5). "
            "Glucose: 98 mg/dL."
        )

        files = {
            "file": (
                "requirements.txt",
                report_text,
                "text/plain"
            )
        }

        upload_res = requests.post(
            f"{BASE_URL}/reports/upload",
            headers=patient_headers,
            files=files,
            timeout=60
        )

        print_response("Report upload", upload_res)

        if upload_res.status_code not in (200, 201):
            print("Upload failed. Check the endpoint and server logs.")
            return

        upload_data = upload_res.json()
        report_id = upload_data.get("report_id")

        if report_id is None:
            print("No report_id was returned. Check the API response schema.")
            return

        print(f"Report uploaded. ID: {report_id}")

        print("\n=== 4. PROCESSING REPORT ===")
        process_res = requests.post(
            f"{BASE_URL}/reports/{report_id}/process",
            headers=patient_headers,
            timeout=180
        )

        print_response("Report processing", process_res)

        if not process_res.ok:
            print("Processing failed. Review the backend traceback.")
            return

        print("\n=== 5. VIEWING EXTRACTIONS ===")
        ext_res = requests.get(
            f"{BASE_URL}/reports/{report_id}/extraction",
            headers=patient_headers,
            timeout=60
        )

        print_response("Report extraction", ext_res)

        if not ext_res.ok:
            print("Could not retrieve extractions.")
            return

        ext_data = ext_res.json()
        extractions = ext_data.get("extractions") or []

        print("AI Summary:", ext_data.get("ai_summary"))
        print("Extraction count:", len(extractions))

        for item in extractions:
            print(item)

        print("\n=== 6. LOGGING IN AS DOCTOR ===")
        doctor_headers = login_user(DOCTOR_EMAIL)
        print("Doctor login successful.")

        print("\n=== 7. DOCTOR VERIFICATION ===")

        if not extractions:
            print(
                "No extractions were returned, so verification is skipped. "
                "Check the processing output and extraction schema."
            )
        else:
            first_extraction_id = extractions[0].get("id")

            if first_extraction_id is None:
                print("The first extraction has no id; verification skipped.")
            else:
                verify_payload = {
                    "verifications": [
                        {
                            "extraction_id": first_extraction_id,
                            "is_verified": True,
                            "corrected_value": None
                        }
                    ],
                    "clinical_notes": (
                        "Test note only. Review the reported values "
                        "against the original report."
                    )
                }

                verify_res = requests.post(
                    f"{BASE_URL}/reports/{report_id}/verify",
                    headers=doctor_headers,
                    json=verify_payload,
                    timeout=60
                )

                print_response("Doctor verification", verify_res)

        print("\n=== 8. FETCHING PATIENT RECORDS ===")

        # Use the actual patient database ID here.
        # Do not assume it is 1.
        patient_id = input(
            "Enter the actual patient database ID for records testing: "
        ).strip()

        if patient_id:
            records_res = requests.get(
                f"{BASE_URL}/patients/{patient_id}/records",
                headers=doctor_headers,
                timeout=60
            )

            print_response("Patient records", records_res)

        print("\n=== TEST RUN FINISHED ===")

    except requests.exceptions.ConnectionError:
        print(
            "Cannot connect to the API. Start FastAPI and check BASE_URL."
        )
    except requests.exceptions.Timeout:
        print("Request timed out. Check server logs and AI provider latency.")
    except requests.exceptions.RequestException as exc:
        print(f"HTTP request error: {exc}")
    except ValueError as exc:
        print(f"Could not parse the server response: {exc}")


if __name__ == "__main__":
    main()
