"""
LiturgyBridge FastAPI Entrypoint.

This module bootstraps the FastAPI application, registers middleware (CORS, safety),
includes sub-routers for different resources (auth, community, liturgy, sync),
and manages lifecycle events (like database table auto-creation on startup).
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.database import create_db_and_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    print(f"Starting {settings.PROJECT_NAME} in environment: {settings.ENV}")
    # Auto-create tables (in development)
    create_db_and_tables()
    yield
    # Shutdown actions
    print(f"Stopping {settings.PROJECT_NAME}...")

# Initialize FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Digital multilingual companion for Orthodox worship",
    version="1.0.0",
    lifespan=lifespan,
)

# Set up CORS middleware to allow connection from Vue.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import Routers
from backend.app.routes import auth, community, liturgy, sync, wiki

# Include Routers with API prefix
app.include_router(auth.router, prefix="/api/v1")
app.include_router(community.router, prefix="/api/v1")
app.include_router(liturgy.router, prefix="/api/v1")
app.include_router(sync.router, prefix="/api/v1")
app.include_router(wiki.router, prefix="/api/v1")

# Root endpoint
@app.get("/")
def read_root():
    return {
        "project": settings.PROJECT_NAME,
        "status": "healthy",
        "api_documentation": "/docs",
        "preview_client": "/preview"
    }

@app.get("/preview", response_class=HTMLResponse)
def get_liturgy_preview_client():
    from sqlmodel import Session, select
    from backend.app.database import engine
    from backend.app.models import LiturgicalService, LiturgicalTemplate, Community, AudioTrack
    from datetime import datetime, timezone

    with Session(engine) as session:
        # Resolve the latest scheduled service, or auto-seed one if database was reset by tests
        service = session.exec(
            select(LiturgicalService).order_by(LiturgicalService.scheduled_time.desc())
        ).first()
        
        if not service:
            # Recreate default community
            community = session.exec(select(Community)).first()
            if not community:
                community = Community(name="St. Nicholas Berlin", location="Berlin, Deutschland")
                session.add(community)
                session.commit()
                session.refresh(community)
            
            # Fetch template, and auto-seed if missing
            template = session.exec(
                select(LiturgicalTemplate).where(LiturgicalTemplate.name == "Göttliche Liturgie des Hl. Johannes Chrysostomus")
            ).first()
            
            if not template:
                from backend.app.seed_liturgy import seed_database
                seed_database()
                template = session.exec(
                    select(LiturgicalTemplate).where(LiturgicalTemplate.name == "Göttliche Liturgie des Hl. Johannes Chrysostomus")
                ).first()
            
            if template:
                target_date = datetime(2026, 7, 19, 10, 0, 0, tzinfo=timezone.utc)
                service = LiturgicalService(
                    template_id=template.id,
                    community_id=community.id,
                    scheduled_time=target_date,
                    status="scheduled",
                    active_languages=["de", "cu"]
                )
                session.add(service)
                session.commit()
                session.refresh(service)

        # Check and auto-generate audio tracks if missing from DB (e.g. database reset by tests)
        tracks_exist = session.exec(select(AudioTrack)).first() is not None
        if not tracks_exist:
            from backend.app.scratch.generate_all_liturgy_audio import generate_all_tracks
            generate_all_tracks()
        
        service_id = str(service.id) if service else "a7b2a9ed-faa7-4635-b6f0-2ec3428f4d63"

    html_content = r"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LiturgyBridge - Companion</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0b0c10;
            --accent-color: #d4af37; /* Liturgical Gold */
            --accent-hover: #f3e5ab;
            --glass-bg: rgba(20, 24, 33, 0.6);
            --glass-border: rgba(255, 255, 255, 0.08);
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
            --slavonic-color: #f59e0b; /* Warm Gold */
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #090a0f 0%, #151821 50%, #0d0e12 100%);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            overflow-x: hidden;
            padding-bottom: 120px;
        }

        /* Glowing background blobs */
        .blob {
            position: absolute;
            width: 400px;
            height: 400px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(212, 175, 55, 0.05) 0%, rgba(212, 175, 55, 0) 70%);
            z-index: 0;
            pointer-events: none;
        }
        .blob-1 { top: 10%; left: -10%; }
        .blob-2 { bottom: 20%; right: -10%; }

        header {
            position: relative;
            width: 100%;
            max-width: 900px;
            padding: 40px 20px 20px 20px;
            text-align: center;
            z-index: 10;
        }

        h1 {
            font-family: 'Playfair Display', serif;
            font-size: 2.5rem;
            font-weight: 600;
            background: linear-gradient(135deg, #fff 30%, var(--accent-color) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
            letter-spacing: 0.5px;
        }

        .meta-subtitle {
            font-size: 0.95rem;
            color: var(--text-muted);
            letter-spacing: 1px;
            text-transform: uppercase;
            font-weight: 500;
        }

        main {
            position: relative;
            width: 100%;
            max-width: 900px;
            padding: 20px;
            z-index: 10;
        }

        /* Accordion Cards */
        .card {
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            margin-bottom: 16px;
            overflow: hidden;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        }

        .card:hover {
            border-color: rgba(212, 175, 55, 0.3);
            box-shadow: 0 12px 40px 0 rgba(212, 175, 55, 0.05);
            transform: translateY(-2px);
        }

        .card-header {
            padding: 20px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            cursor: pointer;
            user-select: none;
        }

        .card-header-left {
            display: flex;
            align-items: center;
            gap: 16px;
            flex-grow: 1;
        }

        .index-badge {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: var(--accent-color);
            width: 32px;
            height: 32px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.85rem;
            font-weight: 600;
        }

        .section-title {
            font-family: 'Playfair Display', serif;
            font-size: 1.15rem;
            font-weight: 600;
            color: var(--text-main);
        }

        .card-header-controls {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        /* Buttons styling */
        .btn-circle {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            border: 1px solid rgba(255, 255, 255, 0.12);
            background: rgba(255, 255, 255, 0.03);
            color: var(--text-main);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .btn-circle:hover {
            background: rgba(212, 175, 55, 0.15);
            border-color: var(--accent-color);
            color: var(--accent-color);
            transform: scale(1.05);
        }

        .btn-circle svg {
            width: 16px;
            height: 16px;
            fill: currentColor;
        }

        .btn-circle.playing {
            background: var(--accent-color);
            border-color: var(--accent-color);
            color: #000;
            animation: pulse-gold 2s infinite;
        }

        .btn-circle.playing:hover {
            background: var(--accent-hover);
        }

        .btn-circle.pending {
            border: 1px dashed rgba(255, 255, 255, 0.25) !important;
            background: transparent !important;
            opacity: 0.45;
            cursor: not-allowed !important;
            color: var(--text-muted) !important;
        }
        .btn-circle.pending:hover {
            transform: none !important;
        }

        /* Role Badges */
        .role-badge {
            font-size: 0.68rem;
            font-weight: 600;
            padding: 1px 7px;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            display: inline-flex;
            align-items: center;
        }
        .role-priest {
            background: rgba(212, 175, 55, 0.08);
            color: var(--accent-color);
            border: 1px solid rgba(212, 175, 55, 0.2);
        }
        .role-choir {
            background: rgba(59, 130, 246, 0.08);
            color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.2);
        }
        .role-congregation {
            background: rgba(16, 185, 129, 0.08);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.2);
        }
        .role-dialogue {
            background: rgba(139, 92, 246, 0.08);
            color: #a78bfa;
            border: 1px solid rgba(139, 92, 246, 0.2);
        }

        @keyframes pulse-gold {
            0% { box-shadow: 0 0 0 0 rgba(212, 175, 55, 0.4); }
            70% { box-shadow: 0 0 0 10px rgba(212, 175, 55, 0); }
            100% { box-shadow: 0 0 0 0 rgba(212, 175, 55, 0); }
        }

        .arrow-icon {
            font-size: 0.8rem;
            color: var(--text-muted);
            transition: transform 0.3s ease;
        }

        .card.expanded .arrow-icon {
            transform: rotate(180deg);
        }

        /* Card Content Parallel Columns */
        .card-content {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
            background: rgba(0, 0, 0, 0.15);
            border-top: 1px solid rgba(255, 255, 255, 0.02);
        }

        .card.expanded .card-content {
            max-height: 1500px; /* Adjust if needed */
        }

        .columns-container {
            padding: 24px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }

        @media (max-width: 768px) {
            .columns-container {
                grid-template-columns: 1fr;
                gap: 20px;
            }
        }

        .column {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .column-header {
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-muted);
            font-weight: 600;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding-bottom: 6px;
        }

        .text-slavonic {
            font-family: 'Playfair Display', serif;
            font-size: 1.15rem;
            line-height: 1.6;
            color: var(--slavonic-color);
            letter-spacing: 0.2px;
        }

        .text-german {
            font-size: 1rem;
            line-height: 1.6;
            color: #d1d5db;
        }

        /* Global Floating Player Dashboard */
        .player-bar {
            position: fixed;
            bottom: -100px;
            left: 50%;
            transform: translateX(-50%);
            width: 90%;
            max-width: 800px;
            height: 80px;
            background: rgba(15, 20, 28, 0.85);
            backdrop-filter: blur(24px);
            -webkit-backdrop-filter: blur(24px);
            border: 1px solid rgba(212, 175, 55, 0.2);
            border-radius: 20px;
            z-index: 100;
            box-shadow: 0 10px 40px 0 rgba(0, 0, 0, 0.6);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 24px;
            transition: bottom 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
        }

        .player-bar.active {
            bottom: 24px;
        }

        .player-info {
            display: flex;
            flex-direction: column;
            gap: 4px;
            width: 25%;
        }

        .player-info-title {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--accent-color);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .player-info-status {
            font-size: 0.75rem;
            color: var(--text-muted);
        }

        .player-controls {
            display: flex;
            align-items: center;
            gap: 16px;
            width: 50%;
            justify-content: center;
        }

        /* Seek Bar Slider */
        .seek-container {
            display: flex;
            align-items: center;
            gap: 10px;
            width: 100%;
        }

        .seek-time {
            font-size: 0.75rem;
            color: var(--text-muted);
            min-width: 35px;
            text-align: center;
        }

        .slider {
            -webkit-appearance: none;
            width: 100%;
            height: 4px;
            border-radius: 2px;
            background: rgba(255, 255, 255, 0.1);
            outline: none;
            cursor: pointer;
            transition: background 0.3s;
        }

        .slider:hover {
            background: rgba(255, 255, 255, 0.2);
        }

        .slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: var(--accent-color);
            cursor: pointer;
            box-shadow: 0 0 10px rgba(212, 175, 55, 0.5);
            transition: transform 0.1s;
        }

        .slider::-webkit-slider-thumb:hover {
            transform: scale(1.2);
        }

        .player-options {
            display: flex;
            align-items: center;
            gap: 16px;
            justify-content: flex-end;
            width: 25%;
        }

        .speed-badge {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-main);
            cursor: pointer;
            user-select: none;
            transition: all 0.2s ease;
        }

        .speed-badge:hover {
            border-color: var(--accent-color);
            color: var(--accent-color);
        }

        .volume-container {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .volume-icon {
            color: var(--text-muted);
            cursor: pointer;
        }

        .volume-slider {
            width: 60px;
        }
    </style>
</head>
<body>
    <div class="blob blob-1"></div>
    <div class="blob blob-2"></div>

    <header>
        <h1 id="service-name">Gottesdienst-Begleiter</h1>
        <div class="meta-subtitle" id="service-date">LÄDT VERBINDUNG...</div>
    </header>

    <main id="liturgy-container">
        <!-- Dynamic Cards Inserted Here -->
    </main>

    <!-- Quellenverzeichnis / Bibliographie -->
    <section id="bibliography-container" style="width: 100%; max-width: 900px; padding: 0 20px 20px 20px; z-index: 10; margin-top: 10px;">
        <div style="background: var(--glass-bg); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border: 1px solid var(--glass-border); border-radius: 16px; padding: 24px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);">
            <h2 style="font-family: 'Playfair Display', serif; font-weight: 600; font-size: 1.3rem; color: var(--accent-color); margin-top: 0; margin-bottom: 16px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 10px;">Quellenverzeichnis / Bibliographie</h2>
            <ul id="bibliography-list" style="list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 12px; font-size: 0.88rem; color: var(--text-muted); line-height: 1.4;">
                <!-- Dynamic Bibliography Items Inserted Here -->
            </ul>
        </div>
    </section>

    <!-- Floating Audio Dashboard -->
    <div class="player-bar" id="global-player">
        <div class="player-info">
            <div class="player-info-title" id="player-title">Kein Titel</div>
            <div class="player-info-status" id="player-status">Bereit</div>
        </div>

        <div class="player-controls">
            <button class="btn-circle" id="player-play-btn" title="Abspielen/Pause">
                <svg viewBox="0 0 24 24" id="play-svg"><path d="M8 5v14l11-7z"/></svg>
                <svg viewBox="0 0 24 24" id="pause-svg" style="display:none;"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
            </button>
            <button class="btn-circle" id="player-stop-btn" title="Stoppen">
                <svg viewBox="0 0 24 24"><path d="M6 6h12v12H6z"/></svg>
            </button>

            <div class="seek-container">
                <span class="seek-time" id="time-current">0:00</span>
                <input type="range" class="slider" id="seek-slider" min="0" max="100" value="0">
                <span class="seek-time" id="time-total">0:00</span>
            </div>
        </div>

        <div class="player-options">
            <div class="speed-badge" id="speed-btn" title="Geschwindigkeit ändern">1.0x</div>
            <div class="volume-container">
                <span class="volume-icon" id="volume-btn">🔊</span>
                <input type="range" class="slider volume-slider" id="volume-slider" min="0" max="100" value="80">
            </div>
        </div>
    </div>

    <script>
        const container = document.getElementById("liturgy-container");
        
        let audioPlayer = new Audio();
        let currentPlayingKey = null;
        let playList = [];
        let playbackSpeeds = [1.0, 1.25, 1.5];
        let currentSpeedIndex = 0;

        // Initialize Audio player volume
        audioPlayer.volume = 0.8;

        // Load Service Details from API
        async function loadLiturgy() {
            try {
                // Resolve the latest service ID dynamically
                const latestRes = await fetch("/api/v1/liturgy/services/latest");
                if (!latestRes.ok) throw new Error("Latest service not found");
                const latestService = await latestRes.json();
                const serviceId = latestService.id;

                const response = await fetch(`/api/v1/liturgy/services/${serviceId}?languages=de,cu`);
                if (!response.ok) throw new Error("Laden fehlgeschlagen");
                const data = await response.json();
                
                // Set Header Metadata
                document.getElementById("service-name").textContent = data.template.name;
                const dateObj = new Date(data.service.scheduled_time);
                document.getElementById("service-date").textContent = `Sonntag, ${dateObj.toLocaleDateString("de-DE", {day:"numeric", month:"long", year:"numeric"})}`;

                // Populate Liturgy Cards
                container.innerHTML = "";
                playList = [];
                
                let index = 1;
                data.template.structure.sections.forEach(sec => {
                    const sectionKey = sec.section_key;
                    sec.text_keys.forEach(key => {
                        const textItem = data.texts[key];
                        if (!textItem) return;

                        const slavonicText = textItem.translations.cu || "";
                        const germanText = textItem.translations.de || "";
                        const audioUrl = textItem.audio_url || "";
                        
                        // Parse source indexes
                        const cuSourceIdx = (textItem.translation_source_indices && textItem.translation_source_indices.cu) ? textItem.translation_source_indices.cu : "";
                        const deSourceIdx = (textItem.translation_source_indices && textItem.translation_source_indices.de) ? textItem.translation_source_indices.de : "";

                        const cuSourceText = cuSourceIdx ? (data.sources_bibliography[cuSourceIdx] || "") : "";
                        const deSourceText = deSourceIdx ? (data.sources_bibliography[deSourceIdx] || "") : "";

                        const cuSourceLabel = cuSourceIdx ? `<span title="${cuSourceText}" style="font-size: 0.75rem; color: var(--accent-color); margin-left: 4px; vertical-align: super; font-weight: bold; cursor: help;">[${cuSourceIdx}]</span>` : "";
                        const deSourceLabel = deSourceIdx ? `<span title="${deSourceText}" style="font-size: 0.75rem; color: var(--accent-color); margin-left: 4px; vertical-align: super; font-weight: bold; cursor: help;">[${deSourceIdx}]</span>` : "";

                        const title = formatKeyTitle(key);
                        const roles = getLiturgicalRoles(key);
                        const rolesHtml = roles.map(r => `<span class="role-badge ${r.class}">${r.text}</span>`).join(" ");

                        // Parse theological explanation
                        let explanationHtml = "";
                        let infoIconHtml = "";
                        if (textItem.explanation) {
                            infoIconHtml = `<span title="Theologische Bedeutung: ${textItem.explanation.title}" style="font-size: 0.85rem; color: var(--accent-color); cursor: help; margin-left: 6px;">ℹ️</span>`;
                            explanationHtml = `
                                <div style="padding: 20px 24px 0 24px;">
                                    <div style="background: rgba(214, 175, 55, 0.05); border: 1px dashed rgba(214, 175, 55, 0.2); border-radius: 12px; padding: 16px; font-size: 0.88rem; line-height: 1.5; color: #f3e5ab;">
                                        <div style="display: flex; align-items: center; gap: 8px; font-weight: 600; margin-bottom: 6px; color: var(--accent-color); font-family: 'Playfair Display', serif; font-size: 0.95rem;">
                                            <span style="font-size: 1rem;">ℹ️</span> Theologische Bedeutung: ${textItem.explanation.title}
                                        </div>
                                        <div style="color: #d1d5db;">${textItem.explanation.description}</div>
                                    </div>
                                </div>
                            `;
                        }

                        const card = document.createElement("div");
                        card.className = "card";
                        card.id = `card-${key}`;
                        
                        card.innerHTML = `
                            <div class="card-header" onclick="toggleCard('${key}')">
                                <div class="card-header-left">
                                    <div class="index-badge">${index}</div>
                                    <div style="display: flex; flex-direction: column; gap: 4px; align-items: flex-start;">
                                        <div style="display: flex; align-items: center; gap: 4px;">
                                            <div class="section-title">${title}</div>
                                            ${infoIconHtml}
                                        </div>
                                        <div style="display: flex; gap: 6px; flex-wrap: wrap;">${rolesHtml}</div>
                                    </div>
                                </div>
                                <div class="card-header-controls" onclick="event.stopPropagation()">
                                    ${audioUrl ? `
                                    <button class="btn-circle" id="play-${key}" onclick="playAudio('${key}', '${audioUrl}', '${title}')" title="Audio anhören">
                                        <svg class="play-svg-card" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                                        <svg class="pause-svg-card" viewBox="0 0 24 24" style="display:none;"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
                                    </button>
                                    ` : `
                                    <button class="btn-circle pending" title="Audio ausstehend (noch nicht generiert)">
                                        <svg class="play-svg-card" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                                    </button>
                                    `}
                                    <span class="arrow-icon">▼</span>
                                </div>
                            </div>
                            <div class="card-content">
                                ${explanationHtml}
                                <div class="columns-container">
                                    <div class="column">
                                        <div class="column-header">Kirchenslawisch (cu)${cuSourceLabel}</div>
                                        <div class="text-slavonic">${slavonicText}</div>
                                    </div>
                                    <div class="column">
                                        <div class="column-header">Deutsch (de)${deSourceLabel}</div>
                                        <div class="text-german">${germanText}</div>
                                    </div>
                                </div>
                            </div>
                        `;
                        
                        container.appendChild(card);
                        playList.push({ key, title, audioUrl });
                        index++;
                    });
                });

                // Populate Sources Bibliography
                const bibList = document.getElementById("bibliography-list");
                if (bibList && data.sources_bibliography) {
                    bibList.innerHTML = "";
                    Object.entries(data.sources_bibliography).forEach(([idx, text]) => {
                        const li = document.createElement("li");
                        li.style.display = "flex";
                        li.style.gap = "8px";
                        li.innerHTML = `<span style="color: var(--accent-color); font-weight: 600; min-width: 25px;">[${idx}]</span> <span>${text}</span>`;
                        bibList.appendChild(li);
                    });
                }
            } catch (err) {
                console.error(err);
                document.getElementById("service-date").textContent = "FEHLER BEIM VERBINDUNGSAUFBAU";
            }
        }

        const titleTranslations = {
            "opening_blessing": "Eröffnungssegen",
            "great_litany": "Große Ektenie",
            "first_antiphon": "Erstes Antiphon",
            "small_litany_1": "Erste Kleine Ektenie",
            "second_antiphon": "Zweites Antiphon",
            "small_litany_2": "Zweite Kleine Ektenie",
            "third_antiphon": "Drittes Antiphon (Seligpreisungen)",
            "small_entrance": "Kleiner Einzug",
            "tonal_troparion": "Troparion des Tages",
            "trisagion": "Dreimalheilig-Hymnus (Trisagion)",
            "tonal_prokeimenon": "Prokeimenon des Tages",
            "epistle_reading": "Epistellesung (Apostelgeschichte/Briefe)",
            "alleluia_ref": "Halleluja-Vers",
            "gospel_reading": "Evangelienlesung",
            "sermon_placeholder": "Predigt",
            "cherubic_hymn": "Cherubim-Hymnus",
            "litany_supplication": "Ektenie der Rüstung",
            "creed": "Glaubensbekenntnis",
            "anaphora.dialogue": "Eucharistisches Hochgebet (Dialog)",
            "anaphora.sanctus": "Sanctus (Heilig-Ruf)",
            "anaphora.institution": "Einsetzungsworte",
            "anaphora.epiklesis": "Epiklesis (Herabrufung des Heiligen Geistes)",
            "hymn_to_theotokos": "Muttergottes-Hymnus (Axion Estin)",
            "lords_prayer": "Vaterunser",
            "communion.elevation": "Erhebung der heiligen Gaben",
            "communion.response": "Antwort des Chores",
            "communion.koinonikon": "Kommuniongesang (Koinonikon)",
            "communion.invitation": "Einladung zur Kommunion",
            "communion.post_communion": "Danksagung nach der Kommunion",
            "thanksgiving_hymn": "Dankhymnus",
            "prayer_ambo": "Gebet hinter dem Ambo",
            "dismissal": "Entlassung"
        };

        function getLiturgicalRoles(key) {
            const priestKeys = [
                "opening_blessing", 
                "sermon_placeholder", 
                "communion.elevation", 
                "prayer_ambo"
            ];
            const choirKeys = [
                "first_antiphon", 
                "second_antiphon", 
                "third_antiphon", 
                "tonal_troparion", 
                "alleluia_ref", 
                "cherubic_hymn", 
                "anaphora.sanctus", 
                "communion.response", 
                "communion.koinonikon", 
                "communion.post_communion", 
                "thanksgiving_hymn"
            ];
            const congregationKeys = [
                "creed", 
                "lords_prayer"
            ];
            const dialogueKeys = [
                "great_litany", 
                "small_litany_1", 
                "small_litany_2", 
                "small_entrance", 
                "trisagion", 
                "tonal_prokeimenon", 
                "epistle_reading", 
                "gospel_reading", 
                "litany_supplication", 
                "anaphora.dialogue", 
                "anaphora.institution", 
                "anaphora.epiklesis", 
                "hymn_to_theotokos", 
                "communion.invitation", 
                "dismissal"
            ];

            for (const k of priestKeys) {
                if (key.includes(k)) return [{ text: "Priester", class: "role-priest" }];
            }
            for (const k of choirKeys) {
                if (key.includes(k)) return [{ text: "Chor", class: "role-choir" }];
            }
            for (const k of congregationKeys) {
                if (key.includes(k)) return [{ text: "Gemeinde", class: "role-congregation" }];
            }
            for (const k of dialogueKeys) {
                if (key.includes(k)) return [{ text: "Wechselgesang", class: "role-dialogue" }];
            }
            return [];
        }

        function formatKeyTitle(key) {
            // Find traditional German translation
            for (const [k, translation] of Object.entries(titleTranslations)) {
                if (key.includes(k)) {
                    return translation;
                }
            }
            // Fallback
            const parts = key.split(".");
            let name = parts[parts.length - 1];
            if (name === "main" && parts.length > 2) {
                name = parts[parts.length - 2];
            }
            return name
                .replace(/_/g, " ")
                .replace(/\b\w/g, c => c.toUpperCase());
        }

        // Toggle Accordion Collapse/Expand
        window.toggleCard = function(key) {
            const card = document.getElementById(`card-${key}`);
            card.classList.toggle("expanded");
        }

        // Play/Pause Audio Tracks
        window.playAudio = function(key, audioUrl, title) {
            const cardPlayBtn = document.getElementById(`play-${key}`);
            const globalPlayBtn = document.getElementById("player-play-btn");
            const playSvg = document.getElementById("play-svg");
            const pauseSvg = document.getElementById("pause-svg");

            if (currentPlayingKey === key) {
                // If clicked the currently playing track -> Toggle Play/Pause
                if (audioPlayer.paused) {
                    audioPlayer.play();
                } else {
                    audioPlayer.pause();
                }
                return;
            }

            // If a different track is requested -> Reset previous UI play states
            if (currentPlayingKey) {
                resetCardUI(currentPlayingKey);
            }

            // Set new active track
            currentPlayingKey = key;
            audioPlayer.src = audioUrl;
            audioPlayer.playbackRate = playbackSpeeds[currentSpeedIndex];
            
            // Set Player Bar Active
            document.getElementById("global-player").classList.add("active");
            document.getElementById("player-title").textContent = title;
            document.getElementById("player-status").textContent = "Ladet...";

            // Toggle Card Play Button UI to Playing state
            cardPlayBtn.classList.add("playing");
            cardPlayBtn.querySelector(".play-svg-card").style.display = "none";
            cardPlayBtn.querySelector(".pause-svg-card").style.display = "block";

            // Expand playing card for parallel text visibility
            const card = document.getElementById(`card-${key}`);
            card.classList.add("expanded");

            audioPlayer.play();
        }

        function resetCardUI(key) {
            const btn = document.getElementById(`play-${key}`);
            if (btn) {
                btn.classList.remove("playing");
                btn.querySelector(".play-svg-card").style.display = "block";
                btn.querySelector(".pause-svg-card").style.display = "none";
            }
        }

        // HTML5 Audio Event Listeners for Sync
        audioPlayer.addEventListener("play", () => {
            document.getElementById("player-status").textContent = "Spielt";
            // Set Play/Pause SVG inside global control
            document.getElementById("play-svg").style.display = "none";
            document.getElementById("pause-svg").style.display = "block";

            if (currentPlayingKey) {
                const btn = document.getElementById(`play-${currentPlayingKey}`);
                if (btn) {
                    btn.querySelector(".play-svg-card").style.display = "none";
                    btn.querySelector(".pause-svg-card").style.display = "block";
                }
            }
        });

        audioPlayer.addEventListener("pause", () => {
            document.getElementById("player-status").textContent = "Pausiert";
            document.getElementById("play-svg").style.display = "block";
            document.getElementById("pause-svg").style.display = "none";

            if (currentPlayingKey) {
                const btn = document.getElementById(`play-${currentPlayingKey}`);
                if (btn) {
                    btn.querySelector(".play-svg-card").style.display = "block";
                    btn.querySelector(".pause-svg-card").style.display = "none";
                }
            }
        });

        audioPlayer.addEventListener("ended", () => {
            stopAudio();
            // Automatically play next track in playlist for continuous guide!
            const currentIndex = playList.findIndex(item => item.key === currentPlayingKey);
            if (currentIndex !== -1 && currentIndex + 1 < playList.length) {
                const nextTrack = playList[currentIndex + 1];
                if (nextTrack.audioUrl) {
                    playAudio(nextTrack.key, nextTrack.audioUrl, nextTrack.title);
                }
            }
        });

        function stopAudio() {
            audioPlayer.pause();
            audioPlayer.currentTime = 0;
            if (currentPlayingKey) {
                resetCardUI(currentPlayingKey);
                currentPlayingKey = null;
            }
            document.getElementById("global-player").classList.remove("active");
            document.getElementById("play-svg").style.display = "block";
            document.getElementById("pause-svg").style.display = "none";
        }

        // Global Player Event Controls
        document.getElementById("player-play-btn").addEventListener("click", () => {
            if (audioPlayer.paused) {
                audioPlayer.play();
            } else {
                audioPlayer.pause();
            }
        });

        document.getElementById("player-stop-btn").addEventListener("click", stopAudio);

        // Progress bar updates
        const seekSlider = document.getElementById("seek-slider");
        const timeCurrent = document.getElementById("time-current");
        const timeTotal = document.getElementById("time-total");

        audioPlayer.addEventListener("timeupdate", () => {
            if (!isNaN(audioPlayer.duration)) {
                const pct = (audioPlayer.currentTime / audioPlayer.duration) * 100;
                seekSlider.value = pct;
                timeCurrent.textContent = formatTime(audioPlayer.currentTime);
                timeTotal.textContent = formatTime(audioPlayer.duration);
            }
        });

        seekSlider.addEventListener("input", () => {
            if (!isNaN(audioPlayer.duration)) {
                const newTime = (seekSlider.value / 100) * audioPlayer.duration;
                audioPlayer.currentTime = newTime;
            }
        });

        function formatTime(secs) {
            const m = Math.floor(secs / 60);
            const s = Math.floor(secs % 60);
            return `${m}:${s < 10 ? '0' : ''}${s}`;
        }

        // Playback Speed Controller
        const speedBtn = document.getElementById("speed-btn");
        speedBtn.addEventListener("click", () => {
            currentSpeedIndex = (currentSpeedIndex + 1) % playbackSpeeds.length;
            const newSpeed = playbackSpeeds[currentSpeedIndex];
            speedBtn.textContent = `${newSpeed.toFixed(2)}x`;
            audioPlayer.playbackRate = newSpeed;
        });

        // Volume controls
        const volumeSlider = document.getElementById("volume-slider");
        const volumeBtn = document.getElementById("volume-btn");

        volumeSlider.addEventListener("input", () => {
            audioPlayer.volume = volumeSlider.value / 100;
            if (audioPlayer.volume === 0) {
                volumeBtn.textContent = "🔇";
            } else if (audioPlayer.volume < 0.5) {
                volumeBtn.textContent = "🔉";
            } else {
                volumeBtn.textContent = "🔊";
            }
        });

        let lastVolume = 0.8;
        volumeBtn.addEventListener("click", () => {
            if (audioPlayer.volume > 0) {
                lastVolume = audioPlayer.volume;
                audioPlayer.volume = 0;
                volumeSlider.value = 0;
                volumeBtn.textContent = "🔇";
            } else {
                audioPlayer.volume = lastVolume;
                volumeSlider.value = lastVolume * 100;
                volumeBtn.textContent = lastVolume < 0.5 ? "🔉" : "🔊";
            }
        });

        // Load content on page initialization
        window.addEventListener("DOMContentLoaded", loadLiturgy);
    </script>
</body>
</html>"""
    return HTMLResponse(
        content=html_content,
        status_code=200,
        headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"}
    )
