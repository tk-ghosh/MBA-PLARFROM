from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/drive']


def main():
    flow = InstalledAppFlow.from_client_secrets_file('oauth_client_secret.json', SCOPES)
    creds = flow.run_local_server(port=0)
    with open('token.json', 'w') as f:
        f.write(creds.to_json())
    print('Success! token.json created — Drive access is now authorized.')


if __name__ == '__main__':
    main()


