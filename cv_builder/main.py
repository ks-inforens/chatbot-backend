import sys
from cv_builder.parse_cv import extract_info_from_pdf, extract_info_from_docx
from cv_builder.prompt_builder import build_prompt_CV
from cv_builder.generate_cv import call_perplexity  
from cv_builder.save import save_as_docx

def get_work_experience_entries():
    entries = []
    while True:
        print("\n--- Enter Work Experience Entry ---")
        company = input("Company Name: ").strip()
        location = input("Location (optional): ").strip()
        role = input("Role/Designation: ").strip()
        duration = input("Duration: ").strip()
        responsibilities = []

        print("Enter responsibilities (type 'done' when finished):")
        while True:
            resp = input(" - ")
            if resp.strip().lower() == "done": #when you enter done, it will end
                break
            elif resp.strip():
                responsibilities.append(resp.strip())

        entry = f"{role} at {company}, {location or 'N/A'} ({duration})\n" + "\n".join(f"- {r}" for r in responsibilities)
        entries.append(entry)
        #ask if they want to add another work ex
        more = input("Add another work experience entry? (yes/no): ").strip().lower()
        if more != "yes":
            break
    return "\n\n".join(entries)

def get_education_entries():
    entries = []
    while True:
        print("\n--- Enter Education Entry ---")
        university = input("University Name: ").strip()
        location = input("Location (optional): ").strip()
        degree = input("Degree: ").strip()
        completed = input("Is this course ongoing or completed?: ").strip().lower()
        course = input("Course Name: ").strip()
        duration = input("Duration: ").strip()
        relevant = input("Relevant Coursework (optional): ").strip()
        outcome = input("Outcome / Expected outcome (optional): ").strip()

        entry = f"{degree} in {course}, {university}, {location or 'N/A'} ({duration})"
        if relevant:
            entry += f"\nRelevant Coursework: {relevant}"
        if completed == "completed":
            entry += f"\nOutcome: {outcome}"
        elif completed == "ongoing":
            entry += f"\nExpected outcome: {outcome}"

        entries.append(entry)

        more = input("Add another education entry? (yes/no): ").strip().lower()
        if more != "yes":
            break
    return "\n\n".join(entries)

def main():
    workflow = input("Choose workflow (new / existing): ").lower() #new cv or existing cv
    user_data = {}
    has_work_exp = None

    if workflow == "new":
        has_work_exp = input("Do you have relevant work experience? (yes/no): ").strip().lower()
        if has_work_exp not in ("yes", "no"):
            print("Please answer yes or no")
            sys.exit(1)

        user_data = {
            "full_name": input("Full name: "),
            "target_country": input("Target country: "),
            "cv_length": input("CV length (1 or 2): (optional) "),
            "style": input("CV style (Formal / Modern / Creative / ATS-friendly / etc.): (optional) "),
            "email": input("Email: "),
            "phone": input("Phone number: "),
            "linkedin": input("LinkedIn URL (optional): "),
            "location": input("Location: (optional) "),
            "work_experience": get_work_experience_entries() if has_work_exp == "yes" else "",
            "education": get_education_entries(),
            "skills": input("Skills: "),
            "certificates": input("Certificates and awards (optional): "),
            "projects": input("Projects: (optional) ")
        }

    elif workflow == "existing":
        file_path = input("Path to CV file (PDF or DOCX): ").strip()
        if file_path.endswith(".pdf"):
            user_data = extract_info_from_pdf(file_path)
        elif file_path.endswith(".docx"):
            user_data = extract_info_from_docx(file_path)
        else:
            print("Unsupported file type")
            sys.exit(1)

        choice = input("Reformat for a (country/company)? ").lower()
        if choice == "country":
            user_data["target_country"] = input("Enter target country: ")
        else:
            user_data["job_description"] = input("Paste JD here: ")

        user_data["cv_length"] = input("CV length (1 or 2 pages): (optional) ")
        user_data["style"] = input("CV style (Formal / Modern / Creative / ATS-friendly / etc.): (optional) ")

    else:
        print("Invalid workflow")
        sys.exit(1)

    prompt = build_prompt(user_data, has_work_exp)

    try:
        generated_cv = call_perplexity(prompt)
        print("\nGenerated CV:\n")
        print(generated_cv)

        #need to find alternatives for downloading cv
        download_choice = input("\nDo you want to download the CV? (yes/no): ").strip().lower()
        if download_choice == "yes":
            file_type = input("Choose file format (pdf/docx): ").strip().lower()
            if file_type == "docx":
                save_as_docx(generated_cv)
            else:
                print("Unsupported file format. Please choose 'pdf' or 'docx'.")
    except Exception as e:
        print(f"Error generating CV: {e}")

def generate_cv_from_data(user_data, workflow, has_work_exp=None):
    if workflow == "new":
        if has_work_exp not in ("yes", "no"):
            raise ValueError("Invalid has_work_exp value")    
    elif workflow == "existing": pass
    else: raise ValueError("Invalid workflow choice")
    
    prompt = build_prompt(user_data, has_work_exp)
    generated_cv = call_perplexity(prompt)
    return generated_cv

if __name__ == "__main__":
    main()
