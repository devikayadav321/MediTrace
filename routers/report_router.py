from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
import shutil, os
from database import get_db
import models, schemas, auth

router = APIRouter(prefix="", tags=["Reports & Records"])
UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 1. POST /reports/upload
@router.post("/reports/upload")
def upload_report(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != models.RoleEnum.PATIENT:
        raise HTTPException(status_code=403, detail="Only patients can upload reports.")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    report = models.Report(patient_id=current_user.id, file_path=file_path, status="uploaded")
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"message": "Report uploaded successfully", "report_id": report.id, "status": report.status}

# 2. POST /reports/{id}/process (OCR & AI Extraction Pipeline Integration)
@router.post("/reports/{id}/process")
def process_report(id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    report = db.query(models.Report).filter(models.Report.id == id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # 1. Here is where your AI/OCR pipeline runs. 
    # In production, you would send the file text to OpenAI/Gemini/Ollama here.
    # For now, we generate a professional AI summary:
    generated_ai_summary = (
        "AI Summary: The patient's metabolic panel is largely within normal limits, "
        "except for a notable dip in Hemoglobin (11.2 g/dL), indicating mild anemia. "
        "Fasting blood glucose is normal at 98 mg/dL. Recommended clinician review for iron levels."
    )
    
    # 2. Simulated Extracted Values
    mock_extracted_data = [
        {"test_name": "Hemoglobin", "result_value": "11.2", "unit": "g/dL", "reference_range": "13.5 - 17.5", "is_out_of_range": True, "evidence_snippet": "Hemoglobin: 11.2 g/dL (Ref: 13.5 - 17.5)"},
        {"test_name": "Fasting Blood Glucose", "result_value": "98", "unit": "mg/dL", "reference_range": "70 - 99", "is_out_of_range": False, "evidence_snippet": "Glucose Fasting 98 mg/dL [70-99]"}
    ]
    
    for item in mock_extracted_data:
        ext = models.ExtractedValue(
            report_id=report.id,
            test_name=item["test_name"],
            result_value=item["result_value"],
            unit=item["unit"],
            reference_range=item["reference_range"],
            is_out_of_range=item["is_out_of_range"],
            evidence_snippet=item["evidence_snippet"]
        )
        db.add(ext)
        
    # Save the AI summary and update status
    report.ai_summary = generated_ai_summary
    report.status = "processed"
    db.commit()
    
    return {
        "message": "Report processed successfully with AI Summary", 
        "report_id": report.id, 
        "ai_summary": report.ai_summary,
        "status": report.status
    }

# 3. GET /reports/{id}/extraction
@router.get("/reports/{id}/extraction")
def get_report_extraction(id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    report = db.query(models.Report).filter(models.Report.id == id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    extractions = db.query(models.ExtractedValue).filter(models.ExtractedValue.report_id == id).all()
    
    return {
        "report_id": report.id,
        "file_path": report.file_path,  # <--- Doctor gets access to the original report file path
        "ai_summary": report.ai_summary,  # <--- Doctor gets the AI generated summary text
        "status": report.status,
        "extractions": extractions
    }

# 4. POST /reports/{id}/verify
@router.post("/reports/{id}/verify")
def verify_report(id: int, payload: schemas.ReportVerifyPayload, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != models.RoleEnum.DOCTOR:
        raise HTTPException(status_code=403, detail="Only doctors can verify reports.")
        
    report = db.query(models.Report).filter(models.Report.id == id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    for v in payload.verifications:
        ext = db.query(models.ExtractedValue).filter(models.ExtractedValue.id == v.extraction_id, models.ExtractedValue.report_id == id).first()
        if ext:
            ext.is_verified = v.is_verified
            ext.corrected_value = v.corrected_value
            
    if payload.clinical_notes:
        note = models.ClinicalNote(report_id=report.id, doctor_id=current_user.id, notes=payload.clinical_notes)
        db.add(note)
        
    report.status = "verified"
    db.commit()
    return {"message": "Report verification and clinical notes saved successfully", "report_id": report.id}

# 5. GET /patients/{id}/records
@router.get("/patients/{id}/records")
def get_patient_records(id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role == models.RoleEnum.PATIENT and current_user.id != id:
        raise HTTPException(status_code=403, detail="Access denied to other patient records.")
        
    reports = db.query(models.Report).filter(models.Report.patient_id == id).all()
    
    results = []
    for rep in reports:
        verified_extractions = [e for e in rep.extractions if e.is_verified]
        note = rep.clinical_note.notes if rep.clinical_note else None
        results.append({
            "report_id": rep.id,
            "upload_date": rep.created_at,
            "status": rep.status,
            "verified_values": verified_extractions,
            "clinical_note": note
        })
        
    return {"patient_id": id, "trusted_records": results}