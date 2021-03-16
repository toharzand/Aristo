import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart



class EmailSender:
    def __init__(self, reciver):
        self.sender_email = "AristoTenders@gmail.com"
        self.password = "TIa123456"
        self.receiver_email = reciver

        self.message = MIMEMultipart("alternative")
        self.message["Subject"] = "Deadline is arriving"
        self.message["From"] = self.sender_email
        self.message["To"] = self.receiver_email

    def send_email(self, text):
        start = """
            <html>
              <body>
                <p>
            """
        end = """
                </p>
              </body>
            </html>
            """
        html = start + text.replace("\n", "<br>") + end
        # Turn these into plain/html MIMEText objects
        part_1 = MIMEText(text, "plain")
        # Add HTML/plain-text parts to MIMEMultipart message
        # The email client will try to render the last part first
        self.message.attach(part_1)

        if html:
            part_2 = MIMEText(html, "html")
        self.message.attach(part_2)

        # Create secure connection with server and send email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(self.sender_email, self.password)
            server.sendmail(
                self.sender_email, self.receiver_email, self.message.as_string()
            )


if __name__ == '__main__':
    # Create the plain-text and HTML version of your message
    text = """\
    שלום איתי,
           שים לב!
           מערכת אריסטו זיהתה כי המשימה "לבנות מערכת שלמה לניהול משימות" 
           שהוטלה עליך צריכה להתבצע עד התאריך 19.3.2021
           אנא ממך, הפסק ללמוד והחל להשקיע בדברים החשובים באמת
           בתודה
           Mr Asaf Stern, Aristo CTO
           """
    em = EmailSender("itay2803@gmail.com")
    em.send_email(text)
