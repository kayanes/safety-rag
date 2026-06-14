import re
import json

class ParserService:
    @staticmethod
    def extract_hara_table(markdown_text: str):
        """
        Extracts the markdown table from the text and converts it to a list of dicts.
        Handles both well-formed tables and tables that were word-wrapped across multiple lines.
        """
        # Find the start of the table
        match = re.search(r'(\|\s*(?:사고\s*)?ID.*)', markdown_text, re.DOTALL | re.IGNORECASE)
        if not match:
            return []
            
        table_text = match.group(1).strip()
        # The table usually ends with a double newline
        table_text = re.split(r'\n\s*\n', table_text)[0]
        
        # Flatten all text to overcome wrapped lines
        flat_text = table_text.replace('\n', ' ')
        
        # Split by |
        cells = [c.strip() for c in flat_text.split('|')]
        # Filter out empty cells (edges padding) and Markdown separator lines (e.g. '---')
        cells = [c for c in cells if c and not re.match(r'^[-: ]+$', c)]
        
        if not cells:
            return []
            
        # The headers should be the first 18 cells based on the prompt
        header_count = 18
        headers = cells[:header_count]
        data_cells = cells[header_count:]
        
        results = []
        for i in range(0, len(data_cells), header_count):
            row_cells = data_cells[i:i+header_count]
            if not row_cells:
                break
                
            # Pad or truncate values to match headers length
            if len(row_cells) < header_count:
                row_cells.extend([""] * (header_count - len(row_cells)))
                
            row = dict(zip(headers, row_cells))
            
            # Normalize keys to match frontend expectation (HaraRow interface)
            # Map headers robustly by checking for substrings since LLM might generate slightly different table headers
            
            def get_val(keywords):
                for k, v in row.items():
                    if any(kw.lower() in k.lower() for kw in keywords):
                        return v
                return ""
                
            normalized_row = {
                "id": get_val(["사고 ID", "ID"]),
                "function": get_val(["Function", "기능", "Functional group", "Feature"]),
                "malfunction": get_val(["Mal function", "오작동", "Malfunction"]),
                "consequences": get_val(["Consequences", "고려된 시나리오", "Scenario"]),
                "severity": get_val(["S", "Severity"]),
                "exposure": get_val(["E", "Exposure"]),
                "controllability": get_val(["C", "Controllability"]),
                "asil": get_val(["ASIL"]),
                "safetyGoal": get_val(["Safety Goal", "안전 목표"]),
                "safeState": get_val(["Safe State", "안전 상태"]),
            }
            results.append(normalized_row)
        
        return results

    @staticmethod
    def check_structure(text: str):
        """
        Checks if the text contains the required 7 questions using Regex for robustness.
        """
        required_patterns = [
            r"질문\s*1", r"질문\s*2", r"질문\s*3", r"질문\s*4", 
            r"질문\s*5", r"질문\s*6", r"질문\s*7"
        ]
        
        # Check for presence of each question header
        matches = [re.search(p, text) for p in required_patterns]
        score = sum(1 for m in matches if m) / len(required_patterns)
        
        compliance = {
            "hasSituation": bool(re.search(r"질문\s*3", text)),
            "hasHazard": bool(re.search(r"질문\s*3", text) and re.search(r"위험원|Hazard", text, re.IGNORECASE)),
            "hasRiskAssessment": bool(re.search(r"질문\s*5", text) and re.search(r"S\(.*E\(.*C\(", text, re.DOTALL)), # S, E, C patterns
            "hasASIL": bool(re.search(r"ASIL", text)),
            "hasSafetyGoal": bool(re.search(r"질문\s*6", text)),
        }
        
        return {
            "score": score,
            "details": compliance
        }
