/**
 * ==============================================================================
 * SERVICES LAYER: MailService (Asynchronous DSN Store-and-Forward Mailbox)
 * ==============================================================================
 * Manages medical orders, clinical advisories, and asynchronous communication
 * between the Flight Surgeon (JSC Houston) and Mars Cabin Crew via simulated
 * Deep Space Network (DSN) uplink/downlink.
 * Kept strictly under 300 lines (Clean Code & SRP).
 * ==============================================================================
 */

class MailService {
  constructor(soundService = null, authService = null) {
    this._sound = soundService || window.soundService;
    this._auth = authService || window.authService;
    this._storageKey = "helios_dsn_mailbox";
    this._listeners = [];
    this._messages = this._loadInitialMessages();
  }

  _loadInitialMessages() {
    try {
      const stored = localStorage.getItem(this._storageKey);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch (e) {
      console.warn("Could not read localStorage for DSN mail:", e);
    }

    return [
      {
        id: "DSN-MSG-101",
        sender: "Dr. Marcus Vance",
        senderRole: "Flight Surgeon (JSC Houston)",
        recipientId: "ASTRO-01",
        recipientName: "Alex Mercer",
        subject: "Sol 120 Clinical Protocols & Environmental Baseline",
        body: "Ares-VI baseline telemetry nominal for Sol 120. Maintain routine hydration quota (>2.2 L) and perform scheduled acoustic dosimetry check during EVA operations.",
        priority: "NOMINAL",
        category: "BMed Protocol",
        sol: 120,
        timestamp: "Sol 120 · 14:00 UTC",
        synced: true,
        acknowledged: true,
        ackTimestamp: "Sol 120 · 14:18 UTC"
      }
    ];
  }

  _save() {
    try {
      localStorage.setItem(this._storageKey, JSON.stringify(this._messages));
    } catch (e) {
      console.warn("Could not persist DSN mail:", e);
    }
    this._notify();
  }

  subscribe(callback) {
    if (typeof callback === "function") {
      this._listeners.push(callback);
    }
  }

  _notify() {
    this._listeners.forEach((fn) => {
      try {
        fn(this._messages);
      } catch (err) {
        console.error("Mail listener error:", err);
      }
    });
    this.updateMailUi();
  }

  getMessagesForUser(userId = null) {
    const target = userId || this._auth?.getCurrentUser()?.id || "ASTRO-01";
    return this._messages.filter((m) => m.recipientId === target || m.recipientId === "ALL");
  }

  getPendingCount(userId = null) {
    const userMessages = this.getMessagesForUser(userId);
    return userMessages.filter((m) => !m.synced).length;
  }

  getUnacknowledgedCount(userId = null) {
    const userMessages = this.getMessagesForUser(userId);
    return userMessages.filter((m) => m.synced && !m.acknowledged).length;
  }

  sendMedicalOrder({ recipientId, recipientName, subject, body, priority = "URGENT", category = "Medical Order" }) {
    if (!body || !body.trim()) return null;

    const newMessage = {
      id: "DSN-" + Date.now().toString(36).toUpperCase(),
      sender: "Dr. Marcus Vance",
      senderRole: "Flight Surgeon (JSC Houston)",
      recipientId: recipientId || "ASTRO-01",
      recipientName: recipientName || (recipientId === "ASTRO-02" ? "Elena Rostova" : "Alex Mercer"),
      subject: (subject || "BMed Clinical Prescription").trim(),
      body: body.trim(),
      priority: priority.toUpperCase(),
      category,
      sol: 120,
      timestamp: `Sol 120 · ${new Date().toISOString().substring(11, 16)} UTC`,
      synced: false,
      acknowledged: false,
      ackTimestamp: null
    };

    this._messages.unshift(newMessage);
    this._save();
    return newMessage;
  }

  syncMailbox(userId = null) {
    const target = userId || this._auth?.getCurrentUser()?.id || "ASTRO-01";
    let newlySynced = 0;
    this._messages.forEach((m) => {
      if ((m.recipientId === target || m.recipientId === "ALL") && !m.synced) {
        m.synced = true;
        newlySynced++;
      }
    });

    if (newlySynced > 0) {
      this._sound?.playNominal?.();
    } else {
      this._sound?.playClick?.();
    }

    this._save();
    return newlySynced;
  }

  acknowledgeOrder(messageId) {
    const msg = this._messages.find((m) => m.id === messageId);
    if (!msg) return null;

    msg.acknowledged = true;
    msg.ackTimestamp = `Sol 120 · ${new Date().toISOString().substring(11, 16)} UTC`;
    this._sound?.playNominal?.();
    this._save();
    return msg;
  }

  updateMailUi() {
    const user = this._auth?.getCurrentUser();
    const userId = user?.id || "ASTRO-01";
    const pendingCount = this.getPendingCount(userId);
    const badge = document.getElementById("mailPendingBadge");
    const statusText = document.getElementById("mailStatusText");
    const btnSync = document.getElementById("btnSyncMail");

    if (badge) {
      if (pendingCount > 0) {
        badge.style.display = "inline-flex";
        badge.innerText = `${pendingCount} PENDING DSN PACKET${pendingCount > 1 ? "S" : ""}`;
      } else {
        badge.style.display = "none";
      }
    }

    if (statusText) {
      if (pendingCount > 0) {
        statusText.innerHTML = `<span style="color:var(--neon-amber); font-weight:bold;">⚠️ ${pendingCount} incoming packet${pendingCount > 1 ? "s" : ""} in DSN queue from Houston.</span>`;
      } else {
        statusText.innerText = "No new messages pending in the DSN queue.";
      }
    }

    if (btnSync && pendingCount > 0) {
      btnSync.style.borderColor = "var(--neon-amber)";
      btnSync.style.color = "var(--neon-amber)";
    } else if (btnSync) {
      btnSync.style.borderColor = "";
      btnSync.style.color = "";
    }

    this.renderInbox(userId);
  }

  renderInbox(userId = null) {
    const inboxContainer = document.getElementById("mailInboxList");
    if (!inboxContainer) return;

    const userMessages = this.getMessagesForUser(userId).filter((m) => m.synced);
    if (userMessages.length === 0) {
      inboxContainer.innerHTML = `
        <div style="padding:12px; text-align:center; color:var(--text-muted); font-size:11px; font-family:var(--font-data);">
          Inbox empty. Synchronize DSN link to retrieve pending Houston transmissions.
        </div>`;
      return;
    }

    inboxContainer.innerHTML = userMessages
      .map((msg) => {
        const isAck = msg.acknowledged;
        const borderCol = isAck ? "rgba(0,240,255,0.25)" : "var(--neon-amber)";
        const bgCol = isAck ? "#060d1d" : "rgba(255,170,0,0.06)";
        const priorityBadge =
          msg.priority === "URGENT"
            ? '<span class="badge-status status-critical" style="font-size:9px; padding:1px 5px;">URGENT</span>'
            : msg.priority === "HIGH"
            ? '<span class="badge-status status-warning" style="font-size:9px; padding:1px 5px;">HIGH</span>'
            : '<span class="badge-status status-stable" style="font-size:9px; padding:1px 5px;">ROUTINE</span>';

        return `
        <div style="background:${bgCol}; border:1px solid ${borderCol}; border-radius:6px; padding:10px 12px; display:flex; flex-direction:column; gap:6px;">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:4px;">
            <div style="display:flex; align-items:center; gap:6px;">
              <span style="font-size:12px;">🩺</span>
              <strong style="color:#f8fafc; font-family:var(--font-hud); font-size:11px;">${msg.sender}</strong>
              <span style="color:var(--text-muted); font-size:9.5px;">(${msg.senderRole})</span>
              ${priorityBadge}
            </div>
            <div style="color:var(--text-muted); font-size:10px; font-family:var(--font-data);">
              ${msg.timestamp}
            </div>
          </div>

          <div style="font-weight:600; color:var(--neon-cyan); font-size:11.5px; font-family:var(--font-data);">
            ${msg.subject}
          </div>

          <div style="color:#cbd5e1; font-size:11px; line-height:1.4; background:rgba(0,0,0,0.25); padding:8px 10px; border-radius:4px; font-family:var(--font-data); border-left:2px solid var(--neon-cyan);">
            ${msg.body}
          </div>

          <div style="display:flex; justify-content:space-between; align-items:center; margin-top:2px;">
            <span style="font-size:9.5px; color:var(--text-muted); font-family:var(--font-data);">
              TO: ${msg.recipientName} (${msg.recipientId})
            </span>
            ${
              isAck
                ? `
              <span style="color:var(--c-green-ink); font-size:10px; font-family:var(--font-hud); display:flex; align-items:center; gap:4px;">
                <span>✓</span> ACKNOWLEDGED (${msg.ackTimestamp})
              </span>
            `
                : `
              <button type="button" class="btn-hud" onclick="window.mailService?.acknowledgeOrder('${msg.id}')" style="font-size:9.5px; padding:4px 10px; border-color:var(--neon-amber); color:var(--neon-amber);">
                ✓ ACKNOWLEDGE ORDER &amp; LOG TO CABIN RECORD
              </button>
            `
            }
          </div>
        </div>
      `;
      })
      .join("");
  }
}

window.MailService = MailService;
