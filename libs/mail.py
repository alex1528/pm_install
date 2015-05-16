# -*- coding: utf-8 -*-

import email
import smtplib
import mimetypes
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
from email.header import Header


SMTP_HOST = 'mx.hy01.nosa.me'
SMTP_PORT = 25

CONT_MAIL_LIST = [
    'tawateer@gmail.com'
]


def sanitize_subject(subject):
    try:
        subject.decode('ascii')
    except UnicodeEncodeError:
        pass
    except UnicodeDecodeError:
        subject = Header(subject, 'utf-8')
    return subject

# Assuming send_mail() is intended for scripting usage, only Subject is sanitzed here.
# Also, the sanitzation procedure for other Headers is far too complicated.


def mail(mailto, subject, content):
    mail_from = 'noreply@nosa.me'
    mail_cc = None
    mail_body_type = 'html'

    msg = MIMEMultipart('alternative')
    msg['Subject'] = sanitize_subject(subject)
    msg['From'] = mail_from
    # assert(isinstance(mailto, list))

    if isinstance(mailto, list):
        mailto.extend(CONT_MAIL_LIST)
        msg['To'] = ', '.join(mailto)
    elif isinstance(mailto, str) or isinstance(mailto, unicode):
        msg['To'] = ", ".join(CONT_MAIL_LIST) + ", " + mailto
    else:
        mailto = CONT_MAIL_LIST
        msg['To'] = ", ".join(CONT_MAIL_LIST)

    if mail_cc:
        assert(isinstance(mail_cc, list))
        msg['Cc'] = ', '.join(mail_cc)
    body = MIMEText(content, mail_body_type, 'utf-8')
    msg.attach(body)
    smtp = smtplib.SMTP()
    smtp.connect(SMTP_HOST, SMTP_PORT)
    smtp.sendmail(mail_from, mailto, msg.as_string())


if __name__ == '__main__':
    mail(None, "物理机创建完毕", "1. 美丽的宝贝,这只是一个测试而已,你感动了么？")
    mail(["tawateer@gmail.com"], "物理机创建完毕", "2. 美丽的宝贝,这只是一个测试而已,你感动了么？")