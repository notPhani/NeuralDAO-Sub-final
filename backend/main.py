# main.py
from fastapi import FastAPI, HTTPException, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
from typing import Optional, Dict, Any, List
import uvicorn
from supabase import create_client
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import your existing classes
from LLM_api import (
    IntelligentClinicalRAGSystem, 
    TreatmentRecommendation, 
    RAGSummary
)

# Import the intelligent analyzer
from LLM1 import IntelligentPatientAnalyzer

# Initialize FastAPI app
app = FastAPI(
    title="DocPilot Clinical AI Assistant",
    description="AI-powered clinical decision support system with integrated UI",
    version="1.0.0"
)

# ============================================================================
# CORS CONFIGURATION
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# MOUNT STATIC FILES
# ============================================================================

# Create static directory if it doesn't exist
if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/static", StaticFiles(directory="static"), name="static")

# ============================================================================
# INITIALIZE AI ANALYZER FIRST
# ============================================================================

try:
    PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
    if PERPLEXITY_API_KEY:
        intelligent_analyzer = IntelligentPatientAnalyzer(PERPLEXITY_API_KEY)
        print("✅ Intelligent Patient Analyzer initialized with Perplexity API")
    else:
        intelligent_analyzer = None
        print("⚠️  WARNING: PERPLEXITY_API_KEY not found. AI analysis will be disabled.")
except Exception as e:
    intelligent_analyzer = None
    print(f"❌ Failed to initialize AI analyzer: {e}")

# ============================================================================
# SERVICE CLASSES
# ============================================================================

class CombinedClinicalService:
    """Combined service for RAG + Treatment Recommendations"""
    
    def __init__(self):
        self.rag_system = IntelligentClinicalRAGSystem()
        self.treatment_system = TreatmentRecommendation()
    
    def process_clinical_query(self, query: str, patient_id: Optional[str] = None) -> Dict[str, Any]:
        """Process clinical query with RAG + treatment recommendations"""
        
        # Construct full query
        full_query = query
        if patient_id:
            full_query = f"{query} for patient {patient_id}"
        
        # Step 1: Get clinical data using intelligent RAG
        rag_result = self.rag_system.search(full_query)
        
        if "error" in rag_result:
            return {"error": rag_result["error"]}
        
        # Step 2: Get treatment recommendations based on RAG data
        summary_data = {
            "success": True,
            "summary": {
                "key_findings": self._extract_key_findings(rag_result),
                "summary": f"Clinical data retrieved for query: {query}"
            }
        }
        
        treatment_result = self.treatment_system.get_treatment_recommendations(summary_data)
        
        return {
            "success": True,
            "query": query,
            "patient_id": patient_id,
            "rag_data": rag_result,
            "treatment_recommendations": treatment_result,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _extract_key_findings(self, rag_result: Dict[str, Any]) -> List[str]:
        """Extract key findings from RAG data for treatment system"""
        findings = []
        
        raw_data = rag_result.get("raw_data", [])
        if raw_data:
            conditions = set()
            medications = set()
            
            for record in raw_data[:5]:  # Analyze first 5 records
                if "condition" in str(record).lower():
                    conditions.update([v for k, v in record.items() if "condition" in k.lower() and v])
                if "medication" in str(record).lower():
                    medications.update([v for k, v in record.items() if "medication" in k.lower() and v])
            
            if conditions:
                findings.extend(list(conditions)[:3])  # Top 3 conditions
            if medications:
                findings.extend(list(medications)[:3])  # Top 3 medications
        
        return findings if findings else ["Clinical data analysis"]


class SummaryService:
    """Service for AI-powered clinical data summarization"""
    
    def __init__(self):
        self.summarizer = RAGSummary()
    
    def generate_summary(self, table_data: Dict[str, Any], original_query: str) -> Dict[str, Any]:
        """Generate comprehensive clinical summary"""
        
        try:
            result = self.summarizer.summarize_table_data(table_data, original_query)
            
            # Add metadata
            result["timestamp"] = datetime.utcnow().isoformat()
            result["data_source"] = {
                "total_records": table_data.get("total_records", 0),
                "search_type": table_data.get("search_type", "unknown")
            }
            
            return result
            
        except Exception as e:
            return {"success": False, "error": f"Summarization failed: {str(e)}"}


class AIPatientService:
    """AI-powered patient management service"""
    
    def __init__(self, analyzer):
        self.patients = {}  # In-memory storage for demo
        self.analyzer = analyzer  # Use the passed analyzer instance
    
    def process_patient_with_ai(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process patient data with AI analysis similar to clinical_query pattern"""
        try:
            patient_id = str(uuid.uuid4())
            
            if not self.analyzer:
                # Fallback without AI - similar to your other services
                return {
                    "success": True,
                    "patient_id": patient_id,
                    "message": "Patient added without AI analysis (service unavailable)",
                    "rag_data": {
                        "total_records": 1,
                        "search_type": "patient_add",
                        "patients_searched": 1,
                        "raw_data": [self._format_patient_for_table(patient_data)],
                        "sql_query": f"Patient added: {patient_data.get('personal_details', {}).get('name', 'Unknown')}",
                        "explanation": "Patient data stored successfully without AI analysis"
                    },
                    "treatment_recommendations": {
                        "success": False,
                        "error": "AI analysis service unavailable"
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Process with AI - similar to your RAG system
            print(f"🔍 DEBUG: Calling analyzer.analyze_patient_data with type: {type(patient_data)}")
            ai_result = self.analyzer.analyze_patient_data(patient_data)
            print(f"🔍 DEBUG: AI result: {ai_result}")
            
            if not ai_result.get("success"):
                return {"error": ai_result.get("error", "AI analysis failed")}
            
            # Format result similar to your text-query response structure
            result = {
                "success": True,
                "patient_id": patient_id,
                "query": f"AI analysis for patient: {patient_data.get('current_complaint', 'Medical assessment')}",
                "rag_data": {
                    "total_records": 1,
                    "search_type": "ai_patient_analysis", 
                    "patients_searched": 1,
                    "raw_data": [self._format_patient_for_table(patient_data)],
                    "sql_query": f"AI Analysis: {patient_data.get('current_complaint', 'N/A')}",
                    "explanation": f"Intelligent clinical analysis focusing on: {ai_result.get('ai_analysis', {}).get('problem', 'clinical assessment')}"
                },
                "treatment_recommendations": self._format_ai_recommendations(ai_result.get("ai_analysis", {})),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store patient data
            self.patients[patient_id] = {
                "created_at": result["timestamp"],
                "original_data": patient_data,
                "ai_analysis": ai_result
            }
            
            return result
            
        except Exception as e:
            print(f"❌ DEBUG: Exception in process_patient_with_ai: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": f"Failed to process patient: {str(e)}"}
    
    def _format_patient_for_table(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format patient data for table display"""
        personal = patient_data.get('personal_details', {})
        return {
            "name": personal.get('name', 'Unknown'),
            "age": personal.get('age', 'Unknown'),
            "gender": personal.get('gender', 'Unknown'),
            "complaint": patient_data.get('current_complaint', 'Not specified'),
            "medical_history": ', '.join(patient_data.get('medical_history', [])),
            "current_medications": ', '.join(patient_data.get('current_medications', [])),
            "vital_signs": str(patient_data.get('vital_signs', {}))
        }
    
    def _format_ai_recommendations(self, ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Format AI analysis into treatment recommendations"""
        return {
            "success": True,
            "treatment_recommendations": {
                "problem_statement": ai_analysis.get("problem", ""),
                "key_factors": ai_analysis.get("relevant_factors", []),
                "priority_order": ai_analysis.get("priority_order", []),
                "action_plan": ai_analysis.get("action_plan", []),
                "clinical_reasoning": ai_analysis.get("filtering_rationale", "AI-powered intelligent filtering applied"),
                "evidence_sources": ai_analysis.get("clinical_references", [])
            }
        }


class SessionService:
    """Service for session management"""
    
    def __init__(self):
        self.current_session = None
    
    def create_new_session(self) -> Dict[str, Any]:
        """Create a new clinical session"""
        try:
            session_id = str(uuid.uuid4())
            
            self.current_session = {
                "session_id": session_id,
                "created_at": datetime.utcnow().isoformat(),
                "queries": [],
                "status": "active"
            }
            
            return {
                "success": True,
                "session_id": session_id,
                "message": "New session created successfully",
                "session_data": self.current_session
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to create session: {str(e)}"}


# Initialize services (AFTER analyzer initialization)
combined_service = CombinedClinicalService()
summary_service = SummaryService()
ai_patient_service = AIPatientService(intelligent_analyzer)  # Pass the analyzer instance
session_service = SessionService()

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ClinicalQueryRequest(BaseModel):
    query: str
    patient_id: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "query": "Show me all medications for this patient",
                "patient_id": "006c29d1-d868-3a9e-ceab-31f23e398f45"
            }
        }


class SummaryRequest(BaseModel):
    table_data: Dict[str, Any]
    query: str
    
    class Config:
        schema_extra = {
            "example": {
                "table_data": {
                    "search_type": "patient_search",
                    "total_records": 4,
                    "raw_data": [
                        {
                            "patient_name": "John Doe",
                            "medications_DESCRIPTION": "Acetaminophen 325 MG",
                            "medications_START": "2023-01-01",
                            "medications_TOTALCOST": 45.86
                        }
                    ]
                },
                "query": "Show patient medications"
            }
        }


class PatientData(BaseModel):
    personal_details: Dict[str, Any]
    medical_history: List[str]
    current_complaint: str
    current_medications: List[str]
    vital_signs: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "personal_details": {
                    "name": "John Smith",
                    "age": 45,
                    "gender": "Male"
                },
                "medical_history": [
                    "Asthma (controlled)",
                    "Type 2 Diabetes (on Metformin)",
                    "Childhood fracture of hand → rod present in hand"
                ],
                "current_complaint": "Fell down today, severe pain in leg",
                "current_medications": ["Metformin", "Albuterol inhaler"],
                "vital_signs": {
                    "blood_pressure": "140/90",
                    "heart_rate": "88",
                    "pain_scale": "8/10"
                }
            }
        }


# ============================================================================
# API ROUTER
# ============================================================================

# Create API router with /api prefix
api_router = APIRouter(
    prefix="/api",
    tags=["Clinical AI API"],
    responses={404: {"description": "Not found"}},
)


@api_router.post("/text-query")
async def clinical_text_query(request: ClinicalQueryRequest):
    """
    Combined clinical query endpoint that retrieves patient data using AI-powered RAG 
    and provides evidence-based treatment recommendations.
    """
    try:
        result = combined_service.process_clinical_query(
            query=request.query,
            patient_id=request.patient_id
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Clinical query failed: {result['error']}"
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@api_router.post("/summarize")
async def summarize_clinical_data(request: SummaryRequest):
    """
    AI-powered clinical data summarization endpoint that provides comprehensive 
    analysis and insights from clinical table data.
    """
    try:
        result = summary_service.generate_summary(
            table_data=request.table_data,
            original_query=request.query
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Summarization failed: {result.get('error')}"
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

import random
from datetime import datetime, timedelta

@app.get("/api/list-patients")
async def list_patients():
    """List all patient folders with realistic metadata for hackathon demo"""
    try:
        # Your actual patient IDs
        patient_ids = [
            'patient_006c29d1-d868-3a9e-ceab-31f23e398f45', 'patient_0098f2a9-2f4d-4209-778d-cb3426d85987',
            'patient_02cb6ae2-d3fd-e497-7077-77cdbeb5f0a1', 'patient_033cccaf-bc92-3ddd-b64c-9ea45268a971',
            'patient_04181caa-fcc1-c6c8-743e-a903eff368de', 'patient_04300771-e00c-e414-830a-66f7ef3584da',
            'patient_0851b7fb-87a8-3edc-1e11-8dcb03824dde', 'patient_0a1bd9a2-fc21-7ad3-3d85-cf31b68eec28',
            'patient_0c76b28e-5685-0754-12d1-b1a6b79866f7', 'patient_0db7560a-db72-0cef-c59c-1fd6762bc50d',
            'patient_0e5401fd-b241-3c84-066e-2b88e5ddafc7', 'patient_0fca905f-391c-08d3-4b93-b53f69b9da53',
            'patient_103b63c9-9ef8-6d25-771e-2fba661489a1', 'patient_119e46a1-9323-916b-4152-e0daedb48f23',
            'patient_13ac6eee-8cf1-e597-1c91-453c8f069a3c', 'patient_155b0e07-d5a9-cc0c-e01a-a982c5d9a8d6',
            'patient_15c6645a-8f7b-df42-95ec-8b49bda12c10', 'patient_1754bc7d-28cd-4933-fc72-3d9a0d77cf54',
            'patient_1a9873c2-1d93-e9d6-4e36-77fdb07fbcb2', 'patient_1c1ab155-7314-095d-1641-06efd2cd0873',
            'patient_1e9713a5-742f-aca0-cf95-446338fdc57f', 'patient_1f0ca842-8c2d-a943-c047-dafce690f5a2',
            'patient_20802592-1c31-7339-4c4c-2fe648e1a716', 'patient_25f30c19-e98a-85ea-6de8-f976388d4678',
            'patient_28f107b5-e973-ece3-b762-c2dbd9a01ba8', 'patient_2bc26ad6-ad32-0bb0-f964-0fe271fdf054',
            'patient_2da86d63-34ae-b887-ddff-8f6f1e6990f1', 'patient_2e2eb927-efd5-bbd4-297d-99071243a8cb',
            'patient_30e48e16-2df7-207e-7a3d-1650ef0c1ed8', 'patient_31014896-9c27-ae1a-71db-319df60ac5d3',
            'patient_3270397c-dfa3-6cea-f2ec-be21ade6c52c', 'patient_3477fa4e-a09a-e779-5d56-eeb00dee758b',
            'patient_349720c1-0627-e77a-1619-bb11b1530e96', 'patient_37895f0e-877f-7ea7-aa1b-0b69fcd11385',
            'patient_3ac8c3a5-3c16-699f-537b-e7816347104b', 'patient_3c763653-7fd3-af8a-e65f-79d5bde98d3a',
            'patient_3de203ff-a5b9-e99a-c705-3927503e2abf', 'patient_3f7873ab-0f61-be0c-9af8-f246eec6223a',
            'patient_406e8bad-81b5-7624-5b8a-4aeeb74028f5', 'patient_43e4a5fe-add4-5581-d0ef-80764c313418',
            'patient_45e1243b-470c-efa8-8ce9-f0d50485a846', 'patient_48f06a5e-0d20-3fe6-f5ea-b45bc79e90db',
            'patient_49424eb4-e2ba-40b5-0e2b-2c2d742cce4b', 'patient_4faedf9f-2c0e-9800-943a-0930bd08c4c8',
            'patient_55bc1034-ecf9-d005-5b9e-eac706fe541f', 'patient_575cac8f-bed1-32da-30a6-3a516a78500d',
            'patient_57b21dea-ff00-6c3e-92d9-91c7627f53b2', 'patient_583c0740-39e1-9e33-f9d6-4fdb2b815669',
            'patient_5a0fd7a2-6bfd-af1e-7bb6-2060136302c3', 'patient_5c68f376-dd2c-1133-a9cf-f023a5d99078',
            'patient_5dbd017f-d447-9546-8610-8f7bdaa77789', 'patient_5f9bfe93-062d-ca4b-5389-f8cac604a7e3',
            'patient_5fda1015-d0a5-e32d-d0b8-4662e6ce6c2b', 'patient_641efcda-7397-4172-c6ac-8231342fa53e',
            'patient_6754b3bf-f5ac-f359-fef6-87cf4b8508ab', 'patient_6da68959-d157-b9a3-48bc-1454e5517d6a',
            'patient_6f808eef-a811-11eb-3fcb-1ed910d79c4b', 'patient_70775c58-59fb-a3db-9858-1d427567c195',
            'patient_72b7a6b1-b196-7ba5-eb82-1e9b0f75b7bd', 'patient_74a4cdcf-7cc0-7658-e1e0-cd1182d5f205',
            'patient_750eda4e-3f12-c701-869e-1d392387dfa0', 'patient_7757f538-bffe-a8bf-0efb-8363354aab87',
            'patient_7785daad-accb-cb33-7d8f-2faebf8eb639', 'patient_77dfae18-8c8c-0ec2-050c-dd93f3ea1cc2',
            'patient_782001bc-f712-50ae-04f5-9a488f3ef4aa', 'patient_782ada1b-32a4-888a-8812-d8de70d6e5d0',
            'patient_787f9e8e-d3a4-0407-55d1-01a3414fceaf', 'patient_7cad1f7c-cf61-fd24-254f-d02265160c0a',
            'patient_7ddb0322-da41-c9d3-2018-4581109426b2', 'patient_80cca49f-29f9-d04f-851d-84b95f863793',
            'patient_80e7f50a-3e99-d5ac-cf97-f8a4b4f9e6c7', 'patient_8c8e1c9a-b310-43c6-33a7-ad11bad21c40',
            'patient_8dacd3c2-9e71-7d5d-02aa-7ad9541a0ab9', 'patient_8f87d617-a91b-29e0-e155-96a5d71de419',
            'patient_97a046ab-d147-2707-d4cd-cba26c5360ad', 'patient_9ad4a69b-02de-4aeb-2262-76745583a8ac',
            'patient_9c6ef4a8-79e8-92c4-2279-a0666694419b', 'patient_9cbd97ef-2209-9b1c-b6f7-a23a6c081740',
            'patient_9f867ec4-9f3a-35af-4bb6-e2c18a603c72', 'patient_9f9dbdcb-23a1-82cc-b7bc-e0e420a95bd1',
            'patient_a331b5bc-cbea-a205-a8bf-dbf3255ef36a', 'patient_a3d34c1f-5421-e078-38ec-1498a5941dbe',
            'patient_add095a2-64e5-aae2-11d2-9be2f89ff843', 'patient_add41d13-8e70-e327-4367-8d945e20f27b',
            'patient_ae05f1fa-7913-f7bc-41bd-2dc8827555e7', 'patient_b427e4ea-3a48-207a-bf7d-710f0b574091',
            'patient_b5193ef4-ab73-ddd3-e7dd-d8168b33e7f6', 'patient_b61886a1-b76f-4ecf-b37a-29d0c6aefc26',
            'patient_b8ded152-e326-5833-f747-bf9b35c60a76', 'patient_b9bacf2f-7027-2e05-fa5b-19167071fdde',
            'patient_bd6e7acc-7c87-7f0a-5d15-959cf11e22da', 'patient_be874504-c868-ebfd-9a77-df6b1e5ff6cc',
            'patient_c3dae8db-25ee-c40b-c605-600fad411d34', 'patient_c420eb5d-97eb-59b6-b247-0ba188408db5',
            'patient_c8114bff-6bab-8353-597d-4f155f5f1c3e', 'patient_cae42a0d-c36c-8af1-8277-7c9abd011778',
            'patient_d423f0d1-e7ed-d47e-af4f-20cfd996ac67', 'patient_e1c6b5c4-34b7-7296-56ed-4c634e93deb9',
            'patient_e5ed5bc3-51e1-a9a7-01fb-f66b8ac4045d', 'patient_e64918a6-528c-b49e-dff2-3cbe33266342',
            'patient_e6705c33-7349-8b12-484d-3b1f93227178', 'patient_e83fe1b3-f94f-5591-f851-1da300e24e99',
            'patient_edc17058-55fb-08c7-12df-ece93a402e50', 'patient_eeae0d25-5865-76b4-8ad7-9526bcf3a94d',
            'patient_ef2eaed0-b056-2a9f-7ccb-07a9c9fdabd5', 'patient_f380d818-b685-618e-22dc-b2db2fe0a6c0',
            'patient_f49221bb-20fb-45cb-9345-09b6a83ae9de', 'patient_f4e9b2c8-9db5-5597-a6a7-1215a638c1e2',
            'patient_faec5a04-6c56-4296-9fec-4e218e627a32', 'patient_fc3e2c0f-6809-7e7b-4ad8-769a732bf13a',
            'patient_fd7387f3-3465-7a34-6778-25aac38a13c2'
        ]
        
        # Generate realistic metadata for each patient
        patient_folders = []
        
        for patient_id in patient_ids:
            # Random dates in the last 30 days
            days_ago = random.randint(1, 30)
            created_date = datetime.now() - timedelta(days=days_ago)
            modified_date = created_date + timedelta(days=random.randint(0, days_ago))
            
            # Random file metadata
            csv_count = random.randint(1, 4)
            csv_size = random.randint(1500, 8000)  # bytes
            total_size = csv_size + random.randint(0, 2000)  # some additional files
            
            patient_folders.append({
                'patient_id': patient_id,
                'csv_count': csv_count,
                'main_csv': f"{patient_id}_data.csv",
                'main_csv_size': csv_size,
                'total_size': total_size,
                'created_at': created_date.isoformat(),
                'updated_at': modified_date.isoformat()
            })
        
        # Sort by creation date (newest first)
        patient_folders.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return {
            "success": True,
            "patient_folders": patient_folders,
            "total_patients": len(patient_folders),
            "source": "local_test_data",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "source": "local_test_data",
            "timestamp": datetime.now().isoformat()
        }

@api_router.post("/add-patient")
async def add_patient_with_ai_analysis(request: PatientData):
    """
    Add patient with AI-powered clinical analysis using Perplexity API.
    Provides intelligent filtering and prioritized treatment recommendations.
    Follows the same response pattern as text-query for consistent frontend handling.
    """
    try:
        # Convert Pydantic model to dict
        patient_dict = request.dict()
        
        print(f"🧠 Processing patient data with AI...")
        print(f"🔍 Patient dict keys: {list(patient_dict.keys())}")
        
        # Process using the AI patient service (matches your other service patterns)
        result = ai_patient_service.process_patient_with_ai(patient_dict)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Patient processing failed: {result['error']}"
            )
        
        print(f"✅ Patient processed successfully")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Endpoint error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@api_router.post("/new-session")
async def create_new_session():
    """Create a new clinical session for the user."""
    try:
        result = session_service.create_new_session()
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {
            "rag_system": "operational",
            "treatment_recommendations": "operational", 
            "ai_summarization": "operational",
            "patient_management": "operational with AI" if intelligent_analyzer else "operational without AI",
            "session_management": "operational"
        }
    }


# Include the API router in the main app
app.include_router(api_router)


# ============================================================================
# UI ROUTES
# ============================================================================

@app.get("/")
async def serve_docpilot_ui():
    """Serve the DocPilot UI"""
    html_file = "index.html"
    
    if os.path.exists(html_file):
        return FileResponse(html_file, media_type="text/html")
    else:
        return {
            "message": "DocPilot Clinical AI Assistant API",
            "version": "1.0.0",
            "status": "Running",
            "ui_file": "index.html not found - place it in the same directory as main.py",
            "api_docs": "/docs",
            "endpoints": {
                "/api/text-query": "Clinical queries with AI",
                "/api/summarize": "AI data summarization",
                "/api/add-patient": "Add patient with AI analysis",
                "/api/new-session": "Create new session",
                "/api/health": "Health check"
            }
        }


@app.get("/{path:path}")
async def catch_all_routes(path: str):
    """Serve index.html for SPA routing, exclude API routes"""
    
    if path.startswith(("api/", "docs", "openapi.json", "static/")):
        raise HTTPException(status_code=404, detail="Route not found")
    
    if os.path.exists("index.html"):
        return FileResponse("index.html", media_type="text/html")
    else:
        raise HTTPException(status_code=404, detail="UI file not found")


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Endpoint not found", "status_code": 404}


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"error": "Internal server error", "status_code": 500}


# ============================================================================
# MAIN APPLICATION RUNNER
# ============================================================================

if __name__ == "__main__":
    print("🏥 Starting DocPilot Clinical AI Assistant...")
    print("📁 Looking for index.html in current directory")
    print("🌐 UI will be available at: http://localhost:8000")
    print("📚 API documentation at: http://localhost:8000/docs")
    print("🔗 API endpoints at: http://localhost:8000/api/*")
    print("")
    print("📋 Available API Endpoints:")
    print("   • POST /api/text-query     - Clinical queries with AI-powered RAG")
    print("   • POST /api/summarize      - AI clinical data summarization")
    print("   • POST /api/add-patient    - Add patient with AI analysis")
    print("   • POST /api/new-session    - Create new clinical session")
    print("   • GET  /api/health         - System health check")
    print("")
    print("🚀 Starting server...")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
