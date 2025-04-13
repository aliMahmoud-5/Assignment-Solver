import PyPDF2
from typing import Union
import io

def extract_text_from_uploaded_pdf(course_file: Union[list, 'UploadedFile']) -> str:
    """
    Extracts text from the first UploadedFile in the list.

    Parameters:
    - course_file: A list containing a Streamlit UploadedFile object

    Returns:
    - Extracted text from the PDF as a string
    """
    if isinstance(course_file, list):
        uploaded_file = course_file[0]
    else:
        uploaded_file = course_file

    if uploaded_file.type != "application/pdf":
        raise ValueError("Uploaded file is not a PDF.")

    reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return text

