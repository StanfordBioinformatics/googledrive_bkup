import io
import os
from googleapiclient.discovery import build
import googleapiclient.http
from httplib2 import Http
import oauth2client
import oauth2client.tools
import oauth2client.file

#
## See list of scopes at https://developers.google.com/drive/api/v3/about-auth.
SCOPES = "https://www.googleapis.com/auth/drive.file"

## Headers needed for resumable upload session
#Authorization: Bearer [YOUR_AUTH_TOKEN]
#Content-Length: 38
#Content-Type: application/json; charset=UTF-8
#X-Upload-Content-Type: image/jpeg
#X-Upload-Content-Length: 2000000

def request_bearer_token():
    """
    Locates the Google Drive client file (the one that was downloaded from Google Cloud Console
    after creating registering client) by looking at the value of the environmet variable
    GOOGLE_DRIVE_CLIENT.
    """
    store = oauth2client.file.Storage('token.json')
    credentials_file = os.environ["GOOGLE_DRIVE_CLIENT"]
    flow = oauth2client.client.flow_from_clientsecrets(credentials_file, SCOPES)
    # Opens a browser page for you to authorize the client, then downloads the bearer token. 
    creds = oauth2client.tools.run_flow(flow, store)

def main():
    store = oauth2client.file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = oauth2client.client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = oauth2client.tools.run_flow(flow, store)
    service = build('drive', 'v3', http=creds.authorize(Http()))
    file_id = "0BxBVcx6RbBMLcmR1cERya2hJM0ZBVHJDLXZGcFdqc25nS2Nr"
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = googleapiclient.http.MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print("Download %d%%." % int(status.progress() * 100))

#if __name__ == '__main__':
#    main()
