#!/usr/bin/env python3
"""Simple web server to decompress Raspberry Pi OS .img.xz images.

The server presents a web form for uploading a `.img.xz` file.
After upload, the file is decompressed using Python's `lzma` module
and streamed back to the client as an `.img` download.
"""

import lzma
import os
from http import server
import cgi

HTML_FORM = b"""<html><body><h1>Upload Raspberry Pi OS image (.img.xz)</h1>
<form method='POST' enctype='multipart/form-data'>
<input type='file' name='image'>
<input type='submit' value='Upload and Decompress'>
</form></body></html>"""


class DecompressHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(HTML_FORM)

    def do_POST(self):
        ctype, pdict = cgi.parse_header(self.headers.get('Content-Type'))
        if ctype != 'multipart/form-data':
            self.send_error(400, "Invalid form submission")
            return
        form = cgi.FieldStorage(fp=self.rfile,
                                headers=self.headers,
                                environ={'REQUEST_METHOD': 'POST'},
                                keep_blank_values=True)
        if 'image' not in form:
            self.send_error(400, "File field 'image' missing")
            return
        file_item = form['image']
        if not file_item.filename.endswith('.img.xz'):
            self.send_error(400, 'Only .img.xz files are accepted')
            return
        try:
            decompressed = lzma.LZMAFile(file_item.file).read()
        except lzma.LZMAError:
            self.send_error(400, 'Failed to decompress file')
            return

        self.send_response(200)
        self.send_header('Content-Type', 'application/octet-stream')
        out_name = os.path.splitext(file_item.filename)[0]
        if not out_name.endswith('.img'):
            out_name += '.img'
        self.send_header('Content-Disposition', f'attachment; filename="{out_name}"')
        self.end_headers()
        self.wfile.write(decompressed)


def run(server_class=server.HTTPServer, handler_class=DecompressHandler):
    addr = ('', 8000)
    httpd = server_class(addr, handler_class)
    print(f"Serving on http://{addr[0] or 'localhost'}:{addr[1]}")
    httpd.serve_forever()


if __name__ == '__main__':
    run()
