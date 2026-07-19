<template>
  <div class="relative min-h-screen pb-32 flex flex-col items-center">
    <!-- Glowing background blobs -->
    <div class="blob blob-1"></div>
    <div class="blob blob-2"></div>

    <!-- Header -->
    <header class="relative w-full max-w-4xl px-6 pt-10 pb-4 text-center z-10">
      <div class="flex flex-col sm:flex-row items-center justify-between gap-4 mb-6">
        <!-- Logo and Title -->
        <div class="text-left flex flex-col gap-1.5">
          <h1 class="font-serif text-3xl sm:text-4xl font-semibold bg-gradient-to-r from-white to-amber-500 bg-clip-text text-transparent">
            {{ serviceName || 'Gottesdienst-Begleiter' }}
          </h1>
          
          <div class="flex items-center gap-3 flex-wrap">
            <p class="text-xs sm:text-sm text-gray-400 uppercase tracking-wider font-semibold">
              {{ serviceDate || 'LÄDT VERBINDUNG...' }}
            </p>
            
            <!-- Service Selector Dropdown -->
            <div v-if="servicesList.length > 0" class="flex items-center gap-1.5 bg-slate-950/60 border border-white/5 rounded-lg px-2.5 py-1">
              <span class="text-[10px] text-gray-500 uppercase font-semibold">Wechseln:</span>
              <select 
                v-model="serviceId" 
                @change="loadLiturgyDetails" 
                class="bg-transparent text-xs text-amber-500 font-semibold focus:outline-none cursor-pointer"
              >
                <option v-for="srv in sortedServices" :key="srv.id" :value="srv.id" class="bg-slate-950 text-white">
                  {{ formatServiceOption(srv) }}
                </option>
              </select>
            </div>

            <!-- Schedule Service Button (Priest / Admin Only) -->
            <button 
              v-if="isPriest || isAdmin" 
              @click="openScheduleModal" 
              class="bg-amber-500/10 border border-amber-500/30 text-amber-500 hover:bg-amber-500/20 text-[10px] uppercase font-bold py-1 px-2.5 rounded-lg transition-all"
              title="Neuen Gottesdienst planen"
            >
              📅 Planen
            </button>
          </div>
        </div>

        <!-- Auth and Language Controls -->
        <div class="flex items-center gap-3 flex-wrap">
          <!-- Target Language Select -->
          <div class="flex items-center gap-2 bg-slate-900/60 border border-white/10 rounded-xl px-3 py-2">
            <span class="text-xs text-gray-400 uppercase font-semibold">Sprache:</span>
            <select v-model="targetLanguage" @change="onLanguageChange" class="bg-transparent text-sm text-white font-medium focus:outline-none cursor-pointer">
              <option value="de" class="bg-slate-950 text-white">Deutsch (de)</option>
              <option value="en" class="bg-slate-950 text-white">English (en)</option>
              <option value="ru" class="bg-slate-950 text-white">Русский (ru)</option>
              <option value="uk" class="bg-slate-950 text-white">Українська (uk)</option>
            </select>
          </div>

          <!-- SSO User Identity State -->
          <div v-if="user" class="flex items-center gap-2 bg-slate-900/80 border border-amber-500/20 rounded-xl px-3 py-2">
            <div class="flex flex-col text-left">
              <span class="text-[10px] text-gray-400 leading-tight">Eingeloggt als</span>
              <span class="text-xs font-bold text-amber-500 leading-tight">{{ user.name }}</span>
            </div>
            <div class="flex gap-1">
              <span v-if="isPriest" class="text-[9px] bg-amber-500/10 text-amber-500 border border-amber-500/20 px-1 rounded uppercase font-bold">Priester</span>
              <span v-if="isAdmin" class="text-[9px] bg-blue-500/10 text-blue-400 border border-blue-500/20 px-1 rounded uppercase font-bold">Admin</span>
            </div>
            <button @click="logout" class="ml-2 text-xs text-gray-400 hover:text-red-400 transition-colors" title="Ausloggen">
              🚪
            </button>
          </div>

          <!-- Login Button -->
          <button v-else @click="loginWithNextcloud" class="bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-black text-xs font-bold py-2.5 px-4 rounded-xl shadow-lg shadow-amber-500/10 transition-all transform hover:-translate-y-0.5 active:translate-y-0">
            Priester Login (Nextcloud)
          </button>
        </div>
      </div>

      <!-- Priest Control Panel -->
      <div v-if="isPriest || isAdmin" class="w-full bg-slate-900/60 backdrop-blur-xl border border-amber-500/30 rounded-2xl p-5 mb-8 text-left shadow-2xl">
        <!-- Sermon Editor Collapsible -->
        <div>
          <button @click="showSermonEditor = !showSermonEditor" class="text-xs text-amber-500 hover:underline flex items-center gap-1">
            <span>{{ showSermonEditor ? '▼' : '▶' }}</span> Predigt für Sonntag editieren (Übersetzungen & Audio generieren)
          </button>
          
          <div v-if="showSermonEditor" class="mt-3 flex flex-col gap-3">
            <textarea v-model="sermonText" placeholder="Predigttext hier eingeben... (Wird automatisch in alle Zielsprachen übersetzt und Audio generiert)" class="w-full h-32 bg-slate-950/80 border border-white/10 rounded-xl p-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-amber-500/50 resize-y"></textarea>
            <div class="flex items-center justify-between">
              <span class="text-xs text-gray-400">Zielsprache für den Editor: Deutsch (de)</span>
              <button @click="saveSermon" :disabled="savingSermon" class="bg-amber-500 text-black text-xs font-bold py-2 px-4 rounded-lg hover:bg-amber-400 transition-colors disabled:opacity-50">
                {{ savingSermon ? 'Speichert & übersetzt...' : 'Predigt speichern & Audio generieren' }}
              </button>
            </div>
          </div>
        </div>
      </div>


    </header>

    <!-- Main Content -->
    <main class="relative w-full max-w-4xl px-4 z-10 flex-grow">
      <div v-if="loading" class="flex flex-col items-center justify-center py-20 gap-3">
        <div class="animate-spin rounded-full h-10 w-10 border-2 border-t-amber-500 border-r-transparent border-b-transparent border-l-transparent"></div>
        <p class="text-sm text-gray-400">Lade Liturgie...</p>
      </div>

      <div v-else-if="error" class="text-center py-20">
        <p class="text-red-400">{{ error }}</p>
        <button @click="loadLiturgy" class="mt-4 bg-slate-800 text-white text-xs py-2 px-4 rounded-lg hover:bg-slate-700">Erneut versuchen</button>
      </div>

      <div v-else class="flex flex-col gap-4">
        <!-- Liturgical Section Cards -->
        <div 
          v-for="(item, idx) in listItems" 
          :key="item.key"
          :id="'card-' + item.key"
          class="card group"
          :class="[
            activeSectionKey === item.key ? 'active-step border-amber-500/50 shadow-amber-500/5' : '',
            expandedCards.has(item.key) ? 'expanded' : ''
          ]"
        >
          <!-- Card Header -->
          <div @click="toggleCard(item.key)" class="flex items-center justify-between p-5 cursor-pointer user-select-none">
            <div class="flex items-center gap-4 flex-grow">
              <!-- Index Badge -->
              <div class="index-badge">
                {{ idx + 1 }}
              </div>
              
              <!-- Title and Roles -->
              <div class="flex flex-col items-start gap-1">
                <div class="flex items-center gap-1.5 flex-wrap">
                  <span class="font-serif text-lg font-semibold text-gray-100 group-hover:text-white transition-colors">
                    {{ formatKeyTitle(item.key) }}
                  </span>
                  <!-- Info Icon -->
                  <span 
                    v-if="item.explanation"
                    :title="'Theologische Bedeutung: ' + item.explanation.title"
                    class="text-xs text-amber-500 opacity-80 hover:opacity-100 cursor-help transition-opacity"
                    @click.stop="toggleCard(item.key)"
                  >
                    ℹ️
                  </span>
                </div>
                <div class="flex gap-1.5 flex-wrap">
                  <span 
                    v-for="role in getLiturgicalRoles(item.key)" 
                    :key="role.text"
                    class="role-badge"
                    :class="role.class"
                  >
                    {{ role.text }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Audio and Expand Controls -->
            <div class="flex items-center gap-3" @click.stop>
              <!-- Card Audio Play Button -->
              <button 
                v-if="item.audio_url" 
                @click="playAudio(item.key, item.audio_url, formatKeyTitle(item.key))"
                class="btn-circle"
                :class="currentPlayingKey === item.key && isPlaying ? 'playing' : ''"
                :title="currentPlayingKey === item.key && isPlaying ? 'Stoppen' : 'Audio anhören'"
              >
                <svg v-if="currentPlayingKey === item.key && isPlaying" viewBox="0 0 24 24" class="w-4 h-4 fill-black"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
                <svg v-else viewBox="0 0 24 24" class="w-4 h-4 fill-current"><path d="M8 5v14l11-7z"/></svg>
              </button>
              <button 
                v-else
                class="btn-circle pending cursor-not-allowed opacity-30" 
                title="Audio ausstehend (noch nicht generiert)"
              >
                <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current"><path d="M8 5v14l11-7z"/></svg>
              </button>

              <!-- Collapse Arrow -->
              <span class="arrow-icon text-gray-400 group-hover:text-white transition-transform duration-300" :class="expandedCards.has(item.key) ? 'rotate-180' : ''">
                ▼
              </span>
            </div>
          </div>

          <!-- Card Content (Parallel Columns) -->
          <div v-show="expandedCards.has(item.key)" class="card-content border-t border-white/5 bg-black/15">
            <!-- Theological Explanation Banner -->
            <div v-if="item.explanation" class="p-5 pb-0">
              <div class="bg-amber-500/[0.03] border border-amber-500/20 rounded-xl p-4 text-sm leading-relaxed text-amber-200/90 font-light shadow-inner">
                <div class="flex items-center gap-2 font-semibold mb-1.5 text-amber-500 font-serif">
                  <span>ℹ️</span> Theologische Bedeutung: {{ item.explanation.title }}
                </div>
                <div class="text-gray-300">{{ item.explanation.description }}</div>
              </div>
            </div>

            <!-- Parallel Columns -->
            <div class="p-6 grid grid-cols-1 md:grid-cols-2 gap-8">
              <!-- Left Column: Slavonic -->
              <div class="flex flex-col gap-2 text-left">
                <div class="text-xs uppercase tracking-wider font-semibold text-gray-500 border-b border-white/5 pb-1 flex items-center justify-between">
                  <span>Kirchenslawisch (cu)</span>
                  <span v-if="item.translation_source_indices && item.translation_source_indices.cu" :title="sourcesBibliography[item.translation_source_indices.cu]" class="text-[10px] text-amber-500 hover:underline cursor-help">
                    Source [{{ item.translation_source_indices.cu }}]
                  </span>
                </div>
                <div class="font-serif text-lg leading-relaxed text-amber-500/90 whitespace-pre-line tracking-wide">
                  {{ item.translations.cu || 'Kein kirchenslawischer Text verfügbar' }}
                </div>
              </div>

              <!-- Right Column: Selected Target Language -->
              <div class="flex flex-col gap-2 text-left">
                <div class="text-xs uppercase tracking-wider font-semibold text-gray-500 border-b border-white/5 pb-1 flex items-center justify-between">
                  <span>{{ formatLanguageLabel(targetLanguage) }} ({{ targetLanguage }})</span>
                  <span v-if="item.translation_source_indices && item.translation_source_indices[targetLanguage]" :title="sourcesBibliography[item.translation_source_indices[targetLanguage]]" class="text-[10px] text-amber-500 hover:underline cursor-help">
                    Source [{{ item.translation_source_indices[targetLanguage] }}]
                  </span>
                </div>
                <div class="text-sm leading-relaxed text-gray-200 whitespace-pre-line">
                  {{ item.translations[targetLanguage] || 'Kein deutscher Text verfügbar' }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Sources Bibliography -->
      <section v-if="!loading && !error" class="w-full pt-10 pb-6">
        <div class="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl p-6 shadow-2xl">
          <h2 class="font-serif font-semibold text-lg text-amber-500 mb-4 border-b border-white/5 pb-2">
            Quellenverzeichnis / Bibliographie
          </h2>
          <ul class="flex flex-col gap-3 text-xs text-gray-400 leading-relaxed text-left">
            <li v-for="(text, idx) in sourcesBibliography" :key="idx" class="flex gap-2">
              <span class="text-amber-500 font-bold min-w-[24px]">[{{ idx }}]</span>
              <span>{{ text }}</span>
            </li>
          </ul>
        </div>
      </section>
    </main>

    <!-- Floating Audio Dashboard / Unified Controller -->
    <div class="player-bar" :class="{ 'active': currentPlayingKey || isPriest || isAdmin }">
      <!-- Player Info (Title, Status, Autoplay Checkbox) -->
      <div class="player-info flex flex-col gap-1 text-left min-w-[20%] max-w-[25%]">
        <div class="player-info-title truncate font-semibold text-xs sm:text-sm text-amber-500">
          {{ isPriest || isAdmin ? 'Live-Steuerung' : (currentPlayingKey ? playerTitle : 'Gottesdienst-Begleiter') }}
        </div>
        <div class="player-info-status text-[11px] text-gray-400 leading-none mb-1">
          {{ isPriest || isAdmin ? 'Priester-Modus' : (currentPlayingKey ? playerStatus : 'Audio inaktiv') }}
        </div>
        <label class="flex items-center gap-1.5 cursor-pointer text-[10px] text-gray-400 hover:text-white transition-colors select-none">
          <input type="checkbox" v-model="autoplay" class="accent-amber-500 h-3.5 w-3.5 rounded border-white/10 bg-slate-950 focus:ring-0 cursor-pointer">
          <span>Autoplay</span>
        </label>
      </div>

      <!-- Playback Controls (Prev Step, Play/Pause, Next Step, Stop, Timeline Seeker) -->
      <div class="player-controls flex-grow" :class="{ 'opacity-40 pointer-events-none': !currentPlayingKey && !isPriest && !isAdmin }">
        <!-- Previous Step (⏮ symbol) -->
        <button 
          @click="advanceLiturgy(-1)" 
          :disabled="currentSectionIndex <= 0" 
          class="btn-circle subtle" 
          title="Vorheriger Liturgieschritt"
        >
          <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current"><path d="M6 6h2v12H6zm3.5 6 8.5 6V6z"/></svg>
        </button>

        <!-- Play / Pause -->
        <button @click="togglePlay" class="btn-circle" :disabled="!currentPlayingKey" title="Abspielen/Pause">
          <svg v-if="isPlaying" viewBox="0 0 24 24" class="w-4 h-4 fill-current"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
          <svg v-else viewBox="0 0 24 24" class="w-4 h-4 fill-current"><path d="M8 5v14l11-7z"/></svg>
        </button>

        <!-- Next Step (⏭ symbol) -->
        <button 
          @click="advanceLiturgy(1)" 
          :disabled="currentSectionIndex >= liturgySections.length - 1" 
          class="btn-circle subtle" 
          title="Nächster Liturgieschritt"
        >
          <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current"><path d="M16 6h2v12h-2zm-10.5 0 8.5 6-8.5 6z"/></svg>
        </button>

        <!-- Stop -->
        <button @click="stopAudio" class="btn-circle" :disabled="!currentPlayingKey" title="Stoppen">
          <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current"><path d="M6 6h12v12H6z"/></svg>
        </button>

        <!-- Seek Slider -->
        <div class="seek-container ml-2">
          <span class="seek-time">{{ formatTime(currentTime) }}</span>
          <input 
            type="range" 
            class="slider" 
            min="0" 
            :max="totalDuration || 100" 
            v-model="currentTime"
            :disabled="!currentPlayingKey"
            @input="onSeek"
          >
          <span class="seek-time">{{ formatTime(totalDuration) }}</span>
        </div>
      </div>

      <!-- Player Options (Speed, Volume) -->
      <div class="player-options" :class="{ 'opacity-40 pointer-events-none': !currentPlayingKey && !isPriest && !isAdmin }">
        <!-- Speed Badge -->
        <div @click="cycleSpeed" class="speed-badge" :disabled="!currentPlayingKey" title="Geschwindigkeit ändern">
          {{ playbackSpeeds[currentSpeedIndex] }}x
        </div>
        <!-- Volume -->
        <div class="volume-container">
          <span @click="toggleMute" class="volume-icon select-none cursor-pointer">
            {{ isMuted ? '🔇' : '🔊' }}
          </span>
          <input 
            type="range" 
            class="slider volume-slider" 
            min="0" 
            max="1" 
            step="0.05"
            v-model="volume"
            @input="onVolumeChange"
          >
        </div>
      </div>
    </div>

    <!-- Schedule Service Modal -->
    <div v-if="showScheduleModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
      <div class="bg-slate-900 border border-white/10 rounded-2xl max-w-md w-full p-6 shadow-2xl text-left transform transition-all">
        <div class="flex items-center justify-between border-b border-white/5 pb-3 mb-4">
          <h3 class="font-serif text-lg font-semibold text-amber-500 flex items-center gap-2">
            <span>📅</span> Gottesdienst planen
          </h3>
          <button @click="showScheduleModal = false" class="text-gray-400 hover:text-white text-lg leading-none">×</button>
        </div>

        <form @submit.prevent="scheduleService" class="flex flex-col gap-4">
          <!-- Template -->
          <div class="flex flex-col gap-1.5">
            <label class="text-xs text-gray-400">Typ / Liturgie-Vorlage</label>
            <select 
              v-model="newServiceTemplateId" 
              required
              class="w-full bg-slate-950 border border-white/10 rounded-xl p-2.5 text-sm text-white focus:outline-none focus:border-amber-500/50 cursor-pointer"
            >
              <option v-for="t in templatesList" :key="t.id" :value="t.id" class="bg-slate-950 text-white">{{ t.name }}</option>
            </select>
          </div>

          <!-- Date and Time -->
          <div class="flex flex-col gap-1.5">
            <label class="text-xs text-gray-400">Datum & Uhrzeit</label>
            <input 
              type="datetime-local" 
              v-model="newServiceDate" 
              required
              class="w-full bg-slate-950 border border-white/10 rounded-xl p-2.5 text-sm text-white focus:outline-none focus:border-amber-500/50 cursor-pointer"
            >
          </div>

          <!-- Languages -->
          <div class="flex flex-col gap-1.5">
            <label class="text-xs text-gray-400">Aktive Sprachen</label>
            <div class="grid grid-cols-2 gap-2 bg-slate-950/50 border border-white/5 rounded-xl p-3">
              <label class="flex items-center gap-2 text-xs text-gray-300 cursor-pointer select-none">
                <input type="checkbox" value="de" v-model="newServiceLanguages" class="accent-amber-500"> Deutsch
              </label>
              <label class="flex items-center gap-2 text-xs text-gray-300 cursor-pointer select-none">
                <input type="checkbox" value="cu" v-model="newServiceLanguages" class="accent-amber-500"> Kirchenslawisch
              </label>
              <label class="flex items-center gap-2 text-xs text-gray-300 cursor-pointer select-none">
                <input type="checkbox" value="en" v-model="newServiceLanguages" class="accent-amber-500"> English
              </label>
              <label class="flex items-center gap-2 text-xs text-gray-300 cursor-pointer select-none">
                <input type="checkbox" value="ru" v-model="newServiceLanguages" class="accent-amber-500"> Русский
              </label>
              <label class="flex items-center gap-2 text-xs text-gray-300 cursor-pointer select-none">
                <input type="checkbox" value="uk" v-model="newServiceLanguages" class="accent-amber-500"> Українська
              </label>
            </div>
          </div>

          <div class="flex justify-end gap-3 border-t border-white/5 pt-4 mt-2">
            <button 
              type="button" 
              @click="showScheduleModal = false" 
              class="bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold py-2.5 px-4 rounded-xl transition-colors"
            >
              Abbrechen
            </button>
            <button 
              type="submit" 
              class="bg-amber-500 text-black hover:bg-amber-400 text-xs font-bold py-2.5 px-4 rounded-xl transition-colors"
            >
              Planen
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      serviceId: null,
      serviceName: '',
      serviceDate: '',
      loading: true,
      error: null,
      liturgySections: [],
      listItems: [],
      sourcesBibliography: {},
      targetLanguage: localStorage.getItem('targetLanguage') || 'de',
      
      // Card states
      expandedCards: new Set(),
      
      // Auth states
      user: null,
      
      // Audio states
      audioPlayer: new Audio(),
      currentPlayingKey: null,
      isPlaying: false,
      currentTime: 0,
      totalDuration: 0,
      volume: parseFloat(localStorage.getItem('volume') || '0.8'),
      isMuted: false,
      playbackSpeeds: [1.0, 1.25, 1.5],
      currentSpeedIndex: 0,
      playerTitle: 'Kein Titel',
      playerStatus: 'Bereit',

      // Live Sync
      activeSectionKey: null,
      autoplay: localStorage.getItem('autoplay') === 'true',
      pollingInterval: null,

      // Priest Panel
      showSermonEditor: false,
      sermonText: '',
      savingSermon: false,
      communityId: null,
      servicesList: [],
      templatesList: [],
      showScheduleModal: false,
      newServiceTemplateId: '',
      newServiceDate: '',
      newServiceLanguages: ['de'],
    }
  },
  computed: {
    isPriest() {
      return this.user && this.user.roles && this.user.roles.includes('priest');
    },
    isAdmin() {
      return this.user && this.user.roles && this.user.roles.includes('admin');
    },
    currentSectionIndex() {
      if (!this.activeSectionKey) return -1;
      return this.liturgySections.findIndex(sec => sec.text_keys.includes(this.activeSectionKey));
    },
    sortedServices() {
      return [...this.servicesList].sort((a, b) => new Date(b.scheduled_time) - new Date(a.scheduled_time));
    }
  },
  async mounted() {
    // 1. Check callback route in URL (nextcloud sso redirect)
    if (window.location.pathname === '/auth/callback') {
      const params = new URLSearchParams(window.location.search);
      const token = params.get('token');
      if (token) {
        localStorage.setItem('token', token);
      }
      // Redirect to clean path
      window.location.href = '/';
      return;
    }

    // 2. Parse existing auth token from local storage
    const token = localStorage.getItem('token');
    if (token) {
      this.user = this.decodeJwt(token);
    }

    // 3. Load Liturgy details
    await this.loadLiturgy();

    // 4. Configure audio player events
    this.audioPlayer.volume = this.volume;
    this.audioPlayer.addEventListener('timeupdate', () => {
      this.currentTime = this.audioPlayer.currentTime;
    });
    this.audioPlayer.addEventListener('durationchange', () => {
      this.totalDuration = this.audioPlayer.duration;
    });
    this.audioPlayer.addEventListener('ended', () => {
      this.isPlaying = false;
      this.playerStatus = 'Beendet';
      
      // Auto-advance audio to next part if we are in normal progression (and not sync mode)
      if (!this.isPriest && this.autoplay && this.currentPlayingKey === this.activeSectionKey) {
        // Just let it wait for the priest to advance
      }
    });

    // 5. Start live synchronization polling (every 3 seconds)
    this.pollingInterval = setInterval(this.pollActiveServiceState, 3000);
  },
  beforeUnmount() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
    }
    this.audioPlayer.pause();
  },
  methods: {
    // Decode JWT payload on frontend without extra library
    decodeJwt(token) {
      try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(
          window.atob(base64)
            .split('')
            .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
            .join('')
        );
        return JSON.parse(jsonPayload);
      } catch (e) {
        console.error("Failed to decode JWT:", e);
        return null;
      }
    },
    loginWithNextcloud() {
      // Initiate OIDC login flow via backend
      window.location.href = '/api/v1/auth/login';
    },
    logout() {
      localStorage.removeItem('token');
      this.user = null;
      window.location.reload();
    },
    async loadLiturgy() {
      this.loading = true;
      try {
        // 1. Fetch all scheduled services
        const servicesRes = await fetch("/api/v1/liturgy/services");
        if (servicesRes.ok) {
          this.servicesList = await servicesRes.json();
        }

        // 2. Fetch templates list
        await this.loadTemplates();

        // 3. Find latest service if not set
        if (!this.serviceId) {
          try {
            const latestRes = await fetch("/api/v1/liturgy/services/latest");
            if (latestRes.ok) {
              const latestService = await latestRes.json();
              this.serviceId = latestService.id;
              this.communityId = latestService.community_id;
            } else if (this.servicesList.length > 0) {
              // Sort by date desc
              const sorted = [...this.servicesList].sort((a, b) => new Date(b.scheduled_time) - new Date(a.scheduled_time));
              this.serviceId = sorted[0].id;
              this.communityId = sorted[0].community_id;
            }
          } catch (e) {
            console.error("Failed to fetch latest service:", e);
          }
        }

        if (!this.serviceId) {
          throw new Error("Kein aktiver Gottesdienst gefunden. Bitte planen Sie einen Gottesdienst.");
        }

        // 4. Load details
        await this.loadLiturgyDetails();

      } catch (err) {
        this.error = err.message;
      } finally {
        this.loading = false;
      }
    },
    async loadLiturgyDetails() {
      if (!this.serviceId) return;
      this.loading = true;
      try {
        const response = await fetch(`/api/v1/liturgy/services/${this.serviceId}?languages=de,cu,en,ru,uk`);
        if (!response.ok) throw new Error("Laden der Liturgie fehlgeschlagen.");
        const data = await response.json();

        this.serviceName = data.template.name;
        this.communityId = data.service.community_id;
        
        const dateObj = new Date(data.service.scheduled_time);
        this.serviceDate = `${dateObj.toLocaleDateString("de-DE", {weekday:"long", day:"numeric", month:"long", year:"numeric"})} um ${dateObj.toLocaleTimeString("de-DE", {hour:"2-digit", minute:"2-digit"})}`;
        
        this.activeSectionKey = data.service.current_section_key;
        this.liturgySections = data.template.structure.sections;
        this.sourcesBibliography = data.sources_bibliography || {};

        // Build flat array of items to render
        const items = [];
        this.liturgySections.forEach(sec => {
          sec.text_keys.forEach(key => {
            const textItem = data.texts[key];
            if (textItem) {
              items.push({
                key,
                ...textItem
              });
            }
          });
        });
        this.listItems = items;
        
        // Auto-expand active step
        if (this.activeSectionKey) {
          this.expandedCards.clear();
          this.expandedCards.add(this.activeSectionKey);
        }

        // Preload sermon if editing
        const sermonKey = `sermon.service_${this.serviceId}`;
        if (data.texts[sermonKey]) {
          this.sermonText = data.texts[sermonKey].translations.de || '';
        } else {
          this.sermonText = '';
        }
      } catch (err) {
        this.error = err.message;
      } finally {
        this.loading = false;
      }
    },
    openScheduleModal() {
      if (this.templatesList.length === 0) {
        this.loadTemplates();
      }
      // Pre-fill date to next Sunday at 09:30
      const nextSunday = new Date();
      nextSunday.setDate(nextSunday.getDate() + (7 - nextSunday.getDay()) % 7);
      nextSunday.setHours(9, 30, 0, 0);
      
      const pad = (n) => n.toString().padStart(2, '0');
      this.newServiceDate = `${nextSunday.getFullYear()}-${pad(nextSunday.getMonth()+1)}-${pad(nextSunday.getDate())}T${pad(nextSunday.getHours())}:${pad(nextSunday.getMinutes())}`;
      
      if (this.templatesList.length > 0) {
        this.newServiceTemplateId = this.templatesList[0].id;
      }
      this.showScheduleModal = true;
    },
    async loadTemplates() {
      try {
        const res = await fetch("/api/v1/liturgy/templates");
        if (res.ok) {
          this.templatesList = await res.json();
          if (this.templatesList.length > 0 && !this.newServiceTemplateId) {
            this.newServiceTemplateId = this.templatesList[0].id;
          }
        }
      } catch (err) {
        console.error("Failed to load templates:", err);
      }
    },
    async scheduleService() {
      try {
        const payload = {
          template_id: this.newServiceTemplateId,
          community_id: this.communityId || "929e9fd8-cdaf-4152-8e62-e89eb991fd6c",
          scheduled_time: new Date(this.newServiceDate).toISOString(),
          active_languages: this.newServiceLanguages
        };

        const res = await fetch("/api/v1/liturgy/services", {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify(payload)
        });

        if (!res.ok) {
          const detail = await res.json();
          throw new Error(detail.detail || "Erstellen fehlgeschlagen.");
        }

        const newService = await res.json();
        
        // Refresh list
        const servicesRes = await fetch("/api/v1/liturgy/services");
        if (servicesRes.ok) {
          this.servicesList = await servicesRes.json();
        }

        this.showScheduleModal = false;
        
        // Select newly created service
        this.serviceId = newService.id;
        await this.loadLiturgyDetails();

      } catch (err) {
        alert("Fehler beim Planen des Gottesdienstes: " + err.message);
      }
    },
    formatServiceOption(srv) {
      const d = new Date(srv.scheduled_time);
      const dateStr = d.toLocaleDateString("de-DE", { day: '2-digit', month: '2-digit' });
      const timeStr = d.toLocaleTimeString("de-DE", { hour: '2-digit', minute: '2-digit' });
      const name = this.getTemplateName(srv.template_id);
      return `${dateStr} ${timeStr} - ${name}`;
    },
    getTemplateName(templateId) {
      const t = this.templatesList.find(x => x.id === templateId);
      return t ? t.name : 'Gottesdienst';
    },
    async pollActiveServiceState() {
      if (!this.serviceId) return;
      try {
        const res = await fetch(`/api/v1/liturgy/services/${this.serviceId}`);
        if (!res.ok) return;
        const data = await res.json();
        
        const newActiveKey = data.service.current_section_key;
        if (newActiveKey && newActiveKey !== this.activeSectionKey) {
          this.activeSectionKey = newActiveKey;
          this.expandedCards.clear();
          this.expandedCards.add(newActiveKey);

          // Scroll to the active element card smoothly
          this.$nextTick(() => {
            const cardEl = document.getElementById(`card-${newActiveKey}`);
            if (cardEl) {
              cardEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
          });

        }
      } catch (err) {
        console.error("Live-sync polling error:", err);
      }
    },
    // Priest controller actions
    async advanceLiturgy(direction) {
      if (this.currentSectionIndex === -1 && this.liturgySections.length > 0) {
        this.updateActiveStepOnServer(this.liturgySections[0].text_keys[0]);
        return;
      }

      let nextIndex = this.currentSectionIndex + direction;
      if (nextIndex >= 0 && nextIndex < this.liturgySections.length) {
        const nextKey = this.liturgySections[nextIndex].text_keys[0];
        await this.updateActiveStepOnServer(nextKey);
      }
    },
    async updateActiveStepOnServer(key) {
      this.activeSectionKey = key;
      this.expandedCards.clear();
      this.expandedCards.add(key);

      // Scroll to it locally
      this.$nextTick(() => {
        const cardEl = document.getElementById(`card-${key}`);
        if (cardEl) {
          cardEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      });

      try {
        await fetch(`/api/v1/liturgy/services/${this.serviceId}`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            // Send JWT authorization if logged in
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({ current_section_key: key })
        });
      } catch (err) {
        console.error("Failed to update active section on server:", err);
      }
    },
    async saveSermon() {
      if (!this.sermonText.trim()) return;
      this.savingSermon = true;
      try {
        const res = await fetch(`/api/v1/liturgy/services/${this.serviceId}/sermon`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({
            text: this.sermonText,
            language: 'de'
          })
        });
        if (!res.ok) throw new Error("Speichern fehlgeschlagen.");
        
        // Reload liturgy translation content to fetch new translations and generated audio urls
        await this.loadLiturgy();
        alert("Predigt erfolgreich gespeichert, übersetzt und Audio generiert!");
        this.showSermonEditor = false;
      } catch (err) {
        alert("Fehler beim Speichern der Predigt: " + err.message);
      } finally {
        this.savingSermon = false;
      }
    },
    onLanguageChange() {
      localStorage.setItem('targetLanguage', this.targetLanguage);
    },
    toggleCard(key) {
      if (this.expandedCards.has(key)) {
        this.expandedCards.delete(key);
      } else {
        this.expandedCards.add(key);
      }
    },
    // Player controls
    playAudio(key, url, title) {
      // Toggle play/pause if clicking currently loaded audio
      if (this.currentPlayingKey === key) {
        this.togglePlay();
        return;
      }

      this.currentPlayingKey = key;
      this.playerTitle = title;
      this.playerStatus = 'Verbinde...';
      
      // Load and play
      this.audioPlayer.src = url;
      this.audioPlayer.playbackRate = this.playbackSpeeds[this.currentSpeedIndex];
      this.audioPlayer.play()
        .then(() => {
          this.isPlaying = true;
          this.playerStatus = 'Spielt ab';
        })
        .catch(err => {
          console.error("Playback error:", err);
          this.playerStatus = 'Fehler beim Laden';
        });
    },
    togglePlay() {
      if (!this.currentPlayingKey) return;
      
      if (this.isPlaying) {
        this.audioPlayer.pause();
        this.isPlaying = false;
        this.playerStatus = 'Pausiert';
      } else {
        this.audioPlayer.play()
          .then(() => {
            this.isPlaying = true;
            this.playerStatus = 'Spielt ab';
          });
      }
    },
    stopAudio() {
      this.audioPlayer.pause();
      this.audioPlayer.currentTime = 0;
      this.isPlaying = false;
      this.currentPlayingKey = null;
      this.playerTitle = 'Kein Titel';
      this.playerStatus = 'Bereit';
    },
    onSeek() {
      this.audioPlayer.currentTime = this.currentTime;
    },
    cycleSpeed() {
      this.currentSpeedIndex = (this.currentSpeedIndex + 1) % this.playbackSpeeds.length;
      const speed = this.playbackSpeeds[this.currentSpeedIndex];
      this.audioPlayer.playbackRate = speed;
    },
    onVolumeChange() {
      this.audioPlayer.volume = this.volume;
      this.isMuted = this.volume === 0;
      localStorage.setItem('volume', this.volume.toString());
    },
    toggleMute() {
      this.isMuted = !this.isMuted;
      this.audioPlayer.muted = this.isMuted;
    },
    // Formatting helpers
    formatKeyTitle(key) {
      if (!key) return '';
      const titles = {
        "liturgy.opening_blessing": "Eröffnungssegen",
        "liturgy.great_litany.lord_have_mercy": "Große Ektenie",
        "liturgy.first_antiphon.refrain": "Erstes Antiphon",
        "liturgy.small_litany_1": "Erste Kleine Ektenie",
        "liturgy.second_antiphon.refrain": "Zweites Antiphon",
        "liturgy.small_litany_2": "Zweite Kleine Ektenie",
        "liturgy.third_antiphon.beatitudes": "Drittes Antiphon (Seligpreisungen)",
        "liturgy.small_entrance.verse": "Kleiner Einzug",
        "liturgy.trisagion.main": "Trisagion (Dreimalheilig-Hymnus)",
        "liturgy.alleluia_ref": "Halleluja-Vers",
        "liturgy.sermon_placeholder": "Predigt",
        "liturgy.cherubic_hymn.main": "Cherubim-Hymnus",
        "liturgy.litany_supplication": "Ektenie der Rüstung",
        "liturgy.creed.main": "Glaubensbekenntnis",
        "liturgy.anaphora.dialogue": "Anaphora (Eucharistie-Dialog)",
        "liturgy.anaphora.sanctus": "Sanctus (Heilig-Ruf)",
        "liturgy.anaphora.institution": "Einsetzungsworte",
        "liturgy.anaphora.epiklesis": "Epiklesis (Herabrufung des Geistes)",
        "liturgy.hymn_to_theotokos": "Muttergottes-Hymnus (Axion Estin)",
        "liturgy.lords_prayer.main": "Vaterunser",
        "liturgy.communion.elevation": "Erhebung der Gaben",
        "liturgy.communion.response": "Antwort des Chores",
        "liturgy.communion.koinonikon": "Kommuniongesang (Koinonikon)",
        "liturgy.communion.invitation": "Einladung zur Kommunion",
        "liturgy.communion.post_communion": "Danksagung nach der Kommunion",
        "liturgy.thanksgiving_hymn": "Dankhymnus",
        "liturgy.prayer_ambo": "Gebet hinter dem Ambo",
        "liturgy.dismissal": "Entlassung"
      };

      if (titles[key]) return titles[key];
      if (key.includes("sermon.service_")) return "Predigt";
      if (key.startsWith("oktoechos.tone_")) {
        const parts = key.split('.');
        const type = parts[parts.length - 1];
        const toneStr = parts[1].replace("tone_", "");
        if (type === "troparion") return `Troparion (Ton ${toneStr})`;
        if (type === "kontakion") return `Kontakion (Ton ${toneStr})`;
        if (type === "prokeimenon") return `Prokeimenon (Ton ${toneStr})`;
        return `Tagesgesang (Ton ${toneStr})`;
      }
      if (key.startsWith("scripture.epistle.")) {
        let ref = key.replace("scripture.epistle.", "");
        ref = this.translateBibleRef(ref);
        return `Epistellesung (${ref})`;
      }
      if (key.startsWith("scripture.gospel.")) {
        let ref = key.replace("scripture.gospel.", "");
        ref = this.translateBibleRef(ref);
        return `Evangelienlesung (${ref})`;
      }
      return key.split('.').pop().replace(/_/g, ' ');
    },
    translateBibleRef(ref) {
      if (!ref) return '';
      const books = {
        "Romans": "Römer",
        "Matthew": "Matthäus",
        "Mark": "Markus",
        "Luke": "Lukas",
        "John": "Johannes",
        "Acts": "Apostelgeschichte",
        "Corinthians": "Korinther",
        "Galatians": "Galater",
        "Ephesians": "Epheser",
        "Philippians": "Philipper",
        "Colossians": "Kolosser",
        "Thessalonians": "Thessalonicher",
        "Timothy": "Timotheus",
        "Hebrews": "Hebräer",
        "Peter": "Petrus",
        "Revelation": "Offenbarung"
      };
      let result = ref;
      Object.keys(books).forEach(en => {
        result = result.replace(en, books[en]);
      });
      return result;
    },
    getLiturgicalRoles(key) {
      const roles = [];
      const priestKeys = ["opening_blessing", "sermon", "communion.elevation", "prayer_ambo"];
      const choirKeys = ["antiphon", "troparion", "alleluia_ref", "cherubic_hymn", "anaphora.sanctus", "communion.response", "communion.koinonikon", "communion.post_communion", "thanksgiving_hymn"];
      const congregationKeys = ["creed", "lords_prayer"];
      const dialogueKeys = ["great_litany", "small_litany", "small_entrance", "trisagion", "prokeimenon", "epistle_reading", "gospel_reading", "litany_supplication", "anaphora.dialogue", "anaphora.institution", "anaphora.epiklesis", "hymn_to_theotokos", "communion.invitation", "dismissal"];

      if (priestKeys.some(k => key.includes(k))) roles.push({ text: "Priester", class: "role-priest" });
      if (choirKeys.some(k => key.includes(k))) roles.push({ text: "Chor", class: "role-choir" });
      if (congregationKeys.some(k => key.includes(k))) roles.push({ text: "Gemeinde", class: "role-congregation" });
      if (dialogueKeys.some(k => key.includes(k))) roles.push({ text: "Wechselgesang", class: "role-dialogue" });

      if (roles.length === 0) roles.push({ text: "Gottesdienst", class: "role-dialogue" });
      return roles;
    },
    formatLanguageLabel(lang) {
      const labels = {
        'de': 'Deutsch',
        'en': 'English',
        'ru': 'Русский',
        'uk': 'Українська'
      };
      return labels[lang] || lang.toUpperCase();
    },
    formatTime(seconds) {
      if (isNaN(seconds)) return '0:00';
      const m = Math.floor(seconds / 60);
      const s = Math.floor(seconds % 60);
      return `${m}:${s < 10 ? '0' : ''}${s}`;
    }
  },
  watch: {
    activeSectionKey(newVal) {
      if (this.autoplay && newVal) {
        const item = this.listItems.find(i => i.key === newVal);
        if (item && item.audio_url) {
          this.playAudio(item.key, item.audio_url, this.formatKeyTitle(item.key));
        }
      }
    },
    autoplay(newVal) {
      localStorage.setItem('autoplay', newVal.toString());
    }
  }
}
</script>

<style scoped>
.btn-control {
  font-size: 0.88rem;
  padding: 8px 16px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: white;
  cursor: pointer;
  transition: all 0.2s ease;
}
.btn-control:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}
.btn-control:active:not(:disabled) {
  transform: translateY(0);
}

.card {
  background: var(--glass-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--glass-border);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}
.card:hover {
  border-color: rgba(212, 175, 55, 0.3);
  box-shadow: 0 12px 40px 0 rgba(212, 175, 55, 0.05);
  transform: translateY(-2px);
}

.active-step {
  animation: border-pulse 3s infinite;
}

@keyframes border-pulse {
  0%, 100% { border-color: rgba(212, 175, 55, 0.3); }
  50% { border-color: rgba(212, 175, 55, 0.75); }
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
  flex-shrink: 0;
}

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
  flex-shrink: 0;
}
.btn-circle:hover {
  background: rgba(212, 175, 55, 0.15);
  border-color: var(--accent-color);
  color: var(--accent-color);
  transform: scale(1.05);
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
.btn-circle.subtle {
  opacity: 0.65;
  border-color: transparent;
  background: transparent;
}
.btn-circle.subtle:hover:not(:disabled) {
  opacity: 1;
  color: var(--accent-color);
  background: rgba(255, 255, 255, 0.05);
}

@keyframes pulse-gold {
  0% { box-shadow: 0 0 0 0 rgba(212, 175, 55, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(212, 175, 55, 0); }
  100% { box-shadow: 0 0 0 0 rgba(212, 175, 55, 0); }
}

.role-badge {
  font-size: 0.65rem;
  font-weight: 600;
  padding: 1px 6px;
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
  gap: 2px;
  width: 25%;
  text-align: left;
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
}

.player-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 50%;
  justify-content: center;
}

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
.volume-slider {
  width: 60px;
}
</style>
