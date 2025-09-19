# LLM1.py - Perplexity Pro-Powered Clinical Analysis
import json
import uuid
import re
from typing import Dict, List, Any
from datetime import datetime
import requests


class IntelligentPatientAnalyzer:
    """Perplexity Pro-powered intelligent patient analyzer"""
    
    def __init__(self, perplexity_api_key: str):
        self.api_key = perplexity_api_key
        self.api_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {perplexity_api_key}",
            "Content-Type": "application/json"
        }
        print("✅ Perplexity Pro Clinical Analyzer initialized")
    
    def analyze_patient_data(self, patient_json: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze patient with Perplexity Pro for high-quality clinical analysis"""
        try:
            print(f"🔍 Analyzing patient with Perplexity Pro...")
            
            # Extract patient data
            personal = patient_json.get('personal_details', {})
            history = patient_json.get('medical_history', [])
            complaint = patient_json.get('current_complaint', 'No complaint')
            medications = patient_json.get('current_medications', [])
            vitals = patient_json.get('vital_signs', {})
            
            # Create clinical prompt
            clinical_prompt = self._create_clinical_prompt(personal, history, complaint, medications, vitals)
            
            # Get AI analysis from Perplexity Pro
            ai_response = self._call_perplexity_pro(clinical_prompt)
            
            # Parse the structured response
            parsed_analysis = self._parse_clinical_response(ai_response)
            
            return {
                "success": True,
                "patient_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "original_data": patient_json,
                "ai_analysis": parsed_analysis
            }
            
        except Exception as e:
            print(f"❌ Perplexity analysis error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _create_clinical_prompt(self, personal: Dict, history: List, complaint: str, medications: List, vitals: Dict) -> str:
        """Create a sophisticated clinical prompt for Perplexity Pro"""
        
        # Format patient data
        age = personal.get('age', 'Unknown')
        gender = personal.get('gender', 'Unknown')
        name = personal.get('name', 'Patient')
        
        history_str = '; '.join(history) if history else 'None'
        medications_str = '; '.join(medications) if medications else 'None'
        vitals_str = json.dumps(vitals) if vitals else 'Not provided'
        
        return f"""You are an expert emergency medicine physician analyzing a patient case. Provide intelligent clinical analysis with evidence-based recommendations.

PATIENT DATA:
- Age: {age} years old
- Gender: {gender}  
- Name: {name}
- Current Complaint: {complaint}
- Medical History: {history_str}
- Current Medications: {medications_str}
- Vital Signs: {vitals_str}

ANALYSIS REQUIREMENTS:
You must provide a structured clinical analysis that focuses ONLY on factors relevant to the current complaint. Use intelligent filtering to identify which medical history items matter and which should be ignored.

REQUIRED OUTPUT FORMAT:

CLINICAL PROBLEM:
[One clear sentence describing the primary clinical problem based on the complaint]

RELEVANT MEDICAL FACTORS:
[List only 2-3 medical history items that directly impact the current complaint, with explanations of WHY they matter]
- [Factor 1]: [Why it matters for current complaint]  
- [Factor 2]: [Why it matters for diagnosis/treatment]
- [Factor 3]: [Why it affects management]

IRRELEVANT FACTORS (FILTERED OUT):
[List medical history items that don't affect the current complaint and explain why they're excluded]
- [Condition]: [Why it doesn't matter for current complaint]

PRIORITY TREATMENT PLAN:
1. [Most urgent immediate action with specific details]
2. [Second priority intervention with clinical reasoning]  
3. [Third action or follow-up care with timeline]

DETAILED ACTION STEPS:
Step 1: [Specific diagnostic or therapeutic action with medical details]
Step 2: [Secondary intervention with clinical rationale]  
Step 3: [Follow-up care with specific timeline and monitoring]

FOLLOW-UP RECOMMENDATIONS:
- [Specific follow-up timeline based on condition severity]
- [Warning signs patient should watch for]  
- [When to return immediately or seek urgent care]
- [Specialist referrals if needed with timeline]

CLINICAL REASONING:
[Explain your filtering logic - why certain conditions were included/excluded based on the current complaint. Discuss how this intelligent filtering improves clinical decision-making and efficiency.]

Focus on evidence-based medicine. For trauma cases involving falls, consider fracture risk, imaging needs, pain management, and complications. For patients with diabetes, consider healing implications. For patients with metal implants, consider MRI contraindications.

Provide citations from reputable medical sources to support your recommendations."""

    def _call_perplexity_pro(self, prompt: str) -> str:
        """Call Perplexity Pro API for high-quality clinical analysis"""
        
        payload = {
            "model": "sonar-pro",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert emergency medicine and primary care physician with 20+ years of experience. Provide evidence-based clinical analysis with proper medical citations. Focus on intelligent clinical reasoning and efficient decision-making."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.1,  # Low temperature for consistent medical reasoning
            "top_p": 0.9,
            "search_domain_filter": ["ncbi.nlm.nih.gov", "mayoclinic.org", "aafp.org", "acep.org", "uptodate.com"],
            "return_citations": True
        }
        
        try:
            print("🔍 DEBUG: Calling Perplexity Pro API...")
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30)
            
            print(f"🔍 DEBUG: Response status: {response.status_code}")
            
            if response.status_code == 401:
                raise Exception("Invalid Perplexity API key - check your PERPLEXITY_API_KEY environment variable")
            elif response.status_code == 429:
                raise Exception("Perplexity API rate limit exceeded - please wait and try again")
            elif response.status_code != 200:
                raise Exception(f"Perplexity API error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            if 'choices' not in result or not result['choices']:
                raise Exception("Invalid API response format - no choices returned")
            
            content = result['choices'][0]['message']['content']
            print(f"🔍 DEBUG: Received {len(content)} characters from Perplexity")
            
            return content
            
        except requests.exceptions.Timeout:
            raise Exception("Perplexity API timeout - please try again")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error calling Perplexity API: {str(e)}")
        except Exception as e:
            raise Exception(f"Perplexity API call failed: {str(e)}")
    
    def _parse_clinical_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the structured clinical response from Perplexity"""
        
        try:
            sections = {}
            
            # Extract Clinical Problem
            problem_match = re.search(r'CLINICAL PROBLEM:\s*\n?(.*?)(?=\n\n|\nRELEVANT|\nIRRELEVANT)', response_text, re.DOTALL | re.IGNORECASE)
            sections["problem"] = problem_match.group(1).strip() if problem_match else "Clinical assessment pending"
            
            # Extract Relevant Factors
            relevant_match = re.search(r'RELEVANT MEDICAL FACTORS:\s*\n(.*?)(?=\nIRRELEVANT|\nPRIORITY)', response_text, re.DOTALL | re.IGNORECASE)
            if relevant_match:
                factors_text = relevant_match.group(1).strip()
                sections["relevant_factors"] = [
                    line.strip('- ').strip() for line in factors_text.split('\n') 
                    if line.strip() and line.strip().startswith('-')
                ]
            else:
                sections["relevant_factors"] = []
            
            # Extract Irrelevant Factors (what was filtered out)
            irrelevant_match = re.search(r'IRRELEVANT FACTORS.*?:\s*\n(.*?)(?=\nPRIORITY)', response_text, re.DOTALL | re.IGNORECASE)
            if irrelevant_match:
                irrelevant_text = irrelevant_match.group(1).strip()
                sections["excluded_factors"] = [
                    line.strip('- ').strip() for line in irrelevant_text.split('\n') 
                    if line.strip() and line.strip().startswith('-')
                ]
            else:
                sections["excluded_factors"] = []
            
            # Extract Priority Treatment Plan
            priority_match = re.search(r'PRIORITY TREATMENT PLAN:\s*\n(.*?)(?=\nDETAILED)', response_text, re.DOTALL | re.IGNORECASE)
            if priority_match:
                priority_text = priority_match.group(1).strip()
                sections["priority_order"] = [
                    re.sub(r'^\d+\.\s*', '', line.strip()) for line in priority_text.split('\n')
                    if line.strip() and re.match(r'^\d+\.', line.strip())
                ]
            else:
                sections["priority_order"] = []
            
            # Extract Detailed Action Steps
            action_match = re.search(r'DETAILED ACTION STEPS:\s*\n(.*?)(?=\nFOLLOW)', response_text, re.DOTALL | re.IGNORECASE)
            if action_match:
                action_text = action_match.group(1).strip()
                sections["action_plan"] = [
                    re.sub(r'^Step \d+:\s*', '', line.strip()) for line in action_text.split('\n')
                    if line.strip() and line.strip().startswith('Step')
                ]
            else:
                sections["action_plan"] = []
            
            # Extract Follow-up Recommendations
            followup_match = re.search(r'FOLLOW-UP RECOMMENDATIONS:\s*\n(.*?)(?=\nCLINICAL)', response_text, re.DOTALL | re.IGNORECASE)
            if followup_match:
                followup_text = followup_match.group(1).strip()
                sections["follow_up_recommendations"] = [
                    line.strip('- ').strip() for line in followup_text.split('\n')
                    if line.strip() and line.strip().startswith('-')
                ]
            else:
                sections["follow_up_recommendations"] = []
            
            # Extract Clinical Reasoning
            reasoning_match = re.search(r'CLINICAL REASONING:\s*\n(.*?)$', response_text, re.DOTALL | re.IGNORECASE)
            sections["filtering_rationale"] = reasoning_match.group(1).strip() if reasoning_match else "AI-powered clinical analysis completed"
            
            # Extract citations/references from the text
            citations = []
            citation_patterns = [
                r'https?://[^\s\)]+',
                r'www\.[^\s\)]+',
                r'\[.*?\]',
                r'Source:.*?\n'
            ]
            
            for pattern in citation_patterns:
                citations.extend(re.findall(pattern, response_text))
            
            sections["clinical_references"] = list(set(citations))[:5] if citations else [
                "https://www.aafp.org/afp/",
                "https://www.acep.org/clinical/",
                "https://www.mayoclinic.org/diseases-conditions/"
            ]
            
            sections["raw_ai_response"] = response_text
            
            print(f"✅ Successfully parsed clinical response with {len(sections)} sections")
            return sections
            
        except Exception as e:
            print(f"❌ Error parsing clinical response: {e}")
            return {
                "problem": "Clinical analysis completed (parsing error)",
                "relevant_factors": ["Manual review recommended"],
                "priority_order": ["Clinical assessment"],
                "action_plan": ["Comprehensive evaluation"],
                "follow_up_recommendations": ["Follow-up as clinically indicated"],
                "clinical_references": ["https://www.mayoclinic.org/"],
                "filtering_rationale": f"Response parsing error: {str(e)}",
                "raw_ai_response": response_text,
                "error": f"Parsing failed: {str(e)}"
            }
