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
    'di.raw': 'Sendet Bytes unverändert an den Drucker. Text wird als Text gesendet; reine Hex-Zeichen werden als Bytes interpretiert, z. B. "1B 40" für einen Reset. Nur benutzen, wenn du weißt was du tust.'
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
    'di.raw': 'Sends bytes to the printer unchanged. Text is sent as text; pure hex characters are interpreted as bytes, e.g. "1B 40" for a reset. Only use this if you know what you are doing.'
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

/** Collapsible list of health checks with title + explanation. */
function checksBlock(entry, label) {
  if (!entry || !(entry.checks || []).length) return '';
  const problems = entry.problems || [];
  const summary = problems.length
    ? problems.map((c) => esc(bi(c, 'title'))).join(' · ')
    : t('status.ok');
  let html = '<details class="checks"' + (problems.length ? ' open' : '') + '>';
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
    '</div>' + checksBlock(health.device) + '</div>';

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
      '</div></div>' + checksBlock(ph) +
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

  root.innerHTML =
    '<div class="card"><h2>' + t('pt.title') + '</h2>' +
    '<div class="row"><div>' +
    lbl('pt.printer', t('pt.printer')) +
    '<select id="ptPrinter">' + printers.map((p) =>
      '<option value="' + esc(p.id) + '"' + (p.id === selected ? ' selected' : '') + '>' +
      esc(p.name) + '</option>').join('') + '</select>' +
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
/* Diagnostics                                                         */
/* ------------------------------------------------------------------ */

async function renderDiag() {
  const root = $('#diag');
  root.innerHTML = '<div class="card">' + t('common.loading') + '</div>';
  let diag, discovery;
  try {
    diag = await api('/api/diagnostics');
    discovery = (await api('/api/discovery')).discovery;
  } catch (e) { root.innerHTML = '<div class="card">' + t('common.error') + ': ' + esc(e.message) + '</div>'; return; }

  let html = '<div class="card"><h2>' + t('di.title') + '</h2><div class="btnbar">' +
    '<button class="act primary" onclick="downloadReport()">' + t('di.report') + '</button>' +
    '<button class="act" onclick="renderDiag()">' + t('di.reload') + '</button></div></div>';

  const health = (STATE.overview || {}).health || {};
  html += '<div class="card"><h2>' + t('di.health') + '</h2>' +
    checksBlock(health.device, LANG === 'de' ? 'Gerät' : 'Device');
  Object.keys(health.printers || {}).forEach((printerId) => {
    html += checksBlock(health.printers[printerId], printerId);
  });
  html += '</div>';

  /* discovery */
  const enpc = discovery.enpc || {};
  html += '<div class="card"><h2>' + t('di.discovery') + '</h2><div class="kv">' +
    kv('mDNS', discovery.mdns ? (discovery.mdns_active ? 'aktiv (zeroconf)' : 'Avahi') : t('common.no')) +
    kv('ENPC (UDP 3289)', enpc.enabled ? (enpc.listening ? t('common.yes') : t('common.error')) : t('common.no')) +
    kv(t('di.received'), String(enpc.requests || 0)) +
    kv(t('di.answered'), String(enpc.replies || 0)) +
    '</div><p class="muted" style="font-size:.82rem">' + esc(bi(enpc, 'note')) + '</p>' +
    '<h3>' + t('di.probes') + '</h3>';
  if (!(enpc.probes || []).length) {
    html += '<p class="muted">' + t('di.noProbes') + '</p>';
  } else {
    enpc.probes.forEach((probe) => {
      html += '<div style="margin-bottom:.7rem"><div class="muted" style="font-size:.82rem">' +
        fmtTime(probe.time) + ' — ' + esc(probe.peer) + ' — ' + probe.bytes + ' B — ' +
        (probe.answered ? t('di.answered') : '—') + (probe.magic ? ' — ' + esc(probe.magic) : '') +
        (probe.function ? ' ' + esc(probe.function) : '') + '</div>' +
        '<pre>' + esc(probe.hexdump) + '</pre></div>';
    });
    html += '<div class="btnbar"><button class="act" onclick="clearProbes()">' + t('di.clearProbes') + '</button></div>';
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
      '<h3>Status</h3><pre>' + esc(JSON.stringify(printer.status || {}, null, 1)) + '</pre>' +
      '<h3>Identity</h3><pre>' + esc(JSON.stringify(printer.identity || {}, null, 1)) + '</pre></div>';
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
  try {
    await api('/api/printers/' + encodeURIComponent(printerId) + '/raw', { method: 'POST', body: JSON.stringify(body) });
    toast(t('common.queued'));
  } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
async function clearSpool(printerId) {
  try { const r = await api('/api/printers/' + encodeURIComponent(printerId) + '/spool/clear', { method: 'POST' });
    toast('OK (' + r.removed + ')'); await reload(true); } catch (e) { toast(t('common.error') + ': ' + e.message, true); }
}
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

    '<div class="card"><h2>' + t('sy.docs') + '</h2>' +
    '<p class="muted">' + (LANG === 'de'
      ? 'Die vollständige Dokumentation liegt auf dem Gerät und funktioniert ohne Internet.'
      : 'The full documentation is stored on the device and works without internet access.') + '</p>' +
    '<div class="btnbar"><a class="act primary" style="text-decoration:none" href="/docs?lang=' + LANG +
    '" target="_blank">' + t('sy.openDocs') + '</a></div></div>';

  document.getElementById('cfgLang').value = config.web.language || 'de';
}

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
  if (CURRENT === 'overview') renderOverview();
  else if (CURRENT === 'printers') renderPrinters();
  else if (CURRENT === 'features') renderFeatures();
  else if (CURRENT === 'print') renderPrint();
  else if (CURRENT === 'diag') renderDiag();
  else if (CURRENT === 'connect') renderConnect();
  else if (CURRENT === 'system') renderSystem();
}

async function reload(force) {
  try {
    STATE.overview = await api('/api/overview');
    const config = (await api('/api/config')).config;
    STATE.configOptions = {}; STATE.configProfiles = {};
    (config.printers || []).forEach((p) => {
      STATE.configOptions[p.id] = p.options || {};
      STATE.configProfiles[p.id] = p.profile || 'auto';
    });
    if (force || CURRENT === 'overview' || CURRENT === 'features' || CURRENT === 'connect') {
      if (!(CURRENT === 'print' && !force)) renderCurrent();
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
  applyLanguage();
  reload(true);
  TIMER = setInterval(() => {
    if (CURRENT === 'overview' || CURRENT === 'features') reload(false);
  }, 5000);
});
