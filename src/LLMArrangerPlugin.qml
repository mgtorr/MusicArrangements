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
    height: 580

    // Provider configurations
    property var providers: [
        {
            name: "Claude (Anthropic)",
            endpoint: "https://api.anthropic.com/v1/messages",
            model: "claude-sonnet-4-20250514",
            needsKey: true
        },
        {
            name: "Gemini (Google)",
            endpoint: "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            model: "gemini-1.5-flash",
            needsKey: true
        },
        {
            name: "OpenAI",
            endpoint: "https://api.openai.com/v1/chat/completions",
            model: "gpt-4o",
            needsKey: true
        },
        {
            name: "Ollama (Local)",
            endpoint: "http://localhost:11434/api/generate",
            model: "llama3",
            needsKey: false
        }
    ]

    // Current configuration
    property int currentProvider: 0
    property string apiKey: ""
    property string customModel: ""

    // State
    property bool isProcessing: false
    property var pendingActions: []

    // Get current provider config
    function getProvider() {
        return providers[currentProvider]
    }

    function getModel() {
        return customModel.length > 0 ? customModel : getProvider().model
    }

    function getEndpoint() {
        var endpoint = getProvider().endpoint
        // For Gemini, replace {model} placeholder
        if (currentProvider === 1) {
            endpoint = endpoint.replace("{model}", getModel())
            endpoint += "?key=" + apiKey
        }
        return endpoint
    }

    Rectangle {
        anchors.fill: parent
        color: "#f5f5f5"

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 15
            spacing: 8

            // Header
            Text {
                text: "LLM Music Arranger"
                font.pixelSize: 20
                font.bold: true
                Layout.alignment: Qt.AlignHCenter
                color: "#333"
            }

            Text {
                text: "Describe the changes you want to make to your score in natural language"
                font.pixelSize: 11
                color: "#666"
                Layout.alignment: Qt.AlignHCenter
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
            }

            // Provider selection
            Rectangle {
                Layout.fillWidth: true
                height: providerColumn.implicitHeight + 20
                color: "#e8f4e8"
                border.color: "#4CAF50"
                border.width: 1
                radius: 4

                ColumnLayout {
                    id: providerColumn
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 8

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        Text {
                            text: "Provider:"
                            font.pixelSize: 12
                            font.bold: true
                            color: "#333"
                        }

                        ComboBox {
                            id: providerCombo
                            Layout.preferredWidth: 180
                            model: ["Claude (Anthropic)", "Gemini (Google)", "OpenAI", "Ollama (Local)"]
                            currentIndex: currentProvider
                            font.pixelSize: 11
                            onCurrentIndexChanged: {
                                currentProvider = currentIndex
                                modelField.text = getProvider().model
                            }
                        }

                        Text {
                            text: "Model:"
                            font.pixelSize: 12
                            color: "#333"
                        }

                        TextField {
                            id: modelField
                            Layout.preferredWidth: 160
                            text: getProvider().model
                            font.pixelSize: 11
                            placeholderText: "model name"
                            onTextChanged: customModel = text
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        visible: getProvider().needsKey

                        Text {
                            text: "API Key:"
                            font.pixelSize: 12
                            font.bold: true
                            color: "#333"
                        }

                        TextField {
                            id: apiKeyField
                            Layout.fillWidth: true
                            text: apiKey
                            font.pixelSize: 11
                            echoMode: TextInput.Password
                            placeholderText: currentProvider === 0 ? "sk-ant-..." :
                                           currentProvider === 1 ? "AIza..." :
                                           currentProvider === 2 ? "sk-..." : ""
                            onTextChanged: apiKey = text
                        }

                        Button {
                            text: apiKeyField.echoMode === TextInput.Password ? "Show" : "Hide"
                            font.pixelSize: 10
                            onClicked: {
                                apiKeyField.echoMode = apiKeyField.echoMode === TextInput.Password ?
                                    TextInput.Normal : TextInput.Password
                            }
                        }
                    }
                }
            }

            // Input area
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "white"
                border.color: "#ccc"
                border.width: 1
                radius: 4

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 8

                    Text {
                        text: "Your Request:"
                        font.bold: true
                        font.pixelSize: 12
                        color: "#333"
                    }

                    Flickable {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        contentWidth: width
                        contentHeight: inputText.implicitHeight
                        clip: true

                        TextArea {
                            id: inputText
                            width: parent.width
                            placeholderText: "Examples:\n- Add a violin harmony line\n- Transpose up a major third\n- Add drums with rock beat\n- Add crescendo from measure 5 to 12\n- Change style to jazz swing"
                            wrapMode: TextArea.Wrap
                            font.pixelSize: 13
                            enabled: !isProcessing
                            background: Rectangle { color: "transparent" }
                        }
                    }

                    // Quick action buttons
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 5

                        Text {
                            text: "Quick:"
                            font.pixelSize: 11
                            color: "#888"
                        }

                        Button {
                            text: "Harmonize"
                            font.pixelSize: 10
                            onClicked: inputText.text = "Add harmony voices to the main melody"
                            enabled: !isProcessing
                        }
                        Button {
                            text: "Add Drums"
                            font.pixelSize: 10
                            onClicked: inputText.text = "Add a drum part with an appropriate rhythm pattern"
                            enabled: !isProcessing
                        }
                        Button {
                            text: "Transpose"
                            font.pixelSize: 10
                            onClicked: inputText.text = "Transpose the score up by a perfect fifth"
                            enabled: !isProcessing
                        }
                        Button {
                            text: "Jazz Style"
                            font.pixelSize: 10
                            onClicked: inputText.text = "Transform this piece into jazz style with swing rhythm and extended chords"
                            enabled: !isProcessing
                        }
                    }
                }
            }

            // Response/Status area
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 140
                color: "white"
                border.color: "#ccc"
                border.width: 1
                radius: 4

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 5

                    Text {
                        text: "Response:"
                        font.bold: true
                        font.pixelSize: 12
                        color: "#333"
                    }

                    Flickable {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        contentWidth: width
                        contentHeight: responseText.implicitHeight
                        clip: true

                        TextArea {
                            id: responseText
                            width: parent.width
                            readOnly: true
                            wrapMode: TextArea.Wrap
                            font.pixelSize: 12
                            color: "#333"
                            text: "Ready. Enter your request above and click 'Apply Changes'.\n\nMake sure you have an LLM server running (e.g., Ollama with 'ollama serve')."
                            background: Rectangle { color: "transparent" }
                        }
                    }
                }
            }

            // Progress indicator
            Rectangle {
                Layout.fillWidth: true
                height: 4
                color: "#ddd"
                visible: isProcessing
                radius: 2

                Rectangle {
                    id: progressAnim
                    width: parent.width * 0.3
                    height: parent.height
                    color: "#4CAF50"
                    radius: 2

                    SequentialAnimation on x {
                        running: isProcessing
                        loops: Animation.Infinite
                        NumberAnimation {
                            from: 0
                            to: progressAnim.parent.width * 0.7
                            duration: 1000
                            easing.type: Easing.InOutQuad
                        }
                        NumberAnimation {
                            from: progressAnim.parent.width * 0.7
                            to: 0
                            duration: 1000
                            easing.type: Easing.InOutQuad
                        }
                    }
                }
            }

            // Settings row
            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Text {
                    text: "API:"
                    font.pixelSize: 11
                    color: "#666"
                }

                TextField {
                    id: endpointField
                    Layout.fillWidth: true
                    text: apiEndpoint
                    font.pixelSize: 11
                    placeholderText: "http://localhost:11434/api/generate"
                }

                Text {
                    text: "Model:"
                    font.pixelSize: 11
                    color: "#666"
                }

                TextField {
                    id: modelField
                    Layout.preferredWidth: 100
                    text: modelName
                    font.pixelSize: 11
                    placeholderText: "llama3"
                    onTextChanged: modelName = text
                }
            }

            // Action buttons
            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Button {
                    text: "Analyze Score"
                    onClicked: analyzeCurrentScore()
                    enabled: !isProcessing
                }

                Item { Layout.fillWidth: true }

                Button {
                    text: "Apply Changes"
                    highlighted: true
                    enabled: !isProcessing && inputText.text.length > 0
                    onClicked: {
                        apiEndpoint = endpointField.text
                        processRequest()
                    }
                }

                Button {
                    text: "Close"
                    onClicked: Qt.quit()
                }
            }
        }
    }

    // Score analysis function
    function analyzeCurrentScore() {
        if (!curScore) {
            responseText.text = "Error: No score is currently open.\n\nPlease open a score in MuseScore first."
            return
        }

        var analysis = getScoreAnalysis()
        responseText.text = "Score Analysis:\n" + analysis
    }

    function getScoreAnalysis() {
        var score = curScore
        var info = []

        info.push("Title: " + (score.title || "Untitled"))
        info.push("Composer: " + (score.composer || "Unknown"))
        info.push("Parts/Staves: " + score.nstaves)
        info.push("Measures: " + score.nmeasures)

        // Get instrument names
        var instruments = []
        var numParts = score.parts ? score.parts.length : 0
        for (var i = 0; i < numParts; i++) {
            var part = score.parts[i]
            if (part) {
                var name = part.longName || part.shortName || ("Part " + (i+1))
                instruments.push(name)
            }
        }
        if (instruments.length > 0) {
            info.push("Instruments: " + instruments.join(", "))
        }

        // Get key and time signature from first measure
        try {
            var cursor = score.newCursor()
            cursor.rewind(0)  // Cursor.SCORE_START = 0

            if (cursor.keySignature !== undefined) {
                info.push("Key Signature: " + getKeySignatureName(cursor.keySignature))
            }

            if (cursor.timeSignature) {
                info.push("Time Signature: " + cursor.timeSignature.numerator + "/" + cursor.timeSignature.denominator)
            }
        } catch (e) {
            console.log("Error reading cursor: " + e)
        }

        return info.join("\n")
    }

    function getKeySignatureName(key) {
        var keys = {
            "-7": "Cb Major", "-6": "Gb Major", "-5": "Db Major", "-4": "Ab Major",
            "-3": "Eb Major", "-2": "Bb Major", "-1": "F Major", "0": "C Major",
            "1": "G Major", "2": "D Major", "3": "A Major", "4": "E Major",
            "5": "B Major", "6": "F# Major", "7": "C# Major"
        }
        return keys[String(key)] || ("Key: " + key)
    }

    // Main processing function
    function processRequest() {
        if (!inputText.text.trim()) {
            responseText.text = "Please enter a description of the changes you want to make."
            return
        }

        // Validate API key if required
        if (getProvider().needsKey && (!apiKey || apiKey.length < 10)) {
            responseText.text = "Please enter a valid API key for " + getProvider().name
            return
        }

        isProcessing = true
        responseText.text = "Processing your request...\n\nProvider: " + getProvider().name + "\nModel: " + getModel()

        var scoreContext = "No score open"
        if (curScore) {
            scoreContext = getScoreAnalysis()
        }

        var prompt = buildPrompt(inputText.text, scoreContext)
        sendToLLM(prompt)
    }

    function buildPrompt(userRequest, scoreContext) {
        var promptText = "You are a music arrangement assistant for MuseScore. "
        promptText += "You help modify musical scores based on natural language descriptions.\n\n"
        promptText += "Current Score Information:\n" + scoreContext + "\n\n"
        promptText += "User Request: \"" + userRequest + "\"\n\n"
        promptText += "Analyze the request and provide a JSON response with actions to perform. Use this format:\n"
        promptText += "{\n"
        promptText += "  \"understanding\": \"Brief description of what you understood\",\n"
        promptText += "  \"actions\": [\n"
        promptText += "    { \"type\": \"action_type\", \"params\": { } }\n"
        promptText += "  ],\n"
        promptText += "  \"explanation\": \"Explanation of changes\"\n"
        promptText += "}\n\n"
        promptText += "Available action types:\n"
        promptText += "- transpose: {semitones: number}\n"
        promptText += "- add_dynamics: {type: \"pp\"|\"p\"|\"mp\"|\"mf\"|\"f\"|\"ff\", measure: number}\n"
        promptText += "- add_tempo: {bpm: number, text: string}\n"
        promptText += "- add_instrument: {name: string}\n"
        promptText += "- add_crescendo: {type: \"crescendo\"|\"decrescendo\", startMeasure, endMeasure}\n"
        promptText += "- harmonize: {intervals: [number], description: string}\n"
        promptText += "- change_style: {style: string, description: string}\n\n"
        promptText += "Respond ONLY with valid JSON."

        return promptText
    }

    function sendToLLM(prompt) {
        var xhr = new XMLHttpRequest()
        var endpoint = getEndpoint()
        var model = getModel()
        var requestBody

        // Build request based on provider
        switch (currentProvider) {
            case 0: // Claude (Anthropic)
                requestBody = JSON.stringify({
                    model: model,
                    max_tokens: 4096,
                    messages: [
                        { role: "user", content: prompt }
                    ]
                })
                break

            case 1: // Gemini (Google)
                requestBody = JSON.stringify({
                    contents: [
                        {
                            parts: [
                                { text: prompt }
                            ]
                        }
                    ],
                    generationConfig: {
                        temperature: 0.7,
                        maxOutputTokens: 4096
                    }
                })
                break

            case 2: // OpenAI
                requestBody = JSON.stringify({
                    model: model,
                    messages: [
                        { role: "system", content: "You are a music arrangement assistant. Output JSON." },
                        { role: "user", content: prompt }
                    ],
                    temperature: 0.7,
                    max_tokens: 4096
                })
                break

            case 3: // Ollama (Local)
            default:
                requestBody = JSON.stringify({
                    model: model,
                    prompt: prompt,
                    stream: false
                })
                break
        }

        xhr.onreadystatechange = function() {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                isProcessing = false

                if (xhr.status === 200) {
                    try {
                        var response = JSON.parse(xhr.responseText)
                        var content

                        // Extract content based on provider
                        switch (currentProvider) {
                            case 0: // Claude
                                if (response.content && response.content[0]) {
                                    content = response.content[0].text
                                }
                                break

                            case 1: // Gemini
                                if (response.candidates && response.candidates[0]) {
                                    var candidate = response.candidates[0]
                                    if (candidate.content && candidate.content.parts && candidate.content.parts[0]) {
                                        content = candidate.content.parts[0].text
                                    }
                                }
                                break

                            case 2: // OpenAI
                                if (response.choices && response.choices[0]) {
                                    content = response.choices[0].message.content
                                }
                                break

                            case 3: // Ollama
                            default:
                                content = response.response
                                break
                        }

                        if (content) {
                            processLLMResponse(content)
                        } else {
                            responseText.text = "Empty response from API.\n\nRaw:\n" + xhr.responseText.substring(0, 500)
                        }
                    } catch (e) {
                        responseText.text = "Error parsing response: " + e.message + "\n\nRaw response:\n" + xhr.responseText.substring(0, 500)
                    }
                } else if (xhr.status === 0) {
                    responseText.text = "Connection failed!\n\nCould not connect to API.\n\nCheck your internet connection and API key."
                } else if (xhr.status === 401) {
                    responseText.text = "Authentication failed (401).\n\nPlease check your API key."
                } else if (xhr.status === 429) {
                    responseText.text = "Rate limit exceeded (429).\n\nPlease wait a moment and try again."
                } else {
                    responseText.text = "API Error (Status " + xhr.status + ")\n\n" + xhr.responseText.substring(0, 500)
                }
            }
        }

        xhr.onerror = function() {
            isProcessing = false
            responseText.text = "Network error!\n\nCould not connect to API.\nCheck your internet connection."
        }

        try {
            xhr.open("POST", endpoint)
            xhr.setRequestHeader("Content-Type", "application/json")

            // Set auth headers based on provider
            switch (currentProvider) {
                case 0: // Claude
                    xhr.setRequestHeader("x-api-key", apiKey)
                    xhr.setRequestHeader("anthropic-version", "2023-06-01")
                    break

                case 2: // OpenAI
                    xhr.setRequestHeader("Authorization", "Bearer " + apiKey)
                    break

                // Gemini uses key in URL, Ollama needs no auth
            }

            xhr.send(requestBody)
        } catch (e) {
            isProcessing = false
            responseText.text = "Error sending request: " + e.message
        }
    }

    function processLLMResponse(content) {
        try {
            // Try to extract JSON from the response
            var jsonStart = content.indexOf("{")
            var jsonEnd = content.lastIndexOf("}") + 1

            if (jsonStart === -1 || jsonEnd <= jsonStart) {
                responseText.text = "LLM Response (no JSON found):\n\n" + content
                return
            }

            var jsonStr = content.substring(jsonStart, jsonEnd)
            var parsed = JSON.parse(jsonStr)

            // Display understanding and explanation
            var displayText = "Understanding:\n" + (parsed.understanding || "N/A") + "\n\n"
            displayText += "Explanation:\n" + (parsed.explanation || "N/A") + "\n\n"

            if (parsed.actions && parsed.actions.length > 0) {
                displayText += "Proposed actions (" + parsed.actions.length + "):\n"
                for (var i = 0; i < parsed.actions.length; i++) {
                    var action = parsed.actions[i]
                    displayText += "  " + (i + 1) + ". " + action.type
                    if (action.params) {
                        displayText += ": " + JSON.stringify(action.params)
                    }
                    displayText += "\n"
                }

                pendingActions = parsed.actions
                displayText += "\n[Click 'Execute' below to apply these changes]"
            }

            responseText.text = displayText

            // If we have actions and a score, offer to execute
            if (parsed.actions && parsed.actions.length > 0 && curScore) {
                // Could auto-execute or wait for user confirmation
                executeActions()
            }

        } catch (e) {
            responseText.text = "Error processing response: " + e.message + "\n\nRaw content:\n" + content.substring(0, 500)
        }
    }

    function executeActions() {
        if (!curScore || !pendingActions || pendingActions.length === 0) {
            responseText.text += "\n\nNo score open or no actions to execute."
            return
        }

        curScore.startCmd()

        var results = []
        for (var i = 0; i < pendingActions.length; i++) {
            var action = pendingActions[i]
            var result = executeAction(action)
            results.push(action.type + ": " + (result ? "OK" : "Failed/Manual"))
        }

        curScore.endCmd()

        responseText.text += "\n\n--- Results ---\n" + results.join("\n")
        pendingActions = []
    }

    function executeAction(action) {
        var params = action.params || {}

        switch (action.type) {
            case "transpose":
                return transposeScore(params)
            case "add_dynamics":
                return addDynamics(params)
            case "add_tempo":
                return addTempo(params)
            case "add_instrument":
                responseText.text += "\n\nNote: Add instrument '" + (params.name || "Unknown") + "' manually via Edit > Instruments"
                return false
            case "add_crescendo":
                return addCrescendo(params)
            case "harmonize":
                responseText.text += "\n\nHarmonization suggestion: " + (params.description || JSON.stringify(params))
                return false
            case "change_style":
                responseText.text += "\n\nStyle change suggestion: " + (params.description || params.style || "See above")
                return false
            default:
                console.log("Unknown action: " + action.type)
                return false
        }
    }

    function transposeScore(params) {
        if (!params.semitones) return false

        try {
            cmd("select-all")

            // Transpose by calling the command multiple times
            var semitones = parseInt(params.semitones)
            var direction = semitones > 0 ? "transpose-up" : "transpose-down"
            var count = Math.abs(semitones)

            for (var i = 0; i < count; i++) {
                cmd(direction)
            }

            return true
        } catch (e) {
            console.log("Transpose error: " + e)
            return false
        }
    }

    function addDynamics(params) {
        try {
            var cursor = curScore.newCursor()
            cursor.staffIdx = params.partIndex || 0
            cursor.rewind(0)

            var targetMeasure = (params.measure || 1) - 1
            for (var i = 0; i < targetMeasure && cursor.nextMeasure(); i++) {}

            if (cursor.element) {
                var dynamic = newElement(Element.DYNAMIC)
                dynamic.text = params.type || "mf"
                cursor.add(dynamic)
                return true
            }
        } catch (e) {
            console.log("Add dynamics error: " + e)
        }
        return false
    }

    function addTempo(params) {
        try {
            var cursor = curScore.newCursor()
            cursor.rewind(0)

            var targetMeasure = (params.measure || 1) - 1
            for (var i = 0; i < targetMeasure && cursor.nextMeasure(); i++) {}

            if (cursor.element) {
                var tempo = newElement(Element.TEMPO_TEXT)
                var bpm = params.bpm || 120
                tempo.text = (params.text || "Tempo") + " = " + bpm
                tempo.tempo = bpm / 60.0
                cursor.add(tempo)
                return true
            }
        } catch (e) {
            console.log("Add tempo error: " + e)
        }
        return false
    }

    function addCrescendo(params) {
        try {
            var cursor = curScore.newCursor()
            cursor.staffIdx = params.partIndex || 0
            cursor.rewind(0)

            var startMeasure = (params.startMeasure || 1) - 1
            for (var i = 0; i < startMeasure && cursor.nextMeasure(); i++) {}

            if (cursor.element) {
                var hairpin = newElement(Element.HAIRPIN)
                hairpin.hairpinType = (params.type === "decrescendo") ? 1 : 0
                cursor.add(hairpin)
                return true
            }
        } catch (e) {
            console.log("Add crescendo error: " + e)
        }
        return false
    }
}
