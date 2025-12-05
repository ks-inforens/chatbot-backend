from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
from models import db, Query  , CVUpload
from chatbot.chatbot import PerplexityChatbot
from scholarship_finder.scholarship import build_prompt as scholarship_prompt, fetch_scholarships
from sop_builder.sop_builder import generate_sop, save_pdf, save_docx
from cv_builder.save import save_as_docx  
from cv_builder.parse_cv import extract_info_from_pdf, extract_info_from_docx, extract_json_object
from cv_builder.prompt_builder import build_prompt_CV as cv_prompt
from cv_builder.generate_cv import call_perplexity
from flasgger import swag_from
import requests
import time
import json
import tempfile
import os
import re

bp = Blueprint('api', __name__, url_prefix='/api')

bot = None

ALLOWED_EXTENSIONS = {'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.before_app_request
def create_chatbot():
    global bot
    bot = PerplexityChatbot(
        api_key=current_app.config.get('PERPLEXITY_API_KEY'),
        content_file_path=current_app.config.get('CONTENT_FILE')
    )

# @bp.after_request
# def add_cors_headers(response):
#     response.headers.add('Access-Control-Allow-Origin', 'https://inforens-chatbot.vercel.app')
#     response.headers.add('Access-Control-Allow-Credentials', 'true')
#     response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
#     response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
#     return response

@bp.route('/ask', methods=['POST'])
@swag_from('specs/api_spec.yaml', endpoint='api.ask')
def ask():
    start = time.time()
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    session_id = data.get("sessionId")
    user_id = data.get("userId")

    if not question:
        return jsonify({"error": "Question is required"}), 400

    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    ua = request.headers.get("User-Agent")

    try:
        raw_answer = bot.ask_question(question)
        latency_ms = int((time.time() - start) * 1000)

        query = Query(
            session_id=session_id,
            user_id=user_id,
            question=question,
            answer=raw_answer["answer"],
            model="perplexity-sonar",
            latency_ms=latency_ms,
            success=True,
            ip_address=ip,
            user_agent=ua,
        )

        db.session.add(query)
        db.session.commit()

        return jsonify({
            "answer": raw_answer["answer"],
            "links": raw_answer["links"],
            "latencyMs": latency_ms,
            "messageId": query.id
        })

    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        current_app.logger.error(f"Error during ask: {e}")
        return jsonify({"error": f"Failed to get answer: {str(e)}"}), 500

@bp.route('/feedback', methods=['POST'])
@swag_from('specs/api_spec.yaml', endpoint='api.feedback')
def feedback():
    data = request.get_json()
    message_id = data.get("messageId")
    thumbs_up = data.get("thumbsUp", False)
    thumbs_down = data.get("thumbsDown", False)
    feedback_text = data.get("feedback", "")

    if not message_id:
        return jsonify({"error": "Message ID is required"}), 400

    try:
        query = Query.query.get(message_id)
        if not query:
            return jsonify({"error": "Message ID not found"}), 404

        query.thumbs_up = thumbs_up
        query.thumbs_down = thumbs_down
        query.feedback = feedback_text

        db.session.commit()

        return jsonify({"status": "ok"})
    except Exception as e:
        current_app.logger.error(f"Error updating feedback: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route("/transcribe")
@swag_from('specs/api_spec.yaml', endpoint='api.transcribe')
def transcribe():
    try:
        audio_file = request.files["file"]
        response = requests.post(
            "https://api.perplexity.ai/audio/transcriptions",
            headers={"Authorization": f"Bearer {current_app.config.get('PERPLEXITY_API_KEY')}"},
            files={"file": (audio_file.filename, audio_file, audio_file.mimetype)},
        )
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@bp.route("/scholarships", methods=["POST"])
@swag_from('specs/api_spec.yaml', endpoint='api.scholarships')
def scholarships():
    try:
        data = request.get_json(silent=True) or {}
        required_fields = ["citizenship", "preferred_country", "level", "field"]

        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

        prompt = scholarship_prompt(data)
        results = fetch_scholarships(prompt)  

        results = extract_json_object(results)

        scholarships_data = json.loads(results)

        return jsonify({
            "scholarships": scholarships_data["scholarships"],  
            "prompt": prompt
        })

    except Exception as e:
        current_app.logger.error(f"Error in /scholarships: {e}")
        return jsonify({"error": str(e)}), 500
    
@bp.route("/sop", methods=["POST"])
@swag_from('specs/api_spec.yaml', endpoint='api.sop')
def sop():
    try:
        data = request.get_json(silent=True) or {}
        required_fields = ["name", "country_of_origin", "intended_degree", 
                           "preferred_country", "field_of_study", "preferred_uni"]

        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

        token = current_app.config.get("PERPLEXITY_API_KEY")
        sop, prompt = generate_sop(data, token)

        if not sop:
            return jsonify({"error": "Failed to generate SOP"}), 500

        return jsonify({
            "sop": sop,
            "prompt": prompt,
            "word_count": len(sop.split())
        })

    except Exception as e:
        current_app.logger.error(f"Error in /sop: {e}")
        return jsonify({"error": str(e)}), 500
    
@bp.route("/sop/download/pdf", methods=["POST"])
@swag_from('specs/api_spec.yaml', endpoint='api.sop_download_pdf')
def sop_download_pdf():
    try:
        data = request.get_json()
        sop_text = data.get("sop")
        if not sop_text:
            return {"error": "SOP text is required"}, 400

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp.close()  
        save_pdf(tmp.name, sop_text)

        response = send_file(
            tmp.name,
            as_attachment=True,
            download_name="SOP.pdf",
            mimetype="application/pdf"
        )
        
        @response.call_on_close
        def cleanup():
            try:
                os.unlink(tmp.name)
            except Exception:
                current_app.logger.warning(f"Failed to delete temp file: {tmp.name}")

        return response

    except Exception as e:
        current_app.logger.error(f"Error in /sop/download/pdf: {e}")
        return {"error": str(e)}, 500

@bp.route("/sop/download/docx", methods=["POST"])
@swag_from('specs/api_spec.yaml', endpoint='api.sop_download_docx')
def sop_download_docx():
    try:
        data = request.get_json()
        sop_text = data.get("sop")
        if not sop_text:
            return {"error": "SOP text is required"}, 400

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
        tmp.close()
        save_docx(tmp.name, sop_text)

        response = send_file(
            tmp.name,
            as_attachment=True,
            download_name="SOP.docx",
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        @response.call_on_close
        def cleanup():
            try:
                os.unlink(tmp.name)
            except Exception:
                current_app.logger.warning(f"Failed to delete temp file: {tmp.name}")

        return response

    except Exception as e:
        current_app.logger.error(f"Error in /sop/download/docx: {e}")
        return {"error": str(e)}, 500

@bp.route("/cv/download/docx", methods=["POST"])
@swag_from('specs/api_spec.yaml', endpoint='api.cv_download_docx')
def cv_download_docx():
    try:
        data = request.get_json()
        if not data:
            return {"error": "JSON body required"}, 400

        workflow = data.get("workflow")
        if not workflow:
            return {"error": "workflow field is required"}, 400

        user_data = _extract_user_data(data, workflow)
        generated_cv = call_perplexity(cv_prompt(user_data))

        print("Generated CV:\n" + generated_cv)

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
        tmp.close()
        save_as_docx(generated_cv, tmp.name)

        response = send_file(
            tmp.name,
            as_attachment=True,
            download_name="Generated_CV.docx",
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        @response.call_on_close
        def cleanup():
            try:
                os.unlink(tmp.name)
            except Exception:
                current_app.logger.warning(f"Failed to delete temp file: {tmp.name}")

        return response

    except Exception as e:
        current_app.logger.error(f"Error in /cv/download/docx: {e}")
        return {"error": str(e)}, 500
    
@bp.route("/cv/generate/coverLetter", methods=["POST"])
@swag_from('specs/api_spec.yaml', endpoint='api.generate_cover_letter')
def generate_cover_letter():
    try:
        data = request.get_json()
        if not data:
            return {"error": "JSON body required"}, 400

        user_data = _extract_user_data(data, "existing")
        cover_letter_format = """
                                Full Name\n
                                Location\n
                                Phone number (in +countryCode-number format, eg, +44-1234567890)\n
                                Email\n\n

                                Today's Date in MM dd, yyyy format (where MM is the full month name)\n\n

                                Dear Hiring Manager (or title.+name of the recruiter if provided, eg, Mr. Smith),\n

                                Opening Paragraph\n
                                Body Paragraph(s)\n
                                Closing Paragraph\n\n

                                Sincerely,\n
                                Full Name           
                               """

        if not user_data:
            return {"error": "user_data is required"}, 400

        cover_prompt = (
            "Using the CV information below and the job description, create a professional cover letter:\n\n"
            f"CV information:\n{user_data}\n\nJob Description:\n{user_data['job_description']}\n\n"
            "State role/source, align 2-3 key skills with examples, show company insight, conclude with interview request. Make it highly ATS-friendly, and have a human written tone."
            f"Make sure to use this format:\n {cover_letter_format}"
        )

        generated_cover_letter = call_perplexity(cover_prompt)

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
        tmp.close()
        save_as_docx(generated_cover_letter, tmp.name)

        response = send_file(
            tmp.name,
            as_attachment=True,
            download_name="Generated_Cover_Letter.docx",
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        @response.call_on_close
        def cleanup():
            try:
                os.unlink(tmp.name)
            except Exception:
                current_app.logger.warning(f"Failed to delete temp file: {tmp.name}")

        return response

    except Exception as e:
        current_app.logger.error(f"Error in /cover-letter/generate: {e}")
        return {"error": str(e)}, 500

def _extract_user_data(data, workflow):
    if workflow == "new":
        return {
            "full_name": data.get("full_name"),
            "target_country": data.get("target_country"),
            "email": data.get("email"),
            "phone": data.get("phone"),
            "links": data.get("links"),
            "location": data.get("location"),
            "work_experience": data.get("work_experience", ""),
            "education": data.get("education", ""),
            "skills": data.get("skills"),
            "languages_known": data.get("languages_known"),
            "certificates": data.get("certificates"),
            "projects": data.get("projects"),
            "additionalSec": data.get("additionalSec")
        }
    elif workflow == "existing":
        return_fields = {}
        if (data.get("target_country")): return_fields["target_country"] = data.get("target_country")
        elif (data.get("target_company") or data.get("job_description")):
            return_fields["target_company"] = data.get("target_company")
            return_fields["job_description"] = data.get("job_description")
        elif (data.get("target_role")): return_fields["target_role"] = data.get("target_role")
        
        return_fields["full_name"] = data.get("full_name")
        return_fields["email"] = data.get("email")
        return_fields["phone"] = data.get("phone")
        return_fields["links"] = data.get("links")
        return_fields["location"] = data.get("location")
        return_fields["work_experience"] = data.get("work_experience", "")
        return_fields["education"] = data.get("education", "")
        return_fields["skills"] = data.get("skills")
        return_fields["languages_known"] = data.get("languages_known")
        return_fields["certificates"] = data.get("certificates")
        return_fields["projects"] = data.get("projects")
        return_fields["additionalSec"] = data.get("additionalSec")
                
        return return_fields
    else:
        raise ValueError("Invalid workflow")
    
@bp.route('/upload-cv', methods=['POST'])
@swag_from('specs/api_spec.yaml', endpoint='api.upload_cv')
def upload_cv():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    session_id = request.form.get("session_id")
    user_id = request.form.get("user_id")

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type"}), 400

    filename = secure_filename(file.filename)
    upload_folder = current_app.config.get('UPLOAD_FOLDER', '/tmp/uploads')
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)

    if filename.endswith('.pdf'):
        info = extract_info_from_pdf(file_path)
    else:
        info = extract_info_from_docx(file_path)

    # print("Before cleanup\n" + info)

    info_clean = info.strip()
    info_clean = re.sub(r'^`{3}', '', info_clean)
    info_clean = re.sub(r'`{3}$', '', info_clean)
    info_clean = info_clean.strip()

    # print("After cleanup\n" + info_clean)

    if not (info_clean.startswith('{') and info_clean.endswith('}')):
        current_app.logger.error("Parsed file info does not start and end with curly braces: %r", info_clean)
        return jsonify({"error": "Invalid JSON output from file parsing."}), 422

    try:
        data = json.loads(info_clean)
        cv_upload = CVUpload(session_id=session_id, user_id=user_id, json_response=data)
        db.session.add(cv_upload)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Error parsing cleaned JSON info: {e}")
        return jsonify({"error": "File info could not be parsed as JSON."}), 422

    return jsonify(data), 200