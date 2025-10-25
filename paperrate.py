import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="Total Paper Evaluation", layout="wide")
st.title("📄 Total Paper Evaluation (CRUD + Professional PDF)")

# Initialize session state
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=[
        "Paper Type","Paper Size","Paper GSM","Paper Rate",
        "Paper Cut Size","Rim Size","Billbook","Total Paper",
        "Req Paper","Total Amount","Printing","Binding","Final Total"
    ])
if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

cut_options = {
    "Full Sheet (1)":1, "Half (1/2)":2, "A4 (1/4)":4, "A5 (1/5)":5,
    "A6 (1/6)":6, "A8 (1/8)":8, "A10 (1/10)":10, "A12 (1/12)":12
}

# --- Form ---
edit_idx = st.session_state.edit_index
if edit_idx is not None:
    row = st.session_state.data.loc[edit_idx]
else:
    row = {col: "" for col in st.session_state.data.columns}

with st.form("paper_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        paper_type = st.text_input("Paper Type", value=row["Paper Type"])
        paper_size = st.text_input("Paper Size", value=row["Paper Size"])
        paper_gsm = st.number_input("Paper GSM", min_value=0, value=int(row["Paper GSM"] or 0))
        paper_rate = st.number_input("Paper Rate (₹)", min_value=0.0, value=float(row["Paper Rate"] or 0.0))
    with col2:
        paper_cut_default = row["Paper Cut Size"] if row["Paper Cut Size"] else "A4 (1/4)"
        paper_cut = st.selectbox("Paper Cut Size", options=list(cut_options.keys()),
                                 index=list(cut_options.keys()).index(paper_cut_default))
        rim_size = st.number_input("Rim Size (sheets/rim)", min_value=1, value=int(row["Rim Size"] or 1))
        billbook = st.text_input("Billbook/Register/Pad", value=row["Billbook"])
        total_paper = st.number_input("Total Paper", min_value=0, value=int(row["Total Paper"] or 0))
    with col3:
        printing = st.number_input("Printing (₹)", min_value=0.0, value=float(row["Printing"] or 0.0))
        binding = st.number_input("Binding (₹)", min_value=0.0, value=float(row["Binding"] or 0.0))
        submit_label = "Update Entry" if edit_idx is not None else "Add Paper Entry"
        submit = st.form_submit_button(submit_label)

# --- Add / Update ---
if submit:
    cut_value = cut_options[paper_cut]
    req_paper = total_paper * (1 / cut_value)
    total_amount = (paper_rate / rim_size) * req_paper
    final_total = total_amount + printing + binding

    new_row = {
        "Paper Type": paper_type, "Paper Size": paper_size, "Paper GSM": paper_gsm, "Paper Rate": paper_rate,
        "Paper Cut Size": paper_cut, "Rim Size": rim_size, "Billbook": billbook, "Total Paper": total_paper,
        "Req Paper": round(req_paper,2), "Total Amount": round(total_amount,2),
        "Printing": printing, "Binding": binding, "Final Total": round(final_total,2)
    }

    if edit_idx is not None:
        st.session_state.data.loc[edit_idx] = new_row
        st.session_state.edit_index = None
        st.success("Row updated successfully!")
    else:
        st.session_state.data = pd.concat([st.session_state.data,pd.DataFrame([new_row])], ignore_index=True)
        st.success("Entry added successfully!")

# --- Table with Edit/Delete buttons ---
st.subheader("🗂️ Entries")
df = st.session_state.data.copy()
if not df.empty:
    for i, r in df.iterrows():
        cols = st.columns(len(r)+2)
        for j, val in enumerate(r):
            cols[j].write(val)
        if cols[-2].button("Edit", key=f"edit_{i}"):
            st.session_state.edit_index = i
        if cols[-1].button("Delete", key=f"del_{i}"):
            st.session_state.data.drop(i, inplace=True)
            st.session_state.data.reset_index(drop=True, inplace=True)
            st.success("Row deleted!")

# --- Professional PDF download ---
st.subheader("⬇️ Download Professional PDF Report")

def create_pdf_report(df):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    elements = []
    styles = getSampleStyleSheet()
    title = Paragraph("Total Paper Evaluation Report", styles['Title'])
    elements.append(title)
    elements.append(Paragraph(" ", styles['Normal']))  # Spacer

    # Prepare data for table
    data = [df.columns.tolist()] + df.values.tolist()
    table = Table(data, repeatRows=1)

    # Add style
    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.whitesmoke, colors.lightgrey])
    ])
    table.setStyle(style)
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer

if not st.session_state.data.empty:
    pdf_buffer = create_pdf_report(st.session_state.data)
    st.download_button("Download PDF", pdf_buffer, "Total_Paper_Evaluation_Report.pdf", "application/pdf")
else:
    st.info("No data to generate PDF.")
