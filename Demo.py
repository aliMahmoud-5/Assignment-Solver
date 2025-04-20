from autogen import  AssistantAgent
import autogen
import PyPDF2
import os
from text_to_docx import create_word_doc



llm_config = {
        "api_type": "together",  # Using OpenAI-compatible endpoint
        "model": "meta-llama/Llama-Vision-Free",  # Using Llama 11B Vision model
        "api_key": "3def0b6ae8c16e3523600d8d52ec7de39bd86a823a3678df308f12a6cd53c93a",
        "base_url": "https://api.together.xyz/v1",
        "max_tokens": 10000,
        "temperature": 0.2,

}

SERPAPI_KEY = "3a01b6db013287fb18f155cf27c12c4db852b9a5245bb3c9e18617f5defa27e3"

#the function to extract text from pre-defined documents lives on the server
def extract_text_from_pdf(pdf_path):
    """
    Extracts and returns text from all pages in a PDF file using PyPDF2.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        str: The extracted text.
    """
    text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ''  # fallback in case extract_text() returns None
    return text



#in demo the files are pre-defined and the purpose is to demonstare the app incase
#someone wants to try the app but doesn't have files to run a test
def DemoSolver():

    course_file = r"./material/Course.pdf"
    assignment_file = r"./material/assignment.pdf"


    course_texts = extract_text_from_pdf(course_file)
    assignment_text = extract_text_from_pdf(assignment_file)

    #Host is the agent that takes the files extracted text
    # analyze keypoints and topics and generate web search quiries to be passed to thr researcher
    host = AssistantAgent(
        name="host",
        system_message=(
            f"You have been provided with extracted course text {course_texts}.\n"
            f"start your reply by printing the content of {course_texts}, followed by {assignment_text}.\n"
            "define each text by printing 'course text' before the course text, and 'assignment text' before the assignment text.\n"
            "Your task is to analyze and extract key information.\n"
            "Extract course definitions, topics, and keywords from the provided course texts.\n"
            f"You have also been provided with extracted assignment text {assignment_text}.\n"
            "Step 1: If the assignment requires a choice (company, topic, etc.), pick ONE randomly.\n"
            "Step 2: Generate web search queries for each assignment question/task and return them as 'assignmentWebSearch'.\n"
            "Step 3: Generate web search queries for each course definition/topic and return them as 'courseWebSearch'.\n"
            "Return the output in **JSON format** as follows:\n"
            "{'assignmentWebSearch': [...], 'courseWebSearch': [...]}"
        ),
        llm_config=llm_config,
        human_input_mode="NEVER",
    )
    print("host reply")
    hreply = host.generate_reply(messages=[{"content": "start your task", "role": "user"}])
    print(hreply['content'])


    #resercher is the agent that searches the web for suplimentary information about the assignment and the courses
    researcher = AssistantAgent(
        name="host",
        system_message=(
            f"provided by {hreply}.\n\n"
            "your task is to:\n"
            "1. search the web to answer the quiries in the provided text.\n"
            "2. the answer for each quiry mut be at least 1000 words.\n"
            "3. mention nothing about the word count.\n"
        ),
        llm_config=llm_config,
        human_input_mode="NEVER",
        
    )
    print("researcher reply")
    queries_result = researcher.generate_reply(messages=[{"content": "search the web for the provided quiries", "role": "user"}])
    print(queries_result['content'])




    #provided by all the previous agents work to generate an extended version of the assignment answers
    generator = AssistantAgent(
        name="generator",
        system_message =( f"Given {queries_result}, and {hreply}."
        "You are an academic assistant tasked with generating assignment responses.\n"
        "Inputs provided include:\n"
        f"- Extracted course content from {hreply}\n"
        f"- Assignment questions from {hreply}\n"
        f"- formatting requirements from {hreply}\n"
        f"- Results from web research from {queries_result}\n\n"
        "analyze and understand all your input.\n"
        "note that all the input provided belongs to only one assignment assignment.\n"
        "DO NOT summarize, interpret, or explain the inputs.\n"
        "DO NOT mention the word count.\n"
        "DO NOT output anything unrelated to the direct solution.\n\n"
        "Your task is to directly answer the assignment questions and demands using a structured format that mirrors the assignment's requirements.\n"
        "Ensure each answer is:\n"
        "- at least 1000 words without mentioning the word count \n"
        "- Fully developed and clear\n"
        "- only write the word 'Assinment' before the assignment title\n"
        "- Aligned with course terminology and learning outcomes\n"
        "- Informed by relevant insights from the provided research\n"
        "Avoid any mention of the sources or how the solution was derived.\n"
        "Proceed straight to writing the solution using formal academic language.\n"
        #f"extract and pass to the next agent the forrmating requirements and the word count found in {hreply}\n"
        "Be clear, concise, coherent, and logically organized for easy formatting in the next stage."
        ),
        llm_config=llm_config,
        human_input_mode="NEVER",
    )
    print("generator reply")
    answers = generator.generate_reply(messages=[{"content": "start your task, and never terminate before you generate the answers to the assignments according to the proper structure and requirements", "role": "user"}])
    print(answers['content'])

    #provided by all previous agents effort, it checkes the assignment formatting requirements
    #and summaries the generator answers and construct the text according to the assignment requirements
    #then this text got passed to a function that creates the Word document
    formatter = AssistantAgent(
        name="formatter",
        system_message =("You are a formatting assistant tasked with transforming raw assignment answers into a properly formatted academic document.\n\n"
        "You will receive:\n"
        f"- Assignment answers found in {answers}\n"
        f"-assignment text found in {hreply}\n"
        f"- Formatting instructions (e.g., font, spacing, headings, citations, word count) found in {hreply}\n\n"
        "note that all the answers provided belongs  to the same assignment"
        "Your responsibilities:\n"
        "1. Format the content to be written into Word document (DOCX)\n"
        "2. summaries the asnwers to be within the required word count as defined in the assignment\n"
        "3. Apply all required formatting strictly\n"
        "4. Ensure coherence, grammar correctness, and academic tone\n"
        "5. Check for plagiarism and originality\n\n"
        "always start you response as follows.\n"
        "-list the formatting requirements passed to you by the pervious agent.\n"
        "-write the keyord '**Document:**' to indicate the begining of the document to be converted to Word.\n"
        "-write 'Assignment:' followed by the assignment title"
        "Make no assumptions.\n"
        "count the words after the keyowrd '**Document:**' if it is less than the word count required in '**Formatting Requirements:**' elaborate so the total words after '**Document:**' is within the required word count.\n"
        "Your output should be the final text, formatted and ready to be written in a word document — ready to be submitted.\n"
        ),
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

    print("formatter reply")
    formatter_output = formatter.generate_reply(messages=[{"content": "generate the word document", "role": "user"}])
    print(formatter_output['content'])

    



    filename = "Generated_Assignment.docx"
    filepath = create_word_doc(formatter_output['content'], filename)

    

    return formatter_output['content'], filepath






