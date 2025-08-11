"""
Language Learning Bot:

Generate 5 new words a day. Sends to you via text.
"""
from google import genai
from pydantic import BaseModel
import json
import smtplib, ssl
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText

load_dotenv()

API_KEY = os.getenv("API_KEY")
FILENAME = "history.json"
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
PASSWORD = os.getenv("APP_PASS")

class NewWord(BaseModel):
    thai_word: str
    english_meaning: str
    tone: str

def generate_5_words(oldWords):
    """
    Using Google Gemini API, uses the provided documents to generate 5 new
    vocabulary words for learning. Will not generate duplicate words from
    the history.json file.
    """
    client = genai.Client(api_key=API_KEY)
    book = client.files.upload(file="Collins_Thai_3000_words_and_phrases.pdf")
    dictionary = client.files.upload(file="thai-to-english dictionary.pdf")
    most_common_words = client.files.upload(file="most-common-words.pdf")

    prompt = f"Use this book: {book} as a guide and these most common words in english: {most_common_words} and the fact that I am a intermediate Thai speaker with family who speaks Thai." \
    f"Generate 5 thai words, their translations, and the tone that I need to learn to master the language in as short of time as possible." \
    f"Do not include any words already in this list {oldWords}" \
    f"Only generate 1) the words, 2) their english translation, 3) and the tone. Cross check the tone and definitions with this dictionary: {dictionary}" \
    f"Do not add extra explanations or text before or after these three items."

    response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[prompt],
                config={
                        "response_mime_type": "application/json",
                        "response_schema": list[NewWord],
                        }
    )

    words: list[NewWord] = response.parsed

    return words


def get_old_words(filename):
    """
    Opens history.json and retrieves words already generated.
    If this is the first time running, will use an empty list
    instead.
    """
    try:
        with open(filename, 'r') as file:
            oldWords = json.load(file)
    except FileNotFoundError:
        oldWords = [] 
    
    return oldWords


def save_words_to_history(filename, words, oldWords):
    """
    Adds newly generated words to old words and updates the
    history.json file.
    """
    for word in words:
        if word.dict() not in oldWords:
            oldWords.append(word.dict())

    with open(filename, "w") as f:
        json.dump(oldWords, f, indent=4)


def send_words_to_user(words):
    """
    Using the Gmail API, sends an email containing the 5
    newly generated words to the user.
    """
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = SENDER_EMAIL
    receiver_email = RECEIVER_EMAIL
    password = os.getenv("APP_PASS")

    body = "\n".join(
        f"{w.thai_word} — {w.english_meaning} ({w.tone})"
        for w in words
    )

    message = MIMEText(body, "plain", "utf-8")
    message["Subject"] = ""  # empty for SMS/MMS
    message["From"] = "Language Learning Bot"
    message["To"] = receiver_email

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())


def main():
    oldWords = get_old_words(FILENAME)
    words = generate_5_words(oldWords)
    save_words_to_history(FILENAME, words, oldWords)
    send_words_to_user(words)
    

if __name__ == "__main__":
    main()