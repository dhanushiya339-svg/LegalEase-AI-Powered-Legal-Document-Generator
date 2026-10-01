import os
from datetime import date
from html import escape

import requests
import streamlit as st

from dotenv import load_dotenv

from backend.services.document_formatter import (
    format_docx,
    format_pdf,
    format_txt
)


load_dotenv()


# -------------------------------------------------
# PAGE CONFIGURATION
# -------------------------------------------------

st.set_page_config(

    page_title="LegalEase",

    page_icon="⚖️",

    layout="wide"
)


# -------------------------------------------------
# CONFIGURATION
# -------------------------------------------------

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000"
).rstrip("/")


LOGO_PATH = "assets/logo.png"


# -------------------------------------------------
# PREVIEW FUNCTION
# -------------------------------------------------

def render_preview(text: str):

    html = escape(text)

    html = html.replace(
        "\n",
        "<br>"
    )

    st.markdown(

        f"""
        <div style="
            background:#111827;
            color:#f9fafb;
            padding:24px;
            border-radius:14px;
            border:1px solid #374151;
            max-height:600px;
            overflow-y:auto;
            font-family:Georgia,serif;
            line-height:1.65;
        ">

        {html}

        </div>
        """,

        unsafe_allow_html=True
    )


# -------------------------------------------------
# LOGO
# -------------------------------------------------

if os.path.exists(LOGO_PATH):

    left, center, right = st.columns(
        [1, 2, 1]
    )

    with center:

        st.image(
            LOGO_PATH,
            width=110
        )


# -------------------------------------------------
# HEADER
# -------------------------------------------------

st.title("LegalEase")

st.caption(
    "AI-Powered Legal Document Generator"
)


st.info(
    "LegalEase creates draft documents. "
    "It is not a substitute for a qualified "
    "lawyer. Review generated content before "
    "signing."
)


# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------

with st.sidebar:

    st.header("Settings")

    default_demo = not bool(
        os.getenv(
            "GEMINI_API_KEY",
            ""
        ).strip()
    )

    demo_mode = st.checkbox(

        "Demo Mode",

        value=default_demo,

        help=(
            "Use Demo Mode to test the application "
            "without calling Gemini."
        )
    )

    st.write(
        f"Backend: `{BACKEND_URL}`"
    )

    st.write(
        "Model: "
        f"`{os.getenv('GEMINI_MODEL', 'gemini-3.8-flash')}`"
    )


# -------------------------------------------------
# DOCUMENT DETAILS
# -------------------------------------------------

st.subheader(
    "Document Details"
)


col1, col2 = st.columns(2)


# -------------------------------------------------
# LEFT COLUMN
# -------------------------------------------------

with col1:

    document_type = st.selectbox(

        "Document Type",

        [

            "Employment Contract",

            "Non-Disclosure Agreement (NDA)",

            "Lease Agreement",

            "Freelance Work Contract",

            "Service Agreement",

            "General Agreement",

            "Other"

        ]
    )


    if document_type == "Other":

        document_type = st.text_input(

            "Enter document type",

            value="Legal Agreement"
        )


    effective_date = st.date_input(

        "Effective Date",

        value=date.today()
    )


# -------------------------------------------------
# RIGHT COLUMN
# -------------------------------------------------

with col2:

    language = st.selectbox(

        "Output Language",

        [

            "English",

            "Tamil",

            "Hindi",

            "Malayalam",

            "Telugu",

            "Kannada"

        ]
    )


    parties = st.text_area(

        "Parties Involved",

        placeholder=(
            "Example: Jane Doe "
            "(Service Provider), "
            "TechNova Inc. (Client)"
        ),

        height=120
    )


# -------------------------------------------------
# TERMS
# -------------------------------------------------

terms = st.text_area(

    "Terms & Conditions",

    placeholder=(
        "Enter each term separated by a semicolon;\n"
        "Payment within 30 days of invoice;\n"
        "Confidentiality must be maintained;\n"
        "Either party may terminate with 15 days notice"
    ),

    height=160
)


# -------------------------------------------------
# GENERATE BUTTON
# -------------------------------------------------

generate = st.button(

    "Generate Document",

    type="primary",

    use_container_width=True
)


# -------------------------------------------------
# GENERATE PROCESS
# -------------------------------------------------

if generate:

    if not parties.strip():

        st.error(
            "Please enter the parties involved."
        )

        st.stop()


    if not terms.strip():

        st.error(
            "Please enter at least one "
            "term or condition."
        )

        st.stop()


    payload = {

        "document_type":
            document_type,

        "parties":
            parties,

        "terms":
            terms,

        "effective_date":
            effective_date.isoformat(),

        "language":
            language,

        "demo_mode":
            demo_mode
    }


    with st.spinner(
        "Generating your document..."
    ):

        try:

            response = requests.post(

                f"{BACKEND_URL}/generate",

                json=payload,

                timeout=120
            )

        except requests.RequestException as exc:

            st.error(
                "Could not connect to the "
                "FastAPI backend."
            )

            st.code(
                "python -m uvicorn "
                "backend.main:app "
                "--reload --port 8000"
            )

            st.exception(exc)

            st.stop()


    if response.ok:

        data = response.json()


        st.session_state[
            "document"
        ] = data["document"]


        st.session_state[
            "model"
        ] = data["model"]


        st.session_state[
            "demo"
        ] = data["demo_mode"]


        st.success(
            "Document generated successfully."
        )


    else:

        try:

            detail = response.json().get(
                "detail",
                response.text
            )

        except Exception:

            detail = response.text


        st.error(
            f"Backend error: {detail}"
        )


# -------------------------------------------------
# DISPLAY GENERATED DOCUMENT
# -------------------------------------------------

if "document" in st.session_state:

    st.divider()

    st.subheader(
        "Editable Document"
    )


    edited = st.text_area(

        "Edit your document here:",

        value=st.session_state["document"],

        height=500,

        key="document_editor"
    )


    st.session_state[
        "document"
    ] = edited


    # -------------------------------------------------
    # PREVIEW
    # -------------------------------------------------

    st.subheader(
        "Document Preview"
    )


    render_preview(
        edited
    )


    # -------------------------------------------------
    # DOWNLOAD
    # -------------------------------------------------

    st.subheader(
        "Download Document"
    )


    safe_name = "".join(

        character
        if character.isalnum()
        or character in "-_"
        else "_"

        for character
        in document_type.lower()
    ).strip("_")


    if not safe_name:

        safe_name = "legal_document"


    b1, b2, b3 = st.columns(3)


    # TXT

    with b1:

        st.download_button(

            "Download TXT",

            data=format_txt(
                edited
            ),

            file_name=(
                f"{safe_name}.txt"
            ),

            mime="text/plain",

            use_container_width=True
        )


    # DOCX

    with b2:

        st.download_button(

            "Download DOCX",

            data=format_docx(

                edited,

                document_type,

                terms
            ),

            file_name=(
                f"{safe_name}.docx"
            ),

            mime=(
                "application/"
                "vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),

            use_container_width=True
        )


    # PDF

    with b3:

        st.download_button(

            "Download PDF",

            data=format_pdf(

                edited,

                document_type
            ),

            file_name=(
                f"{safe_name}.pdf"
            ),

            mime="application/pdf",

            use_container_width=True
        )


    st.caption(

        "Model: "
        f"{st.session_state.get('model', 'Unknown')} "
        "| Demo Mode: "
        f"{st.session_state.get('demo', False)}"
    )