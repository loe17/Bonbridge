/* BonBridge web interface - vanilla JS, no build step, no external assets.
 *
 * Everything the user can see is translated here; the backend only ever sends
 * keys (status) or already-bilingual objects (health checks, drawer state), so
 * the interface never shows a mix of languages.
 */
'use strict';

const I18N = {
  de: {
    'tab.overview': 'Übersicht', 'tab.printers': 'Drucker', 'tab.features': 'Funktionen',
    'tab.print': 'Drucken', 'tab.diag': 'Diagnose', 'tab.connect': 'Anbindung',
    'tab.system': 'System', 'tab.docs': 'Doku',

    'status.ok': 'Betriebsbereit', 'status.warn': 'Warnung', 'status.error': 'Fehler',
    'status.offline': 'Nicht verbunden', 'status.unknown': 'Unbekannt', 'status.info': 'Hinweis',

    'msg.ok': 'Betriebsbereit',
    'msg.no_status': 'Kein Status lesbar',
    'msg.unrecoverable_error': 'Nicht behebbarer Druckerfehler',
    'msg.autocutter_error': 'Fehler am Papierschneider',
    'msg.recoverable_error': 'Behebbarer Druckerfehler',
    'msg.cover_open': 'Deckel offen',
    'msg.paper_end': 'Papier leer',
    'msg.paper_near_end': 'Papier fast leer',
    'msg.printer_offline': 'Drucker meldet offline',
    'msg.not_connected': 'Nicht verbunden',

    'ov.title': 'Gerätestatus', 'ov.noPrinters': 'Noch kein Drucker eingerichtet.',
    'ov.address': 'Adresse für das Kassensystem', 'ov.jobs': 'Druckaufträge',
    'ov.queued': 'in Warteschlange', 'ov.spooled': 'zwischengespeichert',
    'ov.connection': 'Verbindung', 'ov.model': 'Erkanntes Modell', 'ov.lastJob': 'Letzter Auftrag',
    'ov.lastError': 'Letzter Fehler', 'ov.listener': 'Netzwerk-Listener', 'ov.never': 'nie',
    'ov.testPrint': 'Testseite drucken', 'ov.refresh': 'Status aktualisieren',
    'ov.why': 'Warum? Alle Einzelprüfungen anzeigen', 'ov.drawer': 'Kassenlade',
    'ov.overall': 'Gesamtstatus', 'ov.overallHint': 'ein Drucker meldet etwas, siehe unten',
    'ov.statusReport': 'Statusbon drucken',

    'pr.title': 'Drucker verwalten', 'pr.add': 'Drucker hinzufügen', 'pr.scan': 'Geräte suchen',
    'pr.name': 'Name', 'pr.enabled': 'Aktiv', 'pr.bind': 'IP-Adresse für Port 9100',
    'pr.transport': 'Anschluss', 'pr.profile': 'Druckerprofil', 'pr.auto': 'automatisch erkennen',
    'pr.save': 'Speichern', 'pr.delete': 'Löschen', 'pr.redetect': 'Neu erkennen',
    'pr.devices': 'Gefundene Geräte', 'pr.noDevices': 'Keine Geräte gefunden. Drucker eingeschaltet? Eigenes 24-V-Netzteil angeschlossen?',
    'pr.use': 'Übernehmen', 'pr.options': 'Optionen', 'pr.confirmDelete': 'Drucker wirklich löschen?',
    'pr.connSettings': 'Anschluss-Einstellungen',

    'op.startup': 'Statusbon beim Start drucken',
    'op.paperlow': 'Warnung drucken, wenn das Papier zur Neige geht',
    'op.netalert': 'Hinweis drucken, wenn das Netzwerk ausfällt',
    'op.cut': 'Nach jedem Auftrag schneiden',
    'op.drawer': 'Nach jedem Auftrag Kassenlade öffnen',
    'op.reset': 'Vor jedem Auftrag zurücksetzen (ESC @)',
    'op.polling': 'Statusabfrage aktiv',
    'op.interval': 'Abfrageintervall (Sekunden)',
    'op.feed': 'Zeilenvorschub nach Auftrag',

    'fe.title': 'Druckerfunktionen', 'fe.detected': 'erkannt', 'fe.override': 'Einstellung',
    'fe.auto': 'automatisch', 'fe.on': 'ein (erzwungen)', 'fe.off': 'aus (erzwungen)',
    'fe.effective': 'wirksam', 'fe.probes': 'Aktive Tests (verbrauchen Papier)',
    'fe.probeCut': 'Schneiden testen', 'fe.probeDrawer': 'Kassenlade öffnen',
    'fe.probeBuzzer': 'Signalton', 'fe.probeFeed': 'Papiervorschub',
    'fe.testFeatures': 'Funktionstestseite', 'fe.recommend': 'Empfohlene Werte für das Kassensystem',
    'fe.drawerCheck': 'Kassenlade prüfen', 'fe.drawerState': 'Zustand der Kassenlade',
    'fe.drawerRunning': 'Test läuft … die Lade sollte jetzt aufspringen',

    'pt.title': 'Bon drucken', 'pt.printer': 'Drucker', 'pt.heading': 'Überschrift',
    'pt.body': 'Inhalt', 'pt.footer': 'Fußzeile', 'pt.qr': 'QR-Code (Text oder Adresse)',
    'pt.cut': 'Am Ende schneiden', 'pt.drawer': 'Kassenlade öffnen',
    'pt.preview': 'Vorschau', 'pt.print': 'Jetzt drucken', 'pt.clear': 'Leeren',
    'pt.example': 'Beispiel einfügen',
    'pt.bodyHelp': 'Eine Zeile = eine Zeile auf dem Bon. "---" ergibt eine Trennlinie. "Text | Wert" setzt den Wert rechtsbündig — ideal für Preise.',
    'pt.previewHint': 'Die Vorschau zeigt die tatsächliche Zeilenbreite des erkannten Druckers.',
    'pt.printed': 'Bon wurde an den Drucker geschickt',
    'pt.width': 'Zeilenbreite',
    'pv.cut': 'hier wird geschnitten', 'pv.drawer': 'Kassenlade öffnen',
    'pv.qr': 'QR-Code', 'pv.barcode': 'Barcode',
    'pt.noteCutter': 'Der Drucker hat keinen Schneider — der Schnitt wird weggelassen.',
    'pt.noteDrawer': 'Keine Kassenlade aktiv — der Impuls wird weggelassen.',
    'pt.noteQr': 'Der Drucker kann keine QR-Codes — der Code wird weggelassen.',
    'pt.noteBarcode': 'Der Drucker kann keine Barcodes — der Barcode wird weggelassen.',

    'di.title': 'Diagnose', 'di.report': 'Support-Bericht herunterladen', 'di.reload': 'Neu laden',
    'di.recentJobs': 'Letzte Druckaufträge', 'di.noJobs': 'Noch keine Aufträge.',
    'di.raw': 'Rohdaten senden (Experten)', 'di.rawSend': 'Senden',
    'di.commands': 'Systemausgaben', 'di.clearSpool': 'Zwischenspeicher leeren',
    'di.discovery': 'Automatische Druckersuche', 'di.probes': 'Empfangene Suchanfragen',
    'di.noProbes': 'Bisher keine Suchanfrage empfangen. Starte in der Kassen-App die Druckersuche und lade diese Seite neu.',
    'di.clearProbes': 'Liste leeren', 'di.answered': 'beantwortet', 'di.received': 'empfangen',
    'di.health': 'Alle Prüfungen',

    'co.title': 'Einbindung ins Kassensystem', 'co.oa': 'OrderAssist',
    'co.generic': 'Andere Kassensysteme', 'co.steps': 'Schritte',
    'co.ip': 'IP-Adresse', 'co.port': 'Port', 'co.protocol': 'Protokoll',
    'co.font': 'Schriftart', 'co.charset': 'Zeichensatz', 'co.width': 'Zeilenbreite',
    'co.copied': 'Kopiert', 'co.alt': 'Alternativen',

    'sy.title': 'System', 'sy.restart': 'Dienste neu starten', 'sy.settings': 'Einstellungen',
    'sy.save': 'Speichern', 'sy.docs': 'Dokumentation', 'sy.restartHint': 'Änderungen werden sofort übernommen.',
    'sy.webPort': 'Port der Weboberfläche', 'sy.rawPort': 'RAW-Port (Kassensystem)',
    'sy.mdns': 'mDNS/Bonjour-Ankündigung', 'sy.enpc': 'Auf Epson-Druckersuche antworten',
    'sy.logProbes': 'Suchanfragen protokollieren (Diagnose)',
    'sy.label': 'Gerätebezeichnung', 'sy.language': 'Sprache der Oberfläche',
    'sy.openDocs': 'Dokumentation öffnen',

    'di.discoveryIntro': 'Ein Drucker wird nicht „gefunden“ oder „nicht gefunden“ — sondern immer nur über ein bestimmtes Protokoll. BonBridge beantwortet deshalb alle gängigen und protokolliert jede eingehende Anfrage mit.',
    'di.probesSeen': '%s Suchanfragen empfangen',
    'di.noProbesYet': 'Noch keine Suchanfrage empfangen',
    'di.testHint': 'So findest du es heraus: Suchanfragen unten leeren, in der Kassen-App die Druckersuche starten, dann diese Seite neu laden. Was in der Tabelle hochzählt, ist das Protokoll, das die App benutzt.',
    'di.protocol': 'Protokoll', 'di.transport': 'Port', 'di.state': 'Zustand',
    'di.off': 'aus', 'di.blocked': 'Port belegt', 'di.answering': 'antwortet', 'di.watching': 'nur mithören',
    'di.notAnswered': 'nicht beantwortet', 'di.reply': 'Gesendete Antwort',
    'di.answeringHint': 'BonBridge antwortet aktiv auf %s Protokolle. „Nur mithören“ heißt: Anfragen werden protokolliert, aber nicht beantwortet — eine halbgare Antwort wäre schlimmer als keine.',
    'di.identity': 'Wie sich BonBridge im Netz nennt',
    'di.identityHelp': 'Kassen-Apps, die gezielt nach Epson-Druckern suchen, filtern nach Hersteller und Modell. Diese beiden Werte entscheiden also, ob das Gerät in der Liste der App überhaupt auftaucht.',
    'di.advVendor': 'Hersteller', 'di.advModel': 'Modell',
    'di.advNow': 'Aktuell angekündigt',
    'di.advSource.detected': 'erkanntes Modell', 'di.advSource.manual': 'von Hand gesetzt',
    'di.advSource.fallback': 'Rückfallwert, kein Modell erkannt',
    'di.enpcReply': 'ENPC-Antwortform',
    'di.enpcReply.cycle': 'durchprobieren (empfohlen)',
    'di.enpcReply.all': 'alle auf einmal senden',
    'di.enpcReplyHelp': 'Die App wiederholt ihre Suche alle paar Sekunden. Im Modus „durchprobieren“ bekommt jede Wiederholung die nächste Antwortform — eine Suche testet damit alle durch. Taucht der Drucker auf, steht unten in der Liste, welche Form zuletzt gesendet wurde; die dann hier fest einstellen.',
    'di.lastCandidate': 'zuletzt gesendet',
    'di.notPinned': 'Dieser Kernel liefert nicht mit, über welche Schnittstelle eine Anfrage kam. Antworten folgen deshalb der Routing-Tabelle — bei Geräten mit LAN und WLAN gleichzeitig kann die Antwort dann die falsche Schnittstelle nehmen.',
    'di.candidateList': 'Welche Antwortformen es gibt', 'di.candidate': 'Form',
    'di.snmpOn': 'SNMP beantworten (UDP 161)',
    'di.lpdOn': 'LPD/LPR beantworten (TCP 515)',
    'di.watchOn': 'Weitere Ports mithören (IPP, ePOS, SSDP)',
    'di.restartNeeded': 'die Lauschposten wurden neu gestartet',
    'di.saveHint': 'Beim Speichern werden die Lauschposten sofort neu gestartet — kein Neustart des Dienstes nötig.',

    'nw.title': 'Netzwerküberwachung',
    'nw.explain': 'BonBridge prüft regelmäßig, ob dieses Gerät überhaupt im Netz ist. Fällt die Verbindung aus, druckt der Drucker einen Hinweiszettel — er hängt ja an USB und funktioniert weiter. Das erspart die Fehlersuche am falschen Ende.',
    'nw.online': 'Netzwerk in Ordnung', 'nw.offline': 'Keine Netzwerkverbindung',
    'nw.unknown': 'noch nicht geprüft',
    'nw.noCarrier': 'kein Signal', 'nw.noAddress': 'verbunden, keine IP',
    'nw.enabled': 'Netzwerküberwachung aktiv',
    'nw.onLoss': 'Bon drucken, wenn die Verbindung ausfällt',
    'nw.onRestore': 'Bon drucken, wenn die Verbindung zurückkommt',
    'nw.gateway': 'Zusätzlich das Gateway anpingen',
    'nw.interval': 'Prüfintervall (Sekunden)',
    'nw.confirmations': 'Bestätigungen vor der Meldung',
    'nw.perPrinterHint': 'Welcher Drucker den Hinweis ausdruckt, stellst du je Drucker unter „Drucker → Optionen“ ein.',
    'nw.checkNow': 'Jetzt prüfen', 'nw.testSlip': 'Hinweiszettel testen',

    'up.title': 'Updates', 'up.installed': 'Installiert', 'up.latest': 'Verfügbar',
    'up.checkedAt': 'Zuletzt geprüft', 'up.repo': 'Quelle',
    'up.available': 'Update verfügbar', 'up.current': 'Aktuell — kein Update nötig',
    'up.notChecked': 'Noch nicht geprüft',
    'up.check': 'Auf Updates prüfen', 'up.checking': 'Suche nach Updates …',
    'up.install': 'Update installieren', 'up.notes': 'Änderungen in dieser Version',
    'up.confirm': 'Version %s jetzt installieren?\n\nDie Programmdateien werden ersetzt und der Dienst neu gestartet. Die Konfiguration bleibt erhalten, vorher wird ein Backup angelegt. Während des Updates wird nicht gedruckt.',
    'up.confirmFile': 'Hochgeladene Version %s jetzt installieren?\n\nDie Programmdateien werden ersetzt und der Dienst neu gestartet.',
    'up.started': 'Update gestartet — Ausgabe unten',
    'up.done': 'Update abgeschlossen', 'up.failed': 'Update fehlgeschlagen',
    'up.restarting': '… Dienst startet neu, die Seite lädt gleich neu …',
    'up.console': 'Konsolenausgabe', 'up.noOutput': '(noch keine Ausgabe)',
    'up.phase': 'Status',
    'up.offline': 'Update ohne Internet', 
    'up.offlineHelp': 'Wenn dieses Gerät nicht ins Internet kommt: Release auf einem anderen Rechner von GitHub herunterladen (.tar.gz oder .zip), hier hochladen und installieren.',
    'up.upload': 'Datei hochladen und installieren', 'up.pickFile': 'Bitte zuerst eine Datei auswählen',
    'up.allowWeb': 'Updates über die Weboberfläche erlauben',
    'up.checkOnStart': 'Beim Start und täglich auf Updates prüfen',
    'up.webDisabled': 'Updates über die Weboberfläche sind abgeschaltet. Auf der Konsole: sudo bonbridge update',
    'up.backups': 'Backups', 
    'up.backupHelp': 'Zurückrollen auf der Konsole:  sudo bonbridge update --rollback',

    'pt.modeText': 'Text', 'pt.modeImage': 'Bild',
    'pt.file': 'Bilddatei', 
    'pt.fileHelp': 'PNG, JPG, BMP, GIF oder WebP. PDF wird nicht unterstützt — bitte vorher als PNG exportieren. Die Vorschau zeigt exakt die Punkte, die gedruckt werden.',
    'pt.scale': 'Breite (% der Druckbreite)', 'pt.threshold': 'Schwellwert (1–254)',
    'pt.dither': 'Graustufen simulieren (Rasterung)', 'pt.invert': 'Invertieren (Negativ)',
    'pt.noImage': 'Noch kein Bild ausgewählt', 'pt.dots': 'Punkte',
    'pt.noteTransparent': 'Transparente Flächen wurden auf Weiß gelegt.',
    'pt.noteTruncated': 'Das Bild war zu hoch und wurde unten abgeschnitten.',

    'common.yes': 'ja', 'common.no': 'nein', 'common.saved': 'Gespeichert',
    'common.error': 'Fehler', 'common.queued': 'An den Drucker geschickt',
    'common.loading': 'Wird geladen …', 'common.unknown': 'unbekannt'
  },

  en: {
    'tab.overview': 'Overview', 'tab.printers': 'Printers', 'tab.features': 'Features',
    'tab.print': 'Print', 'tab.diag': 'Diagnostics', 'tab.connect': 'Integration',
    'tab.system': 'System', 'tab.docs': 'Docs',

    'status.ok': 'Ready', 'status.warn': 'Warning', 'status.error': 'Error',
    'status.offline': 'Not connected', 'status.unknown': 'Unknown', 'status.info': 'Note',

    'msg.ok': 'Ready',
    'msg.no_status': 'No status readable',
    'msg.unrecoverable_error': 'Unrecoverable printer error',
    'msg.autocutter_error': 'Auto cutter error',
    'msg.recoverable_error': 'Recoverable printer error',
    'msg.cover_open': 'Cover open',
    'msg.paper_end': 'Paper end',
    'msg.paper_near_end': 'Paper near end',
    'msg.printer_offline': 'Printer reports offline',
    'msg.not_connected': 'Not connected',

    'ov.title': 'Device status', 'ov.noPrinters': 'No printer configured yet.',
    'ov.address': 'Address for the POS application', 'ov.jobs': 'Print jobs',
    'ov.queued': 'queued', 'ov.spooled': 'spooled',
    'ov.connection': 'Connection', 'ov.model': 'Detected model', 'ov.lastJob': 'Last job',
    'ov.lastError': 'Last error', 'ov.listener': 'Network listener', 'ov.never': 'never',
    'ov.testPrint': 'Print test page', 'ov.refresh': 'Refresh status',
    'ov.why': 'Why? Show all individual checks', 'ov.drawer': 'Cash drawer',
    'ov.overall': 'Overall status', 'ov.overallHint': 'a printer is reporting something, see below',
    'ov.statusReport': 'Print status slip',

    'pr.title': 'Manage printers', 'pr.add': 'Add printer', 'pr.scan': 'Scan for devices',
    'pr.name': 'Name', 'pr.enabled': 'Enabled', 'pr.bind': 'IP address for port 9100',
    'pr.transport': 'Connection', 'pr.profile': 'Printer profile', 'pr.auto': 'detect automatically',
    'pr.save': 'Save', 'pr.delete': 'Delete', 'pr.redetect': 'Re-detect',
    'pr.devices': 'Detected devices', 'pr.noDevices': 'No devices found. Is the printer switched on with its own 24 V supply?',
    'pr.use': 'Use', 'pr.options': 'Options', 'pr.confirmDelete': 'Really delete this printer?',
    'pr.connSettings': 'Connection settings',

    'op.startup': 'Print a status slip on start-up',
    'op.paperlow': 'Print a warning when the paper runs low',
    'op.netalert': 'Print a notice when the network fails',
    'op.cut': 'Cut after every job',
    'op.drawer': 'Open the cash drawer after every job',
    'op.reset': 'Reset (ESC @) before every job',
    'op.polling': 'Status polling enabled',
    'op.interval': 'Polling interval (seconds)',
    'op.feed': 'Feed lines after job',

    'fe.title': 'Printer features', 'fe.detected': 'detected', 'fe.override': 'setting',
    'fe.auto': 'automatic', 'fe.on': 'on (forced)', 'fe.off': 'off (forced)',
    'fe.effective': 'effective', 'fe.probes': 'Active tests (these use paper)',
    'fe.probeCut': 'Test cutter', 'fe.probeDrawer': 'Open cash drawer',
    'fe.probeBuzzer': 'Buzzer', 'fe.probeFeed': 'Feed paper',
    'fe.testFeatures': 'Feature test page', 'fe.recommend': 'Recommended POS settings',
    'fe.drawerCheck': 'Check cash drawer', 'fe.drawerState': 'Cash drawer state',
    'fe.drawerRunning': 'Test running … the drawer should pop open now',

    'pt.title': 'Print a receipt', 'pt.printer': 'Printer', 'pt.heading': 'Heading',
    'pt.body': 'Content', 'pt.footer': 'Footer', 'pt.qr': 'QR code (text or address)',
    'pt.cut': 'Cut at the end', 'pt.drawer': 'Open the cash drawer',
    'pt.preview': 'Preview', 'pt.print': 'Print now', 'pt.clear': 'Clear',
    'pt.example': 'Insert example',
    'pt.bodyHelp': 'One line here = one line on the receipt. "---" draws a divider. "Text | value" puts the value flush right - ideal for prices.',
    'pt.previewHint': 'The preview uses the real line width of the detected printer.',
    'pt.printed': 'Receipt sent to the printer',
    'pt.width': 'Line width',
    'pv.cut': 'cut here', 'pv.drawer': 'open the cash drawer',
    'pv.qr': 'QR code', 'pv.barcode': 'barcode',
    'pt.noteCutter': 'The printer has no cutter - the cut is skipped.',
    'pt.noteDrawer': 'No cash drawer enabled - the pulse is skipped.',
    'pt.noteQr': 'The printer cannot do QR codes - the code is skipped.',
    'pt.noteBarcode': 'The printer cannot do barcodes - the barcode is skipped.',

    'di.title': 'Diagnostics', 'di.report': 'Download support report', 'di.reload': 'Reload',
    'di.recentJobs': 'Recent print jobs', 'di.noJobs': 'No jobs yet.',
    'di.raw': 'Send raw data (expert)', 'di.rawSend': 'Send',
    'di.commands': 'System output', 'di.clearSpool': 'Clear spool',
    'di.discovery': 'Automatic printer search', 'di.probes': 'Received search requests',
    'di.noProbes': 'No search request received yet. Start the printer search in the POS app and reload this page.',
    'di.clearProbes': 'Clear list', 'di.answered': 'answered', 'di.received': 'received',
    'di.health': 'All checks',

    'co.title': 'POS integration', 'co.oa': 'OrderAssist',
    'co.generic': 'Other POS systems', 'co.steps': 'Steps',
    'co.ip': 'IP address', 'co.port': 'Port', 'co.protocol': 'Protocol',
    'co.font': 'Font', 'co.charset': 'Character set', 'co.width': 'Line width',
    'co.copied': 'Copied', 'co.alt': 'Alternatives',

    'sy.title': 'System', 'sy.restart': 'Restart services', 'sy.settings': 'Settings',
    'sy.save': 'Save', 'sy.docs': 'Documentation', 'sy.restartHint': 'Changes are applied immediately.',
    'sy.webPort': 'Web interface port', 'sy.rawPort': 'RAW port (POS)',
    'sy.mdns': 'mDNS/Bonjour announcement', 'sy.enpc': 'Answer the Epson printer search',
    'sy.logProbes': 'Log search requests (diagnostics)',
    'sy.label': 'Device label', 'sy.language': 'Interface language',
    'sy.openDocs': 'Open the documentation',

    'di.discoveryIntro': 'A printer is never simply "found" or "not found" - only ever over a particular protocol. BonBridge therefore answers all the common ones and records every incoming request.',
    'di.probesSeen': '%s search requests received',
    'di.noProbesYet': 'No search request received yet',
    'di.testHint': 'How to find out: clear the log below, start the printer search in the POS app, then reload this page. Whatever counts up in the table is the protocol the app uses.',
    'di.protocol': 'Protocol', 'di.transport': 'Port', 'di.state': 'State',
    'di.off': 'off', 'di.blocked': 'port in use', 'di.answering': 'answering', 'di.watching': 'listening only',
    'di.notAnswered': 'not answered', 'di.reply': 'Reply sent',
    'di.answeringHint': 'BonBridge actively answers %s protocols. "Listening only" means requests are logged but not answered - a half-baked reply would be worse than none.',
    'di.identity': 'What BonBridge calls itself on the network',
    'di.identityHelp': 'POS apps that search specifically for Epson printers filter by manufacturer and model. These two values therefore decide whether the device shows up in the app list at all.',
    'di.advVendor': 'Manufacturer', 'di.advModel': 'Model',
    'di.advNow': 'Currently announced',
    'di.advSource.detected': 'detected model', 'di.advSource.manual': 'set by hand',
    'di.advSource.fallback': 'fallback, no model detected',
    'di.enpcReply': 'ENPC reply shape',
    'di.enpcReply.cycle': 'try each in turn (recommended)',
    'di.enpcReply.all': 'send all at once',
    'di.enpcReplyHelp': 'The app repeats its search every few seconds. In "try each in turn" mode every retry gets the next reply shape, so one search tries them all. When the printer appears, the list below shows which shape was sent last - pin that one here.',
    'di.lastCandidate': 'last sent',
    'di.notPinned': 'This kernel does not report which interface a request arrived on, so replies follow the routing table. On a device with Ethernet and Wi-Fi up at once the reply may take the wrong interface.',
    'di.candidateList': 'The available reply shapes', 'di.candidate': 'Shape',
    'di.snmpOn': 'Answer SNMP (UDP 161)',
    'di.lpdOn': 'Answer LPD/LPR (TCP 515)',
    'di.watchOn': 'Listen on further ports (IPP, ePOS, SSDP)',
    'di.restartNeeded': 'the listeners were restarted',
    'di.saveHint': 'Saving restarts the listeners straight away - no service restart needed.',

    'nw.title': 'Network watchdog',
    'nw.explain': 'BonBridge regularly checks whether this device is on the network at all. If the connection drops, the printer prints a notice - it is attached over USB and keeps working. That saves troubleshooting at the wrong end.',
    'nw.online': 'Network is fine', 'nw.offline': 'No network connection',
    'nw.unknown': 'not checked yet',
    'nw.noCarrier': 'no link', 'nw.noAddress': 'link up, no IP',
    'nw.enabled': 'Network watchdog active',
    'nw.onLoss': 'Print a slip when the connection drops',
    'nw.onRestore': 'Print a slip when the connection returns',
    'nw.gateway': 'Also ping the gateway',
    'nw.interval': 'Check interval (seconds)',
    'nw.confirmations': 'Confirmations before reporting',
    'nw.perPrinterHint': 'Which printer prints the notice is set per printer under "Printers -> Options".',
    'nw.checkNow': 'Check now', 'nw.testSlip': 'Test the notice slip',

    'up.title': 'Updates', 'up.installed': 'Installed', 'up.latest': 'Available',
    'up.checkedAt': 'Last checked', 'up.repo': 'Source',
    'up.available': 'Update available', 'up.current': 'Up to date - nothing to do',
    'up.notChecked': 'Not checked yet',
    'up.check': 'Check for updates', 'up.checking': 'Looking for updates ...',
    'up.install': 'Install the update', 'up.notes': 'What changed in this version',
    'up.confirm': 'Install version %s now?\n\nThe program files are replaced and the service is restarted. The configuration is kept and a backup is written first. Nothing is printed while the update runs.',
    'up.confirmFile': 'Install the uploaded version %s now?\n\nThe program files are replaced and the service is restarted.',
    'up.started': 'Update started - output below',
    'up.done': 'Update finished', 'up.failed': 'Update failed',
    'up.restarting': '... the service is restarting, the page will reload shortly ...',
    'up.console': 'Console output', 'up.noOutput': '(no output yet)',
    'up.phase': 'State',
    'up.offline': 'Update without internet',
    'up.offlineHelp': 'If this device has no internet access: download the release from GitHub on another machine (.tar.gz or .zip), upload it here and install it.',
    'up.upload': 'Upload the file and install', 'up.pickFile': 'Please choose a file first',
    'up.allowWeb': 'Allow updates through the web interface',
    'up.checkOnStart': 'Check for updates at start-up and daily',
    'up.webDisabled': 'Updates through the web interface are switched off. On the console: sudo bonbridge update',
    'up.backups': 'Backups',
    'up.backupHelp': 'Roll back on the console:  sudo bonbridge update --rollback',

    'pt.modeText': 'Text', 'pt.modeImage': 'Image',
    'pt.file': 'Image file',
    'pt.fileHelp': 'PNG, JPG, BMP, GIF or WebP. PDF is not supported - please export it as a PNG first. The preview shows exactly the dots that will be printed.',
    'pt.scale': 'Width (% of the print width)', 'pt.threshold': 'Threshold (1-254)',
    'pt.dither': 'Simulate grey levels (dithering)', 'pt.invert': 'Invert (negative)',
    'pt.noImage': 'No image chosen yet', 'pt.dots': 'dots',
    'pt.noteTransparent': 'Transparent areas were placed on white.',
    'pt.noteTruncated': 'The image was too tall and was cut off at the bottom.',

    'common.yes': 'yes', 'common.no': 'no', 'common.saved': 'Saved',
    'common.error': 'Error', 'common.queued': 'Sent to the printer',
    'common.loading': 'Loading …', 'common.unknown': 'unknown'
  }
};

/* Short explanations shown when hovering an input. */
const HELP = {
  de: {
    'pr.name': 'Frei wählbarer Name, z. B. "Küche" oder "Theke". Er erscheint auf Testdrucken, im Support-Bericht und in der mDNS-Ankündigung. Auf die Funktion hat er keinen Einfluss.',
    'pr.bind': 'An welche IP-Adresse dieses Geräts der Drucker-Port 9100 gebunden wird.\n\n0.0.0.0 (Standard) = alle Adressen. Das ist bei EINEM Drucker immer richtig — das Kassensystem erreicht ihn dann unter jeder IP des Geräts.\n\nEine feste IP trägst du nur ein, wenn MEHRERE Drucker an diesem Gerät hängen: Kassensysteme wie OrderAssist unterscheiden Drucker ausschließlich über die IP-Adresse, der Port ist fest 9100. Jeder Drucker braucht deshalb eine eigene IP. Diese Zusatz-IP muss vorher auf dem Gerät angelegt werden (siehe Doku "Mehrere Drucker").',
    'pr.transport': 'Wie der Drucker angeschlossen ist. "automatisch" sucht bei jedem Start das plausibelste lokale Gerät — für den Normalfall richtig.\n\nusb = über libusb, funktioniert auch bei Druckern ohne /dev/usb/lp0.\nusblp = klassisches Kernel-Gerät /dev/usb/lp0.\nseriell = RS-232 oder USB-Seriell-Adapter.\nnetzwerk = ein Drucker, der bereits selbst im Netz hängt.',
    'pr.profile': 'Bestimmt Zeichen pro Zeile, Codepages und welche Funktionen der Drucker hat. "automatisch erkennen" liest die USB-Kennung und die Drucker-ID aus und wählt selbst — nur ändern, wenn die Erkennung danebenliegt.',
    'pr.enabled': 'Nimmt den Drucker in Betrieb. Deaktiviert bleibt die Konfiguration erhalten, es wird aber kein Port geöffnet und nichts gedruckt.',
    'transport.vendor_id': 'USB-Hersteller-Kennung, z. B. 0x04b8 für Epson. Wird beim Gerätescan automatisch gefüllt.',
    'transport.product_id': 'USB-Produkt-Kennung des Modells. Wird beim Gerätescan automatisch gefüllt.',
    'transport.serial': 'Seriennummer des Druckers. Nur nötig, wenn ZWEI baugleiche Drucker am selben Gerät hängen — ohne sie kann sich die Zuordnung nach einem Neustart vertauschen.',
    'transport.device': 'Gerätedatei, z. B. /dev/usb/lp0 oder /dev/ttyUSB0. Leer lassen, damit die erste passende genommen wird.',
    'transport.baudrate': 'Übertragungsgeschwindigkeit der seriellen Schnittstelle. Muss mit den DIP-Schaltern am Drucker übereinstimmen — bei Epson meist 38400.',
    'transport.host': 'IP-Adresse des Netzwerkdruckers, mit dem sich BonBridge verbinden soll.',
    'transport.port': 'Port des Netzwerkdruckers, praktisch immer 9100.',
    'op.startup': 'Druckt direkt nach dem Einschalten einen Bon mit IP-Adresse, Port und den Werten fürs Kassensystem. Praktisch, weil das Gerät keinen Bildschirm hat. Die Einstellung bleibt auch nach einem Stromausfall erhalten.',
    'op.paperlow': 'Sobald der Drucker "Papier fast leer" meldet, wird einmalig ein Hinweiszettel gedruckt. Wird erst wieder gedruckt, wenn zwischendurch neues Papier eingelegt wurde.',
    'op.cut': 'Hängt an jeden Auftrag einen Schnittbefehl an. Nur einschalten, wenn das Kassensystem selbst nicht schneidet — sonst wird zweimal geschnitten.',
    'op.drawer': 'Löst nach jedem Auftrag den Kassenladen-Impuls aus. Für Küchendrucker in der Regel unerwünscht.',
    'op.reset': 'Setzt den Drucker vor jedem Auftrag in den Grundzustand. Hilft, wenn ein vorheriger Auftrag Schriftgröße oder Ausrichtung verstellt hinterlassen hat.',
    'op.polling': 'Fragt den Druckerzustand regelmäßig ab (Papier, Deckel, Fehler). Ohne diese Abfrage bleibt die Statusampel grau.',
    'op.interval': 'Wie oft der Zustand abgefragt wird. 10 Sekunden sind ein guter Kompromiss; kleinere Werte belasten den Drucker unnötig.',
    'op.feed': 'Zusätzliche Leerzeilen am Ende jedes Auftrags, bevor geschnitten wird. Hilft, wenn der Schnitt zu dicht am Text liegt.',
    'sy.label': 'Name, unter dem sich das Gerät im Netzwerk meldet und der auf dem Statusbon steht. Leer = Hostname des Geräts.',
    'sy.webPort': 'Port dieser Weboberfläche. Nach dem Ändern ist sie nur noch unter dem neuen Port erreichbar.',
    'sy.rawPort': 'Port, auf dem Druckaufträge angenommen werden. OrderAssist verwendet fest 9100 und lässt sich nicht umstellen — nur zu Testzwecken ändern.',
    'sy.mdns': 'Meldet Gerät und Drucker per mDNS/Bonjour im Netz an. Macht Namen wie geraet.local möglich — funktioniert unter Windows aber nur mit installiertem Bonjour. Die IP-Adresse funktioniert immer.',
    'sy.enpc': 'Beantwortet die Suchpakete, die Kassen-Apps für Epson-Netzwerkdrucker verschicken (UDP 3289). Damit kann BonBridge in der automatischen Druckersuche auftauchen. Epson veröffentlicht das Protokoll nicht, deshalb ist das Antwortformat nicht garantiert.',
    'sy.logProbes': 'Zeichnet jede empfangene Suchanfrage samt Hexdump auf. Damit lässt sich prüfen, ob die Kassen-App überhaupt sucht. Sichtbar unter Diagnose.',
    'sy.language': 'Sprache dieser Oberfläche, der gedruckten Statusbons und der verlinkten Dokumentation.',
    'pt.heading': 'Große, fette Überschrift ganz oben auf dem Bon. Kann leer bleiben.',
    'pt.body': 'Der eigentliche Inhalt. Eine Zeile hier wird eine Zeile auf dem Bon.',
    'pt.footer': 'Kleiner, zentrierter Text am Ende, z. B. "Vielen Dank für Ihren Besuch".',
    'pt.qr': 'Wird als QR-Code unten auf den Bon gedruckt, z. B. eine Internetadresse. Leer lassen, wenn kein QR-Code gewünscht ist.',
    'pt.cut': 'Schneidet das Papier nach dem Bon ab, falls der Drucker einen Schneider hat.',
    'pt.drawer': 'Öffnet nach dem Druck die Kassenlade, falls eine angeschlossen ist.',
    'di.raw': 'Sendet Bytes unverändert an den Drucker. Text wird als Text gesendet; reine Hex-Zeichen werden als Bytes interpretiert, z. B. "1B 40" für einen Reset. Nur benutzen, wenn du weißt was du tust.',
    'di.advVendor': 'Der Herstellername, den BonBridge über ENPC, SNMP und mDNS ankündigt. Kassen-Apps, die nur Epson-Drucker anzeigen, vergleichen genau diesen Text. „EPSON“ ist deshalb der sinnvolle Wert, auch wenn im Gerät ein Raspberry Pi steckt — es ist eine Kompatibilitätsangabe, kein Etikettenschwindel.',
    'di.advModel': 'Der Modellname, der angekündigt wird. „auto“ nimmt das erkannte Modell des angeschlossenen Druckers (z. B. TM-T88V) und fällt nur dann auf einen Standardwert zurück, wenn nichts erkannt wurde. Von Hand setzen, wenn die App ein bestimmtes Modell erwartet.',
    'di.enpcReply': 'Epson veröffentlicht das Antwortformat der Druckersuche nicht. Deshalb gibt es mehrere Kandidaten — der erste ist die byteweise nachgebaute Antwort eines echten TM-m30, nur mit ausgetauschtem Modellnamen. „Durchprobieren“ nutzt aus, dass die App ihre Suche wiederholt: jede Wiederholung bekommt die nächste Form.',
    'di.snmpOn': 'Beantwortet Statusabfragen auf UDP 161 wie ein echtes Epson-Netzwerkboard. Viele Suchfunktionen fragen einfach das ganze Subnetz per SNMP ab — ohne Antwort ist das Gerät für sie nicht vorhanden.',
    'di.lpdOn': 'Nimmt Verbindungen auf TCP 515 an (klassischer Netzwerkdruck). Dient der Auffindbarkeit und erlaubt zusätzlich echtes Drucken per LPR.',
    'di.watchOn': 'Öffnet zusätzlich passive Lauschposten auf IPP (631), ePOS (8008) und SSDP (1900). Diese antworten nie — sie halten nur fest, wer angeklopft hat. Genau das zeigt, welches Protokoll eine App tatsächlich benutzt.',
    'op.netalert': 'Druckt auf DIESEM Drucker einen Hinweiszettel, wenn das Gerät seine Netzwerkverbindung verliert oder wiederbekommt. Sinnvoll, weil das Kassensystem dann nicht mehr drucken kann und sonst niemand erfährt, warum. Ist gerade kein Drucker verbunden, wird nichts gedruckt und auch nichts nachgeholt.',
    'nw.interval': 'Wie oft der Netzwerkzustand geprüft wird. 60 Sekunden ist ein guter Kompromiss: schnell genug, um einen Ausfall früh zu bemerken, sparsam genug für einen kleinen Raspberry Pi. Minimum 10 Sekunden.',
    'nw.confirmations': 'Wie oft der neue Zustand hintereinander bestätigt werden muss, bevor gedruckt wird. Bei 2 führt ein kurzer WLAN-Wechsel nicht zu einem Zettel. Bei 1 wird sofort gemeldet.',
    'nw.enabled': 'Schaltet die gesamte Überwachung ein oder aus. Ausgeschaltet wird der Netzwerkzustand weder geprüft noch angezeigt.',
    'nw.onLoss': 'Der Zettel beim Ausfall ist der eigentliche Zweck: Er erklärt am Drucker, warum das Kassensystem nichts mehr sendet.',
    'nw.onRestore': 'Beim Wiederverbinden wird ein zweiter Zettel gedruckt — mit der aktuellen IP-Adresse, die sich nach einem Router-Neustart geändert haben kann.',
    'nw.gateway': 'Prüft zusätzlich, ob der Router antwortet. Erkennt den Fall "verbunden, aber Router tot". Kostet bei jeder Prüfung einen Ping-Prozess, deshalb standardmäßig aus.',
    'up.allowWeb': 'Erlaubt Installation von Updates über diese Weboberfläche. Die Oberfläche hat kein Passwort — wer im selben Netz ist, könnte also Software auf dem Gerät installieren. Ausgeschaltet geht ein Update nur noch über SSH mit "sudo bonbridge update".',
    'up.checkOnStart': 'Fragt beim Start und danach einmal täglich bei GitHub nach, ob es eine neuere Version gibt. Es wird nie automatisch installiert.',
    'pt.scale': 'Wie breit das Bild gedruckt wird, in Prozent der Druckbreite. 100 % nutzt die volle Breite; kleinere Werte lassen links und rechts Rand.',
    'pt.threshold': 'Ab welcher Helligkeit ein Punkt schwarz wird — nur wirksam, wenn die Rasterung aus ist. Kleiner Wert = weniger Schwarz.',
    'pt.dither': 'Simuliert Graustufen durch ein feines Punktmuster. Für Fotos fast immer richtig. Für Logos und Strichzeichnungen ist ein harter Schwellwert oft sauberer.',
    'pt.invert': 'Tauscht Schwarz und Weiß. Nützlich für helle Schrift auf dunklem Grund, die sonst als schwarzer Block herauskäme.'
  },
  en: {
    'pr.name': 'Free-text name such as "Kitchen" or "Bar". It appears on test prints, in the support report and in the mDNS announcement. It has no effect on behaviour.',
    'pr.bind': 'Which IP address of this device the printer port 9100 is bound to.\n\n0.0.0.0 (default) = all addresses. With ONE printer this is always right - the POS application reaches it on any IP of the device.\n\nSet a fixed IP only when SEVERAL printers are attached to this device: POS systems such as OrderAssist tell printers apart by IP address only, the port is fixed at 9100. Each printer therefore needs its own IP. That extra IP has to be created on the device first (see the "Several printers" documentation).',
    'pr.transport': 'How the printer is attached. "detect automatically" picks the most plausible local device at every start - correct for the normal case.\n\nusb = via libusb, also works for printers without /dev/usb/lp0.\nusblp = the classic kernel device /dev/usb/lp0.\nserial = RS-232 or a USB-to-serial adapter.\nnetwork = a printer that is already on the network itself.',
    'pr.profile': 'Determines characters per line, code pages and which features the printer has. "detect automatically" reads the USB identity and the printer ID and decides - only change it if detection got it wrong.',
    'pr.enabled': 'Puts the printer into service. When disabled the configuration is kept but no port is opened and nothing is printed.',
    'transport.vendor_id': 'USB vendor ID, e.g. 0x04b8 for Epson. Filled in automatically by the device scan.',
    'transport.product_id': 'USB product ID of the model. Filled in automatically by the device scan.',
    'transport.serial': 'Serial number of the printer. Only needed when TWO identical printers are attached to the same device - without it the assignment can swap after a reboot.',
    'transport.device': 'Device file, e.g. /dev/usb/lp0 or /dev/ttyUSB0. Leave empty to use the first matching one.',
    'transport.baudrate': 'Speed of the serial line. Must match the DIP switches on the printer - usually 38400 on Epson.',
    'transport.host': 'IP address of the network printer BonBridge should connect to.',
    'transport.port': 'Port of the network printer, practically always 9100.',
    'op.startup': 'Prints a slip with the IP address, port and POS settings right after power-up. Useful because the device has no screen. The setting survives a power cut.',
    'op.paperlow': 'Prints a one-off notice as soon as the printer reports "paper near end". It is only printed again after new paper has been loaded.',
    'op.cut': 'Appends a cut command to every job. Only enable it when the POS application does not cut by itself - otherwise it cuts twice.',
    'op.drawer': 'Fires the cash drawer pulse after every job. Usually undesirable for a kitchen printer.',
    'op.reset': 'Returns the printer to its default state before every job. Helps when a previous job left the font size or alignment changed.',
    'op.polling': 'Polls the printer state regularly (paper, cover, errors). Without it the traffic light stays grey.',
    'op.interval': 'How often the state is polled. 10 seconds is a good compromise; smaller values load the printer for nothing.',
    'op.feed': 'Extra blank lines at the end of every job before cutting. Helps when the cut sits too close to the text.',
    'sy.label': 'The name the device announces on the network and prints on the status slip. Empty = the device hostname.',
    'sy.webPort': 'Port of this web interface. After changing it the interface is only reachable on the new port.',
    'sy.rawPort': 'Port that accepts print jobs. OrderAssist always uses 9100 and cannot be changed - only change this for testing.',
    'sy.mdns': 'Announces the device and its printers via mDNS/Bonjour. Enables names such as device.local - but on Windows only with Bonjour installed. The IP address always works.',
    'sy.enpc': 'Answers the discovery packets POS apps send for Epson network printers (UDP 3289), so BonBridge can appear in the automatic printer search. Epson does not publish the protocol, so the reply format is not guaranteed.',
    'sy.logProbes': 'Records every received search request with a hexdump, so you can tell whether the POS app searches at all. Shown under Diagnostics.',
    'sy.language': 'Language of this interface, of the printed status slips and of the linked documentation.',
    'pt.heading': 'Large, bold heading at the top of the receipt. May be left empty.',
    'pt.body': 'The actual content. One line here becomes one line on the receipt.',
    'pt.footer': 'Small centred text at the end, e.g. "Thank you for your visit".',
    'pt.qr': 'Printed as a QR code at the bottom, e.g. a web address. Leave empty for no QR code.',
    'pt.cut': 'Cuts the paper after the receipt, if the printer has a cutter.',
    'pt.drawer': 'Opens the cash drawer after printing, if one is connected.',
    'di.raw': 'Sends bytes to the printer unchanged. Text is sent as text; pure hex characters are interpreted as bytes, e.g. "1B 40" for a reset. Only use this if you know what you are doing.',
    'di.advVendor': 'The manufacturer name BonBridge announces over ENPC, SNMP and mDNS. POS apps that only list Epson printers compare exactly this text. "EPSON" is therefore the sensible value even though a Raspberry Pi is inside - it is a compatibility declaration, not a disguise.',
    'di.advModel': 'The model name that is announced. "auto" uses the detected model of the attached printer (e.g. TM-T88V) and only falls back to a default when nothing was detected. Set it by hand if the app expects a particular model.',
    'di.enpcReply': 'Epson does not publish the reply format of the printer search, so there are several candidates - the first one reproduces the reply of a real TM-m30 byte for byte with only the model name swapped. "Try each in turn" exploits the fact that the app repeats its search: every retry gets the next shape.',
    'di.snmpOn': 'Answers status queries on UDP 161 the way a real Epson network board does. Many search functions simply sweep the whole subnet with SNMP - without an answer the device does not exist for them.',
    'di.lpdOn': 'Accepts connections on TCP 515 (classic network printing). Helps with discovery and additionally allows real LPR printing.',
    'di.watchOn': 'Additionally opens passive listeners on IPP (631), ePOS (8008) and SSDP (1900). These never answer - they only record who knocked. That is precisely what reveals which protocol an app really uses.',
    'op.netalert': 'Prints a notice on THIS printer when the device loses or regains its network connection. Useful because the POS application cannot print then, and otherwise nobody learns why. If no printer is connected at that moment nothing is printed and nothing is caught up later.',
    'nw.interval': 'How often the network state is checked. 60 seconds is a good compromise: quick enough to notice an outage early, cheap enough for a small Raspberry Pi. Minimum is 10 seconds.',
    'nw.confirmations': 'How many consecutive checks must agree before a slip is printed. At 2 a brief Wi-Fi roam does not produce one. At 1 it is reported immediately.',
    'nw.enabled': 'Switches the whole watchdog on or off. When off, the network state is neither checked nor displayed.',
    'nw.onLoss': 'The outage slip is the actual point: it explains, at the printer, why the POS application stopped sending anything.',
    'nw.onRestore': 'When the connection returns a second slip is printed - carrying the current IP address, which may have changed after a router restart.',
    'nw.gateway': 'Additionally checks whether the router answers. Catches "connected but the router is dead". Costs one ping process per check, hence off by default.',
    'up.allowWeb': 'Allows updates to be installed through this web interface. The interface has no password, so anyone on the same network could install software on the device. When off, updating is only possible over SSH with "sudo bonbridge update".',
    'up.checkOnStart': 'Asks GitHub at start-up and once a day whether a newer version exists. Nothing is ever installed automatically.',
    'pt.scale': 'How wide the image is printed, as a percentage of the print width. 100% uses the full width; smaller values leave a margin left and right.',
    'pt.threshold': 'The brightness at which a dot turns black - only in effect when dithering is off. A lower value means less black.',
    'pt.dither': 'Simulates grey levels with a fine dot pattern. Almost always right for photos. For logos and line art a hard threshold is often cleaner.',
    'pt.invert': 'Swaps black and white. Useful for light text on a dark background, which would otherwise come out as a black block.'
  }
};

let LANG = localStorage.getItem('bb.lang') || 'de';
let STATE = { overview: null, devices: [], profiles: [], scanned: false, configOptions: {}, configProfiles: {} };
let CURRENT = 'overview';
let TIMER = null;
let PREVIEW_TIMER = null;

const t = (key) => (I18N[LANG] && I18N[LANG][key]) || (I18N.de[key] || key);
const help = (key) => (HELP[LANG] && HELP[LANG][key]) || (HELP.de[key] || '');
const $ = (sel, root) => (root || document).querySelector(sel);
const esc = (value) => String(value == null ? '' : value)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const bi = (obj, base) => (obj && (LANG === 'de' ? obj[base + '_de'] : obj[base + '_en'])) || '';

/** A <label> with a dotted underline and the explanation as a tooltip. */
function lbl(key, text) {
  const explanation = help(key);
  if (!explanation) return '<label>' + esc(text) + '</label>';
  return '<label><span class="why" title="' + esc(explanation) + '">' + esc(text) + '</span></label>';
}
function checkbox(key, field, text, checked) {
  return '<label style="display:flex;align-items:flex-start;gap:.5rem;margin:.5rem 0" title="' +
    esc(help(key)) + '"><input type="checkbox" style="width:auto;margin-top:.2rem" data-f="' + field + '"' +
    (checked ? ' checked' : '') + '> <span class="why">' + esc(text) + '</span></label>';
}

function toast(message, isError) {
  const box = $('#toast');
  box.textContent = message;
  box.className = isError ? 'err' : '';
  box.style.display = 'block';
  clearTimeout(box._timer);
  box._timer = setTimeout(() => { box.style.display = 'none'; }, 4000);
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
  return new Date(seconds * 1000).toLocaleString();
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
function statusMessages(keys) {
  return (keys || []).map((k) => t('msg.' + k) || k).join(' · ');
}
function kv(key, value) { return '<div><span>' + key + '</span><span>' + value + '</span></div>'; }

function copyText(value) {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(value).then(() => toast(t('co.copied') + ': ' + value), () => toast(value));
  } else { toast(value); }
}
window.copyText = copyText;

/* ------------------------------------------------------------------ */
/* Remembering what the user opened or closed                          */
/*                                                                     */
/* The overview re-renders every five seconds.  Without this, every    */
/* panel the user collapsed sprang open again on the next refresh.     */
/* The choice is keyed per block, kept in localStorage and therefore   */
/* also survives a page reload.                                        */
/* ------------------------------------------------------------------ */

let OPEN_STATE = {};
try { OPEN_STATE = JSON.parse(localStorage.getItem('bb.open') || '{}') || {}; } catch (e) { OPEN_STATE = {}; }

function isOpen(key, fallback) {
  if (key && Object.prototype.hasOwnProperty.call(OPEN_STATE, key)) return !!OPEN_STATE[key];
  return !!fallback;
}
function rememberOpen(key, open) {
  if (!key) return;
  OPEN_STATE[key] = !!open;
  try { localStorage.setItem('bb.open', JSON.stringify(OPEN_STATE)); } catch (e) { /* private mode */ }
}
/** <details> that keeps its state.  `key` must be stable across renders. */
function detailsOpen(key, fallback) {
  return ' data-open-key="' + esc(key) + '"' + (isOpen(key, fallback) ? ' open' : '');
}
/** A collapsible block whose open/closed state is remembered. */
function foldable(key, title, bodyHtml, defaultOpen) {
  return '<details class="fold"' + detailsOpen(key, defaultOpen) + '><summary>' +
    title + '</summary><div class="foldbody">' + bodyHtml + '</div></details>';
}

/** Collapsible list of health checks with title + explanation. */
function checksBlock(entry, label, key) {
  if (!entry || !(entry.checks || []).length) return '';
  const problems = entry.problems || [];
  const summary = problems.length
    ? problems.map((c) => esc(bi(c, 'title'))).join(' · ')
    : t('status.ok');
  let html = '<details class="checks"' + detailsOpen(key || ('checks:' + (label || 'device')), problems.length > 0) + '>';
  html += '<summary>' + (label || t('ov.why')) + ' — <span class="muted">' + summary + '</span></summary>';
  entry.checks.forEach((c) => {
    html += '<div class="checkitem"><div class="t"><span class="dot ' + esc(c.level) + '"></span>' +
      esc(bi(c, 'title')) + '</div>';
    const detail = bi(c, 'detail');
    if (detail) html += '<div class="d">' + esc(detail) + '</div>';
    html += '</div>';
  });
  html += '</details>';
  return html;
}

/* ------------------------------------------------------------------ */
/* Overview                                                            */
/* ------------------------------------------------------------------ */

function renderOverview() {
  const data = STATE.overview;
  const root = $('#overview');
  if (!data) { root.innerHTML = '<div class="card">' + t('common.loading') + '</div>'; return; }
  const sys = data.system;
  const health = data.health || {};
  $('#hdrHost').textContent = sys.hostname + '  ·  ' + sys.primary_ip + '  ·  v' + data.version;

  const deviceLevel = (health.device && health.device.level) || 'unknown';
  let html = '<div class="card"><h2>' + t('ov.title') + '</h2>' +
    '<div class="big">' + statusDot(deviceLevel) + '</div>' +
    (deviceLevel !== data.overall_status
      ? '<div class="muted" style="margin:.2rem 0 .4rem">' + t('ov.overall') + ': ' +
        statusDot(data.overall_status) + ' — ' + t('ov.overallHint') + '</div>'
      : '') +
    '<div class="kv" style="margin-top:.6rem">' +
    kv(esc(sys.model), esc(sys.os)) + kv('IP', esc(sys.primary_ip)) +
    kv('Uptime', fmtDuration(sys.uptime)) +
    (sys.cpu_temperature ? kv('CPU', sys.cpu_temperature.toFixed(1) + ' °C') : '') +
    '</div>' + checksBlock(health.device, null, 'ov.device') + '</div>';

  if (!data.printers.length) html += '<div class="card">' + t('ov.noPrinters') + '</div>';

  data.printers.forEach((printer) => {
    const listener = printer.listener || {};
    const caps = printer.capabilities || {};
    const drawer = printer.drawer || {};
    const ph = (health.printers || {})[printer.id];
    html += '<div class="card"><h2>' + esc(printer.name) + ' <span class="tag">' + esc(printer.id) + '</span></h2>' +
      '<div class="big">' + statusDot(printer.status_level) + '</div>' +
      '<div class="muted" style="margin:.2rem 0 .8rem">' + esc(statusMessages(printer.status_messages)) + '</div>' +
      '<div class="row"><div class="kv">' +
      kv(t('ov.address'), '<code class="copy" onclick="copyText(\'' + esc(printer.pos_address) + '\')">' +
         esc(printer.pos_address) + ':' + esc(printer.pos_port) + '</code>') +
      kv(t('ov.connection'), esc(printer.connection || '-')) +
      kv(t('ov.model'), esc(caps.profile_name || '-')) +
      (drawer.state ? kv(t('ov.drawer'), esc(bi(drawer, 'label'))) : '') +
      '</div><div class="kv">' +
      kv(t('ov.jobs'), printer.jobs_total + ' / ' + fmtBytes(printer.bytes_total) +
         ' · ' + printer.queued + ' ' + t('ov.queued') + ' · ' + printer.spooled + ' ' + t('ov.spooled')) +
      kv(t('ov.lastJob'), fmtTime(printer.last_job_at)) +
      kv(t('ov.listener'), (listener.listening ? '' : '<span class="dot error"></span>') +
         esc(listener.bind + ':' + listener.port) + (listener.error ? ' — ' + esc(listener.error) : '')) +
      (printer.last_error ? kv(t('ov.lastError'), '<span style="color:var(--err)">' + esc(printer.last_error) + '</span>') : '') +
      '</div></div>' + checksBlock(ph, null, 'ov.printer:' + printer.id) +
      '<div class="btnbar">' +
      '<button class="act primary" onclick="testPrint(\'' + esc(printer.id) + '\',\'standard\')">' + t('ov.testPrint') + '</button>' +
      '<button class="act" onclick="printStatusSlip(\'' + esc(printer.id) + '\')">' + t('ov.statusReport') + '</button>' +
      '<button class="act" onclick="refreshPrinter(\'' + esc(printer.id) + '\')">' + t('ov.refresh') + '</button>' +
      '</div></div>';
  });

  root.innerHTML = html;
}

async function testPrint(printerId, kind) {
  try {
    await api('/api/printers/' + encodeURIComponent(printerId) + '/test',
      { method: 'POST', body: JSON.stringify({ kind: kind }) });
    toast(t('common.queued'));
  } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
async function printStatusSlip(printerId) {
  try {
    await api('/api/printers/' + encodeURIComponent(printerId) + '/startup-report', { method: 'POST' });
    toast(t('common.queued'));
  } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
async function refreshPrinter(printerId) {
  try { await api('/api/printers/' + encodeURIComponent(printerId) + '/refresh', { method: 'POST' }); await reload(true); }
  catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
window.testPrint = testPrint; window.refreshPrinter = refreshPrinter; window.printStatusSlip = printStatusSlip;

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
      html += '<tr><td>' + esc(device.transport) + '</td><td>' + esc(device.label || '') +
        (device.serial ? '<br><span class="muted">SN ' + esc(device.serial) + '</span>' : '') + '</td>' +
        '<td style="width:6rem"><button class="act" onclick="useDevice(' + index + ')">' + t('pr.use') + '</button></td></tr>';
    });
    html += '</table>';
  } else if (STATE.scanned) {
    html += '<p class="muted">' + t('pr.noDevices') + '</p>';
  }
  html += '</div>';

  data.printers.forEach((printer) => {
    const transport = (printer.transport && printer.transport.settings) || {};
    const transportType = (printer.transport && printer.transport.type) || 'auto';
    const options = STATE.configOptions[printer.id] || {};
    html += '<div class="card" data-printer="' + esc(printer.id) + '"><h2>' + esc(printer.name) + '</h2>' +
      '<div class="grid2">' +
      '<div>' + lbl('pr.name', t('pr.name')) + '<input data-f="name" value="' + esc(printer.name) + '" title="' + esc(help('pr.name')) + '">' +
      lbl('pr.bind', t('pr.bind')) + '<input data-f="bind" value="' + esc(printer.bind) + '" title="' + esc(help('pr.bind')) + '">' +
      '<div class="fieldhelp">' + esc(help('pr.bind').split('\n\n')[1] || '') + '</div></div>' +
      '<div>' + lbl('pr.transport', t('pr.transport')) +
      '<select data-f="transport.type" title="' + esc(help('pr.transport')) + '">' +
      ['auto', 'usb', 'usblp', 'serial', 'network'].map((k) =>
        '<option value="' + k + '"' + (k === transportType ? ' selected' : '') + '>' +
        (k === 'auto' ? t('pr.auto') : k) + '</option>').join('') + '</select>' +
      lbl('pr.profile', t('pr.profile')) + '<select data-f="profile" title="' + esc(help('pr.profile')) + '">' +
      '<option value="auto">' + t('pr.auto') + '</option>' +
      STATE.profiles.map((p) => '<option value="' + esc(p.id) + '">' + esc(p.name) +
        (p.columns ? ' (' + p.columns + ')' : '') + '</option>').join('') + '</select>' +
      checkbox('pr.enabled', 'enabled', t('pr.enabled'), printer.enabled) +
      '</div></div>' +
      '<h3>' + t('pr.connSettings') + ' — ' + esc(transportType) + '</h3>' +
      transportFields(transportType, transport) +
      '<h3>' + t('pr.options') + '</h3>' + optionFields(options) +
      '<div class="btnbar">' +
      '<button class="act primary" onclick="savePrinter(\'' + esc(printer.id) + '\')">' + t('pr.save') + '</button>' +
      '<button class="act" onclick="redetect(\'' + esc(printer.id) + '\')">' + t('pr.redetect') + '</button>' +
      '<button class="act danger" onclick="deletePrinter(\'' + esc(printer.id) + '\')">' + t('pr.delete') + '</button>' +
      '</div></div>';
  });

  root.innerHTML = html;
  data.printers.forEach((printer) => {
    const card = root.querySelector('[data-printer="' + printer.id + '"]');
    if (!card) return;
    const select = card.querySelector('[data-f="profile"]');
    select.value = STATE.configProfiles[printer.id] || 'auto';
    if (select.selectedIndex < 0) select.value = 'auto';
  });
}

function transportFields(type, settings) {
  const field = (key, label, value, placeholder) =>
    '<div>' + lbl('transport.' + key, label) + '<input data-f="transport.' + key + '" value="' +
    esc(value == null ? '' : value) + '" placeholder="' + esc(placeholder || '') +
    '" title="' + esc(help('transport.' + key)) + '"></div>';
  if (type === 'usb') {
    return '<div class="grid2">' + field('vendor_id', 'Vendor ID', settings.vendor_id, '0x04b8') +
      field('product_id', 'Product ID', settings.product_id, '0x0202') +
      field('serial', LANG === 'de' ? 'Seriennummer' : 'Serial number', settings.serial, '') + '</div>';
  }
  if (type === 'usblp') {
    return '<div class="grid2">' + field('device', LANG === 'de' ? 'Gerätedatei' : 'Device file', settings.device, '/dev/usb/lp0') + '</div>';
  }
  if (type === 'serial') {
    return '<div class="grid2">' + field('device', LANG === 'de' ? 'Gerätedatei' : 'Device file', settings.device, '/dev/ttyUSB0') +
      field('baudrate', LANG === 'de' ? 'Baudrate' : 'Baud rate', settings.baudrate, '38400') + '</div>';
  }
  if (type === 'network') {
    return '<div class="grid2">' + field('host', LANG === 'de' ? 'Adresse des Druckers' : 'Printer address', settings.host, '192.168.1.20') +
      field('port', 'Port', settings.port, '9100') + '</div>';
  }
  return '<p class="muted">' + (LANG === 'de'
    ? 'Der Anschluss wird bei jedem Start automatisch gesucht. Es gibt nichts einzustellen.'
    : 'The connection is detected automatically at every start. Nothing to configure.') + '</p>';
}

function optionFields(options) {
  return '<div class="grid2"><div>' +
    checkbox('op.startup', 'options.startup_report', t('op.startup'), options.startup_report !== false) +
    checkbox('op.paperlow', 'options.paper_low_warning', t('op.paperlow'), !!options.paper_low_warning) +
    checkbox('op.netalert', 'options.network_alert', t('op.netalert'), options.network_alert !== false) +
    checkbox('op.cut', 'options.cut_after_job', t('op.cut'), !!options.cut_after_job) +
    checkbox('op.drawer', 'options.open_drawer_after_job', t('op.drawer'), !!options.open_drawer_after_job) +
    checkbox('op.reset', 'options.reset_before_job', t('op.reset'), !!options.reset_before_job) +
    '</div><div>' +
    checkbox('op.polling', 'options.status_polling', t('op.polling'), options.status_polling !== false) +
    lbl('op.interval', t('op.interval')) + '<input data-f="options.status_interval" title="' + esc(help('op.interval')) +
    '" value="' + esc(options.status_interval == null ? 10 : options.status_interval) + '">' +
    lbl('op.feed', t('op.feed')) + '<input data-f="options.feed_lines_after_job" title="' + esc(help('op.feed')) +
    '" value="' + esc(options.feed_lines_after_job == null ? 0 : options.feed_lines_after_job) + '">' +
    '</div></div>';
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
    await api('/api/printers/' + encodeURIComponent(printerId),
      { method: 'PATCH', body: JSON.stringify(collectPatch(card)) });
    toast(t('common.saved'));
    await reload(true);
  } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
async function deletePrinter(printerId) {
  if (!confirm(t('pr.confirmDelete'))) return;
  try { await api('/api/printers/' + encodeURIComponent(printerId), { method: 'DELETE' }); await reload(true); }
  catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
async function addPrinter() {
  const count = (STATE.overview.printers || []).length + 1;
  try {
    await api('/api/printers', { method: 'POST', body: JSON.stringify({
      id: 'printer' + count, name: (LANG === 'de' ? 'Drucker ' : 'Printer ') + count, transport: { type: 'auto' } }) });
    await reload(true);
  } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
async function scanDevices() {
  try { STATE.devices = (await api('/api/scan')).devices; STATE.scanned = true; renderPrinters(); }
  catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
async function useDevice(index) {
  const device = STATE.devices[index];
  if (!(STATE.overview.printers || []).length) { await addPrinter(); }
  const target = (STATE.overview.printers[0] || {}).id;
  const transport = { type: device.transport };
  if (device.vendor_id != null) { transport.vendor_id = '0x' + device.vendor_id_hex; transport.product_id = '0x' + device.product_id_hex; }
  if (device.serial) transport.serial = device.serial;
  if (device.device) transport.device = device.device;
  if (device.baudrate) transport.baudrate = device.baudrate;
  try {
    await api('/api/printers/' + encodeURIComponent(target), { method: 'PATCH', body: JSON.stringify({ transport: transport }) });
    await reload(true); toast(t('common.saved'));
  } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
async function redetect(printerId) {
  try { await api('/api/printers/' + encodeURIComponent(printerId) + '/redetect', { method: 'POST' }); await reload(true); }
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
    const drawer = printer.drawer || {};
    html += '<div class="card" data-features="' + esc(printer.id) + '"><h2>' + esc(printer.name) +
      ' <span class="tag">' + esc(caps.profile_name || '') + '</span></h2>';
    html += '<p class="muted" style="margin-top:0">' + esc((printer.identity || {}).profile_reason || '') + '</p>';

    Object.keys(features).forEach((key) => {
      const entry = features[key];
      const label = bi(entry, 'label');
      let extra = '';
      if (key === 'cashdrawer' && drawer.state) {
        extra = '<div class="muted" style="font-size:.8rem;margin-top:.2rem" title="' + esc(bi(drawer, 'explain')) + '">' +
          t('fe.drawerState') + ': <b>' + esc(bi(drawer, 'label')) + '</b> · ' +
          '<span class="why">' + (LANG === 'de' ? 'warum unsicher?' : 'why uncertain?') + '</span></div>';
      }
      html += '<div class="switch"><span class="name">' + esc(label) +
        ' <span class="tag">' + t('fe.detected') + ': ' + (entry.detected ? t('common.yes') : t('common.no')) + '</span>' +
        '<span class="tag">' + t('fe.effective') + ': ' + (entry.effective ? t('common.yes') : t('common.no')) + '</span>' +
        extra + '</span>' +
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
      '<p class="muted" style="font-size:.8rem">' + esc(bi(rec, 'note')) + '</p>';
    html += '<div class="btnbar">' +
      '<button class="act primary" onclick="saveFeatures(\'' + esc(printer.id) + '\')">' + t('pr.save') + '</button>' +
      '<button class="act" onclick="testPrint(\'' + esc(printer.id) + '\',\'features\')">' + t('fe.testFeatures') + '</button>' +
      '</div>';
    html += '<h3>' + t('fe.probes') + '</h3><div class="btnbar">' +
      probeButton(printer.id, 'cut', t('fe.probeCut')) +
      probeButton(printer.id, 'drawer', t('fe.probeDrawer')) +
      '<button class="act" onclick="checkDrawer(\'' + esc(printer.id) + '\')" title="' +
      esc(bi(drawer, 'explain')) + '">' + t('fe.drawerCheck') + '</button>' +
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
  try {
    await api('/api/printers/' + encodeURIComponent(printerId) + '/probe',
      { method: 'POST', body: JSON.stringify({ what: what }) });
    toast(t('common.queued'));
  } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
async function checkDrawer(printerId) {
  toast(t('fe.drawerRunning'));
  try {
    const result = await api('/api/printers/' + encodeURIComponent(printerId) + '/drawer-check', { method: 'POST' });
    await reload(true);
    toast(t('fe.drawerState') + ': ' + bi(result.drawer || {}, 'label'));
  } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
async function saveFeatures(printerId) {
  const card = document.querySelector('[data-features="' + printerId + '"]');
  const features = {};
  card.querySelectorAll('[data-feature]').forEach((select) => {
    const value = select.value;
    features[select.getAttribute('data-feature')] = value === 'auto' ? null : (value === 'on');
  });
  try {
    await api('/api/printers/' + encodeURIComponent(printerId),
      { method: 'PATCH', body: JSON.stringify({ features: features }) });
    toast(t('common.saved')); await reload(true);
  } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
window.probe = probe; window.saveFeatures = saveFeatures; window.checkDrawer = checkDrawer;

/* ------------------------------------------------------------------ */
/* Print a receipt                                                     */
/* ------------------------------------------------------------------ */

const EXAMPLE_DE = 'Tisch 7 | 19:42\n---\n2x Cola 0,4l | 7,00\n1x Pommes | 3,50\n1x Currywurst | 4,90\n---\nSumme | 15,40\nMwSt 19% | 2,46\n\nZahlung: EC-Karte';
const EXAMPLE_EN = 'Table 7 | 19:42\n---\n2x Cola 0.4l | 7.00\n1x Fries | 3.50\n1x Sausage | 4.90\n---\nTotal | 15.40\nVAT 19% | 2.46\n\nPayment: card';

function renderPrint() {
  const root = $('#print');
  const data = STATE.overview;
  if (!data) { root.innerHTML = '<div class="card">' + t('common.loading') + '</div>'; return; }
  if (!data.printers.length) { root.innerHTML = '<div class="card">' + t('ov.noPrinters') + '</div>'; return; }

  const printers = data.printers;
  const selected = STATE.printTarget && printers.some((p) => p.id === STATE.printTarget)
    ? STATE.printTarget : printers[0].id;
  STATE.printTarget = selected;

  const mode = STATE.printMode === 'image' ? 'image' : 'text';
  const printerSelect = lbl('pt.printer', t('pt.printer')) +
    '<select id="ptPrinter">' + printers.map((p) =>
      '<option value="' + esc(p.id) + '"' + (p.id === selected ? ' selected' : '') + '>' +
      esc(p.name) + '</option>').join('') + '</select>';
  const modeSwitch = '<div class="modeswitch">' +
    '<button class="act' + (mode === 'text' ? ' primary' : '') + '" onclick="setPrintMode(\'text\')">' +
    t('pt.modeText') + '</button>' +
    '<button class="act' + (mode === 'image' ? ' primary' : '') + '" onclick="setPrintMode(\'image\')">' +
    t('pt.modeImage') + '</button></div>';

  if (mode === 'image') { renderPrintImage(root, printerSelect, modeSwitch); return; }

  root.innerHTML =
    '<div class="card"><h2>' + t('pt.title') + '</h2>' + modeSwitch +
    '<div class="row"><div>' +
    printerSelect +
    lbl('pt.heading', t('pt.heading')) + '<input id="ptTitle" title="' + esc(help('pt.heading')) + '">' +
    lbl('pt.body', t('pt.body')) + '<textarea id="ptBody" title="' + esc(help('pt.body')) + '"></textarea>' +
    '<div class="fieldhelp">' + esc(t('pt.bodyHelp')) + '</div>' +
    lbl('pt.footer', t('pt.footer')) + '<input id="ptFooter" title="' + esc(help('pt.footer')) + '">' +
    lbl('pt.qr', t('pt.qr')) + '<input id="ptQr" title="' + esc(help('pt.qr')) + '">' +
    checkbox('pt.cut', 'ptCut', t('pt.cut'), true).replace('data-f="ptCut"', 'id="ptCut"') +
    checkbox('pt.drawer', 'ptDrawer', t('pt.drawer'), false).replace('data-f="ptDrawer"', 'id="ptDrawer"') +
    '<div class="btnbar">' +
    '<button class="act primary" onclick="doPrint()">' + t('pt.print') + '</button>' +
    '<button class="act" onclick="updatePreview()">' + t('pt.preview') + '</button>' +
    '<button class="act" onclick="insertExample()">' + t('pt.example') + '</button>' +
    '<button class="act" onclick="clearReceipt()">' + t('pt.clear') + '</button>' +
    '</div></div>' +
    '<div><label>' + t('pt.preview') + ' <span id="ptWidth" class="tag"></span></label>' +
    '<div class="papershell"><div class="paper" id="ptPaper"></div></div>' +
    '<div class="fieldhelp">' + esc(t('pt.previewHint')) + '</div>' +
    '<div id="ptNotes" class="fieldhelp"></div>' +
    '</div></div></div>';

  ['ptTitle', 'ptBody', 'ptFooter', 'ptQr'].forEach((id) => {
    document.getElementById(id).addEventListener('input', schedulePreview);
  });
  ['ptCut', 'ptDrawer', 'ptPrinter'].forEach((id) => {
    document.getElementById(id).addEventListener('change', () => {
      if (id === 'ptPrinter') STATE.printTarget = document.getElementById('ptPrinter').value;
      updatePreview();
    });
  });
  if (STATE.receipt) {
    document.getElementById('ptTitle').value = STATE.receipt.title || '';
    document.getElementById('ptBody').value = STATE.receipt.body || '';
    document.getElementById('ptFooter').value = STATE.receipt.footer || '';
    document.getElementById('ptQr').value = STATE.receipt.qr || '';
  }
  updatePreview();
}

function receiptSpec() {
  const title = document.getElementById('ptTitle').value;
  const body = document.getElementById('ptBody').value;
  const footer = document.getElementById('ptFooter').value;
  const qr = document.getElementById('ptQr').value;
  STATE.receipt = { title: title, body: body, footer: footer, qr: qr };

  const elements = [];
  if (title) {
    elements.push({ type: 'text', text: title, align: 'center', bold: true, size: 'double' });
    elements.push({ type: 'divider' });
  }
  body.split('\n').forEach((raw) => {
    const line = raw.replace(/\s+$/, '');
    const trimmed = line.trim();
    if (trimmed === '---' || trimmed === '***') elements.push({ type: 'divider' });
    else if (trimmed === '===') elements.push({ type: 'divider', char: '=' });
    else if (line.indexOf('|') !== -1) {
      const parts = line.split('|');
      elements.push({ type: 'kv', left: parts[0].trim(), right: parts.slice(1).join('|').trim() });
    } else elements.push({ type: 'text', text: line });
  });
  if (footer) { elements.push({ type: 'divider' }); elements.push({ type: 'text', text: footer, align: 'center' }); }
  if (qr) elements.push({ type: 'qr', data: qr });

  return {
    elements: elements,
    cut: document.getElementById('ptCut').checked,
    open_drawer: document.getElementById('ptDrawer').checked,
    feed: 1
  };
}

function schedulePreview() {
  clearTimeout(PREVIEW_TIMER);
  PREVIEW_TIMER = setTimeout(updatePreview, 350);
}

async function updatePreview() {
  const printerId = STATE.printTarget;
  if (!printerId || !document.getElementById('ptBody')) return;
  try {
    const result = await api('/api/printers/' + encodeURIComponent(printerId) + '/compose',
      { method: 'POST', body: JSON.stringify({ spec: receiptSpec(), print: false }) });
    renderPaper(result);
  } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}

function renderPaper(result) {
  const paper = document.getElementById('ptPaper');
  if (!paper) return;
  const columns = result.columns || 42;
  document.getElementById('ptWidth').textContent = t('pt.width') + ': ' + columns;
  paper.style.width = (columns + 2) + 'ch';
  let html = '';
  (result.preview || []).forEach((line) => {
    const classes = ['pl'];
    if (line.bold) classes.push('b');
    if (line.double) classes.push('dbl');
    if (line.align === 'center') classes.push('c');
    if (line.align === 'right') classes.push('r');
    let text = esc(line.text);
    /* markers whose wording belongs to the interface, not to the printer */
    if (line.kind === 'cut') { classes.push('cutmark'); text = '- - - - - ' + t('pv.cut') + ' - - - - -'; }
    else if (line.kind === 'drawer') { classes.push('cutmark'); text = '[ ' + t('pv.drawer') + ' ]'; }
    else if (line.kind === 'qr') text = '[ ' + t('pv.qr') + ': ' + text + ' ]';
    else if (line.kind === 'barcode') text = '[ ' + t('pv.barcode') + ': ' + text + ' ]';
    html += '<span class="' + classes.join(' ') + '">' + (text || '&nbsp;') + '</span>';
  });
  paper.innerHTML = html || '&nbsp;';

  const noteMap = {
    cutter_unsupported: t('pt.noteCutter'), drawer_unsupported: t('pt.noteDrawer'),
    qr_unsupported: t('pt.noteQr'), barcode_unsupported: t('pt.noteBarcode')
  };
  const notes = Array.from(new Set(result.notes || [])).map((n) => noteMap[n] || n);
  document.getElementById('ptNotes').innerHTML = notes.map((n) => '⚠ ' + esc(n)).join('<br>');
}

async function doPrint() {
  const printerId = STATE.printTarget;
  try {
    const result = await api('/api/printers/' + encodeURIComponent(printerId) + '/compose',
      { method: 'POST', body: JSON.stringify({ spec: receiptSpec(), print: true }) });
    renderPaper(result);
    toast(t('pt.printed'));
  } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
function insertExample() {
  document.getElementById('ptTitle').value = LANG === 'de' ? 'Beispielbon' : 'Sample receipt';
  document.getElementById('ptBody').value = LANG === 'de' ? EXAMPLE_DE : EXAMPLE_EN;
  document.getElementById('ptFooter').value = LANG === 'de' ? 'Vielen Dank für Ihren Besuch' : 'Thank you for your visit';
  updatePreview();
}
function clearReceipt() {
  ['ptTitle', 'ptBody', 'ptFooter', 'ptQr'].forEach((id) => { document.getElementById(id).value = ''; });
  updatePreview();
}
window.doPrint = doPrint; window.updatePreview = updatePreview;
window.insertExample = insertExample; window.clearReceipt = clearReceipt;

/* ------------------------------------------------------------------ */
/* Printing an image                                                   */
/*                                                                     */
/* The preview is not a simulation: the device rasterises the file and */
/* sends back exactly the bitmap it would print, so a logo that turns  */
/* into a black block is visible before it costs paper.                */
/* ------------------------------------------------------------------ */

function setPrintMode(mode) {
  STATE.printMode = mode;
  renderPrint();
}

function renderPrintImage(root, printerSelect, modeSwitch) {
  const options = STATE.imageOptions || (STATE.imageOptions = {
    scale: 100, dither: true, threshold: 128, invert: false, cut: true, align: 'center'
  });
  const support = STATE.imageSupport;

  let html = '<div class="card"><h2>' + t('pt.title') + '</h2>' + modeSwitch;
  if (support && !support.available) {
    html += '<p class="fieldhelp" style="color:var(--warn)">⚠ ' +
      esc(LANG === 'de' ? support.hint_de : support.hint_en) + '</p>';
  }
  html += '<div class="row"><div>' + printerSelect +
    lbl('pt.file', t('pt.file')) +
    '<input type="file" id="ptFile" accept="image/*">' +
    '<div class="fieldhelp">' + esc(t('pt.fileHelp')) + '</div>' +
    '<div class="grid2" style="margin-top:.6rem">' +
    '<div>' + lbl('pt.scale', t('pt.scale')) +
    '<input type="number" id="ptScale" min="10" max="100" step="5" value="' + options.scale +
    '" title="' + esc(help('pt.scale')) + '"></div>' +
    '<div>' + lbl('pt.threshold', t('pt.threshold')) +
    '<input type="number" id="ptThreshold" min="1" max="254" step="4" value="' + options.threshold +
    '" title="' + esc(help('pt.threshold')) + '"' + (options.dither ? ' disabled' : '') + '></div>' +
    '</div>' +
    checkbox('pt.dither', 'ptDither', t('pt.dither'), options.dither).replace('data-f="ptDither"', 'id="ptDither"') +
    checkbox('pt.invert', 'ptInvert', t('pt.invert'), options.invert).replace('data-f="ptInvert"', 'id="ptInvert"') +
    checkbox('pt.cut', 'ptImgCut', t('pt.cut'), options.cut).replace('data-f="ptImgCut"', 'id="ptImgCut"') +
    '<div class="btnbar">' +
    '<button class="act primary" onclick="doPrintImage()" id="ptImgPrint">' + t('pt.print') + '</button>' +
    '<button class="act" onclick="prepareImage()">' + t('pt.preview') + '</button>' +
    '<button class="act" onclick="clearImage()">' + t('pt.clear') + '</button>' +
    '</div></div>' +
    '<div><label>' + t('pt.preview') + ' <span id="ptImgInfo" class="tag"></span></label>' +
    '<div class="papershell"><div class="paper imagepaper" id="ptImgPaper">' +
    '<span class="muted">' + esc(t('pt.noImage')) + '</span></div></div>' +
    '<div id="ptImgNotes" class="fieldhelp"></div>' +
    '</div></div></div>';
  root.innerHTML = html;

  document.getElementById('ptPrinter').addEventListener('change', (event) => {
    STATE.printTarget = event.target.value;
    if (STATE.imageFile) prepareImage();
  });
  document.getElementById('ptFile').addEventListener('change', (event) => {
    STATE.imageFile = event.target.files && event.target.files[0];
    STATE.imageToken = null;
    if (STATE.imageFile) prepareImage();
  });
  ['ptScale', 'ptThreshold'].forEach((id) => {
    document.getElementById(id).addEventListener('change', collectImageOptions);
  });
  ['ptDither', 'ptInvert', 'ptImgCut'].forEach((id) => {
    document.getElementById(id).addEventListener('change', collectImageOptions);
  });

  if (STATE.imagePreview) showImagePreview(STATE.imagePreview);
  if (!support) loadImageSupport();
}

async function loadImageSupport() {
  try {
    STATE.imageSupport = (await api('/api/image/support')).support;
    if (STATE.printMode === 'image') renderPrint();
  } catch (e) { /* the tab still works, only the hint is missing */ }
}

function collectImageOptions() {
  const number = (id, fallback) => {
    const value = parseInt(document.getElementById(id).value, 10);
    return isNaN(value) ? fallback : value;
  };
  STATE.imageOptions = {
    scale: Math.max(10, Math.min(100, number('ptScale', 100))),
    threshold: Math.max(1, Math.min(254, number('ptThreshold', 128))),
    dither: document.getElementById('ptDither').checked,
    invert: document.getElementById('ptInvert').checked,
    cut: document.getElementById('ptImgCut').checked,
    align: 'center'
  };
  document.getElementById('ptThreshold').disabled = STATE.imageOptions.dither;
  if (STATE.imageFile) prepareImage();
}

async function prepareImage() {
  if (!STATE.imageFile) { toast(t('pt.noImage')); return; }
  const options = STATE.imageOptions || {};
  const query = '?scale=' + (options.scale || 100) +
    '&threshold=' + (options.threshold || 128) +
    '&dither=' + (options.dither === false ? '0' : '1') +
    '&invert=' + (options.invert ? '1' : '0') +
    '&cut=' + (options.cut === false ? '0' : '1');
  const paper = document.getElementById('ptImgPaper');
  if (paper) paper.innerHTML = '<span class="muted">' + esc(t('common.loading')) + '</span>';
  try {
    const response = await fetch(
      '/api/printers/' + encodeURIComponent(STATE.printTarget) + '/image' + query,
      { method: 'POST', body: STATE.imageFile,
        headers: { 'Content-Type': 'application/octet-stream' } });
    const result = await response.json();
    if (!response.ok || result.ok === false) throw new Error(result.error || ('HTTP ' + response.status));
    STATE.imageToken = result.token;
    STATE.imagePreview = result;
    showImagePreview(result);
  } catch (e) {
    STATE.imageToken = null;
    if (paper) paper.innerHTML = '<span style="color:var(--err)">' + esc(e.message) + '</span>';
    toast(t('common.error') + ': ' + e.message, true);
  }
}

function showImagePreview(result) {
  const paper = document.getElementById('ptImgPaper');
  if (!paper) return;
  paper.innerHTML = '<img src="' + result.preview_png + '" alt="preview">' +
    (result.cutmark === false ? '' : '<span class="pl cutmark">- - - - - ' + t('pv.cut') + ' - - - - -</span>');
  const info = document.getElementById('ptImgInfo');
  if (info) {
    info.textContent = result.width + ' × ' + result.height + ' ' + t('pt.dots') +
      ' · ' + fmtBytes(result.bytes) + (result.format ? ' · ' + result.format.toUpperCase() : '');
  }
  const noteMap = {
    cutter_unsupported: t('pt.noteCutter'),
    transparency_flattened: t('pt.noteTransparent'),
    truncated: t('pt.noteTruncated')
  };
  const notes = (result.notes || []).map((n) => noteMap[n] || n);
  const box = document.getElementById('ptImgNotes');
  if (box) box.innerHTML = notes.map((n) => '⚠ ' + esc(n)).join('<br>');
}

async function doPrintImage() {
  if (!STATE.imageToken) { await prepareImage(); }
  if (!STATE.imageToken) return;
  try {
    await api('/api/printers/' + encodeURIComponent(STATE.printTarget) + '/image/print',
      { method: 'POST', body: JSON.stringify({ token: STATE.imageToken }) });
    toast(t('pt.printed'));
  } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}

function clearImage() {
  STATE.imageFile = null; STATE.imageToken = null; STATE.imagePreview = null;
  renderPrint();
}

window.setPrintMode = setPrintMode; window.prepareImage = prepareImage;
window.doPrintImage = doPrintImage; window.clearImage = clearImage;

/* ------------------------------------------------------------------ */
/* Diagnostics                                                         */
/* ------------------------------------------------------------------ */

async function renderDiag() {
  const root = $('#diag');
  root.innerHTML = '<div class="card">' + t('common.loading') + '</div>';
  let diag, discovery;
  try {
    diag = await api('/api/diagnostics');
    discovery = (await api('/api/discovery')).discovery;
    STATE.discoveryConfig = (await api('/api/config')).config.discovery || {};
  } catch (e) { root.innerHTML = '<div class="card">' + t('common.error') + ': ' + esc(e.message) + '</div>'; return; }

  let html = '<div class="card"><h2>' + t('di.title') + '</h2><div class="btnbar">' +
    '<button class="act primary" onclick="downloadReport()">' + t('di.report') + '</button>' +
    '<button class="act" onclick="renderDiag()">' + t('di.reload') + '</button></div></div>';

  const health = (STATE.overview || {}).health || {};
  html += '<div class="card"><h2>' + t('di.health') + '</h2>' +
    checksBlock(health.device, LANG === 'de' ? 'Gerät' : 'Device', 'diag.device');
  Object.keys(health.printers || {}).forEach((printerId) => {
    html += checksBlock(health.printers[printerId], printerId, 'diag.printer:' + printerId);
  });
  html += '</div>';

  /* discovery: every protocol side by side, plus what actually arrived */
  const adv = discovery.advertised || {};
  const protocols = discovery.protocols || [];
  const answering = protocols.filter((p) => p.enabled && p.listening && p.answers).length;

  html += '<div class="card"><h2>' + t('di.discovery') + '</h2>' +
    '<p class="fieldhelp">' + esc(t('di.discoveryIntro')) + '</p>' +
    '<div class="big">' +
    (discovery.total_requests
      ? '<span class="dot ok"></span>' + t('di.probesSeen').replace('%s', discovery.total_requests)
      : '<span class="dot unknown"></span>' + t('di.noProbesYet')) +
    '</div>' +
    '<p class="fieldhelp">' + esc(t('di.testHint')) + '</p>';

  html += '<table><tr><th>' + t('di.protocol') + '</th><th>' + t('di.transport') +
    '</th><th>' + t('di.state') + '</th><th>' + t('di.received') + '</th></tr>';
  protocols.forEach((entry) => {
    let state;
    if (!entry.enabled) state = '<span class="muted">' + t('di.off') + '</span>';
    else if (!entry.listening) state = '<span class="dot error"></span>' + t('di.blocked');
    else if (entry.answers) state = '<span class="dot ok"></span>' + t('di.answering');
    else state = '<span class="dot warn"></span>' + t('di.watching');
    html += '<tr><td><b>' + esc(entry.label) + '</b><br><span class="muted">' +
      esc(LANG === 'de' ? entry.purpose_de : entry.purpose_en) + '</span></td><td><code>' +
      esc(entry.transport) + '</code></td><td>' + state + '</td><td>' +
      entry.requests + (entry.answers && entry.replies ? ' / ' + entry.replies + ' ' + t('di.answered') : '') +
      '</td></tr>';
  });
  html += '</table>';
  html += '<p class="fieldhelp">' + esc(t('di.answeringHint').replace('%s', answering)) + '</p>';

  /* what we call ourselves - this is what an Epson filter matches on */
  html += '<h3>' + t('di.identity') + '</h3>' +
    '<p class="fieldhelp">' + esc(t('di.identityHelp')) + '</p>' +
    '<div class="grid2"><div>' +
    lbl('di.advVendor', t('di.advVendor')) +
    '<input id="dsVendor" title="' + esc(help('di.advVendor')) + '" value="' + esc(adv.vendor || '') + '">' +
    lbl('di.advModel', t('di.advModel')) +
    '<input id="dsModel" title="' + esc(help('di.advModel')) + '" value="' +
    esc((STATE.discoveryConfig && STATE.discoveryConfig.advertise_model) || 'auto') + '">' +
    '<div class="fieldhelp">' +
    esc(t('di.advNow')) + ': <b>' + esc(adv.vendor || '') + ' ' + esc(adv.model || '') + '</b> (' +
    esc(t('di.advSource.' + (adv.source || 'fallback'))) + ')</div>' +
    '</div><div>' +
    lbl('di.enpcReply', t('di.enpcReply')) +
    '<select id="dsEnpcReply" title="' + esc(help('di.enpcReply')) + '">' +
    '<option value="cycle"' + (discovery.enpc_reply === 'cycle' ? ' selected' : '') + '>' +
    t('di.enpcReply.cycle') + '</option>' +
    '<option value="all"' + (discovery.enpc_reply === 'all' ? ' selected' : '') + '>' +
    t('di.enpcReply.all') + '</option>' +
    (discovery.enpc_candidates || []).map((c, i) =>
      '<option value="' + esc(c.id) + '"' + (discovery.enpc_reply === c.id ? ' selected' : '') + '>' +
      (i + 1) + '. ' + esc(c.id) + '</option>').join('') + '</select>' +
    '<div class="fieldhelp">' + esc(t('di.enpcReplyHelp')) +
    (discovery.enpc_last_candidate
      ? ' ' + t('di.lastCandidate') + ': <b>' + esc(discovery.enpc_last_candidate) + '</b>'
      : '') +
    ((discovery.enpc || {}).pinned_replies === false
      ? '<br>⚠ ' + esc(t('di.notPinned'))
      : '') + '</div>' +
    foldable('di.candidates', t('di.candidateList'),
      '<table><tr><th>#</th><th>' + t('di.candidate') + '</th><th></th></tr>' +
      (discovery.enpc_candidates || []).map((c, i) =>
        '<tr><td>' + (i + 1) + '</td><td><code>' + esc(c.id) + '</code></td><td class="muted">' +
        esc(LANG === 'de' ? c.note_de : c.note_en) + '</td></tr>').join('') +
      '</table>', false) +
    checkbox('di.snmpOn', 'dsSnmp', t('di.snmpOn'), !STATE.discoveryConfig || STATE.discoveryConfig.snmp !== false)
      .replace('data-f="dsSnmp"', 'id="dsSnmp"') +
    checkbox('di.lpdOn', 'dsLpd', t('di.lpdOn'), !STATE.discoveryConfig || STATE.discoveryConfig.lpd !== false)
      .replace('data-f="dsLpd"', 'id="dsLpd"') +
    checkbox('di.watchOn', 'dsWatch', t('di.watchOn'), !STATE.discoveryConfig || STATE.discoveryConfig.watch_ports !== false)
      .replace('data-f="dsWatch"', 'id="dsWatch"') +
    '</div></div>' +
    '<div class="btnbar"><button class="act primary" onclick="saveDiscovery()">' + t('sy.save') + '</button>' +
    '<button class="act" onclick="renderDiag()">' + t('di.reload') + '</button></div>' +
    '<div class="fieldhelp">' + t('di.saveHint') + '</div>';

  /* the log itself */
  html += '<h3>' + t('di.probes') + '</h3>';
  const probes = discovery.probes || [];
  if (!probes.length) {
    html += '<p class="muted">' + t('di.noProbes') + '</p>';
  } else {
    probes.forEach((probe, index) => {
      const head = '<code>' + esc(probe.protocol) + '</code> · ' + fmtTime(probe.time) + ' · ' +
        esc(probe.peer) +
        (probe.local ? ' → ' + esc(probe.local) : '') + ' · ' + probe.bytes + ' B · ' +
        (probe.answered ? t('di.answered') : t('di.notAnswered')) +
        (probe.summary ? ' · ' + esc(probe.summary) : '');
      let body = '<pre>' + esc(probe.hexdump || '(0 B)') + '</pre>';
      if (probe.reply_hexdump) {
        body += '<div class="muted" style="font-size:.8rem">' + t('di.reply') + '</div>' +
          '<pre>' + esc(probe.reply_hexdump) + '</pre>';
      }
      html += foldable('diag.probe:' + index + ':' + probe.protocol, head, body, index === 0);
    });
    html += '<div class="btnbar"><button class="act" onclick="clearProbes()">' +
      t('di.clearProbes') + '</button></div>';
  }
  html += '</div>';

  (STATE.overview ? STATE.overview.printers : []).forEach((printer) => {
    html += '<div class="card"><h2>' + esc(printer.name) + '</h2><h3>' + t('di.recentJobs') + '</h3>';
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
    html += '<h3>' + t('di.raw') + '</h3>' +
      '<div class="row" style="margin-top:.4rem"><input id="raw-' + esc(printer.id) +
      '" placeholder="1B 40 48 61 6C 6C 6F 0A 0A 0A" title="' + esc(help('di.raw')) + '">' +
      '<button class="act" style="flex:0 0 auto" onclick="sendRaw(\'' + esc(printer.id) + '\')">' + t('di.rawSend') + '</button></div>' +
      '<div class="btnbar"><button class="act" onclick="clearSpool(\'' + esc(printer.id) + '\')">' + t('di.clearSpool') +
      ' (' + printer.spooled + ')</button></div>' +
      foldable('diag.status:' + printer.id, 'Status',
               '<pre>' + esc(JSON.stringify(printer.status || {}, null, 1)) + '</pre>', false) +
      foldable('diag.identity:' + printer.id, 'Identity',
               '<pre>' + esc(JSON.stringify(printer.identity || {}, null, 1)) + '</pre>', false) + '</div>';
  });

  html += '<div class="card"><h2>' + t('di.commands') + '</h2>';
  Object.keys(diag.commands).forEach((key) => {
    html += foldable('diag.cmd:' + key, esc(key),
                     '<pre>' + esc(diag.commands[key]) + '</pre>', false);
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
  try {
    await api('/api/printers/' + encodeURIComponent(printerId) + '/raw', { method: 'POST', body: JSON.stringify(body) });
    toast(t('common.queued'));
  } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
async function clearSpool(printerId) {
  try { const r = await api('/api/printers/' + encodeURIComponent(printerId) + '/spool/clear', { method: 'POST' });
    toast('OK (' + r.removed + ')'); await reload(true); } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
async function saveDiscovery() {
  const patch = { discovery: {
    advertise_vendor: document.getElementById('dsVendor').value.trim() || 'EPSON',
    advertise_model: document.getElementById('dsModel').value.trim() || 'auto',
    enpc_reply: document.getElementById('dsEnpcReply').value,
    snmp: document.getElementById('dsSnmp').checked,
    lpd: document.getElementById('dsLpd').checked,
    watch_ports: document.getElementById('dsWatch').checked
  } };
  try {
    await api('/api/config', { method: 'PUT', body: JSON.stringify(patch) });
    toast(t('common.saved') + ' — ' + t('di.restartNeeded'));
    clearDirty('diag');
  } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
window.saveDiscovery = saveDiscovery;

async function clearProbes() {
  try { await api('/api/discovery/clear', { method: 'POST' }); renderDiag(); }
  catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
window.downloadReport = downloadReport; window.sendRaw = sendRaw; window.clearSpool = clearSpool;
window.renderDiag = renderDiag; window.clearProbes = clearProbes;

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
    const address = String(printer.pos_address);
    const alternatives = (rec.alternatives || []).map((a) => a.font + '=' + a.columns).join(', ');
    const steps = LANG === 'de' ? [
      'In OrderAssist das Hauptmenü (☰) öffnen und <b>Drucker</b> wählen.',
      '<b>+ Hinzufügen</b> antippen. Findet die automatische Suche nichts, den Drucker manuell eintragen.',
      'Als IP-Adresse <code class="copy" onclick="copyText(\'' + esc(address) + '\')">' + esc(address) + '</code> eintragen. Der Port ist fest 9100 und muss nicht angegeben werden.',
      'Unter <b>Drucker korrekt konfigurieren</b> die Werte aus der Tabelle oben eintragen.',
      'Testseite drucken. Prüfen: Zeilenbreite passt, Umlaute und € korrekt, Trennlinie bricht nicht um.',
      'Den Drucker in OrderAssist einer <b>Ausdruckgruppe</b> zuweisen (Küche, Theke …).'
    ] : [
      'Open the main menu (☰) in OrderAssist and choose <b>Drucker</b> (printers).',
      'Tap <b>+ Hinzufügen</b>. If the automatic search finds nothing, add the printer manually.',
      'Enter <code class="copy" onclick="copyText(\'' + esc(address) + '\')">' + esc(address) + '</code> as the IP address. The port is fixed at 9100.',
      'Enter the values from the table above in the printer configuration section.',
      'Print a test page and check line width, umlauts/€ and that the divider does not wrap.',
      'Assign the printer to a print group (kitchen, bar …).'
    ];

    html += '<div class="card"><h2>' + t('co.oa') + ' — ' + esc(printer.name) + '</h2><div class="kv">' +
      kv(t('co.ip'), '<code class="copy" onclick="copyText(\'' + esc(address) + '\')">' + esc(address) + '</code>') +
      kv(t('co.port'), '<code>' + esc(printer.pos_port) + '</code>') +
      kv(t('co.protocol'), 'RAW / ESC-POS (JetDirect)') +
      kv(t('co.font'), '<code>' + esc(rec.font || '-') + '</code> — ' + esc(rec.font_name || '')) +
      kv(t('co.charset'), '<code>' + esc(rec.codepage || '-') + '</code>') +
      kv(t('co.width'), '<code>' + esc(rec.columns || '-') + '</code>') +
      (alternatives ? kv(t('co.alt'), esc(alternatives)) : '') +
      '</div><p class="muted" style="font-size:.8rem">' + esc(bi(rec, 'note')) + '</p>' +
      '<h3>' + t('co.steps') + '</h3><ol>' + steps.map((s) => '<li>' + s + '</li>').join('') + '</ol>' +
      '<div class="btnbar"><button class="act primary" onclick="testPrint(\'' + esc(printer.id) + '\',\'standard\')">' +
      t('ov.testPrint') + '</button></div></div>';
  });

  const first = data.printers[0] || {};
  const port = first.pos_port || 9100;
  html += '<div class="card"><h2>' + t('co.generic') + '</h2><p>' + (LANG === 'de'
    ? 'BonBridge verhält sich wie ein gewöhnlicher Netzwerk-Bondrucker (RAW/JetDirect). Jedes Kassensystem, das einen Netzwerkdrucker per IP ansprechen kann, funktioniert:'
    : 'BonBridge behaves like an ordinary network receipt printer (RAW/JetDirect). Any POS system that can address a network printer by IP will work:') + '</p><table>' +
    '<tr><th>' + (LANG === 'de' ? 'Kassensystem / App' : 'POS system / app') + '</th><th>' +
    (LANG === 'de' ? 'Einstellung' : 'Setting') + '</th></tr>' +
    '<tr><td>OrderAssist</td><td>' + (LANG === 'de' ? 'IP eintragen, Port fest 9100' : 'enter the IP, port fixed at 9100') + '</td></tr>' +
    '<tr><td>' + (LANG === 'de' ? 'Allgemein RAW/Socket' : 'Generic RAW/socket') + '</td><td><code>socket://' + esc(first.pos_address || '') + ':' + esc(port) + '</code></td></tr>' +
    '<tr><td>CUPS / Linux</td><td><code>lpadmin -p Bon -E -v socket://' + esc(first.pos_address || '') + ':' + esc(port) + ' -m raw</code></td></tr>' +
    '<tr><td>Windows</td><td>' + (LANG === 'de' ? 'Drucker hinzufügen → TCP/IP-Port → RAW → Port ' : 'Add printer → TCP/IP port → RAW → port ') + esc(port) + '</td></tr>' +
    '<tr><td>' + (LANG === 'de' ? 'Test von der Kommandozeile' : 'Command line test') + '</td><td><code>printf "Test\\n\\n\\n" | nc ' + esc(first.pos_address || '') + ' ' + esc(port) + '</code></td></tr>' +
    '</table></div>';

  root.innerHTML = html || '<div class="card">' + t('ov.noPrinters') + '</div>';
}

/* ------------------------------------------------------------------ */
/* System                                                              */
/* ------------------------------------------------------------------ */

async function renderSystem() {
  const root = $('#system');
  let config;
  try { config = (await api('/api/config')).config; }
  catch (e) { root.innerHTML = '<div class="card">' + t('common.error') + ': ' + esc(e.message) + '</div>'; return; }
  const sys = STATE.overview ? STATE.overview.system : {};

  root.innerHTML = '<div class="card"><h2>' + t('sy.settings') + '</h2><div class="grid2">' +
    '<div>' + lbl('sy.label', t('sy.label')) + '<input id="cfgLabel" title="' + esc(help('sy.label')) + '" value="' + esc(config.hostname_label || '') + '">' +
    lbl('sy.webPort', t('sy.webPort')) + '<input id="cfgWebPort" title="' + esc(help('sy.webPort')) + '" value="' + esc(config.web.port) + '">' +
    lbl('sy.language', t('sy.language')) + '<select id="cfgLang" title="' + esc(help('sy.language')) + '"><option value="de">Deutsch</option><option value="en">English</option></select></div>' +
    '<div>' + lbl('sy.rawPort', t('sy.rawPort')) + '<input id="cfgRawPort" title="' + esc(help('sy.rawPort')) + '" value="' + esc(config.raw.port) + '">' +
    '<label style="display:flex;align-items:flex-start;gap:.5rem;margin-top:.8rem" title="' + esc(help('sy.mdns')) + '">' +
    '<input type="checkbox" style="width:auto;margin-top:.2rem" id="cfgMdns"' + (config.discovery.mdns ? ' checked' : '') + '> <span class="why">' + t('sy.mdns') + '</span></label>' +
    '<label style="display:flex;align-items:flex-start;gap:.5rem" title="' + esc(help('sy.enpc')) + '">' +
    '<input type="checkbox" style="width:auto;margin-top:.2rem" id="cfgEnpc"' + (config.discovery.enpc ? ' checked' : '') + '> <span class="why">' + t('sy.enpc') + '</span></label>' +
    '<label style="display:flex;align-items:flex-start;gap:.5rem" title="' + esc(help('sy.logProbes')) + '">' +
    '<input type="checkbox" style="width:auto;margin-top:.2rem" id="cfgLogProbes"' + (config.discovery.log_probes !== false ? ' checked' : '') + '> <span class="why">' + t('sy.logProbes') + '</span></label>' +
    '</div></div>' +
    '<div class="btnbar"><button class="act primary" onclick="saveConfig()">' + t('sy.save') + '</button>' +
    '<button class="act" onclick="restartServices()">' + t('sy.restart') + '</button></div>' +
    '<div class="fieldhelp">' + t('sy.restartHint') + '</div></div>' +

    '<div class="card"><h2>System</h2><div class="kv">' +
    kv('BonBridge', esc(STATE.overview ? STATE.overview.version : '')) +
    kv('Host', esc(sys.hostname || '')) + kv('Model', esc(sys.model || '')) +
    kv('OS', esc(sys.os || '')) + kv('Kernel', esc(sys.kernel || '')) +
    kv('Arch', esc(sys.architecture || '')) + kv('Python', esc(sys.python || '')) +
    kv('Uptime', fmtDuration(sys.uptime)) +
    kv(LANG === 'de' ? 'Speicher frei' : 'Disk free', sys.disk ? fmtBytes(sys.disk.free) : '-') +
    '</div></div>' +

    networkCard(config) + updateCard(config) +

    '<div class="card"><h2>' + t('sy.docs') + '</h2>' +
    '<p class="muted">' + (LANG === 'de'
      ? 'Die vollständige Dokumentation liegt auf dem Gerät und funktioniert ohne Internet.'
      : 'The full documentation is stored on the device and works without internet access.') + '</p>' +
    '<div class="btnbar"><a class="act primary" style="text-decoration:none" href="/docs?lang=' + LANG +
    '" target="_blank">' + t('sy.openDocs') + '</a></div></div>';

  document.getElementById('cfgLang').value = config.web.language || 'de';
  if (document.getElementById('updLog')) pollUpdate();
}

/* ---- network watchdog ------------------------------------------------- */

function networkCard(config) {
  const watch = config.network_watch || {};
  const live = (STATE.overview || {}).network || {};
  const printers = ((STATE.overview || {}).printers || []);
  const state = live.online == null
    ? '<span class="dot unknown"></span>' + t('nw.unknown')
    : (live.online
        ? '<span class="dot ok"></span>' + t('nw.online')
        : '<span class="dot error"></span>' + t('nw.offline'));
  const links = (live.interfaces || []).map((link) =>
    kv(esc(link.name) + (link.wireless ? ' (WLAN)' : ''),
       (link.addresses || []).length
         ? esc(link.addresses.join(', '))
         : '<span class="muted">' + (link.carrier ? t('nw.noAddress') : t('nw.noCarrier')) + '</span>')
  ).join('');

  return '<div class="card"><h2>' + t('nw.title') + '</h2>' +
    '<div class="big">' + state + '</div>' +
    '<p class="fieldhelp">' + esc(t('nw.explain')) + '</p>' +
    '<div class="kv">' + links + '</div>' +
    '<div class="grid2" style="margin-top:.8rem"><div>' +
    checkbox('nw.enabled', 'nwEnabled', t('nw.enabled'), watch.enabled !== false)
      .replace('data-f="nwEnabled"', 'id="nwEnabled"') +
    checkbox('nw.onLoss', 'nwLoss', t('nw.onLoss'), watch.print_on_loss !== false)
      .replace('data-f="nwLoss"', 'id="nwLoss"') +
    checkbox('nw.onRestore', 'nwRestore', t('nw.onRestore'), watch.print_on_restore !== false)
      .replace('data-f="nwRestore"', 'id="nwRestore"') +
    checkbox('nw.gateway', 'nwGateway', t('nw.gateway'), !!watch.gateway_check)
      .replace('data-f="nwGateway"', 'id="nwGateway"') +
    '</div><div>' +
    lbl('nw.interval', t('nw.interval')) +
    '<input type="number" id="nwInterval" min="10" max="3600" step="10" value="' +
    esc(watch.interval || 60) + '" title="' + esc(help('nw.interval')) + '">' +
    lbl('nw.confirmations', t('nw.confirmations')) +
    '<input type="number" id="nwConfirm" min="1" max="10" value="' +
    esc(watch.confirmations || 2) + '" title="' + esc(help('nw.confirmations')) + '">' +
    '<div class="fieldhelp">' + esc(t('nw.perPrinterHint')) + '</div>' +
    '</div></div>' +
    '<div class="btnbar">' +
    '<button class="act primary" onclick="saveNetworkWatch()">' + t('sy.save') + '</button>' +
    '<button class="act" onclick="checkNetworkNow()">' + t('nw.checkNow') + '</button>' +
    (printers.length
      ? '<button class="act" onclick="testNetworkSlip(\'' + esc(printers[0].id) + '\')">' +
        t('nw.testSlip') + '</button>'
      : '') +
    '</div></div>';
}

async function saveNetworkWatch() {
  const patch = { network_watch: {
    enabled: document.getElementById('nwEnabled').checked,
    print_on_loss: document.getElementById('nwLoss').checked,
    print_on_restore: document.getElementById('nwRestore').checked,
    gateway_check: document.getElementById('nwGateway').checked,
    interval: Number(document.getElementById('nwInterval').value) || 60,
    confirmations: Number(document.getElementById('nwConfirm').value) || 2
  } };
  try {
    await api('/api/config', { method: 'PUT', body: JSON.stringify(patch) });
    toast(t('common.saved') + ' — ' + t('sy.restartHint'));
    clearDirty('system');
  } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
async function checkNetworkNow() {
  try {
    const result = await api('/api/network/check', { method: 'POST' });
    await reload(true);
    toast(result.network && result.network.online ? t('nw.online') : t('nw.offline'));
  } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
async function testNetworkSlip(printerId) {
  try {
    await api('/api/printers/' + encodeURIComponent(printerId) + '/network-test',
      { method: 'POST', body: JSON.stringify({ online: false }) });
    toast(t('common.queued'));
  } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
window.saveNetworkWatch = saveNetworkWatch; window.checkNetworkNow = checkNetworkNow;
window.testNetworkSlip = testNetworkSlip;

/* ---- updates ---------------------------------------------------------- */

function updateCard(config) {
  const upd = (STATE.overview || {}).update || {};
  const settings = config.update || {};
  const status = upd.status || {};
  const available = upd.update_available;

  let head;
  if (available) {
    head = '<div class="big"><span class="dot warn"></span>' +
      t('up.available') + ': ' + esc(upd.latest) + '</div>';
  } else if (upd.check_error) {
    // A failed check is a normal state (offline device, GitHub rate limit) -
    // it belongs in a sentence, not in a headline.
    head = '<div class="big"><span class="dot unknown"></span>' + t('up.notChecked') + '</div>' +
      '<p class="fieldhelp">' + esc(upd.check_error) + '</p>';
  } else if (upd.latest) {
    head = '<div class="big"><span class="dot ok"></span>' + t('up.current') + '</div>';
  } else {
    head = '<div class="big"><span class="dot unknown"></span>' + t('up.notChecked') + '</div>';
  }

  let html = '<div class="card"><h2>' + t('up.title') + '</h2>' + head +
    '<div class="kv">' +
    kv(t('up.installed'), esc(upd.current || '')) +
    kv(t('up.latest'), esc(upd.latest || '-')) +
    kv(t('up.checkedAt'), upd.checked_at ? fmtTime(upd.checked_at) : t('ov.never')) +
    kv(t('up.repo'), '<a href="https://github.com/' + esc(upd.repository || '') +
       '" target="_blank" rel="noopener">' + esc(upd.repository || '') + '</a>') +
    '</div>';

  const notes = (upd.release || {}).notes;
  if (available && notes) {
    html += foldable('up.notes', t('up.notes'), '<pre>' + esc(notes) + '</pre>', true);
  }

  if (upd.allow_web === false) {
    html += '<p class="fieldhelp">🔒 ' + esc(t('up.webDisabled')) + '</p>';
  }

  html += '<div class="btnbar">' +
    '<button class="act" onclick="checkUpdate()">' + t('up.check') + '</button>' +
    (available && upd.allow_web !== false
      ? '<button class="act primary" onclick="installUpdate()">' + t('up.install') + '</button>'
      : '') +
    '</div>';

  html += '<h3>' + t('up.offline') + '</h3>' +
    '<p class="fieldhelp">' + esc(t('up.offlineHelp')) + '</p>' +
    '<input type="file" id="updFile" accept=".zip,.gz,.tgz,.tar"' +
    (upd.allow_web === false ? ' disabled' : '') + '>' +
    '<div class="btnbar"><button class="act" onclick="uploadUpdate()"' +
    (upd.allow_web === false ? ' disabled' : '') + '>' + t('up.upload') + '</button></div>';

  html += '<h3>' + t('up.console') + '</h3>' +
    '<pre id="updLog" class="console">' + esc(t('up.noOutput')) + '</pre>';
  if (status.phase) {
    html += '<div class="fieldhelp">' + t('up.phase') + ': ' + esc(status.phase) + '</div>';
  }

  html += checkbox('up.allowWeb', 'updAllowWeb', t('up.allowWeb'), settings.allow_web !== false)
    .replace('data-f="updAllowWeb"', 'id="updAllowWeb"') +
    checkbox('up.checkOnStart', 'updCheckStart', t('up.checkOnStart'), settings.check_on_start !== false)
      .replace('data-f="updCheckStart"', 'id="updCheckStart"') +
    '<div class="btnbar"><button class="act" onclick="saveUpdateSettings()">' + t('sy.save') + '</button></div>';

  const backups = upd.backups || [];
  if (backups.length) {
    html += foldable('up.backups', t('up.backups'),
      '<div class="kv">' + backups.map((b) =>
        kv(esc(b.file), fmtBytes(b.size) + ' · ' + fmtTime(b.time))).join('') + '</div>' +
      '<p class="fieldhelp">' + esc(t('up.backupHelp')) + '</p>', false);
  }
  return html + '</div>';
}

async function checkUpdate() {
  toast(t('up.checking'));
  try {
    const result = await api('/api/update/check', { method: 'POST' });
    await reload(true);
    const check = result.check || {};
    toast(check.update_available
      ? t('up.available') + ': ' + check.latest
      : (check.error || t('up.current')), !!check.error);
  } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}

async function installUpdate() {
  const upd = (STATE.overview || {}).update || {};
  if (!confirm(t('up.confirm').replace('%s', upd.latest || '?'))) return;
  try {
    await api('/api/update/install', { method: 'POST', body: JSON.stringify({ source: 'online' }) });
    toast(t('up.started'));
    UPDATE_WATCH = true;
    pollUpdate();
  } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}

async function uploadUpdate() {
  const input = document.getElementById('updFile');
  const file = input && input.files && input.files[0];
  if (!file) { toast(t('up.pickFile'), true); return; }
  try {
    const response = await fetch('/api/update/upload?name=' + encodeURIComponent(file.name),
      { method: 'POST', body: file, headers: { 'Content-Type': 'application/octet-stream' } });
    const result = await response.json();
    if (!response.ok || result.ok === false) throw new Error(result.error || ('HTTP ' + response.status));
    if (!confirm(t('up.confirmFile').replace('%s', result.version || '?'))) return;
    await api('/api/update/install',
      { method: 'POST', body: JSON.stringify({ source: 'file', file: result.file }) });
    toast(t('up.started'));
    UPDATE_WATCH = true;
    pollUpdate();
  } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}

async function saveUpdateSettings() {
  const patch = { update: {
    allow_web: document.getElementById('updAllowWeb').checked,
    check_on_start: document.getElementById('updCheckStart').checked
  } };
  try {
    await api('/api/config', { method: 'PUT', body: JSON.stringify(patch) });
    toast(t('common.saved'));
    clearDirty('system');
    await reload(true);
  } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}

let UPDATE_WATCH = false;
async function pollUpdate() {
  const box = document.getElementById('updLog');
  if (!box) return;
  try {
    const result = await api('/api/update/log?lines=400');
    if (result.log) {
      box.textContent = result.log;
      box.scrollTop = box.scrollHeight;
    }
    const status = result.status || {};
    if (UPDATE_WATCH && status.running === false) {
      UPDATE_WATCH = false;
      toast(status.ok ? t('up.done') : (t('up.failed') + ': ' + (status.error || '')), !status.ok);
      setTimeout(() => location.reload(), 2500);
    }
  } catch (e) {
    // During the restart the daemon is briefly gone - that is expected.
    if (UPDATE_WATCH) box.textContent += '\n' + t('up.restarting');
  }
  // While an update runs, watch it closely instead of on the 5 s tick.
  if (UPDATE_WATCH) setTimeout(pollUpdate, 2000);
}
window.checkUpdate = checkUpdate; window.installUpdate = installUpdate;
window.uploadUpdate = uploadUpdate; window.saveUpdateSettings = saveUpdateSettings;
window.pollUpdate = pollUpdate;

async function saveConfig() {
  const patch = {
    hostname_label: document.getElementById('cfgLabel').value,
    web: { port: Number(document.getElementById('cfgWebPort').value), language: document.getElementById('cfgLang').value },
    raw: { port: Number(document.getElementById('cfgRawPort').value) },
    discovery: {
      mdns: document.getElementById('cfgMdns').checked,
      enpc: document.getElementById('cfgEnpc').checked,
      log_probes: document.getElementById('cfgLogProbes').checked
    }
  };
  try { await api('/api/config', { method: 'PUT', body: JSON.stringify(patch) }); toast(t('common.saved')); }
  catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
async function restartServices() {
  try { await api('/api/restart', { method: 'POST' }); await reload(true); toast('OK'); }
  catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
window.saveConfig = saveConfig; window.restartServices = restartServices;

/* ------------------------------------------------------------------ */
/* Shell                                                               */
/* ------------------------------------------------------------------ */

function renderCurrent() {
  // A full re-render replaces the DOM, so nothing unsaved survives it anyway.
  clearDirty(CURRENT);
  if (CURRENT === 'overview') renderOverview();
  else if (CURRENT === 'printers') renderPrinters();
  else if (CURRENT === 'features') renderFeatures();
  else if (CURRENT === 'print') renderPrint();
  else if (CURRENT === 'diag') renderDiag();
  else if (CURRENT === 'connect') renderConnect();
  else if (CURRENT === 'system') renderSystem();
}

/** True while the user is typing in, or has unsaved changes on, the open tab.
 *
 * The automatic refresh replaces the whole tab, so re-rendering underneath
 * someone who is halfway through changing a dropdown would silently throw
 * their change away.  In that case the refresh is skipped until they save or
 * click elsewhere.
 */
function tabBusy() {
  const section = document.getElementById(CURRENT);
  if (!section) return false;
  const active = document.activeElement;
  if (active && section.contains(active) &&
      /^(INPUT|SELECT|TEXTAREA)$/.test(active.tagName)) return true;
  return section.getAttribute('data-dirty') === '1';
}
function markDirty(node) {
  const section = node && node.closest ? node.closest('main section') : null;
  if (section) section.setAttribute('data-dirty', '1');
}
function clearDirty(tab) {
  const section = document.getElementById(tab || CURRENT);
  if (section) section.removeAttribute('data-dirty');
}

async function reload(force) {
  try {
    STATE.overview = await api('/api/overview');
    const config = (await api('/api/config')).config;
    STATE.config = config;
    STATE.configOptions = {}; STATE.configProfiles = {};
    (config.printers || []).forEach((p) => {
      STATE.configOptions[p.id] = p.options || {};
      STATE.configProfiles[p.id] = p.profile || 'auto';
    });
    if (force || CURRENT === 'overview' || CURRENT === 'features' || CURRENT === 'connect') {
      if (CURRENT === 'print' && !force) return;
      if (!force && tabBusy()) return;
      renderCurrent();
    }
  } catch (e) {
    toast(t('common.error') + ': ' + e.message, true);
  }
}

function applyLanguage() {
  document.documentElement.lang = LANG;
  document.querySelectorAll('[data-i18n]').forEach((node) => { node.textContent = t(node.getAttribute('data-i18n')); });
  document.getElementById('lang').value = LANG;
  document.getElementById('docLink').href = '/docs?lang=' + LANG;
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
  // `toggle` does not bubble, so listen in the capture phase.  Without this
  // every collapsed panel reopened on the next automatic refresh.
  document.addEventListener('toggle', (event) => {
    const node = event.target;
    if (node && node.tagName === 'DETAILS' && node.hasAttribute('data-open-key')) {
      rememberOpen(node.getAttribute('data-open-key'), node.open);
    }
  }, true);
  // Anything the user changes marks its tab as unsaved, which pauses the
  // automatic refresh for that tab until it is saved.
  document.addEventListener('change', (event) => markDirty(event.target), true);
  document.addEventListener('input', (event) => markDirty(event.target), true);

  applyLanguage();
  reload(true);
  TIMER = setInterval(() => {
    if (CURRENT === 'overview' || CURRENT === 'features') reload(false);
    if (CURRENT === 'system') pollUpdate();
  }, 5000);
});
