import { memo } from "react";
import { Icon } from "../../components/Icon";

interface SettingsDrawerProps {
  open: boolean;
  onClose: () => void;
  model: string | undefined;
  setModel: (v: string) => void;
  config: { host: string; model: string; tools: number; tool_names: string[] } | undefined;
}

export const SettingsDrawer = memo(({ open, onClose, model, setModel, config }: SettingsDrawerProps) => {
  const activeModel = model ?? config?.model ?? "";

  return (
    <>
      <div className={`sidebar-backdrop ${open ? "open" : ""}`} style={{ display: open ? "block" : "none" }} onClick={onClose} />
      <div className={`settings-drawer ${open ? "open" : "collapsed"}`}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ fontSize: "var(--text-lg)", fontWeight: 600 }}>Settings</div>
          <button className="icon-btn" onClick={onClose} aria-label="Close settings">
             <Icon name="moon" style={{ width: "1.2rem", height: "1.2rem" }} />
          </button>
        </div>
        <div className="card" style={{ padding: "var(--space-4)" }}>
          <div className="card-title">Agent Configuration</div>
          <div className="card-sub">Ollama Model Settings</div>
          <div style={{ marginTop: "var(--space-4)", display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
            <label className="field">
              <span>Model Name</span>
              <input
                className="input"
                list="ollama-models"
                value={activeModel}
                placeholder="Model"
                aria-label="Ollama model"
                onChange={(e) => setModel(e.target.value)}
              />
            </label>
            <datalist id="ollama-models">
              {config ? <option value={config.model} /> : null}
            </datalist>
            <div>
              <span className="badge badge-muted">{config?.host ?? "Not connected"}</span>
            </div>
          </div>
        </div>
        <div className="card" style={{ padding: "var(--space-4)" }}>
          <div className="card-title">Available Tools</div>
          <div className="card-sub">{config?.tools ?? 0} active tools</div>
          <div className="tools-panel" style={{marginTop: "0.5rem"}}>
            {(config?.tool_names ?? []).map((name) => (
              <div className="tool-item" key={name}>
                <code>{name}</code>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
});
