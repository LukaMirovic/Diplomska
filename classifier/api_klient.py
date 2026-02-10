"""
API klient za CoinGecko.
Skrbi za vse HTTP zahteve in obdelavo odgovorov.
Brez fallbackov - ce ni podatkov, vrze napako.
"""

import os
import time
import requests
from typing import Dict, Optional
from dotenv import load_dotenv

# Nalozi .env datoteko
load_dotenv()


class CoinGeckoKlient:
    """
    Klient za komunikacijo s CoinGecko API-jem.
    Ima vgrajeno omejitev hitrosti da ne dobimo bana.
    """
    
    BAZNI_URL = "https://api.coingecko.com/api/v3"
    
    def __init__(self, api_kljuc: Optional[str] = None):
        self.seja = requests.Session()
        # Uporabi API kljuc iz .env, ce ni podan direktno
        self.api_kljuc = api_kljuc or os.getenv('COINGECKO_API_KEY')
        
        # Nastavi headerje
        headerji = {'User-Agent': 'KriptoKlasifikator/2.0 (Diplomska naloga FRI)'}
        
        if api_kljuc:
            headerji['x-cg-demo-api-key'] = api_kljuc
            print("✓ Uporablja se CoinGecko API kljuc")
            self._zakasnitev = 0.5
            self._max_ponovitev = 5
        else:
            print("⚠ Brez API kljuca - omejitve hitrosti veljajo")
            print("  Brezplacni kljuc: https://www.coingecko.com/en/api")
            self._zakasnitev = 6.0  # 10 zahtev na minuto = 6 sekund med zahtevami
            self._max_ponovitev = 3
        
        self.seja.headers.update(headerji)
        self._zadnja_zahteva = 0
    
    def _pocakaj_rate_limit(self):
        """Pocaka dovolj casa med zahtevami."""
        preteceno = time.time() - self._zadnja_zahteva
        if preteceno < self._zakasnitev:
            time.sleep(self._zakasnitev - preteceno)
        self._zadnja_zahteva = time.time()
    
    def _izvedi_zahtevo(self, url: str, parametri: Dict = None) -> Dict:
        """
        Izvede HTTP zahtevo z obdelavo napak.
        Vrze napako ce ne uspe dobiti podatkov.
        """
        if parametri is None:
            parametri = {}
        
        for poskus in range(self._max_ponovitev):
            try:
                self._pocakaj_rate_limit()
                
                odgovor = self.seja.get(url, params=parametri, timeout=30)
                
                # Ce smo dobili rate limit, pocakamo in poskusimo znova
                if odgovor.status_code == 429:
                    cas_cakanja = 65 + (poskus * 30)  # Vedno dlje cakamo
                    print(f"  ⚠ Rate limit (poskus {poskus+1}/{self._max_ponovitev}) - cakam {cas_cakanja}s...")
                    time.sleep(cas_cakanja)
                    continue
                
                if odgovor.status_code == 404:
                    return None  # Kovanec ne obstaja
                
                odgovor.raise_for_status()
                return odgovor.json()
                
            except requests.exceptions.HTTPError as e:
                if poskus < self._max_ponovitev - 1:
                    print(f"  HTTP napaka (poskus {poskus+1}): {e}")
                    time.sleep(10)
                    continue
                raise RuntimeError(f"HTTP napaka po {self._max_ponovitev} poskusih: {e}")
                
            except requests.exceptions.RequestException as e:
                if poskus < self._max_ponovitev - 1:
                    print(f"  Napaka pri zahtevi (poskus {poskus+1}): {e}")
                    time.sleep(10)
                    continue
                raise RuntimeError(f"Napaka pri zahtevi po {self._max_ponovitev} poskusih: {e}")
        
        raise RuntimeError(f"Ni uspelo dobiti podatkov po {self._max_ponovitev} poskusih (rate limit)")
    
    def poisci_kovanec(self, poizvedba: str) -> Optional[str]:
        """
        Poisce kovanec in vrne njegov CoinGecko ID.
        Najprej proba exact match, sicer vzame prvi rezultat.
        """
        url = f"{self.BAZNI_URL}/search"
        podatki = self._izvedi_zahtevo(url, {'query': poizvedba})
        
        if not podatki or not podatki.get('coins'):
            return None
        
        kovanci = podatki['coins']
        
        # Najprej isci tocno ujemanje
        for kovanec in kovanci:
            simbol = kovanec.get('symbol', '').lower()
            ime = kovanec.get('name', '').lower()
            id_kov = kovanec.get('id', '').lower()
            
            if poizvedba.lower() in [simbol, ime, id_kov]:
                print(f"  Najden: {kovanec.get('name')} ({simbol.upper()})")
                return kovanec['id']
        
        # Sicer vzemi prvega
        najden = kovanci[0]
        print(f"  Najden: {najden.get('name')} ({najden.get('symbol', '').upper()})")
        
        return najden['id']
    
    def pridobi_podatke_kovanca(self, identifikator: str) -> Dict:
        """
        Pridobi vse podatke o kovancu.
        Vrze napako ce ne uspe.
        """
        print(f"  Iscem: {identifikator}")
        
        # Najprej probaj direkten dostop
        id_kovanca = identifikator.lower().replace(' ', '-')
        podatki_kovanca = self._dobi_podrobnosti(id_kovanca)
        
        # Ce ni uspelo, probaj z iskanjem
        if not podatki_kovanca or 'error' in podatki_kovanca:
            id_kovanca = self.poisci_kovanec(identifikator)
            if not id_kovanca:
                raise ValueError(f"Kovanec '{identifikator}' ni najden")
            podatki_kovanca = self._dobi_podrobnosti(id_kovanca)
        
        if not podatki_kovanca:
            raise ValueError(f"Ni podatkov za kovanec '{identifikator}'")
        
        # Pridobi se trzne podatke
        trzni_podatki = self._dobi_trzne_podatke(id_kovanca)
        
        # Preveri da imamo kljucne podatke
        trzni_info = podatki_kovanca.get('market_data', {})
        rang = trzni_podatki.get('market_cap_rank') or trzni_info.get('market_cap_rank')
        
        if not rang:
            raise ValueError(f"Manjka market cap rank za '{identifikator}' - nepopolni podatki")
        
        return {
            'basic_info': podatki_kovanca,
            'market_data': trzni_podatki,
            'coin_id': id_kovanca
        }
    
    def _dobi_podrobnosti(self, id_kovanca: str) -> Optional[Dict]:
        """Pridobi podrobne informacije o kovancu."""
        url = f"{self.BAZNI_URL}/coins/{id_kovanca}"
        parametri = {
            'localization': 'false',
            'tickers': 'true',
            'market_data': 'true',
            'community_data': 'true',
            'developer_data': 'true',
            'sparkline': 'false'
        }
        return self._izvedi_zahtevo(url, parametri)
    
    def _dobi_trzne_podatke(self, id_kovanca: str) -> Dict:
        """Pridobi trzne podatke (cena, volume, market cap...)."""
        url = f"{self.BAZNI_URL}/coins/markets"
        parametri = {
            'vs_currency': 'usd',
            'ids': id_kovanca,
            'order': 'market_cap_desc',
            'sparkline': 'false',
            'price_change_percentage': '1h,24h,7d,30d'
        }
        
        podatki = self._izvedi_zahtevo(url, parametri)
        
        # Markets vrne seznam, vzamemo prvi element
        if podatki and len(podatki) > 0:
            return podatki[0]
        return {}
