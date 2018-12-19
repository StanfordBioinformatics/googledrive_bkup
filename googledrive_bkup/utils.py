# -*- coding: utf-8 -*-                                                                                 
                                                                                                        
###                                                                                                     
# © 2018 The Board of Trustees of the Leland Stanford Junior University                                 
# Nathaniel Watson                                                                                      
# nathankw@stanford.edu                                                                                 
### 

"""
Enabling the Drive API
======================

To start, go to https://developers.google.com/drive/api/v3/quickstart/python. In Step 1 listed on
that page, click on the blue button named "ENABLE THE DRIVE API". This will open up a dialog box 
prompting you to select or create a Google Project for which to enable the Drive API. Enabling an
API in GCP amounts to registering a client to use that API in the given Google Project. Click on the
"Next" button after selecting a project in order to continue with the client registraion, which will
assign a Client ID and a Client Secret and downloads them into a file by the name of credentials.json.
You can also see your credentials in GCC by going to "APIs and Services" and clicking on "Credentials".

Obtaining client OAuth2 credentials
===================================
Now that your client is registered with your Google Project, each user of the client will need to 
obtain OAuth2 credentials ,which include an access token, in able to user the client. 
In GCC, select the Navigation menu and then 
select APIs & Services -> Credentials. Click on the button that says "Create Credentials", and 
select "OAuth client ID". You will then be
prompted to select the type of client that this token is for. Select "other" since our client is a 
native application. Also give a name for your client. Your token will be created, and then 
you'll need to download your credentials file.
It will have a long name; just rename it to something like credentials_$project_$clientname.json, 
where $project is your GCC project name, and $clientname is the name you gave to your client when you
selected the type of client above. 
"""

