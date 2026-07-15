# Technical Notes & FAQ

This document captures architectural details, technical discussions, and answers to key questions about the design and implementation of LiturgyBridge. It acts as a reference to prevent duplicate discussions.

---

## 1. Mobile Strategy (PWA vs. Native Apps)

### Question
How do we deploy to mobile devices (smartphones)? Is it a web browser app, and is it realistic to build native iOS and Android apps?

### Answer & Decision
We prioritize a **Web-First / Progressive Web App (PWA)** approach for the initial phases:
- **Zero-Friction Access:** Visitors scanning a QR code in church can open the application instantly in Safari/Chrome without downloading anything from the App Store.
- **PWA Capabilities:** Frequent users (members, choir, clergy) can add the app to their home screen. It will launch in full screen, hide the browser address bar, support offline caching of texts, and feel like a native app.
- **Native Packaging (Capacitor):** Because the frontend is built as a Vue.js Single Page Application (SPA), we can later package the exact same codebase into native iOS/Android packages using **Capacitor** (Ionic). This avoids writing native Kotlin/Swift apps from scratch.

---

## 2. Audio Capture & Microphones

### Question
How do we connect physical microphones (priest, choir) to the server for speech-to-text / translation?

### Answer & Decision
The LiturgyBridge backend is completely **decoupled from physical audio hardware**:
- **Client-Side Streaming:** Microphones are connected to the client device (e.g., a phone, tablet, or a local Raspberry Pi connected to the church mixing console). 
- **WebSockets Transmission:** The client captures the audio via the browser's MediaDevices API and streams binary audio chunks (PCM/Opus) to the backend via WebSockets.
- **Backend Service:** The `services/audio.py` module handles these stream buffers and feeds them asynchronously into the AI translation service (`services/translation.py`).
- **Benefit:** No physical sound cards or audio drivers are required on the server, ensuring the app runs anywhere (Docker, Cloud, or Local PC).

---

## 3. Video Output (Wall Displays / Beamers)

### Question
How do we output the synchronized text to a screen or projector in the church? Do we need a video cable from the server?

### Answer & Decision
We utilize a **web-based display casting model**:
- **Display URL:** We expose a dedicated, clean display route (`/services/{service_id}/display`) optimized for large-screen readability and projectors.
- **Wireless Sync:** Any cheap smart screen, TV, or projector connected to a browser (e.g., Smart TV browser, Fire TV Stick, tablet) opens this URL. It connects to the same sync WebSocket as the visitors.
- **Benefit:** Zero custom hardware video drivers are needed on the server, and no long cables are required. The layout is managed entirely via CSS.

---

## 4. QR-Code Generation & Local WiFi Deployment

### Question
How do we generate QR codes and configure the server to work on a local offline church WiFi?

### Answer & Decision
- **Dynamic URLs:** QR codes are generated dynamically in `routes/liturgy.py` by converting a service URL into a QR graphic.
- **Base URL Configuration:** The backend uses a `BASE_URL` setting (configured in `config.py` via environment variables). 
  - On a public cloud server: `BASE_URL=https://liturgybridge.org`
  - On a local offline church server: `BASE_URL=http://192.168.1.100` (the server's local IP).
- **Local DNS Routing:** For local network deployments, a local DNS router (like dnsmasq) can map a human-friendly domain (e.g., `http://liturgie.local`) to the server IP.

---

## 5. Global vs. Community Roles

### Question
Can a user have multiple roles (e.g., a priest in parish A, translator globally, simple visitor in parish B)?

### Answer & Decision
Yes. We split roles into two logical buckets:
- **Global Roles:** Stored directly on the `User` model (e.g., `["translator", "platform_admin"]`). A global translator can translate standard liturgical texts regardless of parish affiliation.
- **Community Roles:** Stored on the `Membership` join table (e.g., `["priest", "administrator", "member"]`). A user's authority is scoped to that specific community.
