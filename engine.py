"""AI Engine for Atlantis Bot"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import GROQ_KEYS, HF_API_KEY

class AtlantisEngine:
    def __init__(self):
        self.keys = GROQ_KEYS
        self.key_index = 0
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.3-70b-versatile"
        self.vision_url = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
        
        self.session = requests.Session()
        retries = Retry(total=5, backoff_factor=2, status_forcelist=[502, 503, 504, 429])
        self.session.mount('https://', HTTPAdapter(max_retries=retries, pool_maxsize=10))

    def get_current_key(self):
        return self.keys[self.key_index].strip()

    def analyze_vision(self, img_data):
        """Analyze images"""
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        try:
            response = self.session.post(self.vision_url, headers=headers, data=img_data, timeout=60)
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', 'Unable to recognize')
                return str(result)
            return f"API Error: {response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def analyze_shipping_document(self, vision_result):
        """Analyze shipping documents with AI"""
        prompt = f"""Analyze this shipping document: "{vision_result}"

Provide:
**DOCUMENT TYPE:** [Bill of Lading/Invoice/etc]
**KEY INFO:** Main details visible
**CHECKLIST:** What's present/missing
**WARNINGS:** Issues to check
**NEXT STEPS:** What to do

Keep under 400 words."""
        return self.get_logic(prompt)

    def get_logic(self, text, context=None):
        """AI responses via Groq"""
        headers = {
            "Authorization": f"Bearer {self.get_current_key()}",
            "Content-Type": "application/json"
        }
        
        system_msg = """You are Atlantis AI, expert maritime logistics agent.
Be specific, concise (250-500 words), mention real companies, warn about hidden costs, 
and always state estimates may vary."""
        
        if context:
            system_msg += f"\n\nContext: {context}"
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": text}
            ],
            "temperature": 0.7,
            "max_tokens": 600
        }
        
        try:
            response = self.session.post(self.api_url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            elif response.status_code == 401:
                return "Invalid API key"
            elif response.status_code == 429:
                return "Rate limit. Wait and retry."
            return f"Error {response.status_code}"
        except Exception as e:
            print(f"[!] AI Error: {str(e)}")
            return "Error. Please retry."
