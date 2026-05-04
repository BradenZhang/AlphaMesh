import { useCallback, useState } from "react";
import type { WatchlistItem } from "../types";

interface WatchlistPanelProps {
  items: WatchlistItem[];
  onAdd: (symbol: string) => void;
  onRemove: (itemId: string) => void;
  onBatchResearch: () => void;
  onRebalance: () => void;
  loading: boolean;
}

export function WatchlistPanel({
  items,
  onAdd,
  onRemove,
  onBatchResearch,
  onRebalance,
  loading
}: WatchlistPanelProps) {
  const [inputValue, setInputValue] = useState("");

  const handleAdd = useCallback(() => {
    const symbol = inputValue.trim().toUpperCase();
    if (!symbol) return;
    onAdd(symbol);
    setInputValue("");
  }, [inputValue, onAdd]);

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      if (event.key === "Enter") handleAdd();
    },
    [handleAdd]
  );

  return (
    <section className="railSection">
      <div className="sectionHeading">
        <span>Watchlist</span>
        <small>{items.length}</small>
      </div>
      <div className="watchlistInputRow">
        <input
          placeholder="Add symbol..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button className="ghostButton" onClick={handleAdd} disabled={loading} type="button">
          +
        </button>
      </div>
      <div className="railFeed">
        {items.map((item) => (
          <div className="feedCard" key={item.item_id}>
            <strong>{item.symbol}</strong>
            {item.label ? <span>{item.label}</span> : null}
            <button
              className="ghostButton dangerGhost"
              onClick={() => onRemove(item.item_id)}
              type="button"
            >
              x
            </button>
          </div>
        ))}
        {items.length === 0 ? <p className="mutedText">No symbols in watchlist.</p> : null}
      </div>
      {items.length > 0 ? (
        <div className="watchlistActions">
          <button className="ghostButton" onClick={onBatchResearch} disabled={loading} type="button">
            Batch Research
          </button>
          <button className="primaryButton" onClick={onRebalance} disabled={loading} type="button">
            Rebalance
          </button>
        </div>
      ) : null}
    </section>
  );
}
