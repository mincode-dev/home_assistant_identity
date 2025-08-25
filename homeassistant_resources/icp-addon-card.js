// /config/www/icp_addon/icp-addon-card.js
class IcpAddonCard extends HTMLElement {
  setConfig(config) {
    const defaults = {
      title: "ICP Card",
      api_base: "http://127.0.0.1:8099",
      identity_url: "http://127.0.0.1:8099/api/v1/identity",
      layout_density: "comfortable",
      collapse_actions: false,
      // (the old primary actions remain available; not used in this layout)
      primary_actions: {
        add:    { label: "Add",    icon: "mdi:plus",               prompt_label: "Name", prompt_placeholder: "Enter name", prompt_key: "name" },
        list:   { label: "List",   icon: "mdi:format-list-bulleted" },
        delete: { label: "Delete", icon: "mdi:trash-can", confirm: true },
      }
    };
    this._config = { ...defaults, ...config };
    if (this.shadowRoot) this._render();
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._init) {
      this.attachShadow({ mode: "open" });
      this._identity = null;
      this._identityStatus = "idle";
      this._init = true;
      this._fetchIdentity();
    }
    this._render();
  }

  getCardSize() { return 6; }

  // ---------- API helpers ----------
  async _api(path, { method = "GET", json } = {}) {
    const url = path.startsWith("http") ? path : `${this._config.api_base}${path}`;
    const opts = { method, headers: {} };
    if (json !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(json);
    }
    const r = await fetch(url, opts);
    const data = await r.json().catch(() => ({}));
    if (!r.ok || data.status === "error") {
      const msg = data?.message || `HTTP ${r.status}`;
      throw new Error(msg);
    }
    return data;
  }

  _showResult(title, obj) {
    const dlg = this.shadowRoot.getElementById("resultDialog");
    if (!dlg) return;
    dlg.heading = title || "Result";
    const pre = dlg.querySelector("pre");
    pre.textContent = typeof obj === "string" ? obj : JSON.stringify(obj, null, 2);
    dlg.open = true;
  }

  _notify(msg) {
    const s = this.shadowRoot.getElementById("toast");
    if (!s) return;
    s.labelText = msg;
    s.open = false;
    setTimeout(() => (s.open = true), 0);
  }

  // ---------- Identity ----------
  async _fetchIdentity() {
    if (this._identityStatus === "loading") return;
    this._identityStatus = "loading";
    this._render();
    try {
      const resp = await this._api(this._config.identity_url);
      if (resp && resp.status === "success" && resp.identity) {
        this._identity = {
          principal: String(resp.identity.principal || ""),
          public_key: String(resp.identity.public_key || "")
        };
        this._identityStatus = "success";
      } else {
        this._identity = null;
        this._identityStatus = "error";
      }
    } catch (e) {
      console.error("Identity fetch failed:", e);
      this._identity = null;
      this._identityStatus = "error";
    }
    this._render();
  }

  async _regenerateIdentity() {
    try {
      const resp = await this._api("/api/v1/identity/regenerate");
      const id = resp?.identity || {};
      this._identity = {
        principal: String(id.principal || ""),
        public_key: String(id.public_key || "")
      };
      this._identityStatus = "success";
      this._render();
      this._notify("Identity regenerated");
    } catch (e) {
      console.error(e);
      this._notify(`Regenerate failed: ${e.message}`);
    }
  }

  // ---------- render ----------
  _render() {
    if (!this.shadowRoot) return;
    const comfortable = (this._config.layout_density || "comfortable") === "comfortable";

    const css = `
      :host { --pad:${comfortable ? 16 : 12}px; --gap:${comfortable ? 12 : 8}px; --radius:12px; }
      ha-card { padding: var(--pad); }
      .header { display:flex; align-items:center; justify-content:space-between; gap: var(--gap); margin-bottom:${comfortable ? 8 : 6}px; }
      .title { font-weight:600; font-size:${comfortable ? "1.1rem" : "1rem"}; }

      .idwrap { margin: 4px 0 ${comfortable ? 12 : 8}px; border:1px solid var(--divider-color); border-radius: var(--radius); padding:${comfortable ? 12 : 10}px; }
      .idrow { display:grid; grid-template-columns: 120px 1fr auto; gap:6px 10px; align-items:center; }
      .idlabel { color: var(--secondary-text-color); font-size:0.9rem; }
      .idvalue {
        font-family: var(--code-font-family, ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace);
        font-size:0.9rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width: 28ch;
      }
      .copy-btn {
        justify-self: end; width:36px; height:36px; display:grid; place-items:center;
        border-radius:50%; border:1px solid var(--divider-color);
        background: transparent; color: var(--secondary-text-color);
        cursor: pointer; transition: transform .12s ease, color .12s ease, border-color .12s ease;
      }
      .copy-btn:hover { background: rgba(255,255,255,0.06); }
      .copy-btn[disabled] { opacity: 0.4; pointer-events: none; }
      .copy-btn ha-icon { --mdc-icon-size: 20px; }
      .copy-btn.copied { border-color: var(--primary-color); color: var(--primary-color); transform: scale(0.95); }

      .toolbar { margin-top:10px; display:flex; gap:8px; flex-wrap: wrap; }
      .section { border:1px solid var(--divider-color); border-radius: var(--radius); padding:${comfortable ? 12 : 10}px; margin-top:${comfortable ? 12 : 8}px; }
      .section h4 { margin:0 0 ${comfortable ? 8 : 6}px; font-size:0.95rem; font-weight:600; }

      .grid-2 { display:grid; grid-template-columns: repeat(2, minmax(140px, 1fr)); gap:${comfortable ? 10 : 8}px; }
      .grid-3 { display:grid; grid-template-columns: repeat(3, minmax(140px, 1fr)); gap:${comfortable ? 10 : 8}px; }
      mwc-button[unelevated]{ border-radius:12px; }
      .hint { color: var(--secondary-text-color); font-size:0.9rem; margin-top:${comfortable ? 6 : 4}px; }

      .spacer { height:${comfortable ? 4 : 2}px; }
      .form-row { display:grid; gap:8px; margin:8px 0; }
      .stack { display:grid; gap:10px; }
      pre { margin:0; white-space:pre-wrap; word-break:break-word; }
    `;

    const idBlock = this._renderIdentityBlock();
    const identityActions = `
      <div class="section">
        <h4>Identity</h4>
        <div class="grid-2">
          <mwc-button outlined id="btnRegenerate"><ha-icon icon="mdi:autorenew"></ha-icon>&nbsp;Regenerate</mwc-button>
          <mwc-button outlined id="btnRefreshId"><ha-icon icon="mdi:refresh"></ha-icon>&nbsp;Refresh</mwc-button>
        </div>
      </div>
    `;

    const canisterActions = `
      <div class="section">
        <h4>Canisters</h4>
        <div class="grid-3">
          <mwc-button unelevated id="btnList"><ha-icon icon="mdi:format-list-bulleted"></ha-icon>&nbsp;List</mwc-button>
          <mwc-button unelevated id="btnGet"><ha-icon icon="mdi:magnify"></ha-icon>&nbsp;Get</mwc-button>
          <mwc-button unelevated id="btnAdd"><ha-icon icon="mdi:plus-box"></ha-icon>&nbsp;Add</mwc-button>
          <mwc-button unelevated id="btnCall"><ha-icon icon="mdi:play-circle"></ha-icon>&nbsp;Call method</mwc-button>
          <mwc-button unelevated id="btnMethods"><ha-icon icon="mdi:code-tags"></ha-icon>&nbsp;Get methods</mwc-button>
          <mwc-button unelevated id="btnDelete"><ha-icon icon="mdi:trash-can"></ha-icon>&nbsp;Delete</mwc-button>
        </div>
        <div class="hint">Operations call your local API at ${this._config.api_base}.</div>
      </div>
    `;

    this.shadowRoot.innerHTML = `
      <style>${css}</style>
      <ha-card>
        <div class="header">
          <div class="title">${this._config.title || ""}</div>
          <div></div>
        </div>

        ${idBlock}
        ${identityActions}
        ${canisterActions}

        <!-- Dialogs -->
        <ha-dialog id="dlgGet" heading="Get canister">
          <div class="form-row">
            <ha-textfield label="Canister name" id="inGetName" style="width:100%"></ha-textfield>
          </div>
          <div slot="primaryAction" class="stack">
            <mwc-button id="doGet" unelevated>Fetch</mwc-button>
            <mwc-button dialogAction="close">Close</mwc-button>
          </div>
        </ha-dialog>

        <ha-dialog id="dlgAdd" heading="Add canister">
          <div class="form-row">
            <ha-textfield label="Canister ID" id="inAddId" style="width:100%"></ha-textfield>
            <ha-textfield label="Canister name (optional)" id="inAddName" style="width:100%"></ha-textfield>
          </div>
          <div slot="primaryAction" class="stack">
            <mwc-button id="doAdd" unelevated>Add</mwc-button>
            <mwc-button dialogAction="close">Close</mwc-button>
          </div>
        </ha-dialog>

        <ha-dialog id="dlgCall" heading="Call canister method">
          <div class="form-row">
            <ha-textfield label="Canister name" id="inCallName" style="width:100%"></ha-textfield>
            <ha-textfield label="Method name" id="inCallMethod" style="width:100%"></ha-textfield>
            <ha-textfield label='Args (JSON, e.g. [] or ["alice"])' id="inCallArgs" style="width:100%"></ha-textfield>
          </div>
          <div slot="primaryAction" class="stack">
            <mwc-button id="doCall" unelevated>Call</mwc-button>
            <mwc-button dialogAction="close">Close</mwc-button>
          </div>
        </ha-dialog>

        <ha-dialog id="dlgMethods" heading="Get canister methods">
          <div class="form-row">
            <ha-textfield label="Canister name" id="inMethName" style="width:100%"></ha-textfield>
          </div>
          <div slot="primaryAction" class="stack">
            <mwc-button id="doMethods" unelevated>Fetch</mwc-button>
            <mwc-button dialogAction="close">Close</mwc-button>
          </div>
        </ha-dialog>

        <ha-dialog id="dlgDelete" heading="Delete canister">
          <div class="form-row">
            <ha-textfield label="Canister name" id="inDelName" style="width:100%"></ha-textfield>
          </div>
          <div slot="primaryAction" class="stack">
            <mwc-button id="doDelete" unelevated>Delete</mwc-button>
            <mwc-button dialogAction="close">Close</mwc-button>
          </div>
        </ha-dialog>

        <ha-dialog id="resultDialog" heading="Result">
          <pre id="resultPre"></pre>
          <div slot="primaryAction" class="stack">
            <mwc-button dialogAction="close">Close</mwc-button>
          </div>
        </ha-dialog>

        <mwc-snackbar id="toast"></mwc-snackbar>
      </ha-card>
    `;

    this._wireHandlers();
  }

  _renderIdentityBlock() {
    const s = this._identityStatus;
    const p = this._identity?.principal || "";
    const k = this._identity?.public_key || "";
    const statusText = (value) => value || (s === "loading" || s === "idle" ? "loading…" : "unavailable");

    const principalRow = `
      <div class="idrow">
        <div class="idlabel">Principal</div>
        <div class="idvalue" title="${p}">${statusText(p)}</div>
        <button class="copy-btn" title="Copy principal" data-copy="principal" ${p ? "" : "disabled"}>
          <ha-icon icon="mdi:content-copy"></ha-icon>
        </button>
      </div>`;

    const keyRow = `
      <div class="idrow">
        <div class="idlabel">Public key</div>
        <div class="idvalue" title="${k}">${statusText(k)}</div>
        <button class="copy-btn" title="Copy public key" data-copy="public_key" ${k ? "" : "disabled"}>
          <ha-icon icon="mdi:content-copy"></ha-icon>
        </button>
      </div>`;

    return `<div class="idwrap">${principalRow}<div class="spacer"></div>${keyRow}</div>`;
  }

  // ---------- event wiring ----------
  _wireHandlers() {
    const $ = (sel) => this.shadowRoot.querySelector(sel);

    // Copy buttons with feedback
    this.shadowRoot.querySelectorAll('button.copy-btn').forEach(btn => {
      btn.addEventListener("click", async (e) => {
        const key = e.currentTarget.getAttribute("data-copy");
        const value = this._identity?.[key];
        if (!value) return;
        try {
          if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(value);
          else this._legacyCopy(value);
          this._flashCopy(e.currentTarget);
          this._notify(`Copied ${key.replace("_"," ")}`);
        } catch {
          // try legacy before failing
          const ok = this._legacyCopy(value);
          this._notify(ok ? `Copied ${key.replace("_"," ")}` : "Copy failed");
        }
      });
    });

    // Identity buttons
    $("#btnRegenerate")?.addEventListener("click", () => this._regenerateIdentity());
    $("#btnRefreshId")?.addEventListener("click", () => this._fetchIdentity());

    // Canister buttons -> open dialogs or run calls
    $("#btnList")?.addEventListener("click", async () => {
      try {
        const data = await this._api("/api/v1/canisters");
        this._showResult("Canisters", data);
      } catch (e) {
        this._notify(`List failed: ${e.message}`);
      }
    });

    $("#btnGet")?.addEventListener("click", () => $("#dlgGet").open = true);
    $("#doGet")?.addEventListener("click", async () => {
      const name = $("#inGetName").value.trim();
      if (!name) return this._notify("Enter canister name");
      try {
        const data = await this._api(`/api/v1/canisters/${encodeURIComponent(name)}`);
        this._showResult("Canister", data);
      } catch (e) {
        this._notify(`Get failed: ${e.message}`);
      }
    });

    $("#btnAdd")?.addEventListener("click", () => $("#dlgAdd").open = true);
    $("#doAdd")?.addEventListener("click", async () => {
      const id = $("#inAddId").value.trim();
      const name = $("#inAddName").value.trim() || undefined;
      if (!id) return this._notify("Canister ID is required");
      try {
        const data = await this._api("/api/v1/canisters/add", {
          method: "POST",
          json: { canister_id: id, canister_name: name }
        });
        this._showResult("Add canister", data);
        $("#dlgAdd").open = false;
      } catch (e) {
        this._notify(`Add failed: ${e.message}`);
      }
    });

    $("#btnCall")?.addEventListener("click", () => $("#dlgCall").open = true);
    $("#doCall")?.addEventListener("click", async () => {
      const name = $("#inCallName").value.trim();
      const method = $("#inCallMethod").value.trim();
      const argsRaw = $("#inCallArgs").value.trim();
      if (!name || !method) return this._notify("Enter name and method");
      let args;
      try {
        args = argsRaw ? JSON.parse(argsRaw) : [];
      } catch {
        return this._notify("Args must be valid JSON");
      }
      try {
        const data = await this._api("/api/v1/canisters/call", {
          method: "POST",
          json: { canister_name: name, method_name: method, args }
        });
        this._showResult("Call result", data);
        $("#dlgCall").open = false;
      } catch (e) {
        this._notify(`Call failed: ${e.message}`);
      }
    });

    $("#btnMethods")?.addEventListener("click", () => $("#dlgMethods").open = true);
    $("#doMethods")?.addEventListener("click", async () => {
      const name = $("#inMethName").value.trim();
      if (!name) return this._notify("Enter canister name");
      try {
        const data = await this._api(`/api/v1/canisters/methods/${encodeURIComponent(name)}`);
        this._showResult("Methods", data);
        $("#dlgMethods").open = false;
      } catch (e) {
        this._notify(`Fetch methods failed: ${e.message}`);
      }
    });

    $("#btnDelete")?.addEventListener("click", () => $("#dlgDelete").open = true);
    $("#doDelete")?.addEventListener("click", async () => {
      const name = $("#inDelName").value.trim();
      if (!name) return this._notify("Enter canister name");
      if (!confirm(`Delete canister "${name}"?`)) return;
      try {
        const data = await this._api(`/api/v1/canisters/delete/${encodeURIComponent(name)}`, { method: "DELETE" });
        this._showResult("Delete", data);
        $("#dlgDelete").open = false;
      } catch (e) {
        this._notify(`Delete failed: ${e.message}`);
      }
    });
  }

  _legacyCopy(text) {
    try {
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.top = "-1000px";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      const ok = document.execCommand("copy");
      document.body.removeChild(ta);
      return ok;
    } catch {
      return false;
    }
  }

  _flashCopy(btn) {
    const icon = btn.querySelector("ha-icon");
    const prev = icon?.getAttribute("icon") || "mdi:content-copy";
    btn.classList.add("copied");
    icon?.setAttribute("icon", "mdi:check");
    setTimeout(() => {
      icon?.setAttribute("icon", prev);
      btn.classList.remove("copied");
    }, 1000);
  }
}

customElements.define("icp-addon-card", IcpAddonCard);
(window.customCards = window.customCards || []).push({
  type: "icp-addon-card",
  name: "ICP Card",
  description: "ICP identity controls and canister tools calling a local API.",
});
