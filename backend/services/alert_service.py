"""
AegisFlow - Alert Service
Handles sending automated email alerts for newly discovered vulnerabilities.
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def send_vulnerability_alert(to_email: str, repo_name: str, vulnerabilities_found: int, risk_level: str, scan_link: str):
    """Send an email alert using SMTP when new vulnerabilities are discovered."""
    sender_email = os.getenv("SMTP_EMAIL", "aegisflow.alerts@gmail.com")
    sender_password = os.getenv("SMTP_PASSWORD", "mock_password")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    
    # If it's a mock setup or we don't have real credentials, just log it.
    if sender_password == "mock_password":
        print(f"[ALERT SERVICE] Mock email sent to {to_email}")
        print(f"Subject: AegisFlow Alert: {vulnerabilities_found} vulnerabilities found in {repo_name}")
        print(f"Risk Level: {risk_level}. Link: {scan_link}")
        return True

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"AegisFlow Alert: {vulnerabilities_found} vulnerabilities found in {repo_name}"
    msg["From"] = sender_email
    msg["To"] = to_email

    text = f"""
    AegisFlow Security Alert
    
    Repository: {repo_name}
    Vulnerabilities Found: {vulnerabilities_found}
    Overall Risk Level: {risk_level}
    Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
    
    View Full Scan Details: {scan_link}
    """

    html = f"""
    <html>
      <body>
        <h2>🛡️ AegisFlow Security Alert</h2>
        <p>We detected new vulnerabilities during a scheduled scan.</p>
        <ul>
            <li><b>Repository:</b> {repo_name}</li>
            <li><b>Vulnerabilities Found:</b> {vulnerabilities_found}</li>
            <li><b>Risk Level:</b> <span style="color:red;">{risk_level}</span></li>
            <li><b>Date:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</li>
        </ul>
        <p><a href="{scan_link}">Click here to view full scan details</a></p>
      </body>
    </html>
    """

    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    msg.attach(part1)
    msg.attach(part2)

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        print(f"[ALERT SERVICE] Email successfully sent to {to_email}")
        return True
    except Exception as e:
        print(f"[ALERT SERVICE ERROR] Failed to send email: {e}")
        return False
