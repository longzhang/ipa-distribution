#!/usr/bin/env python
# -*- coding:utf-8 -*- 
"""Simple HTTP Server With Upload.
 
This module builds on BaseHTTPServer by implementing the standard GET
and HEAD requests in a fairly straightforward manner.
 
"""
__version__ = "0.1"
__all__ = ["an ios ipa upload and distrbut tools"]
__author__ = "long.zhang@rekoo.com"
__home_page__ = ""
 
import os
import posixpath
import BaseHTTPServer
from BaseHTTPServer import HTTPServer , BaseHTTPRequestHandler
import urllib
import cgi
import shutil
import mimetypes
import re
from SocketServer import ThreadingMixIn
import threading
import sys
port = None
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
 
#itms-services://?action=download-manifest&url=http://192.168.1.22/static/memeyu.plist 

class SimpleHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
 
    """Simple HTTP request handler with GET/HEAD/POST commands.
 
    This serves files from the current directory and any of its
    subdirectories.  The MIME type for files is determined by
    calling the .guess_type() method. And can reveive file uploaded
    by client.
 
    The GET/HEAD/POST requests are identical except that the HEAD
    request omits the actual contents of the file.
 
    """
 
    server_version = "SimpleHTTPWithUpload/" + __version__
 
    def do_GET(self):
        """Serve a GET request."""
        self.host = self.headers.get('host')
        f = self.send_head()
        if f:
            self.copyfile(f, self.wfile)
            f.close()
 
    def do_HEAD(self):
        """Serve a HEAD request."""
        f = self.send_head()
        if f:
            f.close()
 
    def do_POST(self):
        """Serve a POST request."""
        r, info = self.deal_post_data()
        print r, info, "by: ", self.client_address
        f = StringIO()
        f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write("<html>\n<title>Upload Result Page</title>\n")
        f.write("<body>\n<h2>Upload Result Page</h2>\n")
        f.write("<hr>\n")
        if r:
            f.write("<strong>Success:</strong>")
        else:
            f.write("<strong>Failed:</strong>")
        f.write(info)
        f.write("<br><a href=\"%s\">back</a>" % self.headers['referer'])
        f.write("<hr><small>Powerd by zhanglong  long.zhang@rekoo.com")
        f.write("</small></body>\n</html>\n")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        if f:
            self.copyfile(f, self.wfile)
            f.close()
        
    def deal_post_data(self):
        boundary = self.headers.plisttext.split("=")[1]
        remainbytes = int(self.headers['content-length'])
        line = self.rfile.readline()
        remainbytes -= len(line)
        if not boundary in line:
            return (False, "Content NOT begin with boundary")
        line = self.rfile.readline()
        remainbytes -= len(line)
        fn = re.findall(r'Content-Disposition.*name="file"; filename="(.*)"', line)
        if not fn:
            return (False, "Can't find out file name...")
        path = self.translate_path(self.path)
        fn = os.path.join(path, fn[0])
        line = self.rfile.readline()
        remainbytes -= len(line)
        line = self.rfile.readline()
        remainbytes -= len(line)
        try:
            out = open(fn, 'wb')
        except IOError:
            return (False, "Can't create file to write, do you have permission to write?")
                
        preline = self.rfile.readline()
        remainbytes -= len(preline)
        while remainbytes > 0:
            line = self.rfile.readline()
            remainbytes -= len(line)
            if boundary in line:
                preline = preline[0:-1]
                if preline.endswith('\r'):
                    preline = preline[0:-1]
                out.write(preline)
                out.close()
                return (True, "File '%s' upload success!" % fn)
            else:
                out.write(preline)
                preline = line
        return (False, "Unexpect Ends of data.")
 
    def send_head(self):
        """Common code for GET and HEAD commands.
 
        This sends the response code and MIME headers.
 
        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.
 
        """
        path = self.translate_path(self.path)
        ctype = self.guess_type(path)
        f = None
        if self.path.endswith('.restart'):
            os.system('/opt/sites/buyu_backend/web_api/restart.sh')
            self.send_response(200)
            self.send_header("Content-type", ctype)
            self.end_headers()
            f = StringIO()
            f.write('restart success!!')
            return

        if self.path.endswith('_itunes'):
            self.send_response(200)
            self.send_header("Content-type", ctype)
            self.end_headers()
            f = StringIO()
            f.write('restart success!!')
            return
        if self.path.endswith('.plist'):
            f = StringIO()
            ipa_name = self.path.split('/')[-1].split('.')[0]
            self.send_response(200)
            self.send_header("Content-type", ctype)
            #self.send_header("Content-type", "application/x-www-form-urlencoded")
            self.end_headers()
            ipa_url = 'http://%s/%s.ipa' % (self.host , ipa_name)
            plist_content = make_plist_content(ipa_url , ipa_name)
            f.write(plist_content)
            print 'plist content ' , plist_content
            f.seek(0)
            return f 

        if os.path.isdir(path):
            if not self.path.endswith('/'):
                # redirect browser - doing basically what apache does
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.list_directory(path)
        ctype = self.guess_type(path)
        try:
            # Always read in binary mode. Opening files in text mode may cause
            # newline translations, making the actual size of the content
            # transmitted *less* than the content-length!
            f = open(path, 'rb')
        except IOError:
            self.send_error(404, "File not found")
            return None
        self.send_response(200)
        self.send_header("Content-type", ctype)
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f
 
    def list_directory(self, path):
        """Helper to produce a directory listing (absent index.html).
 
        Return value is either a file object, or None (indicating an
        error).  In either case, the headers are sent, making the
        interface the same as for send_head().
 
        """
        try:
            list = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        list.sort(key=lambda a: a.lower())
        f = StringIO()
        displaypath = cgi.escape(urllib.unquote(self.path))
        f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write("<html>\n<title>Directory listing for %s</title>\n" % displaypath)
        f.write("<body>\n<h2>Directory listing for %s</h2>\n" % displaypath)
        f.write("<hr>\n")
        f.write("<form ENCTYPE=\"multipart/form-data\" method=\"post\">")
        f.write("<input name=\"file\" type=\"file\"/>")
        f.write("<input type=\"submit\" value=\"upload\"/></form>\n")
        f.write("<hr>\n<ul>\n")
        for name in list:
            if name.endswith('pyc'):
                continue
            if name.endswith('py'):
                continue
            if name.endswith('out'):
                continue
            if name.endswith('~'):
                continue
            fullname = os.path.join(path, name)
            displayname = linkname = name
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            if os.path.islink(fullname):
                displayname = name + "@"
                # Note: a link to a directory displays with @ and links with /
            f.write('<li><a href="%s">%s</a>\n'
                    % (urllib.quote(linkname), cgi.escape(displayname)))
            if name.endswith('ipa'):
                url = 'itms-services://?action=download-manifest&url=http://%s/%s.plist' % ( self.host , cgi.escape(displayname).split('.')[0] )
                to_write = '<a href="%s">ios download</a>'
                to_write = to_write % (url)
                f.write(to_write )
        f.write("</ul>\n<hr>\n</body>\n</html>\n")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f
 
    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.
 
        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)
 
        """
        # abandon query parameters
        path = path.split('?',1)[0]
        path = path.split('#',1)[0]
        path = posixpath.normpath(urllib.unquote(path))
        words = path.split('/')
        words = filter(None, words)
        path = os.getcwd()
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir): continue
            path = os.path.join(path, word)
        return path
 
    def copyfile(self, source, outputfile):
        """Copy all data between two file objects.
 
        The SOURCE argument is a file object open for reading
        (or anything with a read() method) and the DESTINATION
        argument is a file object open for writing (or
        anything with a write() method).
 
        The only reason for overriding this would be to change
        the block size or perhaps to replace newlines by CRLF
        -- note however that this the default server uses this
        to copy binary data as well.
 
        """
        shutil.copyfileobj(source, outputfile)
 
    def guess_type(self, path):
        """Guess the type of a file.
 
        Argument is a PATH (a filename).
 
        Return value is a string of the form type/subtype,
        usable for a MIME Content-type header.
 
        The default implementation looks the file's extension
        up in the table self.extensions_map, using application/octet-stream
        as a default; however it would be permissible (if
        slow) to look inside the data to make a better guess.
 
        """
 
        base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return self.extensions_map['']
 
    if not mimetypes.inited:
        mimetypes.init() # try to read system mime.types
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({
        '': 'application/octet-stream', # Default
        '.py': 'text/plain',
        '.c': 'text/plain',
        '.h': 'text/plain',
        })
 
class ThreadHTTPServer(ThreadingMixIn , HTTPServer):
    pass

def test(HandlerClass = SimpleHTTPRequestHandler, ServerClass = BaseHTTPServer.HTTPServer):
    #BaseHTTPServer.test(HandlerClass, ServerClass)
    server = ThreadHTTPServer(('0.0.0.0',port),HandlerClass )
    print server
    print 'ready start'
    server.serve_forever()
    
def make_plist_content(ipa_url , name): 
    plist_content="""<?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
    <dict>
       <key>items</key>
       <array>
           <dict>
               <key>assets</key>
               <array>
                   <dict>
                       <key>kind</key>
                       <string>software-package</string>
                       <key>url</key>
                       <string>%s</string>
                   </dict>
                   <dict>
                       <key>kind</key>
                       <string>display-image</string>
                       <key>needs-shine</key>
                       <true/>
                       <key>url</key>
                       <string>http://a4.mzstatic.com/us/r30/Purple4/v4/70/61/05/70610526-8929-0092-b95d-8a8e5f8410c6/mzl.ucghkxxu.175x175-75.jpg</string>
                   </dict>
               <dict>
                       <key>kind</key>
                       <string>full-size-image</string>
                       <key>needs-shine</key>
                       <true/>
                       <key>url</key>
                       <string>http://a4.mzstatic.com/us/r30/Purple4/v4/70/61/05/70610526-8929-0092-b95d-8a8e5f8410c6/mzl.ucghkxxu.175x175-75.jpg</string>
                   </dict>
               </array><key>metadata</key>
               <dict>
                   <key>bundle-identifier</key>
                   <string>com.rekoo.fishingcube91</string>
                   <key>bundle-version</key>
                   <string>1.0</string>
                   <key>kind</key>
                   <string>software</string>
                   <key>subtitle</key>
                   <string>%s</string>
                   <key>title</key>
                   <string>%s</string>
               </dict>
           </dict>
       </array>
    </dict>
    </plist>
    
    """
    return plist_content % ( ipa_url , name , name)
if __name__ == '__main__':
    try: 
	port = sys.argv[1]
    except:
        port = 80

    port = int(port)
    test()
