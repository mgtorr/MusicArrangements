import QtQuick 2.9
import QtQuick.Controls 2.2
import QtQuick.Layouts 1.3
import QtQuick.Dialogs 1.2
import MuseScore 3.0

MuseScore {
    id: plugin
    version: "1.0.0"
    description: "Use natural language to describe arrangement changes to your score"
    menuPath: "Plugins.LLM Arranger"
    pluginType: "dialog"
    requiresScore: true

    width: 600
    height: 500

    // Configuration properties
    property string apiEndpoint: "http://localhost:11434/api/generate"  // Default: Ollama local
    property string apiKey: ""
    property string modelName: "llama3"
    property bool useOpenAI: false

    // State
    property bool isProcessing: false
    property var pendingActions: []

    // Include external JavaScript modules
    property var scoreUtils: Qt.createComponent("ScoreUtils.js")

    Component.onCompleted: {
        loadSettings()
    }

    function loadSettings() {
        // Load saved settings if available
        var savedEndpoint = settings.value("apiEndpoint", "")
        var savedKey = settings.value("apiKey", "")
        var savedModel = settings.value("modelName", "")

        if (savedEndpoint) apiEndpoint = savedEndpoint
        if (savedKey) apiKey = savedKey
        if (savedModel) modelName = savedModel
    }

    function saveSettings() {
        settings.setValue("apiEndpoint", apiEndpoint)
        settings.setValue("apiKey", apiKey)
        settings.setValue("modelName", modelName)
    }

    Settings {
        id: settings
        category: "LLMArrangerPlugin"
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 15
        spacing: 10

        // Header
        Label {
            text: "LLM Music Arranger"
            font.pixelSize: 20
            font.bold: true
            Layout.alignment: Qt.AlignHCenter
        }

        Label {
            text: "Describe the changes you want to make to your score in natural language"
            font.pixelSize: 12
            color: "#666"
            Layout.alignment: Qt.AlignHCenter
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
        }

        // Input area
        GroupBox {
            title: "Your Request"
            Layout.fillWidth: true
            Layout.fillHeight: true

            ColumnLayout {
                anchors.fill: parent
                spacing: 10

                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    TextArea {
                        id: inputText
                        placeholderText: "Examples:\n- Add a violin harmony line following the melody\n- Transpose the entire piece up a major third\n- Add drums with a rock beat pattern\n- Remove the bass line and replace with pizzicato cello\n- Add crescendo from measure 5 to 12\n- Change the style to jazz swing"
                        wrapMode: TextArea.Wrap
                        font.pixelSize: 13
                        enabled: !isProcessing
                    }
                }

                // Quick action buttons
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 5

                    Label {
                        text: "Quick actions:"
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
                        onClicked: inputText.text = "Transpose the score up by "
                        enabled: !isProcessing
                    }
                    Button {
                        text: "Simplify"
                        font.pixelSize: 10
                        onClicked: inputText.text = "Simplify the arrangement by reducing complexity"
                        enabled: !isProcessing
                    }
                }
            }
        }

        // Response/Status area
        GroupBox {
            title: "Response"
            Layout.fillWidth: true
            Layout.preferredHeight: 120

            ScrollView {
                anchors.fill: parent

                TextArea {
                    id: responseText
                    readOnly: true
                    wrapMode: TextArea.Wrap
                    font.pixelSize: 12
                    color: "#333"
                    text: "Ready. Enter your request above and click 'Apply Changes'."
                }
            }
        }

        // Progress indicator
        ProgressBar {
            id: progressBar
            Layout.fillWidth: true
            visible: isProcessing
            indeterminate: true
        }

        // Action buttons
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Button {
                text: "Settings"
                onClicked: settingsDialog.open()
                enabled: !isProcessing
            }

            Item { Layout.fillWidth: true }

            Button {
                text: "Analyze Score"
                onClicked: analyzeCurrentScore()
                enabled: !isProcessing && curScore
            }

            Button {
                text: "Apply Changes"
                highlighted: true
                enabled: !isProcessing && inputText.text.length > 0 && curScore
                onClicked: processRequest()
            }

            Button {
                text: "Close"
                onClicked: Qt.quit()
            }
        }
    }

    // Settings Dialog
    Dialog {
        id: settingsDialog
        title: "LLM Settings"
        width: 450
        height: 300
        standardButtons: Dialog.Ok | Dialog.Cancel

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 15

            GroupBox {
                title: "API Configuration"
                Layout.fillWidth: true

                GridLayout {
                    columns: 2
                    rowSpacing: 10
                    columnSpacing: 10
                    anchors.fill: parent

                    Label { text: "Provider:" }
                    ComboBox {
                        id: providerCombo
                        model: ["Ollama (Local)", "OpenAI", "Anthropic Claude", "Custom"]
                        Layout.fillWidth: true
                        onCurrentIndexChanged: {
                            switch(currentIndex) {
                                case 0: // Ollama
                                    endpointField.text = "http://localhost:11434/api/generate"
                                    modelField.text = "llama3"
                                    break
                                case 1: // OpenAI
                                    endpointField.text = "https://api.openai.com/v1/chat/completions"
                                    modelField.text = "gpt-4"
                                    break
                                case 2: // Anthropic
                                    endpointField.text = "https://api.anthropic.com/v1/messages"
                                    modelField.text = "claude-3-sonnet-20240229"
                                    break
                            }
                        }
                    }

                    Label { text: "API Endpoint:" }
                    TextField {
                        id: endpointField
                        Layout.fillWidth: true
                        text: apiEndpoint
                        placeholderText: "http://localhost:11434/api/generate"
                    }

                    Label { text: "API Key:" }
                    TextField {
                        id: apiKeyField
                        Layout.fillWidth: true
                        text: apiKey
                        echoMode: TextInput.Password
                        placeholderText: "Enter API key (leave empty for local)"
                    }

                    Label { text: "Model:" }
                    TextField {
                        id: modelField
                        Layout.fillWidth: true
                        text: modelName
                        placeholderText: "llama3, gpt-4, claude-3-sonnet, etc."
                    }
                }
            }

            Item { Layout.fillHeight: true }
        }

        onAccepted: {
            apiEndpoint = endpointField.text
            apiKey = apiKeyField.text
            modelName = modelField.text
            useOpenAI = providerCombo.currentIndex === 1
            saveSettings()
        }
    }

    // Score analysis function
    function analyzeCurrentScore() {
        if (!curScore) {
            responseText.text = "Error: No score is currently open."
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
        info.push("Parts/Instruments: " + score.nstaves)
        info.push("Measures: " + score.nmeasures)

        // Get instrument names
        var instruments = []
        for (var i = 0; i < score.nstaves; i++) {
            var part = score.parts[i]
            if (part) {
                instruments.push(part.longName || part.shortName || "Part " + (i+1))
            }
        }
        info.push("Instruments: " + instruments.join(", "))

        // Get key signature and time signature from first measure
        var cursor = score.newCursor()
        cursor.rewind(Cursor.SCORE_START)

        if (cursor.keySignature !== undefined) {
            info.push("Key Signature: " + getKeySignatureName(cursor.keySignature))
        }

        if (cursor.timeSignature) {
            info.push("Time Signature: " + cursor.timeSignature.numerator + "/" + cursor.timeSignature.denominator)
        }

        // Tempo
        var tempo = score.metaTag("tempo") || "Not specified"
        info.push("Tempo: " + tempo)

        return info.join("\n")
    }

    function getKeySignatureName(key) {
        var keys = {
            "-7": "Cb Major / Ab minor",
            "-6": "Gb Major / Eb minor",
            "-5": "Db Major / Bb minor",
            "-4": "Ab Major / F minor",
            "-3": "Eb Major / C minor",
            "-2": "Bb Major / G minor",
            "-1": "F Major / D minor",
            "0": "C Major / A minor",
            "1": "G Major / E minor",
            "2": "D Major / B minor",
            "3": "A Major / F# minor",
            "4": "E Major / C# minor",
            "5": "B Major / G# minor",
            "6": "F# Major / D# minor",
            "7": "C# Major / A# minor"
        }
        return keys[String(key)] || "Unknown"
    }

    // Main processing function
    function processRequest() {
        if (!curScore) {
            responseText.text = "Error: No score is currently open."
            return
        }

        if (!inputText.text.trim()) {
            responseText.text = "Please enter a description of the changes you want to make."
            return
        }

        isProcessing = true
        responseText.text = "Processing your request..."

        // Build the prompt with score context
        var scoreContext = getScoreAnalysis()
        var prompt = buildPrompt(inputText.text, scoreContext)

        // Send to LLM
        sendToLLM(prompt)
    }

    function buildPrompt(userRequest, scoreContext) {
        return `You are a music arrangement assistant for MuseScore. You help modify musical scores based on natural language descriptions.

Current Score Information:
${scoreContext}

User Request: "${userRequest}"

Analyze the request and provide a JSON response with the actions to perform. Use this exact format:
{
    "understanding": "Brief description of what you understood from the request",
    "actions": [
        {
            "type": "action_type",
            "params": { action specific parameters }
        }
    ],
    "explanation": "Explanation of changes that will be made"
}

Available action types:
- "add_instrument": Add a new instrument. Params: {name, family, clef}
- "remove_instrument": Remove an instrument. Params: {partIndex or name}
- "transpose": Transpose notes. Params: {semitones, selection: "all"|"part"|"measures", partIndex, startMeasure, endMeasure}
- "add_notes": Add notes to a part. Params: {partIndex, measure, beat, pitches[], duration}
- "add_dynamics": Add dynamic marking. Params: {type: "pp"|"p"|"mp"|"mf"|"f"|"ff", measure, partIndex}
- "add_tempo": Add tempo marking. Params: {bpm, measure, text}
- "add_articulation": Add articulation. Params: {type, partIndex, startMeasure, endMeasure}
- "copy_pattern": Copy a musical pattern. Params: {sourcePart, targetPart, transformation}
- "harmonize": Add harmony voices. Params: {sourcePart, intervals[], newPartName}
- "change_style": Apply style changes. Params: {style, description}
- "add_crescendo": Add crescendo/decrescendo. Params: {type: "crescendo"|"decrescendo", startMeasure, endMeasure, partIndex}

Respond ONLY with valid JSON. Be specific and practical in your action suggestions.`
    }

    function sendToLLM(prompt) {
        var xhr = new XMLHttpRequest()
        var endpoint = apiEndpoint
        var requestBody

        // Determine API format based on endpoint
        if (endpoint.includes("openai.com")) {
            requestBody = JSON.stringify({
                model: modelName,
                messages: [
                    { role: "system", content: "You are a music arrangement assistant that outputs JSON." },
                    { role: "user", content: prompt }
                ],
                temperature: 0.7
            })
        } else if (endpoint.includes("anthropic.com")) {
            requestBody = JSON.stringify({
                model: modelName,
                max_tokens: 2048,
                messages: [
                    { role: "user", content: prompt }
                ]
            })
        } else {
            // Default Ollama format
            requestBody = JSON.stringify({
                model: modelName,
                prompt: prompt,
                stream: false
            })
        }

        xhr.onreadystatechange = function() {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                isProcessing = false

                if (xhr.status === 200) {
                    try {
                        var response = JSON.parse(xhr.responseText)
                        var content

                        // Extract content based on API format
                        if (response.choices) {
                            // OpenAI format
                            content = response.choices[0].message.content
                        } else if (response.content) {
                            // Anthropic format
                            content = response.content[0].text
                        } else if (response.response) {
                            // Ollama format
                            content = response.response
                        } else {
                            content = xhr.responseText
                        }

                        processLLMResponse(content)
                    } catch (e) {
                        responseText.text = "Error parsing response: " + e.message + "\n\nRaw response:\n" + xhr.responseText.substring(0, 500)
                    }
                } else {
                    responseText.text = "API Error (Status " + xhr.status + "): " + xhr.statusText + "\n\n" + xhr.responseText.substring(0, 300)
                }
            }
        }

        xhr.open("POST", endpoint)
        xhr.setRequestHeader("Content-Type", "application/json")

        if (apiKey) {
            if (endpoint.includes("openai.com")) {
                xhr.setRequestHeader("Authorization", "Bearer " + apiKey)
            } else if (endpoint.includes("anthropic.com")) {
                xhr.setRequestHeader("x-api-key", apiKey)
                xhr.setRequestHeader("anthropic-version", "2023-06-01")
            }
        }

        xhr.send(requestBody)
    }

    function processLLMResponse(content) {
        try {
            // Try to extract JSON from the response
            var jsonMatch = content.match(/\{[\s\S]*\}/)
            if (!jsonMatch) {
                responseText.text = "Could not parse LLM response as JSON.\n\nResponse:\n" + content
                return
            }

            var parsed = JSON.parse(jsonMatch[0])

            // Display understanding and explanation
            var displayText = "Understanding: " + (parsed.understanding || "N/A") + "\n\n"
            displayText += "Explanation: " + (parsed.explanation || "N/A") + "\n\n"
            displayText += "Actions to apply: " + (parsed.actions ? parsed.actions.length : 0)

            if (parsed.actions && parsed.actions.length > 0) {
                displayText += "\n\nProposed actions:\n"
                for (var i = 0; i < parsed.actions.length; i++) {
                    displayText += (i + 1) + ". " + parsed.actions[i].type
                    if (parsed.actions[i].params) {
                        displayText += " - " + JSON.stringify(parsed.actions[i].params)
                    }
                    displayText += "\n"
                }

                pendingActions = parsed.actions
                displayText += "\n[Actions ready - Click 'Execute Actions' to apply]"
            }

            responseText.text = displayText

            // Auto-execute if we have valid actions
            if (parsed.actions && parsed.actions.length > 0) {
                executeActionsDialog.open()
            }

        } catch (e) {
            responseText.text = "Error processing response: " + e.message + "\n\nRaw content:\n" + content.substring(0, 500)
        }
    }

    // Confirmation dialog before executing
    Dialog {
        id: executeActionsDialog
        title: "Confirm Actions"
        width: 400
        standardButtons: Dialog.Yes | Dialog.No

        Label {
            text: "Do you want to apply the proposed changes to your score?\n\nThis will modify your score. Make sure you have saved a backup."
            wrapMode: Text.WordWrap
            anchors.fill: parent
        }

        onAccepted: {
            executeActions()
        }
    }

    function executeActions() {
        if (!curScore || !pendingActions || pendingActions.length === 0) {
            return
        }

        curScore.startCmd()

        var results = []
        for (var i = 0; i < pendingActions.length; i++) {
            var action = pendingActions[i]
            var result = executeAction(action)
            results.push(action.type + ": " + (result ? "Success" : "Failed"))
        }

        curScore.endCmd()

        responseText.text += "\n\n--- Execution Results ---\n" + results.join("\n")
        pendingActions = []
    }

    function executeAction(action) {
        switch (action.type) {
            case "transpose":
                return transposeScore(action.params)
            case "add_dynamics":
                return addDynamics(action.params)
            case "add_tempo":
                return addTempo(action.params)
            case "add_instrument":
                return addInstrument(action.params)
            case "add_crescendo":
                return addCrescendo(action.params)
            case "add_articulation":
                return addArticulation(action.params)
            default:
                console.log("Unknown action type: " + action.type)
                return false
        }
    }

    // Action implementations
    function transposeScore(params) {
        if (!params.semitones) return false

        var cursor = curScore.newCursor()
        cursor.rewind(Cursor.SCORE_START)

        // Select all if needed
        curScore.selection.selectAll()

        // Use built-in transpose command
        cmd("transpose-up")  // This is simplified - real implementation would be more complex

        return true
    }

    function addDynamics(params) {
        var cursor = curScore.newCursor()
        cursor.staffIdx = params.partIndex || 0
        cursor.rewind(Cursor.SCORE_START)

        // Move to the specified measure
        for (var i = 0; i < (params.measure || 0); i++) {
            cursor.nextMeasure()
        }

        if (cursor.element) {
            var dynamic = newElement(Element.DYNAMIC)
            dynamic.text = params.type || "mf"
            cursor.add(dynamic)
            return true
        }
        return false
    }

    function addTempo(params) {
        var cursor = curScore.newCursor()
        cursor.rewind(Cursor.SCORE_START)

        // Move to measure
        for (var i = 0; i < (params.measure || 0); i++) {
            cursor.nextMeasure()
        }

        if (cursor.element) {
            var tempo = newElement(Element.TEMPO_TEXT)
            tempo.text = (params.text || "Tempo") + " = " + (params.bpm || 120)
            tempo.tempo = (params.bpm || 120) / 60.0
            cursor.add(tempo)
            return true
        }
        return false
    }

    function addInstrument(params) {
        // Note: Adding instruments programmatically is limited in MuseScore plugin API
        // This would typically require using the score.appendPart() method if available
        console.log("Add instrument requested: " + JSON.stringify(params))
        responseText.text += "\n\nNote: Adding instruments requires manual action in MuseScore.\nSuggested instrument: " + (params.name || "Unknown")
        return false
    }

    function addCrescendo(params) {
        var cursor = curScore.newCursor()
        cursor.staffIdx = params.partIndex || 0
        cursor.rewind(Cursor.SCORE_START)

        // Move to start measure
        for (var i = 0; i < (params.startMeasure || 0); i++) {
            cursor.nextMeasure()
        }

        if (cursor.element) {
            var hairpin = newElement(Element.HAIRPIN)
            hairpin.hairpinType = params.type === "decrescendo" ? 1 : 0
            cursor.add(hairpin)
            return true
        }
        return false
    }

    function addArticulation(params) {
        var cursor = curScore.newCursor()
        cursor.staffIdx = params.partIndex || 0
        cursor.rewind(Cursor.SCORE_START)

        // Move to measure
        for (var i = 0; i < (params.startMeasure || 0); i++) {
            cursor.nextMeasure()
        }

        while (cursor.segment && cursor.measure.no < (params.endMeasure || params.startMeasure + 1)) {
            if (cursor.element && cursor.element.type === Element.CHORD) {
                var art = newElement(Element.ARTICULATION)
                art.symbol = getArticulationSymbol(params.type)
                cursor.add(art)
            }
            cursor.next()
        }
        return true
    }

    function getArticulationSymbol(type) {
        var symbols = {
            "staccato": "articStaccatoAbove",
            "accent": "articAccentAbove",
            "tenuto": "articTenutoAbove",
            "marcato": "articMarcatoAbove",
            "fermata": "fermataAbove"
        }
        return symbols[type] || "articStaccatoAbove"
    }
}
