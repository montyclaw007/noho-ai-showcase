#!/usr/bin/env python3
"""
nøho · AI-Showcase — Mehrsprachiger Immobilien-Anfragen-Bot (Live-Demo)

Kleiner lokaler Server: liefert index.html aus und proxyt /api/chat an Claude
(Modell: claude-opus-4-8) mit Structured Output, damit das Frontend gleichzeitig
die Antwort UND die qualifizierten Lead-Felder bekommt.

Start (Live-KI):
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...
    python3 server.py
    →  http://localhost:8000

Ohne Key / ohne Server läuft index.html im Demo-Modus (Datei doppelklicken).
"""
import json, os, http.server, socketserver
from pathlib import Path

MODEL = "claude-opus-4-8"
PORT  = int(os.environ.get("PORT", "8000"))
HERE  = Path(__file__).parent

SYSTEM = """Du bist „Marisol", die digitale Empfangs- und Vertriebsassistentin der
Luxus-Immobilienagentur **Mar y Sol Inmobiliaria** auf Mallorca (Sitz: Port d'Andratx).

Deine Aufgabe: eingehende Anfragen freundlich beantworten, Interesse wecken und den
Lead Schritt für Schritt qualifizieren — wie ein erstklassiger Concierge, nicht wie ein Formular.

SPRACHE:
- Antworte IMMER in der Sprache der letzten Nutzernachricht: Deutsch, English oder Español.
- Erkenne die Sprache selbst und spiegle sie. Wechselt der Kunde die Sprache, wechselst du mit.

STIL:
- Warm, gehoben, knapp. Maximal 2–3 Sätze pro Antwort. Kein Fließtext, keine Floskelflut.
- Stelle pro Antwort höchstens EINE Qualifizierungsfrage. Reihenfolge sinnvoll:
  Vorhaben (Kauf/Miete) → Lage/Region → Budget → Schlafzimmer → Zeitrahmen → Kontakt (E-Mail/Telefon).
- Frage nur nach noch Unbekanntem. Wenn der Kunde schon etwas genannt hat, bestätige es kurz und gehe weiter.
- Sobald Vorhaben, Lage und (Budget ODER Schlafzimmer) bekannt sind, bitte um Kontaktdaten,
  um passende Objekte zu senden.

OBJEKT-WISSEN (nur diese drei sind frei nennbar; alles weitere „auf Anfrage / Off-Market"):
- Villa Lluna — Santa Ponça, Meerblick, 4 SZ, Pool, 320 m², 3.450.000 € (Ref. MS-204)
- Finca Es Pinar — Pollença, 5 SZ, Olivenhain, 410 m², 14.000 m² Land, 2.190.000 € (Ref. MS-187)
- Ático Marina — Port d'Andratx, 3 SZ, Dachterrasse, 180 m², Liegeplatz optional, 2.850.000 € (Ref. MS-231)
Passt eine dieser Optionen grob zum Wunsch, darfst du sie konkret erwähnen. Erfinde keine weiteren Preise/Objekte.

WICHTIG — Lead-Erfassung:
- Fülle das `lead`-Objekt mit allem, was du bisher aus dem GESAMTEN Gespräch weißt.
- Unbekannte Felder als leerer String "". Niemals raten oder erfinden.
- `intent` ist eines von: "kaufen", "mieten", "verkaufen", "unklar".
- `qualified` = true, sobald intent (≠ unklar), area und (budget ODER bedrooms) vorliegen.
- `language` = "de" | "en" | "es" (Sprache deiner aktuellen Antwort).
"""

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "reply": {"type": "string"},
        "language": {"type": "string", "enum": ["de", "en", "es"]},
        "lead": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "name":     {"type": "string"},
                "intent":   {"type": "string", "enum": ["kaufen", "mieten", "verkaufen", "unklar"]},
                "area":     {"type": "string"},
                "budget":   {"type": "string"},
                "bedrooms": {"type": "string"},
                "timeline": {"type": "string"},
                "contact":  {"type": "string"},
            },
            "required": ["name", "intent", "area", "budget", "bedrooms", "timeline", "contact"],
        },
        "qualified": {"type": "boolean"},
    },
    "required": ["reply", "language", "lead", "qualified"],
}

# Claude-Client nur aktiv, wenn SDK installiert UND Key gesetzt → sonst Demo-Modus im Frontend.
client = None
try:
    import anthropic
    if os.environ.get("ANTHROPIC_API_KEY"):
        client = anthropic.Anthropic()
except ImportError:
    pass


class Handler(http.server.BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(204, b"")

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, (HERE / "index.html").read_text(encoding="utf-8"),
                       "text/html; charset=utf-8")
        elif self.path == "/api/health":
            self._send(200, json.dumps({"live": client is not None, "model": MODEL}))
        else:
            self._send(404, "not found", "text/plain")

    def do_POST(self):
        if self.path != "/api/chat":
            self._send(404, "not found", "text/plain"); return
        if client is None:
            self._send(503, json.dumps({"error": "no_api_key"})); return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or "{}")
            messages = payload.get("messages", [])
            resp = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=SYSTEM,
                messages=messages,
                output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
            )
            text = next(b.text for b in resp.content if b.type == "text")
            self._send(200, text)  # bereits valides JSON gem. SCHEMA
        except Exception as e:
            self._send(500, json.dumps({"error": str(e)}))

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("", PORT), Handler) as httpd:
        mode = "Live-KI (Claude " + MODEL + ")" if client else "OHNE Key → Frontend nutzt Demo-Modus"
        print(f"\n  nøho AI-Showcase  →  http://localhost:{PORT}")
        print(f"  Status: {mode}\n  (Strg+C zum Beenden)\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Beendet.")
