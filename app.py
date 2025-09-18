import streamlit as st
import PyPDF2
from docx import Document
from docx.enum.text import WD_COLOR_INDEX
import io
import re
import fitz  # PyMuPDF, PDF işaretleme için eklendi

# Aranacak olan özel klozların listesi
TARGET_CLAUSES = [
    "Total Asbestos Exclusion Clause",
    "CL380 Institute Cyber Attack Exclusion",
    "LMA5394 Communicable Disease Exclusion",
    "NMA 2738 Claims Control Clause",
    "LMA3100 Sanction Limitation and Exclusion Clause"
]

def extract_text_from_pdf(file_content):
    """
    Yüklenen PDF dosyasının içeriğini metin olarak çıkarır.
    """
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
        return text
    except Exception as e:
        st.error(f"PDF dosyası okunurken bir hata oluştu: {e}")
        return None

def extract_text_from_docx(file_content):
    """
    Yüklenen DOCX dosyasının içeriğini metin olarak çıkarır.
    """
    try:
        doc = Document(io.BytesIO(file_content))
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        st.error(f"DOCX dosyası okunurken bir hata oluştu: {e}")
        return None

def highlight_clauses_in_pdf(file_content, clauses_to_find):
    """
    Verilen PDF içeriğinde belirtilen klozları bulur ve sarı renkle işaretler.
    İşaretlenmiş PDF'in byte verisini döndürür.
    """
    try:
        pdf_doc = fitz.open(stream=file_content, filetype="pdf")
        for page in pdf_doc:
            for clause in clauses_to_find:
                # Metin örneklerini (koordinatları) bul
                text_instances = page.search_for(clause)
                # Bulunan her örneği işaretle
                for inst in text_instances:
                    highlight = page.add_highlight_annot(inst)
                    highlight.update()
        
        output_buffer = io.BytesIO()
        pdf_doc.save(output_buffer)
        pdf_doc.close()
        return output_buffer.getvalue()
    except Exception as e:
        st.error(f"PDF dosyası işaretlenirken bir hata oluştu: {e}")
        return None

def highlight_clauses_in_docx(file_content, clauses_to_find):
    """
    Verilen DOCX içeriğinde belirtilen klozları bulur ve klozun geçtiği paragrafı sarı renkle işaretler.
    İşaretlenmiş DOCX'in byte verisini döndürür.
    """
    try:
        doc = Document(io.BytesIO(file_content))
        clauses_lower = [c.lower() for c in clauses_to_find]

        for para in doc.paragraphs:
            # Eğer paragraf metni aranan klozlaran birini içeriyorsa
            if any(clause in para.text.lower() for clause in clauses_lower):
                # Paragraftaki tüm metin parçalarını (run) sarı ile işaretle
                for run in para.runs:
                    run.font.highlight_color = WD_COLOR_INDEX.YELLOW
        
        output_buffer = io.BytesIO()
        doc.save(output_buffer)
        return output_buffer.getvalue()
    except Exception as e:
        st.error(f"DOCX dosyası işaretlenirken bir hata oluştu: {e}")
        return None

def find_and_highlight_clauses_for_html(text, clauses_to_find):
    """
    Metin içinde belirtilen klozları arar ve HTML'de göstermek için <mark> ile işaretler.
    Bulunan klozların bir listesini ve HTML için işaretlenmiş metni döndürür.
    """
    found_clauses = []
    highlighted_text = text
    text_lower = text.lower()

    for clause in clauses_to_find:
        if clause.lower() in text_lower:
            found_clauses.append(clause)
            pattern = re.compile(re.escape(clause), re.IGNORECASE)
            highlighted_text = pattern.sub(lambda match: f"<mark>{match.group(0)}</mark>", highlighted_text)
            
    return found_clauses, highlighted_text

# --- Streamlit Arayüzü ---

st.set_page_config(page_title="Poliçe Kloz Analiz Aracı", layout="wide")

st.title("📑 Poliçe Kloz Analiz Aracı")
st.markdown("""
Bu araç, yüklediğiniz poliçe dosyalarında (.pdf veya .docx) aşağıda listelenen özel klozların bulunup bulunmadığını kontrol eder. 
Bulunan klozlar listelenir, belge içinde önizlenir ve **işaretlenmiş dosyanın yeni bir kopyasını indirebilirsiniz.**
""")

st.subheader("Aranacak Klozlar Listesi")
for clause in TARGET_CLAUSES:
    st.info(clause)

# Dosya yükleme alanı
uploaded_file = st.file_uploader(
    "Lütfen analiz edilecek poliçe dosyasını (.pdf, .docx) sürükleyip bırakın veya seçin.",
    type=["pdf", "docx"]
)

if uploaded_file is not None:
    # 'session_state' kullanarak dosyanın tekrar tekrar işlenmesini önle
    if 'processed_file' not in st.session_state or st.session_state.processed_file != uploaded_file.name:
        st.session_state.processed_file = uploaded_file.name
        
        file_content = uploaded_file.read()
        file_name = uploaded_file.name
        document_text = ""

        with st.spinner(f"'{file_name}' dosyası işleniyor... Lütfen bekleyin."):
            if file_name.lower().endswith('.pdf'):
                document_text = extract_text_from_pdf(file_content)
            elif file_name.lower().endswith('.docx'):
                document_text = extract_text_from_docx(file_content)
        
        st.session_state.document_text = document_text
        st.session_state.file_content = file_content

    # Eğer metin başarıyla çıkarıldıysa sonuçları göster
    if st.session_state.document_text:
        file_name = uploaded_file.name
        document_text = st.session_state.document_text
        file_content = st.session_state.file_content
        
        found_clauses, highlighted_html_text = find_and_highlight_clauses_for_html(document_text, TARGET_CLAUSES)

        st.success(f"'{file_name}' dosyası başarıyla analiz edildi.")
        st.markdown("---")
        
        st.header("🔍 Analiz Sonuçları")

        col1, col2 = st.columns([1, 2])

        with col1:
            if found_clauses:
                st.subheader("✅ Belgede Bulunan Klozlar")
                for clause in found_clauses:
                    st.markdown(f"- **{clause}**")

                st.markdown("---")
                
                # --- İNDİRME BUTONU BÖLÜMÜ ---
                st.subheader("⬇️ İşaretli Dosyayı İndir")
                
                highlighted_file_bytes = None
                
                if file_name.lower().endswith('.pdf'):
                    with st.spinner("PDF dosyası işaretleniyor..."):
                        highlighted_file_bytes = highlight_clauses_in_pdf(file_content, found_clauses)
                elif file_name.lower().endswith('.docx'):
                    with st.spinner("DOCX dosyası işaretleniyor..."):
                        highlighted_file_bytes = highlight_clauses_in_docx(file_content, found_clauses)

                if highlighted_file_bytes:
                    st.download_button(
                        label="İndirmek için tıklayın",
                        data=highlighted_file_bytes,
                        file_name=f"isaretli_{file_name}",
                        mime=uploaded_file.type
                    )
                else:
                    st.error("Dosya işaretlenirken bir sorun oluştu.")

            else:
                st.warning("Listelenen klozların hiçbiri bu belgede bulunamadı.")
        
        with col2:
            st.subheader("📑 Belge İçeriği Önizlemesi")
            st.markdown(f'<div style="background-color:#f0f2f6; border: 1px solid #ddd; border-radius: 5px; padding: 15px; height: 600px; overflow-y: scroll;">{highlighted_html_text.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)

