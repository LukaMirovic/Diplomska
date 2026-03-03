# 🔍 Klasifikator kriptovalut

Orodje za ocenjevanje legitimnosti in tveganja kriptovalutnih projektov, razvito v okviru diplomske naloge **'Sodobne tehnologije veriženja blokov: varnostne grožnje, delovanje in vpliv NFT-jev'** na Fakulteti za računalništvo in informatiko, Univerza v Ljubljani.

Klasifikator izračuna kompozitno oceno legitimnosti (**Legitimacy Score – LS**), ki združuje tri ključne dimenzije analize v uteženo formulo:

$$LS = 0{,}40 \cdot T + 0{,}35 \cdot E + 0{,}25 \cdot S$$

kjer je **T** tehnična ocena, **E** ekonomska ocena in **S** socialna ocena (vse na lestvici 0–100).

---

## 📦 Struktura projekta

```
classifier/
├── main.py                  # Vstopna točka (CLI)
├── scam_indicators.json     # Baza znanih prevar
├── .env                     # API ključ (ni v repozitoriju)
└── classifier/
    ├── __init__.py           # Izvoz modulov
    ├── klasifikator.py       # Glavni klasifikator z utežmi
    ├── analizatorji.py       # Izračun tehničnih, ekonomskih in socialnih metrik
    ├── api_klient.py         # CoinGecko API klient
    ├── baza_prevar.py        # Upravljanje baze znanih prevar
    └── models.py             # Podatkovni modeli (dataclass-i, enum-i)
```

---

## ⚙️ Namestitev

### Predpogoji
- Python 3.10+
- Brezplačen CoinGecko API ključ (priporočeno): https://www.coingecko.com/en/api

### Koraki

```bash
# 1. Kloniraj repozitorij in se premakni v mapo
cd classifier

# 2. Namesti odvisnosti
pip install requests python-dotenv

# 3. Nastavi API ključ (neobvezno, a priporočeno)
echo "COINGECKO_API_KEY=tvoj_kljuc" > .env
```

> ⚠️ Brez API ključa velja omejitev 10 zahtev na minuto, zato bo analiza počasnejša.

---

## 🚀 Uporaba

### Ukazna vrstica (CLI)

```bash
# Analiziraj posamezen kovanec
python main.py bitcoin
python main.py ethereum

# Uporabi simbol namesto ID-ja
python main.py eth
python main.py sol

# Izvozi kot Markdown
python main.py bitcoin --format markdown

# Izvozi kot JSON
python main.py solana --format json

# Shrani rezultat v datoteko
python main.py bitcoin --format markdown --output bitcoin_analiza.md

# Batch analiza – primerjava več kovancev
python main.py btc eth sol dot ada --batch

# Preveri znano prevaro
python main.py safemoon
python main.py bitconnect
```

### Programska uporaba (Python)

```python
from classifier import KriptoKlasifikator, analiziraj_kovanec

# Opcija 1: hitra funkcija
rezultat = analiziraj_kovanec('bitcoin')
print(f"Ocena: {rezultat['koncna_ocena']}/100 ({rezultat['ocena_crka']})")

# Opcija 2: preko razreda
klasifikator = KriptoKlasifikator()
rezultat = klasifikator.klasificiraj('ethereum')

# Izvozi poročilo
porocilo = klasifikator.izvozi_porocilo(rezultat, format='markdown')
print(porocilo)

# Batch analiza
rezultati = klasifikator.batch_analiziraj(['bitcoin', 'ethereum', 'solana'])
```

---

## 📊 Metodologija ocenjevanja

Klasifikator ocenjuje projekte po treh dimenzijah:

| Dimenzija | Utež | Opis |
|-----------|------|------|
| **Tehnična (T)** | 40 % | Dostopnost kode, kvaliteta arhitekture, decentralizacija, varnostni mehanizmi, status revizije |
| **Ekonomska (E)** | 35 % | Pravičnost distribucije, likvidnost, koncentracija lastništva, indikatorji manipulacije, vzdržnost tokenomike |
| **Socialna (S)** | 25 % | Transparentnost ekipe, kvaliteta dokumentacije, angažiranost skupnosti, pristop marketinga |

### Lestvica ocen

| Ocena | Razpon LS | Stopnja tveganja |
|-------|-----------|------------------|
| A+ / A | 85–100 | Zelo nizko tveganje |
| B+ / B | 70–84 | Nizko tveganje |
| C+ / C | 55–69 | Zmerno tveganje |
| D+ / D | 40–54 | Visoko tveganje |
| F | < 40 | Kritično tveganje / verjetna prevara |

---

## 📈 Rezultati avtomatizirane klasifikacije

Klasifikator je bil validiran na izbranih projektih iz treh skupin: Layer 1 platforme, ter znane prevare. Spodnji rezultati so bili pridobljeni z dejanskim zagonom programa (CoinGecko API podatki).

### Layer 1 projekti

| Projekt | T | E | S | **LS** | Ocena | Kategorija |
|---------|---|---|---|--------|-------|------------|
| Bitcoin | 92,0 | 90,9 | 86,5 | **90,2** | A | Layer 1 |
| Ethereum | 91,1 | 87,3 | 85,8 | **88,4** | A | Layer 1 |
| Solana | 87,1 | 87,2 | 85,8 | **86,8** | A | Layer 1 |
| TRON | 86,2 | 85,7 | 81,8 | **84,9** | A– | Layer 1 |
| Cardano | 83,3 | 83,7 | 83,2 | **83,4** | A– | Layer 1 |
| Stellar | 79,8 | 79,8 | 83,8 | **80,8** | A– | Layer 1 |
| Polkadot | 79,8 | 77,5 | 78,6 | **78,7** | B+ | Layer 1 |
| Avalanche | 79,8 | 79,7 | 74,7 | **78,5** | B+ | Layer 1 |
| Tezos | 71,2 | 68,0 | 78,8 | **72,0** | B | Layer 1 |

### Znane prevare

| Projekt | LS | Ocena | Kategorija |
|---------|-----|-------|------------|
| SafeMoon | 0,0 | F | Znana prevara |
| BitConnect | 0,0 | F | Znana prevara |
| Squid Game Token | 0,0 | F | Znana prevara |

> Znane prevare sistem prepozna **takoj iz baze** (še pred klicem API-ja) in jim dodeli oceno **LS = 0** ter stopnjo tveganja **CRITICAL**.

### Ključne ugotovitve

- **Hierarhija kakovosti:** Vodilni projekti (Bitcoin, Ethereum, Solana) dosegajo ocene LS > 86, uveljavljeni projekti LS > 78, medtem ko problematični projekti padejo pod LS = 30.
- **Zanesljiva detekcija prevar:** Sistem pravilno identificira vse znane prevare iz baze in dinamično zaznava sumljive vzorce pri neznanih projektih.
- **Realistična rangiranja:** Projekti so razporejeni v naboru od B (Tezos, 72,0) do A (Bitcoin, 90,2), kar odraža razlike v zrelosti, sprejetosti in tehnični odličnosti.
- **Uravnotežene dimenzije:** Pri legitimnih projektih so vse tri dimenzije (T, E, S) konsistentno visoko ocenjene, z manjšimi variacijami, ki odražajo specifične prednosti posameznih projektov.

---

## 🛡️ Baza znanih prevar

Datoteka `scam_indicators.json` vsebuje podatke o znanih prevarah, vključno z:
- imenom, simbolom in tipom prevare,
- letom propada in ocenjenimi izgubami,
- rdečimi zastavicami (opozorilnimi znaki).

Klasifikator **samodejno prepozna** znane prevare (npr. BitConnect, SafeMoon, OneCoin) še pred klicem API-ja in vrne ustrezno opozorilo.

---

## 📝 Primeri izpisa

### Legitimen projekt
```
╔════════════════════════════════════════════════════════════════════╗
║            CRYPTOCURRENCY ANALYSIS REPORT                        ║
╠════════════════════════════════════════════════════════════════════╣
║                   Bitcoin (BTC)                                   ║
╚════════════════════════════════════════════════════════════════════╝

   [████████████████████░] 90.2/100 (A)
   Risk Level: Very Low Risk
   Category: Layer 1 - Own Blockchain
```

### Znana prevara
```
╔════════════════════════════════════════════════════════════════════╗
║            CRYPTOCURRENCY ANALYSIS REPORT                        ║
╠════════════════════════════════════════════════════════════════════╣
║                   BitConnect (BCC)                                ║
╚════════════════════════════════════════════════════════════════════╝

  ⚠️  CONFIRMED SCAM WARNING  ⚠️

  Type: Ponzi Scheme
  Red Flags:
    ✗ Promised guaranteed daily returns of 0.5-1%
    ✗ Referral system with up to 7% commissions
    ✗ Anonymous team
    ✗ No working product or verifiable trading bot
```

---

## 📚 Referenca

Če uporabite to orodje v akademske namene, prosim citirajte:

> Mirović, L. (2026). *Sodobne tehnologije veriženja blokov: varnostne grožnje, delovanje in vpliv NFT-jev*. Diplomska naloga. Fakulteta za računalništvo in informatiko, Univerza v Ljubljani.

---

## ⚖️ Omejitve

- Podatki se pridobivajo iz CoinGecko API-ja – dostopnost in točnost sta odvisni od zunanjega vira.
- Klasifikator **ni finančni svetovalec** – ocene so namenjene informativni in akademski uporabi.
- Nekateri projekti morda niso na voljo v CoinGecko bazi.
- Ocene za novejše projekte z omejeno zgodovino so lahko manj zanesljive.

---

## 📄 Licenca

Razvito v okviru diplomske naloge na FRI UL. Za akademsko in izobraževalno uporabo.
