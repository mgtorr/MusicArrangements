import QtQuick 2.9
import QtQuick.Controls 2.2
import QtWebSockets 1.1
import MuseScore 3.0

MuseScore {
    id: plugin
    version: "2.0.0"
    description: "LLM Bridge - WebSocket listener for AI-driven score modifications"
    menuPath: "Plugins.LLM Bridge"
    pluginType: "dock"
    dockArea: "right"
    requiresScore: false

    width: 300
    height: 400

    property bool connected: false
    property int commandsExecuted: 0

    // WebSocket Server
    WebSocketServer {
        id: server
        port: 8765
        listen: true

        onClientConnected: {
            console.log("Client connected")
            connected = true
            statusText.text = "Connected"
            statusText.color = "#4CAF50"

            webSocket.onTextMessageReceived.connect(function(message) {
                handleMessage(message)
            })
        }

        onErrorStringChanged: {
            console.log("WebSocket error: " + errorString)
            logMessage("Error: " + errorString)
        }
    }

    // Alternative: WebSocket client mode (connects to Python server)
    WebSocket {
        id: clientSocket
        url: "ws://localhost:8766"
        active: false

        onStatusChanged: {
            if (status === WebSocket.Open) {
                connected = true
                statusText.text = "Connected to server"
                statusText.color = "#4CAF50"
                // Send handshake
                sendCommand({ type: "handshake", plugin: "musescore", version: "2.0.0" })
            } else if (status === WebSocket.Closed) {
                connected = false
                statusText.text = "Disconnected"
                statusText.color = "#f44336"
            } else if (status === WebSocket.Error) {
                logMessage("Connection error: " + errorString)
            }
        }

        onTextMessageReceived: {
            handleMessage(message)
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "#2d2d2d"

        Column {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 10

            // Header
            Text {
                text: "LLM Bridge"
                font.pixelSize: 16
                font.bold: true
                color: "white"
            }

            // Status
            Row {
                spacing: 10
                Text { text: "Status:"; color: "#aaa"; font.pixelSize: 12 }
                Text {
                    id: statusText
                    text: "Waiting..."
                    color: "#ff9800"
                    font.pixelSize: 12
                }
            }

            // Port info
            Text {
                text: "WebSocket: ws://localhost:8765"
                color: "#888"
                font.pixelSize: 10
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

            // Score info
            Rectangle {
                width: parent.width
                height: 60
                color: "#3d3d3d"
                radius: 4

                Column {
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 4

                    Text {
                        text: "Current Score:"
                        color: "#aaa"
                        font.pixelSize: 10
                    }
                    Text {
                        id: scoreInfo
                        text: curScore ? curScore.title || "Untitled" : "No score open"
                        color: "white"
                        font.pixelSize: 12
                        elide: Text.ElideRight
                        width: parent.width
                    }
                    Text {
                        text: curScore ? (curScore.nmeasures + " measures, " + curScore.nstaves + " staves") : ""
                        color: "#888"
                        font.pixelSize: 10
                    }
                }
            }

            // Connect button
            Button {
                text: connected ? "Disconnect" : "Connect to Server"
                width: parent.width
                onClicked: {
                    if (connected) {
                        clientSocket.active = false
                    } else {
                        clientSocket.active = true
                    }
                }
            }

            // Log area
            Rectangle {
                width: parent.width
                height: 150
                color: "#1a1a1a"
                radius: 4

                Flickable {
                    anchors.fill: parent
                    anchors.margins: 5
                    contentHeight: logText.implicitHeight
                    clip: true

                    Text {
                        id: logText
                        width: parent.width
                        text: "Ready.\n"
                        color: "#0f0"
                        font.family: "monospace"
                        font.pixelSize: 10
                        wrapMode: Text.Wrap
                    }
                }
            }

            // Manual test button
            Button {
                text: "Test: Add C4 Note"
                width: parent.width
                enabled: curScore !== null
                onClicked: {
                    executeCommand({ type: "add_note", pitch: 60, duration: 480 })
                }
            }
        }
    }

    // Message handler
    function handleMessage(message) {
        try {
            var cmd = JSON.parse(message)
            logMessage("< " + cmd.type)

            if (cmd.type === "ping") {
                sendResponse({ type: "pong", timestamp: Date.now() })
            } else if (cmd.type === "get_score_info") {
                sendScoreInfo()
            } else if (cmd.type === "get_selection") {
                sendSelectionInfo()
            } else if (cmd.type === "execute") {
                // Execute a batch of atomic commands
                var results = []
                for (var i = 0; i < cmd.commands.length; i++) {
                    var result = executeCommand(cmd.commands[i])
                    results.push(result)
                }
                sendResponse({ type: "execute_result", success: true, results: results })
            } else {
                // Single command
                var result = executeCommand(cmd)
                sendResponse({ type: "command_result", success: result.success, data: result })
            }
        } catch (e) {
            logMessage("Error: " + e.message)
            sendResponse({ type: "error", message: e.message })
        }
    }

    // Execute atomic command
    function executeCommand(cmd) {
        if (!curScore) {
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
                case "add_rest":
                    result = cmdAddRest(cmd)
                    break
                case "add_chord":
                    result = cmdAddChord(cmd)
                    break
                case "set_cursor":
                    result = cmdSetCursor(cmd)
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
                case "delete_selection":
                    result = cmdDeleteSelection(cmd)
                    break
                case "select_range":
                    result = cmdSelectRange(cmd)
                    break
                default:
                    result = { success: false, error: "Unknown command: " + cmd.type }
            }
        } catch (e) {
            result = { success: false, error: e.message }
        }

        curScore.endCmd()
        logMessage(cmd.type + ": " + (result.success ? "OK" : result.error))
        return result
    }

    // === ATOMIC COMMANDS ===

    function cmdAddNote(cmd) {
        var cursor = curScore.newCursor()
        cursor.track = cmd.track || 0
        cursor.rewind(0)

        // Move to position
        if (cmd.measure !== undefined) {
            for (var i = 0; i < cmd.measure; i++) {
                cursor.nextMeasure()
            }
        }
        if (cmd.tick !== undefined) {
            cursor.rewindToTick(cmd.tick)
        }

        // Set duration
        cursor.setDuration(cmd.duration || 480, 1)

        // Add note
        cursor.addNote(cmd.pitch)

        return { success: true, tick: cursor.tick }
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

        // Add first note
        cursor.addNote(cmd.pitches[0])

        // Add remaining notes to chord
        if (cursor.element && cursor.element.type === Element.CHORD) {
            for (var i = 1; i < cmd.pitches.length; i++) {
                cursor.addNote(cmd.pitches[i], true)  // true = add to chord
            }
        }

        return { success: true }
    }

    function cmdSetCursor(cmd) {
        // This is mainly for tracking state - actual cursor is per-operation
        return { success: true, measure: cmd.measure, beat: cmd.beat, track: cmd.track }
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

        var textType = Element.STAFF_TEXT
        if (cmd.textType === "system") textType = Element.SYSTEM_TEXT
        else if (cmd.textType === "lyrics") textType = Element.LYRICS

        var text = newElement(textType)
        text.text = cmd.text || ""
        cursor.add(text)

        return { success: true }
    }

    function cmdTranspose(cmd) {
        cmd("select-all")
        var semitones = cmd.semitones || 0
        var direction = semitones > 0 ? "transpose-up" : "transpose-down"
        for (var i = 0; i < Math.abs(semitones); i++) {
            cmd(direction)
        }
        return { success: true }
    }

    function cmdDeleteSelection(cmd) {
        cmd("delete")
        return { success: true }
    }

    function cmdSelectRange(cmd) {
        // Selection is complex in MuseScore - simplified version
        var cursor = curScore.newCursor()
        cursor.rewind(0)
        for (var i = 0; i < (cmd.startMeasure || 0); i++) {
            cursor.nextMeasure()
        }
        // Full selection requires more complex API calls
        return { success: true, note: "Selection is limited in plugin API" }
    }

    // === SCORE INFO ===

    function sendScoreInfo() {
        if (!curScore) {
            sendResponse({ type: "score_info", data: null })
            return
        }

        var info = {
            title: curScore.title || "Untitled",
            composer: curScore.composer || "",
            measures: curScore.nmeasures,
            staves: curScore.nstaves,
            parts: [],
            timeSignature: null,
            keySignature: null,
            tempo: null
        }

        // Get parts info
        for (var i = 0; i < curScore.parts.length; i++) {
            var part = curScore.parts[i]
            info.parts.push({
                name: part.longName || part.shortName || "Part " + (i+1),
                instrument: part.instrumentId || ""
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

        sendResponse({ type: "score_info", data: info })
    }

    function sendSelectionInfo() {
        if (!curScore || !curScore.selection) {
            sendResponse({ type: "selection_info", data: null })
            return
        }

        var sel = curScore.selection
        var info = {
            isRange: sel.isRange,
            startTick: sel.startSegment ? sel.startSegment.tick : 0,
            endTick: sel.endSegment ? sel.endSegment.tick : 0,
            elements: []
        }

        // Get selected elements
        var elements = sel.elements
        for (var i = 0; i < elements.length && i < 100; i++) {
            var el = elements[i]
            info.elements.push({
                type: el.type,
                name: el.name
            })
        }

        sendResponse({ type: "selection_info", data: info })
    }

    // === COMMUNICATION ===

    function sendResponse(obj) {
        var msg = JSON.stringify(obj)
        if (clientSocket.status === WebSocket.Open) {
            clientSocket.sendTextMessage(msg)
        }
        // Server mode would need different handling
    }

    function sendCommand(obj) {
        sendResponse(obj)
    }

    function logMessage(msg) {
        var timestamp = new Date().toLocaleTimeString()
        logText.text += "[" + timestamp + "] " + msg + "\n"
        // Auto-scroll would be nice here
    }

    // Update score info when score changes
    onScoreStateChanged: {
        if (curScore) {
            scoreInfo.text = curScore.title || "Untitled"
        } else {
            scoreInfo.text = "No score open"
        }
    }
}
