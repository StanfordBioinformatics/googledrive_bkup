import io
import os
import pdb
from googleapiclient.discovery import build
import googleapiclient.http
from httplib2 import Http
import oauth2client
import oauth2client.tools
import oauth2client.file

#
## See list of scopes at https://developers.google.com/drive/api/v3/about-auth.
#SCOPES = "https://www.googleapis.com/auth/drive.file" # For creating and opening files.
SCOPES = "https://www.googleapis.com/auth/drive" # For creating and opening files.

## Headers needed for resumable upload session
#Authorization: Bearer [YOUR_AUTH_TOKEN]
#Content-Length: 38
#Content-Type: application/json; charset=UTF-8
#X-Upload-Content-Type: image/jpeg
#X-Upload-Content-Length: 2000000

class Drive():
    def __init__(self, client_token_file="", client_registration_file=""):
        """
        Args:
            client_registration_file: `str`. The name of the JSON file that contains the client
                client regitration information that was obtained at the time of enabling the
                Google Drive API in your Google Project. 
            client_token_file: `str`. The name of the file that contains the OAuth2 bearer token.
                If not provided here, then it will be looked up in the environment under the variable
                name GOOGLE_DRIVE_CLIENT_TOKEN.  If this file doesn't exist yet, then a new bearer
                token will be requested and it will be stored in a file by this name. 
        """
        if not client_registration_file:
            self.client_registration_file = os.environ.get("GOOGLE_DRIVE_CLIENT_REGISTRATION", "")
        else:
            self.client_registration_file = client_registration_file

        if not client_token_file:
            try:
                client_token_file = os.environ["GOOGLE_DRIVE_CLIENT_TOKEN"]
            except KeyError:
                msg = ("The name of an existing JSON file containing an OAuth2 bearor must be provided. "
                       "If such a file does not yet exist, then a new one will be created with the "
                       "given name.")
                raise Exception(msg)
        self.client_token_file = client_token_file
        self.service = self._build_service()

    def _build_service(self):
        store = oauth2client.file.Storage(self.client_token_file)
        creds = store.get() # Will be None if self.client_token_file doesn't exist.
        if not creds or creds.invalid:
            creds = self.request_bearer_token()
        return build('drive', 'v3', http=creds.authorize(Http()))

    def request_bearer_token(self):
        """
        Locates the Google Drive client file (the one that was downloaded from Google Cloud Console
        after registering your client) by looking at the value of the environment variable
        GOOGLE_DRIVE_CLIENT_REGISTRATION.
    
        Returns: `oauth2client.client.OAuth2Credentials` instance. 
        """
        if not self.client_registration_file:
            msg = ("Path to the client registration JSON file is not known. This can be set "
                   "either via the GOOGLE_DRIVE_CLIENT_REGISTRATION environment variable, or the "
                   "initialization parameter client_registration_file.")
            raise Exception(msg)

        store = oauth2client.file.Storage(self.client_token_file)
        flow = oauth2client.client.flow_from_clientsecrets(self.client_registration_file, SCOPES)
        # Opens a browser page for you to authorize the client, then downloads the bearer token. 
        creds = oauth2client.tools.run_flow(flow, store)
        return creds

    def process_mime_type(self, mime_type):
        """
        Converts the mime types for Google Documents and Google Presentations. For some reason, 
        when reading the file metadata for such a file, it's specified mime type is different than
        the conversion type listed at https://developers.google.com/drive/api/v3/manage-downloads;
        furthermore, it's not any valid conversion type. 
        In order for the download to work, the mime type must be a valid conversion type.
        """
        if mime_type == "application/vnd.google-apps.presentation":
            return "application/vnd.oasis.opendocument.presentation"
        elif mime_type == "application/vnd.google-apps.document":
            return "application/vnd.oasis.opendocument.text"
        return mime_type

    def download(self, file_id):
        # meta is a dict that looks like
        # {'kind': 'drive#file', 'id': '0BxBVcx6RbBMLbTFwbDBVdllZSUR1SDNVRklaQ1BSajlsNGxR', 'name': 'image1.JPG', 'mimeType': 'image/jpeg'}
        # {'kind': 'drive#file', 'id': '1uaWo0Jsahb03hhuj70GLNm-IG_euvX6qIsIMY1EQ5Ug', 'name': 'Groceries', 'mimeType': 'application/vnd.google-apps.document'}
        meta = self.service.files().get(fileId=file_id).execute()
        name = meta["name"]
        mime_type = meta["mimeType"]
        mime_type = self.process_mime_type(mime_type)
        #pdb.set_trace()
        if "oasis" in mime_type:
            request = self.service.files().export_media(fileId=file_id, mimeType=mime_type)
        else:
            request = self.service.files().get_media(fileId=file_id)
        #fh = io.BytesIO()
        fh = open(name, "wb")
        downloader = googleapiclient.http.MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print("Download %d%%." % int(status.progress() * 100))
        fh.close()

    def download_google_doc(self, file_id, mime_type):
        request = self.service.files().export_media(fileId=file_id, mimeType=mime_type)
        self._download_request(request)
    
if __name__ == '__main__':
    d = Drive()
    #d.download_google_doc(file_id="0BxBVcx6RbBMLbTFwbDBVdllZSUR1SDNVRklaQ1BSajlsNGxR", mime_type="image/jpeg")
    #d.download(file_id="0BxBVcx6RbBMLbTFwbDBVdllZSUR1SDNVRklaQ1BSajlsNGxR")
    #d.download(file_id="1HzyB_UCfO3kpp9EGNVKuyAqVQZVzNMQSIvmqxMkSwtk") # ppt
    #d.download(file_id="1EqvG_-h8XCRe0k5-RrV1dq-2-hfRF_9uT61E7nOTtco") # Google doc
    d.download(file_id="0BxBVcx6RbBMLX09LZVpJTHhJMTFQbFk3QUdFb3JDNF9wck9j")
    #d.download(file_id="1M9GWZutVNdwtBmAR9gULzhizJOoYoy3l7j5Cz3WGxDs")

