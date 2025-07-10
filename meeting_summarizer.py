import os
import io
import time
import requests
from pathlib import Path
from transformers import pipeline
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

# === CONFIG ===
ASSEMBLYAI_API_KEY = "YOUR API KEY "
SERVICE_ACCOUNT_FILE = "meetingsummarybot-465308-569908b2a5c7.json"
MP3_PATH = "meeting_audio.mp3"
VIDEO_PATH = "meeting_video.mp4"
TRANSCRIPT_FILE = "meeting_transcript.txt"
SUMMARY_FILE = "meeting_summary.md"
DRIVE_FOLDER_ID = "YOUR DRIVE FOLDER ID HERE"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# Email Config
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "parthasarathyg693@gmail.com"
SENDER_PASSWORD = "YOUR SENDER EMAIL PASSWORD"
RECEIVER_EMAIL = "parthasarathyg694@gmail.com"

# === AUTH: Google Drive ===
def authenticate_google_drive():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build("drive", "v3", credentials=creds)
    return service

# === Download latest .mp4 from Drive ===
def download_latest_video_from_drive(service):
    print(" Searching for .mp4 file in Drive...")
    query = f"'{DRIVE_FOLDER_ID}' in parents and mimeType='video/mp4'"
    results = service.files().list(
        q=query, orderBy="createdTime desc", pageSize=1, fields="files(id, name)"
    ).execute()
    files = results.get("files", [])
    if not files:
        raise Exception(" No .mp4 files found in the specified Drive folder.")
    file = files[0]
    print(f"⬇ Downloading: {file['name']} ...")
    request = service.files().get_media(fileId=file["id"])
    with open(VIDEO_PATH, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"    Progress: {int(status.progress() * 100)}%")
    print(" Download complete.")

# === Convert video to MP3 ===
def convert_to_mp3(video_path, audio_path):
    print(" Converting to MP3...")
    os.system(f'ffmpeg -i "{video_path}" -vn -acodec libmp3lame -ar 44100 -ac 2 -ab 192k -f mp3 "{audio_path}" -y')
    print(" MP3 conversion done.")

# === Transcribe Audio ===
def transcribe_audio_with_whisper(audio_path):
    print(" Transcribing audio using Hugging Face Whisper model...")
    asr = pipeline("automatic-speech-recognition", model="openai/whisper-base", device=-1)
    # Handle long audio by enabling long-form generation with timestamps
    transcript_result = asr(audio_path, return_timestamps=True)
    # If the result is a dict with 'chunks', concatenate text from all chunks
    if "chunks" in transcript_result:
        transcript = " ".join([chunk["text"] for chunk in transcript_result["chunks"]])
    else:
        transcript = transcript_result["text"]
    save_to_file(transcript, TRANSCRIPT_FILE)
    return transcript

# === Summarize ===
def summarize_with_huggingface(transcript):
    print(" Summarizing using Hugging Face in structured format...")

    instruction = """
You are an AI assistant helping summarize a business meeting transcript.

Extract the key content and organize it clearly into the following sections:

1. 🧩 **Agenda** – List all planned discussion topics at the start of the meeting.
2. ✅ **Tasks Completed** – List any updates or work marked as done.
3. 🔧 **Tasks In Progress** – Mention tasks that are ongoing or being worked on.
4. 🔮 **Future Action Items** – Clearly state the upcoming work or follow-up actions.
5. 📣 **Key Decisions Made** – Note any decisions finalized during the meeting.
6. 👥 **Participants Mentioned** – List the names or roles of key people who spoke.
7. 🧠 **Overall Meeting Intent** – Summarize the core reason for this meeting.

Guidelines:
- Use bullet points under each section.
- Remove irrelevant or repeated content.
- Focus on clarity and usefulness to a reader who didn’t attend.

Now summarize the following transcript:
"""


    full_text = instruction + transcript
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    CHUNK_SIZE = 1024
    chunks = [full_text[i:i + CHUNK_SIZE] for i in range(0, len(full_text), CHUNK_SIZE)]
    summary = ""
    for i, chunk in enumerate(chunks):
        print(f"   Summarizing chunk {i + 1}/{len(chunks)}...")
        result = summarizer(chunk, max_length=150, min_length=40, do_sample=False)
        summary += result[0]['summary_text'].strip() + "\n\n"
    save_to_file(summary, SUMMARY_FILE)
    return summary

# === Send Email ===
def send_email(subject, content):
    print(" Sending email...")
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(content, "plain"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(" Email sent successfully.")
    except Exception as e:
        print(" Email failed:", e)

# === Save Text File ===
def save_to_file(text, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

# === MAIN WORKFLOW ===
def main():
    try:
        service = authenticate_google_drive()
        download_latest_video_from_drive(service)
        convert_to_mp3(VIDEO_PATH, MP3_PATH)
        transcript = transcribe_audio_with_whisper(MP3_PATH)
        summary = summarize_with_huggingface(transcript)
        send_email(subject="Meeting Summary", content=summary)
    except Exception as err:
        print(" ERROR:", err)

# === Entry Point ===
if __name__ == "__main__":
    main()
