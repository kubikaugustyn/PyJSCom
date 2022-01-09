from .cgiserver import runServer, getMimeType
from .htmlhelpers import fileRead
import threading, os, json


class Communication:
    def __init__(self, data, port):
        self.data = data
        self.port = port
        self.__isServerRunning = False
        self.runThread = threading.Thread(target=self.__Run, args=())
        self.commands = []
        self.thisPath = os.path.dirname(os.path.abspath(__file__)) + os.sep
        self.readedString = "Readed_"

    def __Run(self):
        runServer(self.port, {
            "": self.__home,
            "/": self.__home,
            "console": self.__console,
            "console/data.json": self.__dataJSON,
            "console/send": self.__consoleSend,
            "console/script.js": self.__scriptJS,
            "console/w3schools.css": self.__w3schoolsCSS
        })

    def __home(self, request, response):
        s = ''
        for key, value in request.query.items():
            s += f'{key}:{value}<br>'
        response.buildResult(
            '<h2>Params:</h2>' + s + "<br><a href='console'>Console</a><script>document.title = 'Server'</script>")

    def __console(self, request, response):
        response.buildResult(fileRead(self.thisPath + 'consolePage/console.html'))

    def __dataJSON(self, request, response):
        response.buildResult(json.dumps({"html_data": self.data, "commands": self.commands}), 'application/json')

    def __scriptJS(self, request, response):
        response.buildResult(fileRead(self.thisPath + 'consolePage/script.js'), getMimeType("script.js"))

    def __w3schoolsCSS(self, request, response):
        response.buildResult(fileRead(self.thisPath + 'consolePage/w3schools.css'), getMimeType("w3schools.css"))

    def __consoleSend(self, request, response):
        text = request.query["text"]

        if text.find(self.readedString) == 0 and len(self.commands) > 0:
            del self.commands[self.commands.index(text[len(self.readedString):])]
        else:
            self.__onReceive(text)

        response.buildResult(fileRead(self.thisPath + 'consolePage/consoleSend.html'), getMimeType("consoleSend.html"))

    def __onReceive(self, text):
        self.onReceive(text)

    def onReceive(self, text):
        pass

    def send(self, text):
        if not self.commands.__contains__(text):
            self.commands.append(text)

    def reloadConsole(self):
        self.send("console.reload()")

    def run(self):
        if not self.__isServerRunning:
            self.__isServerRunning = True
            self.runThread.start()
        else:
            print(f"Server is already running at port {self.port}, url is: http://localhost:{self.port}/")

