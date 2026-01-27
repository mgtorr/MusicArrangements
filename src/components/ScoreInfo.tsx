import { useAppStore } from "../lib/store";

export function ScoreInfo() {
  const { scoreInfo, connected } = useAppStore();

  const keySignatureNames: Record<string, string> = {
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
    "7": "C# Major / A# minor",
  };

  if (!connected) {
    return (
      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">Score Info</h2>
        <p className="text-sm text-gray-500">
          Connect to MuseScore to see score information.
        </p>
      </div>
    );
  }

  if (!scoreInfo) {
    return (
      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">Score Info</h2>
        <p className="text-sm text-gray-500">
          No score information received yet. Open a score in MuseScore and click
          "Send Score Info" in the plugin.
        </p>
      </div>
    );
  }

  return (
    <div className="card">
      <h2 className="text-lg font-semibold text-white mb-4">Score Info</h2>

      <div className="space-y-3">
        <div>
          <span className="text-xs text-gray-400 block">Title</span>
          <span className="text-white font-medium">
            {scoreInfo.title || "Untitled"}
          </span>
        </div>

        {scoreInfo.composer && (
          <div>
            <span className="text-xs text-gray-400 block">Composer</span>
            <span className="text-gray-300">{scoreInfo.composer}</span>
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          <div>
            <span className="text-xs text-gray-400 block">Measures</span>
            <span className="text-gray-300">{scoreInfo.measures}</span>
          </div>
          <div>
            <span className="text-xs text-gray-400 block">Staves</span>
            <span className="text-gray-300">{scoreInfo.staves}</span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <span className="text-xs text-gray-400 block">Time Signature</span>
            <span className="text-gray-300">
              {scoreInfo.timeSignature
                ? `${scoreInfo.timeSignature.numerator}/${scoreInfo.timeSignature.denominator}`
                : "4/4"}
            </span>
          </div>
          <div>
            <span className="text-xs text-gray-400 block">Key</span>
            <span className="text-gray-300">
              {keySignatureNames[scoreInfo.keySignature.toString()] || "C Major"}
            </span>
          </div>
        </div>

        {scoreInfo.parts && scoreInfo.parts.length > 0 && (
          <div>
            <span className="text-xs text-gray-400 block">Parts</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {scoreInfo.parts.map((part, index) => (
                <span
                  key={index}
                  className="text-xs bg-surface-hover px-2 py-1 rounded text-gray-300"
                >
                  {part.name}
                </span>
              ))}
            </div>
          </div>
        )}

        {scoreInfo.tempo && (
          <div>
            <span className="text-xs text-gray-400 block">Tempo</span>
            <span className="text-gray-300">{scoreInfo.tempo} BPM</span>
          </div>
        )}
      </div>
    </div>
  );
}
