// ==========================================================================
// GROUNDED: TouchGrass AI - Open-Source Outdoor Companion
// Frontend Controller (Gemma 3 Inference, Bioacoustics, Leaflet, Audio TTS)
// ==========================================================================

let leafletMap = null;
let currentRoutePolyline = null;
let currentMarkers = [];
let lastGeneratedGpx = "";
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let countdownInterval = null;
let currentBirdResult = null;
let currentDispatchResult = null;

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initOutdoorModes();
  initStatus();
  initDispatch();
  initBirdIdentifier();
  initGardenPlanner();
  initTrailBuilder();
  initJournal();
});

// ==========================================================================
// 1. TABS & ERGONOMIC MODES
// ==========================================================================

function initTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      tabBtns.forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      const targetContent = document.getElementById(targetId);
      if (targetContent) {
        targetContent.classList.add("active");
        if (targetId === "tab-trails" && leafletMap) {
          setTimeout(() => leafletMap.invalidateSize(), 200);
        }
      }
    });
  });
}

function initOutdoorModes() {
  const btnStd = document.getElementById("btn-mode-standard");
  const btnSun = document.getElementById("btn-mode-sunlight");
  const btnNight = document.getElementById("btn-mode-night");

  function setMode(mode) {
    document.body.classList.remove("sunlight-mode", "night-mode");
    [btnStd, btnSun, btnNight].forEach(b => b.classList.remove("active"));

    if (mode === "sunlight") {
      document.body.classList.add("sunlight-mode");
      btnSun.classList.add("active");
    } else if (mode === "night") {
      document.body.classList.add("night-mode");
      btnNight.classList.add("active");
    } else {
      btnStd.classList.add("active");
    }
  }

  btnStd.addEventListener("click", () => setMode("standard"));
  btnSun.addEventListener("click", () => setMode("sunlight"));
  btnNight.addEventListener("click", () => setMode("night"));
}

async function initStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    const pill = document.getElementById("system-status-text");
    if (data.online) {
      pill.textContent = `${data.active_model} (CUDA Active • 100% Offline)`;
    } else {
      pill.textContent = "Offline Fallback Naturalist Engine";
    }
  } catch (err) {
    console.warn("Status check notice:", err);
  }
}

// Text-to-Speech Helper (Zero-screen pocket mode)
function speakText(text) {
  if (!('speechSynthesis' in window)) {
    alert("Speech synthesis is not supported on this device.");
    return;
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 0.95;
  utterance.pitch = 1.0;
  window.speechSynthesis.speak(utterance);
}

// ==========================================================================
// 2. TAB 1: QUICK DISPATCH ("GET OUT THERE")
// ==========================================================================

function initDispatch() {
  const form = document.getElementById("dispatch-form");
  const loading = document.getElementById("dispatch-loading");
  const cardBody = document.getElementById("dispatch-card-body");
  const btnSpeak = document.getElementById("btn-speak-dispatch");
  const btnSave = document.getElementById("btn-save-expedition");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const activity_type = document.getElementById("dispatch-activity").value;
    const duration_mins = parseInt(document.getElementById("dispatch-duration").value);
    const environment = document.getElementById("dispatch-env").value;

    loading.style.display = "block";
    cardBody.style.opacity = "0.4";

    try {
      const res = await fetch("/api/dispatch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ activity_type, duration_mins, environment })
      });
      const data = await res.json();
      currentDispatchResult = data;
      renderDispatchCard(data, duration_mins);
    } catch (err) {
      alert("Error generating dispatch: " + err);
    } finally {
      loading.style.display = "none";
      cardBody.style.opacity = "1";
    }
  });

  btnSpeak.addEventListener("click", () => {
    if (!currentDispatchResult) return;
    const speech = `Expedition dispatched: ${currentDispatchResult.title}. Your mission: ${currentDispatchResult.primary_mission}. Auditory anchor: ${currentDispatchResult.auditory_anchor}. Now close your device and step outside.`;
    speakText(speech);
  });

  btnSave.addEventListener("click", async () => {
    if (!currentDispatchResult) return;
    alert("Expedition logged to your offline journal! Time to head outside.");
  });
}

function renderDispatchCard(data, durationMins) {
  document.getElementById("card-title").textContent = data.title || "Field Expedition";
  document.getElementById("card-mission").textContent = data.primary_mission || "Observe nature closely.";
  document.getElementById("card-auditory").textContent = data.auditory_anchor || "Listen carefully to the surroundings.";
  document.getElementById("card-advice").textContent = data.field_advice || "Pack water and wear suitable footwear.";
  document.getElementById("card-countdown-text").textContent = data.screen_off_countdown || "Lock your device and step outside.";

  // Species watchlist pills
  const watchlistContainer = document.getElementById("card-watchlist");
  watchlistContainer.innerHTML = "";
  const list = data.species_watchlist || ["Autumn Canopy", "Local Songbirds"];
  list.forEach(item => {
    const pill = document.createElement("span");
    pill.className = "pill";
    pill.textContent = item;
    watchlistContainer.appendChild(pill);
  });

  // Start timer
  startCountdown(durationMins * 60);
}

function startCountdown(totalSeconds) {
  if (countdownInterval) clearInterval(countdownInterval);
  const display = document.getElementById("timer-display");

  function update() {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    display.textContent = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    if (totalSeconds <= 0) {
      clearInterval(countdownInterval);
      display.textContent = "00:00 - WELCOME BACK!";
    }
    totalSeconds--;
  }

  update();
  countdownInterval = setInterval(update, 1000);
}

// ==========================================================================
// 3. TAB 2: BIOACOUSTIC BIRD IDENTIFIER
// ==========================================================================

async function initBirdIdentifier() {
  const sampleList = document.getElementById("sample-buttons-list");
  const audioPlayer = document.getElementById("audio-player");
  const micBtn = document.getElementById("btn-mic-record");
  const recordText = document.getElementById("record-btn-text");
  const fileInput = document.getElementById("audio-file-input");
  const btnSpeakBird = document.getElementById("btn-speak-bird");
  const btnSaveBird = document.getElementById("btn-save-bird-obs");

  // Load sample list
  try {
    const res = await fetch("/api/samples");
    const samples = await res.json();
    sampleList.innerHTML = "";
    samples.forEach(s => {
      const chip = document.createElement("div");
      chip.className = "sample-chip";
      chip.innerHTML = `
        <div class="title">${s.name}</div>
        <div class="sub">${s.pitch}</div>
      `;
      chip.addEventListener("click", () => {
        audioPlayer.src = `/api/samples/audio/${s.id}`;
        audioPlayer.play();
        analyzeSample(s.id);
      });
      sampleList.appendChild(chip);
    });
  } catch (err) {
    console.error("Could not load samples:", err);
  }

  // File upload
  fileInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) {
      audioPlayer.src = URL.createObjectURL(file);
      audioPlayer.play();
      uploadAndAnalyze(file);
    }
  });

  // Microphone recording
  micBtn.addEventListener("click", async () => {
    if (!isRecording) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (e) => {
          if (e.data.size > 0) audioChunks.push(e.data);
        };

        mediaRecorder.onstop = () => {
          const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
          audioPlayer.src = URL.createObjectURL(audioBlob);
          audioPlayer.play();
          uploadAndAnalyze(audioBlob, "trail_recording.wav");
        };

        mediaRecorder.start();
        isRecording = true;
        micBtn.classList.add("recording");
        recordText.textContent = "Recording... Click to Stop";
      } catch (err) {
        alert("Microphone access denied or unavailable: " + err);
      }
    } else {
      if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(t => t.stop());
      }
      isRecording = false;
      micBtn.classList.remove("recording");
      recordText.textContent = "Record from Mic";
    }
  });

  btnSpeakBird.addEventListener("click", () => {
    if (!currentBirdResult) return;
    const sp = currentBirdResult.identification;
    const speech = `Identified: ${sp.primary_species}. ${sp.field_visual_markers}. Behavior: ${sp.call_behavior}`;
    speakText(speech);
  });

  btnSaveBird.addEventListener("click", async () => {
    if (!currentBirdResult) return;
    const sp = currentBirdResult.identification;
    const ac = currentBirdResult.acoustics;
    try {
      await fetch("/api/journal/observation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          category: "bird",
          species_name: sp.primary_species,
          scientific_name: sp.scientific_name,
          confidence: sp.confidence_percent,
          location_name: "Trail Bioacoustic Recording",
          notes: `${sp.field_visual_markers}. ${sp.call_behavior}`,
          acoustic_data: `Peak: ${ac.dominant_frequency_hz}Hz, Centroid: ${ac.spectral_centroid_hz}Hz`
        })
      });
      alert(`Saved ${sp.primary_species} to your offline field journal!`);
      loadJournalObservations();
    } catch (err) {
      alert("Error saving observation: " + err);
    }
  });
}

async function analyzeSample(sampleId) {
  const formData = new FormData();
  formData.append("sample_id", sampleId);
  formData.append("habitat", "temperate mixed forest");
  await executeAudioInference(formData);
}

async function uploadAndAnalyze(blobOrFile, filename = "upload.wav") {
  const formData = new FormData();
  formData.append("file", blobOrFile, filename);
  formData.append("habitat", "woodland edge / trail");
  await executeAudioInference(formData);
}

async function executeAudioInference(formData) {
  const loading = document.getElementById("bird-loading");
  const emptyState = document.getElementById("bird-empty-state");
  const details = document.getElementById("bird-result-details");
  const spectroImg = document.getElementById("spectrogram-image");
  const spectroContainer = document.getElementById("spectrogram-container");

  loading.style.display = "block";
  emptyState.style.display = "none";
  details.style.display = "none";

  try {
    const res = await fetch("/api/identify/audio", {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    currentBirdResult = data;

    // Display Spectrogram
    if (data.acoustics && data.acoustics.spectrogram_image) {
      spectroImg.src = data.acoustics.spectrogram_image;
      spectroContainer.style.display = "block";
    }

    // Display Metrics
    document.getElementById("metric-peak-freq").textContent = `${data.acoustics.dominant_frequency_hz} Hz`;
    document.getElementById("metric-centroid").textContent = `${data.acoustics.spectral_centroid_hz} Hz`;
    document.getElementById("metric-duration").textContent = `${data.acoustics.duration_seconds} s`;

    // Display Species & Reasoning
    const sp = data.identification;
    document.getElementById("res-species-name").textContent = sp.primary_species;
    document.getElementById("res-scientific-name").textContent = sp.scientific_name;
    document.getElementById("res-confidence").textContent = `${sp.confidence_percent}% Confidence`;
    document.getElementById("res-rationale").textContent = sp.acoustic_match_rationale;
    document.getElementById("res-visual-markers").textContent = sp.field_visual_markers;
    document.getElementById("res-behavior").textContent = sp.call_behavior;

    details.style.display = "block";
  } catch (err) {
    alert("Audio inference error: " + err);
    emptyState.style.display = "block";
  } finally {
    loading.style.display = "none";
  }
}

// ==========================================================================
// 4. TAB 3: GARDEN PLANNER & FROST ENGINE
// ==========================================================================

function initGardenPlanner() {
  const zoneSelect = document.getElementById("garden-zone-select");
  const btnAsk = document.getElementById("btn-garden-ask");
  const queryInput = document.getElementById("garden-query-input");

  zoneSelect.addEventListener("change", () => {
    loadGardenCalendar(zoneSelect.value);
  });

  btnAsk.addEventListener("click", async () => {
    const query = queryInput.value.trim();
    const zone = zoneSelect.value;
    const resultBox = document.getElementById("garden-advice-result");
    resultBox.innerHTML = "<em>Gemma 3 consulting organic soil wisdom...</em>";

    try {
      const res = await fetch("/api/garden/advice", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ zone, query })
      });
      const data = await res.json();
      resultBox.innerHTML = `<strong>Zone ${zone} Soil Guidance:</strong><br><br>${data.advice.replace(/\n/g, '<br>')}`;
    } catch (err) {
      resultBox.textContent = "Error: " + err;
    }
  });

  // Initial load
  loadGardenCalendar(zoneSelect.value);
}

async function loadGardenCalendar(zone) {
  try {
    const res = await fetch(`/api/garden/calendar?zone=${zone}`);
    const data = await res.json();

    document.getElementById("frost-days-num").textContent = `${data.days_to_fall_frost} Days`;
    document.getElementById("frost-target-date").textContent = `First Fall Frost: ${data.first_fall_frost}`;
    document.getElementById("frost-badge-status").textContent = data.season_status;
    document.getElementById("frost-urgency-title").textContent = data.urgency.split(':')[0] || "Active Planting Window";
    document.getElementById("frost-urgency-desc").textContent = data.urgency.split(':')[1] || data.urgency;

    // Render crop cards
    const container = document.getElementById("crop-cards-container");
    container.innerHTML = "";
    (data.recommended_crops || []).forEach(crop => {
      const card = document.createElement("div");
      card.className = "crop-card";
      card.innerHTML = `
        <div>
          <h4>${crop.name}</h4>
          <div class="category">${crop.category} • ${crop.hardiness}</div>
          <p>${crop.instructions}</p>
        </div>
        <div style="font-size: 0.78rem; color: var(--accent-amber); font-weight: 600;">
          ❄️ Strategy: ${crop.frost_strategy}
        </div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    console.error("Garden calendar error:", err);
  }
}

// ==========================================================================
// 5. TAB 4: TRAIL & RUN CLUB ROUTE BUILDER
// ==========================================================================

function initTrailBuilder() {
  const form = document.getElementById("trail-form");
  const btnDownloadGpx = document.getElementById("btn-download-gpx");
  const btnGeolocate = document.getElementById("btn-geolocate");

  // Init Leaflet map
  try {
    leafletMap = L.map('map-container').setView([40.7829, -73.9654], 14);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '© OpenStreetMap contributors'
    }).addTo(leafletMap);
  } catch (err) {
    console.warn("Leaflet map initialization notice:", err);
  }

  btnGeolocate.addEventListener("click", () => {
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition((pos) => {
        document.getElementById("trail-lat").value = pos.coords.latitude.toFixed(4);
        document.getElementById("trail-lng").value = pos.coords.longitude.toFixed(4);
        if (leafletMap) leafletMap.setView([pos.coords.latitude, pos.coords.longitude], 14);
      }, (err) => alert("Could not fetch location: " + err.message));
    } else {
      alert("Geolocation not supported by browser.");
    }
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const center_lat = parseFloat(document.getElementById("trail-lat").value);
    const center_lng = parseFloat(document.getElementById("trail-lng").value);
    const distance_km = parseFloat(document.getElementById("trail-dist").value);
    const route_type = document.getElementById("trail-type").value;

    try {
      const res = await fetch("/api/trail/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ center_lat, center_lng, distance_km, route_type })
      });
      const data = await res.json();
      lastGeneratedGpx = data.gpx_data;
      renderTrailRoute(data);
    } catch (err) {
      alert("Trail generation error: " + err);
    }
  });

  btnDownloadGpx.addEventListener("click", () => {
    if (!lastGeneratedGpx) {
      alert("Generate a route first to export GPX.");
      return;
    }
    const blob = new Blob([lastGeneratedGpx], { type: "application/gpx+xml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "foliage_loop_route.gpx";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });

  // Generate default initial route
  setTimeout(() => form.dispatchEvent(new Event('submit')), 300);
}

function renderTrailRoute(data) {
  document.getElementById("route-foliage-score").textContent = `Canopy Index: ${data.foliage_canopy_index}`;
  document.getElementById("route-duration-est").textContent = `Est: ${data.estimated_duration_minutes} Mins (${data.distance_km}km / +${data.elevation_gain_meters}m)`;
  document.getElementById("route-club-prompt").textContent = data.run_club_prompt;

  // Waypoints table
  const container = document.getElementById("waypoints-container");
  container.innerHTML = "";
  const latLngs = [];

  (data.waypoints || []).forEach((wp, idx) => {
    latLngs.push([wp.lat, wp.lng]);
    const item = document.createElement("div");
    item.className = "waypoint-item";
    item.innerHTML = `
      <div>
        <strong>#${wp.step}: ${wp.foliage_feature}</strong>
        <div style="font-size: 0.75rem; color: var(--text-muted);">${wp.foliage_palette} • Ele: ${wp.elevation_m}m</div>
      </div>
      <span class="foliage-badge">${wp.foliage_intensity_percent}% Foliage</span>
    `;
    container.appendChild(item);
  });

  // Update Leaflet map
  if (leafletMap && latLngs.length > 0) {
    if (currentRoutePolyline) leafletMap.removeLayer(currentRoutePolyline);
    currentMarkers.forEach(m => leafletMap.removeLayer(m));
    currentMarkers = [];

    currentRoutePolyline = L.polyline(latLngs, {
      color: '#f97316',
      weight: 5,
      opacity: 0.85,
      dashArray: '8, 8'
    }).addTo(leafletMap);

    // Add trailhead marker
    const startMarker = L.marker(latLngs[0]).addTo(leafletMap)
      .bindPopup("<b>Trailhead / Start</b><br>Regroup and begin your loop.")
      .openPopup();
    currentMarkers.push(startMarker);

    // Add peak foliage marker
    const midIdx = Math.floor(latLngs.length / 2);
    const midMarker = L.marker(latLngs[midIdx]).addTo(leafletMap)
      .bindPopup(`<b>Peak Foliage Overlook</b><br>${data.waypoints[midIdx].foliage_feature}`);
    currentMarkers.push(midMarker);

    leafletMap.fitBounds(currentRoutePolyline.getBounds(), { padding: [30, 30] });
  }
}

// ==========================================================================
// 6. TAB 5: OFFLINE FIELD JOURNAL
// ==========================================================================

function initJournal() {
  loadJournalObservations();

  document.getElementById("btn-export-csv").addEventListener("click", async () => {
    const res = await fetch("/api/journal/observations");
    const data = await res.json();
    if (!data.length) { alert("Journal is empty."); return; }
    
    let csv = "ID,Timestamp,Category,Species,ScientificName,Confidence,Location,Notes\n";
    data.forEach(r => {
      csv += `"${r.id}","${r.timestamp}","${r.category}","${r.species_name}","${r.scientific_name || ''}","${r.confidence || ''}","${r.location_name || ''}","${(r.notes || '').replace(/"/g, '""')}"\n`;
    });
    
    downloadFile(csv, "grounded_field_journal.csv", "text/csv");
  });

  document.getElementById("btn-export-md").addEventListener("click", async () => {
    const res = await fetch("/api/journal/observations");
    const data = await res.json();
    if (!data.length) { alert("Journal is empty."); return; }

    let md = "# Grounded: Offline Nature & Trail Journal\n\n";
    md += `*Exported on ${new Date().toLocaleDateString()} • Zero-Signal Local Field Records*\n\n`;
    data.forEach(r => {
      md += `### ${r.species_name} (*${r.scientific_name || 'Species'}*)\n`;
      md += `- **Date:** ${r.timestamp}\n`;
      md += `- **Category:** ${r.category} (Confidence: ${r.confidence}%)\n`;
      md += `- **Location:** ${r.location_name}\n`;
      md += `- **Notes:** ${r.notes}\n\n`;
    });

    downloadFile(md, "grounded_field_journal.md", "text/markdown");
  });
}

async function loadJournalObservations() {
  const tbody = document.getElementById("journal-table-body");
  try {
    const res = await fetch("/api/journal/observations");
    const data = await res.json();
    tbody.innerHTML = "";

    if (!data.length) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 24px;">No observations logged yet. Go outside and make your first sighting!</td></tr>`;
      return;
    }

    data.forEach(r => {
      const tr = document.createElement("tr");
      const dt = new Date(r.timestamp);
      tr.innerHTML = `
        <td>${dt.toLocaleDateString()} ${dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</td>
        <td><span class="pill">${r.category}</span></td>
        <td><strong>${r.species_name}</strong><br><small style="color: var(--text-muted);">${r.scientific_name || ''}</small></td>
        <td>${r.confidence ? r.confidence + '%' : '-'}</td>
        <td>${r.location_name || 'Trailside'}</td>
        <td style="max-width: 250px; font-size: 0.8rem;">${r.notes || '-'}</td>
        <td><button class="btn btn-secondary btn-sm" onclick="deleteObservation(${r.id})">🗑️</button></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Journal load error:", err);
  }
}

async function deleteObservation(id) {
  if (!confirm("Delete observation?")) return;
  await fetch(`/api/journal/observation/${id}`, { method: "DELETE" });
  loadJournalObservations();
}

function downloadFile(content, filename, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
