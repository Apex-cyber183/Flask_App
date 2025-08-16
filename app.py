import io
import os
import json
from flask import Flask, jsonify, send_file, abort, request
from flask_cors import CORS
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload

# -------- CONFIG ----------
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 5000))
API_KEY = os.environ.get("API_KEY")  # set in Railway
DRIVE_FOLDER_ID = os.environ.get("GDRIVE_FOLDER_ID")  # set in Railway
# --------------------------

if not DRIVE_FOLDER_ID:
    raise Exception("GDRIVE_FOLDER_ID not found in environment variables!")

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

app = Flask(__name__)
CORS(app)

# Load Google Service Account credentials from environment variable
service_account_info = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
if not service_account_info:
    raise Exception("GOOGLE_SERVICE_ACCOUNT_JSON not found in environment variables!")

creds_dict = json.loads(service_account_info)
creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)

drive_service = build('drive', 'v3', credentials=creds, cache_discovery=False)

def list_files_in_folder(folder_id):
    files = []
    page_token = None
    q = f"'{folder_id}' in parents and trashed = false"
    while True:
        response = drive_service.files().list(
            q=q,
            spaces='drive',
            fields='nextPageToken, files(id, name, mimeType, modifiedTime, size, md5Checksum)',
            pageToken=page_token
        ).execute()
        files.extend(response.get('files', []))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break
    return files

def require_api_key():
    key = request.headers.get("x-api-key")
    if not API_KEY or key != API_KEY:
        abort(401, description="Unauthorized: invalid API key")

@app.route('/manifest', methods=['GET'])
def manifest():
    """ Returns JSON manifest of files in the folder """
    require_api_key()
    try:
        files = list_files_in_folder(DRIVE_FOLDER_ID)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    version = max((f.get('modifiedTime') or '') for f in files) if files else ""

    manifest_files = []
    for f in files:
        manifest_files.append({
            "name": f.get("name"),
            "id": f.get("id"),
            "modifiedTime": f.get("modifiedTime"),
            "md5": f.get("md5Checksum"),
            "download_url": f"/download/{f.get('id')}"
        })

    return jsonify({
        "version": version,
        "files": manifest_files
    })

@app.route('/download/<file_id>', methods=['GET'])
def download(file_id):
    """ Streams a Drive file to the client """
    require_api_key()
    try:
        metadata = drive_service.files().get(fileId=file_id, fields='name, mimeType').execute()
        file_name = metadata.get('name', file_id)
        mime = metadata.get('mimeType', 'application/octet-stream')

        request_media = drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request_media)
        done = False
        while not done:
            status, done = downloader.next_chunk()

        fh.seek(0)
        return send_file(
            fh, mimetype=mime, as_attachment=True, download_name=file_name
        )
    except Exception as e:
        return abort(404, description=str(e))

@app.route('/')
def home():
    return jsonify({
        "status": "Backend is running",
        "endpoints": {
            "manifest": "/manifest",
            "download": "/download/<file_id>"
        },
        "note": "All endpoints require x-api-key header"
    })

if __name__ == '__main__':
    print(f"Backend on http://{HOST}:{PORT} | Folder: {DRIVE_FOLDER_ID}")
    app.run(host=HOST, port=PORT)






















# # import io
# # import os
# # from flask import Flask, jsonify, send_file, abort
# # from flask_cors import CORS
# # from googleapiclient.discovery import build
# # from google.oauth2 import service_account
# # from googleapiclient.http import MediaIoBaseDownload
# #
# # # -------- CONFIG ----------
# # SERVICE_ACCOUNT_FILE = r"C:\Users\Admin\Desktop\drive_backend\certain-tangent-465609-p5-ce8ccab7ef90.json"   # your downloaded key (rename to this)
# # DRIVE_FOLDER_ID = "1CyDBGm6BvIY5SErybLue9jC1r-WL18EB"  # from the Drive folder URL
# # HOST = "0.0.0.0"
# # PORT = 5000
# # # --------------------------
# #
# # SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
# #
# # app = Flask(__name__)
# # CORS(app)
# #
# # creds = service_account.Credentials.from_service_account_file(
# #     SERVICE_ACCOUNT_FILE, scopes=SCOPES)
# # drive_service = build('drive', 'v3', credentials=creds, cache_discovery=False)
# #
# # def list_files_in_folder(folder_id):
# #     files = []
# #     page_token = None
# #     q = f"'{folder_id}' in parents and trashed = false"
# #     while True:
# #         response = drive_service.files().list(
# #             q=q,
# #             spaces='drive',
# #             fields='nextPageToken, files(id, name, mimeType, modifiedTime, size, md5Checksum)',
# #             pageToken=page_token
# #         ).execute()
# #         files.extend(response.get('files', []))
# #         page_token = response.get('nextPageToken', None)
# #         if page_token is None:
# #             break
# #     return files
# #
# # @app.route('/manifest', methods=['GET'])
# # def manifest():
# #     """
# #     Returns JSON manifest of files in the shared Drive folder:
# #     {
# #       "version": "<latest modifiedTime>",
# #       "files": [
# #         { "name": "...", "id": "...", "download_url": "/download/<id>", "modifiedTime": "...", "md5": "..." }
# #       ]
# #     }
# #     """
# #     try:
# #         files = list_files_in_folder(DRIVE_FOLDER_ID)
# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 500
# #
# #     version = max((f.get('modifiedTime') or '') for f in files) if files else ""
# #
# #     manifest_files = []
# #     for f in files:
# #         manifest_files.append({
# #             "name": f.get("name"),
# #             "id": f.get("id"),
# #             "modifiedTime": f.get("modifiedTime"),
# #             "md5": f.get("md5Checksum"),
# #             "download_url": f"/download/{f.get('id')}"
# #         })
# #
# #     return jsonify({
# #         "version": version,
# #         "files": manifest_files
# #     })
# #
# # @app.route('/download/<file_id>', methods=['GET'])
# # def download(file_id):
# #     """ Streams a Drive file to the client. """
# #     try:
# #         metadata = drive_service.files().get(fileId=file_id, fields='name, mimeType').execute()
# #         file_name = metadata.get('name', file_id)
# #         mime = metadata.get('mimeType', 'application/octet-stream')
# #
# #         request = drive_service.files().get_media(fileId=file_id)
# #         fh = io.BytesIO()
# #         downloader = MediaIoBaseDownload(fh, request)
# #         done = False
# #         while not done:
# #             status, done = downloader.next_chunk()
# #
# #         fh.seek(0)
# #         return send_file(
# #             fh, mimetype=mime, as_attachment=True, download_name=file_name
# #         )
# #     except Exception as e:
# #         return abort(404, description=str(e))
# #
# # @app.route('/')
# # def home():
# #     return jsonify({
# #         "status": "Backend is running",
# #         "endpoints": {
# #             "manifest": "/manifest",
# #             "download": "/download/<file_id>"
# #         }
# #     })
# #
# #
# #
# # if __name__ == '__main__':
# #     print(f"Backend on http://{HOST}:{PORT} | Folder: {DRIVE_FOLDER_ID}")
# #     app.run(host=HOST, port=PORT)
#
#
#
#
# import io
# import os
# import json
# from flask import Flask, jsonify, send_file, abort, request
# from flask_cors import CORS
# from googleapiclient.discovery import build
# from google.oauth2 import service_account
# from googleapiclient.http import MediaIoBaseDownload
#
# # -------- CONFIG ----------
# DRIVE_FOLDER_ID = "1CyDBGm6BvIY5SErybLue9jC1r-WL18EB"  # from the Drive folder URL
# HOST = "0.0.0.0"
# PORT = int(os.environ.get("PORT", 5000))
# API_KEY = os.environ.get("API_KEY")  # set a secret API key in Railway
# # --------------------------
#
# SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
#
# app = Flask(__name__)
# CORS(app)
#
# # Load Google Service Account credentials from environment variable
# service_account_info = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
# if not service_account_info:
#     raise Exception("Google service account JSON not found in environment variables!")
#
# creds_dict = json.loads(service_account_info)
# creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
#
# drive_service = build('drive', 'v3', credentials=creds, cache_discovery=False)
#
# def list_files_in_folder(folder_id):
#     files = []
#     page_token = None
#     q = f"'{folder_id}' in parents and trashed = false"
#     while True:
#         response = drive_service.files().list(
#             q=q,
#             spaces='drive',
#             fields='nextPageToken, files(id, name, mimeType, modifiedTime, size, md5Checksum)',
#             pageToken=page_token
#         ).execute()
#         files.extend(response.get('files', []))
#         page_token = response.get('nextPageToken', None)
#         if page_token is None:
#             break
#     return files
#
# def require_api_key():
#     key = request.headers.get("x-api-key")
#     if not API_KEY or key != API_KEY:
#         abort(401, description="Unauthorized: invalid API key")
#
# @app.route('/manifest', methods=['GET'])
# def manifest():
#     """ Returns JSON manifest of files in the folder """
#     require_api_key()
#     try:
#         files = list_files_in_folder(DRIVE_FOLDER_ID)
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
#
#     version = max((f.get('modifiedTime') or '') for f in files) if files else ""
#
#     manifest_files = []
#     for f in files:
#         manifest_files.append({
#             "name": f.get("name"),
#             "id": f.get("id"),
#             "modifiedTime": f.get("modifiedTime"),
#             "md5": f.get("md5Checksum"),
#             "download_url": f"/download/{f.get('id')}"
#         })
#
#     return jsonify({
#         "version": version,
#         "files": manifest_files
#     })
#
# @app.route('/download/<file_id>', methods=['GET'])
# def download(file_id):
#     """ Streams a Drive file to the client """
#     require_api_key()
#     try:
#         metadata = drive_service.files().get(fileId=file_id, fields='name, mimeType').execute()
#         file_name = metadata.get('name', file_id)
#         mime = metadata.get('mimeType', 'application/octet-stream')
#
#         request_media = drive_service.files().get_media(fileId=file_id)
#         fh = io.BytesIO()
#         downloader = MediaIoBaseDownload(fh, request_media)
#         done = False
#         while not done:
#             status, done = downloader.next_chunk()
#
#         fh.seek(0)
#         return send_file(
#             fh, mimetype=mime, as_attachment=True, download_name=file_name
#         )
#     except Exception as e:
#         return abort(404, description=str(e))
#
# @app.route('/')
# def home():
#     return jsonify({
#         "status": "Backend is running",
#         "endpoints": {
#             "manifest": "/manifest",
#             "download": "/download/<file_id>"
#         },
#         "note": "All endpoints require x-api-key header"
#     })
#
# if __name__ == '__main__':
#     print(f"Backend on http://{HOST}:{PORT} | Folder: {DRIVE_FOLDER_ID}")
#     app.run(host=HOST, port=PORT)




