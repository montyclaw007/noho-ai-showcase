# nøho · AI-Showcase — Mehrsprachiger Immobilien-Anfragen-Bot

Vorzeigbare Live-Demo für die Akquise: eine Luxus-Makler-Landingpage („Mar y Sol Inmobiliaria")
mit Chat-Widget, das Anfragen **automatisch auf Deutsch, English und Español** beantwortet,
den Lead qualifiziert (Vorhaben, Lage, Budget, Schlafzimmer, Kontakt) und live „ans CRM übergibt".

Genau der Zeitfresser, den ein Mallorca-Makler heute manuell auf drei Sprachen erledigt.

---

## Zwei Betriebsarten

**1. Demo-Modus (kein Setup) — zum Screensharen / Verschicken**
`index.html` einfach doppelklicken. Das Widget läuft mit einer eingebauten,
mehrsprachigen Logik (Status-Badge: „Demo-Modus"). Reicht, um Interessenten den
Effekt zu zeigen — ohne Server, ohne API-Key, ohne Internet.

**2. Live-KI (das eigentliche Produkt) — angetrieben von Claude Opus 4.8**
```bash
cd ~/Developer/noho-ai-showcase
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...      # dein Key
python3 server.py
```
Dann **http://localhost:8000** öffnen. Das Badge zeigt „Live-KI · Claude".
Jetzt antwortet echtes Claude — versteht freie Formulierungen in allen drei
Sprachen, geht auf Rückfragen ein und füllt die Lead-Felder selbst.

> Ohne gesetzten `ANTHROPIC_API_KEY` startet der Server trotzdem und fällt im
> Frontend automatisch auf den Demo-Modus zurück.

---

## Wie es technisch funktioniert (für die Erklärung beim Kunden)

- **Structured Output:** Claude liefert pro Nachricht ein JSON mit `reply` + `lead`-Objekt
  (`intent`, `area`, `budget`, `bedrooms`, `timeline`, `contact`) + `qualified`-Flag.
  Damit bekommt das Chatfenster die Antwort UND die CRM-Daten in einem Schritt.
- **Sprach-Spiegelung:** Claude erkennt DE/EN/ES selbst und antwortet in derselben Sprache.
- **Anbindung:** Das `lead`-Objekt geht beim echten Einsatz per Webhook/Make.com in
  Airtable / das CRM des Maklers (hier im Panel rechts visualisiert).

## Verkaufs-Talking-Points

- „Eure Website beantwortet Anfragen **rund um die Uhr, in drei Sprachen** — automatisch."
- „Jede Anfrage kommt **vorqualifiziert** rein: Lage, Budget, Zimmer, Kontakt — ihr ruft nur noch warme Leads an."
- „Spart pro Woche X Stunden manuelles Anfragen-Handling."

## Anpassen

- Agentur, Objekte, Persona → in `server.py` (`SYSTEM`-Prompt) und `index.html` (Listings/Texte).
- Branche wechseln (Hotel/Finca, Yacht-Charter) → nur den `SYSTEM`-Prompt + Objektliste tauschen.
- Modell → `MODEL` in `server.py`.

_Demo-Objekt von nøho studio. Fiktive Agentur, fiktive Objekte._
