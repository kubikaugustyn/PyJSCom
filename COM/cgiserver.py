#  -*- coding: utf-8 -*-
__author__ = "radek.augustyn@email.cz"

import datetime
import urllib, codecs, web, os
#package web is named web.py, not web

from .htmlhelpers import replaceHTMLTags, getFileExtension, getFileContent
import logging as log

IS_SERVER_SOFTWARE = 'SERVER_SOFTWARE' in os.environ
from os import O_BINARY

CONFIG = type('Test', (object,), {})

def strToBool(s):
    return s.lower() in ["true", "T", "1"]

class TypedList(list):
    """List class for store specific value types."""

    def __init__(self, itemType=int, seq=()):
        """Initialize typed list instance.

        :param type: Type of items allowed.
        :param seq: Initial items sequence.

        >>> TypedList(int, [5, 6])
        [5, 6]
        >>> TypedList(basestring, ["5", "6"])
        ["5", "6"]

        """
        self.itemType = itemType
        for item in seq:
            self.validateItem(item)
        list.__init__(self, seq)


    def validateItem(self, item):
        """Valudates value prior it's placing into list. If not, raise TypeError.

        :param item: Item to be validated.
        """
        if hasattr(item, "__class__"):
            cls = item.__class__
        else:
            cls = item

        if not issubclass(cls, self.itemType):
            raise TypeError('%r value is not allowed in %r list.' % (item, self.itemType.__name__))

        return True


    # Original methods with type validation
    def append(self, p_object):
        """Validate and append p_object."""
        if self.validateItem(p_object):
            list.append(self, p_object)


    def insert(self, index, p_object):
        """Validate and insert p_object."""
        self.validateItem(p_object)
        list.insert(self, index, p_object)


    def extend(self, iterable):
        """Validate each item in iterable and extends list by it."""
        for item in iterable:
            self.validateItem(item)
        list.extend(self, iterable)


    def asDict(self, deep=True):
        result = []
        for item in self.__iter__():
            if hasattr(item, "asDict"):
                result.append(item.asDict(deep))
        return result


class Container:
    """Empty class holding values. Pascal record or CPP union equivalent."""

    def __init__(self, fieldNamesOrFields=None, fields={}, fieldNames=[]):
        """

        :param fieldNamesOrFields:
        :param fields:
        :param fieldNames:

        >>> Container(["id", "name"])
        Container({'id': None, 'name': None})

        >>> Container({"id": 0, "name": "Test"})
        Container({'id': 0, 'name': 'Test'})
        """
        if fieldNamesOrFields:
            if isinstance(fieldNamesOrFields, list):
                fieldNames = fieldNamesOrFields
            elif isinstance(fieldNamesOrFields, dict):
                fields = fieldNamesOrFields

        if fields:
            for fieldName, fieldValue in fields.items():
                setattr(self, fieldName, fieldValue)

        if fieldNames:
            for fieldName in fieldNamesOrFields:
                setattr(self, fieldName, None)

    def __repr__(self):
        return "Container(%s)" % str(self.__dict__)


def getMimeType(fileName):
    return {
        ".js": "application/javascript",
        ".json": "application/json",
        ".css": "text/css; charset=utf-8",
        ".png": "image/png",
        ".ico": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".htm": "text/html; charset=utf-8",
        ".html": "text/html; charset=utf-8",
        ".txt": "text/plain; charset=utf-8",
        ".log": "text/plain; charset=utf-8",
    }.get(getFileExtension(fileName), "application/data")


class DirectoryProvider:
    def __init__(self, path):
        self.path = os.path.normpath(path)
        self.templateProcessors = {}

    def applyTemplates(self, fileName, content=""):
        if not content:
            content = getFileContent(fileName)
        fileExtension = getFileExtension(fileName).lower()
        for templateProcessor, applicableExtensions in self.templateProcessors.items():
            if fileExtension in applicableExtensions:
                content = templateProcessor.processContent(content, fileName)
        return content

    def provideFileProcessor(self, request, response):
        log.debug("Processing path alias...")
        log.debug("request.subPath=" + str(request.subPath))
        fileNameBase = "/".join(request.subPath)
        if fileNameBase:
            log.debug("Requesting file '%s'" % fileNameBase)
            fileName = os.path.normpath(os.path.join(self.path, fileNameBase))
            if os.path.exists(fileName):
                if os.path.isfile(fileName):
                    response.htmlData = self.applyTemplates(fileName)
                    response.mimeFormat = getMimeType(fileName)
                    response.handled = True
                else:
                    log.error(fileName + " is a directory.")
                    response.msgs.append(fileName + " is a directory.")
            else:
                log.error("File '%s' not found" % fileNameBase)
                response.msgs.append("File %s not found" % fileNameBase)
        else:
            log.error("You must specify file name")
        ## log.closeSection()


class DirectoryProviders(TypedList):
    def __init__(self):
        TypedList.__init__(self, DirectoryProvider)

    def getProvider(self, path):
        path = os.path.normpath(path)
        for provider in self:
            if provider.path == path:
                return provider

        provider = DirectoryProvider(path)
        self.append(provider)
        return provider

    def getProcessor(self, path):
        return self.getProvider(path).provideFileProcessor


providers = DirectoryProviders()
urls = ('/(.*)', 'handler')
cssData = None
operations = {
}

HTML_RESULT_TEMPLATE = """
<html>
    <head>
        <!--<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">-->
        <!--<script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>-->
        <!--<script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.12.9/umd/popper.min.js" integrity="sha384-ApNbgh9B+Y1QKtv3Rn7W3mgPxhU9K/ScQsAP7hUibX39j7fakFPskvXusvfa0b4Q" crossorigin="anonymous"></script>-->
        <!--<script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js" integrity="sha384-JZR6Spejh4U02d8jOt6vLEHfe/JQGiRRSQQxSfFWpi1MquVdAyjUar5+76PVCmYl" crossorigin="anonymous"></script>-->
    </head>
    <body>
    <div class="container">
      HTML_DATA
    </div>

    </body>
</html>    
"""


class PathContainer:
    @staticmethod
    def getProcessor(processorOrPathContainer):
        if isinstance(processorOrPathContainer, PathContainer):
            return processorOrPathContainer.proc
        else:
            return processorOrPathContainer

    @staticmethod
    def getDescription(processorOrPathContainer):
        if isinstance(processorOrPathContainer, PathContainer):
            return processorOrPathContainer.description
        else:
            return ""

    def __init__(self, proc, description=""):
        self.proc = proc
        self.description = description


def processRequest(request, response):
    #log.startCommand()
    log.debug("REQUEST:%s::%s" % (request.path, str(request.query)))
    path = request.path.lower()

    pathFound = False
    log.debug("Searching for path")
    for operationPath, info in operations.items():
        if path.startswith(operationPath.lower()):
            log.info("Processor for path '%s' found" % operationPath)
            subPath = request.path[len(operationPath) + 1:]
            if subPath:
                request.subPath = subPath.split("/")
            else:
                request.subPath = []
            processor = PathContainer.getProcessor(info)
            processor(request, response)
            pathFound = True
    if not pathFound:
        log.info("Unknown request")
    # log.closeSection()

    if not response.handled:
        response.buildResult("")
    # log.closeSection()


class HTTPResponse:
    def __init__(self, handled, mimeFormat="text/html", htmlData=""):
        self.handled = handled
        self.mimeFormat = mimeFormat
        self.htmlData = htmlData
        self.contextDisposition = None
        self.htmlTags = {}
        self.msgs = []

    def returnFile(self, fileName, fileNameBase=""):
        if os.path.exists(fileName):
            if os.path.isfile(fileName):
                self.buildResult(open(fileName, "rb").read(), getMimeType(fileName))
            else:
                log.error(fileName + " is a directory.")
                self.msgs.append(fileName + " is a directory.")
        else:
            from html import pathLeaf
            if not fileNameBase:
                fileNameBase = pathLeaf(fileName)
            log.error("File '%s' not found" % fileNameBase)
            self.msgs.append("File %s not found" % fileNameBase)

    def buildResult(self, htmlData, format="text/html"):
        def formatLogLine(line):
            if line.find("ERROR") >= 0:
                line = "<div class='errorLine'>" + line + "</div>"
            return line

        formatType = format.lower()
        if format.find(";") >= 0:
            formatType = formatType[:format.find(";")]

        if formatType in ["text/json", "application/json"] and not isinstance(htmlData, str):
            from json import dumps
            htmlData = dumps(htmlData, indent=4).decode('unicode-escape').encode('utf8')

        if formatType == "text/html" and htmlData:
            if htmlData.find("<html>") < 0:
                #if htmlData:
                #    htmlData += "<hr>"

                htmlData = HTML_RESULT_TEMPLATE.replace("HTML_DATA", htmlData)

            htmlData = htmlData.replace("#datetime#", str(datetime.datetime.now()))
            if cssData:
                htmlData = htmlData.replace("</head>", f"{cssData}</head>")

            pathInfos = []
            for key in sorted(operations.keys()):
                info = operations[key]
                pathInfos.append({"name": key, "description": PathContainer.getDescription(info)})
            self.htmlTags["/* PATH_INFOS */"] = str(pathInfos)

            htmlData = replaceHTMLTags(htmlData, self.htmlTags)

        self.handled = True
        self.mimeFormat = format
        self.htmlData = htmlData


class QueryReader:
    def __init__(self, key, defaultValue=None, type=None, mandatory=False):
        self.key = key
        self.defaultValue = defaultValue
        self.type = type
        self.mandatory = mandatory


class HTTPRequest:
    def __init__(self, path, query, remoteUrl):
        assert isinstance(path, str)
        assert isinstance(query, dict)
        assert isinstance(remoteUrl, str)

        self.path = path
        self.query = {}
        for key, value in query.items():
            self.query[key.lower()] = value
        self.remoteUrl = remoteUrl
        self.pathItems = path.split("/")[1:]

    def getQueryValue(self, key, defaultValue=None, type=None):
        value = self.query.get(key.lower(), defaultValue)
        if value and type and not isinstance(value, type):
            if type == float:
                value = float(value)
            elif type == bool:
                value = strToBool(value)
        return value

    def getLowerPathItem(self, index):
        pathItem = self.getPathItem(index)
        if pathItem:
            return pathItem.lower()

    def getPathItem(self, index):
        if index < len(self.pathItems):
            return self.pathItems[index]

    def readQuery(self, params=[]):
        items = {}
        for reader in params:
            value = self.getQueryValue(reader.key, reader.defaultValue)
            if reader.mandatory and not value:
                log.error("Query parameter '%s' is missing" % reader.key)
                return None
            if value and reader.type:
                value = reader.type(value)
            items[reader.key] = value

        return Container(items)


class MyApplication(web.application):
    def run(self, port, *middleware):
        func = self.wsgifunc(*middleware)
        return web.httpserver.runsimple(func, ("localhost", port))


def getHTTPOrigin():
    if CONFIG.isCGIApplication:
        remoteHost = os.environ.get("REMOTE_HOST")
        remoteAddr = os.environ.get("REMOTE_ADDR")
        if remoteHost:
            result = remoteHost
        else:
            result = remoteAddr
    else:
        result = web.ctx.environ.get('HTTP_ORIGIN', None)
        if not result:
            result = "http://localhost:63342"

    return result


class handler:
    def doProcessRequest(self, page):
        CONFIG.isCGIApplication = False
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Access-Control-Allow-Credentials', 'true')

        request = HTTPRequest(page, dict(web.input()), getHTTPOrigin())
        response = HTTPResponse(False)
        processRequest(request, response)

        if response.handled:
            web.header("Content-Type", response.mimeFormat + "; charset=utf-8")
            if response.contextDisposition:
                web.header("Content-Disposition", response.contextDisposition)
            return response.htmlData
        else:
            web.header("Content-Type", "text/plain;charset=utf-8")
            return "doProcessRequest Error"

    def GET(self, page):
        return self.doProcessRequest(page)

    def POST(self, page):
        return self.doProcessRequest(page)


def runServer(portNumber, op):
    #if not log.logger:
    #    import os

    #log.createLogger(os.path.dirname(__file__) + "cgiserver.log")

    global operations
    operations.update(op)

    # Nastavení znakové sady na utf-8
    #from pygeotoolbox.sharedtools import setupEncoding
    #setupEncoding()

    if IS_SERVER_SOFTWARE:
        import cgi, cgitb, sys
        cgitb.enable()

        if sys.platform == "win32":
            import msvcrt

            msvcrt.setmode(0, O_BINARY)  # stdin  = 0
            msvcrt.setmode(1, O_BINARY)  # stdout = 1

        CONFIG.isCGIApplication = True
        jsonLog = {}

        form = cgi.FieldStorage()
        query = {}
        for item in form.list:
            if hasattr(item, "filename") and item.filename:
                query[item.name] = item
            else:
                decodedValue = urllib.unquote(item.value)
                try:
                    decodedValue = decodedValue.decode("utf-8")
                except:
                    decodedValue = codecs.decode(decodedValue, "latin-1")
                decodedValue = urllib.unquote(decodedValue)
                query[item.name] = decodedValue

            jsonLog[item.name] = decodedValue

        request = HTTPRequest("", query, getHTTPOrigin())
        response = HTTPResponse(False)
        processRequest(request, response)

        if not response.handled:
            response.handled = True
            response.mimeFormat = "text/html"
            response.htmlData = "ProcessRequest not handled"
            for key, value in query.items():
                response.htmlData += "<br>%s:%s" % (str(key), str(value))

        print("Content-Type: " + response.mimeFormat + "; charset=utf-8")  # HTML is following
        if response.contextDisposition:
            print("Content-Disposition: " + response.contextDisposition)
        print("Access-Control-Allow-Origin: *")
        print  # blank line, end of headers

        if response.mimeFormat in ["text/html", "text/javascript", "text/plain"]:
            sys.stdout.write(response.htmlData.encode('utf-8'))
        else:
            if sys.platform != "win32":
                sys.stdout.write(response.htmlData)
                sys.stdout.flush()
            else:
                import os, msvcrt
                msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
                sys.stdout.write(response.htmlData)
                sys.stdout.flush()
                msvcrt.setmode(sys.stdout.fileno(), os.O_TEXT)

    else:
        app = MyApplication(urls, globals())
        app.run(port=portNumber)
