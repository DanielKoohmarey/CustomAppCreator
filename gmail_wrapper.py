import httplib2
import os
import argparse
import base64
import email

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from apiclient import discovery, errors
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

class GmailWrapper(object):

    SCOPES = 'https://www.googleapis.com/auth/gmail.modify'
    CLIENT_SECRET_FILE = 'client_secret.json' # https://console.developers.google.com/apis/credentials
    APPLICATION_NAME = "Pericror Custom App Creator"
    SENDER = 'pericror@gmail.com'
    RECIPIENT = 'info@pericror.com'

    def __init__(self):
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        self.service = discovery.build('gmail', 'v1', http=http)

    def get_credentials(self):
        """Gets valid user credentials from storage.
    
        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.
    
        Returns:
            Credentials, the obtained credential.
        """
        flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()        
        
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                       'gmail-python-wrapper.json')
    
        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self.CLIENT_SECRET_FILE, self.SCOPES)
            flow.user_agent = self.APPLICATION_NAME
            credentials = tools.run_flow(flow, store,flags)
            print 'Storing credentials to ' + credential_path
            
        return credentials

    def get_unread_message_id(self):
        msg_id = None    
        
        try:
            query = "from:danielkoohmarey@gmail.com is:unread"
            response = self.service.users().messages().list(userId='me', maxResults=1,
                                                       q=query).execute()
            if 'messages' in response:
                msg_id = response['messages'][0]['id']

        except errors.HttpError, error:
            print 'An error occurred: %s' % error
            
        return msg_id

    def get_message_data(self, msg_id):
        to_return = {}
        
        try:
            message = self.service.users().messages().get(userId='me', id=msg_id,
                                                     format='raw').execute()
            msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
            mime_msg = email.message_from_string(msg_str)

            body = ""
            if mime_msg.is_multipart():
                for payload in mime_msg.get_payload():
                    if payload.get_content_type() == 'text/plain':
                        body = payload.get_payload()
            elif payload.get_content_type() == 'text/plain':
                body = mime_msg.get_payload()
            
            to_return = { 'date' : mime_msg['Date'], 'body' : body }
            
        except errors.HttpError, error:
            print 'An error occurred: %s' % error
            
        return to_return

    def mark_as_read(self, msg_id):
        success = False
        
        try:
            msg_labels = { "removeLabelIds": ["UNREAD"] }
            message = self.service.users().messages().modify(userId='me', id=msg_id,
                                                        body=msg_labels).execute()
            success = message
            
        except errors.HttpError, error:
            print 'An error occurred: %s' % error 
            
        return success

    def create_message(self, subject, plain, html):
        """Create a message for an email.
        
        Args:
            subject: The subject of the email message.
            plain: The text of the email message.
            html: The html of the email message.
        
        Returns:
            An object containing a base64url encoded email object.
        """
        message = MIMEMultipart('alternative')
        
        plain_part = MIMEText(plain, 'plain')
        html_part = MIMEText(html, 'html')
        message.attach(plain_part)
        message.attach(html_part)
        
        message['To'] = self.RECIPIENT
        message['From'] = self.SENDER
        message['Subject'] = subject
        
        return {'raw': base64.urlsafe_b64encode(message.as_string())}        
        
    def send_message(self, message):
        """Send an email message.
        
        Args:
            message: Message to be sent.
        
        Returns:
            Sent message.
        """
        success = None
          
        try:
            message = (self.service.users().messages().send(userId='me',
                           body=message).execute())
            success = message
        
        except errors.HttpError, error:
            print 'An error occurred: %s' % error 
        
        return success