# pdf_parser.py
import pdfplumber
import re

def parse_pdf_to_markdown(pdf_path):
    """
    Parses a PDF using pdfplumber to intelligently extract text, tables, 
    and infer structure, converting it into clean Markdown.
    """
    markdown_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # --- Table Extraction ---
                tables = page.extract_tables()
                for table_data in tables:
                    table_data = [row for row in table_data if row is not None]
                    if not table_data:
                        continue
                    
                    header = [str(cell).replace('\n', ' ') if cell is not None else '' for cell in table_data[0]]
                    markdown_text += f"| {' | '.join(header)} |\n"
                    markdown_text += f"|{'|'.join(['---'] * len(header))}|\n"
                    
                    for row in table_data[1:]:
                        cleaned_row = [str(cell).replace('\n', ' ') if cell is not None else '' for cell in row]
                        markdown_text += f"| {' | '.join(cleaned_row)} |\n"
                    markdown_text += "\n"

                # --- Text Extraction ---
                # Extract text while trying to preserve layout for paragraph detection
                page_text = page.extract_text(x_tolerance=1, y_tolerance=3)
                if page_text:
                    markdown_text += page_text + "\n\n"

    except Exception as e:
        print(f"Error processing PDF: {e}")
        return None

    # --- Post-processing and Cleanup ---
    # Collapse excess newlines to a maximum of two
    markdown_text = re.sub(r'(\n\s*){3,}', '\n\n', markdown_text.strip())
    
    # Simple heuristic for headings (lines with few words, no period, and often sentence case)
    lines = markdown_text.split('\n')
    processed_lines = []
    for line in lines:
        stripped_line = line.strip()
        words = stripped_line.split()
        
        # Conditions for a line to be considered a heading
        is_short = 1 <= len(words) <= 8
        no_period = not stripped_line.endswith('.')
        is_title_case = stripped_line == stripped_line.title() or stripped_line == stripped_line.upper()

        if is_short and no_period and is_title_case:
            processed_lines.append(f"## {stripped_line}")
        else:
            processed_lines.append(line)
            
    # Re-join and clean up again
    final_text = "\n".join(processed_lines)
    return re.sub(r'\n{3,}', '\n\n', final_text).strip()

