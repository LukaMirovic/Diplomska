"""
Classifier modul za analizo kriptovalut.

Uporaba:
    from classifier import KriptoKlasifikator, analiziraj_kovanec
    
    # Opcija 1: preko razreda
    klasifikator = KriptoKlasifikator()
    rezultat = klasifikator.klasificiraj('bitcoin')
    
    # Opcija 2: hitra funkcija
    rezultat = analiziraj_kovanec('ethereum')
"""

from .models import (
    TehnicneMetrike,
    EkonomskeMetrike,
    SocialneMetrike,
    IndikatorjiPrevare,
    StopnjaTveganja,
    TipPrevare,
    KategorijaProjekta
)
from .baza_prevar import UpravljalecBazePrevar
from .api_klient import CoinGeckoKlient
from .analizatorji import AnalizatorMetrik
from .klasifikator import KriptoKlasifikator, analiziraj_kovanec

__all__ = [
    # Glavni razredi
    'KriptoKlasifikator',
    'AnalizatorMetrik',
    'CoinGeckoKlient',
    'UpravljalecBazePrevar',
    
    # Podatkovni modeli
    'TehnicneMetrike',
    'EkonomskeMetrike',
    'SocialneMetrike',
    'IndikatorjiPrevare',
    
    # Enumi
    'StopnjaTveganja',
    'TipPrevare',
    'KategorijaProjekta',
    
    # Pomocne funkcije
    'analiziraj_kovanec',
]

__version__ = '1.0.0'
