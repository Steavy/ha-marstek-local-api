import os
import requests
import pdfplumber
import ollama

def extract_api_info(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

def main():
    # 1. Download PDF
    pdf_url = os.getenv("PDF_URL")
    r = requests.get(pdf_url)
    with open("MarstekDeviceOpenApi.pdf", "wb") as f:
        f.write(r.content)
    
    # 2. Extract tekst
    api_spec = extract_api_info("MarstekDeviceOpenApi.pdf")
    
    # 3. Lees de huidige API code (bijv. de sensor mapping)
    file_path = "custom_components/marstek_local/const.py" # Pas aan naar behoefte
    with open(file_path, "r") as f:
        current_code = f.read()

    # 4. Vraag Llama 3 om de code te updaten
    prompt = f"""
    You are an expert Python developer for Home Assistant integrations.
    Compare the following Marstek API Rev 2 specification with the current Python code.
    Update the Python code to match the new specification (add new fields, fix registers).
    
    API SPECIFICATION:
    {api_spec[:4000]} # Beperk lengte voor context window
    
    CURRENT CODE:
    {current_code}
    
    Only return the updated Python code. No explanations.
    """

    response = ollama.chat(model='llama3.2:3b', messages=[
        {'role': 'user', 'content': prompt},
    ])

    updated_code = response['message']['content']

    # 5. Schrijf wijzigingen terug
    with open(file_path, "w") as f:
        f.write(updated_code)
    print("Code succesvol bijgewerkt door Llama 3.")

if __name__ == "__main__":
    main()