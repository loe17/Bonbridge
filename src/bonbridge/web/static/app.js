/* BonBridge web interface - vanilla JS, no build step, no external assets. */
'use strict';

const I18N = {
  de: {
    'tab.overview': 'Übersicht', 'tab.printers': 'Drucker', 'tab.features': 'Funktionen',
    'tab.diag': 'Diagnose', 'tab.connect': 'Anbindung', 'tab.system': 'System',
    'status.ok': 'Betriebsbereit', 'status.warn': 'Warnung', 'status.error': 'Fehler',
    'status.offline': 'Nicht verbunden', 'status.unknown': 'Unbekannt',
    'ov.title': 'Gerätestatus', 'ov.noPrinters': 'Noch kein Drucker eingerichtet.',
    'ov.address': 'Adresse für das Kassensystem', 'ov.jobs': 'Druckaufträge',
    'ov.queued': 'in Warteschlange', 'ov.spooled': 'zwischengespeichert',
    'ov.connection': 'Verbindung', 'ov.model': 'Erkanntes Modell', 'ov.lastJob': 'Letzter Auftrag',
    'ov.lastError': 'Letzter Fehler', 'ov.listener': 'Netzwerk-Listener', 'ov.never': 'nie',
    'ov.testPrint': 'Testseite drucken', 'ov.refresh': 'Status aktualisieren',
    'pr.title': 'Drucker verwalten', 'pr.add': 'Drucker hinzufügen', 'pr.scan': 'Geräte suchen',
    'pr.name': 'Name', 'pr.enabled': 'Aktiv', 'pr.bind': 'IP-Adresse für Port 9100',
    'pr.bindHint': '0.0.0.0 = alle Adressen des Geräts. Für mehrere Ausdruckgruppen je Drucker eine eigene IP eintragen (siehe Doku).',
    'pr.transport': 'Anschluss', 'pr.profile': 'Druckerprofil', 'pr.auto': 'automatisch',
    'pr.save': 'Speichern', 'pr.delete': 'Löschen', 'pr.redetect': 'Neu erkennen',
    'pr.devices': 'Gefundene Geräte', 'pr.noDevices': 'Keine Geräte gefunden. Drucker eingeschaltet? Eigenes 24-V-Netzteil angeschlossen?',
    'pr.use': 'Übernehmen', 'pr.options': 'Optionen', 'pr.confirmDelete': 'Drucker wirklich löschen?',
    'fe.title': 'Druckerfunktionen', 'fe.detected': 'erkannt', 'fe.override': 'Einstellung',
    'fe.auto': 'automatisch', 'fe.on': 'ein (erzwungen)', 'fe.off': 'aus (erzwungen)',
    'fe.effective': 'wirksam', 'fe.probes': 'Aktive Tests (verbrauchen Papier)',
    'fe.probeCut': 'Schneiden testen', 'fe.probeDrawer': 'Kassenlade öffnen',
    'fe.probeBuzzer': 'Signalton', 'fe.probeFeed': 'Papiervorschub',
    'fe.testFeatures': 'Funktionstestseite', 'fe.recommend': 'Empfohlene Werte für das Kassensystem',
    'di.title': 'Diagnose', 'di.report': 'Support-Bericht herunterladen', 'di.reload': 'Neu laden',
    'di.recentJobs': 'Letzte Druckaufträge', 'di.noJobs': 'Noch keine Aufträge.',
    'di.raw': 'Rohdaten senden (Experten)', 'di.rawSend': 'Senden',
    'di.rawHint': 'Text oder Hex-Bytes, z. B. 1B 40 für ESC @ (Reset).',
    'di.commands': 'Systemausgaben', 'di.clearSpool': 'Zwischenspeicher leeren',
    'co.title': 'Einbindung ins Kassensystem', 'co.oa': 'OrderAssist',
    'co.generic': 'Andere Kassensysteme', 'co.steps': 'Schritte',
    'co.ip': 'IP-Adresse', 'co.port': 'Port', 'co.protocol': 'Protokoll',
    'co.font': 'Schriftart', 'co.charset': 'Zeichensatz', 'co.width': 'Zeilenbreite',
    'co.copied': 'Kopiert', 'co.alt': 'Alternativen',
    'sy.title': 'System', 'sy.restart': 'Dienste neu starten', 'sy.settings': 'Einstellungen',
    'sy.save': 'Speichern', 'sy.docs': 'Dokumentation', 'sy.restartHint': 'Änderungen werden sofort übernommen.',
    'sy.webPort': 'Port der Weboberfläche', 'sy.rawPort': 'RAW-Port (Kassensystem)',
    'sy.rawPortHint': 'OrderAssist verwendet fest 9100 - nur zu Testzwecken ändern.',
    'sy.mdns': 'mDNS/Bonjour-Ankündigung', 'sy.enpc': 'Epson-Suchprotokoll beantworten (experimentell)',
    'sy.label': 'Gerätebezeichnung', 'sy.language': 'Sprache der Oberfläche',
    'common.yes': 'ja', 'common.no': 'nein', 'common.saved': 'Gespeichert',
    'common.error': 'Fehler', 'common.queued': 'An den Drucker geschickt',
    'common.loading': 'Wird geladen …',
    'op.cut': 'Nach jedem Auftrag schneiden', 'op.drawer': 'Nach jedem Auftrag Kassenlade öffnen',
    'op.reset': 'Vor jedem Auftrag zurücksetzen (ESC @)', 'op.polling': 'Statusabfrage aktiv',
    'op.interval': 'Abfrageintervall (s)', 'op.feed': 'Zeilenvorschub nach Auftrag'
  },
  en: {
    'tab.overview': 'Overview', 'tab.printers': 'Printers', 'tab.features': 'Features',
    'tab.diag': 'Diagnostics', 'tab.connect': 'Integration', 'tab.system': 'System',
    'status.ok': 'Ready', 'status.warn': 'Warning', 'status.error': 'Error',
    'status.offline': 'Not connected', 'status.unknown': 'Unknown',
    'ov.title': 'Device status', 'ov.noPrinters': 'No printer configured yet.',
    'ov.address': 'Address for the POS application', 'ov.jobs': 'Print jobs',
    'ov.queued': 'queued', 'ov.spooled': 'spooled',
    'ov.connection': 'Connection', 'ov.model': 'Detected model', 'ov.lastJob': 'Last job',
    'ov.lastError': 'Last error', 'ov.listener': 'Network listener', 'ov.never': 'never',
    'ov.testPrint': 'Print test page', 'ov.refresh': 'Refresh status',
    'pr.title': 'Manage printers', 'pr.add': 'Add printer', 'pr.scan': 'Scan for devices',
    'pr.name': 'Name', 'pr.enabled': 'Enabled', 'pr.bind': 'IP address for port 9100',
    'pr.bindHint': '0.0.0.0 = every address of this device. For several print groups give each printer its own IP (see docs).',
    'pr.transport': 'Connection', 'pr.profile': 'Printer profile', 'pr.auto': 'automatic',
    'pr.save': 'Save', 'pr.delete': 'Delete', 'pr.redetect': 'Re-detect',
    'pr.devices': 'Detected devices', 'pr.noDevices': 'No devices found. Is the printer switched on with its own 24 V supply?',
    'pr.use': 'Use', 'pr.options': 'Options', 'pr.confirmDelete': 'Really delete this printer?',
    'fe.title': 'Printer features', 'fe.detected': 'detected', 'fe.override': 'setting',
    'fe.auto': 'automatic', 'fe.on': 'on (forced)', 'fe.off': 'off (forced)',
    'fe.effective': 'effective', 'fe.probes': 'Active tests (these use paper)',
    'fe.probeCut': 'Test cutter', 'fe.probeDrawer': 'Open cash drawer',
    'fe.probeBuzzer': 'Buzzer', 'fe.probeFeed': 'Feed paper',
    'fe.testFeatures': 'Feature test page', 'fe.recommend': 'Recommended POS settings',
    'di.title': 'Diagnostics', 'di.report': 'Download support report', 'di.reload': 'Reload',
    'di.recentJobs': 'Recent print jobs', 'di.noJobs': 'No jobs yet.',
    'di.raw': 'Send raw data (expert)', 'di.rawSend': 'Send',
    'di.rawHint': 'Text or hex bytes, e.g. 1B 40 for ESC @ (reset).',
    'di.commands': 'System output', 'di.clearSpool': 'Clear spool',
    'co.title': 'POS integration', 'co.oa': 'OrderAssist',
    'co.generic': 'Other POS systems', 'co.steps': 'Steps',
    'co.ip': 'IP address', 'co.port': 'Port', 'co.protocol': 'Protocol',
    'co.font': 'Font', 'co.charset': 'Character set', 'co.width': 'Line width',
    'co.copied': 'Copied', 'co.alt': 'Alternatives',
    'sy.title': 'System', 'sy.restart': 'Restart services', 'sy.settings': 'Settings',
    'sy.save': 'Save', 'sy.docs': 'Documentation', 'sy.restartHint': 'Changes are applied immediately.',
    'sy.webPort': 'Web interface port', 'sy.rawPort': 'RAW port (POS)',
    'sy.rawPortHint': 'OrderAssist always uses 9100 - change for testing only.',
    'sy.mdns': 'mDNS/Bonjour announcement', 'sy.enpc': 'Answer Epson discovery probes (experimental)',
    'sy.label': 'Device label', 'sy.language': 'Interface language',
    'common.yes': 'yes', 'common.no': 'no', 'common.saved': 'Saved',
    'common.error': 'Error', 'common.queued': 'Sent to the printer',
    'common.loading': 'Loading …',
    'op.cut': 'Cut after every job', 'op.drawer': 'Open cash drawer after every job',
    'op.reset': 'Reset (ESC @) before every job', 'op.polling': 'Status polling enabled',
    'op.interval': 'Polling interval (s)', 'op.feed': 'Feed lines after job'
  }
};

let LANG = localStorage.getItem('bb.lang') || 'de';
let STATE = { overview: null, devices: [], profiles: [], selected: null };
let TIMER = null;

const t = (key) => (I18N[LANG] && I18N[LANG][key]) || (I18N.de[key] || key);
const $ = (sel, root) => (root || document).querySelector(sel);
const esc = (value) => String(value == null ? '' : value)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

function toast(message, isError) {
  const box = $('#toast');
  box.textContent = message;
  box.className = isError ? 'err' : '';
  box.style.display = 'block';
  clearTimeout(box._timer);
  box._timer = setTimeout(() => { box.style.display = 'none'; }, 3500);
}

async function api(path, options) {
  const response = await fetch(path, Object.assign({ headers: { 'Content-Type': 'application/json' } }, options || {}));
  const type = response.headers.get('content-type') || '';
  if (type.indexOf('application/json') === -1) {
    const text = await response.text();
    if (!response.ok) throw new Error(text.slice(0, 200));
    return text;
  }
  const data = await response.json();
  if (!response.ok || data.ok === false) throw new Error(data.error || ('HTTP ' + response.status));
  return data;
}

function fmtTime(seconds) {
  if (!seconds) return t('ov.never');
  const date = new Date(seconds * 1000);
  return date.toLocaleString();
}

function fmtDuration(seconds) {
  if (seconds == null) return '-';
  seconds = Math.floor(seconds);
  const d = Math.floor(seconds / 86400), h = Math.floor(seconds % 86400 / 3600), m = Math.floor(seconds % 3600 / 60);
  if (d) return d + 'd ' + h + 'h';
  if (h) return h + 'h ' + m + 'm';
  return m + 'm ' + (seconds % 60) + 's';
}

function fmtBytes(value) {
  if (!value) return '0 B';
  const units = ['B', 'kB', 'MB', 'GB'];
  let index = 0, size = value;
  while (size >= 1024 && index < units.length - 1) { size /= 1024; index++; }
  return size.toFixed(index ? 1 : 0) + ' ' + units[index];
}

function statusDot(level) {
  return '<span class="dot ' + esc(level || 'unknown') + '"></span>' + t('status.' + (level || 'unknown'));
}

function copyText(value) {
  navigator.clipboard && navigator.clipboard.writeText(value).then(
    () => toast(t('co.copied') + ': ' + value),
    () => toast(value)
  );
}
window.copyText = copyText;

/* ------------------------------------------------------------------ */
/* Overview                                                            */
/* ------------------------------------------------------------------ */

function renderOverview() {
  const data = STATE.overview;
  const root = $('#overview');
  if (!data) { root.innerHTML = '<div class="card">' + t('common.loading') + '</div>'; return; }
  const sys = data.system;
  $('#hdrHost').textContent = sys.hostname + '  ·  ' + sys.primary_ip + '  ·  v' + data.version;

  let html = '<div class="card"><h2>' + t('ov.title') + '</h2>' +
    '<div class="big">' + statusDot(data.overall_status) + '</div>' +
    '<div class="kv" style="margin-top:.6rem">' +
    kv(sys.model, sys.os) + kv('IP', sys.primary_ip) +
    kv('Uptime', fmtDuration(sys.uptime)) +
    (sys.cpu_temperature ? kv('CPU', sys.cpu_temperature.toFixed(1) + ' °C') : '') +
    '</div></div>';

  if (!data.printers.length) {
    html += '<div class="card">' + t('ov.noPrinters') + '</div>';
  }

  data.printers.forEach((printer) => {
    const listener = printer.listener || {};
    const caps = printer.capabilities || {};
    html += '<div class="card"><h2>' + esc(printer.name) + ' <span class="tag">' + esc(printer.id) + '</span></h2>' +
      '<div class="big">' + statusDot(printer.status_level) + '</div>' +
      '<div class="muted" style="margin:.2rem 0 .8rem">' + esc((printer.status_messages || []).join(' · ')) + '</div>' +
      '<div class="row"><div class="kv">' +
      kv(t('ov.address'), '<code class="copy" onclick="copyText(\'' + esc(printer.pos_address) + '\')">' +
         esc(printer.pos_address) + ':' + esc(printer.pos_port) + '</code>') +
      kv(t('ov.connection'), esc(printer.connection || '-')) +
      kv(t('ov.model'), esc(caps.profile_name || '-')) +
      '</div><div class="kv">' +
      kv(t('ov.jobs'), printer.jobs_total + ' / ' + fmtBytes(printer.bytes_total) +
         ' · ' + printer.queued + ' ' + t('ov.queued') + ' · ' + printer.spooled + ' ' + t('ov.spooled')) +
      kv(t('ov.lastJob'), fmtTime(printer.last_job_at)) +
      kv(t('ov.listener'), (listener.listening ? '' : '<span class="dot error"></span>') +
         esc(listener.bind + ':' + listener.port) + (listener.error ? ' — ' + esc(listener.error) : '')) +
      (printer.last_error ? kv(t('ov.lastError'), '<span style="color:var(--err)">' + esc(printer.last_error) + '</span>') : '') +
      '</div></div>' +
      '<div class="btnbar">' +
      '<button class="act primary" onclick="testPrint(\'' + esc(printer.id) + '\',\'standard\')">' + t('ov.testPrint') + '</button>' +
      '<button class="act" onclick="refreshPrinter(\'' + esc(printer.id) + '\')">' + t('ov.refresh') + '</button>' +
      '</div></div>';
  });

  root.innerHTML = html;
}

function kv(key, value) {
  return '<div><span>' + key + '</span><span>' + value + '</span></div>';
}

async function testPrint(printerId, kind) {
  try { await api('/api/printers/' + encodeURIComponent(printerId) + '/test', { method: 'POST', body: JSON.stringify({ kind: kind }) });
    toast(t('common.queued')); } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
async function refreshPrinter(printerId) {
  try { await api('/api/printers/' + encodeURIComponent(printerId) + '/refresh', { method: 'POST' }); await reload(); toast('OK'); }
  catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
window.testPrint = testPrint;
window.refreshPrinter = refreshPrinter;

/* ------------------------------------------------------------------ */
/* Printers                                                            */
/* ------------------------------------------------------------------ */

async function renderPrinters() {
  const root = $('#printers');
  const data = STATE.overview;
  if (!data) { root.innerHTML = '<div class="card">' + t('common.loading') + '</div>'; return; }
  if (!STATE.profiles.length) {
    try { STATE.profiles = (await api('/api/profiles')).profiles; } catch (e) { /* ignore */ }
  }

  let html = '<div class="card"><h2>' + t('pr.title') + '</h2><div class="btnbar">' +
    '<button class="act" onclick="scanDevices()">' + t('pr.scan') + '</button>' +
    '<button class="act" onclick="addPrinter()">' + t('pr.add') + '</button></div>';
  if (STATE.devices.length) {
    html += '<h3>' + t('pr.devices') + '</h3><table>';
    STATE.devices.forEach((device, index) => {
      html += '<tr><td>' + esc(device.transport) + '</td><td>' + esc(device.label || '') + '</td>' +
        '<td style="width:6rem"><button class="act" onclick="useDevice(' + index + ')">' + t('pr.use') + '</button></td></tr>';
    });
    html += '</table>';
  } else if (STATE.scanned) {
    html += '<p class="muted">' + t('pr.noDevices') + '</p>';
  }
  html += '</div>';

  data.printers.forEach((printer) => {
    const config = printer;
    const transport = (printer.transport && printer.transport.settings) || {};
    const transportType = (printer.transport && printer.transport.type) || 'auto';
    html += '<div class="card" data-printer="' + esc(printer.id) + '"><h2>' + esc(printer.name) + '</h2>' +
      '<div class="grid2">' +
      '<div><label>' + t('pr.name') + '</label><input data-f="name" value="' + esc(printer.name) + '">' +
      '<label>' + t('pr.bind') + '</label><input data-f="bind" value="' + esc(printer.bind) + '">' +
      '<div class="muted" style="font-size:.78rem;margin-top:.25rem">' + t('pr.bindHint') + '</div></div>' +
      '<div><label>' + t('pr.transport') + '</label>' +
      '<select data-f="transport.type">' + ['auto', 'usb', 'usblp', 'serial', 'network'].map((k) =>
        '<option value="' + k + '"' + (k === transportType ? ' selected' : '') + '>' + k + '</option>').join('') + '</select>' +
      '<label>' + t('pr.profile') + '</label><select data-f="profile">' +
      '<option value="auto">' + t('pr.auto') + '</option>' +
      STATE.profiles.map((p) => '<option value="' + esc(p.id) + '">' + esc(p.name) +
        (p.columns ? ' (' + p.columns + ')' : '') + '</option>').join('') + '</select>' +
      '<label style="display:flex;align-items:center;gap:.5rem;margin-top:.7rem">' +
      '<input type="checkbox" data-f="enabled" style="width:auto"' + (printer.enabled ? ' checked' : '') + '> ' + t('pr.enabled') + '</label>' +
      '</div></div>' +
      '<h3>' + t('pr.transport') + ' — ' + esc(transportType) + '</h3>' +
      transportFields(transportType, transport) +
      '<h3>' + t('pr.options') + '</h3>' + optionFields(printer) +
      '<div class="btnbar">' +
      '<button class="act primary" onclick="savePrinter(\'' + esc(printer.id) + '\')">' + t('pr.save') + '</button>' +
      '<button class="act" onclick="redetect(\'' + esc(printer.id) + '\')">' + t('pr.redetect') + '</button>' +
      '<button class="act danger" onclick="deletePrinter(\'' + esc(printer.id) + '\')">' + t('pr.delete') + '</button>' +
      '</div></div>';
  });

  root.innerHTML = html;
  // Restore select values that need JS (profile is dynamic).
  data.printers.forEach((printer) => {
    const card = root.querySelector('[data-printer="' + printer.id + '"]');
    if (!card) return;
    const select = card.querySelector('[data-f="profile"]');
    const wanted = (printer.capabilities && printer.capabilities.profile_id) || 'auto';
    select.value = STATE.configProfiles && STATE.configProfiles[printer.id] ? STATE.configProfiles[printer.id] : 'auto';
    if (select.selectedIndex < 0) select.value = 'auto';
    select.setAttribute('data-detected', wanted);
  });
}

function transportFields(type, settings) {
  const field = (key, label, value, placeholder) =>
    '<div><label>' + label + '</label><input data-f="transport.' + key + '" value="' + esc(value == null ? '' : value) +
    '" placeholder="' + esc(placeholder || '') + '"></div>';
  if (type === 'usb') {
    return '<div class="grid2">' +
      field('vendor_id', 'Vendor ID', settings.vendor_id, '0x04b8') +
      field('product_id', 'Product ID', settings.product_id, '0x0202') +
      field('serial', 'Serial', settings.serial, '') + '</div>';
  }
  if (type === 'usblp') {
    return '<div class="grid2">' + field('device', 'Device', settings.device, '/dev/usb/lp0') + '</div>';
  }
  if (type === 'serial') {
    return '<div class="grid2">' + field('device', 'Device', settings.device, '/dev/ttyUSB0') +
      field('baudrate', 'Baud', settings.baudrate, '38400') + '</div>';
  }
  if (type === 'network') {
    return '<div class="grid2">' + field('host', 'Host', settings.host, '192.168.1.20') +
      field('port', 'Port', settings.port, '9100') + '</div>';
  }
  return '<p class="muted">auto</p>';
}

function optionFields(printer) {
  const options = (STATE.configOptions && STATE.configOptions[printer.id]) || {};
  const check = (key, label) => '<label style="display:flex;align-items:center;gap:.5rem">' +
    '<input type="checkbox" style="width:auto" data-f="options.' + key + '"' + (options[key] ? ' checked' : '') + '> ' + label + '</label>';
  return '<div class="grid2">' +
    '<div>' + check('cut_after_job', t('op.cut')) + check('open_drawer_after_job', t('op.drawer')) +
    check('reset_before_job', t('op.reset')) + '</div>' +
    '<div>' + check('status_polling', t('op.polling')) +
    '<label>' + t('op.interval') + '</label><input data-f="options.status_interval" value="' +
    esc(options.status_interval == null ? 10 : options.status_interval) + '">' +
    '<label>' + t('op.feed') + '</label><input data-f="options.feed_lines_after_job" value="' +
    esc(options.feed_lines_after_job == null ? 0 : options.feed_lines_after_job) + '"></div></div>';
}

function collectPatch(card) {
  const patch = {};
  card.querySelectorAll('[data-f]').forEach((input) => {
    const path = input.getAttribute('data-f').split('.');
    let value = input.type === 'checkbox' ? input.checked : input.value;
    if (value === '' && input.type !== 'checkbox') value = null;
    if (typeof value === 'string' && /^-?\d+(\.\d+)?$/.test(value) && path[0] === 'options') value = Number(value);
    let node = patch;
    path.slice(0, -1).forEach((key) => { node[key] = node[key] || {}; node = node[key]; });
    node[path[path.length - 1]] = value;
  });
  return patch;
}

async function savePrinter(printerId) {
  const card = document.querySelector('[data-printer="' + printerId + '"]');
  try {
    await api('/api/printers/' + encodeURIComponent(printerId), { method: 'PATCH', body: JSON.stringify(collectPatch(card)) });
    toast(t('common.saved'));
    await reload(true);
  } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
async function deletePrinter(printerId) {
  if (!confirm(t('pr.confirmDelete'))) return;
  try { await api('/api/printers/' + encodeURIComponent(printerId), { method: 'DELETE' }); await reload(true); toast('OK'); }
  catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
async function addPrinter() {
  const count = (STATE.overview.printers || []).length + 1;
  try {
    await api('/api/printers', { method: 'POST', body: JSON.stringify({
      id: 'printer' + count, name: 'Drucker ' + count, transport: { type: 'auto' } }) });
    await reload(true); toast('OK');
  } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
async function scanDevices() {
  try { STATE.devices = (await api('/api/scan')).devices; STATE.scanned = true; renderPrinters(); }
  catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
async function useDevice(index) {
  const device = STATE.devices[index];
  const printers = STATE.overview.printers || [];
  if (!printers.length) { await addPrinter(); }
  const target = (STATE.selected || (STATE.overview.printers[0] || {}).id);
  const transport = { type: device.transport };
  if (device.vendor_id != null) { transport.vendor_id = '0x' + device.vendor_id_hex; transport.product_id = '0x' + device.product_id_hex; }
  if (device.device) transport.device = device.device;
  if (device.baudrate) transport.baudrate = device.baudrate;
  try {
    await api('/api/printers/' + encodeURIComponent(target), { method: 'PATCH', body: JSON.stringify({ transport: transport }) });
    await reload(true); toast(t('common.saved'));
  } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
async function redetect(printerId) {
  try { await api('/api/printers/' + encodeURIComponent(printerId) + '/redetect', { method: 'POST' }); await reload(true); toast('OK'); }
  catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
window.savePrinter = savePrinter; window.deletePrinter = deletePrinter; window.addPrinter = addPrinter;
window.scanDevices = scanDevices; window.useDevice = useDevice; window.redetect = redetect;

/* ------------------------------------------------------------------ */
/* Features                                                            */
/* ------------------------------------------------------------------ */

function renderFeatures() {
  const root = $('#features');
  const data = STATE.overview;
  if (!data) { root.innerHTML = '<div class="card">' + t('common.loading') + '</div>'; return; }
  let html = '';
  data.printers.forEach((printer) => {
    const caps = printer.capabilities || {};
    const features = caps.features || {};
    const rec = caps.recommendation || {};
    html += '<div class="card" data-features="' + esc(printer.id) + '"><h2>' + esc(printer.name) +
      ' <span class="tag">' + esc(caps.profile_name || '') + '</span></h2>';
    html += '<p class="muted" style="margin-top:0">' + esc((printer.identity || {}).profile_reason || '') + '</p>';
    Object.keys(features).forEach((key) => {
      const entry = features[key];
      const label = LANG === 'de' ? entry.label_de : entry.label_en;
      html += '<div class="switch"><span class="name">' + esc(label) +
        ' <span class="tag">' + t('fe.detected') + ': ' + (entry.detected ? t('common.yes') : t('common.no')) + '</span>' +
        '<span class="tag">' + t('fe.effective') + ': ' + (entry.effective ? t('common.yes') : t('common.no')) + '</span></span>' +
        '<select data-feature="' + esc(key) + '">' +
        '<option value="auto"' + (entry.override == null ? ' selected' : '') + '>' + t('fe.auto') + '</option>' +
        '<option value="on"' + (entry.override === true ? ' selected' : '') + '>' + t('fe.on') + '</option>' +
        '<option value="off"' + (entry.override === false ? ' selected' : '') + '>' + t('fe.off') + '</option>' +
        '</select></div>';
    });
    html += '<h3>' + t('fe.recommend') + '</h3><div class="kv">' +
      kv(t('co.font'), esc(rec.font || '-') + ' (' + esc(rec.font_name || '') + ')') +
      kv(t('co.width'), esc(rec.columns || '-')) +
      kv(t('co.charset'), esc(rec.codepage || '-')) + '</div>' +
      '<p class="muted" style="font-size:.8rem">' + esc(LANG === 'de' ? (rec.note_de || '') : (rec.note_en || '')) + '</p>';
    html += '<div class="btnbar">' +
      '<button class="act primary" onclick="saveFeatures(\'' + esc(printer.id) + '\')">' + t('pr.save') + '</button>' +
      '<button class="act" onclick="testPrint(\'' + esc(printer.id) + '\',\'features\')">' + t('fe.testFeatures') + '</button>' +
      '</div>';
    html += '<h3>' + t('fe.probes') + '</h3><div class="btnbar">' +
      probeButton(printer.id, 'cut', t('fe.probeCut')) +
      probeButton(printer.id, 'drawer', t('fe.probeDrawer')) +
      probeButton(printer.id, 'buzzer', t('fe.probeBuzzer')) +
      probeButton(printer.id, 'feed', t('fe.probeFeed')) +
      '</div></div>';
  });
  root.innerHTML = html || '<div class="card">' + t('ov.noPrinters') + '</div>';
}

function probeButton(printerId, what, label) {
  return '<button class="act" onclick="probe(\'' + esc(printerId) + '\',\'' + what + '\')">' + label + '</button>';
}

async function probe(printerId, what) {
  try { await api('/api/printers/' + encodeURIComponent(printerId) + '/probe', { method: 'POST', body: JSON.stringify({ what: what }) });
    toast(t('common.queued')); } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
async function saveFeatures(printerId) {
  const card = document.querySelector('[data-features="' + printerId + '"]');
  const features = {};
  card.querySelectorAll('[data-feature]').forEach((select) => {
    const value = select.value;
    features[select.getAttribute('data-feature')] = value === 'auto' ? null : (value === 'on');
  });
  try {
    await api('/api/printers/' + encodeURIComponent(printerId), { method: 'PATCH', body: JSON.stringify({ features: features }) });
    toast(t('common.saved')); await reload(true);
  } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
window.probe = probe; window.saveFeatures = saveFeatures;

/* ------------------------------------------------------------------ */
/* Diagnostics                                                         */
/* ------------------------------------------------------------------ */

async function renderDiag() {
  const root = $('#diag');
  root.innerHTML = '<div class="card">' + t('common.loading') + '</div>';
  let diag;
  try { diag = await api('/api/diagnostics'); }
  catch (e) { root.innerHTML = '<div class="card">' + t('common.error') + ': ' + esc(e.message) + '</div>'; return; }

  let html = '<div class="card"><h2>' + t('di.title') + '</h2><div class="btnbar">' +
    '<button class="act primary" onclick="downloadReport()">' + t('di.report') + '</button>' +
    '<button class="act" onclick="renderDiag()">' + t('di.reload') + '</button></div></div>';

  (STATE.overview ? STATE.overview.printers : []).forEach((printer) => {
    html += '<div class="card"><h2>' + esc(printer.name) + '</h2>' +
      '<h3>' + t('di.recentJobs') + '</h3>';
    if (!(printer.recent_jobs || []).length) {
      html += '<p class="muted">' + t('di.noJobs') + '</p>';
    } else {
      html += '<table><tr><th>#</th><th>' + t('ov.connection') + '</th><th>Bytes</th><th></th></tr>';
      printer.recent_jobs.forEach((job) => {
        html += '<tr><td>' + job.number + '</td><td>' + esc(job.source) + '<br><span class="muted">' +
          fmtTime(job.printed_at) + '</span></td><td>' + fmtBytes(job.size) + '</td><td><code>' +
          esc(job.preview || '') + '</code></td></tr>';
      });
      html += '</table>';
    }
    html += '<h3>' + t('di.raw') + '</h3><div class="muted" style="font-size:.8rem">' + t('di.rawHint') + '</div>' +
      '<div class="row" style="margin-top:.4rem"><input id="raw-' + esc(printer.id) + '" placeholder="1B 40 48 61 6C 6C 6F 0A 0A 0A">' +
      '<button class="act" style="flex:0 0 auto" onclick="sendRaw(\'' + esc(printer.id) + '\')">' + t('di.rawSend') + '</button></div>' +
      '<div class="btnbar"><button class="act" onclick="clearSpool(\'' + esc(printer.id) + '\')">' + t('di.clearSpool') +
      ' (' + printer.spooled + ')</button></div>' +
      '<h3>Status</h3><pre>' + esc(JSON.stringify(printer.status || {}, null, 1)) + '</pre>' +
      '<h3>Identity</h3><pre>' + esc(JSON.stringify(printer.identity || {}, null, 1)) + '</pre>' +
      '</div>';
  });

  html += '<div class="card"><h2>' + t('di.commands') + '</h2>';
  Object.keys(diag.commands).forEach((key) => {
    html += '<h3>' + esc(key) + '</h3><pre>' + esc(diag.commands[key]) + '</pre>';
  });
  html += '</div>';
  root.innerHTML = html;
}

function downloadReport() { window.location = '/api/report'; }
async function sendRaw(printerId) {
  const input = document.getElementById('raw-' + printerId);
  const value = input.value.trim();
  if (!value) return;
  const isHex = /^[0-9a-fA-F\s]+$/.test(value) && value.replace(/\s/g, '').length % 2 === 0;
  const body = isHex ? { hex: value } : { text: value + '\n\n\n' };
  try { await api('/api/printers/' + encodeURIComponent(printerId) + '/raw', { method: 'POST', body: JSON.stringify(body) });
    toast(t('common.queued')); } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
async function clearSpool(printerId) {
  try { const r = await api('/api/printers/' + encodeURIComponent(printerId) + '/spool/clear', { method: 'POST' });
    toast('OK (' + r.removed + ')'); await reload(true); } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
window.downloadReport = downloadReport; window.sendRaw = sendRaw; window.clearSpool = clearSpool; window.renderDiag = renderDiag;

/* ------------------------------------------------------------------ */
/* Integration                                                         */
/* ------------------------------------------------------------------ */

function renderConnect() {
  const root = $('#connect');
  const data = STATE.overview;
  if (!data) { root.innerHTML = '<div class="card">' + t('common.loading') + '</div>'; return; }
  let html = '';
  data.printers.forEach((printer) => {
    const caps = printer.capabilities || {};
    const rec = caps.recommendation || {};
    const address = printer.pos_address + '';
    const alternatives = (rec.alternatives || []).map((a) => a.font + '=' + a.columns).join(', ');
    const stepsDe = [
      'In OrderAssist das Hauptmenü (☰) öffnen und <b>Drucker</b> wählen.',
      '<b>+ Hinzufügen</b> antippen. Die automatische Suche findet nur EPSON-Netzwerkdrucker – BonBridge daher manuell eintragen.',
      'Als IP-Adresse <code class="copy" onclick="copyText(\'' + esc(address) + '\')">' + esc(address) + '</code> eintragen. Der Port ist fest 9100 und muss nicht angegeben werden.',
      'Unter <b>Drucker korrekt konfigurieren</b> die Werte aus der Tabelle unten eintragen.',
      'Testseite drucken. Prüfen: Zeilenbreite passt, Umlaute und € korrekt, Trennlinie bricht nicht um.',
      'Den Drucker in OrderAssist einer <b>Ausdruckgruppe</b> zuweisen (Küche, Theke …).'
    ];
    const stepsEn = [
      'Open the main menu (☰) in OrderAssist and choose <b>Drucker</b> (printers).',
      'Tap <b>+ Hinzufügen</b>. The automatic search only finds EPSON network printers, so add BonBridge manually.',
      'Enter <code class="copy" onclick="copyText(\'' + esc(address) + '\')">' + esc(address) + '</code> as the IP address. The port is fixed at 9100.',
      'Enter the values from the table below in the printer configuration section.',
      'Print a test page and check line width, umlauts/€ and that the divider does not wrap.',
      'Assign the printer to a print group (kitchen, bar …).'
    ];
    const steps = LANG === 'de' ? stepsDe : stepsEn;

    html += '<div class="card"><h2>' + t('co.oa') + ' — ' + esc(printer.name) + '</h2>' +
      '<div class="kv">' +
      kv(t('co.ip'), '<code class="copy" onclick="copyText(\'' + esc(address) + '\')">' + esc(address) + '</code>') +
      kv(t('co.port'), '<code>' + esc(printer.pos_port) + '</code>') +
      kv(t('co.protocol'), 'RAW / ESC-POS (JetDirect)') +
      kv(t('co.font'), '<code>' + esc(rec.font || '-') + '</code> — ' + esc(rec.font_name || '')) +
      kv(t('co.charset'), '<code>' + esc(rec.codepage || '-') + '</code>') +
      kv(t('co.width'), '<code>' + esc(rec.columns || '-') + '</code>') +
      (alternatives ? kv(t('co.alt'), esc(alternatives)) : '') +
      '</div><p class="muted" style="font-size:.8rem">' +
      esc(LANG === 'de' ? (rec.note_de || '') : (rec.note_en || '')) + '</p>' +
      '<h3>' + t('co.steps') + '</h3><ol>' + steps.map((s) => '<li>' + s + '</li>').join('') + '</ol>' +
      '<div class="btnbar"><button class="act primary" onclick="testPrint(\'' + esc(printer.id) + '\',\'standard\')">' +
      t('ov.testPrint') + '</button></div></div>';
  });

  const first = data.printers[0] || {};
  html += '<div class="card"><h2>' + t('co.generic') + '</h2>' +
    '<p>' + (LANG === 'de'
      ? 'BonBridge verhält sich wie ein gewöhnlicher Netzwerk-Bondrucker (RAW/JetDirect). Jedes Kassensystem, das einen Netzwerkdrucker per IP ansprechen kann, funktioniert:'
      : 'BonBridge behaves like an ordinary network receipt printer (RAW/JetDirect). Any POS system that can address a network printer by IP will work:') + '</p>' +
    '<table>' +
    '<tr><th>' + (LANG === 'de' ? 'Kassensystem / App' : 'POS system / app') + '</th><th>' +
    (LANG === 'de' ? 'Einstellung' : 'Setting') + '</th></tr>' +
    '<tr><td>OrderAssist</td><td>IP eintragen, Port fest 9100</td></tr>' +
    '<tr><td>' + (LANG === 'de' ? 'Allgemein RAW/Socket' : 'Generic RAW/socket') + '</td><td><code>socket://' + esc(first.pos_address || '') + ':' + esc(first.pos_port || 9100) + '</code></td></tr>' +
    '<tr><td>CUPS / Linux</td><td><code>lpadmin -p Bon -E -v socket://' + esc(first.pos_address || '') + ':' + esc(first.pos_port || 9100) + ' -m raw</code></td></tr>' +
    '<tr><td>Windows</td><td>' + (LANG === 'de' ? 'Drucker hinzufügen → TCP/IP-Port → RAW → Port 9100' : 'Add printer → TCP/IP port → RAW → port 9100') + '</td></tr>' +
    '<tr><td>' + (LANG === 'de' ? 'Test von der Kommandozeile' : 'Command line test') + '</td><td><code>printf "Test\\n\\n\\n" | nc ' + esc(first.pos_address || '') + ' ' + esc(first.pos_port || 9100) + '</code></td></tr>' +
    '</table></div>';

  root.innerHTML = html || '<div class="card">' + t('ov.noPrinters') + '</div>';
}

/* ------------------------------------------------------------------ */
/* System                                                              */
/* ------------------------------------------------------------------ */

async function renderSystem() {
  const root = $('#system');
  let config, docs;
  try { config = (await api('/api/config')).config; docs = (await api('/api/docs')).documents; }
  catch (e) { root.innerHTML = '<div class="card">' + t('common.error') + ': ' + esc(e.message) + '</div>'; return; }
  STATE.config = config;
  const sys = STATE.overview ? STATE.overview.system : {};

  let html = '<div class="card"><h2>' + t('sy.settings') + '</h2><div class="grid2">' +
    '<div><label>' + t('sy.label') + '</label><input id="cfgLabel" value="' + esc(config.hostname_label || '') + '">' +
    '<label>' + t('sy.webPort') + '</label><input id="cfgWebPort" value="' + esc(config.web.port) + '">' +
    '<label>' + t('sy.language') + '</label><select id="cfgLang"><option value="de">Deutsch</option><option value="en">English</option></select></div>' +
    '<div><label>' + t('sy.rawPort') + '</label><input id="cfgRawPort" value="' + esc(config.raw.port) + '">' +
    '<div class="muted" style="font-size:.78rem">' + t('sy.rawPortHint') + '</div>' +
    '<label style="display:flex;align-items:center;gap:.5rem;margin-top:.8rem"><input type="checkbox" style="width:auto" id="cfgMdns"' +
    (config.discovery.mdns ? ' checked' : '') + '> ' + t('sy.mdns') + '</label>' +
    '<label style="display:flex;align-items:center;gap:.5rem"><input type="checkbox" style="width:auto" id="cfgEnpc"' +
    (config.discovery.enpc ? ' checked' : '') + '> ' + t('sy.enpc') + '</label></div></div>' +
    '<div class="btnbar"><button class="act primary" onclick="saveConfig()">' + t('sy.save') + '</button>' +
    '<button class="act" onclick="restartServices()">' + t('sy.restart') + '</button></div>' +
    '<div class="muted" style="font-size:.8rem;margin-top:.4rem">' + t('sy.restartHint') + '</div></div>';

  html += '<div class="card"><h2>System</h2><div class="kv">' +
    kv('BonBridge', esc(STATE.overview ? STATE.overview.version : '')) +
    kv('Host', esc(sys.hostname || '')) + kv('Model', esc(sys.model || '')) +
    kv('OS', esc(sys.os || '')) + kv('Kernel', esc(sys.kernel || '')) +
    kv('Arch', esc(sys.architecture || '')) + kv('Python', esc(sys.python || '')) +
    kv('Uptime', fmtDuration(sys.uptime)) +
    kv('Disk free', sys.disk ? fmtBytes(sys.disk.free) : '-') +
    '</div></div>';

  html += '<div class="card"><h2>' + t('sy.docs') + '</h2><ul>';
  (docs || []).filter((d) => d.language === LANG).forEach((d) => {
    html += '<li><a href="/api/docs/' + d.language + '/' + encodeURIComponent(d.file) + '" target="_blank">' + esc(d.title) + '</a></li>';
  });
  html += '</ul></div>';
  root.innerHTML = html;
  document.getElementById('cfgLang').value = config.web.language || 'de';
}

async function saveConfig() {
  const patch = {
    hostname_label: document.getElementById('cfgLabel').value,
    web: { port: Number(document.getElementById('cfgWebPort').value), language: document.getElementById('cfgLang').value },
    raw: { port: Number(document.getElementById('cfgRawPort').value) },
    discovery: { mdns: document.getElementById('cfgMdns').checked, enpc: document.getElementById('cfgEnpc').checked }
  };
  try { await api('/api/config', { method: 'PUT', body: JSON.stringify(patch) }); toast(t('common.saved')); }
  catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
async function restartServices() {
  try { await api('/api/restart', { method: 'POST' }); toast('OK'); await reload(true); }
  catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
window.saveConfig = saveConfig; window.restartServices = restartServices;

/* ------------------------------------------------------------------ */
/* Shell                                                               */
/* ------------------------------------------------------------------ */

let CURRENT = 'overview';

function renderCurrent() {
  if (CURRENT === 'overview') renderOverview();
  else if (CURRENT === 'printers') renderPrinters();
  else if (CURRENT === 'features') renderFeatures();
  else if (CURRENT === 'diag') renderDiag();
  else if (CURRENT === 'connect') renderConnect();
  else if (CURRENT === 'system') renderSystem();
}

async function reload(force) {
  try {
    STATE.overview = await api('/api/overview');
    const config = (await api('/api/config')).config;
    STATE.configOptions = {}; STATE.configProfiles = {};
    (config.printers || []).forEach((p) => { STATE.configOptions[p.id] = p.options || {}; STATE.configProfiles[p.id] = p.profile || 'auto'; });
    if (force || CURRENT === 'overview' || CURRENT === 'features' || CURRENT === 'connect') renderCurrent();
  } catch (e) {
    toast(t('common.error') + ': ' + e.message, true);
  }
}

function applyLanguage() {
  document.documentElement.lang = LANG;
  document.querySelectorAll('[data-i18n]').forEach((node) => { node.textContent = t(node.getAttribute('data-i18n')); });
  document.getElementById('lang').value = LANG;
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('nav button').forEach((button) => {
    button.addEventListener('click', () => {
      document.querySelectorAll('nav button').forEach((b) => b.classList.remove('active'));
      document.querySelectorAll('main section').forEach((s) => s.classList.remove('active'));
      button.classList.add('active');
      CURRENT = button.getAttribute('data-tab');
      document.getElementById(CURRENT).classList.add('active');
      renderCurrent();
    });
  });
  document.getElementById('lang').addEventListener('change', (event) => {
    LANG = event.target.value; localStorage.setItem('bb.lang', LANG); applyLanguage(); renderCurrent();
  });
  applyLanguage();
  reload(true);
  TIMER = setInterval(() => {
    if (CURRENT === 'overview' || CURRENT === 'features') reload(false);
  }, 5000);
});
