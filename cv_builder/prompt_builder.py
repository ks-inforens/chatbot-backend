def build_prompt_CV(user_data, raw_text=None):
    schema = """
{
  "additionalSec": [
    {
      "desc": "",
      "title": ""
    },
    ...
  ],
  "certifications": [
    {
      "date": "", (when they obtained it)
      "name": "",
      "organisation": "", (name of the issuing organization)
      "type": "" (either Certificate, Award, Scholarship or Recognition)
    },
    ...
  ],
  "education": [
    {
      "country": "",
      "course": "",
      "discipline": "",
      "level": "", (either Undergraduate, Post graduate or PhD)
      "location": "", (name of the city of study)
      "region": "", 
      "results": "",
      "start_date": "",
      "end_date": "",
      "university_name": ""
    },
    ...
  ],
  "email": "",
  "full_name": "",
  "languages_known": [...],
  "links": [
    {
      "name": "",
      "url": "" (in https:// format)
    },
    ...
  ],
  "location": "",
  "phone": "",
  "projects": [
    {
      "description": "",
      "link": "",
      "title": "",
      "type": "" (either Project, Research or Publication)
    },
    ...
  ],
  "skills": [...],
  "work_experience": [
    {
      "achievements": [...],
      "company_name": "",
      "start_date": "",
      "end_date": "",
      "job_title": "",
      "responsibilities": [...],
      "type_of_work": "" (either Full-time or Internship)
    },
    ...
  ]
}
"""

    if raw_text:
        prompt = f"""
You are an expert CV parser and formatter.
Extract structured information from the following CV text.

⚠️ Rules:
- Return ONLY valid JSON in the schema below.
- If any new sections exist in the CV (e.g., Languages, Positions of Responsibility), include them in JSON.
- If information is missing, leave the field empty, do not fabricate.
- Respect the JSON structure exactly as shown.

Schema:
{schema}

CV Text:
\"\"\" 
{raw_text}
\"\"\"
"""
    else:
        prompt = f"""
You are an expert CV generator. Use the provided information to create a professional CV.\n
Ensure that the CV is highly ATS-friendly and has a human written tone. \n
Incorporate strong action verbs, especially for leadership roles, such as these power action verbs:\n 
- Leadership: managed, orchestrated. \n
- Results: acheived, generated, maximised. \n
- Innovation: designed, implemented, streamlined.\n
These are just a handful of examples.\n
Include quantifiable results where possible.\n
Also, write a professional summary highlighting my goals ONLY IF I have work experience (if no work experience is mentioned, do NOT include a professional summary).\n  

⚠️ Rules:
- Return ONLY valid JSON in the schema below.
- Respect the JSON structure exactly as shown.
- If information is missing, leave the field empty, do not fabricate.
- There are 3 format options that could be provided:\n
  a) Format by country - for which we need to ensure that the CV format, layout and word selection is tailored to the chosen target/preferred country.
  b) Format by company - for which we need to ensure that all experiences, word selection/terminology is tailored to the provided target company and job description. Make sure to use ATS-friendly and powerful keywords to get hired for the job description.
  c) Format by role - for which we need to ensure that all experiences, word selection/terminology is tailored to the provided target/desired role. Make sure to use ATS-friendly and powerful keywords that strongly relate to the target/desired role.
- Strictly start and end the response with a curly bracket, do not include any other characters or text in the start or end.

Schema:
{schema}

User Data:
{user_data}
"""

    return prompt