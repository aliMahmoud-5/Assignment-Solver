from autogen import ConversableAgent, GroupChat, GroupChatManager, AssistantAgent
from autogen.coding import LocalCommandLineCodeExecutor
import autogen
import json
import re
import PyPDF2
import requests
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
from docx import Document
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




def DemoSolver():

    course_file = r"./material/Course.pdf"
    assignment_file = r"./material/assignment.pdf"


    course_texts = extract_text_from_pdf(course_file)
    assignment_text = extract_text_from_pdf(assignment_file)

    host = autogen.AssistantAgent(
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
    hreply = host.generate_reply(messages=[{"content": "start your task", "role": "user"}])






    try:
        # Extract JSON from LLM response using regex
        json_match = re.search(r"\{.*\}", hreply['content'], re.DOTALL)

        if json_match:
            json_text = json_match.group(0)
            extracted_data = json.loads(json_text)
            print("Extracted JSON:", extracted_data)
        else:
            print("No JSON structure found. Full response:", hreply['content'])
            extracted_data = {}

        assignmentWebSearch = extracted_data.get("assignmentWebSearch", [])
        courseWebSearch = extracted_data.get("courseWebSearch", [])

    except json.JSONDecodeError as e:
        print("Failed to parse JSON:", str(e))
        print("Full response:", hreply['content'])
        extracted_data = {}


    all_queries = assignmentWebSearch + courseWebSearch




    def google_search(query):
        """Uses SERPAPI to search Google and return top result links."""
        params = {
            "q": query,
            "api_key": SERPAPI_KEY,
            "num": 2
        }

        search = GoogleSearch(params)
        results = search.get_dict()

        if "organic_results" in results:
            return [result["link"] for result in results["organic_results"]]  # Extract URLs
        return []

    def scrape_website(url):
        """Fetch and extract text content from a given website URL."""
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()  # Raise an error for HTTP issues

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract main content from <p> tags
            paragraphs = soup.find_all("p")
            extracted_text = "\n".join(p.get_text() for p in paragraphs[:5])  # Limit to 5 paragraphs

            return extracted_text if extracted_text else "No relevant content found."

        except requests.exceptions.RequestException as e:
            return f"Error fetching {url}: {str(e)}"


    def process_queries(query_list):

        """
        this function scrape the internet for queries provied by courseWebSearch + assignmentWebSearch.
        Args:
          query_list : a concatenation of the provided two lists courseWebSearch and assignmentWebSearch

        returns:
          the search result preceded by the query.
        """
        results = {}
        for query in query_list:
            print(f"Searching: {query}")
            links = google_search(query)
            if links:
                scraped_data = [scrape_website(link) for link in links]
                results[query] = scraped_data
            else:
                results[query] = ["No relevant search results."]
        return results



    if all_queries:
        search_results = process_queries(all_queries)
        print("\n🔍 Web Scraping Results:")
        for query, results in search_results.items():
            print(f"\n🔹 Query: {query}")
            for res in results:
                print(f"   - {res[:300]}...")
    else:
        print("⚠️ No queries to process.")


    web_scraper = LocalCommandLineCodeExecutor(
        timeout=60,
        work_dir="coding",
        functions=[process_queries],

    )
    queries_result = process_queries(all_queries)
    print(queries_result)




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
        "note that all the input provided belongs to the same assignment.\n"
        "DO NOT summarize, interpret, or explain the inputs.\n"
        "DO NOT output anything unrelated to the direct solution.\n\n"
        "Your task is to directly answer the assignment using a structured format that mirrors the assignment's requirements.\n"
        "Ensure each answer is:\n"
        "- Fully developed and clear\n"
        "- Aligned with course terminology and learning outcomes\n"
        "- Informed by relevant insights from the provided research\n"
        "Avoid any mention of the sources or how the solution was derived.\n"
        "Proceed straight to writing the solution using formal academic language.\n"
        f"extract and pass to the next agent the forrmating requirements and the word count found in {hreply}\n"
        "Be clear, concise, coherent, and logically organized for easy formatting in the next stage."
        ),
        llm_config=llm_config,
        human_input_mode="NEVER",
    )




    formatter = AssistantAgent(
        name="formatter",
        system_message =("You are a formatting assistant tasked with transforming raw assignment answers into a properly formatted academic document.\n\n"
        "You will receive:\n"
        "- Assignment answers generated by the 'generator' agent\n"
        "- Formatting instructions (e.g., font, spacing, headings, citations, word count)\n\n"
        "Your responsibilities:\n"
        "1. summaries the asnwers to be within the required word count as defined by the assignment\n\n"
        "2. Format the content to be written into Word document (DOCX)\n"
        "3. Apply all required formatting strictly\n"
        "4. Ensure coherence, grammar correctness, and academic tone\n"
        "5. Check for plagiarism and originality\n\n"
        "always start you response as follows.\n"
        "-list the formatting requirements passed to you by the pervious agent.\n"
        "-write the keyord '**Document:**' to indicate the begining of the document to be converted to Word"
        "Make no assumptions.\n"
        "Your output should be the final text, formatted and ready to be written in a word document — ready to be submitted.\n"
        ),
        llm_config=llm_config,
        human_input_mode="NEVER",
    )






    groupchat = autogen.GroupChat(
        agents=[generator,formatter],
        messages=[],
        allowed_or_disallowed_speaker_transitions={
            generator: [formatter],
        },
        speaker_transitions_type="allowed",
    )

    manager = autogen.GroupChatManager(
        groupchat=groupchat, llm_config=llm_config
    )

    task = "start your task, and never terminate before you generate the answers to the assignments according to the proper structure and requirements"
    groupchat_result = manager.initiate_chat(
        generator,
        message=task,
    )
    

    # At the end of your solver()
    formatter_output = groupchat_result.chat_history[-1]['content']
    # Set filename (extract from content or use default)
    filename = "Generated_Assignment.docx"
    filepath = create_word_doc(formatter_output, filename)

    # Return both content and file path
    return formatter_output, filepath






