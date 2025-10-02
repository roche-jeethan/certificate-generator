"""
email_sender.py

Usage example:
python email_sender.py --zip certificates.zip --csv participants.csv --smtp-server smtp.gmail.com --smtp-port 587 --email your-email@gmail.com --password your-app-password
"""

import argparse
import csv
import os
import smtplib
import sys
import zipfile
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Tuple
import re
from dotenv import load_dotenv


def sanitize_filename(name: str) -> str:
    if not name or not name.strip():
        return "participant"
    s = re.sub(r"\s+", "_", name.strip())
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", s)
    return s[:120] or "participant"


def load_participants_with_emails(csv_path: str) -> List[Tuple[str, str]]:
    participants = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
    except UnicodeDecodeError:
        with open(csv_path, 'r', encoding='latin-1') as f:
            content = f.read().strip()
    
    if not content:
        return participants
    
    lines = content.splitlines()
    reader = csv.reader(lines)
    
    for row_idx, row in enumerate(reader):
        if len(row) >= 2:
            name = row[0].strip() if row[0] else ""
            email = row[1].strip() if row[1] else ""
            if name and email and "@" in email:
                participants.append((name, email))
            else:
                print(f"Warning: Invalid data in row {row_idx + 1}: {row}", file=sys.stderr)
        elif len(row) == 1 and row[0].strip():
            print(f"Warning: Missing email for '{row[0].strip()}' in row {row_idx + 1}", file=sys.stderr)
    
    return participants


def extract_certificates_from_zip(zip_path: str) -> Dict[str, bytes]:
    certificates = {}
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for filename in zf.namelist():
                if filename.endswith('.png'):
                    name_part = os.path.splitext(filename)[0]
                    certificates[name_part] = zf.read(filename)
    except Exception as e:
        raise RuntimeError(f"Failed to extract certificates from ZIP: {e}")
    
    return certificates


def load_email_body(body_path: str = "email_body.txt") -> str:
    default_body = """Dear {name},

Congratulations on getting this certificate for nothing. Please find your certificate attached to this email.

We appreciate your participation (for real) and wish you continued success.

Best regards,
Jeethan Roche - From VS Code"""
    
    if os.path.exists(body_path):
        try:
            with open(body_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception:
            return default_body
    return default_body


def create_email_message(sender_email: str, recipient_email: str, recipient_name: str, 
                        certificate_data: bytes, certificate_filename: str, 
                        subject: str = None, body_template: str = None) -> MIMEMultipart:
    
    if subject is None:
        subject = f"Your Certificate - {recipient_name}"
    
    if body_template is None:
        body_template = load_email_body()
    
    body = body_template.format(name=recipient_name)

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))
    
    attachment = MIMEApplication(certificate_data, _subtype='png')
    attachment.add_header('Content-Disposition', 'attachment', filename=certificate_filename)
    msg.attach(attachment)
    
    return msg


def send_certificates_via_email(participants: List[Tuple[str, str]], 
                               certificates: Dict[str, bytes],
                               smtp_server: str, smtp_port: int,
                               sender_email: str, sender_password: str,
                               custom_subject: str = None, body_template: str = None,
                               dry_run: bool = False) -> Tuple[int, int]:
    
    sent_count = 0
    failed_count = 0
    
    if dry_run:
        print("DRY RUN MODE - No emails will be sent")
        print("=" * 50)
    
    try:
        if not dry_run:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            print(f"Successfully connected to {smtp_server}")
    except Exception as e:
        print(f"ERROR: Failed to connect to SMTP server: {e}", file=sys.stderr)
        return 0, len(participants)
    
    for idx, (name, email) in enumerate(participants, 1):
        try:
            sanitized_name = sanitize_filename(name)
            
            if sanitized_name in certificates:
                certificate_data = certificates[sanitized_name]
                certificate_filename = f"{sanitized_name}.png"
                
                if dry_run:
                    print(f"[{idx}/{len(participants)}] Would send to {name} ({email}) - Certificate: {certificate_filename}")
                    sent_count += 1
                else:
                    msg = create_email_message(
                        sender_email, email, name, certificate_data, certificate_filename,
                        custom_subject, body_template
                    )
                    
                    server.send_message(msg)
                    print(f"[{idx}/{len(participants)}] ✓ Sent to {name} ({email})")
                    sent_count += 1
            else:
                print(f"[{idx}/{len(participants)}] ✗ Certificate not found for {name} (looking for: {sanitized_name})", file=sys.stderr)
                failed_count += 1
                
        except Exception as e:
            print(f"[{idx}/{len(participants)}] ✗ Failed to send to {name} ({email}): {e}", file=sys.stderr)
            failed_count += 1
    
    if not dry_run:
        try:
            server.quit()
        except Exception:
            pass
    
    return sent_count, failed_count


def send_emails(zip_path="certificates.zip", csv_path="participants.csv", 
                smtp_server="smtp.gmail.com", smtp_port=587, sender_email=None, 
                sender_password=None, custom_subject=None, body_template=None, 
                dry_run=False):
    
    load_dotenv()
    
    if sender_password is None:
        sender_password = os.getenv("APP_PASSWORD")
    
    if not os.path.exists(zip_path):
        print(f"ERROR: ZIP file not found: {zip_path}", file=sys.stderr)
        return False
    
    if not os.path.exists(csv_path):
        print(f"ERROR: CSV file not found: {csv_path}", file=sys.stderr)
        return False
    
    try:
        participants = load_participants_with_emails(csv_path)
    except Exception as e:
        print(f"ERROR: Failed to load participants: {e}", file=sys.stderr)
        return False
    
    if not participants:
        print("ERROR: No valid participants with emails found in CSV file", file=sys.stderr)
        return False
    
    print(f"Loaded {len(participants)} participants with email addresses")
    
    try:
        certificates = extract_certificates_from_zip(zip_path)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return False
    
    print(f"Extracted {len(certificates)} certificates from ZIP file")
    
    if dry_run:
        print("\nRunning in DRY RUN mode - no emails will be sent")
    
    sent_count, failed_count = send_certificates_via_email(
        participants, certificates, smtp_server, smtp_port,
        sender_email, sender_password, custom_subject, body_template, dry_run
    )
    
    print(f"\nEmail Summary:")
    print(f"Successfully sent: {sent_count}")
    print(f"Failed: {failed_count}")
    print(f"Total participants: {len(participants)}")
    
    if failed_count > 0:
        print(f"\nNote: {failed_count} emails failed. Check the error messages above.")
        return False
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Send certificates via email to participants")
    parser.add_argument("--zip", required=False, default="certificates.zip", help="Path to certificates ZIP file")
    parser.add_argument("--csv", required=False, default="participants.csv", help="Path to participants CSV file (name,email format)")
    parser.add_argument("--smtp-server", required=False, default="smtp.gmail.com", help="SMTP server address (e.g., smtp.gmail.com)")
    parser.add_argument("--smtp-port", type=int, default=587, help="SMTP server port (default: 587)")
    parser.add_argument("--email", required=True, help="Your email address")
    parser.add_argument("--password", default=os.getenv("APP_PASSWORD"), help="Your email password or app password (default: APP_PASSWORD env var)")
    parser.add_argument("--subject", help="Custom email subject")
    parser.add_argument("--body", help="Custom email body")
    parser.add_argument("--dry-run", action="store_true", help="Test run without sending actual emails")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.zip):
        print(f"ERROR: ZIP file not found: {args.zip}", file=sys.stderr)
        sys.exit(1)
    
    if not os.path.exists(args.csv):
        print(f"ERROR: CSV file not found: {args.csv}", file=sys.stderr)
        sys.exit(1)
    
    try:
        participants = load_participants_with_emails(args.csv)
    except Exception as e:
        print(f"ERROR: Failed to load participants: {e}", file=sys.stderr)
        sys.exit(1)
    
    if not participants:
        print("ERROR: No valid participants with emails found in CSV file", file=sys.stderr)
        sys.exit(1)
    
    print(f"Loaded {len(participants)} participants with email addresses")
    
    try:
        certificates = extract_certificates_from_zip(args.zip)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Extracted {len(certificates)} certificates from ZIP file")
    
    if args.dry_run:
        print("\nRunning in DRY RUN mode - no emails will be sent")
    
    sent_count, failed_count = send_certificates_via_email(
        participants, certificates, args.smtp_server, args.smtp_port,
        args.email, args.password, args.subject, args.body, args.dry_run
    )
    
    print(f"\nEmail Summary:")
    print(f"Successfully sent: {sent_count}")
    print(f"Failed: {failed_count}")
    print(f"Total participants: {len(participants)}")
    
    if failed_count > 0:
        print(f"\nNote: {failed_count} emails failed. Check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()