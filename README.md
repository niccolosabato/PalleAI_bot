# PalleAI_bot

Bot Telegram per chat di gruppo tra amici, con più "personalità" AI generate da
**Google Gemini**. Risponde quando lo tagghi (o in privato), tiene a mente gli
ultimi messaggi della chat e li usa come contesto, e ha qualche comando extra per
farsi sfottere addosso.

> ⚠️ Il bot è pensato per gruppi di amici stretti: le personalità sono volutamente
> volgari, cattive e sopra le righe. Non è un assistente educato e non è adatto a
> contesti pubblici o professionali.

## Cosa fa

- **Risposte contestuali**: mantiene una cronologia in memoria degli ultimi
  messaggi per ogni chat (`MAX_HISTORY_MESSAGES`, default 10) e la passa a Gemini
  come contesto, così le battute sono su misura per chi sta scrivendo.
- **Quando risponde**: sempre in chat privata; nei gruppi solo se viene taggato
  (`@nomebot`) o se rispondi a un suo messaggio. Gli altri messaggi li legge e li
  memorizza in silenzio.
- **Personalità intercambiabili** per chat, scelte da una tastiera inline.

## Comandi

| Comando | Cosa fa |
|---|---|
| `/start` | Messaggio di benvenuto (a modo suo). |
| `/help` | Riepilogo rapido dei comandi. |
| `/chiedi <domanda>` | Risposta **davvero utile e corretta**, con il tono da stronzo ridotto a una stoccata. Funziona anche rispondendo a un messaggio con `/chiedi`. |
| `/persona` | Tastiera inline per cambiare la personalità attiva nella chat. |
| `/psicoanalizza [@utente]` | Finta diagnosi psicoanalitica cialtrona, basata sui messaggi recenti della vittima. Senza argomenti analizza chi ha scritto il comando; in risposta a un messaggio analizza il suo autore. |
| `/rissa @tizio @caio` | Racconto di una scazzottata immaginaria tra due membri, con verdetto finale. Accetta anche un solo `@utente` (l'altro sei tu) o una risposta a un messaggio. |

### Personalità disponibili

| Chiave | Nome | Registro |
|---|---|---|
| `stronzo` (default) | 😈 Stronzo cinico | Volgare, sfottente, gergo da bar. |
| `filosofo` | 🧘 Filosofo assurdo | Solenne e pomposo a sproposito. |
| `piccante` | 🌶️ Piccante | Doppi sensi e allusioni da latin lover cringe. |

Tutte le personalità condividono due regole di sistema: **brevità** (una sola frase
per le risposte in chat) e **varietà** (mai ripetere la stessa battuta già usata nel
contesto).

## Struttura

```
main.py                    entrypoint: keep_alive() + polling Telegram
bot/config.py              lettura env vars
bot/handlers.py            comandi, callback e handler dei messaggi
bot/gemini_client.py       chiamate a Gemini (risposta, /chiedi, psicoanalisi, rissa)
bot/personalities.py       system instruction delle personalità + personalità attiva per chat
bot/history.py             cronologia messaggi in memoria, troncata a MAX_HISTORY_MESSAGES
bot/members.py             anagrafica membri per chat (per risolvere gli @username)
bot/mentions.py            capire se un messaggio di gruppo è rivolto al bot
requirements.txt
```

Cronologia, membri e personalità attiva stanno **solo in memoria**: a ogni riavvio
del processo si azzerano. Non c'è database.

## Setup locale

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Crea un `.env` nella root:

```
TELEGRAM_TOKEN=...                   # token da @BotFather
GEMINI_API_KEY=...                   # chiave Google AI Studio
GEMINI_MODEL=gemini-3.1-flash-lite   # opzionale, questo è il default
MAX_HISTORY_MESSAGES=10              # opzionale
LOG_LEVEL=INFO                       # opzionale
PORT=8080                            # opzionale, porta del keep-alive HTTP
```

Avvio:

```bash
python3 main.py
```

Perché il bot risponda ai messaggi di gruppo che lo taggano, su @BotFather va
disattivata la *privacy mode* (`/setprivacy` → Disable), altrimenti Telegram non
gli consegna i messaggi normali del gruppo.

## Deploy (Render, piano free)

Il progetto è pensato per girare come **Web Service** su Render:

- Build command: `pip install -r requirements.txt`
- Start command: `python3 main.py`
- Variabili d'ambiente: quelle del `.env` (Render fornisce `PORT` da sé)

`main.py` avvia un server Flask fittizio (`keep_alive()`) su `PORT` in un thread
separato **solo per superare l'health check di Render**: senza, il servizio va in
restart loop e più istanze finiscono a fare polling Telegram in contemporanea,
causando errori `Conflict`. Se si passa a un hosting senza health check HTTP
(worker / background service), quel pezzo si può togliere.

## Note

- Nessun test automatizzato al momento. `bot/history.py`, `bot/personalities.py` e
  `bot/mentions.py` sono logica pura e sarebbero i primi candidati.
- Il bot spezza le risposte lunghe di `/chiedi` in blocchi da 4000 caratteri per
  stare sotto il limite di Telegram.
- Se Gemini esaurisce la quota (429) il bot lo dice esplicitamente; per gli altri
  errori risponde con un messaggio generico e logga l'eccezione.
