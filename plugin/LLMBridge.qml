import QtQuick 2.9
import QtQuick.Controls 2.2
import MuseScore 3.0

MuseScore {
    id: plugin
    version: "2.0.0"
    description: "LLM Bridge - HTTP connection for AI-driven score modifications"
    menuPath: "Plugins.LLM Bridge"
    pluginType: "dialog"
    requiresScore: false

    width: 400
    height: 500

    property string serverUrl: "http://localhost:8766"
    property bool connected: false
    property int commandsExecuted: 0
    property var pendingCommands: []

    // Polling timer
    Timer {
        id: pollTimer
        interval: 1000
        repeat: true
        running: connected
        onTriggered: pollServer()
    }

    Rectangle {
        anchors.fill: parent
        color: "#2d2d2d"

        Column {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 10

            // Header
            Text {
                text: "LLM Bridge"
                font.pixelSize: 18
                font.bold: true
                color: "white"
            }

            // Status row
            Row {
                spacing: 10
                Text { text: "Status:"; color: "#aaa"; font.pixelSize: 12 }
                Text {
                    id: statusText
                    text: "Disconnected"
                    color: "#f44336"
                    font.pixelSize: 12
                }
            }

            // Server URL
            Row {
                spacing: 8
                width: parent.width
                Text { text: "Server:"; color: "#aaa"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter }
                TextField {
                    id: urlField
                    width: parent.width - 60
                    text: serverUrl
                    font.pixelSize: 11
                    color: "white"
                    background: Rectangle { color: "#3d3d3d"; radius: 3 }
                    onTextChanged: serverUrl = text
                }
            }

            // Commands counter
            Row {
                spacing: 10
                Text { text: "Commands executed:"; color: "#aaa"; font.pixelSize: 11 }
                Text {
                    id: counterText
                    text: "0"
                    color: "white"
                    font.pixelSize: 11
                }
            }

            // Score info box
            Rectangle {
                width: parent.width
                height: 70
                color: "#3d3d3d"
                radius: 4

                Column {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 4

                    Text {
                        text: "Current Score:"
                        color: "#aaa"
                        font.pixelSize: 11
                    }
                    Text {
                        id: scoreTitle
                        text: curScore ? (curScore.title || "Untitled") : "No score open"
                        color: "white"
                        font.pixelSize: 13
                        font.bold: true
                    }
                    Text {
                        text: curScore ? (curScore.nmeasures + " measures, " + curScore.nstaves + " staves") : ""
                        color: "#888"
                        font.pixelSize: 10
                    }
                }
            }

            // Buttons row
            Row {
                spacing: 10
                width: parent.width

                Button {
                    text: connected ? "Disconnect" : "Connect"
                    width: (parent.width - 10) / 2
                    onClicked: {
                        if (connected) {
                            disconnect()
                        } else {
                            connect()
                        }
                    }
                }

                Button {
                    text: "Send Score Info"
                    width: (parent.width - 10) / 2
                    enabled: connected && curScore
                    onClicked: sendScoreInfo()
                }
            }

            // Log area
            Rectangle {
                width: parent.width
                height: 180
                color: "#1a1a1a"
                radius: 4

                Column {
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 4

                    Text {
                        text: "Log:"
                        color: "#888"
                        font.pixelSize: 10
                    }

                    Flickable {
                        width: parent.width
                        height: parent.height - 20
                        contentHeight: logText.implicitHeight
                        clip: true

                        Text {
                            id: logText
                            width: parent.width
                            text: "Ready. Click 'Connect' to connect to Python server.\n"
                            color: "#0f0"
                            font.family: "monospace"
                            font.pixelSize: 10
                            wrapMode: Text.Wrap
                        }
                    }
                }
            }

            // Test buttons
            Row {
                spacing: 8
                width: parent.width

                Button {
                    text: "Test: Add C4"
                    width: (parent.width - 16) / 3
                    enabled: curScore !== null
                    font.pixelSize: 10
                    onClicked: executeCommand({ type: "add_note", pitch: 60, duration: 480, measure: 0 })
                }

                Button {
                    text: "Test: Add Chord"
                    width: (parent.width - 16) / 3
                    enabled: curScore !== null
                    font.pixelSize: 10
                    onClicked: executeCommand({ type: "add_chord", pitches: [60, 64, 67], duration: 480, measure: 0 })
                }

                Button {
                    text: "Test: Dynamic"
                    width: (parent.width - 16) / 3
                    enabled: curScore !== null
                    font.pixelSize: 10
                    onClicked: executeCommand({ type: "add_dynamic", dynamic: "ff", measure: 0 })
                }
            }

            Button {
                text: "Close"
                width: parent.width
                onClicked: Qt.quit()
            }
        }
    }

    // === CONNECTION ===

    function connect() {
        log("Connecting to " + serverUrl + "...")
        var xhr = new XMLHttpRequest()
        xhr.onreadystatechange = function() {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                if (xhr.status === 200) {
                    connected = true
                    statusText.text = "Connected"
                    statusText.color = "#4CAF50"
                    log("Connected!")
                    sendScoreInfo()
                } else {
                    log("Connection failed: " + xhr.status)
                    statusText.text = "Failed"
                    statusText.color = "#f44336"
                }
            }
        }
        xhr.open("GET", serverUrl + "/ping")
        xhr.send()
    }

    function disconnect() {
        connected = false
        statusText.text = "Disconnected"
        statusText.color = "#f44336"
        log("Disconnected")
    }

    function pollServer() {
        var xhr = new XMLHttpRequest()
        xhr.onreadystatechange = function() {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                if (xhr.status === 200) {
                    try {
                        var response = JSON.parse(xhr.responseText)
                        if (response.commands && response.commands.length > 0) {
                            processCommands(response.commands)
                        }
                    } catch (e) {
                        // No commands or parse error
                    }
                } else if (xhr.status === 0) {
                    // Connection lost
                    disconnect()
                }
            }
        }
        xhr.open("GET", serverUrl + "/poll")
        xhr.send()
    }

    function processCommands(commands) {
        log("Received " + commands.length + " command(s)")
        for (var i = 0; i < commands.length; i++) {
            executeCommand(commands[i])
        }
        // Send results back
        sendResults()
    }

    // === SCORE INFO ===

    function sendScoreInfo() {
        if (!curScore) {
            log("No score open")
            return
        }

        var info = {
            title: curScore.title || "Untitled",
            composer: curScore.composer || "",
            measures: curScore.nmeasures,
            staves: curScore.nstaves,
            parts: []
        }

        // Get parts
        for (var i = 0; i < curScore.parts.length; i++) {
            var part = curScore.parts[i]
            info.parts.push({
                name: part.longName || part.shortName || "Part " + (i+1)
            })
        }

        // Get time/key signature
        try {
            var cursor = curScore.newCursor()
            cursor.rewind(0)
            if (cursor.timeSignature) {
                info.timeSignature = {
                    numerator: cursor.timeSignature.numerator,
                    denominator: cursor.timeSignature.denominator
                }
            }
            if (cursor.keySignature !== undefined) {
                info.keySignature = cursor.keySignature
            }
        } catch (e) {}

        var xhr = new XMLHttpRequest()
        xhr.onreadystatechange = function() {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                if (xhr.status === 200) {
                    log("Score info sent")
                } else {
                    log("Failed to send score info")
                }
            }
        }
        xhr.open("POST", serverUrl + "/score_info")
        xhr.setRequestHeader("Content-Type", "application/json")
        xhr.send(JSON.stringify(info))
    }

    function sendResults() {
        // Send execution results back to server
        var xhr = new XMLHttpRequest()
        xhr.open("POST", serverUrl + "/results")
        xhr.setRequestHeader("Content-Type", "application/json")
        xhr.send(JSON.stringify({ executed: commandsExecuted }))
    }

    // === COMMAND EXECUTION ===

    function executeCommand(cmd) {
        if (!curScore) {
            log("Error: No score open")
            return { success: false, error: "No score open" }
        }

        commandsExecuted++
        counterText.text = commandsExecuted.toString()

        curScore.startCmd()
        var result = { success: true }

        try {
            switch (cmd.type) {
                case "add_note":
                    result = cmdAddNote(cmd)
                    break
                case "add_chord":
                    result = cmdAddChord(cmd)
                    break
                case "add_rest":
                    result = cmdAddRest(cmd)
                    break
                case "add_dynamic":
                    result = cmdAddDynamic(cmd)
                    break
                case "add_tempo":
                    result = cmdAddTempo(cmd)
                    break
                case "add_text":
                    result = cmdAddText(cmd)
                    break
                case "transpose":
                    result = cmdTranspose(cmd)
                    break
                default:
                    result = { success: false, error: "Unknown command: " + cmd.type }
            }
        } catch (e) {
            result = { success: false, error: e.message }
            log("Error: " + e.message)
        }

        curScore.endCmd()
        log(cmd.type + ": " + (result.success ? "OK" : result.error))
        return result
    }

    // === ATOMIC COMMANDS ===

    function cmdAddNote(cmd) {
        var cursor = curScore.newCursor()
        cursor.track = cmd.track || 0
        cursor.rewind(0)

        if (cmd.measure !== undefined) {
            for (var i = 0; i < cmd.measure; i++) {
                cursor.nextMeasure()
            }
        }

        cursor.setDuration(cmd.duration || 480, 1)
        cursor.addNote(cmd.pitch)

        return { success: true }
    }

    function cmdAddChord(cmd) {
        var cursor = curScore.newCursor()
        cursor.track = cmd.track || 0
        cursor.rewind(0)

        if (cmd.measure !== undefined) {
            for (var i = 0; i < cmd.measure; i++) {
                cursor.nextMeasure()
            }
        }

        cursor.setDuration(cmd.duration || 480, 1)
        cursor.addNote(cmd.pitches[0])

        // Add remaining notes to chord
        if (cursor.element && cursor.element.type === Element.CHORD) {
            for (var i = 1; i < cmd.pitches.length; i++) {
                cursor.addNote(cmd.pitches[i], true)
            }
        }

        return { success: true }
    }

    function cmdAddRest(cmd) {
        var cursor = curScore.newCursor()
        cursor.track = cmd.track || 0
        cursor.rewind(0)

        if (cmd.measure !== undefined) {
            for (var i = 0; i < cmd.measure; i++) {
                cursor.nextMeasure()
            }
        }

        cursor.setDuration(cmd.duration || 480, 1)
        cursor.addRest()

        return { success: true }
    }

    function cmdAddDynamic(cmd) {
        var cursor = curScore.newCursor()
        cursor.track = cmd.track || 0
        cursor.rewind(0)

        if (cmd.measure !== undefined) {
            for (var i = 0; i < cmd.measure; i++) {
                cursor.nextMeasure()
            }
        }

        var dynamic = newElement(Element.DYNAMIC)
        dynamic.text = cmd.dynamic || "mf"
        cursor.add(dynamic)

        return { success: true }
    }

    function cmdAddTempo(cmd) {
        var cursor = curScore.newCursor()
        cursor.rewind(0)

        if (cmd.measure !== undefined) {
            for (var i = 0; i < cmd.measure; i++) {
                cursor.nextMeasure()
            }
        }

        var tempo = newElement(Element.TEMPO_TEXT)
        tempo.text = cmd.text || ("q = " + (cmd.bpm || 120))
        tempo.tempo = (cmd.bpm || 120) / 60.0
        cursor.add(tempo)

        return { success: true }
    }

    function cmdAddText(cmd) {
        var cursor = curScore.newCursor()
        cursor.track = cmd.track || 0
        cursor.rewind(0)

        if (cmd.measure !== undefined) {
            for (var i = 0; i < cmd.measure; i++) {
                cursor.nextMeasure()
            }
        }

        var text = newElement(Element.STAFF_TEXT)
        text.text = cmd.text || ""
        cursor.add(text)

        return { success: true }
    }

    function cmdTranspose(cmd) {
        var semitones = cmd.semitones || 0
        var dir = semitones > 0 ? "transpose-up" : "transpose-down"
        for (var i = 0; i < Math.abs(semitones); i++) {
            cmd(dir)
        }
        return { success: true }
    }

    // === LOGGING ===

    function log(msg) {
        var time = new Date().toLocaleTimeString()
        logText.text += "[" + time + "] " + msg + "\n"
    }

    // Update score info display
    onScoreStateChanged: {
        if (curScore) {
            scoreTitle.text = curScore.title || "Untitled"
        } else {
            scoreTitle.text = "No score open"
        }
    }
}
