import QtQuick 2.9
import QtQuick.Controls 2.2
import QtQuick.Layouts 1.3
import MuseScore 3.0

MuseScore {
    id: plugin
    version: "1.1.0"
    description: "Use natural language to describe arrangement changes to your score"
    menuPath: "Plugins.LLM Arranger"
    pluginType: "dialog"
    requiresScore: false

    width: 620
    height: 520

    // Provider configurations
    property var providers: [
        { name: "Claude (Anthropic)", endpoint: "https://api.anthropic.com/v1/messages", model: "claude-sonnet-4-20250514", needsKey: true },
        { name: "Gemini (Google)", endpoint: "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", model: "gemini-2.0-flash", needsKey: true },
        { name: "OpenAI", endpoint: "https://api.openai.com/v1/chat/completions", model: "gpt-4o", needsKey: true },
        { name: "Ollama (Local)", endpoint: "http://localhost:11434/api/generate", model: "llama3", needsKey: false }
    ]

    property int currentProvider: 0
    property string apiKey: ""
    property string customModel: ""
    property bool isProcessing: false
    property var pendingActions: []

    function getProvider() { return providers[currentProvider] }
    function getModel() { return customModel.length > 0 ? customModel : getProvider().model }
    function getEndpoint() {
        var ep = getProvider().endpoint
        if (currentProvider === 1) { ep = ep.replace("{model}", getModel()) + "?key=" + apiKey }
        return ep
    }

    Rectangle {
        anchors.fill: parent
        color: "#f0f0f0"

        Column {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 8

            // Title
            Text {
                text: "LLM Music Arranger"
                font.pixelSize: 18
                font.bold: true
                anchors.horizontalCenter: parent.horizontalCenter
            }

            // Provider selection box
            Rectangle {
                width: parent.width
                height: 90
                color: "#e0f0e0"
                border.color: "#4CAF50"
                radius: 4

                Column {
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 6

                    Row {
                        spacing: 8
                        Text { text: "Provider:"; font.pixelSize: 12; anchors.verticalCenter: parent.verticalCenter }
                        ComboBox {
                            id: providerCombo
                            width: 160
                            model: ["Claude (Anthropic)", "Gemini (Google)", "OpenAI", "Ollama (Local)"]
                            currentIndex: currentProvider
                            onCurrentIndexChanged: {
                                currentProvider = currentIndex
                                modelInput.text = getProvider().model
                            }
                        }
                        Text { text: "Model:"; font.pixelSize: 12; anchors.verticalCenter: parent.verticalCenter }
                        TextField {
                            id: modelInput
                            width: 150
                            text: getProvider().model
                            font.pixelSize: 11
                            onTextChanged: customModel = text
                        }
                    }

                    Row {
                        spacing: 8
                        visible: getProvider().needsKey
                        Text { text: "API Key:"; font.pixelSize: 12; font.bold: true; anchors.verticalCenter: parent.verticalCenter }
                        TextField {
                            id: apiKeyInput
                            width: 400
                            echoMode: TextInput.Password
                            placeholderText: currentProvider === 0 ? "sk-ant-..." : currentProvider === 1 ? "AIza..." : "sk-..."
                            onTextChanged: apiKey = text
                        }
                        Button {
                            text: "Show"
                            width: 50
                            onClicked: apiKeyInput.echoMode = apiKeyInput.echoMode === TextInput.Password ? TextInput.Normal : TextInput.Password
                        }
                    }
                }
            }

            // Request input
            Rectangle {
                width: parent.width
                height: 140
                color: "white"
                border.color: "#ccc"
                radius: 4

                Column {
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 4

                    Text { text: "Your Request:"; font.bold: true; font.pixelSize: 12 }

                    TextArea {
                        id: inputText
                        width: parent.width
                        height: 80
                        placeholderText: "Examples:\n- Add harmony to the melody\n- Transpose up a fifth\n- Add jazz chords"
                        wrapMode: TextArea.Wrap
                        font.pixelSize: 12
                    }

                    Row {
                        spacing: 4
                        Button { text: "Harmonize"; font.pixelSize: 9; onClicked: inputText.text = "Add harmony voices to the melody" }
                        Button { text: "Add Drums"; font.pixelSize: 9; onClicked: inputText.text = "Add a drum part with rock beat" }
                        Button { text: "Transpose"; font.pixelSize: 9; onClicked: inputText.text = "Transpose up by a perfect fifth" }
                        Button { text: "Jazz"; font.pixelSize: 9; onClicked: inputText.text = "Transform to jazz style with swing" }
                    }
                }
            }

            // Response area
            Rectangle {
                width: parent.width
                height: 140
                color: "white"
                border.color: "#ccc"
                radius: 4

                Column {
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 4

                    Text { text: "Response:"; font.bold: true; font.pixelSize: 12 }

                    Flickable {
                        width: parent.width
                        height: 110
                        contentHeight: responseText.implicitHeight
                        clip: true

                        TextArea {
                            id: responseText
                            width: parent.width
                            readOnly: true
                            wrapMode: TextArea.Wrap
                            font.pixelSize: 11
                            text: "Ready. Select a provider, enter your API key, and describe your request."
                        }
                    }
                }
            }

            // Progress bar
            Rectangle {
                width: parent.width
                height: 4
                color: "#ddd"
                visible: isProcessing
                Rectangle {
                    id: progress
                    width: parent.width * 0.3
                    height: parent.height
                    color: "#4CAF50"
                    SequentialAnimation on x {
                        running: isProcessing
                        loops: Animation.Infinite
                        NumberAnimation { from: 0; to: progress.parent.width * 0.7; duration: 800 }
                        NumberAnimation { from: progress.parent.width * 0.7; to: 0; duration: 800 }
                    }
                }
            }

            // Buttons
            Row {
                spacing: 10
                anchors.horizontalCenter: parent.horizontalCenter

                Button {
                    text: "Analyze Score"
                    onClicked: analyzeCurrentScore()
                    enabled: !isProcessing
                }
                Button {
                    text: "Apply Changes"
                    highlighted: true
                    enabled: !isProcessing && inputText.text.length > 0
                    onClicked: processRequest()
                }
                Button {
                    text: "Close"
                    onClicked: Qt.quit()
                }
            }
        }
    }

    function analyzeCurrentScore() {
        if (!curScore) {
            responseText.text = "No score open. Please open a score in MuseScore first."
            return
        }
        responseText.text = "Score Analysis:\n" + getScoreAnalysis()
    }

    function getScoreAnalysis() {
        var score = curScore
        var info = []
        info.push("Title: " + (score.title || "Untitled"))
        info.push("Parts: " + score.nstaves)
        info.push("Measures: " + score.nmeasures)
        try {
            var cursor = score.newCursor()
            cursor.rewind(0)
            if (cursor.keySignature !== undefined) {
                var keyNames = {"-7":"Cb","-6":"Gb","-5":"Db","-4":"Ab","-3":"Eb","-2":"Bb","-1":"F","0":"C","1":"G","2":"D","3":"A","4":"E","5":"B","6":"F#","7":"C#"}
                info.push("Key: " + (keyNames[String(cursor.keySignature)] || "?") + " Major")
            }
            if (cursor.timeSignature) {
                info.push("Time: " + cursor.timeSignature.numerator + "/" + cursor.timeSignature.denominator)
            }
        } catch(e) {}
        return info.join("\n")
    }

    function processRequest() {
        if (!inputText.text.trim()) {
            responseText.text = "Please enter a request."
            return
        }
        if (getProvider().needsKey && (!apiKey || apiKey.length < 5)) {
            responseText.text = "Please enter your API key for " + getProvider().name
            return
        }

        isProcessing = true
        responseText.text = "Sending to " + getProvider().name + "..."

        var scoreContext = curScore ? getScoreAnalysis() : "No score open"
        var prompt = buildPrompt(inputText.text, scoreContext)
        sendToLLM(prompt)
    }

    function buildPrompt(userRequest, scoreContext) {
        var p = "You are a music arrangement assistant for MuseScore.\n\n"
        p += "Score Info:\n" + scoreContext + "\n\n"
        p += "User Request: " + userRequest + "\n\n"
        p += "Respond with JSON:\n"
        p += '{"understanding":"...","actions":[{"type":"action_type","params":{}}],"explanation":"..."}\n\n'
        p += "Actions: transpose{semitones}, add_dynamics{type,measure}, add_tempo{bpm,text}, add_instrument{name}, harmonize{description}, change_style{style}\n"
        p += "Respond ONLY with valid JSON."
        return p
    }

    function sendToLLM(prompt) {
        var xhr = new XMLHttpRequest()
        var endpoint = getEndpoint()
        var model = getModel()
        var body

        if (currentProvider === 0) { // Claude
            body = JSON.stringify({ model: model, max_tokens: 4096, messages: [{ role: "user", content: prompt }] })
        } else if (currentProvider === 1) { // Gemini
            body = JSON.stringify({ contents: [{ parts: [{ text: prompt }] }], generationConfig: { temperature: 0.7, maxOutputTokens: 4096 } })
        } else if (currentProvider === 2) { // OpenAI
            body = JSON.stringify({ model: model, messages: [{ role: "user", content: prompt }], temperature: 0.7, max_tokens: 4096 })
        } else { // Ollama
            body = JSON.stringify({ model: model, prompt: prompt, stream: false })
        }

        xhr.onreadystatechange = function() {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                isProcessing = false
                if (xhr.status === 200) {
                    try {
                        var resp = JSON.parse(xhr.responseText)
                        var content = ""
                        if (currentProvider === 0 && resp.content) content = resp.content[0].text
                        else if (currentProvider === 1 && resp.candidates) content = resp.candidates[0].content.parts[0].text
                        else if (currentProvider === 2 && resp.choices) content = resp.choices[0].message.content
                        else if (resp.response) content = resp.response

                        if (content) processLLMResponse(content)
                        else responseText.text = "Empty response.\n" + xhr.responseText.substring(0,300)
                    } catch(e) {
                        responseText.text = "Parse error: " + e.message + "\n" + xhr.responseText.substring(0,300)
                    }
                } else if (xhr.status === 401) {
                    responseText.text = "Auth error (401). Check your API key."
                } else if (xhr.status === 0) {
                    responseText.text = "Connection failed. Check internet/API endpoint."
                } else {
                    responseText.text = "Error " + xhr.status + ": " + xhr.responseText.substring(0,300)
                }
            }
        }

        try {
            xhr.open("POST", endpoint)
            xhr.setRequestHeader("Content-Type", "application/json")
            if (currentProvider === 0) {
                xhr.setRequestHeader("x-api-key", apiKey)
                xhr.setRequestHeader("anthropic-version", "2023-06-01")
            } else if (currentProvider === 2) {
                xhr.setRequestHeader("Authorization", "Bearer " + apiKey)
            }
            xhr.send(body)
        } catch(e) {
            isProcessing = false
            responseText.text = "Request error: " + e.message
        }
    }

    function processLLMResponse(content) {
        try {
            var start = content.indexOf("{")
            var end = content.lastIndexOf("}") + 1
            if (start === -1 || end <= start) {
                responseText.text = "Response:\n" + content
                return
            }
            var parsed = JSON.parse(content.substring(start, end))
            var txt = "Understanding: " + (parsed.understanding || "N/A") + "\n\n"
            txt += "Explanation: " + (parsed.explanation || "N/A") + "\n\n"
            if (parsed.actions && parsed.actions.length > 0) {
                txt += "Actions:\n"
                for (var i = 0; i < parsed.actions.length; i++) {
                    txt += "- " + parsed.actions[i].type + ": " + JSON.stringify(parsed.actions[i].params || {}) + "\n"
                }
                pendingActions = parsed.actions
                if (curScore) executeActions()
            }
            responseText.text = txt
        } catch(e) {
            responseText.text = "JSON error: " + e.message + "\n\n" + content.substring(0,400)
        }
    }

    function executeActions() {
        if (!curScore || !pendingActions) return
        curScore.startCmd()
        for (var i = 0; i < pendingActions.length; i++) {
            var a = pendingActions[i]
            var p = a.params || {}
            if (a.type === "transpose" && p.semitones) {
                cmd("select-all")
                var dir = p.semitones > 0 ? "transpose-up" : "transpose-down"
                for (var j = 0; j < Math.abs(p.semitones); j++) cmd(dir)
            } else if (a.type === "add_dynamics") {
                try {
                    var cursor = curScore.newCursor()
                    cursor.rewind(0)
                    var dyn = newElement(Element.DYNAMIC)
                    dyn.text = p.type || "mf"
                    cursor.add(dyn)
                } catch(e) {}
            } else if (a.type === "add_tempo") {
                try {
                    var cursor2 = curScore.newCursor()
                    cursor2.rewind(0)
                    var tempo = newElement(Element.TEMPO_TEXT)
                    tempo.text = (p.text || "") + " = " + (p.bpm || 120)
                    tempo.tempo = (p.bpm || 120) / 60.0
                    cursor2.add(tempo)
                } catch(e) {}
            }
        }
        curScore.endCmd()
        pendingActions = []
        responseText.text += "\n\nActions applied."
    }
}
