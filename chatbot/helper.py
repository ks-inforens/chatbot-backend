import re

def linkify_urls(text):
    url_pattern = r"https?://[^\s\)\]\}]+"

    def replacer(match):
        url = match.group(0)
        cleaned_url = url.replace('--', '')
        return f'[{cleaned_url}]({cleaned_url})'

    return re.sub(url_pattern, replacer, text)