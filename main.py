"""
main.py

Usage example:
uv run main.py --x 1000 --y 707
"""

import argparse
import sys
from generator import generate_certificates
from email_sender import send_emails


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


if __name__ == "__main__":
    main()
