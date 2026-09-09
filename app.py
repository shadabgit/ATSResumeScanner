import streamlit as st
import pdf2image
import io
import json

from google import genai
from google.genai import types


# =========================================================
# Gemini Configuration
# =========================================================

client = genai.Client(
    api_key=st.secrets["GOOGLE_API_KEY"]
)


# =========================================================
# Gemini Response Functions
# =========================================================

@st.cache_data()
def get_gemini_response(input_text, pdf_content, prompt):

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=[
            input_text,
            pdf_content,
            prompt
        ]
    )

    return response.text


@st.cache_data()
def get_gemini_response_keywords(input_text, pdf_content, prompt):

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=[
            input_text,
            pdf_content,
            prompt
        ]
    )

    text = response.text.strip()

    # Remove Markdown JSON code fences
    if text.startswith("```json"):
        text = text[7:]

    if text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    return json.loads(text)


# =========================================================
# PDF Processing
# =========================================================

@st.cache_data()
def input_pdf_setup(uploaded_file):

    if uploaded_file is None:
        raise FileNotFoundError("No file uploaded")

    # Convert PDF into images
    images = pdf2image.convert_from_bytes(
        uploaded_file.read()
    )

    if not images:
        raise ValueError("Could not read the PDF")

    # Currently using the first page
    first_page = images[0]

    # Convert image to bytes
    img_byte_arr = io.BytesIO()

    first_page.save(
        img_byte_arr,
        format="JPEG"
    )

    img_bytes = img_byte_arr.getvalue()

    # Convert image to Gemini Part
    image_part = types.Part.from_bytes(
        data=img_bytes,
        mime_type="image/jpeg"
    )

    return image_part


# =========================================================
# Streamlit App
# =========================================================

st.set_page_config(
    page_title="ATS Resume Scanner",
    page_icon="📄",
    layout="centered"
)

st.header("Application Tracking System")


# =========================================================
# Job Description
# =========================================================

input_text = st.text_area(
    "Job Description:",
    key="input",
    height=200
)


# =========================================================
# Resume Upload
# =========================================================

uploaded_file = st.file_uploader(
    "Upload your resume (PDF)...",
    type=["pdf"]
)


# =========================================================
# Session State
# =========================================================

if "resume" not in st.session_state:
    st.session_state.resume = None


if uploaded_file is not None:

    st.write("✅ PDF Uploaded Successfully")

    st.session_state.resume = uploaded_file


# =========================================================
# Buttons
# =========================================================

col1, col2, col3 = st.columns(
    3,
    gap="medium"
)


with col1:
    submit1 = st.button(
        "Tell Me About the Resume"
    )


with col2:
    submit2 = st.button(
        "Get Keywords"
    )


with col3:
    submit3 = st.button(
        "Percentage Match"
    )


# =========================================================
# Prompts
# =========================================================

input_prompt1 = """
You are an experienced Technical Human Resource Manager.

Your task is to review the provided resume against the provided job description.

Please provide a professional evaluation of whether the candidate's profile aligns with the role.

Highlight:

1. Candidate strengths
2. Candidate weaknesses
3. Relevant skills
4. Missing skills
5. Overall suitability for the role

Base your response only on the resume and job description provided.
"""


input_prompt2 = """
You are an expert ATS (Applicant Tracking System) scanner.

Evaluate the resume against the provided job description.

Identify the specific skills and keywords from the job description that are relevant for the candidate.

Return ONLY valid JSON in exactly this structure:

{
    "Technical Skills": [],
    "Analytical Skills": [],
    "Soft Skills": []
}

Do not add Markdown.
Do not add explanations outside the JSON.

Only identify skills and keywords that actually appear in the job description.
Do not make up skills.
"""


input_prompt3 = """
You are a skilled ATS (Applicant Tracking System) scanner.

Evaluate the provided resume against the provided job description.

Calculate an estimated percentage match between the resume and job description.

Your response must contain:

1. Match Percentage
2. Missing Keywords
3. Final Thoughts

Example:

Match Percentage: 85%

Missing Keywords:
- Docker
- Kubernetes

Final Thoughts:
The candidate is a strong match because...

Base your evaluation only on the provided resume and job description.
"""


# =========================================================
# Tell Me About the Resume
# =========================================================

if submit1:

    if st.session_state.resume is not None:

        if not input_text.strip():
            st.warning(
                "Please enter the job description."
            )

        else:

            try:

                with st.spinner(
                    "Analyzing resume..."
                ):

                    pdf_content = input_pdf_setup(
                        st.session_state.resume
                    )

                    response = get_gemini_response(
                        input_text,
                        pdf_content,
                        input_prompt1
                    )

                st.subheader(
                    "Resume Analysis"
                )

                st.write(response)

            except Exception as e:

                st.error(
                    f"Error analyzing resume: {e}"
                )

    else:

        st.warning(
            "Please upload the resume."
        )


# =========================================================
# Get Keywords
# =========================================================

elif submit2:

    if st.session_state.resume is not None:

        if not input_text.strip():

            st.warning(
                "Please enter the job description."
            )

        else:

            try:

                with st.spinner(
                    "Finding relevant keywords..."
                ):

                    pdf_content = input_pdf_setup(
                        st.session_state.resume
                    )

                    response = get_gemini_response_keywords(
                        input_text,
                        pdf_content,
                        input_prompt2
                    )

                st.subheader(
                    "Skills & Keywords"
                )

                if response:

                    technical_skills = response.get(
                        "Technical Skills",
                        []
                    )

                    analytical_skills = response.get(
                        "Analytical Skills",
                        []
                    )

                    soft_skills = response.get(
                        "Soft Skills",
                        []
                    )

                    st.write(
                        "### Technical Skills"
                    )

                    if technical_skills:
                        st.write(
                            ", ".join(technical_skills)
                        )
                    else:
                        st.write(
                            "No technical skills found."
                        )

                    st.write(
                        "### Analytical Skills"
                    )

                    if analytical_skills:
                        st.write(
                            ", ".join(analytical_skills)
                        )
                    else:
                        st.write(
                            "No analytical skills found."
                        )

                    st.write(
                        "### Soft Skills"
                    )

                    if soft_skills:
                        st.write(
                            ", ".join(soft_skills)
                        )
                    else:
                        st.write(
                            "No soft skills found."
                        )

            except json.JSONDecodeError:

                st.error(
                    "Gemini returned an invalid JSON response. Please try again."
                )

            except Exception as e:

                st.error(
                    f"Error finding keywords: {e}"
                )

    else:

        st.warning(
            "Please upload the resume."
        )


# =========================================================
# Percentage Match
# =========================================================

elif submit3:

    if st.session_state.resume is not None:

        if not input_text.strip():

            st.warning(
                "Please enter the job description."
            )

        else:

            try:

                with st.spinner(
                    "Calculating resume match..."
                ):

                    pdf_content = input_pdf_setup(
                        st.session_state.resume
                    )

                    response = get_gemini_response(
                        input_text,
                        pdf_content,
                        input_prompt3
                    )

                st.subheader(
                    "Resume Match"
                )

                st.write(response)

            except Exception as e:

                st.error(
                    f"Error calculating match: {e}"
                )

    else:

        st.warning(
            "Please upload the resume."
        )
