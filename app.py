import streamlit as st
import PyPDF2
from docx import Document
import io
import re

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

def find_and_highlight_clauses(text, clauses_to_find):
    """
    Metin içinde belirtilen klozları arar ve bulduklarını işaretler.
    Bulunan klozların bir listesini ve işaretlenmiş metni döndürür.
    """
    found_clauses = []
    highlighted_text = text

    # Büyük/küçük harf duyarsız arama yapmak için metnin bir kopyasını küçük harfe çevirelim
    text_lower = text.lower()

    for clause in clauses_to_find:
        if clause.lower() in text_lower:
            found_clauses.append(clause)
            # Klozu metin içinde işaretlemek için regex kullanalım (büyük/küçük harf duyarsız)
            # re.escape, kloz adındaki özel karakterlerin (varsa) sorun çıkarmasını engeller.
            pattern = re.compile(re.escape(clause), re.IGNORECASE)
            highlighted_text = pattern.sub(lambda match: f"<mark>{match.group(0)}</mark>", highlighted_text)
            
    return found_clauses, highlighted_text

# --- Streamlit Arayüzü ---

st.set_page_config(page_title="Poliçe Kloz Analiz Aracı", layout="wide")

st.title("📑 Poliçe Kloz Analiz Aracı")
st.markdown("""
Bu araç, yüklediğiniz poliçe dosyalarında (.pdf veya .docx) aşağıda listelenen özel klozların bulunup bulunmadığını kontrol eder. 
Bulunan klozlar hem bir liste halinde sunulur hem de belge metni içinde sarı renkle işaretlenir.
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
    # Dosya içeriğini oku
    file_content = uploaded_file.read()
    file_name = uploaded_file.name
    document_text = ""

    st.spinner(f"'{file_name}' dosyası işleniyor... Lütfen bekleyin.")

    # Dosya türüne göre metin çıkarma işlemi
    if file_name.lower().endswith('.pdf'):
        document_text = extract_text_from_pdf(file_content)
    elif file_name.lower().endswith('.docx'):
        document_text = extract_text_from_docx(file_content)

    if document_text:
        # Klozları bul ve metni işaretle
        found_clauses, highlighted_text = find_and_highlight_clauses(document_text, TARGET_CLAUSES)

        st.success(f"'{file_name}' dosyası başarıyla analiz edildi.")
        st.markdown("---")
        
        # Sonuçları gösterme
        st.header("🔍 Analiz Sonuçları")

        if found_clauses:
            st.subheader("✅ Belgede Bulunan Klozlar")
            for clause in found_clauses:
                st.markdown(f"- **{clause}**")
        else:
            st.warning("Listelenen klozların hiçbiri bu belgede bulunamadı.")

        # İşaretlenmiş metni bir expander içinde göster
        with st.expander("İşaretlenmiş Belge Metnini Görüntüle", expanded=True):
            st.markdown(f"### '{file_name}' Dosyasının İçeriği")
            # `unsafe_allow_html=True` kullanarak <mark> etiketinin çalışmasını sağlıyoruz
            st.markdown(f'<div style="background-color:#f0f2f6; border: 1px solid #ddd; border-radius: 5px; padding: 15px; height: 500px; overflow-y: scroll;">{highlighted_text.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
