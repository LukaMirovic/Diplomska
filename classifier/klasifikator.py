"""
Glavni klasifikator kriptovalut.
Tukaj se zdruzijo vse metrike in izracuna koncna ocena.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .models import (
    TehnicneMetrike, EkonomskeMetrike, SocialneMetrike,
    IndikatorjiPrevare, StopnjaTveganja, KategorijaProjekta
)
from .baza_prevar import UpravljalecBazePrevar
from .api_klient import CoinGeckoKlient
from .analizatorji import AnalizatorMetrik


class KriptoKlasifikator:
    """
    Glavni razred za klasifikacijo kriptovalut.
    
    Utezi metrik (iz diplomske):
    - Tehnicne: 40%
    - Ekonomske: 35%
    - Socialne: 25%
    """
    
    # Utezi za koncno oceno
    UTEZ_TEHNICNE = 0.40
    UTEZ_EKONOMSKE = 0.35
    UTEZ_SOCIALNE = 0.25
    
    def __init__(self, pot_do_baze: str = "scam_indicators.json"):
        """
        Inicializiraj klasifikator.
        
        Args:
            pot_do_baze: Pot do JSON datoteke z znanimu prevarami
        """
        self.baza = UpravljalecBazePrevar(pot_do_baze)
        self.klient = CoinGeckoKlient()
        self.analizator = AnalizatorMetrik(self.baza)
    
    def klasificiraj(self, identifikator: str) -> Dict:
        """
        Izvede celotno klasifikacijo kovanca.
        
        Args:
            identifikator: ID kovanca ali simbol (npr. 'bitcoin' ali 'BTC')
        
        Returns:
            Slovar z vsemi rezultati analize
        """
        # Najprej preveri ali je znana prevara (PRED API klicem)
        je_prevara, podatki_prevare = self.baza.je_znana_prevara(identifikator)
        if je_prevara:
            ime = podatki_prevare.get('name', identifikator)
            simbol = podatki_prevare.get('symbol', '???').upper()
            
            # Ustvari indikatorje za prevaro
            indikatorji = IndikatorjiPrevare()
            indikatorji.je_znana_prevara = True
            indikatorji.podatki_znane_prevare = podatki_prevare
            indikatorji.verjetnost_prevare = 1.0
            indikatorji.rdeci_zastavice.extend(podatki_prevare.get('red_flags', []))
            
            return self._ustvari_porocilo_prevare(ime, simbol, {}, indikatorji)
        
        # Pridobi podatke iz API-ja
        podatki = self.klient.pridobi_podatke_kovanca(identifikator)
        
        # Ce ni podatkov, morda je neznan kovanec
        if not podatki:
            raise ValueError(f"Kovanec '{identifikator}' ni najden na CoinGecko")
        
        ime = podatki.get('basic_info', {}).get('name', identifikator)
        simbol = podatki.get('basic_info', {}).get('symbol', '???').upper()
        
        # Preveri se po imenu (v primeru da identifikator ni bil v bazi)
        indikatorji = self.analizator.analiziraj_prevare(podatki, ime)
        
        # Ce je znana prevara, vrni posebno porocilo
        if indikatorji.je_znana_prevara:
            return self._ustvari_porocilo_prevare(ime, simbol, podatki, indikatorji)
        
        # Sicer analiziraj vse metrike
        tehnicne = self.analizator.analiziraj_tehnicne(podatki, indikatorji)
        ekonomske = self.analizator.analiziraj_ekonomske(podatki, indikatorji)
        socialne = self.analizator.analiziraj_socialne(podatki, indikatorji)
        
        # Izracunaj koncno oceno
        ocena_teh = tehnicne.izracunaj_oceno()
        ocena_eko = ekonomske.izracunaj_oceno()
        ocena_soc = socialne.izracunaj_oceno()
        
        # Koncna ocena z utezmi
        koncna = (
            ocena_teh * self.UTEZ_TEHNICNE +
            ocena_eko * self.UTEZ_EKONOMSKE +
            ocena_soc * self.UTEZ_SOCIALNE
        )
        
        # Popravek glede na verjetnost prevare
        if indikatorji.verjetnost_prevare > 0:
            faktor_kazni = 1 - (indikatorji.verjetnost_prevare * 0.5)
            koncna *= faktor_kazni
        
        # Doloci stopnjo tveganja
        stopnja = self._doloci_stopnjo(koncna, indikatorji)
        
        # Kategorija projekta
        kategorija = self._doloci_kategorijo(podatki, koncna)
        
        # Ocena (A-F)
        crka = self._doloci_crko(koncna)
        
        # Prednosti in slabosti
        prednosti, slabosti = self._analiziraj_prednosti_slabosti(
            tehnicne, ekonomske, socialne, indikatorji
        )
        
        return {
            'ime': ime,
            'simbol': simbol,
            'koncna_ocena': round(koncna, 2),
            'ocena_crka': crka,
            'stopnja_tveganja': stopnja.value,
            'kategorija': kategorija.value,
            'tehnicna_ocena': round(ocena_teh, 2),
            'ekonomska_ocena': round(ocena_eko, 2),
            'socialna_ocena': round(ocena_soc, 2),
            'tehnicne_metrike': tehnicne.v_slovar(),
            'ekonomske_metrike': ekonomske.v_slovar(),
            'socialne_metrike': socialne.v_slovar(),
            'verjetnost_prevare': round(indikatorji.verjetnost_prevare * 100, 1),
            'opozorila': indikatorji.opozorila,
            'rdeci_zastavice': indikatorji.rdeci_zastavice,
            'prednosti': prednosti,
            'slabosti': slabosti,
            'cas_analize': datetime.now().isoformat()
        }
    
    def _ustvari_porocilo_prevare(
        self, ime: str, simbol: str, podatki: Dict, indikatorji: IndikatorjiPrevare
    ) -> Dict:
        """Ustvari porocilo za znano prevaro."""
        podatki_prevare = indikatorji.podatki_znane_prevare
        
        return {
            'ime': ime,
            'simbol': simbol,
            'koncna_ocena': podatki_prevare.get('score', 0),
            'ocena_crka': podatki_prevare.get('grade', 'F'),
            'stopnja_tveganja': 'CRITICAL',
            'kategorija': 'KNOWN_SCAM',
            'je_potrjena_prevara': True,
            'tip_prevare': podatki_prevare.get('scam_type', 'Unknown'),
            'rdeci_zastavice': podatki_prevare.get('red_flags', []),
            'opis_prevare': podatki_prevare.get('description', ''),
            'datum_propada': podatki_prevare.get('collapse_date'),
            'ocenjene_izgube': podatki_prevare.get('estimated_losses'),
            'opozorila': ["OPOZORILO: Ta projekt je potrjena prevara. Izogibajte se!"],
            'cas_analize': datetime.now().isoformat()
        }
    
    def _doloci_stopnjo(self, ocena: float, indikatorji: IndikatorjiPrevare) -> StopnjaTveganja:
        """Doloci stopnjo tveganja glede na koncno oceno."""
        if indikatorji.je_znana_prevara or indikatorji.verjetnost_prevare > 0.8:
            return StopnjaTveganja.KRITICNO
        
        if ocena >= 85:
            return StopnjaTveganja.ZELO_NIZKO
        elif ocena >= 70:
            return StopnjaTveganja.NIZKO
        elif ocena >= 55:
            return StopnjaTveganja.SREDNJE
        elif ocena >= 40:
            return StopnjaTveganja.VISOKO
        elif ocena >= 25:
            return StopnjaTveganja.ZELO_VISOKO
        else:
            return StopnjaTveganja.KRITICNO
    
    def _doloci_kategorijo(self, podatki: Dict, ocena: float) -> KategorijaProjekta:
        """
        Doloci kategorijo projekta.
        Uporablja samo podatke iz API-ja, brez hardkodirani seznamov.
        """
        osnovni = podatki.get('basic_info', {})
        kategorije = osnovni.get('categories', []) or []
        trzni = podatki.get('market_data', {})
        trzni_info = osnovni.get('market_data', {}) or {}
        
        rang = trzni.get('market_cap_rank') or trzni_info.get('market_cap_rank') or 10000
        
        # Preveri ce je Layer 1 glede na kategorije iz CoinGecko
        je_layer1 = any(
            'layer 1' in kat.lower() or 
            'layer 0' in kat.lower() or
            'layer-1' in kat.lower() or
            'layer-0' in kat.lower() or
            'smart contract platform' in kat.lower() or
            'proof of stake' in kat.lower() or
            'proof of work' in kat.lower()
            for kat in kategorije
        )
        
        # Preveri ce ima lastno omrezje (znak L1)
        ima_omrezje = any(
            'blockchain' in kat.lower() or
            'protocol' in kat.lower() or
            'infrastructure' in kat.lower() or
            'ecosystem' in kat.lower()
            for kat in kategorije
        )
        
        # Ce ima kategorijo L1 in dobro oceno
        if je_layer1:
            return KategorijaProjekta.LAYER_1
        
        # Ce ima lastno omrezje, visok rang in dobro oceno
        if ima_omrezje and rang <= 100 and ocena >= 55:
            return KategorijaProjekta.LAYER_1
        
        # Dobri projekti z visoko oceno
        if ocena >= 50:
            return KategorijaProjekta.KVALITETEN_TOKEN
        else:
            return KategorijaProjekta.PROBLEMATICEN
    
    def _doloci_crko(self, ocena: float) -> str:
        """Pretvori numericno oceno v crko."""
        if ocena >= 93:
            return 'A+'
        elif ocena >= 85:
            return 'A'
        elif ocena >= 80:
            return 'A-'
        elif ocena >= 75:
            return 'B+'
        elif ocena >= 70:
            return 'B'
        elif ocena >= 65:
            return 'B-'
        elif ocena >= 60:
            return 'C+'
        elif ocena >= 55:
            return 'C'
        elif ocena >= 50:
            return 'C-'
        elif ocena >= 45:
            return 'D+'
        elif ocena >= 40:
            return 'D'
        elif ocena >= 35:
            return 'D-'
        else:
            return 'F'
    
    def _analiziraj_prednosti_slabosti(
        self,
        teh: TehnicneMetrike,
        eko: EkonomskeMetrike,
        soc: SocialneMetrike,
        ind: IndikatorjiPrevare
    ) -> Tuple[List[str], List[str]]:
        """Analizira prednosti in slabosti kovanca."""
        prednosti = []
        slabosti = []
        
        # Tehnicne
        if teh.dostopnost_kode >= 8:
            prednosti.append("Odprta koda")
        elif teh.dostopnost_kode < 5:
            slabosti.append("Omejena dostopnost kode")
        
        if teh.kvaliteta_arhitekture >= 8:
            prednosti.append("Mocna razvojna aktivnost")
        elif teh.kvaliteta_arhitekture < 5:
            slabosti.append("Pomanjkljiva razvojna aktivnost")
        
        if teh.decentralizacija >= 8:
            prednosti.append("Visoka stopnja decentralizacije")
        elif teh.decentralizacija < 5:
            slabosti.append("Vprasljiva decentralizacija")
        
        if teh.varnostni_mehanizmi >= 8.5:
            prednosti.append("Odlicni varnostni mehanizmi")
        elif teh.varnostni_mehanizmi < 5:
            slabosti.append("Pomanjkljivi varnostni mehanizmi")
        
        # Ekonomske
        if eko.globina_likvidnosti >= 8.5:
            prednosti.append("Odlicna likvidnost")
        elif eko.globina_likvidnosti < 5:
            slabosti.append("Nizka likvidnost")
        
        if eko.vzdrznost_tokenomike >= 8:
            prednosti.append("Vzdrzna tokenomika")
        elif eko.vzdrznost_tokenomike < 5:
            slabosti.append("Vprasljiva tokenomika")
        
        if eko.koncentracija_lastnistva >= 8:
            prednosti.append("Dobra distribucija lastnistva")
        elif eko.koncentracija_lastnistva < 5:
            slabosti.append("Visoka koncentracija lastnistva")
        
        if eko.indikatorji_manipulacije >= 8:
            prednosti.append("Nizka volatilnost")
        elif eko.indikatorji_manipulacije < 4:
            slabosti.append("Visoka volatilnost - mozna manipulacija")
        
        # Socialne
        if soc.angaziranost_skupnosti >= 8:
            prednosti.append("Velika in aktivna skupnost")
        elif soc.angaziranost_skupnosti < 5:
            slabosti.append("Majhna skupnost")
        
        if soc.transparentnost_ekipe >= 8:
            prednosti.append("Transparentna ekipa")
        elif soc.transparentnost_ekipe < 5:
            slabosti.append("Netransparentna ekipa")
        
        if soc.kvaliteta_dokumentacije >= 8:
            prednosti.append("Obsezna dokumentacija")
        elif soc.kvaliteta_dokumentacije < 5:
            slabosti.append("Pomanjkljiva dokumentacija")
        
        # Prevare
        if ind.verjetnost_prevare > 0.5:
            slabosti.append("Visoka verjetnost prevare")
        elif ind.verjetnost_prevare > 0.3:
            slabosti.append("Nekateri indikatorji prevare")
        elif ind.verjetnost_prevare < 0.1:
            prednosti.append("Nizka verjetnost prevare")
        
        return prednosti[:7], slabosti[:7]  # Max 7 od vsake
    
    # ========================================================================
    # Izvoz in batch procesiranje
    # ========================================================================
    
    def izvozi_porocilo(self, rezultat: Dict, format: str = "json") -> str:
        """
        Izvozi rezultat v zelen format.
        
        Args:
            rezultat: Rezultat iz klasificiraj()
            format: 'json', 'markdown' ali 'text'
        """
        if format == "json":
            return json.dumps(rezultat, indent=2, ensure_ascii=False)
        
        elif format == "markdown":
            return self._v_markdown(rezultat)
        
        else:  # text
            return self._v_text(rezultat)
    
    def _v_markdown(self, r: Dict) -> str:
        """Pretvori rezultat v Markdown."""
        je_prevara = r.get('je_potrjena_prevara', False)
        
        md = f"# Analiza: {r['ime']} ({r['simbol']})\n\n"
        
        if je_prevara:
            md += f"## ⚠️ OPOZORILO: POTRJENA PREVARA ⚠️\n\n"
            md += f"**Tip prevare:** {r.get('tip_prevare', 'Neznano')}\n\n"
            md += f"**Opis:** {r.get('opis_prevare', 'N/A')}\n\n"
            
            if r.get('rdeci_zastavice'):
                md += "### Rdeci znaki:\n"
                for znak in r['rdeci_zastavice']:
                    md += f"- ❌ {znak}\n"
        else:
            md += f"## Povzetek\n\n"
            md += f"| Metrika | Vrednost |\n"
            md += f"|---------|----------|\n"
            md += f"| **Koncna ocena** | {r['koncna_ocena']}/100 ({r['ocena_crka']}) |\n"
            md += f"| **Stopnja tveganja** | {r['stopnja_tveganja']} |\n"
            md += f"| **Kategorija** | {r['kategorija']} |\n"
            md += f"| **Tehnicna** | {r['tehnicna_ocena']}/100 |\n"
            md += f"| **Ekonomska** | {r['ekonomska_ocena']}/100 |\n"
            md += f"| **Socialna** | {r['socialna_ocena']}/100 |\n\n"
            
            if r.get('prednosti'):
                md += "### ✅ Prednosti\n"
                for p in r['prednosti']:
                    md += f"- {p}\n"
                md += "\n"
            
            if r.get('slabosti'):
                md += "### ⚠️ Slabosti\n"
                for s in r['slabosti']:
                    md += f"- {s}\n"
                md += "\n"
            
            if r.get('rdeci_zastavice'):
                md += "### 🚨 Rdeci znaki\n"
                for z in r['rdeci_zastavice']:
                    md += f"- {z}\n"
        
        md += f"\n---\n*Generirano: {r['cas_analize']}*\n"
        return md
    
    def _v_text(self, r: Dict) -> str:
        """Pretvori rezultat v navaden tekst z lepim formatiranjem."""
        je_prevara = r.get('je_potrjena_prevara', False)
        
        # Header
        sirina = 70
        linije = [
            "",
            "╔" + "═" * (sirina - 2) + "╗",
            "║" + f" CRYPTOCURRENCY ANALYSIS REPORT ".center(sirina - 2) + "║",
            "╠" + "═" * (sirina - 2) + "╣",
            "║" + f" {r['ime']} ({r['simbol']}) ".center(sirina - 2) + "║",
            "╚" + "═" * (sirina - 2) + "╝",
        ]
        
        if je_prevara:
            linije.extend([
                "",
                "┌" + "─" * (sirina - 2) + "┐",
                "│" + " ⚠️  CONFIRMED SCAM WARNING  ⚠️ ".center(sirina - 2) + "│",
                "└" + "─" * (sirina - 2) + "┘",
                "",
                f"  Type: {r.get('tip_prevare', 'Unknown')}",
                f"  Description: {r.get('opis_prevare', 'N/A')}",
                "",
                "  Red Flags:",
            ])
            for z in r.get('rdeci_zastavice', []):
                linije.append(f"    ✗ {z}")
        else:
            # Ocena z vizualizacijo
            ocena = r['koncna_ocena']
            crka = r['ocena_crka']
            
            # Graficni prikaz ocene
            polni = int(ocena / 5)  # 20 blokov za 100%
            prazni = 20 - polni
            bar = "█" * polni + "░" * prazni
            
            linije.extend([
                "",
                "┌" + "─" * (sirina - 2) + "┐",
                "│" + " OVERALL SCORE ".center(sirina - 2) + "│",
                "├" + "─" * (sirina - 2) + "┤",
                "│" + f"   [{bar}] {ocena:.1f}/100 ({crka})".ljust(sirina - 2) + "│",
                "│" + f"   Risk Level: {r['stopnja_tveganja']}".ljust(sirina - 2) + "│",
                "│" + f"   Category: {r['kategorija']}".ljust(sirina - 2) + "│",
                "└" + "─" * (sirina - 2) + "┘",
            ])
            
            # Podrobne ocene
            teh = r['tehnicna_ocena']
            eko = r['ekonomska_ocena']
            soc = r['socialna_ocena']
            
            linije.extend([
                "",
                "┌" + "─" * (sirina - 2) + "┐",
                "│" + " DETAILED SCORES ".center(sirina - 2) + "│",
                "├" + "─" * (sirina - 2) + "┤",
            ])
            
            # Tehnicna
            t_bar = "█" * int(teh / 5) + "░" * (20 - int(teh / 5))
            linije.append("│" + f"   Technical:  [{t_bar}] {teh:.1f}".ljust(sirina - 2) + "│")
            
            # Ekonomska
            e_bar = "█" * int(eko / 5) + "░" * (20 - int(eko / 5))
            linije.append("│" + f"   Economic:   [{e_bar}] {eko:.1f}".ljust(sirina - 2) + "│")
            
            # Socialna
            s_bar = "█" * int(soc / 5) + "░" * (20 - int(soc / 5))
            linije.append("│" + f"   Social:     [{s_bar}] {soc:.1f}".ljust(sirina - 2) + "│")
            
            linije.append("└" + "─" * (sirina - 2) + "┘")
            
            # Metrike
            teh_met = r.get('tehnicne_metrike', {})
            eko_met = r.get('ekonomske_metrike', {})
            soc_met = r.get('socialne_metrike', {})
            
            if teh_met:
                linije.extend([
                    "",
                    "┌" + "─" * (sirina - 2) + "┐",
                    "│" + " TECHNICAL METRICS ".center(sirina - 2) + "│",
                    "├" + "─" * (sirina - 2) + "┤",
                ])
                for k, v in teh_met.items():
                    ime_met = k.replace('_', ' ').title()
                    linije.append("│" + f"   {ime_met}: {v:.1f}/10".ljust(sirina - 2) + "│")
                linije.append("└" + "─" * (sirina - 2) + "┘")
            
            if eko_met:
                linije.extend([
                    "",
                    "┌" + "─" * (sirina - 2) + "┐",
                    "│" + " ECONOMIC METRICS ".center(sirina - 2) + "│",
                    "├" + "─" * (sirina - 2) + "┤",
                ])
                for k, v in eko_met.items():
                    ime_met = k.replace('_', ' ').title()
                    linije.append("│" + f"   {ime_met}: {v:.1f}/10".ljust(sirina - 2) + "│")
                linije.append("└" + "─" * (sirina - 2) + "┘")
            
            if soc_met:
                linije.extend([
                    "",
                    "┌" + "─" * (sirina - 2) + "┐",
                    "│" + " SOCIAL METRICS ".center(sirina - 2) + "│",
                    "├" + "─" * (sirina - 2) + "┤",
                ])
                for k, v in soc_met.items():
                    ime_met = k.replace('_', ' ').title()
                    linije.append("│" + f"   {ime_met}: {v:.1f}/10".ljust(sirina - 2) + "│")
                linije.append("└" + "─" * (sirina - 2) + "┘")
            
            # Prednosti in slabosti
            prednosti = r.get('prednosti', [])
            slabosti = r.get('slabosti', [])
            
            if prednosti or slabosti:
                linije.extend([
                    "",
                    "┌" + "─" * (sirina - 2) + "┐",
                    "│" + " ASSESSMENT ".center(sirina - 2) + "│",
                    "├" + "─" * (sirina - 2) + "┤",
                ])
                
                if prednosti:
                    linije.append("│" + "   ✅ Strengths:".ljust(sirina - 2) + "│")
                    for p in prednosti:
                        linije.append("│" + f"      • {p}".ljust(sirina - 2) + "│")
                
                if slabosti:
                    if prednosti:
                        linije.append("│" + "".ljust(sirina - 2) + "│")
                    linije.append("│" + "   ⚠️ Weaknesses:".ljust(sirina - 2) + "│")
                    for s in slabosti:
                        linije.append("│" + f"      • {s}".ljust(sirina - 2) + "│")
                
                linije.append("└" + "─" * (sirina - 2) + "┘")
            
            # Opozorila
            opozorila = r.get('opozorila', [])
            rdece = r.get('rdeci_zastavice', [])
            
            if opozorila or rdece:
                linije.extend([
                    "",
                    "┌" + "─" * (sirina - 2) + "┐",
                    "│" + " WARNINGS ".center(sirina - 2) + "│",
                    "├" + "─" * (sirina - 2) + "┤",
                ])
                for o in opozorila:
                    linije.append("│" + f"   ⚡ {o}".ljust(sirina - 2) + "│")
                for z in rdece:
                    linije.append("│" + f"   🚨 {z}".ljust(sirina - 2) + "│")
                linije.append("└" + "─" * (sirina - 2) + "┘")
        
        # Footer
        linije.extend([
            "",
            "─" * sirina,
            f"Generated: {r['cas_analize']}",
            f"Scam Probability: {r.get('verjetnost_prevare', 0)*100:.1f}%",
            "─" * sirina,
            ""
        ])
        
        return "\n".join(linije)
    
    def batch_analiziraj(self, identifikatorji: List[str]) -> List[Dict]:
        """
        Analiziraj vec kovancev naenkrat.
        
        Args:
            identifikatorji: Seznam coin ID-jev ali simbolov
        
        Returns:
            Seznam rezultatov
        """
        rezultati = []
        
        for i, ident in enumerate(identifikatorji, 1):
            print(f"[{i}/{len(identifikatorji)}] Analiziram {ident}...")
            
            try:
                rezultat = self.klasificiraj(ident)
                rezultati.append(rezultat)
            except Exception as e:
                print(f"  Napaka pri {ident}: {e}")
                rezultati.append({
                    'ime': ident,
                    'napaka': str(e)
                })
        
        return rezultati


# ============================================================================
# Pomocna funkcija za hitro uporabo
# ============================================================================

def analiziraj_kovanec(identifikator: str, api_kljuc: str = None) -> Dict:
    """
    Hitra funkcija za analizo posameznega kovanca.
    
    Primer uporabe:
        rezultat = analiziraj_kovanec('bitcoin')
        print(rezultat['koncna_ocena'])
    """
    klasifikator = KriptoKlasifikator(api_kljuc=api_kljuc)
    return klasifikator.klasificiraj(identifikator)
