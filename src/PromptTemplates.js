/**
 * PromptTemplates.js - Pre-defined prompts for common musical transformations
 * Part of the LLM Arranger Plugin
 */

.pragma library

/**
 * System prompt for musical arrangement understanding
 */
var SYSTEM_PROMPT = `You are an expert music arranger and composer assistant integrated with MuseScore.
Your role is to analyze musical requests and translate them into specific, actionable modifications
that can be applied to a MuseScore score.

Key Responsibilities:
1. Understand musical terminology and concepts (harmony, counterpoint, orchestration, style)
2. Translate natural language requests into concrete score modifications
3. Suggest musically appropriate changes based on the current score context
4. Consider instrument ranges, musical conventions, and style guidelines

Always respond with specific, executable actions in JSON format.`;

/**
 * Templates for different types of musical transformations
 */
var TRANSFORMATION_TEMPLATES = {

    // Harmony and Voicing
    "harmonize": {
        description: "Add harmony voices to existing melody",
        prompt: `Analyze the melody and create harmony voices. Consider:
- The key and scale of the piece
- Voice leading principles
- Appropriate intervals (3rds, 6ths, etc.)
- Avoiding parallel fifths and octaves where inappropriate
- Range of the target voice/instrument`,
        actions: ["harmonize", "add_notes"]
    },

    "reharmonize": {
        description: "Change the harmonic progression",
        prompt: `Reharmonize the existing chord progression with:
- Jazz substitutions (tritone subs, altered dominants)
- Modal interchange
- Secondary dominants
- Pedal tones
Maintain the melodic integrity while enriching the harmony.`,
        actions: ["modify_chords", "add_notes"]
    },

    // Arrangement and Orchestration
    "orchestrate": {
        description: "Expand to full orchestration",
        prompt: `Create an orchestral arrangement considering:
- Instrument families and their roles (strings, woodwinds, brass, percussion)
- Register and range of each instrument
- Doubling for richness vs. contrast for texture
- Dynamic balance between sections
- Idiomatic writing for each instrument`,
        actions: ["add_instrument", "copy_pattern", "add_notes", "add_dynamics"]
    },

    "reduce": {
        description: "Reduce arrangement to fewer parts",
        prompt: `Reduce the score to fewer parts while preserving:
- Essential melodic content
- Harmonic framework
- Rhythmic character
- Key dynamic moments
Consider piano reduction or small ensemble adaptation.`,
        actions: ["remove_instrument", "merge_parts", "simplify"]
    },

    // Style Transformations
    "jazz_style": {
        description: "Apply jazz style elements",
        prompt: `Transform to jazz style by:
- Adding swing rhythm notation
- Including jazz chord extensions (7ths, 9ths, 13ths)
- Suggesting walking bass patterns
- Adding syncopation
- Including blue notes where appropriate
- Suggesting improvisation sections`,
        actions: ["change_style", "add_articulation", "add_notes", "add_tempo"]
    },

    "classical_style": {
        description: "Apply classical style elements",
        prompt: `Apply classical style conventions:
- Proper voice leading
- Classical phrase structure
- Appropriate ornaments (trills, turns, mordents)
- Dynamic markings following classical conventions
- Articulation appropriate to the period`,
        actions: ["change_style", "add_articulation", "add_dynamics", "add_ornaments"]
    },

    "rock_style": {
        description: "Apply rock/pop style elements",
        prompt: `Transform to rock style by:
- Adding power chords
- Creating driving rhythmic patterns
- Adding drum part with rock beat
- Suggesting guitar-friendly voicings
- Adding bass line following root movement`,
        actions: ["change_style", "add_instrument", "add_notes"]
    },

    "latin_style": {
        description: "Apply Latin style elements",
        prompt: `Apply Latin style elements:
- Characteristic rhythmic patterns (clave, tumbao)
- Syncopation typical of the style
- Appropriate percussion instruments
- Bass patterns (anticipated bass)
- Piano montuno patterns`,
        actions: ["change_style", "add_instrument", "add_notes", "add_articulation"]
    },

    // Texture and Dynamics
    "add_crescendo_section": {
        description: "Build intensity over measures",
        prompt: `Create a crescendo section by:
- Gradually adding instruments
- Increasing dynamic markings
- Thickening texture
- Raising register
- Intensifying rhythmic activity`,
        actions: ["add_crescendo", "add_dynamics", "add_notes"]
    },

    "create_contrast": {
        description: "Create contrast between sections",
        prompt: `Create contrast by varying:
- Dynamics (loud vs soft)
- Texture (thick vs thin)
- Register (high vs low)
- Rhythm (active vs sustained)
- Instrumentation (tutti vs solo)`,
        actions: ["add_dynamics", "change_style", "add_articulation"]
    },

    // Instrument Specific
    "add_bass_line": {
        description: "Add bass line to arrangement",
        prompt: `Create a bass line that:
- Supports the harmonic progression
- Uses appropriate bass patterns for the style
- Interacts with drums/rhythm section
- Fills appropriate register (not too high)
- Uses typical bass techniques (walking, pedal, etc.)`,
        actions: ["add_instrument", "add_notes"]
    },

    "add_drum_part": {
        description: "Add drum/percussion part",
        prompt: `Create a drum part with:
- Style-appropriate patterns
- Fills at phrase endings
- Hi-hat/ride patterns
- Kick and snare placement
- Crash cymbals for accents`,
        actions: ["add_instrument", "add_notes"]
    },

    "add_string_section": {
        description: "Add string section",
        prompt: `Add strings considering:
- Violin 1 (melody/high harmony)
- Violin 2 (inner voice)
- Viola (inner voice, can double)
- Cello (bass/tenor range)
- Optional double bass
- Bowing indications
- Divisi passages`,
        actions: ["add_instrument", "add_notes", "add_articulation"]
    },

    // Technical Modifications
    "transpose": {
        description: "Transpose the score",
        prompt: `Transpose the score by the requested interval.
Consider:
- Key signature change
- Accidentals
- Instrument ranges
- Practical playability`,
        actions: ["transpose"]
    },

    "change_tempo": {
        description: "Modify tempo",
        prompt: `Adjust tempo markings:
- Add tempo text
- Set BPM
- Add accelerando/ritardando where appropriate
- Consider style implications`,
        actions: ["add_tempo"]
    },

    "add_articulations": {
        description: "Add articulation markings",
        prompt: `Add appropriate articulations:
- Staccato for short, detached notes
- Legato/slurs for smooth passages
- Accents for emphasis
- Tenuto for sustained notes
- Style-specific articulations`,
        actions: ["add_articulation"]
    }
};

/**
 * Style-specific guidelines for the LLM
 */
var STYLE_GUIDELINES = {
    "baroque": {
        period: "1600-1750",
        characteristics: [
            "Ornate melodic lines with ornamentation",
            "Basso continuo (figured bass)",
            "Terraced dynamics",
            "Polyphonic textures",
            "Harpsichord/organ as keyboard"
        ],
        instruments: ["violin", "viola", "cello", "harpsichord", "flute", "oboe", "trumpet"],
        avoid: ["piano", "saxophone", "drums"]
    },

    "classical": {
        period: "1750-1820",
        characteristics: [
            "Clear phrase structure",
            "Homophonic texture",
            "Alberti bass",
            "Gradual dynamics",
            "Balance and symmetry"
        ],
        instruments: ["piano", "violin", "viola", "cello", "flute", "oboe", "clarinet", "bassoon", "horn", "trumpet"],
        avoid: ["electric guitar", "drums", "saxophone"]
    },

    "romantic": {
        period: "1820-1900",
        characteristics: [
            "Expressive melodies",
            "Rich harmonies with chromaticism",
            "Wide dynamic range",
            "Rubato",
            "Large orchestras"
        ],
        instruments: ["piano", "full orchestra", "solo voice"],
        avoid: ["electric instruments"]
    },

    "jazz": {
        period: "1900-present",
        characteristics: [
            "Swing rhythm",
            "Extended chords (7th, 9th, 11th, 13th)",
            "Improvisation",
            "Blue notes",
            "Walking bass",
            "Syncopation"
        ],
        instruments: ["saxophone", "trumpet", "piano", "double bass", "drums", "trombone", "guitar"],
        avoid: []
    },

    "rock": {
        period: "1950-present",
        characteristics: [
            "Strong backbeat",
            "Power chords",
            "Electric guitar prominence",
            "Verse-chorus structure",
            "High energy"
        ],
        instruments: ["electric guitar", "bass guitar", "drums", "keyboard", "voice"],
        avoid: ["harpsichord", "orchestra"]
    },

    "pop": {
        period: "1960-present",
        characteristics: [
            "Catchy melodies",
            "Simple harmonies",
            "Electronic elements",
            "Verse-chorus-bridge structure",
            "Production focus"
        ],
        instruments: ["synthesizer", "guitar", "bass", "drums", "voice"],
        avoid: []
    },

    "latin": {
        period: "Various",
        characteristics: [
            "Clave rhythm",
            "Syncopation",
            "Call and response",
            "Percussion focus",
            "Dance rhythms"
        ],
        instruments: ["congas", "bongos", "timbales", "piano", "bass", "brass", "guitar"],
        avoid: []
    },

    "electronic": {
        period: "1970-present",
        characteristics: [
            "Synthesized sounds",
            "Programmed beats",
            "Heavy use of effects",
            "Repetitive patterns",
            "Build-ups and drops"
        ],
        instruments: ["synthesizer", "drum machine", "sampler"],
        avoid: ["acoustic instruments (unless sampled)"]
    }
};

/**
 * Build a context-aware prompt for the LLM
 * @param {string} userRequest - The user's natural language request
 * @param {object} scoreInfo - Information about the current score
 * @param {string} targetStyle - Optional target style
 * @returns {string} Complete prompt for the LLM
 */
function buildContextualPrompt(userRequest, scoreInfo, targetStyle) {
    var prompt = SYSTEM_PROMPT + "\n\n";

    // Add score context
    prompt += "=== CURRENT SCORE INFORMATION ===\n";
    prompt += JSON.stringify(scoreInfo, null, 2) + "\n\n";

    // Add style guidelines if specified
    if (targetStyle && STYLE_GUIDELINES[targetStyle.toLowerCase()]) {
        var styleGuide = STYLE_GUIDELINES[targetStyle.toLowerCase()];
        prompt += "=== STYLE GUIDELINES ===\n";
        prompt += "Target Style: " + targetStyle + "\n";
        prompt += "Characteristics: " + styleGuide.characteristics.join(", ") + "\n";
        prompt += "Typical Instruments: " + styleGuide.instruments.join(", ") + "\n";
        if (styleGuide.avoid.length > 0) {
            prompt += "Avoid: " + styleGuide.avoid.join(", ") + "\n";
        }
        prompt += "\n";
    }

    // Add the user request
    prompt += "=== USER REQUEST ===\n";
    prompt += userRequest + "\n\n";

    // Add response format instructions
    prompt += "=== RESPONSE FORMAT ===\n";
    prompt += `Respond with a JSON object containing:
{
    "understanding": "Your interpretation of the request",
    "actions": [
        {
            "type": "action_type",
            "params": { ... },
            "description": "What this action does"
        }
    ],
    "explanation": "Musical rationale for the changes",
    "warnings": ["Any potential issues or limitations"]
}

Available action types:
- add_instrument: {name, family, clef}
- remove_instrument: {partIndex, name}
- transpose: {semitones, selection, partIndex, startMeasure, endMeasure}
- add_notes: {partIndex, measure, beat, pitches[], duration}
- add_dynamics: {type, measure, partIndex}
- add_tempo: {bpm, measure, text}
- add_articulation: {type, partIndex, startMeasure, endMeasure}
- add_crescendo: {type, startMeasure, endMeasure, partIndex}
- copy_pattern: {sourcePart, targetPart, transformation}
- harmonize: {sourcePart, intervals[], newPartName}
- change_style: {style, parameters}`;

    return prompt;
}

/**
 * Detect transformation type from user request
 * @param {string} request - User's natural language request
 * @returns {string[]} Array of detected transformation types
 */
function detectTransformationType(request) {
    var detected = [];
    var requestLower = request.toLowerCase();

    var keywords = {
        "harmonize": ["harmony", "harmonize", "harmonise", "voices", "chord"],
        "transpose": ["transpose", "key change", "pitch", "semitone", "higher", "lower"],
        "jazz_style": ["jazz", "swing", "bebop", "blues"],
        "rock_style": ["rock", "metal", "punk", "power chord"],
        "classical_style": ["classical", "baroque", "romantic", "orchestral"],
        "latin_style": ["latin", "salsa", "bossa", "samba", "rumba"],
        "add_drum_part": ["drum", "percussion", "beat", "rhythm"],
        "add_bass_line": ["bass", "bass line", "walking bass"],
        "add_string_section": ["strings", "violin", "cello", "orchestra"],
        "add_crescendo_section": ["crescendo", "build up", "intensity", "louder"],
        "add_articulations": ["articulation", "staccato", "legato", "accent"],
        "orchestrate": ["orchestrate", "arrangement", "full score", "ensemble"],
        "reduce": ["simplify", "reduce", "piano reduction", "solo"],
        "change_tempo": ["tempo", "faster", "slower", "bpm", "speed"]
    };

    for (var type in keywords) {
        var typeKeywords = keywords[type];
        for (var i = 0; i < typeKeywords.length; i++) {
            if (requestLower.indexOf(typeKeywords[i]) !== -1) {
                if (detected.indexOf(type) === -1) {
                    detected.push(type);
                }
                break;
            }
        }
    }

    return detected;
}

/**
 * Get template for a transformation type
 * @param {string} type - Transformation type
 * @returns {object} Template object or null
 */
function getTemplate(type) {
    return TRANSFORMATION_TEMPLATES[type] || null;
}

/**
 * Get style guidelines
 * @param {string} style - Music style
 * @returns {object} Style guidelines or null
 */
function getStyleGuidelines(style) {
    return STYLE_GUIDELINES[style.toLowerCase()] || null;
}
