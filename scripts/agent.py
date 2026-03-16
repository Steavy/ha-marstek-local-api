import os
import requests
import pdfplumber
import ollama
import sys

def main():
    # 1. Download PDF
    pdf_url = os.getenv("PDF_URL")
    print(f"Downloading PDF from {pdf_url}...")
    r = requests.get(pdf_url)
    with open("api_rev2.pdf", "wb") as f:
        f.write(r.content)
    
    # 2. Vind het juiste bestand
    # We zoeken naar de plek waar de sensoren of definities staan. 
    # In de Marstek Local API is dit vaak 'marstek_local_api/marstek_api.py' 
    # of vergelijkbaar. We proberen de meest logische kandidaat:
    possible_paths = [
        "marstek_local_api/marstek_api.py",
        "custom_components/marstek_local/const.py",
        "marstek_api.py"
    ]
    
    file_path = None
    for path in possible_paths:
        if os.path.exists(path):
            file_path = path
            break
    
    if not file_path:
        print("FOUT: Kon geen bronbestand vinden om te updaten!")
        print(f"Huidige bestanden in directory: {os.listdir('.')}")
        sys.exit(1)

    print(f"Bestand gevonden: {file_path}. AI analyse start nu...")

    # 3. Extract tekst uit PDF
    text = ""
    with pdfplumber.open("api_rev2.pdf") as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    
    # 4. Lees huidige code
    with open(file_path, "r") as f:
        current_code = f.read()

    # 5. Llama 3 Prompt
    prompt = f"""
    Update the following Python code based on the Marstek API Rev 2 specs.
    Focus on adding new registers or changing existing ones found in the PDF text.
    
    PDF DATA:
    {text[:3000]}
    
    CURRENT PYTHON CODE:
    {current_code}
    
    Return ONLY the full updated Python code.
    """

    response = ollama.chat(model='llama3.2:3b', messages=[
        {'role': 'user', 'content': prompt},
    ])

    # 6. Schrijf terug
    with open(file_path, "w") as f:
        f.write(response['message']['content'])
    
    print("Code succesvol geüpdatet.")

if __name__ == "__main__":
    main()