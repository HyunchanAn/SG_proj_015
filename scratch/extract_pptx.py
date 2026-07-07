import zipfile
import xml.etree.ElementTree as ET
import re
import os

pptx_path = r'E:\Github\260707_SG_AI를_이용한_피착재_분석_및_매칭과_제품_역설계_통합_서비스_개발.pptx'
output_path = r'E:\Github\SG_proj_015\scratch\pptx_extracted.txt'

def extract_pptx_text(pptx_p, out_p):
    with zipfile.ZipFile(pptx_p, 'r') as zip_ref:
        # Find all slide files
        slide_files = [f for f in zip_ref.namelist() if re.match(r'ppt/slides/slide\d+\.xml', f)]
        # Sort them by slide number
        slide_files.sort(key=lambda x: int(re.findall(r'\d+', x)[0]))
        
        with open(out_p, 'w', encoding='utf-8') as out_f:
            out_f.write(f"=== Extraction of {os.path.basename(pptx_p)} ===\n")
            out_f.write(f"Total Slides: {len(slide_files)}\n\n")
            
            for slide_file in slide_files:
                slide_num = re.findall(r'\d+', slide_file)[0]
                out_f.write(f"\n=========================================\n")
                out_f.write(f"SLIDE {slide_num} ({slide_file})\n")
                out_f.write(f"=========================================\n")
                
                xml_content = zip_ref.read(slide_file)
                root = ET.fromstring(xml_content)
                
                # To group text by shape or paragraph
                # Elements that usually contain text in pptx slides:
                # p:sp (shape) -> p:txBody (text body) -> a:p (paragraph) -> a:r (run) -> a:t (text)
                
                # Let's find all paragraphs (a:p) first
                # Namespace URI maps
                ns = {
                    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
                    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'
                }
                
                # Iterate through all elements. If it is a paragraph (a:p or p:p), collect its runs.
                # Or simply walk the tree and print structural elements
                for shape in root.findall('.//p:sp', ns):
                    txBody = shape.find('.//p:txBody', ns)
                    if txBody is not None:
                        for paragraph in txBody.findall('.//a:p', ns):
                            line_texts = []
                            for run in paragraph.findall('.//a:r', ns):
                                t = run.find('.//a:t', ns)
                                if t is not None and t.text:
                                    line_texts.append(t.text)
                            # Also check for simple text fields without runs
                            fld = paragraph.findall('.//a:fld', ns)
                            for f in fld:
                                t = f.find('.//a:t', ns)
                                if t is not None and t.text:
                                    line_texts.append(t.text)
                                    
                            line_str = "".join(line_texts).strip()
                            if line_str:
                                out_f.write(line_str + "\n")
                        out_f.write("\n") # Blank line between shapes

if __name__ == '__main__':
    extract_pptx_text(pptx_path, output_path)
    print(f"Successfully extracted text to {output_path}")
