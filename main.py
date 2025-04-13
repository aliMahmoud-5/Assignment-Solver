import streamlit as st
from extraction import extract_text_from_uploaded_pdf
from Agents import solver
from Demo import DemoSolver
import os
import random
import string

# Helper to generate random keys
def random_key():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

# Initialize session state
if "course_text" not in st.session_state:
    st.session_state.course_text = ""
if "assignment_text" not in st.session_state:
    st.session_state.assignment_text = ""
if "output_text" not in st.session_state:
    st.session_state.output_text = ""
if "word_file_path" not in st.session_state:
    st.session_state.word_file_path = ""
if "course_key" not in st.session_state:
    st.session_state.course_key = "course_" + random_key()
if "assignment_key" not in st.session_state:
    st.session_state.assignment_key = "assign_" + random_key()

# Reset Button
if st.sidebar.button("🔄 Reset App"):
    st.session_state.clear()
    st.session_state.course_key = "course_" + random_key()
    st.session_state.assignment_key = "assign_" + random_key()
    st.rerun()

# Sidebar UI
st.sidebar.title("Assignment Solver")

demo = st.sidebar.button("Demo")
solve_clicked = st.sidebar.button("Solve Assignment")

# Upload multiple course files
course_files = st.sidebar.file_uploader(
    "Upload Course Files (PDF)",
    type=["pdf"],
    accept_multiple_files=True,
    key=st.session_state.course_key
)

# Upload one assignment file
assignment_file = st.sidebar.file_uploader(
    "Upload Assignment File (PDF)",
    type=["pdf"],
    accept_multiple_files=False,
    key=st.session_state.assignment_key
)

# Main section
st.title("AI Assignment Solver")

# Display uploaded course content
if course_files:
    st.subheader("Uploaded Course Files:")
    course_text = ""
    for file in course_files:
        st.write(f"-> {file.name}")
        text1 = extract_text_from_uploaded_pdf(file)
        course_text += f"\n\n---{file.name}--\n\n{text1}"
    st.session_state.course_text = course_text

# Display uploaded assignment content
if assignment_file:
    st.subheader("Uploaded Assignment File:")
    st.write(f"-> {assignment_file.name}")
    assignment_text = extract_text_from_uploaded_pdf(assignment_file)
    st.session_state.assignment_text = assignment_text

# Solve assignment logic
if solve_clicked:
    if not course_files or not assignment_file:
        st.warning("Please upload all required files first.")
    else:
        st.info("Processing assignment... this may take a while ⏳")
        output_text, word_file_path = solver(
            st.session_state.course_text,
            st.session_state.assignment_text
        )
        st.session_state.output_text = output_text
        st.session_state.word_file_path = word_file_path

# Demo button logic
if demo:
    st.info("Running demo... this may take a while ⏳")
    output_text, word_file_path = DemoSolver()
    st.session_state.output_text = output_text
    st.session_state.word_file_path = word_file_path

# Display results if available
if st.session_state.output_text:
    st.subheader("📝 Generated Assignment Answer")
    st.text_area("Assignment Response", value=st.session_state.output_text, height=400)
    st.markdown(st.session_state.output_text)

    if os.path.exists(st.session_state.word_file_path):
        with open(st.session_state.word_file_path, "rb") as f:
            st.download_button(
                label="📥 Download as Word Document",
                data=f,
                file_name=os.path.basename(st.session_state.word_file_path),
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
