/**
 * ScoreUtils.js - Utility functions for MuseScore score manipulation
 * Part of the LLM Arranger Plugin
 */

.pragma library

// Note name mappings
var NOTE_NAMES = {
    0: "C", 1: "C#", 2: "D", 3: "D#", 4: "E", 5: "F",
    6: "F#", 7: "G", 8: "G#", 9: "A", 10: "A#", 11: "B"
};

var NOTE_TO_MIDI = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
    "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11
};

// Duration constants (in ticks, assuming 480 ticks per quarter note)
var DURATIONS = {
    "whole": 1920,
    "half": 960,
    "quarter": 480,
    "eighth": 240,
    "sixteenth": 120,
    "thirtysecond": 60
};

/**
 * Convert MIDI pitch to note name with octave
 * @param {number} midiPitch - MIDI pitch value (0-127)
 * @returns {string} Note name like "C4", "F#5"
 */
function midiToNoteName(midiPitch) {
    var octave = Math.floor(midiPitch / 12) - 1;
    var noteIndex = midiPitch % 12;
    return NOTE_NAMES[noteIndex] + octave;
}

/**
 * Convert note name to MIDI pitch
 * @param {string} noteName - Note name like "C4", "F#5"
 * @returns {number} MIDI pitch value
 */
function noteNameToMidi(noteName) {
    var match = noteName.match(/([A-Ga-g][#b]?)(\-?\d+)/);
    if (!match) return -1;

    var note = match[1].toUpperCase();
    var octave = parseInt(match[2]);

    var noteValue = NOTE_TO_MIDI[note];
    if (noteValue === undefined) return -1;

    return (octave + 1) * 12 + noteValue;
}

/**
 * Get interval name from semitone distance
 * @param {number} semitones - Number of semitones
 * @returns {string} Interval name
 */
function getIntervalName(semitones) {
    var intervals = {
        0: "Unison", 1: "Minor 2nd", 2: "Major 2nd", 3: "Minor 3rd",
        4: "Major 3rd", 5: "Perfect 4th", 6: "Tritone", 7: "Perfect 5th",
        8: "Minor 6th", 9: "Major 6th", 10: "Minor 7th", 11: "Major 7th",
        12: "Octave"
    };
    var normalized = Math.abs(semitones) % 12;
    return intervals[normalized] || "Unknown";
}

/**
 * Get harmony intervals for a given chord type
 * @param {string} chordType - Type of chord (major, minor, dim, aug, etc.)
 * @returns {number[]} Array of semitone intervals from root
 */
function getChordIntervals(chordType) {
    var chords = {
        "major": [0, 4, 7],
        "minor": [0, 3, 7],
        "diminished": [0, 3, 6],
        "augmented": [0, 4, 8],
        "major7": [0, 4, 7, 11],
        "minor7": [0, 3, 7, 10],
        "dominant7": [0, 4, 7, 10],
        "sus2": [0, 2, 7],
        "sus4": [0, 5, 7],
        "add9": [0, 4, 7, 14],
        "power": [0, 7]
    };
    return chords[chordType.toLowerCase()] || chords["major"];
}

/**
 * Analyze a note sequence to determine likely key
 * @param {number[]} pitches - Array of MIDI pitches
 * @returns {object} Key analysis result {key, mode, confidence}
 */
function analyzeKey(pitches) {
    // Krumhansl-Schmuckler key-finding algorithm (simplified)
    var majorProfile = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88];
    var minorProfile = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17];

    // Count pitch classes
    var pitchClasses = new Array(12).fill(0);
    for (var i = 0; i < pitches.length; i++) {
        pitchClasses[pitches[i] % 12]++;
    }

    // Normalize
    var total = pitches.length;
    for (var j = 0; j < 12; j++) {
        pitchClasses[j] /= total;
    }

    // Find best correlation
    var bestKey = 0;
    var bestMode = "major";
    var bestCorr = -1;

    for (var key = 0; key < 12; key++) {
        // Rotate pitch classes
        var rotated = [];
        for (var k = 0; k < 12; k++) {
            rotated.push(pitchClasses[(k + key) % 12]);
        }

        // Calculate correlation with major
        var corrMajor = correlation(rotated, majorProfile);
        if (corrMajor > bestCorr) {
            bestCorr = corrMajor;
            bestKey = key;
            bestMode = "major";
        }

        // Calculate correlation with minor
        var corrMinor = correlation(rotated, minorProfile);
        if (corrMinor > bestCorr) {
            bestCorr = corrMinor;
            bestKey = key;
            bestMode = "minor";
        }
    }

    return {
        key: NOTE_NAMES[bestKey],
        mode: bestMode,
        confidence: bestCorr
    };
}

/**
 * Calculate Pearson correlation coefficient
 */
function correlation(x, y) {
    var n = x.length;
    var sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0, sumY2 = 0;

    for (var i = 0; i < n; i++) {
        sumX += x[i];
        sumY += y[i];
        sumXY += x[i] * y[i];
        sumX2 += x[i] * x[i];
        sumY2 += y[i] * y[i];
    }

    var denom = Math.sqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));
    if (denom === 0) return 0;

    return (n * sumXY - sumX * sumY) / denom;
}

/**
 * Generate a simple harmony line based on the melody
 * @param {number[]} melody - Array of MIDI pitches
 * @param {string} harmonyType - Type of harmony (thirds, sixths, etc.)
 * @returns {number[]} Harmony line
 */
function generateHarmony(melody, harmonyType) {
    var interval;
    switch (harmonyType.toLowerCase()) {
        case "thirds_above": interval = 4; break;
        case "thirds_below": interval = -3; break;
        case "sixths_above": interval = 9; break;
        case "sixths_below": interval = -4; break;
        case "octave_above": interval = 12; break;
        case "octave_below": interval = -12; break;
        case "fifth_above": interval = 7; break;
        case "fifth_below": interval = -7; break;
        default: interval = 4;
    }

    var harmony = [];
    for (var i = 0; i < melody.length; i++) {
        harmony.push(melody[i] + interval);
    }
    return harmony;
}

/**
 * Generate drum pattern based on style
 * @param {string} style - Music style (rock, jazz, latin, etc.)
 * @param {number} measures - Number of measures
 * @param {number} beatsPerMeasure - Time signature numerator
 * @returns {object[]} Array of drum hits {beat, instrument, velocity}
 */
function generateDrumPattern(style, measures, beatsPerMeasure) {
    var patterns = {
        "rock": {
            kick: [1, 3],
            snare: [2, 4],
            hihat: [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5]
        },
        "jazz": {
            ride: [1, 2, 3, 4],
            kick: [1],
            snare: [2.5, 4.5],
            hihat: [2, 4]
        },
        "latin": {
            clave: [1, 2.5, 4, 4.5],
            conga: [1, 2, 3, 4],
            cowbell: [1, 3]
        },
        "waltz": {
            kick: [1],
            snare: [2, 3],
            hihat: [1, 2, 3]
        },
        "pop": {
            kick: [1, 2.5, 3],
            snare: [2, 4],
            hihat: [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5]
        },
        "metal": {
            kick: [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5],
            snare: [2, 4],
            hihat: [1, 1.25, 1.5, 1.75, 2, 2.25, 2.5, 2.75, 3, 3.25, 3.5, 3.75, 4, 4.25, 4.5, 4.75]
        }
    };

    var pattern = patterns[style.toLowerCase()] || patterns["rock"];
    var result = [];

    for (var m = 0; m < measures; m++) {
        for (var instrument in pattern) {
            var beats = pattern[instrument];
            for (var b = 0; b < beats.length; b++) {
                result.push({
                    measure: m,
                    beat: beats[b],
                    instrument: instrument,
                    velocity: 80
                });
            }
        }
    }

    return result;
}

/**
 * Suggest transposition to fit vocal range
 * @param {number} lowestNote - Lowest MIDI pitch in the melody
 * @param {number} highestNote - Highest MIDI pitch in the melody
 * @param {string} voiceType - Voice type (soprano, alto, tenor, bass)
 * @returns {number} Suggested transposition in semitones
 */
function suggestTranspositionForVoice(lowestNote, highestNote, voiceType) {
    var ranges = {
        "soprano": { low: 60, high: 81 },  // C4 - A5
        "alto": { low: 55, high: 77 },      // G3 - F5
        "tenor": { low: 48, high: 69 },     // C3 - A4
        "bass": { low: 40, high: 60 },      // E2 - C4
        "baritone": { low: 45, high: 65 }   // A2 - F4
    };

    var range = ranges[voiceType.toLowerCase()] || ranges["tenor"];

    // Find the transposition that fits the melody in the voice range
    var melodyRange = highestNote - lowestNote;
    var targetMid = (range.low + range.high) / 2;
    var melodyMid = (lowestNote + highestNote) / 2;

    return Math.round(targetMid - melodyMid);
}

/**
 * Get scale degrees for a given scale type
 * @param {string} scaleType - Scale type (major, minor, pentatonic, etc.)
 * @returns {number[]} Array of semitone intervals from tonic
 */
function getScaleDegrees(scaleType) {
    var scales = {
        "major": [0, 2, 4, 5, 7, 9, 11],
        "natural_minor": [0, 2, 3, 5, 7, 8, 10],
        "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
        "melodic_minor": [0, 2, 3, 5, 7, 9, 11],
        "pentatonic_major": [0, 2, 4, 7, 9],
        "pentatonic_minor": [0, 3, 5, 7, 10],
        "blues": [0, 3, 5, 6, 7, 10],
        "dorian": [0, 2, 3, 5, 7, 9, 10],
        "phrygian": [0, 1, 3, 5, 7, 8, 10],
        "lydian": [0, 2, 4, 6, 7, 9, 11],
        "mixolydian": [0, 2, 4, 5, 7, 9, 10],
        "locrian": [0, 1, 3, 5, 6, 8, 10],
        "whole_tone": [0, 2, 4, 6, 8, 10],
        "chromatic": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    };
    return scales[scaleType.toLowerCase()] || scales["major"];
}

/**
 * Convert tempo description to BPM
 * @param {string} description - Tempo description (largo, allegro, etc.)
 * @returns {number} BPM value
 */
function tempoDescriptionToBPM(description) {
    var tempos = {
        "grave": 35,
        "largo": 50,
        "lento": 55,
        "larghetto": 60,
        "adagio": 70,
        "andante": 85,
        "andantino": 95,
        "moderato": 105,
        "allegretto": 115,
        "allegro": 140,
        "vivace": 160,
        "presto": 180,
        "prestissimo": 200
    };
    return tempos[description.toLowerCase()] || 120;
}

/**
 * Analyze rhythm patterns in a score section
 * @param {object[]} notes - Array of note objects with duration info
 * @returns {object} Rhythm analysis
 */
function analyzeRhythm(notes) {
    var durations = {};
    var totalDuration = 0;

    for (var i = 0; i < notes.length; i++) {
        var dur = notes[i].duration;
        durations[dur] = (durations[dur] || 0) + 1;
        totalDuration += dur;
    }

    // Find most common duration
    var mostCommon = null;
    var maxCount = 0;
    for (var d in durations) {
        if (durations[d] > maxCount) {
            maxCount = durations[d];
            mostCommon = d;
        }
    }

    return {
        totalNotes: notes.length,
        totalDuration: totalDuration,
        mostCommonDuration: mostCommon,
        durationDistribution: durations
    };
}
