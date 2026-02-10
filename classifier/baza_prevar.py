"""
Upravljanje baze podatkov o znanih prevarah.
Nalozi podatke iz JSON fajla in omogoca preverjanje.
"""

import json
from pathlib import Path
from typing import Dict, Optional, Tuple


class UpravljalecBazePrevar:
    """
    Razred za delo z bazo znanih prevar.
    Podatki se hranijo v JSON formatu ker je preprost za urejanje.
    """
    
    def __init__(self, pot_do_konfiga: Optional[str] = None):
        self.pot_do_konfiga = pot_do_konfiga or self._najdi_konfig()
        
        # Slovarji za razlicne podatke
        self.znane_prevare: Dict = {}
        self.tipi_prevar: Dict = {}
        self.vzorci_rdecih_zastavic: Dict = {}
        self.pragovi_trzne_kap: Dict = {}
        
        self._nalozi_bazo()
    
    def _najdi_konfig(self) -> str:
        """
        Poisce JSON datoteko s podatki o prevarah.
        Pogleda na vec lokacij - v mapi classifier, v root mapi, itd.
        """
        mozne_poti = [
            Path(__file__).parent.parent / "scam_indicators.json",
            Path(__file__).parent / "scam_indicators.json",
            Path.cwd() / "scam_indicators.json",
        ]
        
        for pot in mozne_poti:
            if pot.exists():
                return str(pot)
        
        # Ce ne najde, vrni privzeto pot - bo pac prazna baza
        return str(mozne_poti[0])
    
    def _nalozi_bazo(self):
        """Nalozi podatke iz JSON datoteke."""
        try:
            if Path(self.pot_do_konfiga).exists():
                with open(self.pot_do_konfiga, 'r', encoding='utf-8') as f:
                    podatki = json.load(f)
                    
                self.znane_prevare = podatki.get('known_scam_coins', {})
                self.tipi_prevar = podatki.get('scam_type_definitions', {})
                self.vzorci_rdecih_zastavic = podatki.get('red_flag_patterns', {})
                self.pragovi_trzne_kap = podatki.get('market_cap_thresholds', {})
                
                print(f"✓ Nalozena baza z {len(self.znane_prevare)} znanimi prevarami")
            else:
                print(f"⚠ Baza prevar ne obstaja na {self.pot_do_konfiga}")
                
        except Exception as e:
            print(f"⚠ Napaka pri nalaganju baze: {e}")
    
    def je_znana_prevara(self, id_kovanca: str) -> Tuple[bool, Optional[Dict]]:
        """
        Preveri ce je kovanec v bazi znanih prevar.
        Proba razlicne oblike ID-ja (z vezaji, brez, male crke...).
        """
        # Normaliziraj ID za iskanje
        normaliziran = id_kovanca.lower().replace(' ', '-').replace('_', '-')
        
        # Probaj razlicne variante
        for kljuc in [normaliziran, id_kovanca.lower(), id_kovanca]:
            if kljuc in self.znane_prevare:
                return True, self.znane_prevare[kljuc]
        
        # Preveri se po imenu ali simbolu v vrednostih
        for kljuc, podatki in self.znane_prevare.items():
            ime = podatki.get('name', '').lower()
            simbol = podatki.get('symbol', '').lower()
            
            if ime == id_kovanca.lower() or simbol == id_kovanca.lower():
                return True, podatki
        
        return False, None
    
    def dobi_info_o_tipu(self, tip_prevare: str) -> Optional[Dict]:
        """Vrne informacije o dolocenem tipu prevare."""
        return self.tipi_prevar.get(tip_prevare)
    
    def dobi_mnozitelj_tveganja(self, trzna_kap: float) -> float:
        """
        Vrne mnozitelj tveganja glede na trzno kapitalizacijo.
        Manjsi coini so bolj tvegani za manipulacijo.
        """
        if not trzna_kap or not self.pragovi_trzne_kap:
            return 1.2  # Privzeto povecano tveganje
        
        # Sortiraj po max vrednosti in najdi ustrezen razred
        for razred, info in sorted(
            self.pragovi_trzne_kap.items(),
            key=lambda x: x[1].get('max_usd', float('inf')) or float('inf')
        ):
            max_usd = info.get('max_usd')
            if max_usd is None or trzna_kap <= max_usd:
                return info.get('risk_multiplier', 1.0)
        
        return 1.0
    
    def dodaj_prevaro(self, id_kovanca: str, podatki_prevare: Dict):
        """Doda novo prevaro v bazo in shrani."""
        self.znane_prevare[id_kovanca.lower()] = podatki_prevare
        self._shrani_bazo()
    
    def _shrani_bazo(self):
        """Shrani bazo nazaj v JSON datoteko."""
        try:
            podatki = {
                'known_scam_coins': self.znane_prevare,
                'scam_type_definitions': self.tipi_prevar,
                'red_flag_patterns': self.vzorci_rdecih_zastavic,
                'market_cap_thresholds': self.pragovi_trzne_kap
            }
            
            with open(self.pot_do_konfiga, 'w', encoding='utf-8') as f:
                json.dump(podatki, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠ Napaka pri shranjevanju baze: {e}")
