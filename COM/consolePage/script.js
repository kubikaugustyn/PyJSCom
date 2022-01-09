var rootDiv, iframesDiv, lastDataString = "", latestData, readedCommands = []
var checkForChangesPerSecond = 20
var offlineCheckForChangesPerSecond = 1
var readedString = "Readed_"

function onLoad() {
    rootDiv = document.getElementById("root")
    iframesDiv = document.getElementById("iframes")
    checkForChanges()
    commandTemplates["console.reload()"]("console.reload()", -1)
}

function buildHTMLContent(html_data) {
    rootDiv.innerHTML = ""
    for (var data of html_data) {
        drawData(rootDiv, data, false)
    }
}

function processCommands(commands) {
    for (var i in commands) {
        var command = commands[i]
        if (!readedCommands.includes(command)) {
            var isTemplate = false
            for (var commandTemplate of Object.keys(commandTemplates)) {
                if (command.search(commandTemplate) > -1) {
                    isTemplate = true
                    readedCommands.push(command)
                    commandTemplates[commandTemplate](command, i)// command.replace(commandTemplate, "")
                    break
                }
            }
            if (!isTemplate) {
                readedCommands.push(command)
                onReceive(command)
            }
        }
    }
    while (readedCommands.length > 0) {
        var readedCommand = readedCommands.shift()
        send(readedString + readedCommand, (readedCommand) => {
            // console.log("Readed command:", readedCommand)
        })
    }
}

function checkForChanges() {
    var [responseJSON, status] = getJSON(document.location.origin + "/console/data.json")
    if (status === 200) {
        latestData = responseJSON
        var latestDataString = JSON.stringify(latestData)
        if (lastDataString !== latestDataString) {
            lastDataString = latestDataString
            processCommands(latestData.commands)
        }
        setTimeout(checkForChanges, 1000 / checkForChangesPerSecond)
    } else {
        console.log("Something went wrong with data response status, may be 200, but is", status)
        setTimeout(checkForChanges, 1000 / offlineCheckForChangesPerSecond)
    }
}

var commandTemplates = {
    "document.location.reload()": (command, i) => {
        document.location.reload()
    },
    "console.reload()": (command, i) => {
        buildHTMLContent(latestData.html_data)
    }
}

function readTextFile(url) {
    var http = new XMLHttpRequest();
    http.open("GET", url, false);
    try {
        http.send();
    } catch (e) {

    }
    return [http.responseText, http.status]
}

function getJSON(url) {
    var [responseText, status] = readTextFile(url)
    return [status === 200 ? JSON.parse(responseText) : {}, status]
}

function drawData(target, thingData, appendToAppending) {
    //console.log(thingData)
    var whatAppend, div, button, bar, barDiv, header, text, table, row, rowIndex, cell, cellIndex, input
    switch (thingData["type"]) {
        case "header":
            header = document.createElement(thingData["tag"])
            header.innerHTML = thingData["text"]
            whatAppend = header
            break
        case "progressBar":
            bar = document.createElement("div")
            bar.className = "w3-light-grey"
            bar.style.width = thingData["width"] + "px"
            barDiv = document.createElement("div")
            barDiv.className = "w3-blue"
            barDiv.style.height = "24px"
            barDiv.style.width = thingData["progress"] + "%"
            bar.appendChild(barDiv)
            // '<div class="w3-light-grey"><div class="w3-blue" style="height:24px;width:' + thingData["progress + '%"></div></div>'
            whatAppend = bar
            break
        case "text":
            text = document.createTextNode(thingData["text"])
            whatAppend = text
            break
        case "table":
            table = document.createElement("table")
            table.style.border = "1px solid black"
            for (rowIndex = 0; rowIndex < thingData["HTML"].length; rowIndex++) {
                row = document.createElement("tr")
                for (cellIndex = 0; cellIndex < thingData["HTML"][0].length; cellIndex++) {
                    cell = document.createElement("td")
                    //var cellInner = drawData("", thingData["HTML[rowIndex][cellIndex], true)
                    /*if (thingData["HTML[rowIndex][cellIndex].type === "progressBar"){

                    }*/
                    cell.appendChild(drawData("", thingData["HTML"][rowIndex][cellIndex], true))
                    cell.style.border = "1px solid black"
                    row.appendChild(cell)
                }
                table.appendChild(row)
            }
            if (thingData["fullWidth"] === "true") {
                table.style.width = window.innerWidth - 15 + "px"
            }
            whatAppend = table
            break
        case "sendData":
            div = document.createElement("div")
            button = document.createElement("button")
            button.innerHTML = thingData.buttonText
            button.onclick = function () {
                send(thingData.data)
            }
            div.appendChild(button)

            whatAppend = div
            break
        case "sendDataWithInput":
            div = document.createElement("div")
            input = document.createElement("input")
            input.placeholder = thingData.placeholder
            input.size = thingData.size
            input.id = thingData.id
            button = document.createElement("button")
            button.innerHTML = thingData.buttonText
            button.onclick = function () {
                send(thingData.firstPart + document.getElementById(thingData.id).value)
            }
            div.appendChild(input)
            div.appendChild(button)

            whatAppend = div
            break
    }
    if (appendToAppending) {
        return whatAppend
    } else {
        target.appendChild(whatAppend)
    }
}

function send(text, onSend) {
    /*//console.log("Sending text: ", text)
    //document.location.href = "/console/send?text=" + text
    var ifr = document.createElement("iframe")
    ifr.src = "/console/send?text=" + text
    document.getElementById("iframe").innerHTML = ""
    document.getElementById("iframe").appendChild(ifr)
    stopLoop = true
    canSend = false
    document.getElementById("iframe").onload = () => {
        canSend = true
        stopLoop = false
    }
    reloadPage()*/
    var ifr = document.createElement("iframe")
    ifr.src = "/console/send?text=" + text
    typeof onSend === "function" && (ifr.onload = () => {
        iframesDiv.removeChild(ifr)
        text.search(readedString) === 0 ? onSend(text.slice(readedString.length)) : onSend()
    })
    iframesDiv.appendChild(ifr)
}

function onReceive(text) {
    console.log("Received text: ", text)
}

var errors = []

function newError(code, message) {
    errors.push({code, message})
    throwError(errors[errors.length - 1])
}

function throwError(error) {
    document.getElementById("errors").innerHTML += `<span class="error"><h1>Error</h1>ErrorCode: ${error.code}, ErrorMessage: ${error.message}</span><br>`
}
