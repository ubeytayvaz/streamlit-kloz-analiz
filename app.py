import streamlit as st
import PyPDF2
from docx import Document
from docx.enum.text import WD_COLOR_INDEX
import io
import re
import fitz  # PyMuPDF

# Aranacak klozlar, Türkçe karşılıkları ve ilgili anahtar kelimeler
CLAUSE_DEFINITIONS = {
    "Total Asbestos Exclusion Clause": {
        "tr": "Total Asbest İstisnası Klozu",
        "keywords": ["asbestos", "asbest", "asbesto"]
    },
    "CL380 Institute Cyber Attack Exclusion": {
        "tr": "CL380 Siber Saldırı İstisnası Enstitü Klozu",
        "keywords": ["cyber", "siber", "CL380", "hacker", "bilgisayar virüsü", "computer virus", "cyber attack", "siber saldırı"]
    },
    "LMA5394 Communicable Disease Exclusion": {
        "tr": "LMA5394 Bulaşıcı Hastalık İstisnası Klozu",
        "keywords": ["communicable disease", "bulaşıcı hastalık", "LMA5394", "salgın", "epidemic", "pandemic", "pandemi"]
    },
    "NMA 2738 Claims Control Clause": {
        "tr": "NMA 2738 Hasar Kontrol Klozu",
        "keywords": ["claims control", "hasar kontrol", "NMA 2738", "claims"]
    },
    "LMA3100 Sanction Limitation and Exclusion Clause": {
        "tr": "LMA3100 Yaptırım Sınırlama ve İstisna Klozu",
        "keywords": ["sanction", "yaptırım", "LMA3100", "ambargo", "embargo", "limitation", "sınırlama"]
    }
}

def extract_text_from_pdf(file_content):
    """Yüklenen PDF dosyasının içeriğini metin olarak çıkarır."""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        st.error(f"PDF dosyası okunurken bir hata oluştu: {e}")
        return None

def extract_text_from_docx(file_content):
    """Yüklenen DOCX dosyasının içeriğini metin olarak çıkarır."""
    try:
        doc = Document(io.BytesIO(file_content))
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        st.error(f"DOCX dosyası okunurken bir hata oluştu: {e}")
        return None

def analyze_document_text(text, clause_definitions):
    """
    Metin içinde klozları ve ilgili anahtar kelimeleri arar.
    Bulunan eşleşmelerin detaylı bir listesini döndürür.
    """
    found_items = []
    # Cümleleri daha iyi ayırmak için temel bir regex
    sentences = re.split(r'(?<=[.!?])\s+', text)
    processed_texts = set()

    for en_clause, details in clause_definitions.items():
        # 1. Kloz adlarının tam eşleşmelerini ara (İngilizce ve Türkçe)
        for clause_name in [en_clause, details.get("tr", "")]:
            if not clause_name: continue
            pattern = re.compile(re.escape(clause_name), re.IGNORECASE)
            for match in pattern.finditer(text):
                found_text = match.group(0).strip()
                if found_text.lower() not in processed_texts:
                    found_items.append({
                        "clause": en_clause,
                        "found_text": found_text,
                        "reason": f"Tam eşleşme bulundu."
                    })
                    processed_texts.add(found_text.lower())

        # 2. Cümleler içinde anahtar kelimeleri ara
        for keyword in details.get("keywords", []):
            if not keyword: continue
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
            for sentence in sentences:
                if pattern.search(sentence):
                    clean_sentence = sentence.strip()
                    if clean_sentence.lower() not in processed_texts:
                        found_items.append({
                            "clause": en_clause,
                            "found_text": clean_sentence,
                            "reason": f"İlgili anahtar kelime: '{keyword}'"
                        })
                        processed_texts.add(clean_sentence.lower())
    
    return found_items

def create_highlighted_html(full_text, found_items):
    """HTML önizlemesi için bulunan metinleri <mark> ile işaretler."""
    highlighted_text = full_text
    # Daha uzun metinlerin (cümlelerin) önce işaretlenmesi için sırala
    sorted_items = sorted(found_items, key=lambda x: len(x['found_text']), reverse=True)
    
    for item in sorted_items:
        pattern = re.compile(re.escape(item['found_text']), re.IGNORECASE)
        # Zaten işaretlenmiş bir metnin içinde tekrar işaretleme yapmaktan kaçın
        highlighted_text = pattern.sub(lambda match: f"<mark>{match.group(0)}</mark>" if "<mark>" not in match.group(0) else match.group(0), highlighted_text)

    return highlighted_text

def highlight_text_in_pdf(file_content, texts_to_highlight):
    """PDF dosyasında belirtilen metinleri sarı ile işaretler."""
    try:
        pdf_doc = fitz.open(stream=file_content, filetype="pdf")
        for page in pdf_doc:
            for text in texts_to_highlight:
                text_instances = page.search_for(text)
                for inst in text_instances:
                    highlight = page.add_highlight_annot(inst)
                    highlight.update()
        
        output_buffer = io.BytesIO()
        pdf_doc.save(output_buffer)
        pdf_doc.close()
        return output_buffer.getvalue()
    except Exception as e:
        st.error(f"PDF işaretlenirken hata: {e}")
        return None

def highlight_text_in_docx(file_content, texts_to_highlight):
    """DOCX dosyasında belirtilen metinleri içeren paragrafları sarı ile işaretler."""
    try:
        doc = Document(io.BytesIO(file_content))
        texts_lower = [t.lower() for t in texts_to_highlight]

        for para in doc.paragraphs:
            para_lower = para.text.lower()
            if any(text_to_find.lower() in para_lower for text_to_find in texts_to_highlight):
                for run in para.runs:
                    run.font.highlight_color = WD_COLOR_INDEX.YELLOW
        
        output_buffer = io.BytesIO()
        doc.save(output_buffer)
        return output_buffer.getvalue()
    except Exception as e:
        st.error(f"DOCX işaretlenirken hata: {e}")
        return None

# --- Streamlit Arayüzü ---

st.set_page_config(page_title="Gelişmiş Poliçe Kloz Analiz Aracı", layout="wide")

st.title("📑 Gelişmiş Poliçe Kloz Analiz Aracı")
st.markdown("""
Bu araç, poliçe dosyalarınızı (.pdf, .docx) analiz ederek belirli klozları ve ilgili anahtar kelimeleri (Türkçe/İngilizce) içeren cümleleri tespit eder.
""")

with st.expander("Analiz Edilen Klozlar ve Anahtar Kelimeleri Gör"):
    for clause, details in CLAUSE_DEFINITIONS.items():
        st.info(f"**{clause}**")
        st.markdown(f"**Anahtar Kelimeler:** `{'`, `'.join(details['keywords'])}`")

uploaded_file = st.file_uploader(
    "Lütfen analiz edilecek poliçe dosyasını seçin.",
    type=["pdf", "docx"]
)

if uploaded_file is not None:
    if 'processed_file' not in st.session_state or st.session_state.processed_file != uploaded_file.name:
        st.session_state.processed_file = uploaded_file.name
        
        file_content = uploaded_file.read()
        
        with st.spinner(f"'{uploaded_file.name}' içeriği okunuyor..."):
            if uploaded_file.name.lower().endswith('.pdf'):
                document_text = extract_text_from_pdf(file_content)
            else:
                document_text = extract_text_from_docx(file_content)
        
        st.session_state.document_text = document_text
        st.session_state.file_content = file_content
    
    if st.session_state.document_text:
        file_name = uploaded_file.name
        document_text = st.session_state.document_text
        file_content = st.session_state.file_content

        with st.spinner("Belge analiz ediliyor..."):
            found_items = analyze_document_text(document_text, CLAUSE_DEFINITIONS)
        
        st.success(f"'{file_name}' analizi tamamlandı. {len(found_items)} potansiyel bulgu tespit edildi.")
        st.markdown("---")
        
        st.header("🔍 Analiz Sonuçları")

        col1, col2 = st.columns([1, 2])

        with col1:
            if found_items:
                st.subheader("✅ Tespit Edilen Bulgular")
                
                # Gruplama için
                grouped_results = {}
                for item in found_items:
                    if item['clause'] not in grouped_results:
                        grouped_results[item['clause']] = []
                    grouped_results[item['clause']].append(item)

                for clause, items in grouped_results.items():
                    with st.expander(f"İlgili Kloz: {clause} ({len(items)} bulgu)"):
                        for item in items:
                            st.markdown(f"**Sebep:** {item['reason']}")
                            st.info(f"*{item['found_text']}*")
                
                st.markdown("---")
                st.subheader("⬇️ İşaretli Dosyayı İndir")
                
                texts_to_highlight = [item['found_text'] for item in found_items]
                highlighted_file_bytes = None
                
                with st.spinner("Dosya işaretleniyor..."):
                    if file_name.lower().endswith('.pdf'):
                        highlighted_file_bytes = highlight_text_in_pdf(file_content, texts_to_highlight)
                    else:
                        highlighted_file_bytes = highlight_text_in_docx(file_content, texts_to_highlight)

                if highlighted_file_bytes:
                    st.download_button(
                        label="İndirmek için tıklayın",
                        data=highlighted_file_bytes,
                        file_name=f"isaretli_{file_name}",
                        mime=uploaded_file.type
                    )
            else:
                st.warning("Listelenen klozlar veya ilgili anahtar kelimeler bu belgede bulunamadı.")
        
        with col2:
            st.subheader("📑 Belge İçeriği Önizlemesi")
            highlighted_html = create_highlighted_html(document_text, found_items)
            st.markdown(f'<div style="background-color:#f0f2f6; border: 1px solid #ddd; border-radius: 5px; padding: 15px; height: 600px; overflow-y: scroll;">{highlighted_html.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)

