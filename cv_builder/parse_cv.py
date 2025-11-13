import re
from docx import Document
import pdfplumber
from cv_builder.generate_cv import call_perplexity

#extract text from pdf
def extract_info_from_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    return extract_info_from_text(text)

#extract text from doc
def extract_info_from_docx(file_path):
    doc = Document(file_path)
    text = "\n".join(p.text for p in doc.paragraphs)
    return extract_info_from_text(text)

#extract required data from extracted text
def extract_info_from_text(text):
    prompt = f"""
                Given this heap of text collected from an existing uploaded CV:\n{text}\n\n
                Can you return a clearly structured json resopnse such that the jsonify(your_output) function can be used to convert your response to a proper json object. Include fields in this format:\n
                full_name: full name of the user\n
                email: user email\n
                phone: user phone number in country code format (e.g. +44 ... for UK)\n
                location: user's location in the format City, Country (e.g. London, UK)\n
                work_experience: this should be an array of dictionaries contaning these following fields\n
                -> type_of_work: out of 2 options - internship or full-time\n
                -> job_title: the title of the job (e.g. Product Manager)\n
                -> company_name: the name of the company they worked for\n
                -> start_date: when they started work in mm/dd/yyyy format\n
                -> end_date: when they ended work in mm/dd/yyyy format or 'Present' for still working\n 
                -> responsibilities: list of roles or responsibilities they had in the job (separated by commahs)\n 
                -> achievements: list of achievements or accomplishments within the job (separated by commahs)\n
                education: this should be an array of dictionaries containing these following fields\n
                -> discipline: name of the discipline pursued (e.g., Arts, Business, IT, etc)\n
                -> level: name of the degree level of education (fixed options - either Undergraduate, Postgraduate or PhD)\n
                -> course: name of the course pursued for education (e.g., Computer Science, Business Management, etc)\n
                -> country: name of the country of education (e.g., Australia, United Kingdom, United States, etc)\n
                -> region: name of region of education (e.g., Greater London for UK, Maharashtra for India, etc)\n
                -> location: name of the city of education (e.g., London in Greater London, Mumbai in Maharshtra, etc)\n
                -> university_name: name of school/university they received the qualification/degree from\n
                -> start_date: when they started their education in that specific institution in mm/dd/yyyy format\n
                -> end_date: when they ended their education in that specific institution in mm/dd/yyyy format or 'Present' for still studying\n
                -> results: results of the qualification (e.g., First Class Hons for UG/PG/PhD, AAA for A levels, 43/45 for IB, etc)\n
                skills: this should be a single dictionary containing these following fields\n
                -> technical_skills: list of technical skills separated by a commah (e.g. Java, Python, C++)\n
                -> soft_skills: list of soft skills separated by a commah (e.g. Communication, Teamwork)\n
                languages_known: this should be a list of languages known (e.g., English, French, etc) \n
                certifications: this should be a list of dictionaries with these following fields\n
                -> type: type of certification (fixed options: Certificate, Award, Scholarship or Recogniition)\n
                -> name: name of the certification\n
                -> organisation: name of the issuing organisation of the certification\n
                -> date: the date they obtained the certification in mm/dd/yyyy format\n
                projects: this should be a list of dictionaries with these following fields\n
                -> type: type of project (fixed options: Project, Research or Publication)\n
                -> title: the name/title of the project\n
                -> link: the URL link to the project in https:// format\n
                -> description: a short description of the project\n
                links: this should be a list of dictionaries with these following fields\n
                -> name: name of the link type (fixed options: LinkedIn, Website or Github)\n
                -> url: the url of the link (in https:// format - format the link accordingly)\n
                additionalSec: this would be a list of dictionaries that you need to extract for additional sections that are useful for the CV build with these following fields\n
                -> title: the name/title of the additional section\n
                -> desc: a description of the key information relative to that section (could be results, achievements, responsibilities, etc) \n\n
                If any of the fields are missing, assign the field with no value (do not fill in that field), leave it as '' (an empty string).\n
                Strictly start and end the response with a curly bracket, do not include any other characters or text in the start or end.
            """
    
    return call_perplexity(prompt)