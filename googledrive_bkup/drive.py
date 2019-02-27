import io
import logging
import mimetypes
import os
import pdb
from googleapiclient.discovery import build
import googleapiclient.http
from httplib2 import Http
import oauth2client
import oauth2client.tools
import oauth2client.file

import googledrive_bkup as b

debug_logger = logging.getLogger(b.DEBUG_LOGGER_NAME)
error_logger = logging.getLogger(b.ERROR_LOGGER_NAME)

#: Upload logger name
UPLOAD_LOGGER_NAME = __package__ + "_upload"
#: A ``logging`` instance that accepts messages at the INFO level and appends them to a file.
#: Each message is written with two tab-delimted fields: 1) The uploaded file name that the
#: user provided, and 2) It's file ID on Google Drive.
upload_logger = logging.getLogger(UPLOAD_LOGGER_NAME)
upload_logger.setLevel(logging.INFO)
file_name = os.path.join(b.LOG_DIR, "log_" + UPLOAD_LOGGER_NAME + ".txt")
file_handler = logging.FileHandler(filename=file_name, mode="a")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(b.f_formatter)
upload_logger.addHandler(file_handler)

#
## See list of scopes at https://developers.google.com/drive/api/v3/about-auth.
SCOPES = "https://www.googleapis.com/auth/drive.file" # For creating and opening files.

class MissingClientRegistration(Exception):
    """
    Raised when the GCC-provided client registration JSON file can't be located.
    """
    pass

class Drive():

    def __init__(self, client_token_file="", client_registration_file=""):
        """
        Args:
            client_registration_file: `str`. The name of the JSON file that contains the client
                registration information that was obtained at the time of enabling the
                Google Drive API in your Google Project.
            client_token_file: `str`. The name of the file that contains the OAuth2 bearer token.
                If not provided here, then it will be looked up in the environment under the variable
                name GOOGLE_DRIVE_CLIENT_TOKEN.  If this file doesn't exist yet, then a new bearer
                token will be requested and it will be stored in a file by this name.

        Raises:
            `MissingClientRegistration`: Both the client_registration_file parameter and the
                GOOGLE_DRIVE_CLIENT_REGISTRATION environment variable is not set when one of them
                should be.
        """
        if not client_registration_file:
            try:
                client_registration_file = os.environ.get("GOOGLE_DRIVE_CLIENT_REGISTRATION", "")
            except KeyError:
                msg = ("Must provide the path to the JSON file that Google Cloud Console provided "
                      "when registering this client; you can do so by either setting the "
                      "client_registration_file parameter or the GOOGLE_DRIVE_CLIENT_REGISTRATION "
                      "environment variable. Follow the instructions at "
                      "https://developers.google.com/drive/api/v3/quickstart/python for assistance.")
                raise Exception(msg)
        self.client_registration_file = client_registration_file

        if not client_token_file:
            try:
                client_token_file = os.environ["GOOGLE_DRIVE_CLIENT_TOKEN"]
            except KeyError:
                msg = ("The name of an existing JSON file containing an OAuth2 bearor must be provided "
                       "either by setting the client_registration_file parameter, or by setting the "
                       "environment variable named GOOGLE_DRIVE_CLIENT_TOKEN. If such a file does "
                       "not yet exist, then a new one will be created with the given name.")
                raise Exception(msg)
        self.client_token_file = client_token_file
        self.service = self._build_service()

    def _build_service(self):
        store = oauth2client.file.Storage(self.client_token_file)
        creds = store.get() # Will be None if self.client_token_file doesn't exist or is expired.
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
        store = oauth2client.file.Storage(self.client_token_file)
        flow = oauth2client.client.flow_from_clientsecrets(self.client_registration_file, SCOPES)
        # Opens a browser page for you to authorize the client, then downloads the bearer token.
        creds = oauth2client.tools.run_flow(flow, store)
        return creds

    def translate_google_mime_type(self, mime_type):
        """
        Translates the Google-specific mime type of a Google Document (Google Document/Spreadsheet/Presentation, etc.)
        to a cross-compatible, standard mime type from Open Office that would be used to, for
        example, download the file. If the provided mime type isn't a recognized Google Document
        mime type, then returns the input. See list of mime types here_.

        Args:
            mime_type: `str`.

        Returns:
            `str`.

        .. _here: https://developers.google.com/drive/api/v3/manage-downloads
        """
        if mime_type == "application/vnd.google-apps.presentation":
            # Google Presentation -> Open Office presentation
            return "application/vnd.oasis.opendocument.presentation"
        elif mime_type == "application/vnd.google-apps.document":
            # Google Document -> Open Office document
            return "application/vnd.oasis.opendocument.text"
        elif mime_type == "application/vnd.google-apps.spreadsheet":
            # Google Sheet -> Open Office sheet
            return "application/x-vnd.oasis.opendocument.spreadsheet"
        return mime_type

    def get_file_meta(self, file_id):
        return self.service.files().get(fileId=file_id).execute()

    def download(self, file_id):
        """
        Downloads the file with the given file identifier from the user's Google Drive account.

        Args:
            file_id: `str`.
        """
        # meta is a dict that looks like
        # {'kind': 'drive#file', 'id': '0BxBVcx6RbBMLbTFwbDBVdllZSUR1SDNVRklaQ1BSajlsNGxR', 'name': 'image1.JPG', 'mimeType': 'image/jpeg'}
        # {'kind': 'drive#file', 'id': '1uaWo0Jsahb03hhuj70GLNm-IG_euvX6qIsIMY1EQ5Ug', 'name': 'Groceries', 'mimeType': 'application/vnd.google-apps.document'}
        meta = self.service.files().get(fileId=file_id, supportsTeamDrives=True).execute()
        name = meta["name"]
        mime_type = meta["mimeType"]
        mime_type = self.translate_google_mime_type(mime_type)
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

    def upload(self, folder_id, infile, meta_fields={}):
        filename = os.path.basename(infile)
        mimetype = mimetypes.guess_type(infile)[0]
        meta = {
            "description": "howdy",
            "name": filename,
            "parents": [folder_id]
        }
        media = googleapiclient.http.MediaIoBaseUpload(open(infile, "rb"), mimetype=mimetype, resumable=True)
        debug_logger.debug("Uploading '{}'.".format(filename))
        file_id = self.service.files().create(body=meta, media_body=media, fields='id').execute()
        msg = infile + "\t" + file_id + "\n"
        debug_Logger.debug(msg)
        upload_logger.info(msg)
        return file_id

    def mkdir(self, name):
        meta = {
            "name": name.strip(),
            "mimeType": "application/vnd.google-apps.folder"
        }
        file_id = self.service.files().create(body=meta, fields="id").execute()
        return file_id

    def teamdrives(self):
        """
        Returns:
            `dict` of the form {"teamdrive_id": "teamdrive_name"}.
        """
        res = self.service.teamdrives().list().execute()["teamDrives"]
        #i.e. [{'kind': 'drive#teamDrive', 'id': '0AF69aIFJ45gyUk9PVA', 'name': 'ENCODE4 - ATAC-seq Production'}, {'kind': 'drive#teamDrive', 'id': '0AInssFUaRejcUk9PVA', 'name': 'Pulsar'}]
        tds = {}
        for i in res:
            tds[i["id"]] = i["name"] 
        return tds

    def list_teamdrive_files(self, teamdrive_id, key_by):
        """
        Generates a dict. of all the files in the specified team drive. 

        Args:
            key_by: `str` being one of "id" or name". 
            
        Returns:
            `dict` where keys are file identifiers or file names, depending on the choice of the
                key_by parameter. If key_by="id", then the resulting dict is of the form:

                {'1NN4RcQIFFPiL3qUzo7VH1I0ubPsZszoT': {
                    'name': '40_A549_ZNF285_rep1_6sec.jpg', 
                    'mimeType': 'image/jpeg', 
                    'teamDriveId': '0AInssFUaRejcUk9PVA'
                    }
                }

               But if key_by="name", then the resulting dict is of the form:

                {'40_A549_ZNF285_rep1_6sec.jpg': {
                    'id': '1NN4RcQIFFPiL3qUzo7VH1I0ubPsZszoT',
                    'mimeType': 'image/jpeg', 
                    'teamDriveId': '0AInssFUaRejcUk9PVA'
                    }
                }
        """

        key_by = key_by.lower()
        if key_by not in ["id", "name"]:
            raise Exception("The key_by parameter must be set to either 'id' or 'name'.")

        def get_page(next_page_token=""):
            """
            Gets a single page of file list results from the specified Google Team Drive.
  
            Args:
                next_page_token: `str`. The default empty string means to fetch the first page of
                    results. Using the Google Drive API, fetching a page of results will default 
                    100 items max per page. The next page of results can be fetched with a token
                    named nextPageToken in the API result of the list operation. 
  
            Returns:
                `list` of dicts, where each dict is of the form:
  
                 {'kind': 'drive#file', 
                  'id': '1NN4RcQIFFPiL3qUzo7VH1I0ubPsZszoT', 
                  'name': '40_A549_ZNF285_rep1_6sec.jpg',
                  'mimeType': 'image/jpeg', 
                  'teamDriveId': '0AInssFUaRejcUk9PVA'
                 }
            """
            # By default, page size is 100 in Google's API. 
            page_res = self.service.files().list(pageToken=next_page_token, corpora="teamDrive", teamDriveId=teamdrive_id, includeTeamDriveItems=True, supportsTeamDrives=True).execute()
            try:
                next_page_token = page_res["nextPageToken"]
            except KeyError:
                next_page_token = False        
            return next_page_token, page_res["files"]

        next_page_token, all_files = get_page()
        while next_page_token:
          next_page_token, page_files = get_page(next_page_token)
          # res is a dict. with keys ['kind', 'nextPageToken', 'incompleteSearch', 'files']. 
          all_files.extend(page_files)

        file_dict = {}
        if key_by == "id":
            for i in all_files:
                key = i.pop("id")
                file_dict[key] = i
        else:
            for i in all_files:
                key = i.pop("name")
                file_dict[key] = i
        return file_dict
        

if __name__ == '__main__':
    d = Drive()
    #d.download_google_doc(file_id="0BxBVcx6RbBMLbTFwbDBVdllZSUR1SDNVRklaQ1BSajlsNGxR", mime_type="image/jpeg")
    #d.download(file_id="0BxBVcx6RbBMLbTFwbDBVdllZSUR1SDNVRklaQ1BSajlsNGxR")
    #d.download(file_id="1HzyB_UCfO3kpp9EGNVKuyAqVQZVzNMQSIvmqxMkSwtk") # ppt
    #d.download(file_id="1EqvG_-h8XCRe0k5-RrV1dq-2-hfRF_9uT61E7nOTtco") # Google doc
    #d.download(file_id="0BxBVcx6RbBMLX09LZVpJTHhJMTFQbFk3QUdFb3JDNF9wck9j")
    #d.download(file_id="1M9GWZutVNdwtBmAR9gULzhizJOoYoy3l7j5Cz3WGxDs")

