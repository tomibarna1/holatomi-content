# holatomi-content: útmutató Claude-nak

Ez a repó a **Hola Tomi** iPhone-app (Tomi saját spanyol tanulóappja) tananyaga. Az app innen frissül:
`https://raw.githubusercontent.com/tomibarna1/holatomi-content/main/manifest.json`.
Itt csak tananyag van, személyes adat (haladás, statisztika) soha.

Tomi kezdő (A1), magyar anyanyelvű, magántanárral tanul. A magyar szöveg tegező, rövid, pontos. **Gondolatjelet (em dash, en dash: U+2014, U+2013) soha ne használj**: vessző, kettőspont, zárójel vagy új mondat.

## Munkafolyamat (minden változtatásnál)

0. Ha még nincs helyben: `gh repo clone tomibarna1/holatomi-content && cd holatomi-content` (vagy `git pull`, ha már megvan).
1. Szerkeszd a JSON-t (lásd sémák lent).
2. Ha új kártya jön: `id` egyedi, stabil, sosem változik.
3. Növeld a `vocab.json` `deckVersion` mezőjét, ha kártya változott.
4. `python3 scripts/validate.py` → hiba nélkül kell lefutnia.
5. `python3 scripts/build_manifest.py` → növeli a `contentVersion`-t, újraszámolja a SHA256-okat.
6. `git add -A && git commit -m "content: ..." && git push`.

Az app a következő frissítéskor (indítás, lehúzás, háttér) letölti, és kiírja: „X új szó érkezett”. Tomi haladása megmarad.

Az app a `main` ág legutóbbi commitjára fordítja a címet (GitHub API), így push után azonnal az új tartalmat kapja. Ha az API épp nem elérhető, a nyers `main` utat használja, ami legfeljebb 5 percig még a régi lehet: ilyenkor pár perc múlva érdemes újra frissíteni.

## Szabályok, amik a haladást védik

- **Kártya `id`-t soha ne nevezz át és ne használd újra.** Az app id alapján fésül össze: új id = új kártya; meglévő id más szöveggel = szöveg frissül, előzmény marad.
- Kártyát **ne törölj**, ha mégis kikerül, az app archiválja (rejtett, előzmény marad). Törlés helyett inkább javítsd.
- id formátum: `<kategória-rövid>.<spanyol-szó-ékezet-nélkül>`, kisbetű, szám, pont, aláhúzás vagy kötőjel, pl. `rutina.despertarse`, `cosas.la_mesa`. Ütközésnél `-2` utótag.

## vocab.json

```json
{
  "schemaVersion": 1,
  "deckVersion": 3,
  "updatedAt": "2026-11-09T12:00:00Z",
  "categories": [{ "id": "Rutina", "nameHu": "Napi rutin" }],
  "cards": [{
    "id": "rutina.despertarse",
    "category": "Rutina",
    "es": "despertarse",
    "hu": "felébredni",
    "lesson": "2026-10-29",
    "addedAt": "2026-11-09",
    "example": "Me despierto a las siete.",
    "exampleHu": "Hétkor ébredek.",
    "note": "visszaható ige: me despierto",
    "gender": null,
    "plural": null,
    "partOfSpeech": "verb",
    "tags": ["rutina"],
    "audioText": null
  }]
}
```

- Kötelező: `id`, `category` (a `categories` egyik `id`-je), `es`, `hu`. Minden más opcionális.
- `es`: alternatívák ` / ` jellel (`el pelo / el cabello`), ellentétpár ` ↔ ` jellel (`corto ↔ largo`). Főnévnél névelővel (`la mesa`): ebből jön a nem.
- `hu`: több jelentés vesszővel vagy ` / ` jellel.
- `lesson`: a tanári óra dátuma (`ÉÉÉÉ-HH-NN`). Ebből épül az „Utolsó óra anyaga”.
- `gender`: `m`, `f`, `mf`. `partOfSpeech`: `noun`, `verb`, `adj`, `phrase`, `number`, `other`.
- Új kategória: előbb a `categories` listába (`id` spanyolul, `nameHu` magyarul).

## verbs.json

```json
{
  "schemaVersion": 1,
  "verbs": [
    { "id": "hablar", "infinitive": "hablar", "hu": "beszélni", "type": "ar",
      "reflexive": false, "irregular": false, "stemChange": null },
    { "id": "despertarse", "infinitive": "despertarse", "hu": "felébredni", "type": "ar",
      "reflexive": true, "irregular": false, "stemChange": "e>ie" },
    { "id": "salir", "infinitive": "salir", "hu": "kimenni, elindulni", "type": "ir",
      "reflexive": false, "irregular": true, "stemChange": null,
      "overrides": { "presente": { "yo": "salgo" } } },
    { "id": "ser", "infinitive": "ser", "hu": "lenni", "type": "er",
      "reflexive": false, "irregular": true, "stemChange": null,
      "overrides": { "presente": { "yo": "soy", "tu": "eres", "el": "es",
        "nosotros": "somos", "vosotros": "sois", "ellos": "son" } },
      "note": "állandó tulajdonság, kiléte, eredet, foglalkozás" }
  ]
}
```

- A szabályos alakokat az app **generálja**, nem tároljuk őket.
- `type`: `ar`, `er`, `ir` (a visszaható ige `-se` nélküli tője szerint).
- `reflexive: true` esetén az `infinitive` `-se`-re végződik; az app teszi elé: me, te, se, nos, os, se.
- `stemChange`: `e>ie`, `o>ue`, `e>i`, `u>ue` vagy `null`. A tőhangváltás az utolsó tőbeli magánhangzón történik, nosotros/vosotros kivételével.
- `overrides`: időnként (`presente`, később `preteritoPerfecto`, `indefinido`, `imperfecto`, `futuro`, `imperativo`) és személyenként (`yo`, `tu`, `el`, `nosotros`, `vosotros`, `ellos`) az **eltérő** alakok. Csak ami eltér a szabályostól (tőhangváltással együtt). Teljesen rendhagyónál mind a 6.
- `irregular: true`, ha van `overrides`. Visszaható igénél az override névmás nélküli alak (`visto`, nem `me visto`).
- Opcionális: `note` (magyar tipp), `examples` (`[{"es","hu"}]`).

## grammar/<id>.json

Fájlnév = `id`, pl. `grammar/g06-ser.json`.

```json
{
  "id": "g06-ser",
  "titleHu": "Ser",
  "subtitleEs": "soy, eres, es",
  "order": 6,
  "level": "A1",
  "status": "taken",
  "sections": [
    { "type": "text", "title": "Mire való?", "body": "..." },
    { "type": "table", "title": "Jelen idő", "columns": ["", "ser"], "rows": [["yo", "soy"]] },
    { "type": "examples", "title": "Példák", "items": [{ "es": "Soy de Hungría.", "hu": "Magyarországról jöttem." }] },
    { "type": "tip", "title": "Magyarul", "body": "..." },
    { "type": "warning", "title": "Figyelj!", "body": "...", "items": ["...", "..."] }
  ],
  "quiz": [ /* gyakorlat-elemek, lásd lent */ ]
}
```

- `status`: `taken` (Órán vettük), `next` (Következik). A „Kész” állapotot az app számolja.
- `body`: egyszerű szöveg, `**félkövér**` és sortörés (`\n`) megengedett.
- `examples.items[].es`: felolvasható spanyol mondat.
- `quiz`: 6-10 elem.

## exercises/<id>.json (pl. tanári házi)

```json
{ "id": "ex-2026-11-12-hazi", "titleHu": "Házi: ser és estar", "lesson": "2026-11-12", "items": [ ... ] }
```

## Gyakorlat-elem (a `quiz` és az `items` közös sémája)

Minden elemen: `id` (fájlon belül egyedi), `type`, `prompt`, opcionális `explanation` (magyar, válasz után látszik), opcionális `hint`.

| type | mezők | jelentés |
|---|---|---|
| `multipleChoice` | `options` [string], `answer` (index) | egy jó válasz |
| `fillBlank` | `prompt` benne `___`, `answers` [string] | beírandó, bármelyik elfogadott |
| `translateToEs` | `prompt` magyarul, `answers` [string] | spanyolra fordít |
| `translateToHu` | `prompt` spanyolul, `answers` [string] | magyarra fordít |
| `reorder` | `tiles` [string], `answers` [string] | szócsempékből mondat |
| `match` | `pairs` [{`es`,`hu`}] | párosítás (3-6 pár) |
| `serEstar` | `prompt` benne `___`, `options` [string], `answer` (index) | ser vagy estar alak |
| `article` | `prompt` benne `___`, `options` [string], `answer` (index) | névelő |

## manifest.json (generált, kézzel ne írd)

```json
{ "contentVersion": 4, "updatedAt": "...", "files": [{ "path": "vocab.json", "sha256": "...", "bytes": 53291 }] }
```
