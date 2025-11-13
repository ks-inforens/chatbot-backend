import requests

def get_user_details():
    print("Please enter your details below.")
    citizenship = input("Country of citizenship: ")
    preferred_country = input("Preferred country for study: ")
    level = input("Level of study (Undergraduate, Postgraduate, PhD): ")

    uni_input = input("Preferred university/universities (comma-separated, press Enter to skip): ")
    preferred_universities = [u.strip() for u in uni_input.split(",")] if uni_input else []

    field = input("Field of study (e.g. Data Science, Engineering): ")
    course_intake = input("Course intake (e.g. September 2025) (optional, press Enter to skip): ")
    academic_perf = input("Current/previous academic performance (GPA, % or degree class) (optional, press Enter to skip): ")
    age = input("Age (optional, press Enter to skip): ")
    gender = input("Gender (optional, press Enter to skip): ")
    disability = input("Disability status (optional, press Enter to skip): ")
    extracurricular = input("Any extracurricular activities (e.g. sports) (optional, press Enter to skip): ")

    return {
        "citizenship": citizenship,
        "preferred_country": preferred_country,
        "level": level,
        "preferred_universities": preferred_universities,
        "field": field,
        "course_intake": course_intake if course_intake else None,
        "academic_perf": academic_perf if academic_perf else None,
        "age": age if age else None,
        "gender": gender if gender else None,
        "disability": disability if disability else None,
        "extracurricular": extracurricular if extracurricular else None,
    }

def build_prompt(user):
    lines = [
        "You are an expert on global scholarships. A student has provided their profile details:\n",
    ]

    if user.get('citizenship'):
        lines.append(f"Citizenship: {user['citizenship']}")
    if user.get('level'):
        lines.append(f"Desired level of study: {user['level']}")
    if user.get('field'):
        lines.append(f"Preferred field of study: {user['field']}")
    if user.get('academic_perf'):
        lines.append(f"Academic performance: {user['academic_perf']}")
    if user.get('disability'):
        lines.append(f"Disability: {user['disability']}")
    if user.get('preferred_country'):
        lines.append(f"Preferred country of study: {user['preferred_country']}")
    if user.get('preferred_universities'):
        lines.append(f"Preferred university: {user['preferred_universities']}")
    if user.get('course_intake'):
        lines.append(f"Course intake: {user['course_intake']}")
    if user.get('age'):
        lines.append(f"Date of Birth: {user['dob']} - use this to calculate age")
    if user.get('gender'):
        lines.append(f"Gender: {user['gender']}")
    if len(user.get("activity", [])) > 0:
        lines.append(f"Extracurricular activities: {user['activity'][0]['description']}")

    lines.append("""
Based on this information, recommend the most relevant scholarships for this student.
Respond ONLY with a SINGLE valid JSON object with a key "scholarships" whose value is an array of objects, each object has:
  - "name": Name of the scholarship.
  - "description": A SHORT description of the scholarship, maximum 20 words.

Example output:
{
  "scholarships": [
    {
      "name": "Commonwealth Scholarship",
      "description": "Covers tuition and living expenses for postgraduate study in the UK for students from eligible Commonwealth countries.",
      "deadline": "Dec 12, 2025 (mmm dd, yyyy format)"
    },
    {
      "name": "...",
      "description": "...",
      "deadline": "... (mmm dd, yyyy format)"
    }
  ]
}

The scholarships recommended must be relevant to the student's profile.
Do not add any explanations or text before or after the JSON.
Ensure the JSON you return is syntactically valid and parseable.
""")

    return "\n".join(lines)

def fetch_scholarships(prompt):
    from flask import current_app
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {current_app.config.get("PERPLEXITY_API_KEY")}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "sonar",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000,
        "reasoning_effort": "medium"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        output = data["choices"][0]["message"]["content"]
        return output
    else:
        raise Exception(f"Error {response.status_code}: {response.text}")

if __name__ == "__main__":
    user_data = get_user_details()
    prompt = build_prompt(user_data)
    fetch_scholarships(prompt)