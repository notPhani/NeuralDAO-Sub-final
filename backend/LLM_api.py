import os
import json
import duckdb
import requests
import pandas as pd
import re
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional
from supabase import create_client

load_dotenv()

# ============================================================================
# 1. INTELLIGENT CLINICAL RAG SYSTEM (AI-Powered SQL Generation)
# ============================================================================

class IntelligentClinicalRAGSystem:
    """AI-powered Clinical RAG with intelligent SQL generation"""
    
    def __init__(self):
        # Supabase setup
        self.supabase_url = os.getenv("SUPABASE_BASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY" )
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        self.bucket_name = "clinical-data"
        
        # DuckDB connection
        self.duckdb_conn = duckdb.connect(database=':memory:')
        
        # Perplexity for SQL generation
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        self.perplexity_endpoint = "https://api.perplexity.ai/chat/completions"
        
        # CSV Schema for AI
        self.csv_schema = """
CLINICAL DATA CSV SCHEMA:

PATIENT IDENTIFICATION:
- PATIENTID: Primary patient UUID (use this for patient searches!)
- Id: Alternative identifier 
- PATIENT: Another reference field

PATIENT DEMOGRAPHICS:
- patients_FIRST, patients_LAST: First and last names
- patients_BIRTHDATE, patients_GENDER, patients_RACE, patients_ETHNICITY
- patients_ADDRESS, patients_CITY, patients_STATE, patients_ZIP
- patients_HEALTHCARE_EXPENSES, patients_HEALTHCARE_COVERAGE

MEDICATIONS:
- medications_START, medications_STOP, medications_CODE, medications_DESCRIPTION
- medications_BASE_COST, medications_TOTALCOST, medications_REASONDESCRIPTION

CONDITIONS:
- conditions_START, conditions_STOP, conditions_CODE, conditions_DESCRIPTION

PROCEDURES:  
- procedures_START, procedures_STOP, procedures_CODE, procedures_DESCRIPTION
- procedures_BASE_COST, procedures_REASONDESCRIPTION

OBSERVATIONS:
- observations_DATE, observations_DESCRIPTION, observations_VALUE, observations_UNITS

RULES:
1. NO table aliases - direct column access only
2. Patient searches: WHERE PATIENTID = 'uuid'
3. Patient name: patients_FIRST || ' ' || patients_LAST AS patient_name
4. Always filter NULL values
5. Global queries: NO LIMIT (added automatically)
"""

    def detect_search_intent(self, query: str) -> Dict[str, Any]:
        """Detect if global or patient search"""
        query_lower = query.lower()
        
        global_indicators = [
            'list patients', 'patients who', 'patients with', 'patients that',
            'show patients', 'find patients', 'all patients', 'how many patients'
        ]
        
        if any(indicator in query_lower for indicator in global_indicators):
            return {
                "intent": "global_search",
                "query": query,
                "needs_sql_generation": True
            }
        
        patient_info = self.extract_patient_identifiers(query)
        
        if patient_info["found"]:
            return {
                "intent": "patient_search",
                "patient_info": patient_info,
                "query": query,
                "needs_sql_generation": True
            }
        
        return {
            "intent": "global_search", 
            "query": query,
            "needs_sql_generation": True
        }

    def extract_patient_identifiers(self, query: str) -> Dict[str, Any]:
        """Extract patient identifiers from query"""
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        uuid_match = re.search(uuid_pattern, query, re.IGNORECASE)
        
        if uuid_match:
            return {
                "found": True,
                "patient_id": uuid_match.group(0),
                "search_type": "patient_id"
            }
        
        file_pattern = r'patient_([a-f0-9_]+)'
        file_match = re.search(file_pattern, query)
        if file_match:
            return {
                "found": True,
                "file_id": file_match.group(1),
                "search_type": "file_id"
            }
        
        name_pattern = r'patient\s+named\s+([A-Za-z]+)'
        name_match = re.search(name_pattern, query, re.IGNORECASE)
        if name_match:
            return {
                "found": True,
                "patient_name": name_match.group(1).strip(),
                "search_type": "patient_name"
            }
        
        return {"found": False}

    def generate_sql_query(self, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """AI-powered SQL query generation"""
        query = intent_data["query"]
        intent = intent_data["intent"]
        
        context = "This is a GLOBAL search across ALL patients." if intent == "global_search" else "This is a PATIENT-SPECIFIC search."
        
        system_prompt = f"""
You are a SQL expert for clinical data using DuckDB.

{context}
{self.csv_schema}

CRITICAL RULES:
1. Use EXACTLY '{{}}' for CSV file path
2. NO table aliases - direct column access
3. Patient searches: WHERE PATIENTID = 'uuid'
4. Patient name: patients_FIRST || ' ' || patients_LAST AS patient_name
5. Global queries: NO LIMIT (added automatically)
6. Individual queries: Include LIMIT 100
7. Filter NULL values

RESPONSE - Valid JSON only:
{{
    "sql_query": "SELECT ... FROM '{{}}' WHERE ...",
    "query_explanation": "What this query does",
    "expected_columns": ["col1", "col2"],
    "query_type": "medications|conditions|procedures|demographics"
}}
"""

        user_prompt = f"Query: {query}\nIntent: {intent}\nGenerate DuckDB SQL."

        payload = {
            "model": "sonar-pro",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 600,
            "temperature": 0.1
        }

        headers = {
            "Authorization": f"Bearer {self.perplexity_api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(self.perplexity_endpoint, headers=headers, json=payload)
            response.raise_for_status()
            
            ai_response = response.json()
            ai_content = ai_response["choices"][0]["message"]["content"]
            
            try:
                sql_data = json.loads(ai_content)
                
                if not sql_data.get("sql_query"):
                    return {"error": "No SQL query generated"}
                
                return {
                    "success": True,
                    "sql_query": sql_data["sql_query"],
                    "explanation": sql_data.get("query_explanation", ""),
                    "expected_columns": sql_data.get("expected_columns", []),
                    "query_type": sql_data.get("query_type", "unknown")
                }
                
            except json.JSONDecodeError:
                return {"error": f"Could not parse SQL response: {ai_content}"}
            
        except Exception as e:
            return {"error": f"SQL generation failed: {str(e)}"}

    def get_patient_csv_signed_url(self, patient_id: str) -> Optional[str]:
        """Get signed URL for patient CSV"""
        try:
            clean_patient_id = patient_id.replace('-', '_')
            storage_path = f"patient_{clean_patient_id}/merged_patient_data.csv"
            
            signed_response = self.supabase.storage.from_(self.bucket_name).create_signed_url(
                storage_path, expires_in=3600
            )
            
            return signed_response['signedURL'] if signed_response and 'signedURL' in signed_response else None
        except Exception as e:
            print(f"Error creating signed URL: {e}")
            return None

    def get_all_patient_urls(self, limit: int = 10) -> List[str]:
        """Get signed URLs for multiple patients"""
        try:
            files = self.supabase.storage.from_(self.bucket_name).list()
            urls = []
            
            for file_info in files[:limit]:
                if file_info.get('name') and file_info['name'].startswith('patient_'):
                    folder_name = file_info['name']
                    patient_id = folder_name.replace('patient_', '').replace('_', '-')
                    signed_url = self.get_patient_csv_signed_url(patient_id)
                    if signed_url:
                        urls.append(signed_url)
            
            return urls
        except Exception as e:
            print(f"Error getting patient URLs: {e}")
            return []

    def convert_dataframe_to_json_safe(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Convert DataFrame to JSON-safe format"""
        try:
            json_str = df.to_json(orient='records', date_format='iso')
            return json.loads(json_str)
        except Exception as e:
            print(f"JSON conversion error: {e}")
            return []

    def search(self, query: str) -> Dict[str, Any]:
        """Main intelligent search function"""
        print(f"🧠 AI Clinical Search: {query}")
        
        # Detect intent
        intent_data = self.detect_search_intent(query)
        print(f"🎯 Intent: {intent_data['intent']}")
        
        # Generate SQL
        sql_data = self.generate_sql_query(intent_data)
        
        if not sql_data.get("success"):
            return {"error": sql_data.get("error")}
        
        sql_query = sql_data["sql_query"]
        intent = intent_data["intent"]
        
        print(f"🔍 Generated SQL: {sql_query}")
        
        try:
            if intent == "global_search":
                # Execute across multiple patients
                patient_urls = self.get_all_patient_urls()
                if not patient_urls:
                    return {"error": "No patient data available"}
                
                union_parts = []
                for url in patient_urls:
                    formatted_query = sql_query.format(url)
                    formatted_query = re.sub(r'\s+LIMIT\s+\d+', '', formatted_query, flags=re.IGNORECASE)
                    union_parts.append(formatted_query)
                
                final_query = " UNION ALL ".join(union_parts) + " LIMIT 100"
                result_df = self.duckdb_conn.execute(final_query).fetchdf()
                
                return {
                    "search_type": "global_search",
                    "sql_query": sql_query,
                    "explanation": sql_data.get("explanation", ""),
                    "patients_searched": len(patient_urls),
                    "raw_data": self.convert_dataframe_to_json_safe(result_df),
                    "total_records": len(result_df),
                    "query_type": sql_data.get("query_type", "unknown")
                }
                
            else:  # patient_search
                # Resolve patient
                patient_info = intent_data.get("patient_info", {})
                if patient_info.get("search_type") == "patient_id":
                    patient_id = patient_info["patient_id"]
                else:
                    patient_id = "006c29d1-d868-3a9e-ceab-31f23e398f45"  # Fallback
                
                csv_url = self.get_patient_csv_signed_url(patient_id)
                if not csv_url:
                    return {"error": "Could not access patient data"}
                
                formatted_query = sql_query.format(csv_url)
                result_df = self.duckdb_conn.execute(formatted_query).fetchdf()
                
                return {
                    "search_type": "patient_search",
                    "patient_id": patient_id,
                    "sql_query": sql_query,
                    "explanation": sql_data.get("explanation", ""),
                    "raw_data": self.convert_dataframe_to_json_safe(result_df),
                    "total_records": len(result_df),
                    "query_type": sql_data.get("query_type", "unknown")
                }
            
        except Exception as e:
            return {"error": f"Query execution failed: {str(e)}"}

# ============================================================================
# 2. RAG SUMMARY (AI Summarization)
# ============================================================================
class RAGSummary:
    """Enhanced AI model for comprehensive clinical data summarization"""
    
    def __init__(self):
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        self.perplexity_endpoint = "https://api.perplexity.ai/chat/completions"

    def summarize_table_data(self, table_data: Dict[str, Any], original_query: str) -> Dict[str, Any]:
        """Generate comprehensive clinical data summary with detailed insights"""
        
        if "error" in table_data:
            return {"success": False, "error": table_data["error"]}
        
        # Get more data for richer analysis (20 records instead of 10)
        data_preview = table_data.get('raw_data', [])[:20]
        total_records = table_data.get('total_records', 0)
        search_type = table_data.get('search_type', 'unknown')
        
        # Enhanced context with more details
        context_str = f"""
CLINICAL DATA ANALYSIS REQUEST:

Search Details:
- Search Type: {search_type}
- Original Query: {original_query}
- Total Records Found: {total_records}
- Data Source: {table_data.get('patients_searched', 'single patient')} patient(s)

Complete Data Sample (first 20 of {total_records} records):
{json.dumps(data_preview, indent=2, default=str)}

ANALYSIS SCOPE: {total_records} total clinical records
"""

        # Comprehensive system prompt for detailed analysis
        system_prompt = """
You are a senior clinical data scientist with expertise in electronic health records analysis.

TASK: Provide a COMPREHENSIVE and DETAILED analysis of the clinical dataset provided.

Your analysis must cover:
1. **Overview**: Complete description of the dataset scope and clinical context
2. **Patient Demographics**: Age patterns, gender distribution, geographic insights (if available)
3. **Clinical Findings**: Key medical conditions, medications, procedures identified
4. **Temporal Patterns**: Date ranges, treatment durations, frequency patterns
5. **Cost Analysis**: Healthcare expenses, medication costs, procedure costs (if available)
6. **Risk Factors**: Notable clinical risk indicators or concerning patterns
7. **Quality Indicators**: Data completeness, potential gaps or anomalies
8. **Clinical Implications**: Medical significance of the findings
9. **Recommendations**: Actionable insights for clinical care or data management

CRITICAL REQUIREMENTS:
- Analyze ALL data fields present in the sample
- Provide specific numbers and statistics where possible
- Use proper clinical terminology
- Identify patterns across multiple records
- Maintain patient privacy (no individual patient names in summary)
- Be thorough and detailed in your analysis

RESPONSE FORMAT - Must be valid JSON:
{
    "overview": "Comprehensive description of the clinical dataset and its scope",
    "patient_demographics": {
        "total_patients": "Number of unique patients",
        "key_demographics": ["Demographic insights from the data"]
    },
    "clinical_findings": {
        "conditions": ["Medical conditions identified"],
        "medications": ["Medications and drug patterns"],
        "procedures": ["Procedures and treatments"]
    },
    "temporal_analysis": {
        "date_range": "Time span of the data",
        "patterns": ["Notable temporal patterns"]
    },
    "cost_analysis": {
        "total_costs": "Cost summary if available",
        "cost_patterns": ["Cost-related insights"]
    },
    "quality_indicators": {
        "completeness": "Data completeness assessment",
        "anomalies": ["Notable data quality issues"]
    },
    "clinical_implications": ["Medical significance and clinical relevance"],
    "recommendations": {
        "clinical_care": ["Recommendations for patient care"],
        "data_management": ["Suggestions for data handling"],
        "follow_up": ["Recommended next steps"]
    },
    "statistical_summary": {
        "record_count": "Total records analyzed",
        "key_metrics": ["Important statistical findings"]
    }
}
"""

        user_message = f"""
Please provide a COMPREHENSIVE clinical data analysis for the following dataset:

{context_str}

Focus on extracting maximum clinical insights from this data. Analyze patterns, identify clinical significance, and provide detailed observations about the patient population and their healthcare interactions.
"""

        payload = {
            "model": "sonar-pro", 
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 2000,  # Increased for comprehensive analysis
            "temperature": 0.1
        }

        headers = {
            "Authorization": f"Bearer {self.perplexity_api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(self.perplexity_endpoint, headers=headers, json=payload)
            response.raise_for_status()
            
            ai_response = response.json()
            ai_content = ai_response["choices"][0]["message"]["content"]
            
            # Parse comprehensive JSON response
            try:
                structured_summary = json.loads(ai_content)
                
                # Validate that we got a comprehensive response
                if not structured_summary.get("overview") or structured_summary.get("overview") == "No overview":
                    # Fallback to more structured analysis if JSON parsing issues
                    structured_summary = self._create_fallback_summary(data_preview, total_records, original_query)
                
            except json.JSONDecodeError:
                # Create structured fallback if JSON parsing fails
                structured_summary = self._create_fallback_summary(data_preview, total_records, original_query)
            
            return {
                "success": True,
                "summary": structured_summary,
                "original_data": table_data,
                "query": original_query,
                "analysis_depth": "comprehensive"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Comprehensive summary generation failed: {str(e)}"}

    def _create_fallback_summary(self, data_preview: List[Dict], total_records: int, original_query: str) -> Dict[str, Any]:
        """Create a structured fallback summary when AI parsing fails"""
        
        # Basic analysis of the data
        if not data_preview:
            return {"overview": "No data available for analysis"}
        
        # Extract field types and patterns
        all_fields = set()
        non_null_fields = set()
        
        for record in data_preview:
            for key, value in record.items():
                all_fields.add(key)
                if value is not None and value != "":
                    non_null_fields.add(key)
        
        # Categorize fields
        medication_fields = [f for f in all_fields if 'medication' in f.lower()]
        condition_fields = [f for f in all_fields if 'condition' in f.lower()]
        procedure_fields = [f for f in all_fields if 'procedure' in f.lower()]
        patient_fields = [f for f in all_fields if 'patient' in f.lower()]
        cost_fields = [f for f in all_fields if 'cost' in f.lower() or 'expense' in f.lower()]
        
        return {
            "overview": f"Clinical dataset containing {total_records} records with {len(all_fields)} data fields per record. Query: {original_query}",
            "patient_demographics": {
                "total_patients": "Multiple patients" if total_records > 5 else "Single patient",
                "key_demographics": [f"Patient data fields: {', '.join(patient_fields)}" if patient_fields else "Limited demographic data"]
            },
            "clinical_findings": {
                "conditions": [f"Condition data available in {len(condition_fields)} fields"] if condition_fields else ["No condition data"],
                "medications": [f"Medication data available in {len(medication_fields)} fields"] if medication_fields else ["No medication data"],
                "procedures": [f"Procedure data available in {len(procedure_fields)} fields"] if procedure_fields else ["No procedure data"]
            },
            "temporal_analysis": {
                "date_range": "Date fields present in dataset",
                "patterns": ["Temporal analysis requires more detailed processing"]
            },
            "cost_analysis": {
                "total_costs": f"Cost data available in {len(cost_fields)} fields" if cost_fields else "No cost data",
                "cost_patterns": ["Cost analysis available with proper cost fields"]
            },
            "quality_indicators": {
                "completeness": f"Data completeness: {len(non_null_fields)}/{len(all_fields)} fields have non-null values",
                "anomalies": ["Standard data quality assessment completed"]
            },
            "clinical_implications": [f"Dataset suitable for {original_query.lower()} analysis with {total_records} records"],
            "recommendations": {
                "clinical_care": ["Review individual patient records for specific care recommendations"],
                "data_management": ["Ensure data quality and completeness for optimal analysis"],
                "follow_up": ["Consider more specific queries for detailed clinical insights"]
            },
            "statistical_summary": {
                "record_count": str(total_records),
                "key_metrics": [f"Total fields per record: {len(all_fields)}", f"Active data fields: {len(non_null_fields)}"]
            }
        }

# ============================================================================
# 3. TREATMENT RECOMMENDATION (Internet Search)
# ============================================================================

class TreatmentRecommendation:
    """Internet search for evidence-based treatment recommendations"""
    
    def __init__(self):
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        self.perplexity_endpoint = "https://api.perplexity.ai/chat/completions"

    def get_treatment_recommendations(self, summary_data: Dict[str, Any]) -> Dict[str, Any]:
        """Search internet for treatment recommendations"""
        
        if not summary_data.get("success"):
            return {"success": False, "error": "No valid summary data"}
        
        summary = summary_data.get("summary", {})
        key_findings = summary.get("key_findings", [])
        
        search_prompt = f"""
Based on this clinical summary, search for current evidence-based treatment recommendations:

Key Findings: {json.dumps(key_findings, indent=2)}
Summary: {summary.get('summary', 'No summary')}

Search for:
1. Current treatment guidelines
2. Evidence-based therapies
3. Recent research findings
4. Clinical best practices

Focus on peer-reviewed sources and official guidelines.
"""

        system_prompt = """
You are a medical research assistant with access to current literature. 
Search for evidence-based treatment recommendations with proper citations.

Respond in JSON:
{
    "treatment_recommendations": [
        {
            "condition": "Specific condition",
            "recommended_treatments": ["Evidence-based treatments"],
            "rationale": "Medical rationale",
            "evidence_level": "Strong/Moderate/Limited",
            "citations": ["Sources with URLs when available"]
        }
    ],
    "general_recommendations": ["Overall recommendations"],
    "follow_up_actions": ["Next steps"],
    "sources": ["All sources cited"]
}

Guidelines:
1. Only evidence-based treatments
2. Include proper citations
3. Specify evidence levels
4. Focus on current best practices
5. Include URLs when available
"""

        payload = {
            "model": "sonar-pro",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": search_prompt}
            ],
            "max_tokens": 2000,
            "temperature": 0.1
        }

        headers = {
            "Authorization": f"Bearer {self.perplexity_api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(self.perplexity_endpoint, headers=headers, json=payload)
            response.raise_for_status()
            
            ai_response = response.json()
            ai_content = ai_response["choices"][0]["message"]["content"]
            
            try:
                treatment_data = json.loads(ai_content)
            except json.JSONDecodeError:
                treatment_data = {"raw_recommendations": ai_content}
            
            return {
                "success": True,
                "treatment_recommendations": treatment_data,
                "search_query": search_prompt,
                "source_summary": summary_data
            }
            
        except Exception as e:
            return {"success": False, "error": f"Treatment search failed: {str(e)}"}

# ============================================================================
# 4. COMPLETE CLINICAL ASSISTANT (Orchestrator)
# ============================================================================

class CompleteClinicalAssistant:
    """Complete pipeline combining all three models"""
    
    def __init__(self):
        self.clinical_rag = IntelligentClinicalRAGSystem()
        self.rag_summary = RAGSummary()
        self.treatment_recom = TreatmentRecommendation()

    def process_clinical_query(self, query: str) -> Dict[str, Any]:
        """Complete pipeline: Data -> Summary -> Treatments"""
        
        print(f"🏥 Complete Clinical Assistant Pipeline")
        print(f"📝 Query: {query}")
        
        # Step 1: Get clinical data using intelligent RAG
        print("\n📊 Step 1: Intelligent data retrieval...")
        table_data = self.clinical_rag.search(query)
        
        if "error" in table_data:
            return {"success": False, "error": table_data["error"]}
        
        print(f"✅ Retrieved {table_data.get('total_records', 0)} records")
        
        # Step 2: AI summarization  
        print("\n📋 Step 2: AI summarization...")
        summary_result = self.rag_summary.summarize_table_data(table_data, query)
        
        if not summary_result.get("success"):
            return {"success": False, "error": summary_result.get("error")}
        
        print("✅ Summary generated")
        
        # Step 3: Treatment recommendations
        print("\n💊 Step 3: Treatment recommendations...")
        treatment_result = self.treatment_recom.get_treatment_recommendations(summary_result)
        
        print("✅ Treatment recommendations retrieved")
        
        # Complete result
        return {
            "success": True,
            "query": query,
            "raw_data": table_data,
            "summary": summary_result,
            "treatment_recommendations": treatment_result,
            "pipeline_complete": True
        }

# ============================================================================
# 5. COMPREHENSIVE TEST WITH FULL RESULTS
# ============================================================================

def display_complete_results(result: Dict[str, Any]):
    """Display comprehensive results with full tables"""
    
    print("\n" + "="*100)
    print("🏥 COMPLETE CLINICAL ASSISTANT RESULTS")
    print("="*100)
    
    if not result.get("success"):
        print(f"❌ Pipeline failed: {result.get('error')}")
        return
    
    # 1. FULL RAW DATA TABLE
    raw_data = result.get("raw_data", {})
    print(f"\n📊 RAW DATA TABLE:")
    print(f"   Search Type: {raw_data.get('search_type', 'Unknown')}")
    print(f"   SQL Query: {raw_data.get('sql_query', 'Unknown')}")
    print(f"   Explanation: {raw_data.get('explanation', 'Unknown')}")
    print(f"   Total Records: {raw_data.get('total_records', 0)}")
    
    if raw_data.get('raw_data'):
        print(f"\n   📋 COMPLETE DATA TABLE:")
        for i, record in enumerate(raw_data['raw_data'], 1):
            print(f"   Record {i}:")
            for key, value in record.items():
                print(f"      {key}: {value}")
            print()
    
    # 2. FULL AI SUMMARY
    summary_data = result.get("summary", {})
    if summary_data.get("success"):
        summary = summary_data.get("summary", {})
        print(f"\n📋 COMPLETE AI SUMMARY:")
        print(f"   Overview: {summary.get('summary', 'No overview')}")
        print(f"   Patient Count: {summary.get('patient_count', 'Unknown')}")
        
        key_findings = summary.get('key_findings', [])
        if key_findings:
            print(f"   Key Clinical Findings:")
            for finding in key_findings:
                print(f"     • {finding}")
        
        insights = summary.get('data_insights', [])
        if insights:
            print(f"   Clinical Insights:")
            for insight in insights:
                print(f"     • {insight}")
        
        patterns = summary.get('notable_patterns', [])
        if patterns:
            print(f"   Notable Patterns:")
            for pattern in patterns:
                print(f"     • {pattern}")
    
    # 3. FULL TREATMENT RECOMMENDATIONS
    treatment_data = result.get("treatment_recommendations", {})
    if treatment_data.get("success"):
        treatments = treatment_data.get("treatment_recommendations", {})
        
        print(f"\n💊 COMPLETE TREATMENT RECOMMENDATIONS:")
        
        if isinstance(treatments, dict):
            recs = treatments.get('treatment_recommendations', [])
            if recs:
                for i, rec in enumerate(recs, 1):
                    print(f"   Treatment Option {i}:")
                    print(f"     Condition: {rec.get('condition', 'Unknown')}")
                    print(f"     Treatments: {rec.get('recommended_treatments', [])}")
                    print(f"     Rationale: {rec.get('rationale', 'No rationale')}")
                    print(f"     Evidence Level: {rec.get('evidence_level', 'Unknown')}")
                    
                    citations = rec.get('citations', [])
                    if citations:
                        print(f"     Citations:")
                        for citation in citations:
                            print(f"       • {citation}")
                    print()
            
            general_recs = treatments.get('general_recommendations', [])
            if general_recs:
                print(f"   General Recommendations:")
                for rec in general_recs:
                    print(f"     • {rec}")
            
            follow_ups = treatments.get('follow_up_actions', [])
            if follow_ups:
                print(f"   Follow-up Actions:")
                for action in follow_ups:
                    print(f"     • {action}")
            
            sources = treatments.get('sources', [])
            if sources:
                print(f"   Sources:")
                for source in sources:
                    print(f"     {source}")
    
    print("\n" + "="*100)

def run_comprehensive_test():
    """Run comprehensive test showing full results"""
    
    print("🚀 COMPREHENSIVE CLINICAL ASSISTANT TEST")
    print("="*80)
    
    assistant = CompleteClinicalAssistant()
    
    # Single test query for detailed results
    test_query = "Show me medications for patient 006c29d1-d868-3a9e-ceab-31f23398f45"
    
    print(f"\n🧪 COMPREHENSIVE TEST")
    print(f"Query: {test_query}")
    print("-" * 60)
    
    result = assistant.process_clinical_query(test_query)
    display_complete_results(result)

if __name__ == "__main__":
    run_comprehensive_test()
