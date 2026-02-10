"""
Podatkovni modeli za klasifikator kriptovalut.
Tukaj so definirane vse strukture podatkov ki jih rabimo.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


# ============================================================================
# Enum razredi - kategorije in stopnje tveganja
# ============================================================================

class StopnjaTveganja(Enum):
    """
    Stopnje tveganja projekta.
    Uporabljam angleške vrednosti ker se tako prikažejo v reportu.
    """
    ZELO_NIZKO = "Very Low Risk"
    NIZKO = "Low Risk"
    SREDNJE = "Moderate Risk"
    VISOKO = "High Risk"
    ZELO_VISOKO = "Very High Risk"
    KRITICNO = "Critical Risk - Likely Scam"


class TipPrevare(Enum):
    """
    Tipi kripto prevar ki jih poznamo.
    Seznam sem sestavil na podlagi literature in realnih primerov.
    """
    PONZIJEVA_SHEMA = "Ponzi Scheme"
    RUG_PULL = "Rug Pull"
    PUMP_AND_DUMP = "Pump and Dump"
    ALGORITMICNA_NAPAKA = "Algorithmic Failure"
    SUMLJIVA_PONZI = "Suspected Ponzi"
    TVEGANJE_BORZE = "Exchange Token Risk"
    HONEYPOT = "Honeypot"
    NEZNANO = "Unknown/Not Classified"


class KategorijaProjekta(Enum):
    """
    Kategorije projektov po metodologiji iz diplomske.
    Layer 1 = lastna veriga, Quality Token = brez lastne verige ampak legit,
    Problematicen = scam ali zelo sumljiv.
    """
    LAYER_1 = "Layer 1 - Own Blockchain"
    KVALITETEN_TOKEN = "Quality Token - No Own Chain"
    PROBLEMATICEN = "Problematic/Scam Project"
    NEKATEGORIZIRAN = "Uncategorized"


# ============================================================================
# Metrike - tehnicne, ekonomske, socialne
# ============================================================================

@dataclass
class TehnicneMetrike:
    """
    Tehnicni kazalniki projekta.
    Vsak parameter je ocena od 0-10, potem se izracuna utezeno povprecje.
    """
    dostopnost_kode: float = 0.0
    kvaliteta_arhitekture: float = 0.0
    decentralizacija: float = 0.0
    varnostni_mehanizmi: float = 0.0
    status_revizije: float = 0.0
    tveganje_pogodbe: float = 5.0  # relevantno samo za tokene
    
    def izracunaj_oceno(self) -> float:
        """
        Izracuna skupno tehnicno oceno.
        Utezi sem dolocil na podlagi pomembnosti posameznega faktorja.
        """
        utezi = {
            'koda': 0.15,
            'arhitektura': 0.18,
            'decentralizacija': 0.22,
            'varnost': 0.22,
            'revizija': 0.13,
            'pogodba': 0.10
        }
        
        ocena = (
            self.dostopnost_kode * utezi['koda'] +
            self.kvaliteta_arhitekture * utezi['arhitektura'] +
            self.decentralizacija * utezi['decentralizacija'] +
            self.varnostni_mehanizmi * utezi['varnost'] +
            self.status_revizije * utezi['revizija'] +
            self.tveganje_pogodbe * utezi['pogodba']
        )
        return ocena * 10
    
    def v_slovar(self) -> Dict:
        """Za export v JSON."""
        return {
            'dostopnost_kode': self.dostopnost_kode,
            'kvaliteta_arhitekture': self.kvaliteta_arhitekture,
            'decentralizacija': self.decentralizacija,
            'varnostni_mehanizmi': self.varnostni_mehanizmi,
            'status_revizije': self.status_revizije,
            'tveganje_pogodbe': self.tveganje_pogodbe
        }


@dataclass
class EkonomskeMetrike:
    """
    Ekonomski in tokenomski kazalniki.
    Pomembni za oceno dolgorocne vzdrznosti projekta.
    """
    pravicnost_distribucije: float = 0.0
    mehanizem_inflacije: float = 0.0
    vesting_urnik: float = 0.0
    koncentracija_lastnistva: float = 0.0
    globina_likvidnosti: float = 0.0
    indikatorji_manipulacije: float = 0.0
    vzdrznost_tokenomike: float = 5.0
    
    def izracunaj_oceno(self) -> float:
        """Izracun ekonomske ocene z utezenimi faktorji."""
        utezi = {
            'distribucija': 0.18,
            'inflacija': 0.12,
            'vesting': 0.15,
            'koncentracija': 0.20,
            'likvidnost': 0.15,
            'manipulacija': 0.12,
            'vzdrznost': 0.08
        }
        
        ocena = (
            self.pravicnost_distribucije * utezi['distribucija'] +
            self.mehanizem_inflacije * utezi['inflacija'] +
            self.vesting_urnik * utezi['vesting'] +
            self.koncentracija_lastnistva * utezi['koncentracija'] +
            self.globina_likvidnosti * utezi['likvidnost'] +
            self.indikatorji_manipulacije * utezi['manipulacija'] +
            self.vzdrznost_tokenomike * utezi['vzdrznost']
        )
        return ocena * 10
    
    def v_slovar(self) -> Dict:
        """Za export v JSON."""
        return {
            'pravicnost_distribucije': self.pravicnost_distribucije,
            'mehanizem_inflacije': self.mehanizem_inflacije,
            'vesting_urnik': self.vesting_urnik,
            'koncentracija_lastnistva': self.koncentracija_lastnistva,
            'globina_likvidnosti': self.globina_likvidnosti,
            'indikatorji_manipulacije': self.indikatorji_manipulacije,
            'vzdrznost_tokenomike': self.vzdrznost_tokenomike
        }


@dataclass
class SocialneMetrike:
    """
    Socialni kazalniki - ekipa, skupnost, dokumentacija.
    Pri scamih je to pogosto najslabse ocenjeno.
    """
    transparentnost_ekipe: float = 0.0
    izkusenost_ekipe: float = 0.0
    kvaliteta_dokumentacije: float = 0.0
    angaziranost_skupnosti: float = 0.0
    pristop_marketinga: float = 0.0
    prisotnost_na_omrezjih: float = 0.0
    zdravje_skupnosti: float = 5.0
    
    def izracunaj_oceno(self) -> float:
        """Izracun socialne ocene."""
        utezi = {
            'transparentnost': 0.22,
            'izkusenost': 0.18,
            'dokumentacija': 0.18,
            'angaziranost': 0.15,
            'marketing': 0.10,
            'prisotnost': 0.08,
            'zdravje': 0.09
        }
        
        ocena = (
            self.transparentnost_ekipe * utezi['transparentnost'] +
            self.izkusenost_ekipe * utezi['izkusenost'] +
            self.kvaliteta_dokumentacije * utezi['dokumentacija'] +
            self.angaziranost_skupnosti * utezi['angaziranost'] +
            self.pristop_marketinga * utezi['marketing'] +
            self.prisotnost_na_omrezjih * utezi['prisotnost'] +
            self.zdravje_skupnosti * utezi['zdravje']
        )
        return ocena * 10
    
    def v_slovar(self) -> Dict:
        """Za export v JSON."""
        return {
            'transparentnost_ekipe': self.transparentnost_ekipe,
            'izkusenost_ekipe': self.izkusenost_ekipe,
            'kvaliteta_dokumentacije': self.kvaliteta_dokumentacije,
            'angaziranost_skupnosti': self.angaziranost_skupnosti,
            'pristop_marketinga': self.pristop_marketinga,
            'prisotnost_na_omrezjih': self.prisotnost_na_omrezjih,
            'zdravje_skupnosti': self.zdravje_skupnosti
        }


@dataclass
class IndikatorjiPrevare:
    """
    Zdruzeni indikatorji prevar.
    Tukaj zbiramo vse warning znake ki jih najdemo med analizo.
    """
    je_znana_prevara: bool = False
    tip_prevare: TipPrevare = TipPrevare.NEZNANO
    verjetnost_prevare: float = 0.0
    rdeci_zastavice: List[str] = field(default_factory=list)
    opozorila: List[str] = field(default_factory=list)
    podatki_znane_prevare: Optional[Dict] = None
