/**
 * ==============================================================================
 * SERVICES LAYER: AuthService (Access Control and Crew Management)
 * ==============================================================================
 * Manages the authentication of space crew members and the flight surgeon
 * through user credentials and a 4-digit PIN.
 */

class AuthService {
  constructor() {
    this._users = [
      {
        id: "ASTRO-01",
        username: "astro1",
        pin: "1001",
        name: "Alex Mercer",
        role: "ASTRONAUT",
        rank: "Commander A01",
        avatar: "👨‍🚀",
        mission: "ARES-VI (Sol 120)"
      },
      {
        id: "ASTRO-02",
        username: "astro2",
        pin: "2002",
        name: "Elena Rostova",
        role: "ASTRONAUT",
        rank: "Specialist A02",
        avatar: "👩‍🚀",
        mission: "ARES-VI (Sol 120)"
      },
      {
        id: "MED-01",
        username: "surgeon",
        pin: "9009",
        name: "Dr. Marcus Vance",
        role: "FLIGHT_SURGEON",
        rank: "Flight Surgeon",
        avatar: "🩺",
        mission: "JSC Houston Control Center"
      }
    ];

    this._storageKey = "helios_session_user";
    this._currentUser = this._loadSavedSession();
    this._listeners = [];
  }

  getCurrentUser() {
    return this._currentUser;
  }

  listDemoUsers() {
    return this._users.map(u => ({
      username: u.username,
      pin: u.pin,
      name: u.name,
      role: u.role,
      rank: u.rank,
      avatar: u.avatar
    }));
  }

  authenticate(username, pin) {
    const usernameCredential = (username || "").trim().toLowerCase();
    const pinCredential = (pin || "").trim();

    const foundUser = this._users.find(
      u => u.username.toLowerCase() === usernameCredential && u.pin === pinCredential
    );

    if (foundUser) {
      this._currentUser = foundUser;
      try {
        localStorage.setItem(this._storageKey, JSON.stringify(foundUser));
      } catch (e) {
        console.warn("[AuthService] Could not save the session to storage:", e);
      }
      this._notifyChange();
      return { success: true, user: foundUser };
    }

    return { success: false, error: "Invalid credentials. Check the username or PIN." };
  }

  logout() {
    this._currentUser = null;
    try {
      localStorage.removeItem(this._storageKey);
    } catch (e) {
      console.warn("[AuthService] Error clearing storage:", e);
    }
    this._notifyChange();
  }

  onSessionChange(callback) {
    if (typeof callback === "function") {
      this._listeners.push(callback);
    }
  }

  subscribe(callback) {
    this.onSessionChange(callback);
  }

  _notifyChange() {
    this._listeners.forEach(cb => {
      try {
        cb(this._currentUser);
      } catch (err) {
        console.error("[AuthService] Listener error:", err);
      }
    });
  }

  isAuthenticated() {
    return !!this._currentUser;
  }

  _loadSavedSession() {
    try {
      const saved = localStorage.getItem(this._storageKey);
      if (saved) {
        const data = JSON.parse(saved);
        const existing = this._users.find(u => u.username === data.username);
        if (existing) return existing;
      }
    } catch (e) {
      console.warn("[AuthService] Error reading the previous session:", e);
    }
    // Requires explicit PIN authentication (no auto-login by default)
    return null;
  }
}

window.authService = new AuthService();
