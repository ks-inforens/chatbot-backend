import requests
import re

from chatbot.helper import linkify_urls

class PerplexityChatbot:
    def __init__(self, api_key, content_file_path="inforens_scraped_data.txt"):
        self.api_key = api_key
        self.content_file_path = content_file_path
        self.full_text = self._load_content()
        self.valid_urls = self._extract_valid_urls()

    def _load_content(self):
        try:
            with open(self.content_file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            print("⚠️ Content file not found.")
            return ""

    def _extract_valid_urls(self):
        urls = set(re.findall(r"https?://[^\s,)]+", self.full_text))
        return urls

    def _postprocess_answer(self, answer):
        # Remove numbered citation marks ([1][2] etc).
        answer = re.sub(r'\[\d+\]', '', answer)
        answer = re.sub(r"\[https?://([^\]]+)\]\(https?://[^\)]+\)", r"https://\1", answer)
        return answer

    def ask_question(self, user_question):
        if not self.full_text:
            return "No content loaded. Please check the .txt file."

        prompt = f"""{{
            "role": "system",
            "content": "You are a chatbot assistant for Inforens, dedicated to helping students and users interested in international education, study abroad, and Inforens's company offerings. Strictly follow these guidelines:\\n\
            1. You MUST ONLY answer questions about the following: Inforens (company, features, services, membership, offers, events, practical use, benefits, history, technology); and topics central to the international student journey, including: studying abroad, planning for or applying to universities abroad, visa and immigration requirements or guidance, scholarships, housing/accommodation, money and banking, SIM cards, jobs, internships, cost of living, travel, health and safety, student life, settling or adapting to study destinations, alumni/post-study experiences, and practical advice relevant to international students globally.\\n\
            2. For ALL other questions, regardless of topic—including programming, technical, entertainment, sports, hobbies, cooking, random trivia, or any subject not whitelisted in (1)—politely refuse and reply exactly: 'Sorry, I can only answer questions about Inforens, international students, or studying and living abroad. For other matters, please contact Inforens support at https://www.inforens.com/contact-us.'\\n\
            3. For valid questions, always use the 'Inforens Content' below first, answering with specific detail, insight, benefits, and including up to five relevant Inforens service/support/CTA/mentor links as plain URLs in your answer—never in markdown, brackets, or as citations. Do not use the homepage except where it is truly best.\\n\
            4. If no relevant info is found in Inforens content, you may briefly supplement with trusted government/university/official info, but ALWAYS finish with a plain Inforens CTA/support/service link.\\n\
            5. Keep all answers clear, practical, friendly, and concise (2 to 4 sentences preferred), never cutting off mid-sentence or mid-word.\\n\
            6. All links should be structured starting with https:// \\n\
            7. Each response MUST contain at least ONE CTA/link to the most relevant Inforens page based on the context of the question.\\n\
            8. When aked to present information in a table, USE A LISTING APPROACH instead, DO NOT display information as a Markdown table.\\n\
            9. Never mention or compare competitors. Do not use citation numbers, footnotes, markdown links, or brackets—only add URLs as plain text in sentences.\\n\\n\
            Inforens Content:\\n{self.full_text}\\n\\n\
            Question: {user_question}\\n\
            Answer:"
        }}"""

        payload = {
            "model": "sonar",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 400
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            raw_answer = response.json()['choices'][0]['message']['content']
            processed_answer = self._postprocess_answer(raw_answer)
            processed_answer = linkify_urls(processed_answer)
            return processed_answer.strip()
        except Exception as e:
            return f"API request failed: {str(e)}"
