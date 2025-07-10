#  Auto Meeting Summarizer

This Python project fetches meeting `.mp4` files from a shared Google Drive folder, converts them to `.mp3`, transcribes them using AssemblyAI, summarizes using a Hugging Face model, and sends the summary via Gmail.

##  Requirements

- Python 3.8+
- FFmpeg installed and in system PATH
- Gmail App Password (for SMTP email sending)
- AssemblyAI API key
- Google Cloud Service Account JSON file
- Drive folder shared with service account email

##  Folder Structure

- `meeting_summarizer.py` → Main script
- `requirements.txt` → Required packages
- `credentials.json` → Your downloaded service account JSON
- `token.json` → Generated after first Google Drive API call
- `.gitignore` → Ignore sensitive/media files

##  How to Run

1. Install requirements:
```bash
pip install -r requirements.txt
```

2. Set up your credentials in `meeting_summarizer.py`.

3. Place your `service_account.json` in the project root.

4. Run the script:
```bash
python meeting_summarizer.py
```

##  Output
- `meeting_summary.md` → Saved locally
- Transcribed and summarized content is emailed to you
