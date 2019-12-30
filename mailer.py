from __future__ import print_function

import smtplib, getpass
import sr, os
from config import config

def def_psource():
    return getpass.getpass("SMTP Server password:")

psource = def_psource

def set_psource( fn ):
    global psource
    psource = fn

the_pass = None
def get_pass():
    global the_pass
    if the_pass == None:
        the_pass = psource()
    return the_pass

def email( fromaddr, toaddr, subject, msg, smtp_pass = None ):
    if smtp_pass == None and config.has_option('mailer', 'password'):
        smtp_pass = config.get('mailer', 'password')

    if smtp_pass == None:
        smtp_pass = get_pass()

    msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n%s" % (fromaddr, toaddr, subject, msg)

    server = smtplib.SMTP(config.get('mailer', 'smtpserver'), timeout = 5)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(config.get('mailer', 'username'), smtp_pass)

    print("Emailing...", end=' ')
    r = server.sendmail(fromaddr, toaddr, msg)
    if len(r):
        print(" FAILED.")
    else:
        print(" OK.")

    try:
        server.quit()
    except smtplib.sslerror:
        pass

def send_template( template_name, user, extravars = [] ):
    "Send the template with the given name to the given user"
    lang = user.get_lang()

    script_dir = os.path.dirname( __file__ )
    temp_path = os.path.join( script_dir, "msg", lang, template_name )

    msg = open( temp_path, "r" ).read()

    subject = msg.splitlines()[0]
    assert subject[:8] == "Subject:"
    subject = subject[8:].strip()

    msg = "\n".join(msg.splitlines()[1:])

    v = { "NAME": user.cname,
          "USERNAME": user.username,
          "EMAIL": user.email }
    v.update(extravars)

    for vname, val in v.items():
        msg = msg.replace( "$%s" % vname, val )

    email( config.get('mailer', 'fromaddr'), user.email, subject, msg, None )
