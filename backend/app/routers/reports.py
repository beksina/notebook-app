from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.report import Report
from app.models.notebook import Notebook
from app.models.user import User
from app.schemas.report import ReportCreate, ReportUpdate, ReportResponse

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/", response_model=ReportResponse, status_code=201)
def create_report(report: ReportCreate, user_id: str, notebook_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    notebook = db.query(Notebook).filter(Notebook.id == notebook_id).first()
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    db_report = Report(**report.model_dump(), user_id=user_id, notebook_id=notebook_id)
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report


@router.get("/", response_model=List[ReportResponse])
def list_reports(
    user_id: str = None,
    notebook_id: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Report)
    if user_id:
        query = query.filter(Report.user_id == user_id)
    if notebook_id:
        query = query.filter(Report.notebook_id == notebook_id)
    return query.order_by(Report.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: str, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.patch("/{report_id}", response_model=ReportResponse)
def update_report(report_id: str, report_update: ReportUpdate, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    update_data = report_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(report, field, value)

    db.commit()
    db.refresh(report)
    return report


@router.delete("/{report_id}", status_code=204)
def delete_report(report_id: str, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    db.delete(report)
    db.commit()
