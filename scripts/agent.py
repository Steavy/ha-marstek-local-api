import os
import requests
import pdfplumber
import ollama
import sys
from pathlib import Path

def main():
    # 1. Download de Marstek PDF
    pdf_url = os.getenv("PDF_URL")
    print(f"Ophalen PDF: {pdf_url}")
    r = requests.get(pdf_url)
    with open("marstek_spec.pdf", "wb") as f:
        f.write(r.content)
    
    # 2. PDF tekst extraheren
    print("PDF analyseren...")
    full_spec_text = ""
    with pdfplumber.open("marstek_spec.pdf") as pdf:
        for page in pdf.pages:
            full_spec_text += page.extract_text() or ""

    # 3. Definieer de doelbestanden op basis van je screenshot
    # We focussen op de bestanden waar de data-definities in staan
    base_folder = Path("custom_components/marstek_local_api")
    files_to_update = ["api.py", "const.py", "sensor.py", "binary_sensor.py"]
    
    found_any = False

    for filename in files_to_update:
        file_path = base_folder / filename
        
        if not file_path.exists():
            print(f"Skipping: {filename} niet gevonden in {base_folder}")
            continue
            
        found_any = True
        print(f"--- AI analyseert nu: {filename} ---")
        
        with open(file_path, "r") as f:
            old_code = f.read()

        # We geven Llama 3 een duidelijke opdracht
        prompt = f"""
        Context: Update a Home Assistant integration for Marstek devices.
        Task: Compare the Python code with the Marstek Open API Rev 2 specs.
        
        SPEC DATA FROM PDF:
        {full_spec_text[:5000]}
        
        CURRENT PYTHON CODE ({filename}):
        {old_code}

        Instructions:
        - Add new registers, fix units, or update device mappings found in Rev 2.
        - Do not explain anything. 
        - Return ONLY the raw Python code.
        - If no changes are needed for this file, return the original code.
        """

        try:
            response = ollama.chat(model='llama3.2:3b', messages=[
                {'role': 'user', 'content': prompt},
            ])
            
            new_code = response['message']['content'].strip()
            
            # Opschonen van eventuele markdown backticks
            if new_code.startswith("```"):
                lines = new_code.splitlines()
                if lines[0].startswith("```"): lines = lines[1:]
                if lines[-1].startswith("```"): lines = lines[:-1]
                new_code = "\n".join(lines)

            with open(file_path, "w") as f:
                f.write(new_code)
            print(f"Check: {filename} is bijgewerkt.")
            
        except Exception as e:
            print(f"Fout bij {filename}: {e}")

    if not found_any:
        print("FOUT: Geen van de doelbestanden gevonden! Check je mappenstructuur.")
        sys.exit(1)

if __name__ == "__main__":
    main()