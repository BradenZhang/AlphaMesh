import { useEffect } from "react";
import { createPortal } from "react-dom";

interface RunDetailDrawerProps {
  open: boolean;
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}

export function RunDetailDrawer({ open, title, onClose, children }: RunDetailDrawerProps) {
  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <>
      <div className="drawerOverlay" onClick={onClose} />
      <aside className="drawerPanel">
        <div className="drawerHeader">
          <h3>{title}</h3>
          <button className="ghostButton" onClick={onClose} type="button">
            Close
          </button>
        </div>
        <div className="drawerBody">{children}</div>
      </aside>
    </>,
    document.body
  );
}
