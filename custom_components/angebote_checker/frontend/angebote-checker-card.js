/**
 * angebote-checker-card
 * Custom Lovelace card for the Angebote Checker integration.
 * Displays supermarket offers found for shopping list items.
 *
 * @version 1.1.0
 * @author  Noack1978
 */

/* ─── Utility ──────────────────────────────────────────────────────────── */

const CARD_NAME    = "angebote-checker-card";
const EDITOR_NAME  = "angebote-checker-card-editor";
const CARD_VERSION = "1.1.0";

/* ─── Styles ────────────────────────────────────────────────────────────── */

const CARD_STYLES = `
  :host {
    --ac-bg:          var(--card-background-color, #1c1c2e);
    --ac-surface:     var(--secondary-background-color, #25253a);
    --ac-border:      var(--divider-color, rgba(255,255,255,0.08));
    --ac-accent:      var(--primary-color, #6c63ff);
    --ac-accent2:     #ff6b6b;
    --ac-text:        var(--primary-text-color, #e8e8f0);
    --ac-subtext:     var(--secondary-text-color, #9090b0);
    --ac-green:       #4ade80;
    --ac-radius:      14px;
    --ac-radius-sm:   8px;
    font-family: 'Segoe UI', system-ui, sans-serif;
  }

  .card-root {
    background: var(--ac-bg);
    border-radius: var(--ac-radius);
    overflow: hidden;
  }

  /* ── Header ── */
  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 16px 12px;
    border-bottom: 1px solid var(--ac-border);
    gap: 10px;
  }
  .header-left {
    display: flex;
    align-items: center;
    gap: 10px;
    flex: 1;
    min-width: 0;
  }
  .header-icon {
    width: 34px;
    height: 34px;
    border-radius: 10px;
    background: linear-gradient(135deg, var(--ac-accent), var(--ac-accent2));
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  .header-icon svg { width: 18px; height: 18px; fill: #fff; }

  .header-title {
    font-size: 15px;
    font-weight: 600;
    color: var(--ac-text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .header-subtitle {
    font-size: 11px;
    color: var(--ac-subtext);
    margin-top: 1px;
  }

  /* refresh button */
  .btn-refresh {
    background: var(--ac-surface);
    border: 1px solid var(--ac-border);
    border-radius: var(--ac-radius-sm);
    color: var(--ac-accent);
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 12px;
    font-weight: 600;
    padding: 6px 10px;
    transition: background 0.18s, transform 0.1s;
    white-space: nowrap;
    flex-shrink: 0;
  }
  .btn-refresh:hover  { background: var(--ac-accent); color: #fff; }
  .btn-refresh:active { transform: scale(0.95); }
  .btn-refresh svg    { width: 14px; height: 14px; fill: currentColor; transition: transform 0.4s; }
  .btn-refresh.spinning svg { animation: spin 0.9s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* ── Filter bar ── */
  .filter-bar {
    display: flex;
    gap: 6px;
    padding: 10px 16px;
    overflow-x: auto;
    scrollbar-width: none;
    border-bottom: 1px solid var(--ac-border);
  }
  .filter-bar::-webkit-scrollbar { display: none; }
  .filter-pill {
    background: var(--ac-surface);
    border: 1px solid var(--ac-border);
    border-radius: 20px;
    color: var(--ac-subtext);
    cursor: pointer;
    font-size: 11px;
    font-weight: 600;
    padding: 4px 10px;
    transition: all 0.15s;
    white-space: nowrap;
    user-select: none;
  }
  .filter-pill.active {
    background: var(--ac-accent);
    border-color: var(--ac-accent);
    color: #fff;
  }
  .filter-pill:hover:not(.active) { border-color: var(--ac-accent); color: var(--ac-text); }

  /* ── Content area ── */
  .card-content {
    padding: 12px 14px 14px;
    max-height: var(--ac-max-height, 500px);
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: var(--ac-border) transparent;
  }

  /* ── Offer grid ── */
  .offers-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 10px;
  }

  /* ── Offer card ── */
  .offer-card {
    background: var(--ac-surface);
    border: 1px solid var(--ac-border);
    border-radius: var(--ac-radius-sm);
    overflow: hidden;
    transition: transform 0.15s, box-shadow 0.15s;
    display: flex;
    flex-direction: column;
  }
  .offer-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.25);
  }

  .offer-img-wrap {
    position: relative;
    background: #111;
    height: 110px;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .offer-img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    padding: 6px;
  }
  .offer-img-placeholder {
    opacity: 0.18;
    width: 44px;
    height: 44px;
    fill: var(--ac-subtext);
  }

  .offer-retailer-badge {
    position: absolute;
    top: 6px;
    right: 6px;
    background: rgba(0,0,0,0.65);
    border-radius: 6px;
    color: #fff;
    font-size: 10px;
    font-weight: 700;
    padding: 2px 6px;
    backdrop-filter: blur(4px);
  }

  /* clickable image cursor */
  .offer-img-wrap.has-image { cursor: zoom-in; }

  /* ── Lightbox ── */
  .lightbox-overlay {
    position: fixed;
    inset: 0;
    z-index: 9999;
    background: rgba(0,0,0,0.85);
    display: flex;
    align-items: center;
    justify-content: center;
    backdrop-filter: blur(6px);
    animation: lb-in 0.18s ease;
  }
  @keyframes lb-in { from { opacity: 0; } to { opacity: 1; } }
  .lightbox-inner {
    position: relative;
    max-width: min(92vw, 560px);
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    animation: lb-scale 0.2s cubic-bezier(0.34,1.56,0.64,1);
  }
  @keyframes lb-scale { from { transform: scale(0.8); } to { transform: scale(1); } }
  .lightbox-img {
    max-width: 100%;
    max-height: 70vh;
    object-fit: contain;
    border-radius: 12px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.6);
    background: #111;
    padding: 12px;
  }
  .lightbox-caption {
    color: #fff;
    font-size: 14px;
    font-weight: 600;
    text-align: center;
    text-shadow: 0 1px 4px rgba(0,0,0,0.8);
  }
  .lightbox-sub {
    color: rgba(255,255,255,0.6);
    font-size: 11px;
    margin-top: 2px;
    text-align: center;
  }
  .lightbox-close {
    position: absolute;
    top: -14px;
    right: -14px;
    background: var(--ac-accent2);
    border: none;
    border-radius: 50%;
    color: #fff;
    cursor: pointer;
    width: 30px;
    height: 30px;
    font-size: 18px;
    line-height: 30px;
    text-align: center;
    padding: 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.4);
    transition: transform 0.15s;
  }
  .lightbox-close:hover { transform: scale(1.15); }

  /* ── Lightbox action buttons ── */
  .lightbox-actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    justify-content: center;
    width: 100%;
  }
  .lb-btn {
    background: var(--ac-surface, #25253a);
    border: 1px solid var(--ac-border, rgba(255,255,255,0.12));
    border-radius: 8px;
    color: var(--ac-text, #e8e8f0);
    cursor: pointer;
    font-size: 12px;
    font-weight: 600;
    padding: 7px 14px;
    transition: all 0.15s;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .lb-btn:hover { background: var(--ac-accent, #6c63ff); color: #fff; border-color: var(--ac-accent, #6c63ff); }
  .lb-btn.success { background: #4ade80; color: #0a2a10; border-color: #4ade80; }
  .lb-btn.error   { background: #ff6b6b; color: #fff; border-color: #ff6b6b; }

  /* ── List picker sheet ── */
  .list-picker {
    background: var(--ac-surface, #25253a);
    border: 1px solid var(--ac-border, rgba(255,255,255,0.12));
    border-radius: 12px;
    padding: 10px 8px;
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 220px;
    max-width: 320px;
  }
  .list-picker-title {
    color: var(--ac-subtext, #9090b0);
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 0 6px 4px;
    border-bottom: 1px solid var(--ac-border, rgba(255,255,255,0.08));
    margin-bottom: 2px;
  }
  .list-picker-item {
    background: none;
    border: none;
    border-radius: 7px;
    color: var(--ac-text, #e8e8f0);
    cursor: pointer;
    font-size: 13px;
    padding: 8px 10px;
    text-align: left;
    transition: background 0.12s;
  }
  .list-picker-item:hover { background: var(--ac-accent, #6c63ff); color: #fff; }

  .offer-body {
    padding: 9px 10px 10px;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 5px;
  }
  .offer-item-name {
    font-size: 11px;
    font-weight: 700;
    color: var(--ac-accent);
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }
  .offer-desc {
    font-size: 12.5px;
    color: var(--ac-text);
    line-height: 1.35;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  .offer-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: auto;
    padding-top: 6px;
  }
  .offer-price {
    font-size: 17px;
    font-weight: 800;
    color: var(--ac-green);
    letter-spacing: -0.02em;
  }
  .offer-period {
    font-size: 10px;
    color: var(--ac-subtext);
    text-align: right;
    line-height: 1.4;
  }
  .offer-period span { display: block; }

  /* ── List view ── */
  .offers-list { display: flex; flex-direction: column; gap: 7px; }
  .offer-row {
    background: var(--ac-surface);
    border: 1px solid var(--ac-border);
    border-radius: var(--ac-radius-sm);
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 9px 12px;
    transition: background 0.15s;
  }
  .offer-row:hover { background: color-mix(in srgb, var(--ac-surface) 80%, var(--ac-accent) 20%); }
  .offer-row-left { flex: 1; min-width: 0; }
  .offer-row-item {
    font-size: 10px;
    font-weight: 700;
    color: var(--ac-accent);
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }
  .offer-row-desc {
    font-size: 13px;
    color: var(--ac-text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .offer-row-retailer {
    font-size: 11px;
    color: var(--ac-subtext);
  }
  .offer-row-right { text-align: right; flex-shrink: 0; }
  .offer-row-price {
    font-size: 15px;
    font-weight: 800;
    color: var(--ac-green);
  }
  .offer-row-period {
    font-size: 10px;
    color: var(--ac-subtext);
    line-height: 1.3;
  }

  /* ── Empty / loading states ── */
  .state-box {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 32px 16px;
    gap: 10px;
    color: var(--ac-subtext);
    text-align: center;
  }
  .state-box svg { width: 44px; height: 44px; fill: var(--ac-subtext); opacity: 0.35; }
  .state-box p { font-size: 13px; margin: 0; }
  .state-box .hint { font-size: 11px; opacity: 0.7; }

  /* ── Footer ── */
  .card-footer {
    border-top: 1px solid var(--ac-border);
    color: var(--ac-subtext);
    font-size: 10.5px;
    padding: 7px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  /* ── View toggle ── */
  .view-toggle {
    display: flex;
    gap: 2px;
    background: var(--ac-surface);
    border: 1px solid var(--ac-border);
    border-radius: 7px;
    padding: 2px;
  }
  .view-btn {
    background: none;
    border: none;
    border-radius: 5px;
    color: var(--ac-subtext);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 4px 6px;
    transition: all 0.15s;
  }
  .view-btn svg { width: 14px; height: 14px; fill: currentColor; }
  .view-btn.active { background: var(--ac-accent); color: #fff; }
`;

/* ─── SVG icons ────────────────────────────────────────────────────────── */

const ICON_TAG    = `<svg viewBox="0 0 24 24"><path d="M21.41 11.58l-9-9A2 2 0 0 0 11 2H4a2 2 0 0 0-2 2v7a2 2 0 0 0 .59 1.42l9 9A2 2 0 0 0 13 22a2 2 0 0 0 1.41-.59l7-7A2 2 0 0 0 22 13a2 2 0 0 0-.59-1.42M5.5 7A1.5 1.5 0 0 1 4 5.5 1.5 1.5 0 0 1 5.5 4 1.5 1.5 0 0 1 7 5.5 1.5 1.5 0 0 1 5.5 7z"/></svg>`;
const ICON_REFRESH= `<svg viewBox="0 0 24 24"><path d="M17.65 6.35A7.96 7.96 0 0 0 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0 1 12 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg>`;
const ICON_GRID   = `<svg viewBox="0 0 24 24"><path d="M3 3h8v8H3zm0 10h8v8H3zM13 3h8v8h-8zm0 10h8v8h-8z"/></svg>`;
const ICON_LIST   = `<svg viewBox="0 0 24 24"><path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/></svg>`;
const ICON_EMPTY  = `<svg viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2zm-7 14l-5-5 1.41-1.41L12 14.17l7.59-7.59L21 8l-9 9z" opacity=".3"/><path d="M11.5 2C6.81 2 3 5.81 3 10.5S6.81 19 11.5 19h.5v3c4.86-2.34 8-7 8-11.5C20 5.81 16.19 2 11.5 2zm1 12.5h-2v-2h2v2zm0-4h-2c0-3.25 3-3 3-5 0-1.1-.9-2-2-2s-2 .9-2 2h-2c0-2.21 1.79-4 4-4s4 1.79 4 4c0 2.5-3 2.75-3 5z"/></svg>`;

/* ─── Helper ────────────────────────────────────────────────────────────── */

function el(tag, attrs = {}, ...children) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") e.className = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else e.setAttribute(k, v);
  }
  for (const c of children) {
    if (c == null) continue;
    e.append(typeof c === "string" ? document.createTextNode(c) : c);
  }
  return e;
}

/* ─── Main card element ─────────────────────────────────────────────────── */

class AngeboteCheckerCard extends HTMLElement {
  static get properties() {
    return { hass: {}, config: {} };
  }

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config    = {};
    this._hass      = null;
    this._activeFilter = "all";
    this._view      = "grid"; // "grid" | "list"
    this._spinning  = false;
    this._rendered  = false;
  }

  /* Called by HA with new hass object on every state change */
  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  setConfig(config) {
    if (!config.entity) throw new Error("entity ist erforderlich.");
    this._config = {
      title:      config.title      ?? "Angebote",
      entity:     config.entity,
      max_height: config.max_height ?? 500,
      show_images:config.show_images ?? true,
      default_view: config.default_view ?? "grid",
    };
    this._view = this._config.default_view;
    this._rendered = false;
  }

  getCardSize() { return 4; }

  /* ── Build shadow DOM once, then patch ── */
  _render() {
    if (!this._hass || !this._config.entity) return;

    const stateObj = this._hass.states[this._config.entity];
    const offers   = stateObj?.attributes?.offers ?? [];
    const lastUpdate = stateObj?.attributes?.last_update ?? "";

    const filtered = this._activeFilter === "all"
      ? offers
      : offers.filter(o => o.retailer === this._activeFilter);

    const retailers = [...new Set(offers.map(o => o.retailer))].sort();

    /* Full re-render on first call */
    if (!this._rendered) {
      this._buildSkeleton();
      this._rendered = true;
    }

    this._updateHeader(offers.length, lastUpdate, stateObj);
    this._updateFilters(retailers);
    this._updateContent(filtered, stateObj);
    this._updateFooter(lastUpdate, filtered.length, offers.length);
    this._updateMaxHeight();
  }

  _buildSkeleton() {
    const shadow = this.shadowRoot;
    shadow.innerHTML = "";

    const style = document.createElement("style");
    style.textContent = CARD_STYLES;
    shadow.appendChild(style);

    const root = el("ha-card", { class: "card-root" });

    this._headerEl  = el("div",  { class: "card-header" });
    this._filterEl  = el("div",  { class: "filter-bar" });
    this._contentEl = el("div",  { class: "card-content" });
    this._footerEl  = el("div",  { class: "card-footer" });

    root.append(this._headerEl, this._filterEl, this._contentEl, this._footerEl);
    shadow.appendChild(root);
  }

  _updateMaxHeight() {
    const maxH = this._config.max_height;
    if (this._contentEl) {
      this._contentEl.style.maxHeight = `${maxH}px`;
    }
  }

  _updateHeader(total, lastUpdate, stateObj) {
    const unavailable = !stateObj || stateObj.state === "unavailable";

    this._headerEl.innerHTML = "";

    const left = el("div", { class: "header-left" });
    const iconWrap = el("div", { class: "header-icon" });
    iconWrap.innerHTML = ICON_TAG;

    const titleWrap = el("div");
    const titleEl   = el("div", { class: "header-title" }, this._config.title);
    const subEl     = el("div", { class: "header-subtitle" });
    subEl.textContent = unavailable
      ? "Sensor nicht verfügbar"
      : `${total} Angebote gefunden`;
    titleWrap.append(titleEl, subEl);
    left.append(iconWrap, titleWrap);

    /* View toggle */
    const toggle = el("div", { class: "view-toggle" });
    const btnGrid = el("button", {
      class: `view-btn${this._view === "grid" ? " active" : ""}`,
      onclick: () => { this._view = "grid"; this._rendered = false; this._render(); },
    });
    btnGrid.innerHTML = ICON_GRID;
    const btnList = el("button", {
      class: `view-btn${this._view === "list" ? " active" : ""}`,
      onclick: () => { this._view = "list"; this._rendered = false; this._render(); },
    });
    btnList.innerHTML = ICON_LIST;
    toggle.append(btnGrid, btnList);

    /* Refresh button */
    const btnRefresh = el("button", {
      class: `btn-refresh${this._spinning ? " spinning" : ""}`,
      onclick: () => this._callRefresh(btnRefresh),
    });
    btnRefresh.innerHTML = ICON_REFRESH + `<span>Suchen</span>`;

    this._headerEl.append(left, toggle, btnRefresh);
  }

  _updateFilters(retailers) {
    this._filterEl.innerHTML = "";

    if (retailers.length === 0) {
      this._filterEl.style.display = "none";
      return;
    }
    this._filterEl.style.display = "";

    const all = el("button", {
      class: `filter-pill${this._activeFilter === "all" ? " active" : ""}`,
      onclick: () => { this._activeFilter = "all"; this._render(); },
    }, "Alle");
    this._filterEl.append(all);

    for (const r of retailers) {
      const pill = el("button", {
        class: `filter-pill${this._activeFilter === r ? " active" : ""}`,
        onclick: () => { this._activeFilter = r; this._render(); },
      }, r);
      this._filterEl.append(pill);
    }
  }

  _updateContent(offers, stateObj) {
    this._contentEl.innerHTML = "";

    const unavailable = !stateObj || stateObj.state === "unavailable";
    if (unavailable) {
      const box = el("div", { class: "state-box" });
      box.innerHTML = ICON_EMPTY;
      box.append(
        el("p", {}, "Sensor nicht verfügbar"),
        el("p", { class: "hint" }, `Prüfe ob der Sensor ${this._config.entity} existiert.`),
      );
      this._contentEl.append(box);
      return;
    }

    if (offers.length === 0) {
      const box = el("div", { class: "state-box" });
      box.innerHTML = ICON_EMPTY;
      box.append(
        el("p", {}, "Keine Angebote gefunden"),
        el("p", { class: "hint" }, "Klicke auf 'Suchen' für eine neue Abfrage."),
      );
      this._contentEl.append(box);
      return;
    }

    if (this._view === "grid") {
      const grid = el("div", { class: "offers-grid" });
      for (const offer of offers) grid.append(this._buildOfferCard(offer));
      this._contentEl.append(grid);
    } else {
      const list = el("div", { class: "offers-list" });
      for (const offer of offers) list.append(this._buildOfferRow(offer));
      this._contentEl.append(list);
    }
  }

  _buildOfferCard(offer) {
    const card = el("div", { class: "offer-card" });

    /* Image area */
    const imgWrap = el("div", { class: "offer-img-wrap" });
    if (this._config.show_images && offer.image_url) {
      imgWrap.classList.add("has-image");
      imgWrap.onclick = () => this._openLightbox(offer);
      const img = el("img", { class: "offer-img", src: offer.image_url, alt: offer.description });
      img.onerror = () => {
        imgWrap.classList.remove("has-image");
        imgWrap.onclick = null;
        imgWrap.innerHTML = "";
        const ph = document.createElement("div");
        ph.innerHTML = `<svg class="offer-img-placeholder" viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-1 16H6l3.5-4.5 2.5 3.01L15 12l4 7z"/></svg>`;
        imgWrap.appendChild(ph.firstChild);
      };
      imgWrap.append(img);
    } else {
      const ph = document.createElement("div");
      ph.innerHTML = `<svg class="offer-img-placeholder" viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-1 16H6l3.5-4.5 2.5 3.01L15 12l4 7z"/></svg>`;
      imgWrap.appendChild(ph.firstChild);
    }

    const badge = el("div", { class: "offer-retailer-badge" }, offer.retailer);
    imgWrap.append(badge);

    /* Body */
    const body = el("div", { class: "offer-body" });
    const itemName = el("div", { class: "offer-item-name" }, offer.item ?? "");
    const desc     = el("div", { class: "offer-desc" }, offer.description ?? "");
    const footer   = el("div", { class: "offer-footer" });
    const price    = el("div", { class: "offer-price" }, offer.price ?? "—");
    const period   = el("div", { class: "offer-period" });
    period.innerHTML = `<span>${offer.valid_from ?? ""}</span><span>bis ${offer.valid_to ?? ""}</span>`;
    footer.append(price, period);
    body.append(itemName, desc, footer);

    card.append(imgWrap, body);
    return card;
  }

  _buildOfferRow(offer) {
    const row = el("div", { class: "offer-row" });
    const left = el("div", { class: "offer-row-left" });
    left.append(
      el("div", { class: "offer-row-item" },     offer.item ?? ""),
      el("div", { class: "offer-row-desc" },     offer.description ?? ""),
      el("div", { class: "offer-row-retailer" }, offer.retailer ?? ""),
    );
    const right = el("div", { class: "offer-row-right" });
    const period = el("div", { class: "offer-row-period" });
    period.innerHTML = `${offer.valid_from ?? ""}–${offer.valid_to ?? ""}`;
    right.append(
      el("div", { class: "offer-row-price" }, offer.price ?? "—"),
      period,
    );
    row.append(left, right);
    return row;
  }

  _updateFooter(lastUpdate, shown, total) {
    this._footerEl.innerHTML = "";
    const ts = lastUpdate ? lastUpdate.replace("T", " ").slice(0, 16) : "—";
    this._footerEl.append(
      el("span", {}, `Stand: ${ts}`),
      el("span", {}, shown < total ? `${shown} / ${total} Angebote` : `${total} Angebote`),
    );
  }


  _openLightbox(offer) {
    this._closeLightbox();

    const overlay = document.createElement("div");
    overlay.className = "lightbox-overlay";

    const inner = document.createElement("div");
    inner.className = "lightbox-inner";

    // Close button
    const closeBtn = document.createElement("button");
    closeBtn.className = "lightbox-close";
    closeBtn.innerHTML = "&#x2715;";
    closeBtn.onclick = (e) => { e.stopPropagation(); this._closeLightbox(); };

    // Image
    const img = document.createElement("img");
    img.className = "lightbox-img";
    img.src = offer.image_url;
    img.alt = offer.description || offer.item;

    // Caption
    const caption = document.createElement("div");
    caption.className = "lightbox-caption";
    caption.textContent = offer.description || offer.item || "";

    const sub = document.createElement("div");
    sub.className = "lightbox-sub";
    sub.textContent = `${offer.retailer}  ·  ${offer.price}  ·  ${offer.valid_from || ""}${offer.valid_to ? " – " + offer.valid_to : ""}`;

    // Action buttons
    const actions = document.createElement("div");
    actions.className = "lightbox-actions";

    // Button: Artikel ergänzen
    const btnEnrich = document.createElement("button");
    btnEnrich.className = "lb-btn";
    btnEnrich.innerHTML = `&#x270F; Artikel ergänzen`;
    btnEnrich.title = `Umbenennen zu: "${offer.item} (${offer.retailer} ${offer.price})"`;
    btnEnrich.onclick = (e) => { e.stopPropagation(); this._enrichItem(offer, btnEnrich); };

    // Button: Auf Liste verschieben
    const btnMove = document.createElement("button");
    btnMove.className = "lb-btn";
    btnMove.innerHTML = `&#x27A1; Auf Liste verschieben`;
    btnMove.onclick = (e) => { e.stopPropagation(); this._showListPicker(offer, inner, btnMove); };

    actions.append(btnEnrich, btnMove);
    inner.append(closeBtn, img, caption, sub, actions);
    overlay.appendChild(inner);

    overlay.onclick = (e) => { if (e.target === overlay) this._closeLightbox(); };
    this._lightboxKeyHandler = (e) => { if (e.key === "Escape") this._closeLightbox(); };
    document.addEventListener("keydown", this._lightboxKeyHandler);

    this.shadowRoot.appendChild(overlay);
    this._lightboxEl = overlay;
  }

  /** Rename the todo item to include price/retailer info */
  async _enrichItem(offer, btn) {
    const newName = `${offer.item} (${offer.retailer} ${offer.price})`;
    const sourceLists = this._config.source_lists
      || this._hass?.states?.[this._config.entity]?.attributes?.source_lists
      || [];

    // Find which list contains this item (try all configured lists)
    const stateObj = this._hass.states[this._config.entity];
    const allLists = stateObj?.attributes?.todo_lists ?? sourceLists;

    let found = false;
    for (const listId of allLists) {
      try {
        const result = await this._hass.callService("todo", "update_item", {
          entity_id: listId,
          item: offer.item,
          rename: newName,
        }, true);
        found = true;
        break;
      } catch (_) { /* try next list */ }
    }

    if (found) {
      btn.classList.add("success");
      btn.innerHTML = `&#x2713; Umbenannt`;
      setTimeout(() => {
        btn.classList.remove("success");
        btn.innerHTML = `&#x270F; Artikel ergänzen`;
      }, 2500);
    } else {
      btn.classList.add("error");
      btn.innerHTML = `&#x2715; Fehler`;
      setTimeout(() => {
        btn.classList.remove("error");
        btn.innerHTML = `&#x270F; Artikel ergänzen`;
      }, 2500);
    }
  }

  /** Show a list picker to move the item to another todo list */
  _showListPicker(offer, inner, btnMove) {
    // Remove existing picker if open (toggle)
    const existing = inner.querySelector(".list-picker");
    if (existing) { existing.remove(); return; }

    const allLists = this._getAllTodoLists();
    if (!allLists.length) return;

    const picker = document.createElement("div");
    picker.className = "list-picker";

    const title = document.createElement("div");
    title.className = "list-picker-title";
    title.textContent = "Ziel-Liste wählen";
    picker.appendChild(title);

    for (const { id, name } of allLists) {
      const item = document.createElement("button");
      item.className = "list-picker-item";
      item.textContent = name;
      item.onclick = async (e) => {
        e.stopPropagation();
        await this._moveItem(offer, id, btnMove);
        picker.remove();
      };
      picker.appendChild(item);
    }

    inner.appendChild(picker);
  }

  /** Move item: add to target list, remove from source list */
  async _moveItem(offer, targetListId, btn) {
    const stateObj = this._hass.states[this._config.entity];
    const sourceLists = stateObj?.attributes?.todo_lists ?? [];

    try {
      // Add to target list
      await this._hass.callService("todo", "add_item", {
        entity_id: targetListId,
        item: offer.item,
      });

      // Remove from all source lists
      for (const listId of sourceLists) {
        if (listId === targetListId) continue;
        try {
          await this._hass.callService("todo", "remove_item", {
            entity_id: listId,
            item: offer.item,
          });
        } catch (_) { /* item may not be on this list */ }
      }

      btn.classList.add("success");
      const targetName = this._hass.states[targetListId]?.attributes?.friendly_name ?? targetListId;
      btn.innerHTML = `&#x2713; Verschoben nach ${targetName}`;
      setTimeout(() => {
        btn.classList.remove("success");
        btn.innerHTML = `&#x27A1; Auf Liste verschieben`;
      }, 3000);
    } catch (err) {
      btn.classList.add("error");
      btn.innerHTML = `&#x2715; Fehler`;
      setTimeout(() => {
        btn.classList.remove("error");
        btn.innerHTML = `&#x27A1; Auf Liste verschieben`;
      }, 2500);
    }
  }

  /** Return all todo entities known to hass as [{id, name}] */
  _getAllTodoLists() {
    if (!this._hass) return [];
    return Object.entries(this._hass.states)
      .filter(([id]) => id.startsWith("todo."))
      .map(([id, state]) => ({
        id,
        name: state.attributes?.friendly_name ?? id,
      }))
      .sort((a, b) => a.name.localeCompare(b.name));
  }

  _closeLightbox() {
    if (this._lightboxEl) {
      this._lightboxEl.remove();
      this._lightboxEl = null;
    }
    if (this._lightboxKeyHandler) {
      document.removeEventListener("keydown", this._lightboxKeyHandler);
      this._lightboxKeyHandler = null;
    }
  }

  async _callRefresh(btn) {
    if (!this._hass || this._spinning) return;
    this._spinning = true;
    btn.classList.add("spinning");
    try {
      await this._hass.callService("angebote_checker", "refresh", {});
    } catch (e) {
      console.error("angebote_checker.refresh:", e);
    }
    /* keep spinner for at least 1.5 s so the user sees feedback */
    setTimeout(() => {
      this._spinning = false;
      btn.classList.remove("spinning");
    }, 1500);
  }

  static getConfigElement() {
    return document.createElement(EDITOR_NAME);
  }

  static getStubConfig(hass) {
    const entity = Object.keys(hass.states)
      .find(e => e.startsWith("sensor.angebote_checker")) ?? "";
    return { entity, title: "Angebote", max_height: 500, show_images: true, default_view: "grid" };
  }
}

/* ─── Visual Editor ──────────────────────────────────────────────────────── */

const EDITOR_STYLES = `
  .editor { display: flex; flex-direction: column; gap: 12px; padding: 4px 0; }
  .editor-row { display: flex; flex-direction: column; gap: 4px; }
  .editor-label { font-size: 12px; font-weight: 600; color: var(--secondary-text-color); }
  .editor-row ha-entity-picker,
  .editor-row ha-textfield,
  .editor-row ha-select { width: 100%; }
  .editor-row ha-formfield { display: flex; align-items: center; }
  .editor-hint { font-size: 11px; color: var(--secondary-text-color); opacity: 0.8; }
`;

class AngeboteCheckerCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
  }

  setConfig(config) {
    this._config = { ...config };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._rendered) this._render();
  }

  _render() {
    if (!this._hass) return;
    this._rendered = true;
    const shadow = this.shadowRoot;
    shadow.innerHTML = `<style>${EDITOR_STYLES}</style>`;

    const editor = document.createElement("div");
    editor.className = "editor";

    /* Entity picker */
    editor.append(this._row("Sensor-Entität *", this._entityPicker()));

    /* Title */
    editor.append(this._row("Kartentitel", this._textField(
      "title", this._config.title ?? "Angebote", "Angebote", "mdi:tag"
    )));

    /* Max height */
    editor.append(this._row("Maximale Höhe (px)", this._textField(
      "max_height", this._config.max_height ?? 500, "500", "mdi:arrow-expand-vertical", "number"
    )));

    /* Default view */
    editor.append(this._row("Standard-Ansicht", this._select(
      "default_view",
      [["grid","Kacheln (Grid)"],["list","Liste"]],
      this._config.default_view ?? "grid"
    )));

    /* Show images */
    editor.append(this._checkRow("Produktbilder anzeigen", "show_images",
      this._config.show_images ?? true));

    shadow.appendChild(editor);
  }

  _row(label, ...children) {
    const wrap = document.createElement("div");
    wrap.className = "editor-row";
    const lbl = document.createElement("div");
    lbl.className = "editor-label";
    lbl.textContent = label;
    wrap.append(lbl, ...children);
    return wrap;
  }

  _entityPicker() {
    const picker = document.createElement("ha-entity-picker");
    picker.hass = this._hass;
    picker.value = this._config.entity ?? "";
    picker.allowCustomEntity = true;
    picker.includeDomains = ["sensor"];
    picker.addEventListener("value-changed", e => {
      this._config = { ...this._config, entity: e.detail.value };
      this._fire();
    });
    return picker;
  }

  _textField(key, value, placeholder, icon, type = "text") {
    const field = document.createElement("ha-textfield");
    field.value = value;
    field.placeholder = placeholder;
    field.type = type;
    if (icon) field.setAttribute("icon", icon);
    field.addEventListener("change", e => {
      const v = type === "number" ? Number(e.target.value) : e.target.value;
      this._config = { ...this._config, [key]: v };
      this._fire();
    });
    return field;
  }

  _select(key, options, value) {
    const sel = document.createElement("ha-select");
    sel.value = value;
    for (const [val, label] of options) {
      const opt = document.createElement("mwc-list-item");
      opt.value = val;
      opt.textContent = label;
      sel.appendChild(opt);
    }
    sel.addEventListener("selected", e => {
      const v = options[e.detail.index]?.[0];
      if (v !== undefined) {
        this._config = { ...this._config, [key]: v };
        this._fire();
      }
    });
    return sel;
  }

  _checkRow(label, key, value) {
    const wrap = document.createElement("div");
    wrap.className = "editor-row";
    const ff = document.createElement("ha-formfield");
    ff.label = label;
    const cb = document.createElement("ha-checkbox");
    cb.checked = value;
    cb.addEventListener("change", e => {
      this._config = { ...this._config, [key]: e.target.checked };
      this._fire();
    });
    ff.appendChild(cb);
    wrap.appendChild(ff);
    return wrap;
  }

  _fire() {
    this.dispatchEvent(new CustomEvent("config-changed", {
      detail: { config: this._config },
      bubbles: true,
      composed: true,
    }));
  }
}

/* ─── Register elements ──────────────────────────────────────────────────── */

customElements.define(EDITOR_NAME, AngeboteCheckerCardEditor);

customElements.define(CARD_NAME, AngeboteCheckerCard);


/* ─── Register in HACS / Lovelace custom card registry ────────────────── */

window.customCards = window.customCards ?? [];
window.customCards.push({
  type: CARD_NAME,
  name: "Angebote Checker",
  description: "Zeigt aktuelle Supermarkt-Angebote deiner Einkaufslisten an.",
  preview: true,
  documentationURL: "https://github.com/Noack1978/ha-angebote-checker",
});

console.info(
  `%c ANGEBOTE-CHECKER-CARD %c v${CARD_VERSION} `,
  "background:#6c63ff;color:#fff;font-weight:700;border-radius:4px 0 0 4px;padding:2px 6px",
  "background:#222;color:#6c63ff;font-weight:700;border-radius:0 4px 4px 0;padding:2px 6px",
);
