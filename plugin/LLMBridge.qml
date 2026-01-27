import QtQuick 2.9
import QtQuick.Controls 2.2
import QtWebSockets 1.1
import MuseScore 3.0

MuseScore {
    id: plugin
    version: "2.1.0"
    description: "LLM Bridge - WebSocket client for AI-driven score modifications"
    menuPath: "Plugins.LLM Bridge"
    pluginType: "dialog"
    requiresScore: false

    width: 420
    height: 550

    property string serverHost: "localhost"
    property int serverPort: 8765
    property bool isConnected: false
    property int commandsExecuted: 0
    property var commandQueue: []
    property bool processingCommand: false

    // WebSocket client connection
    WebSocket {
        id: socket
        url: "ws://" + serverHost + ":" + serverPort
        active: false

        onStatusChanged: {
            switch (status) {
                case WebSocket.Connecting:
                    log("Connecting to " + url + "...")
                    statusText.text = "Connecting..."
                    statusText.color = "#FFC107"
                    break
                case WebSocket.Open:
                    isConnected = true
                    statusText.text = "Connected"
                    statusText.color = "#4CAF50"
                    log("Connected to server!")
                    // Send initial score info
                    sendScoreInfo()
                    break
                case WebSocket.Closed:
                    isConnected = false
                    statusText.text = "Disconnected"
                    statusText.color = "#f44336"
                    log("Connection closed")
                    break
                case WebSocket.Error:
                    isConnected = false
                    statusText.text = "Error"
                    statusText.color = "#f44336"
                    log("WebSocket error: " + socket.errorString)
                    break
            }
        }

        onTextMessageReceived: function(message) {
            try {
                var data = JSON.parse(message)
                handleServerMessage(data)
            } catch (e) {
                log("Parse error: " + e.message)
            }
        }
    }

    // Reconnection timer
    Timer {
        id: reconnectTimer
        interval: 3000
        repeat: true
        running: false
        onTriggered: {
            if (!isConnected && socket.status !== WebSocket.Connecting) {
                log("Attempting to reconnect...")
                socket.active = true
            }
        }
    }

    // Heartbeat timer to keep connection alive
    Timer {
        id: heartbeatTimer
        interval: 5000
        repeat: true
        running: isConnected
        onTriggered: {
            if (isConnected) {
                sendMessage({ type: "ping", timestamp: Date.now() })
            }
        }
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
                text: "LLM Bridge (WebSocket)"
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

            // Server configuration
            Row {
                spacing: 8
                width: parent.width

                Text {
                    text: "Host:"
                    color: "#aaa"
                    font.pixelSize: 11
                    anchors.verticalCenter: parent.verticalCenter
                }
                TextField {
                    id: hostField
                    width: 150
                    text: serverHost
                    font.pixelSize: 11
                    color: "white"
                    background: Rectangle { color: "#3d3d3d"; radius: 3 }
                    onTextChanged: serverHost = text
                }
                Text {
                    text: "Port:"
                    color: "#aaa"
                    font.pixelSize: 11
                    anchors.verticalCenter: parent.verticalCenter
                }
                TextField {
                    id: portField
                    width: 60
                    text: serverPort.toString()
                    font.pixelSize: 11
                    color: "white"
                    background: Rectangle { color: "#3d3d3d"; radius: 3 }
                    validator: IntValidator { bottom: 1; top: 65535 }
                    onTextChanged: serverPort = parseInt(text) || 8765
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
                height: 80
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
                    Text {
                        id: scoreDetails
                        text: ""
                        color: "#666"
                        font.pixelSize: 9
                    }
                }
            }

            // Connection buttons
            Row {
                spacing: 10
                width: parent.width

                Button {
                    text: isConnected ? "Disconnect" : "Connect"
                    width: (parent.width - 20) / 3
                    onClicked: {
                        if (isConnected) {
                            disconnect()
                        } else {
                            connect()
                        }
                    }
                }

                Button {
                    text: "Send Score Info"
                    width: (parent.width - 20) / 3
                    enabled: isConnected && curScore
                    onClicked: sendScoreInfo()
                }

                Button {
                    text: reconnectTimer.running ? "Stop Auto" : "Auto Reconnect"
                    width: (parent.width - 20) / 3
                    onClicked: {
                        reconnectTimer.running = !reconnectTimer.running
                        log(reconnectTimer.running ? "Auto-reconnect enabled" : "Auto-reconnect disabled")
                    }
                }
            }

            // Log area
            Rectangle {
                width: parent.width
                height: 160
                color: "#1a1a1a"
                radius: 4

                Column {
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 4

                    Row {
                        width: parent.width
                        Text {
                            text: "Log:"
                            color: "#888"
                            font.pixelSize: 10
                        }
                        Item { width: parent.width - 80; height: 1 }
                        Text {
                            text: "Clear"
                            color: "#666"
                            font.pixelSize: 10
                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: logText.text = ""
                            }
                        }
                    }

                    Flickable {
                        id: logFlickable
                        width: parent.width
                        height: parent.height - 20
                        contentHeight: logText.implicitHeight
                        clip: true

                        Text {
                            id: logText
                            width: parent.width
                            text: "Ready. Click 'Connect' to connect to the server.\n"
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
                    text: "Test: Chord"
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
                onClicked: {
                    if (isConnected) {
                        disconnect()
                    }
                    Qt.quit()
                }
            }
        }
    }

    // === CONNECTION MANAGEMENT ===

    function connect() {
        log("Connecting to ws://" + serverHost + ":" + serverPort + "...")
        socket.url = "ws://" + serverHost + ":" + serverPort
        socket.active = true
    }

    function disconnect() {
        socket.active = false
        isConnected = false
        reconnectTimer.running = false
        statusText.text = "Disconnected"
        statusText.color = "#f44336"
        log("Disconnected")
    }

    function sendMessage(data) {
        if (isConnected && socket.status === WebSocket.Open) {
            socket.sendTextMessage(JSON.stringify(data))
            return true
        }
        return false
    }

    // === MESSAGE HANDLING ===

    function handleServerMessage(data) {
        switch (data.type) {
            case "pong":
                // Heartbeat response, ignore
                break

            case "command":
                // Single command
                queueCommand(data.command)
                break

            case "commands":
                // Batch of commands
                if (data.commands && Array.isArray(data.commands)) {
                    for (var i = 0; i < data.commands.length; i++) {
                        queueCommand(data.commands[i])
                    }
                }
                break

            case "request_score_info":
                sendScoreInfo()
                break

            case "error":
                log("Server error: " + (data.message || "Unknown error"))
                break

            default:
                log("Unknown message type: " + data.type)
        }
    }

    // === COMMAND QUEUE ===

    function queueCommand(cmd) {
        commandQueue.push(cmd)
        processNextCommand()
    }

    function processNextCommand() {
        if (processingCommand || commandQueue.length === 0) {
            return
        }

        processingCommand = true
        var cmd = commandQueue.shift()
        var result = executeCommand(cmd)

        // Send result back to server
        sendMessage({
            type: "result",
            command: cmd.type,
            success: result.success,
            error: result.error || null,
            commandId: cmd.id || null
        })

        processingCommand = false

        // Process next command if any
        if (commandQueue.length > 0) {
            processNextCommand()
        }
    }

    // === SCORE INFO ===

    function sendScoreInfo() {
        if (!curScore) {
            log("No score open")
            sendMessage({ type: "score_info", error: "No score open" })
            return
        }

        var info = {
            type: "score_info",
            title: curScore.scoreName || curScore.title || "Untitled",
            composer: curScore.composer || "",
            measures: curScore.nmeasures,
            staves: curScore.nstaves,
            parts: [],
            timeSignature: null,
            keySignature: 0,
            tempo: 120
        }

        // Get parts info
        for (var i = 0; i < curScore.parts.length; i++) {
            var part = curScore.parts[i]
            info.parts.push({
                name: part.longName || part.shortName || ("Part " + (i + 1)),
                instruments: part.instrumentId || ""
            })
        }

        // Get time signature, key signature, and tempo from first measure
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

            // Try to find tempo
            var segment = curScore.firstSegment(0x200) // SegChordRest
            while (segment) {
                var annotations = segment.annotations
                for (var j = 0; j < annotations.length; j++) {
                    if (annotations[j].type === Element.TEMPO_TEXT) {
                        info.tempo = Math.round(annotations[j].tempo * 60)
                        break
                    }
                }
                if (info.tempo !== 120) break
                segment = segment.next
            }
        } catch (e) {
            log("Error getting score details: " + e.message)
        }

        // Update UI
        var tsStr = info.timeSignature ? (info.timeSignature.numerator + "/" + info.timeSignature.denominator) : "4/4"
        scoreDetails.text = tsStr + " | " + info.tempo + " BPM | Key: " + info.keySignature

        sendMessage(info)
        log("Score info sent: " + info.title)
    }

    // === COMMAND EXECUTION (with undo support) ===

    function executeCommand(cmd) {
        if (!curScore) {
            log("Error: No score open")
            return { success: false, error: "No score open" }
        }

        commandsExecuted++
        counterText.text = commandsExecuted.toString()

        // Start undoable command block
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
                case "add_articulation":
                    result = cmdAddArticulation(cmd)
                    break
                case "add_slur":
                    result = cmdAddSlur(cmd)
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
            log("Error executing " + cmd.type + ": " + e.message)
        }

        // End undoable command block - this makes the action undoable via Ctrl+Z
        curScore.endCmd()

        log(cmd.type + ": " + (result.success ? "OK" : result.error))
        return result
    }

    // === ATOMIC COMMANDS ===

    function cmdAddNote(cmd) {
        var cursor = curScore.newCursor()
        cursor.track = cmd.track || 0
        cursor.rewind(0)

        // Navigate to measure
        var targetMeasure = cmd.measure || 0
        for (var i = 0; i < targetMeasure; i++) {
            if (!cursor.nextMeasure()) {
                return { success: false, error: "Measure " + targetMeasure + " does not exist" }
            }
        }

        // Navigate to beat within measure if specified
        if (cmd.beat !== undefined && cmd.beat > 0) {
            var ticksPerBeat = 480 // Quarter note
            if (cursor.timeSignature) {
                ticksPerBeat = division * 4 / cursor.timeSignature.denominator
            }
            cursor.setTick(cursor.tick + (cmd.beat * ticksPerBeat))
        }

        // Set duration and add note
        cursor.setDuration(cmd.duration || 480, 1)
        cursor.addNote(cmd.pitch, false)

        // Apply velocity if specified
        if (cmd.velocity !== undefined && cursor.element && cursor.element.type === Element.CHORD) {
            var notes = cursor.element.notes
            for (var j = 0; j < notes.length; j++) {
                notes[j].veloOffset = cmd.velocity - 64
            }
        }

        return { success: true }
    }

    function cmdAddChord(cmd) {
        if (!cmd.pitches || cmd.pitches.length === 0) {
            return { success: false, error: "No pitches specified for chord" }
        }

        var cursor = curScore.newCursor()
        cursor.track = cmd.track || 0
        cursor.rewind(0)

        // Navigate to measure
        var targetMeasure = cmd.measure || 0
        for (var i = 0; i < targetMeasure; i++) {
            if (!cursor.nextMeasure()) {
                return { success: false, error: "Measure " + targetMeasure + " does not exist" }
            }
        }

        // Set duration
        cursor.setDuration(cmd.duration || 480, 1)

        // Add first note
        cursor.addNote(cmd.pitches[0], false)

        // Add remaining notes to create chord
        if (cursor.element && cursor.element.type === Element.CHORD) {
            for (var j = 1; j < cmd.pitches.length; j++) {
                cursor.addNote(cmd.pitches[j], true) // true = add to existing chord
            }
        }

        return { success: true }
    }

    function cmdAddRest(cmd) {
        var cursor = curScore.newCursor()
        cursor.track = cmd.track || 0
        cursor.rewind(0)

        // Navigate to measure
        var targetMeasure = cmd.measure || 0
        for (var i = 0; i < targetMeasure; i++) {
            if (!cursor.nextMeasure()) {
                return { success: false, error: "Measure " + targetMeasure + " does not exist" }
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

        // Navigate to measure
        var targetMeasure = cmd.measure || 0
        for (var i = 0; i < targetMeasure; i++) {
            if (!cursor.nextMeasure()) {
                return { success: false, error: "Measure " + targetMeasure + " does not exist" }
            }
        }

        // Find a chord/rest at this position to attach the dynamic
        while (cursor.element === null && cursor.tick < curScore.lastSegment.tick) {
            cursor.next()
        }

        var dynamic = newElement(Element.DYNAMIC)
        dynamic.text = cmd.dynamic || "mf"

        // Set dynamic velocity offset based on dynamic marking
        var velocityMap = {
            "pppp": -48, "ppp": -40, "pp": -32, "p": -24, "mp": -16,
            "mf": 0, "f": 16, "ff": 32, "fff": 40, "ffff": 48,
            "fp": -16, "sfz": 32, "sf": 24, "rf": 16, "rfz": 24
        }
        if (velocityMap[cmd.dynamic] !== undefined) {
            dynamic.velocity = 64 + velocityMap[cmd.dynamic]
        }

        cursor.add(dynamic)
        return { success: true }
    }

    function cmdAddTempo(cmd) {
        var cursor = curScore.newCursor()
        cursor.rewind(0)

        // Navigate to measure
        var targetMeasure = cmd.measure || 0
        for (var i = 0; i < targetMeasure; i++) {
            if (!cursor.nextMeasure()) {
                return { success: false, error: "Measure " + targetMeasure + " does not exist" }
            }
        }

        var tempo = newElement(Element.TEMPO_TEXT)
        var bpm = cmd.bpm || 120

        // Set tempo text
        if (cmd.text) {
            tempo.text = cmd.text
        } else {
            // Create standard tempo marking
            tempo.text = "<sym>metNoteQuarterUp</sym> = " + bpm
        }

        // Set actual tempo (beats per second)
        tempo.tempo = bpm / 60.0
        tempo.followText = true

        cursor.add(tempo)
        return { success: true }
    }

    function cmdAddText(cmd) {
        var cursor = curScore.newCursor()
        cursor.track = cmd.track || 0
        cursor.rewind(0)

        // Navigate to measure
        var targetMeasure = cmd.measure || 0
        for (var i = 0; i < targetMeasure; i++) {
            if (!cursor.nextMeasure()) {
                return { success: false, error: "Measure " + targetMeasure + " does not exist" }
            }
        }

        // Determine text type
        var textType = Element.STAFF_TEXT
        if (cmd.textType === "system") {
            textType = Element.SYSTEM_TEXT
        } else if (cmd.textType === "lyrics") {
            textType = Element.LYRICS
        } else if (cmd.textType === "rehearsal") {
            textType = Element.REHEARSAL_MARK
        }

        var text = newElement(textType)
        text.text = cmd.text || ""

        cursor.add(text)
        return { success: true }
    }

    function cmdAddArticulation(cmd) {
        var cursor = curScore.newCursor()
        cursor.track = cmd.track || 0
        cursor.rewind(0)

        // Navigate to measure
        var targetMeasure = cmd.measure || 0
        for (var i = 0; i < targetMeasure; i++) {
            if (!cursor.nextMeasure()) {
                return { success: false, error: "Measure " + targetMeasure + " does not exist" }
            }
        }

        // Find chord at position
        while (cursor.element === null || cursor.element.type !== Element.CHORD) {
            if (!cursor.next()) {
                return { success: false, error: "No chord found at position" }
            }
        }

        var articulation = newElement(Element.ARTICULATION)

        // Map articulation names to symbols
        var articulationMap = {
            "staccato": "articStaccatoAbove",
            "accent": "articAccentAbove",
            "tenuto": "articTenutoAbove",
            "marcato": "articMarcatoAbove",
            "fermata": "fermataAbove",
            "trill": "ornamentTrill"
        }

        articulation.symbol = articulationMap[cmd.articulation] || "articStaccatoAbove"
        cursor.add(articulation)

        return { success: true }
    }

    function cmdAddSlur(cmd) {
        // Slurs require selection-based approach
        // This is a simplified version
        return { success: false, error: "Slur command requires manual implementation" }
    }

    function cmdTranspose(cmd) {
        var semitones = cmd.semitones || 0
        if (semitones === 0) {
            return { success: true }
        }

        // Use built-in transpose command
        var direction = semitones > 0 ? "transpose-up" : "transpose-down"
        var steps = Math.abs(semitones)

        for (var i = 0; i < steps; i++) {
            cmd(direction)
        }

        return { success: true }
    }

    function cmdDeleteSelection(cmd) {
        if (curScore.selection.elements.length === 0) {
            return { success: false, error: "Nothing selected" }
        }

        cmd("delete")
        return { success: true }
    }

    function cmdSelectRange(cmd) {
        var startMeasure = cmd.startMeasure || 0
        var endMeasure = cmd.endMeasure || startMeasure
        var startTrack = cmd.startTrack || 0
        var endTrack = cmd.endTrack || startTrack

        curScore.selection.selectRange(
            startMeasure * division * 4, // start tick
            (endMeasure + 1) * division * 4, // end tick
            startTrack,
            endTrack + 1
        )

        return { success: true }
    }

    // === LOGGING ===

    function log(msg) {
        var time = new Date().toLocaleTimeString()
        logText.text += "[" + time + "] " + msg + "\n"

        // Auto-scroll to bottom
        logFlickable.contentY = Math.max(0, logText.implicitHeight - logFlickable.height)
    }

    // === SCORE STATE CHANGES ===

    onScoreStateChanged: {
        if (curScore) {
            scoreTitle.text = curScore.scoreName || curScore.title || "Untitled"
            // Auto-send score info when score changes
            if (isConnected) {
                sendScoreInfo()
            }
        } else {
            scoreTitle.text = "No score open"
            scoreDetails.text = ""
        }
    }

    // Cleanup on close
    Component.onDestruction: {
        if (isConnected) {
            disconnect()
        }
    }
}
