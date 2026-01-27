import { useAppStore } from "../lib/store";
import { requestScoreInfo } from "../lib/commands";

export function ScoreInfo() {
  const { scoreInfo, connected, addLog } = useAppStore();

  const keySignatureNames: Record<string, string> = {
    "-7": "Cb Maj",
    "-6": "Gb Maj",
    "-5": "Db Maj",
    "-4": "Ab Maj",
    "-3": "Eb Maj",
    "-2": "Bb Maj",
    "-1": "F Maj",
    "0": "C Maj",
    "1": "G Maj",
    "2": "D Maj",
    "3": "A Maj",
    "4": "E Maj",
    "5": "B Maj",
    "6": "F# Maj",
    "7": "C# Maj",
  };

  const handleRefresh = async () => {
    try {
      await requestScoreInfo();
      addLog("Requested score info from plugin");
    } catch (error) {
      addLog(`Error requesting score info: ${error}`);
    }
  };

  if (!connected) {
    return (
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-white">Score Info</h2>
        <span className="text-xs text-gray-500">Connect to MuseScore first</span>
      </div>
    );
  }

  if (!scoreInfo) {
    return (
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-white">Score Info</h2>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">No score loaded</span>
          <button
            onClick={handleRefresh}
            className="text-xs text-accent hover:text-accent-hover"
          >
            Refresh
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Title row */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3">
          <h2 className="text-sm font-semibold text-white">
            {scoreInfo.title || "Untitled"}
          </h2>
          {scoreInfo.composer && (
            <span className="text-xs text-gray-400">by {scoreInfo.composer}</span>
          )}
        </div>
        <button
          onClick={handleRefresh}
          className="text-xs text-gray-400 hover:text-white"
          title="Refresh score info"
        >
          &#8635;
        </button>
      </div>

      {/* Info chips */}
      <div className="flex flex-wrap gap-2">
        <InfoChip label="Measures" value={scoreInfo.measures.toString()} />
        <InfoChip label="Staves" value={scoreInfo.staves.toString()} />
        <InfoChip
          label="Time"
          value={
            scoreInfo.timeSignature
              ? `${scoreInfo.timeSignature.numerator}/${scoreInfo.timeSignature.denominator}`
              : "4/4"
          }
        />
        <InfoChip
          label="Key"
          value={keySignatureNames[scoreInfo.keySignature.toString()] || "C Maj"}
        />
        {scoreInfo.tempo && (
          <InfoChip label="Tempo" value={`${scoreInfo.tempo} BPM`} />
        )}
        {scoreInfo.parts && scoreInfo.parts.length > 0 && (
          <InfoChip
            label="Parts"
            value={scoreInfo.parts.map((p) => p.name).join(", ")}
          />
        )}
      </div>
    </div>
  );
}

function InfoChip({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-surface-hover px-2 py-1 rounded text-xs">
      <span className="text-gray-500">{label}: </span>
      <span className="text-gray-300">{value}</span>
    </div>
  );
}
