import argparse
import sys
import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import shutil
from generator import generate_certificates
from email_sender import send_emails
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()

allowed_origins = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')
CORS(app, origins=allowed_origins)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def main():
    parser = argparse.ArgumentParser(description="Generate and send certificates")
    parser.add_argument("--x", type=int, help="X coordinate for name placement")
    parser.add_argument("--y", type=int, help="Y coordinate for name placement")
    parser.add_argument("--fontsize", type=int, default=90, help="Font size")
    parser.add_argument("--color", default="#000000", help="Text color")
    parser.add_argument("--outline", action="store_true", help="Add text outline")
    parser.add_argument("--dpi", type=int, default=600, help="DPI for output")
    parser.add_argument("--email", default="gdg.jeethan@gmail.com", help="Add email for sending certificates")
    parser.add_argument("--password", help="Email password")
    parser.add_argument("--dry-run", action="store_true", help="Test email sending")
    parser.add_argument("--subject", help="Custom email subject")
    parser.add_argument("--body", help="Custom email body")
    
    args = parser.parse_args()
    
    print("Generating certificates...")
    success = generate_certificates(
        x=args.x,
        y=args.y,
        fontsize=args.fontsize,
        color=args.color,
        outline=args.outline,
        dpi=args.dpi
    )
    
    if not success:
        print("Certificate generation failed")
        sys.exit(1)
        
    print("\nSending emails...")
    email_success = send_emails(
        sender_email=args.email,
        sender_password=args.password,
        custom_subject=args.subject,
        custom_body=args.body,
        dry_run=args.dry_run
    )
        
    if not email_success:
        print("Email sending failed")
        sys.exit(1)
    
    print("\nAll operations completed successfully!")


@app.route('/upload-files', methods=['POST'])
def upload_files():
    try:
        if 'participants' not in request.files or 'template' not in request.files:
            return jsonify({'error': 'Missing required files'}), 400
        
        participants_file = request.files['participants']
        template_file = request.files['template']
        email_body = request.form.get('emailBody', '')
        
        if participants_file.filename == '' or template_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        participants_path = os.path.join(UPLOAD_FOLDER, 'participants.csv')
        template_path = os.path.join(UPLOAD_FOLDER, 'template.png')
        email_body_path = os.path.join(UPLOAD_FOLDER, 'email_body.txt')
        
        participants_file.save(participants_path)
        template_file.save(template_path)
        
        if email_body.strip():
            with open(email_body_path, 'w', encoding='utf-8') as f:
                f.write(email_body)
        
        shutil.copy(participants_path, 'participants.csv')
        shutil.copy(template_path, 'template.png')
        if os.path.exists(email_body_path):
            shutil.copy(email_body_path, 'email_body.txt')
        
        return jsonify({'message': 'Files uploaded successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate-certificates', methods=['POST'])
def generate_certificates_endpoint():
    try:
        data = request.json
        x = data.get('x')
        y = data.get('y')
        fontsize = data.get('fontsize', 90)
        color = data.get('color', '#000000')
        outline = data.get('outline', False)
        dpi = data.get('dpi', 600)
        
        success = generate_certificates(
            x=x, y=y, fontsize=fontsize, color=color, outline=outline, dpi=dpi
        )
        
        if success:
            return jsonify({'message': 'Certificates generated successfully'}), 200
        else:
            return jsonify({'error': 'Certificate generation failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/send-emails', methods=['POST'])
def send_emails_endpoint():
    try:
        data = request.json
        sender_email = data.get('senderEmail')
        sender_password = os.getenv('APP_PASSWORD')
        custom_subject = data.get('customSubject')
        dry_run = data.get('dryRun', False)
        
        if not sender_email:
            return jsonify({'error': 'Sender email is required'}), 400
        
        body_template = None
        if os.path.exists('email_body.txt'):
            with open('email_body.txt', 'r', encoding='utf-8') as f:
                body_template = f.read().strip()
        
        success = send_emails(
            sender_email=sender_email,
            sender_password=sender_password,
            custom_subject=custom_subject,
            body_template=body_template,
            dry_run=dry_run
        )
        
        if success:
            return jsonify({'message': 'Emails sent successfully'}), 200
        else:
            return jsonify({'error': 'Email sending failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download-certificates', methods=['GET'])
def download_certificates():
    try:
        if os.path.exists('certificates.zip'):
            return send_file('certificates.zip', as_attachment=True)
        else:
            return jsonify({'error': 'Certificate file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'Server running', 'env': os.getenv('FLASK_ENV', 'development')}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') != 'production')
