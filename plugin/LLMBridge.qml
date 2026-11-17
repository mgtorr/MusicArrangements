import QtQuick 2.9
import QtQuick.Controls 2.2
import MuseScore 3.0

MuseScore {
    id: plugin
    version: "2.1.0"
    description: "LLM Bridge - write notes into the open score from the Python server"
    menuPath: "Plugins.LLM Bridge"
    pluginType: "dialog"
    requiresScore: false

    width: 460
    height: 640

    property string serverUrl: "http://localhost:8766"
    property bool connected: false
    property int commandsExecuted: 0
    property int pollFailures: 0

    Timer {
        id: pollTimer
        interval: 400
        repeat: true
        running: connected
        onTriggered: pollServer()
    }

    Rectangle {
        anchors.fill: parent
        color: "#241c14"

        Column {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 8

            Text {
                text: "LLM Bridge"
                font.pixelSize: 20
                font.bold: true
                color: "#f6f1e6"
            }

            Row {
                spacing: 8
                Text { text: "Status:"; color: "#c8b49a"; font.pixelSize: 12 }
                Text {
                    id: statusText
                    text: "Disconnected"
                    color: "#e07a64"
                    font.pixelSize: 12
                }
            }

            Row {
                spacing: 8
                width: parent.width
                Text {
                    text: "Server:"
                    color: "#c8b49a"
                    font.pixelSize: 11
                    anchors.verticalCenter: parent.verticalCenter
                }
                TextField {
                    id: urlField
                    width: parent.width - 58
                    text: serverUrl
                    font.pixelSize: 11
                    color: "#f6f1e6"
                    background: Rectangle { color: "#3a3128"; radius: 3 }
                    onTextChanged: serverUrl = text
                }
            }

            Rectangle {
                width: parent.width
                height: 58
                color: "#3a3128"
                radius: 4

                Column {
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 2
                    Text { text: "Open score"; color: "#c8b49a"; font.pixelSize: 10 }
                    Text {
                        id: scoreTitle
                        text: "No score open"
                        color: "#f6f1e6"
                        font.pixelSize: 13
                        font.bold: true
                    }
                    Text {
                        id: scoreMeta
                        text: ""
                        color: "#b5a38e"
                        font.pixelSize: 10
                    }
                }
            }

            Text {
                text: "Ask for a change"
                color: "#c8b49a"
                font.pixelSize: 11
            }

            TextField {
                id: requestField
                width: parent.width
                placeholderText: "Add a C major chord at the beginning"
                font.pixelSize: 12
                color: "#f6f1e6"
                background: Rectangle { color: "#3a3128"; radius: 3 }
                onAccepted: sendRequest()
            }

            Button {
                text: "Send"
                width: parent.width
                onClicked: sendRequest()
            }

            Row {
                spacing: 6
                width: parent.width
                Button {
                    text: "Chord"
                    width: (parent.width - 18) / 4
                    font.pixelSize: 10
                    onClicked: useExample("Add a C major chord at the beginning")
                }
                Button {
                    text: "Fifth"
                    width: (parent.width - 18) / 4
                    font.pixelSize: 10
                    onClicked: useExample("Transpose up a perfect fifth")
                }
                Button {
                    text: "Bass"
                    width: (parent.width - 18) / 4
                    font.pixelSize: 10
                    onClicked: useExample("Walking bass G C D G for 4 measures")
                }
                Button {
                    text: "Drums"
                    width: (parent.width - 18) / 4
                    font.pixelSize: 10
                    onClicked: useExample("Rock drums for 4 measures")
                }
            }

            Rectangle {
                width: parent.width
                height: 168
                color: "#1a1612"
                radius: 4

                Flickable {
                    id: logFlick
                    anchors.fill: parent
                    anchors.margins: 8
                    contentHeight: logText.implicitHeight
                    clip: true

                    Text {
                        id: logText
                        width: logFlick.width
                        text: "Connect, then type a request. With no API key, the local theory engine handles chords, bass, drums, tempo, and transpose.\n"
                        color: "#d7e0c8"
                        font.family: "monospace"
                        font.pixelSize: 10
                        wrapMode: Text.Wrap
                        onTextChanged: Qt.callLater(scrollLog)
                    }
                }
            }

            Row {
                spacing: 8
                width: parent.width

                Button {
                    text: connected ? "Disconnect" : "Connect"
                    width: (parent.width - 8) / 2
                    onClicked: connected ? disconnect() : connect()
                }
                Button {
                    text: "Send score"
                    width: (parent.width - 8) / 2
                    enabled: connected && curScore
                    onClicked: sendScoreInfo()
                }
            }

            Row {
                spacing: 6
                width: parent.width
                Button {
                    text: "Test C4"
                    width: (parent.width - 12) / 3
                    enabled: curScore !== null
                    font.pixelSize: 10
                    onClicked: executeBatch([{ type: "add_note", pitch: 60, duration: 480, measure: 0, tick: 0 }])
                }
                Button {
                    text: "Test chord"
                    width: (parent.width - 12) / 3
                    enabled: curScore !== null
                    font.pixelSize: 10
                    onClicked: executeBatch([{ type: "add_chord", pitches: [60, 64, 67], duration: 480, measure: 0, tick: 0 }])
                }
                Button {
                    text: "Close"
                    width: (parent.width - 12) / 3
                    font.pixelSize: 10
                    onClicked: Qt.quit()
                }
            }
        }
    }

    function scrollLog() {
        if (logFlick.contentHeight > logFlick.height)
            logFlick.contentY = logFlick.contentHeight - logFlick.height
    }

    function refreshScore() {
        if (curScore) {
            scoreTitle.text = curScore.title || "Untitled"
            scoreMeta.text = curScore.nmeasures + " bars, " + curScore.nstaves + " staves"
        } else {
            scoreTitle.text = "No score open"
            scoreMeta.text = ""
        }
    }

    function useExample(text) {
        requestField.text = text
        if (connected)
            sendRequest()
        else
            log("Connect, then send. The request is ready.")
    }

    function connect() {
        log("Connecting to " + serverUrl + "...")
        var xhr = new XMLHttpRequest()
        xhr.onreadystatechange = function() {
            if (xhr.readyState !== XMLHttpRequest.DONE)
                return
            if (xhr.status === 200) {
                connected = true
                pollFailures = 0
                statusText.text = "Connected"
                statusText.color = "#7dcea0"
                log("Connected")
                sendScoreInfo()
            } else {
                statusText.text = "Failed"
                statusText.color = "#e07a64"
                log("Connection failed (" + xhr.status + "). Start the server with: python main.py")
            }
        }
        xhr.onerror = function() {
            statusText.text = "Failed"
            statusText.color = "#e07a64"
            log("Could not reach the server. Is python main.py running?")
        }
        xhr.open("GET", serverUrl + "/ping")
        xhr.send()
    }

    function disconnect() {
        connected = false
        statusText.text = "Disconnected"
        statusText.color = "#e07a64"
        log("Disconnected")
    }

    function pollServer() {
        var xhr = new XMLHttpRequest()
        xhr.onreadystatechange = function() {
            if (xhr.readyState !== XMLHttpRequest.DONE)
                return
            if (xhr.status === 200) {
                pollFailures = 0
                try {
                    var response = JSON.parse(xhr.responseText)
                    if (response.commands && response.commands.length > 0)
                        processCommands(response.commands)
                } catch (error) {
                    log("Could not read commands")
                }
            } else if (xhr.status === 0) {
                pollFailures++
                if (pollFailures >= 3)
                    disconnect()
            }
        }
        xhr.open("GET", serverUrl + "/poll")
        xhr.send()
    }

    function processCommands(commands) {
        log("Received " + commands.length + " command(s)")
        var summary = executeBatch(commands)
        var batchIds = []
        var seen = {}
        for (var i = 0; i < commands.length; i++) {
            var id = commands[i].batch_id
            if (id === undefined || id === null || seen[id])
                continue
            seen[id] = true
            batchIds.push(id)
        }
        sendResults(batchIds.length ? batchIds[0] : null, batchIds, summary)
    }

    function sendRequest() {
        var text = requestField.text.trim()
        if (!text)
            return
        if (!connected) {
            log("Connect to the server first.")
            return
        }
        log("You: " + text)
        var xhr = new XMLHttpRequest()
        xhr.onreadystatechange = function() {
            if (xhr.readyState !== XMLHttpRequest.DONE)
                return
            if (xhr.status !== 200) {
                log("Request failed (" + xhr.status + ")")
                return
            }
            try {
                var response = JSON.parse(xhr.responseText)
                if (response.intent)
                    log(response.intent)
                if (response.notes)
                    log(response.notes)
                if (response.errors && response.errors.length)
                    log(response.errors.join("; "))
                else
                    log("Queued " + (response.commands_sent || 0) + " command(s)")
            } catch (error) {
                log("Could not read the server reply")
            }
        }
        xhr.onerror = function() { log("Could not reach the server") }
        xhr.open("POST", serverUrl + "/request")
        xhr.setRequestHeader("Content-Type", "application/json")
        xhr.send(JSON.stringify({ request: text }))
    }

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
        var partCount = curScore.parts ? curScore.parts.length : 0
        for (var i = 0; i < partCount; i++) {
            var part = curScore.parts[i]
            info.parts.push({ name: part.longName || part.shortName || ("Part " + (i + 1)) })
        }
        try {
            var cursor = curScore.newCursor()
            cursor.rewind(0)
            if (cursor.timeSignature) {
                info.timeSignature = {
                    numerator: cursor.timeSignature.numerator,
                    denominator: cursor.timeSignature.denominator
                }
            }
            if (cursor.keySignature !== undefined)
                info.keySignature = cursor.keySignature
        } catch (error) {}

        var xhr = new XMLHttpRequest()
        xhr.onreadystatechange = function() {
            if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200)
                log("Score info sent")
        }
        xhr.open("POST", serverUrl + "/score_info")
        xhr.setRequestHeader("Content-Type", "application/json")
        xhr.send(JSON.stringify(info))
    }

    function sendResults(batchId, batchIds, summary) {
        var xhr = new XMLHttpRequest()
        xhr.open("POST", serverUrl + "/results")
        xhr.setRequestHeader("Content-Type", "application/json")
        xhr.send(JSON.stringify({
            batch_id: batchId,
            batch_ids: batchIds,
            executed: summary.ok,
            failed: summary.failed,
            errors: summary.errors
        }))
    }

    // A quarter note is 480 ticks. setDuration wants a fraction of a whole note.
    function ticksToFraction(ticks) {
        var known = {
            "1920": [1, 1],
            "1440": [3, 4],
            "960": [1, 2],
            "720": [3, 8],
            "640": [1, 3],
            "480": [1, 4],
            "360": [3, 16],
            "320": [1, 6],
            "240": [1, 8],
            "180": [3, 32],
            "160": [1, 12],
            "120": [1, 16],
            "80": [1, 24],
            "60": [1, 32]
        }
        var key = String(ticks)
        if (known[key])
            return known[key]
        var numerator = Math.abs(ticks) || 480
        var denominator = 1920
        var divisor = gcd(numerator, denominator)
        return [numerator / divisor, denominator / divisor]
    }

    function gcd(a, b) {
        a = Math.abs(a)
        b = Math.abs(b)
        while (b) {
            var next = b
            b = a % b
            a = next
        }
        return a || 1
    }

    function gotoMeasure(measure, track) {
        var cursor = curScore.newCursor()
        cursor.track = track || 0
        cursor.rewind(0)
        for (var i = 0; i < (measure || 0); i++) {
            if (!cursor.nextMeasure())
                return null
        }
        return cursor
    }

    function fillGap(cursor, ticks) {
        var sizes = [1920, 1440, 960, 720, 640, 480, 360, 320, 240, 180, 160, 120, 80, 60]
        var left = ticks
        var guard = 0
        while (left > 0 && guard < 64) {
            var slice = 0
            for (var i = 0; i < sizes.length; i++) {
                if (sizes[i] <= left) {
                    slice = sizes[i]
                    break
                }
            }
            if (slice <= 0)
                break
            var fraction = ticksToFraction(slice)
            cursor.setDuration(fraction[0], fraction[1])
            cursor.addRest()
            left -= slice
            guard++
        }
        return ticks - left
    }

    function addPitches(cursor, pitches) {
        if (!pitches || pitches.length === 0)
            throw new Error("Chord has no pitches")
        cursor.addNote(pitches[0])
        for (var i = 1; i < pitches.length; i++)
            cursor.addNote(pitches[i], true)
    }

    function writeEvent(writers, command) {
        var track = command.track || 0
        var measure = command.measure || 0
        var hasTick = command.tick !== undefined && command.tick !== null
        var tick = hasTick ? command.tick : 0
        var writer = writers[track]

        if (!writer || writer.measure !== measure) {
            var cursor = gotoMeasure(measure, track)
            if (!cursor)
                return { success: false, error: "Bar " + (measure + 1) + " is not in the score" }
            writer = { cursor: cursor, measure: measure, tick: 0 }
            writers[track] = writer
        }

        if (hasTick && tick < writer.tick) {
            var rewound = gotoMeasure(measure, track)
            if (!rewound)
                return { success: false, error: "Bar " + (measure + 1) + " is not in the score" }
            writer.cursor = rewound
            writer.tick = 0
        }

        if (hasTick && tick > writer.tick) {
            var filled = fillGap(writer.cursor, tick - writer.tick)
            writer.tick += filled
            if (writer.tick < tick)
                return { success: false, error: "Could not reach beat position " + tick }
        }

        var duration = command.duration || 480
        var fraction = ticksToFraction(duration)
        writer.cursor.setDuration(fraction[0], fraction[1])

        if (command.type === "add_rest") {
            writer.cursor.addRest()
        } else if (command.type === "add_chord") {
            addPitches(writer.cursor, command.pitches)
        } else {
            if (command.pitch === undefined || command.pitch === null)
                return { success: false, error: "Note is missing a pitch" }
            writer.cursor.addNote(command.pitch)
        }
        writer.tick += duration
        return { success: true }
    }

    function cmdTranspose(command) {
        var semitones = command.semitones || 0
        var changed = 0
        var skipped = 0
        var staves = curScore.nstaves || 1
        for (var staff = 0; staff < staves; staff++) {
            for (var voice = 0; voice < 4; voice++) {
                var cursor = curScore.newCursor()
                cursor.track = staff * 4 + voice
                cursor.rewind(0)
                var guard = 0
                while (cursor.segment && guard < 100000) {
                    var element = cursor.element
                    if (element && element.type === Element.CHORD && element.notes) {
                        for (var n = 0; n < element.notes.length; n++) {
                            var nextPitch = element.notes[n].pitch + semitones
                            if (nextPitch < 0 || nextPitch > 127) {
                                skipped++
                                continue
                            }
                            element.notes[n].pitch = nextPitch
                            changed++
                        }
                    }
                    if (!cursor.next())
                        break
                    guard++
                }
            }
        }
        var warning = ""
        if (skipped > 0)
            warning = "Left " + skipped + " note(s) in place because they would leave the MIDI range."
        return { success: true, warning: warning, detail: "Transposed " + changed + " note(s)" }
    }

    function runSimple(command) {
        if (command.type === "transpose")
            return cmdTranspose(command)
        var cursor = gotoMeasure(command.measure || 0, command.track || 0)
        if (!cursor)
            return { success: false, error: "Bar is not in the score" }
        if (command.type === "add_dynamic") {
            var dynamic = newElement(Element.DYNAMIC)
            dynamic.text = command.dynamic || "mf"
            cursor.add(dynamic)
            return { success: true }
        }
        if (command.type === "add_tempo") {
            var tempo = newElement(Element.TEMPO_TEXT)
            var bpm = command.bpm || 120
            tempo.text = command.text || ("q = " + bpm)
            tempo.tempo = bpm / 60.0
            cursor.add(tempo)
            return { success: true }
        }
        if (command.type === "add_text") {
            var elementType = command.textType === "system" ? Element.SYSTEM_TEXT : Element.STAFF_TEXT
            var text = newElement(elementType)
            text.text = command.text || ""
            cursor.add(text)
            return { success: true }
        }
        return { success: false, error: "Unknown command: " + command.type }
    }

    function executeBatch(commands) {
        var summary = { ok: 0, failed: 0, errors: [] }
        if (!curScore) {
            summary.failed = commands.length
            summary.errors.push("No score open")
            log("No score open")
            return summary
        }

        curScore.startCmd()
        try {
            var writers = {}
            for (var i = 0; i < commands.length; i++) {
                var command = commands[i]
                var kind = command.type
                var result = (kind === "add_note" || kind === "add_chord" || kind === "add_rest")
                    ? writeEvent(writers, command)
                    : runSimple(command)
                if (result.success) {
                    summary.ok++
                    if (result.detail)
                        log(result.detail)
                    if (result.warning)
                        log(result.warning)
                    else if (commands.length <= 6)
                        log((kind || "command") + ": ok")
                } else {
                    summary.failed++
                    summary.errors.push(result.error || "Failed")
                    log((kind || "command") + ": " + (result.error || "Failed"))
                }
            }
        } catch (error) {
            summary.failed++
            var message = error.message || String(error)
            summary.errors.push(message)
            log("Error: " + message)
        } finally {
            curScore.endCmd()
        }

        commandsExecuted += summary.ok
        if (connected) {
            statusText.text = "Connected · " + commandsExecuted + " applied"
            statusText.color = "#7dcea0"
        }
        if (commands.length > 6)
            log("Applied " + summary.ok + ", failed " + summary.failed)
        return summary
    }

    function log(msg) {
        var time = new Date().toLocaleTimeString()
        logText.text += "[" + time + "] " + msg + "\n"
    }

    onScoreStateChanged: {
        refreshScore()
        if (connected)
            sendScoreInfo()
    }

    Component.onCompleted: refreshScore()
}
