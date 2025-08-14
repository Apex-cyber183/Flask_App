# # backend.py
# import io
# import os
# import json
# from flask import Flask, request, jsonify, send_file, abort
# from google.oauth2 import service_account
# from googleapiclient.discovery import build
# from googleapiclient.http import MediaIoBaseDownload
#
# # Config
# SERVICE_ACCOUNT_FILE = "certain-tangent-465609-p5-ce8ccab7ef90.json"   # path to your service account json
# SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
# DEFAULT_PAGE_SIZE = 1000
#
# app = Flask(__name__)
#
# # Build the Drive service with the service account
# credentials = service_account.Credentials.from_service_account_file(
#     SERVICE_ACCOUNT_FILE, scopes=SCOPES)
# drive_service = build('drive', 'v3', credentials=credentials, cache_discovery=False)
#
#
# def list_files_in_folder(folder_id):
#     """List files inside a Drive folder (non-recursive)"""
#     q = f"'{folder_id}' in parents and trashed = false"
#     fields = "nextPageToken, files(id, name, mimeType, size, md5Checksum, modifiedTime)"
#     files = []
#     page_token = None
#     while True:
#         res = drive_service.files().list(q=q, pageSize=DEFAULT_PAGE_SIZE, fields=fields, pageToken=page_token).execute()
#         files.extend(res.get('files', []))
#         page_token = res.get('nextPageToken', None)
#         if not page_token:
#             break
#     return files
#
#
# @app.route('/manifest', methods=['GET'])
# def manifest():
#     """
#     Query: /manifest?folderId=FOLDER_ID
#     Returns a JSON manifest describing files (name, id, modifiedTime, size)
#     """
#     folder_id = request.args.get('folderId')
#     if not folder_id:
#         return jsonify({'error': 'folderId required'}), 400
#
#     try:
#         files = list_files_in_folder(folder_id)
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
#
#     # Build a manifest. You can choose versioning strategy; here we'll use latest modifiedTime
#     if files:
#         latest = max(files, key=lambda f: f.get('modifiedTime', ''))
#         manifest_version = latest.get('modifiedTime')
#     else:
#         manifest_version = ""
#
#     manifest = {
#         "folderId": folder_id,
#         "version": manifest_version,
#         "files": []
#     }
#
#     for f in files:
#         manifest['files'].append({
#             "name": f.get('name'),
#             "fileId": f.get('id'),
#             "mimeType": f.get('mimeType'),
#             "size": f.get('size'),
#             "md5": f.get('md5Checksum'),
#             "modifiedTime": f.get('modifiedTime'),
#             # Download endpoint on our backend (so Unity never needs Drive direct link / ID)
#             "downloadUrl": f"/download/{f.get('id')}"
#         })
#
#     return jsonify(manifest)
#
#
# @app.route('/download/<file_id>', methods=['GET'])
# def download(file_id):
#     """Proxy download for the Drive file. This returns the raw file bytes."""
#     try:
#         request_drive = drive_service.files().get_media(fileId=file_id)
#         fh = io.BytesIO()
#         downloader = MediaIoBaseDownload(fh, request_drive)
#         done = False
#         while not done:
#             status, done = downloader.next_chunk()
#             # optional: print progress
#             # print("Download progress: %d%%" % int(status.progress() * 100))
#         fh.seek(0)
#         # Try to get metadata to derive filename
#         meta = drive_service.files().get(fileId=file_id, fields="name, mimeType").execute()
#         filename = meta.get('name', file_id)
#         return send_file(fh, as_attachment=True, download_name=filename)
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
#
#
# if __name__ == '__main__':
#     # Use whatever host/port suitable; ensure HTTPS for production
#     app.run(host='0.0.0.0', port=5000, debug=False)




from flask import Flask, jsonify
from googleapiclient.discovery import build
from google.oauth2 import service_account

# CONFIG
SERVICE_ACCOUNT_FILE = r"C:\Users\Admin\Desktop\drive_backend\certain-tangent-465609-p5-ce8ccab7ef90.json"  # Path to your downloaded key
FOLDER_ID = "1CyDBGm6BvIY5SErybLue9jC1r-WL18EB"  # The ID of your shared Addressables folder
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

app = Flask(__name__)

def get_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

@app.route("/manifest", methods=["GET"])
def get_manifest():
    service = get_drive_service()

    results = service.files().list(
        q=f"'{FOLDER_ID}' in parents and trashed=false",
        fields="files(id, name, modifiedTime)"
    ).execute()

    files = results.get('files', [])
    manifest = []

    for file in files:
        manifest.append({
            "name": file["name"],
            "id": file["id"],
            "modified": file["modifiedTime"],
            "downloadUrl": f"https://drive.google.com/uc?export=download&id={file['id']}"
        })

    return jsonify({
        "version": max(f["modified"] for f in manifest) if manifest else None,
        "files": manifest
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
