# pdf_parser.py
import pdfplumber
import re
import statistics

def parse_pdf_to_markdown(pdf_path):
    """
    Parses a PDF using pdfplumber to intelligently extract text, tables, 
    and infer structure, converting it into clean Markdown.
    """
    markdown_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            all_font_sizes = []
            for page in pdf.pages:
                # Use extract_words to get detailed info about each character
                words = page.extract_words()
                for word in words:
                    all_font_sizes.append(word['size'])
            
            # Determine the most common font size as the body text
            if not all_font_sizes:
                body_font_size = 10 # Default fallback
            else:
                body_font_size = statistics.mode(all_font_sizes)

            for page in pdf.pages:
                # --- 1. Extract and Remove Tables ---
                table_texts = []
                tables = page.extract_tables()
                for table_data in tables:
                    table_data = [row for row in table_data if row is not None]
                    if not table_data: continue
                    
                    # Store the text of each cell to exclude it from regular text extraction
                    for row in table_data:
                        for cell in row:
                            if cell: table_texts.extend(cell.split())

                    # Format table into Markdown
                    header = [str(cell).replace('\n', ' ') if cell is not None else '' for cell in table_data[0]]
                    markdown_text += f"| {' | '.join(header)} |\n"
                    markdown_text += f"|{'|'.join(['---'] * len(header))}|\n"
                    for row in table_data[1:]:
                        cleaned_row = [str(cell).replace('\n', ' ') if cell is not None else '' for cell in row]
                        markdown_text += f"| {' | '.join(cleaned_row)} |\n"
                    markdown_text += "\n"

                # --- 2. Extract Structured Text ---
                # Re-extract words and filter out those that were part of tables
                words = page.extract_words(x_tolerance=1.5, y_tolerance=3, use_text_flow=True)
                
                # A very rough way to filter table text. More robust would be to use bounding boxes.
                words = [w for w in words if w['text'] not in table_texts]

                current_y = -1
                current_line = ""
                
                for word in words:
                    if word['top'] != current_y and current_y != -1:
                        # New line detected, process the previous line
                        processed_line = process_line(current_line.strip(), body_font_size)
                        markdown_text += processed_line
                        current_line = ""
                    
                    current_line += word['text'] + " "
                    current_y = word['top']
                
                # Process the last line on the page
                processed_line = process_line(current_line.strip(), body_font_size)
                markdown_text += processed_line + "\n"

    except Exception as e:
        print(f"Error processing PDF: {e}")
        return None

    # Final cleanup
    markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text.strip())
    return markdown_text

def process_line(line, body_font_size):
    """Helper function to format a single line of text into Markdown."""
    if not line:
        return ""

    # Simple heuristics for formatting
    # Note: This requires a PDF with good metadata. A more robust solution
    # would analyze font names and sizes from the word objects themselves.
    
    # List item detection
    if line.strip().startswith(('●', '•', '*', '-')):
        return f"* {line.strip()[1:].strip()}\n"
    if re.match(r'^\d+\.\s', line.strip()):
        return f"{line.strip()}\n"
    
    # Simple heading detection based on common patterns (can be improved)
    words = line.strip().split()
    if 1 <= len(words) <= 8 and not line.strip().endswith('.') and (line.strip() == line.strip().title() or line.strip() == line.strip().upper()):
         return f"\n## {line.strip()}\n\n"

    # Default to a paragraph
    return f"{line.strip()}\n"

