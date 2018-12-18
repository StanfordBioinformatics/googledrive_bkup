# -*- coding: utf-8 -*-                                                                                 
                                                                                                        
###                                                                                                     
# © 2018 The Board of Trustees of the Leland Stanford Junior University                                 
# Nathaniel Watson                                                                                      
# nathankw@stanford.edu                                                                                 
### 

"""
The user must first go into the Google Cloud Console (GCC) and enable the Google Drive API in order
to allows clients to access resources from Google Drive. 

Next, create an OAuth2 token as follows:

In GCC, select the Navigation menu and then 
  APIs & Services -> Credentials
Click on the button that says "Create Credentials", and select "OAuth client ID". You will then be
prompted to select the type of client that this token is for. Select "other" since our client is a 
native application. Also give a name for your client. Your token will be created, and then 
you'll need to download your credentials file.
It will have a long name; just rename it to something like credentials_$project_$clientname.json, 
where $project is your GCC project name, and $clientname is the name you gave to your client when you
selected the type of client above. 
"""

