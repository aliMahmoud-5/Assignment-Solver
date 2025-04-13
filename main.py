﻿import streamlit as st
from extraction import extract_text_from_uploaded_pdf
from Agents import solver
from Demo import DemoSolver
import os
import random
import string

def random_key():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))


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


if st.sidebar.button("🔄 Reset App"):
    st.session_state.clear()
    st.session_state.course_key = "course_" + random_key()
    st.session_state.assignment_key = "assign_" + random_key()
    st.rerun()


st.sidebar.title("Assignment Solver")

demo = st.sidebar.button("Demo")
solve_clicked = st.sidebar.button("Solve Assignment")


course_files = st.sidebar.file_uploader(
    "Upload Course Files (PDF)",
    type=["pdf"],
    accept_multiple_files=True,
    key=st.session_state.course_key
)


assignment_file = st.sidebar.file_uploader(
    "Upload Assignment File (PDF)",
    type=["pdf"],
    accept_multiple_files=False,
    key=st.session_state.assignment_key
)


st.title("AI Assignment Solver")


if course_files:
    st.subheader("Uploaded Course Files:")
    course_text = ""
    for file in course_files:
        st.write(f"-> {file.name}")
        text1 = extract_text_from_uploaded_pdf(file)
        course_text += f"\n\n---{file.name}--\n\n{text1}"
    st.session_state.course_text = course_text


if assignment_file:
    st.subheader("Uploaded Assignment File:")
    st.write(f"-> {assignment_file.name}")
    assignment_text = extract_text_from_uploaded_pdf(assignment_file)
    st.session_state.assignment_text = assignment_text


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


if demo:
    st.info("Running demo... this may take a while ⏳")
    output_text, word_file_path = DemoSolver()
    st.session_state.output_text = output_text
    st.session_state.word_file_path = word_file_path


if st.session_state.output_text:
    st.subheader("📝 Generated Assignment Answer")
    if os.path.exists(st.session_state.word_file_path):
        with open(st.session_state.word_file_path, "rb") as f:
            st.download_button(
                label="📥 Download as Word Document",
                data=f,
                file_name=os.path.basename(st.session_state.word_file_path),
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
    st.markdown(st.session_state.output_text)

    
