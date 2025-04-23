import os
import json
import base64
import time
import io
import datetime
from typing import Dict, Any, List, Union, Optional
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError
from PIL import Image
import fitz  

class MedicalReportAnalyzer:
    
    def __init__(self, api_key: str = None, model_name: str = "gemini-2.0-flash"):
        
        self.api_key = api_key or os.environ.get('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("No API key provided.")
            
        self.model_name = model_name
        self.rate_limit = {'requests': 0, 'reset_time': time.time(), 'max_rpm': 60}
        self._configure_genai()
        
    def _configure_genai(self) -> None:
        """Configure the Gemini API with credentials."""
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
    
    def _rate_limit_check(self) -> None:
        
        current_time = time.time()
        # Reset counter if a minute has passed
        if current_time - self.rate_limit['reset_time'] >= 60:
            self.rate_limit['requests'] = 0
            self.rate_limit['reset_time'] = current_time
        
        # If we've hit the limit, wait until the next minute
        if self.rate_limit['requests'] >= self.rate_limit['max_rpm']:
            sleep_time = 60 - (current_time - self.rate_limit['reset_time'])
            if sleep_time > 0:
                print(f"Rate limit reached. Waiting {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
                self.rate_limit['requests'] = 0
                self.rate_limit['reset_time'] = time.time()
        
        # Increment request counter
        self.rate_limit['requests'] += 1
    
    def analyze_report(self, file_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a medical report file and return structured data.
        Returns:
            Dictionary with the structured analysis of the report
        """
        # Generate default output path if not provided
        if not output_path:
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            output_path = f"{base_name}_analysis.json"
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            content = self._process_pdf(file_path)
        elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']:
            content = self._process_image(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        analysis_result = self._analyze_with_gemini(content)
        
        self._save_results(analysis_result, output_path)
        
        return analysis_result
    
    def _process_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract content from PDF files for analysis.
        Optimized for efficiency with Flash-Lite.
        
        Returns:
            List of content parts for Gemini to process
        """
        content = []
        
        # Open the PDF file
        pdf_document = fitz.open(pdf_path)
        
        # For efficiency, limit to first 10 pages for free tier
        max_pages = min(len(pdf_document), 10)
        
        for page_num in range(max_pages):
            page = pdf_document[page_num]
            
            # Extract text from page
            text = page.get_text()
            if text.strip():
                content.append({"text": f"Page {page_num+1}: {text}"})
            
            # Extract images from page, but limit resolution for free tier efficiency
            images = self._extract_images_from_page(page, max_images=3)
            content.extend(images)
        
        pdf_document.close()
        return content
    
    def _extract_images_from_page(self, page, max_images=3) -> List[Dict[str, Any]]:
        """
        Extract images from a PDF page with optimizations for Flash-Lite.
        Returns:
            List of image content for Gemini
        """
        images = []
        image_list = page.get_images(full=True)
        
        # Limit number of images for rate limit and token efficiency
        for img_index, img_info in enumerate(image_list[:max_images]):
            xref = img_info[0]
            base_image = page.parent.extract_image(xref)
            
            if base_image:
                image_bytes = base_image["image"]
                try:
                    # Create a PIL Image from bytes
                    img = Image.open(io.BytesIO(image_bytes))
                    
                    # Resize large images to reduce token usage
                    img = self._optimize_image_size(img)
                    
                    # Convert optimized image back to bytes
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format=img.format if hasattr(img, 'format') and img.format else 'PNG')
                    optimized_bytes = img_byte_arr.getvalue()
                    
                    images.append({
                        "inline_data": {
                            "data": base64.b64encode(optimized_bytes).decode('utf-8'),
                            "mime_type": f"image/{base_image['ext']}"
                        }
                    })
                except Exception as e:
                    print(f"Error processing image {img_index} from PDF: {e}")
        
        return images
    
    def _optimize_image_size(self, img):
        """
        Optimize image size for Flash-Lite to reduce token usage.
        Returns:
            Resized PIL Image object
        """
        width, height = img.size
        
        # Target max dimension of 800px for Flash-Lite efficiency
        max_dimension = 800
        
        if width > max_dimension or height > max_dimension:
            # Calculate new dimensions while maintaining aspect ratio
            if width > height:
                new_width = max_dimension
                new_height = int(height * (max_dimension / width))
            else:
                new_height = max_dimension
                new_width = int(width * (max_dimension / height))
            
            # Resize image
            img = img.resize((new_width, new_height), Image.LANCZOS)
        
        return img
    
    def _process_image(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Process an image file for analysis with optimizations for Flash-Lite.
        Returns:
            List with image content for Gemini
        """
        try:
            img = Image.open(image_path)
            
            # Optimize image size for Flash-Lite
            img = self._optimize_image_size(img)
            
            # Convert image to bytes
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format=img.format if hasattr(img, 'format') and img.format else 'PNG')
            img_bytes = img_byte_arr.getvalue()
            
            # Prepare for Gemini
            mime_type = f"image/{img.format.lower() if hasattr(img, 'format') and img.format else 'png'}"
            
            return [{
                "inline_data": {
                    "data": base64.b64encode(img_bytes).decode('utf-8'),
                    "mime_type": mime_type
                }
            }]
        except Exception as e:
            raise ValueError(f"Error processing image: {e}")
    
    def _analyze_with_gemini(self, content: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send the content to Gemini Flash-Lite API for analysis.
        Returns:
            Structured analysis of the medical report
        """
        try:
            # Check rate limits before making API call
            self._rate_limit_check()
            
            
            # Prompt for the Gemini model - optimized for Flash-Lite's more direct approach
            prompt = """
            Extract structured data from this medical report with these fields:
            - patient_info: {name, age, gender, id}
            - dates: {test_date, report_date}
            - provider: {name, credentials}
            - test: {name, type}
            - results: [{parameter, value, reference_range, flag}]
            - abnormal_findings: [{abnormalitites}]
            Analyze the interpretations and provide the following:
             - Diagnosis: [detailed diagnosis of the interpretations from the extracted results] 
             - Medical Suggestions: [medical suggestions based on diagnosis]
             - Treatment: [suggested treatment according to medical standards with list of medicines]
             - Medications: [list of suggested medicines. else return 'None']
            Format as clean JSON.
            """
            
            # Add prompt to content
            full_content = [{"text": prompt}] + content
            
            # Generate response from Gemini with efficient settings for Flash-Lite
            generation_config = {
                "temperature": 0.1,  
                "max_output_tokens": 2048, 
            }
            
            response = self.model.generate_content(
                full_content, 
                generation_config=generation_config
            )
            
            # Parse response
            try:
                
                result = json.loads(response.text)
            except json.JSONDecodeError:
               
                import re
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response.text)
                if json_match:
                    try:
                        result = json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        result = {
                            "raw_analysis": response.text,
                            "processed_date": datetime.datetime.now().isoformat(),
                            "note": "Failed to parse JSON from response"
                        }
                else:
                    # Create a structured format if no JSON found
                    result = {
                        "raw_analysis": response.text,
                        "processed_date": datetime.datetime.now().isoformat()
                    }
            
            return result
            
        except GoogleAPIError as e:
            return {"error": f"Gemini API error: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error during analysis: {str(e)}"}
    
    def _save_results(self, results: Dict[str, Any], output_path: str) -> None:
        """
        Save analysis results to a JSON file.

        """
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # Write the results to a JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
                
            print(f"Results saved to {output_path}")
        except Exception as e:
            print(f"Error saving results: {e}")
    



def analyze_medical_report(file_path: str, output_path: str = None, api_key: str = None):
    """
    Simplified function to analyze a medical report.
   
    Returns:
        Dictionary with the analysis results
    """
    analyzer = MedicalReportAnalyzer(api_key)
    results = analyzer.analyze_report(file_path, output_path)
    return results


# Simple function to batch process multiple reports
def batch_analyze_medical_reports(directory_path: str, output_dir: str = "analysis_results", api_key: str = None):
    """
    Simplified function to analyze multiple medical reports.
    
    Returns:
        List of dictionaries with analysis results
    """
    analyzer = MedicalReportAnalyzer(api_key)
    results = analyzer.batch_process(directory_path, output_dir)
    return results


def analyzer_main(file_path):

    file_path = file_path 
    output_path = "output/Analysis.json"  
    api_key = os.getenv("API_KEY")  
    
    try:

        results = analyze_medical_report(file_path, output_path, api_key)
        print(f"Analysis completed successfully!")
    except Exception as e:
        print(f"Error analyzing report: {e}")

    