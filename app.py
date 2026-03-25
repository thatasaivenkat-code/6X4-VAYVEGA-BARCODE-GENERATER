import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import inch
from reportlab.graphics.barcode import code128
from reportlab.lib.utils import simpleSplit
from datetime import datetime
from PIL import Image
import io
import os
import pandas as pd
import zipfile

# --- 1. LOGO FOLDER SETUP ---
LOGO_FOLDER = "logos"
if not os.path.exists(LOGO_FOLDER):
    os.makedirs(LOGO_FOLDER)

# --- 2. PDF GENERATION FUNCTION ---
def generate_vayu_vega_label(data, uploaded_logo_bytes, show_fixed_logo, selected_folder_logo_path, options, canvas_obj=None):
    is_bulk = canvas_obj is not None
    if not is_bulk:
        buffer = io.BytesIO()
        width, height = 4 * inch, 6 * inch
        c = canvas.Canvas(buffer, pagesize=(width, height))
    else:
        c = canvas_obj

    def draw_wrapped_text(canvas_obj, text, x, y, max_width, font_name, font_size, bold=False, align="left"):
        f_name = f"{font_name}-Bold" if bold else font_name
        canvas_obj.setFont(f_name, font_size)
        lines = simpleSplit(str(text), f_name, font_size, max_width)
        for line in lines:
            if align == "right":
                canvas_obj.drawRightString(x + max_width, y, line)
            else:
                canvas_obj.drawString(x, y, line)
            y -= (font_size + 1.5)
        return y

    c.setLineWidth(1)
    line_y = 5.15 * inch
    
    if show_fixed_logo:
        fixed_path = "logo.png" 
        if os.path.exists(fixed_path):
            c.drawImage(fixed_path, -0.5 * inch, 5 * inch, width=1.7 * inch, height=1 * inch, mask='auto', preserveAspectRatio=True)
    
    final_right_logo_bytes = uploaded_logo_bytes
    final_right_logo_path = selected_folder_logo_path if not uploaded_logo_bytes else None

    if final_right_logo_bytes or final_right_logo_path:
        try:
            img = Image.open(io.BytesIO(final_right_logo_bytes)) if final_right_logo_bytes else Image.open(final_right_logo_path)
            img_w, img_h = img.size
            max_w, max_h = 1.3 * inch, 0.6 * inch
            aspect = img_w / img_h
            final_w, final_h = (max_w, max_w/aspect) if aspect > (max_w/max_h) else (max_h*aspect, max_h)
            if final_right_logo_bytes:
                c.drawInlineImage(img, 3.85 * inch - final_w, 5.22 * inch, width=final_w, height=final_h)
            else:
                c.drawImage(final_right_logo_path, 3.85 * inch - final_w, 5.22 * inch, width=final_w, height=final_h, mask='auto', preserveAspectRatio=True)
        except: pass

    c.line(0.12 * inch, line_y, 3.88 * inch, line_y)

    awb = str(data.get('awb', 'N/A'))
    awb_barcode = code128.Code128(awb, barHeight=0.6 * inch, barWidth=1.8)
    awb_barcode.drawOn(c, 0.4 * inch, 4.4 * inch) 
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(2.0 * inch, 4.25 * inch, f"AWB: {awb}")

    ship_x = 0.15 * inch
    max_ship_w = 1.9 * inch
    ship_y = 3.9 * inch

    to_phone = data.get('to_phone','') if options['show_mobile'] else "0000000000"
    
    ship_y = draw_wrapped_text(c, "SHIP TO:", ship_x, ship_y, max_ship_w, "Helvetica", 9, bold=True)
    ship_y = draw_wrapped_text(c, f"NAME: {data.get('to_name','')}", ship_x + 0.05 * inch, ship_y, max_ship_w, "Helvetica", 8, bold=True)
    ship_y = draw_wrapped_text(c, f"PH: {to_phone}", ship_x + 0.05 * inch, ship_y, max_ship_w, "Helvetica", 8, bold=True)
    draw_wrapped_text(c, data.get('to_address',''), ship_x + 0.05 * inch, ship_y, max_ship_w, "Helvetica", 6)
    
    pincode_x = 2.7 * inch
    c.setFont("Helvetica-Bold", 11); c.drawString(pincode_x + 0.10 * inch, 2.68 * inch, f"PIN: {data.get('to_pincode','')}")
    c.rect(pincode_x, 2.60 * inch, 1.1 * inch, 0.25 * inch)

    from_x_start = 2.2 * inch
    max_from_w = 3.85 * inch - from_x_start - 0.1 * inch
    curr_y_from = 3.9 * inch

    if options['show_from']:
        from_phone = data.get('from_phone','') if options['show_mobile'] else "0000000000"
        curr_y_from = draw_wrapped_text(c, "FROM:", from_x_start, curr_y_from, max_from_w, "Helvetica", 9, bold=True, align="right")
        curr_y_from = draw_wrapped_text(c, f"NAME: {data.get('from_name','')}", from_x_start, curr_y_from, max_from_w, "Helvetica", 8, bold=True, align="right")
        curr_y_from = draw_wrapped_text(c, f"PH: {from_phone}", from_x_start, curr_y_from, max_from_w, "Helvetica", 8, bold=True, align="right")
        draw_wrapped_text(c, data.get('from_address',''), from_x_start, curr_y_from, max_from_w, "Helvetica", 6, align="right")

    c.line(0.15 * inch, 2.5 * inch, 3.85 * inch, 2.5 * inch)
    c.setFont("Helvetica-Bold", 10); c.drawCentredString(2.0 * inch, 2.35 * inch, f"PRODUCT: {data.get('product_name','')}")
    c.setFont("Helvetica-Bold", 11); c.drawCentredString(2.0 * inch, 2.1 * inch, f"VALUE: {data.get('product_value','')}")
    c.line(0.15 * inch, 2.0 * inch, 3.85 * inch, 2.0 * inch)

    c.rect(0.2 * inch, 1.4 * inch, 3.6 * inch, 0.4 * inch)
    c.setFont("Helvetica-Bold", 10); c.drawString(0.3 * inch, 1.55 * inch, f"WT: {data.get('weight','')} KG")
    if options['show_amount']:
        c.drawRightString(3.7 * inch, 1.55 * inch, f"TOTAL: Rs.{data.get('total_amount','')}")

    ref = str(data.get('ref', 'REF'))
    ref_bar = code128.Code128(ref, barHeight=0.4 * inch, barWidth=1.0)
    ref_bar.drawOn(c, -0.1 * inch, 0.75 * inch) 
    c.setFont("Helvetica-Bold", 8); c.drawString(0.2 * inch, 0.62 * inch, f"{ref}")

    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(3.8 * inch, 1.1 * inch, f"MODE: {data.get('mode', 'Surface').upper()}")
    c.drawRightString(3.8 * inch, 0.9 * inch, f"RISK: {data.get('risk', 'Carrier').upper()}")

    c.setFont("Helvetica-Bold", 10); c.drawRightString(3.8 * inch, 0.4 * inch, f"DATE: {data.get('label_date','')}")
    c.setFont("Helvetica-Bold", 10); c.drawCentredString(2.0 * inch, 0.15 * inch, "THANK YOU FOR CHOOSING VAYU VEGA")

    c.setLineWidth(1.5)
    c.rect(0.1 * inch, 0.1 * inch, 3.8 * inch, 5.8 * inch)

    if not is_bulk:
        c.showPage(); c.save(); buffer.seek(0); return buffer
    else:
        c.showPage()

# --- 3. STREAMLIT UI ---
st.set_page_config(page_title="Vayu Vega Ultra Pro", layout="wide")
st.title("🚀 Vayu Vega Ultra Pro - V30")

# --- SIDEBAR SETTINGS ---
st.sidebar.header("⚙️ Settings")
show_logo = st.sidebar.checkbox("Show Fixed Logo (logo.png)", value=True)
uploaded_logo = st.sidebar.file_uploader("Upload Temporary Logo", type=['png', 'jpg'])

# NEW: BROWSER LOGO PREVIEW
if uploaded_logo:
    st.sidebar.image(uploaded_logo, caption="Uploaded Logo Preview", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.header("👁️ Visibility Controls")
opt_amount = st.sidebar.toggle("Show Total Amount", value=True)
opt_mobile = st.sidebar.toggle("Show Mobile Numbers", value=True)
opt_from = st.sidebar.toggle("Show Sender (FROM) Details", value=True)

display_options = {
    'show_amount': opt_amount,
    'show_mobile': opt_mobile,
    'show_from': opt_from
}

st.sidebar.markdown("---")
st.sidebar.header("📁 Folder Logos")
logo_files = [f for f in os.listdir(LOGO_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))] if os.path.exists(LOGO_FOLDER) else []
selected_logo_name = st.sidebar.selectbox("Select Branch Logo", ["None"] + logo_files)
folder_logo_path = os.path.join(LOGO_FOLDER, selected_logo_name) if selected_logo_name != "None" else None

# FOLDER LOGO PREVIEW
if folder_logo_path:
    st.sidebar.image(folder_logo_path, caption="Folder Logo Preview", use_container_width=True)

tab1, tab2 = st.tabs(["📄 Single Label", "📂 Bulk Upload"])

with tab1:
    with st.form("single_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            awb_no = st.text_input("AWB", "VV-100200")
            p_name, p_val = st.text_input("Product", "General"), st.text_input("Value", "1000")
            l_date = st.text_input("Date", datetime.now().strftime("%d-%m-%Y"))
            wt, t_amt, ref_no = st.text_input("Weight", "0.5"), st.text_input("Total Bill", "1100"), st.text_input("Ref", "REF-01")
            mode_opt = st.selectbox("Shipping Mode", ["Surface", "Express"])
            risk_opt = st.selectbox("Risk Type", ["Carrier", "No Risk"])
            
        with c2:
            t_name, t_phone, t_pin = st.text_input("To Name"), st.text_input("To Phone"), st.text_input("To Pin")
            t_addr = st.text_area("To Address")
        with c3:
            f_name, f_phone = st.text_input("From Name", "Vayu Vega Hub"), st.text_input("From Phone")
            f_addr = st.text_area("From Address")
        submit_single = st.form_submit_button("Prepare Label")

    if submit_single:
        l_data = {
            'awb': awb_no, 'product_name': p_name, 'product_value': p_val, 'label_date': l_date, 
            'ref': ref_no, 'weight': wt, 'total_amount': t_amt, 'to_name': t_name, 
            'to_phone': t_phone, 'to_pincode': t_pin, 'to_address': t_addr, 
            'from_name': f_name, 'from_phone': f_phone, 'from_address': f_addr,
            'mode': mode_opt, 'risk': risk_opt
        }
        pdf = generate_vayu_vega_label(l_data, uploaded_logo.getvalue() if uploaded_logo else None, show_logo, folder_logo_path, display_options)
        st.download_button("📥 Download PDF", pdf, f"{awb_no}_{ref_no}.pdf")

with tab2:
    st.info("💡 CSV లేదా Excel ఫైల్‌ను అప్‌లోడ్ చేసి, కావాల్సిన Rows సెలెక్ట్ చేసుకోండి.")

    # --- SAMPLE FILE DOWNLOAD SECTION ---
    sample_data = {
        'awb': ['VV1001', 'VV1002'], 
        'product_name': ['General', 'Electronics'], 
        'product_value': ['1000', '5000'],
        'label_date': [datetime.now().strftime("%d-%m-%Y"), datetime.now().strftime("%d-%m-%Y")], 
        'ref': ['REF01', 'REF02'], 
        'weight': ['0.5', '1.2'],
        'total_amount': ['1100', '5200'], 
        'to_name': ['Rahul', 'Suresh'], 
        'to_phone': ['9876543210', '9999999999'],
        'to_pincode': ['500001', '520001'], 
        'to_address': ['Hyderabad', 'Vijayawada'], 
        'from_name': ['Vayu Vega Hub', 'Vayu Vega Hub'],
        'from_phone': ['8888888888', '8888888888'], 
        'from_address': ['Hub Main Road', 'Hub Main Road'],
        'mode': ['Surface', 'Express'], 
        'risk': ['Carrier', 'No Risk']
    }
    sample_df = pd.DataFrame(sample_data)
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        csv_data = sample_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Sample CSV", data=csv_data, file_name="vayu_vega_sample.csv", mime="text/csv")
    with col_s2:
        output_xlsx = io.BytesIO()
        with pd.ExcelWriter(output_xlsx, engine='openpyxl') as writer:
            sample_df.to_excel(writer, index=False)
        st.download_button("📥 Download Sample Excel", data=output_xlsx.getvalue(), file_name="vayu_vega_sample.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.markdown("---")
    
    uploaded_file = st.file_uploader("Upload Your CSV or Excel File", type=['csv', 'xlsx'])
    
    if uploaded_file:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        st.write("### Select Labels to Generate")
        if "Select" not in df.columns:
            df.insert(0, "Select", True)
            
        edited_df = st.data_editor(df, hide_index=True, use_container_width=True)
        selected_rows = edited_df[edited_df["Select"] == True]
        
        if st.button(f"Generate Labels for {len(selected_rows)} Selected Rows"):
            if len(selected_rows) == 0:
                st.error("Please select at least one row!")
            else:
                logo_bytes = uploaded_logo.getvalue() if uploaded_logo else None
                zip_buffer = io.BytesIO()
                bulk_pdf_buffer = io.BytesIO()
                bulk_c = canvas.Canvas(bulk_pdf_buffer, pagesize=(4 * inch, 6 * inch))

                with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                    for idx, row in selected_rows.iterrows():
                        l_dict = row.to_dict()
                        l_dict.pop('Select', None)
                        
                        single_pdf = generate_vayu_vega_label(l_dict, logo_bytes, show_logo, folder_logo_path, display_options)
                        
                        f_name = f"{l_dict.get('awb', idx)}_{l_dict.get('ref', 'REF')}.pdf"
                        zip_file.writestr(f_name, single_pdf.getvalue())
                        
                        generate_vayu_vega_label(l_dict, logo_bytes, show_logo, folder_logo_path, display_options, canvas_obj=bulk_c)
                
                bulk_c.save()
                bulk_pdf_buffer.seek(0)
                st.success("Labels Generated Successfully!")
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    st.download_button("📥 Download ZIP (Individual)", zip_buffer.getvalue(), "Selected_Labels.zip")
                with col_d2:
                    st.download_button("📥 Download Combined PDF", bulk_pdf_buffer, "Selected_Labels_Combined.pdf")
