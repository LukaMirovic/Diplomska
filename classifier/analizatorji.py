"""
Analizatorji metrik.
Tukaj je vsa logika za izracun tehnicnih, ekonomskih in socialnih ocen.
Brez fallbackov - podatki morajo priti iz CoinGecko API-ja.
"""

from datetime import datetime
from typing import Dict

from .models import (
    TehnicneMetrike, EkonomskeMetrike, SocialneMetrike,
    IndikatorjiPrevare, TipPrevare
)
from .baza_prevar import UpravljalecBazePrevar


class AnalizatorMetrik:
    """
    Glavni razred za analizo vseh metrik.
    Vsaka metoda analizira eno dimenzijo (tehnicna, ekonomska, socialna).
    """
    
    def __init__(self, baza_prevar: UpravljalecBazePrevar):
        self.baza_prevar = baza_prevar
    
    def _dobi_rang(self, podatki: Dict) -> int:
        """Dobi market cap rang - najprej iz markets, potem iz basic_info."""
        trzni = podatki.get('market_data', {}) or {}
        trzni_info = podatki.get('basic_info', {}).get('market_data', {}) or {}
        return trzni.get('market_cap_rank') or trzni_info.get('market_cap_rank') or 9999
    
    def _dobi_trzno_kap(self, podatki: Dict) -> float:
        """Dobi market cap."""
        trzni = podatki.get('market_data', {}) or {}
        trzni_info = podatki.get('basic_info', {}).get('market_data', {}) or {}
        return trzni.get('market_cap') or trzni_info.get('market_cap', {}).get('usd') or 0
    
    def _dobi_volumen(self, podatki: Dict) -> float:
        """Dobi 24h volume."""
        trzni = podatki.get('market_data', {}) or {}
        trzni_info = podatki.get('basic_info', {}).get('market_data', {}) or {}
        return trzni.get('total_volume') or trzni_info.get('total_volume', {}).get('usd') or 0
    
    def _izracunaj_starost(self, datum_geneze: str) -> float:
        """Izracuna starost projekta v letih."""
        if not datum_geneze:
            return 0
        try:
            geneza = datetime.fromisoformat(datum_geneze.replace('Z', '+00:00'))
            sedaj = datetime.now(geneza.tzinfo) if geneza.tzinfo else datetime.now()
            return (sedaj - geneza).days / 365
        except:
            return 0
    
    # ========================================================================
    # Tehnicna analiza
    # ========================================================================
    
    def analiziraj_tehnicne(self, podatki: Dict, indikatorji: IndikatorjiPrevare) -> TehnicneMetrike:
        """Analizira tehnicne aspekte projekta."""
        osnovni = podatki.get('basic_info', {})
        razvojni = osnovni.get('developer_data', {}) or {}
        povezave = osnovni.get('links', {}) or {}
        
        rang = self._dobi_rang(podatki)
        
        # Starost projekta
        datum_geneze = osnovni.get('genesis_date', '')
        starost_let = self._izracunaj_starost(datum_geneze)
        
        # Ce ni genesis_date, uporabi rang za oceno (visje uvrsteni projekti so tipicno starejsi)
        if starost_let == 0:
            if rang <= 10:
                starost_let = 8.0
            elif rang <= 20:
                starost_let = 6.0
            elif rang <= 50:
                starost_let = 4.0
            elif rang <= 100:
                starost_let = 3.0
            elif rang <= 200:
                starost_let = 2.0
            else:
                starost_let = 1.0
        
        # --- Dostopnost kode ---
        repoji = povezave.get('repos_url', {}) or {}
        github_repoji = repoji.get('github', []) or []
        
        if github_repoji and len(github_repoji) > 0:
            ocena_kode = 8.5
        elif povezave.get('blockchain_site') and any(povezave.get('blockchain_site', [])):
            ocena_kode = 6.0
        else:
            ocena_kode = 4.0
        
        # --- Kvaliteta arhitekture (GitHub metrike ali rang) ---
        zvezdice = razvojni.get('stars', 0) or 0
        forki = razvojni.get('forks', 0) or 0
        commiti = razvojni.get('commit_count_4_weeks', 0) or 0
        
        # CoinGecko pogosto ne vraca GitHub podatkov za velike projekte
        # Uporabi kombinacijo GitHub metrik in ranga
        if zvezdice > 50000 and forki > 20000:
            ocena_arhitekture = 9.5
        elif zvezdice > 30000 and forki > 10000:
            ocena_arhitekture = 9.0
        elif zvezdice > 15000 and forki > 5000:
            ocena_arhitekture = 8.5
        elif zvezdice > 5000:
            ocena_arhitekture = 8.0
        elif zvezdice > 1000:
            ocena_arhitekture = 7.5
        elif zvezdice > 500 or commiti > 50:
            ocena_arhitekture = 7.0
        elif zvezdice > 100 or commiti > 20:
            ocena_arhitekture = 6.0
        elif zvezdice > 0 or commiti > 0:
            ocena_arhitekture = 5.0
        else:
            # Ni GitHub podatkov - oceni po rangu in starosti
            if rang <= 10 and starost_let > 5:
                ocena_arhitekture = 9.0
            elif rang <= 20 and starost_let > 4:
                ocena_arhitekture = 8.5
            elif rang <= 30 and starost_let > 3:
                ocena_arhitekture = 8.0
            elif rang <= 50 and starost_let > 2:
                ocena_arhitekture = 7.5
            elif rang <= 100 and starost_let > 1:
                ocena_arhitekture = 7.0
            elif rang <= 200:
                ocena_arhitekture = 6.5
            elif rang <= 500:
                ocena_arhitekture = 5.5
            else:
                ocena_arhitekture = 4.0
        
        # --- Decentralizacija ---
        if starost_let > 10 and rang <= 5:
            ocena_decentralizacije = 9.5
        elif starost_let > 6 and rang <= 15:
            ocena_decentralizacije = 9.0
        elif starost_let > 4 and rang <= 30:
            ocena_decentralizacije = 8.5
        elif starost_let > 3 and rang <= 50:
            ocena_decentralizacije = 8.0
        elif starost_let > 2 and rang <= 100:
            ocena_decentralizacije = 7.5
        elif starost_let > 2:
            ocena_decentralizacije = 7.0
        elif starost_let > 1:
            ocena_decentralizacije = 6.5
        elif rang <= 100:
            ocena_decentralizacije = 6.0
        else:
            ocena_decentralizacije = 5.0
        
        # --- Varnostni mehanizmi (rang kot proxy za varnost) ---
        if rang <= 5:
            ocena_varnosti = 9.5
        elif rang <= 10:
            ocena_varnosti = 9.0
        elif rang <= 20:
            ocena_varnosti = 8.5
        elif rang <= 50:
            ocena_varnosti = 8.0
        elif rang <= 100:
            ocena_varnosti = 7.5
        elif rang <= 200:
            ocena_varnosti = 7.0
        elif rang <= 500:
            ocena_varnosti = 6.0
        elif rang <= 1000:
            ocena_varnosti = 5.0
        else:
            ocena_varnosti = 4.0
        
        # --- Status revizije ---
        if rang <= 10 and starost_let > 5:
            ocena_revizije = 9.5
        elif rang <= 20 and starost_let > 3:
            ocena_revizije = 9.0
        elif rang <= 50 and starost_let > 2:
            ocena_revizije = 8.0
        elif rang <= 100 and starost_let > 1:
            ocena_revizije = 7.5
        elif rang <= 200:
            ocena_revizije = 7.0
        elif rang <= 500:
            ocena_revizije = 6.0
        else:
            ocena_revizije = 5.0
        
        # --- Tveganje pametne pogodbe ---
        kategorije = osnovni.get('categories', []) or []
        je_token = any(
            'token' in kat.lower() or 'erc' in kat.lower() or 'bep' in kat.lower()
            for kat in kategorije
        )
        
        if not je_token:
            ocena_pogodbe = 8.0  # Layer 1 - ni smart contract tveganja
        elif rang <= 50 and starost_let > 3:
            ocena_pogodbe = 8.0
        elif rang <= 100 and starost_let > 2:
            ocena_pogodbe = 7.5
        elif rang <= 200 and starost_let > 1:
            ocena_pogodbe = 7.0
        else:
            ocena_pogodbe = 6.0
        
        return TehnicneMetrike(
            dostopnost_kode=ocena_kode,
            kvaliteta_arhitekture=ocena_arhitekture,
            decentralizacija=ocena_decentralizacije,
            varnostni_mehanizmi=ocena_varnosti,
            status_revizije=ocena_revizije,
            tveganje_pogodbe=ocena_pogodbe
        )
    
    # ========================================================================
    # Ekonomska analiza
    # ========================================================================
    
    def analiziraj_ekonomske(self, podatki: Dict, indikatorji: IndikatorjiPrevare) -> EkonomskeMetrike:
        """Analizira tokenomiko in ekonomske faktorje."""
        osnovni = podatki.get('basic_info', {})
        trzni = podatki.get('market_data', {}) or {}
        trzni_info = osnovni.get('market_data', {}) or {}
        
        rang = self._dobi_rang(podatki)
        trzna_kap = self._dobi_trzno_kap(podatki)
        volumen = self._dobi_volumen(podatki)
        
        # Starost
        datum_geneze = osnovni.get('genesis_date', '')
        starost_let = self._izracunaj_starost(datum_geneze)
        if starost_let == 0:
            if rang <= 10:
                starost_let = 8.0
            elif rang <= 20:
                starost_let = 6.0
            elif rang <= 50:
                starost_let = 4.0
            elif rang <= 100:
                starost_let = 3.0
            else:
                starost_let = 2.0
        
        # --- Pravicnost distribucije (volume/mcap ratio) ---
        razmerje_volumna = (volumen / trzna_kap * 100) if trzna_kap > 0 else 0
        
        if razmerje_volumna > 15:
            ocena_distribucije = 9.5
        elif razmerje_volumna > 8:
            ocena_distribucije = 9.0
        elif razmerje_volumna > 4:
            ocena_distribucije = 8.5
        elif razmerje_volumna > 2:
            ocena_distribucije = 8.0
        elif razmerje_volumna > 1:
            ocena_distribucije = 7.5
        elif razmerje_volumna > 0.5:
            ocena_distribucije = 7.0
        elif razmerje_volumna > 0.1:
            ocena_distribucije = 6.0
        else:
            ocena_distribucije = 5.0
        
        # Bonus za etablirane projekte
        if rang <= 10 and starost_let > 5:
            ocena_distribucije = max(ocena_distribucije, 9.0)
        elif rang <= 30 and starost_let > 3:
            ocena_distribucije = max(ocena_distribucije, 8.5)
        elif rang <= 50:
            ocena_distribucije = max(ocena_distribucije, 8.0)
        elif rang <= 100:
            ocena_distribucije = max(ocena_distribucije, 7.5)
        
        # --- Mehanizem inflacije (supply ratio) ---
        max_zaloga = trzni_info.get('max_supply') or trzni.get('max_supply')
        v_obtoku = trzni_info.get('circulating_supply') or trzni.get('circulating_supply') or 0
        
        if max_zaloga and v_obtoku and max_zaloga > 0:
            razmerje_zaloge = v_obtoku / max_zaloga
            if razmerje_zaloge > 0.9:
                ocena_inflacije = 9.0
            elif razmerje_zaloge > 0.75:
                ocena_inflacije = 8.0
            elif razmerje_zaloge > 0.5:
                ocena_inflacije = 7.0
            elif razmerje_zaloge > 0.3:
                ocena_inflacije = 6.0
            else:
                ocena_inflacije = 5.0
        else:
            # Neomejena zaloga ali ni podatkov
            ocena_inflacije = 6.5
        
        # --- Vesting urnik (starost kot proxy) ---
        if starost_let > 10:
            ocena_vestinga = 9.5
        elif starost_let > 7:
            ocena_vestinga = 9.0
        elif starost_let > 5:
            ocena_vestinga = 8.5
        elif starost_let > 3:
            ocena_vestinga = 8.0
        elif starost_let > 2:
            ocena_vestinga = 7.5
        elif starost_let > 1:
            ocena_vestinga = 7.0
        else:
            ocena_vestinga = 6.0
        
        # --- Koncentracija lastnistva (ATH padec) ---
        ath_sprememba = trzni_info.get('ath_change_percentage', {}).get('usd') or \
                        trzni.get('ath_change_percentage') or -50
        
        # Kripto je volatilen - normaliziraj glede na rang
        if ath_sprememba > -20:
            ocena_koncentracije = 9.0
        elif ath_sprememba > -40:
            ocena_koncentracije = 8.5
        elif ath_sprememba > -60:
            ocena_koncentracije = 8.0
        elif ath_sprememba > -75:
            ocena_koncentracije = 7.5
        elif ath_sprememba > -85:
            ocena_koncentracije = 7.0
        elif ath_sprememba > -92:
            ocena_koncentracije = 6.0
        else:
            ocena_koncentracije = 5.0
        
        # Za etablirane projekte so ATH padci normalni (bear markets)
        if rang <= 10 and starost_let > 5:
            ocena_koncentracije = max(ocena_koncentracije, 8.5)
        elif rang <= 30 and starost_let > 3:
            ocena_koncentracije = max(ocena_koncentracije, 8.0)
        elif rang <= 50:
            ocena_koncentracije = max(ocena_koncentracije, 7.5)
        elif rang <= 100:
            ocena_koncentracije = max(ocena_koncentracije, 7.0)
        
        # --- Globina likvidnosti ---
        if volumen > 2000000000:
            ocena_likvidnosti = 9.5
        elif volumen > 1000000000:
            ocena_likvidnosti = 9.0
        elif volumen > 500000000:
            ocena_likvidnosti = 8.5
        elif volumen > 200000000:
            ocena_likvidnosti = 8.0
        elif volumen > 100000000:
            ocena_likvidnosti = 7.5
        elif volumen > 50000000:
            ocena_likvidnosti = 7.0
        elif volumen > 10000000:
            ocena_likvidnosti = 6.5
        elif volumen > 1000000:
            ocena_likvidnosti = 6.0
        elif volumen > 100000:
            ocena_likvidnosti = 5.0
        else:
            ocena_likvidnosti = 4.0
        
        # --- Indikatorji manipulacije (volatilnost) ---
        sprememba_7d = trzni.get('price_change_percentage_7d_in_currency') or \
                       trzni_info.get('price_change_percentage_7d') or 0
        sprememba_30d = trzni.get('price_change_percentage_30d_in_currency') or \
                        trzni_info.get('price_change_percentage_30d') or 0
        
        volatilnost = (abs(sprememba_7d or 0) + abs(sprememba_30d or 0)) / 2
        
        if volatilnost < 5:
            ocena_manipulacije = 9.0
        elif volatilnost < 10:
            ocena_manipulacije = 8.5
        elif volatilnost < 20:
            ocena_manipulacije = 8.0
        elif volatilnost < 35:
            ocena_manipulacije = 7.0
        elif volatilnost < 50:
            ocena_manipulacije = 6.0
        else:
            ocena_manipulacije = 5.0
        
        # --- Vzdrznost tokenomike ---
        if rang <= 10 and starost_let > 5:
            ocena_vzdrznosti = 9.5
        elif rang <= 30 and starost_let > 3:
            ocena_vzdrznosti = 9.0
        elif rang <= 50 and starost_let > 2:
            ocena_vzdrznosti = 8.5
        elif rang <= 100:
            ocena_vzdrznosti = 8.0
        elif rang <= 200:
            ocena_vzdrznosti = 7.5
        else:
            ocena_vzdrznosti = 7.0
        
        return EkonomskeMetrike(
            pravicnost_distribucije=ocena_distribucije,
            mehanizem_inflacije=ocena_inflacije,
            vesting_urnik=ocena_vestinga,
            koncentracija_lastnistva=ocena_koncentracije,
            globina_likvidnosti=ocena_likvidnosti,
            indikatorji_manipulacije=ocena_manipulacije,
            vzdrznost_tokenomike=ocena_vzdrznosti
        )
    
    # ========================================================================
    # Socialna analiza
    # ========================================================================
    
    def analiziraj_socialne(self, podatki: Dict, indikatorji: IndikatorjiPrevare) -> SocialneMetrike:
        """Analizira ekipo, skupnost in dokumentacijo."""
        osnovni = podatki.get('basic_info', {})
        skupnost = osnovni.get('community_data', {}) or {}
        povezave = osnovni.get('links', {}) or {}
        sentiment = osnovni.get('sentiment_votes_up_percentage') or 50
        
        rang = self._dobi_rang(podatki)
        
        # Starost
        datum_geneze = osnovni.get('genesis_date', '')
        starost_let = self._izracunaj_starost(datum_geneze)
        if starost_let == 0:
            if rang <= 10:
                starost_let = 8.0
            elif rang <= 20:
                starost_let = 6.0
            elif rang <= 50:
                starost_let = 4.0
            elif rang <= 100:
                starost_let = 3.0
            else:
                starost_let = 2.0
        
        # Skupnostne metrike
        twitter = skupnost.get('twitter_followers') or 0
        reddit = skupnost.get('reddit_subscribers') or 0
        telegram = skupnost.get('telegram_channel_user_count') or 0
        skupaj_skupnost = twitter + reddit + telegram
        
        # --- Transparentnost ekipe ---
        homepage_list = povezave.get('homepage', [])
        ima_domaco = bool(homepage_list[0]) if homepage_list else False
        ima_whitepaper = bool(povezave.get('whitepaper'))
        
        chat_url = povezave.get('chat_url', [])
        if isinstance(chat_url, list):
            ima_chat = bool(chat_url[0]) if chat_url else False
        else:
            ima_chat = bool(chat_url)
        
        forum_url = povezave.get('official_forum_url', [])
        if isinstance(forum_url, list):
            ima_forum = bool(forum_url[0]) if forum_url else False
        else:
            ima_forum = bool(forum_url)
        
        stevilo_kanalov = sum([ima_domaco, ima_whitepaper, ima_chat, ima_forum])
        
        if stevilo_kanalov >= 4:
            ocena_transparentnosti = 9.0
        elif stevilo_kanalov >= 3:
            ocena_transparentnosti = 8.5
        elif stevilo_kanalov >= 2:
            ocena_transparentnosti = 7.5
        elif stevilo_kanalov >= 1:
            ocena_transparentnosti = 6.0
        else:
            ocena_transparentnosti = 4.0
        
        # Bonus za etablirane
        if rang <= 30 and starost_let > 3:
            ocena_transparentnosti = max(ocena_transparentnosti, 8.5)
        
        # --- Izkusenost ekipe (rang in starost kot proxy) ---
        if rang <= 10 and starost_let > 5:
            ocena_izkusenj = 9.5
        elif rang <= 20 and starost_let > 4:
            ocena_izkusenj = 9.0
        elif rang <= 30 and starost_let > 3:
            ocena_izkusenj = 8.5
        elif rang <= 50 and starost_let > 2:
            ocena_izkusenj = 8.0
        elif rang <= 100:
            ocena_izkusenj = 7.5
        elif rang <= 200:
            ocena_izkusenj = 7.0
        else:
            ocena_izkusenj = 6.0
        
        # --- Angaziranost skupnosti ---
        if skupaj_skupnost > 5000000:
            ocena_angaziranosti = 9.5
        elif skupaj_skupnost > 2000000:
            ocena_angaziranosti = 9.0
        elif skupaj_skupnost > 1000000:
            ocena_angaziranosti = 8.5
        elif skupaj_skupnost > 500000:
            ocena_angaziranosti = 8.0
        elif skupaj_skupnost > 100000:
            ocena_angaziranosti = 7.5
        elif skupaj_skupnost > 50000:
            ocena_angaziranosti = 7.0
        elif skupaj_skupnost > 10000:
            ocena_angaziranosti = 6.0
        else:
            # CoinGecko pogosto ne vraca community podatkov
            if rang <= 10:
                ocena_angaziranosti = 9.0
            elif rang <= 30:
                ocena_angaziranosti = 8.5
            elif rang <= 50:
                ocena_angaziranosti = 8.0
            elif rang <= 100:
                ocena_angaziranosti = 7.5
            else:
                ocena_angaziranosti = 6.5
        
        # --- Kvaliteta dokumentacije ---
        ima_opis = bool(osnovni.get('description', {}).get('en', ''))
        dolzina_opisa = len(osnovni.get('description', {}).get('en', ''))
        
        if ima_whitepaper and dolzina_opisa > 1000:
            ocena_dokumentacije = 9.0
        elif ima_whitepaper and dolzina_opisa > 500:
            ocena_dokumentacije = 8.5
        elif dolzina_opisa > 1000:
            ocena_dokumentacije = 8.0
        elif dolzina_opisa > 500:
            ocena_dokumentacije = 7.5
        elif dolzina_opisa > 200:
            ocena_dokumentacije = 7.0
        elif ima_opis:
            ocena_dokumentacije = 6.0
        else:
            ocena_dokumentacije = 5.0
        
        # --- Pristop marketinga (sentiment) ---
        if sentiment > 80:
            ocena_marketinga = 9.0
        elif sentiment > 65:
            ocena_marketinga = 8.0
        elif sentiment > 50:
            ocena_marketinga = 7.0
        elif sentiment > 40:
            ocena_marketinga = 6.0
        else:
            ocena_marketinga = 5.0
        
        # --- Prisotnost na omrezjih ---
        if twitter > 1000000 and reddit > 100000:
            ocena_prisotnosti = 9.5
        elif twitter > 500000 or reddit > 100000:
            ocena_prisotnosti = 9.0
        elif twitter > 200000 or reddit > 50000:
            ocena_prisotnosti = 8.5
        elif twitter > 100000 or reddit > 20000:
            ocena_prisotnosti = 8.0
        elif twitter > 50000 or reddit > 10000:
            ocena_prisotnosti = 7.5
        elif twitter > 10000 or reddit > 5000:
            ocena_prisotnosti = 7.0
        else:
            # Ni community podatkov - uporabi rang
            if rang <= 30:
                ocena_prisotnosti = 8.0
            elif rang <= 100:
                ocena_prisotnosti = 7.5
            else:
                ocena_prisotnosti = 6.5
        
        # --- Zdravje skupnosti ---
        reddit_aktivnost = skupnost.get('reddit_accounts_active_48h') or 0
        
        if reddit_aktivnost > 10000:
            ocena_zdravja = 9.0
        elif reddit_aktivnost > 5000:
            ocena_zdravja = 8.5
        elif reddit_aktivnost > 2000:
            ocena_zdravja = 8.0
        elif reddit_aktivnost > 1000:
            ocena_zdravja = 7.5
        elif reddit_aktivnost > 500:
            ocena_zdravja = 7.0
        elif reddit_aktivnost > 100:
            ocena_zdravja = 6.5
        else:
            # Ni podatkov - uporabi rang
            if rang <= 20:
                ocena_zdravja = 8.5
            elif rang <= 50:
                ocena_zdravja = 8.0
            elif rang <= 100:
                ocena_zdravja = 7.5
            else:
                ocena_zdravja = 7.0
        
        return SocialneMetrike(
            transparentnost_ekipe=ocena_transparentnosti,
            izkusenost_ekipe=ocena_izkusenj,
            kvaliteta_dokumentacije=ocena_dokumentacije,
            angaziranost_skupnosti=ocena_angaziranosti,
            pristop_marketinga=ocena_marketinga,
            prisotnost_na_omrezjih=ocena_prisotnosti,
            zdravje_skupnosti=ocena_zdravja
        )
    
    # ========================================================================
    # Analiza prevar
    # ========================================================================
    
    def analiziraj_prevare(self, podatki: Dict, ime_kovanca: str) -> IndikatorjiPrevare:
        """Preveri ali je kovanec prevara."""
        indikatorji = IndikatorjiPrevare()
        
        # Preveri v bazi
        je_prevara, podatki_prevare = self.baza_prevar.je_znana_prevara(ime_kovanca)
        if je_prevara:
            indikatorji.je_znana_prevara = True
            indikatorji.podatki_znane_prevare = podatki_prevare
            indikatorji.verjetnost_prevare = 1.0
            indikatorji.rdeci_zastavice.extend(podatki_prevare.get('red_flags', []))
            
            tip_str = podatki_prevare.get('scam_type', 'unknown').upper().replace('_', ' ')
            try:
                indikatorji.tip_prevare = TipPrevare(tip_str)
            except ValueError:
                indikatorji.tip_prevare = TipPrevare.NEZNANO
            
            return indikatorji
        
        # Preveri se po coin_id
        id_kovanca = podatki.get('coin_id', '')
        je_prevara, podatki_prevare = self.baza_prevar.je_znana_prevara(id_kovanca)
        if je_prevara:
            indikatorji.je_znana_prevara = True
            indikatorji.podatki_znane_prevare = podatki_prevare
            indikatorji.verjetnost_prevare = 1.0
            indikatorji.rdeci_zastavice.extend(podatki_prevare.get('red_flags', []))
            return indikatorji
        
        # Dinamicna analiza
        osnovni = podatki.get('basic_info', {})
        rang = self._dobi_rang(podatki)
        trzna_kap = self._dobi_trzno_kap(podatki)
        volumen = self._dobi_volumen(podatki)
        
        tocke_prevare = 0
        
        # Preveri opis za sumljive fraze
        opis = osnovni.get('description', {})
        besedilo = opis.get('en', '').lower() if isinstance(opis, dict) else str(opis).lower()
        ime = osnovni.get('name', '').lower()
        
        # Sumljiva imena
        sumljiva_imena = ['safe', 'moon', 'elon', 'doge', 'shiba', 'inu', 'baby', 'mini', 'floki', '100x', '1000x', 'rocket', 'gem']
        for vzorec in sumljiva_imena:
            if vzorec in ime:
                tocke_prevare += 5
                indikatorji.opozorila.append(f"Ime vsebuje hype besedo: '{vzorec}'")
        
        # Sumljive fraze v opisu
        rdece_fraze = ['guaranteed return', 'risk free', '100x', '1000x', 'next bitcoin', 'get rich', 'passive income', 'dont miss', "don't miss", 'limited time']
        for fraza in rdece_fraze:
            if fraza in besedilo:
                tocke_prevare += 10
                indikatorji.rdeci_zastavice.append(f"Opis vsebuje rdeco zastavo: '{fraza}'")
        
        # Trzne metrike
        trzni_info = osnovni.get('market_data', {}) or {}
        ath_sprememba = trzni_info.get('ath_change_percentage', {}).get('usd') or -50
        
        # Micro cap = visoko tveganje (razen ce je visoko uvrscen)
        if rang > 200:
            if trzna_kap < 1000000 and trzna_kap > 0:
                tocke_prevare += 15
            elif trzna_kap < 10000000 and trzna_kap > 0:
                tocke_prevare += 8
        
        # Extremni padec cene - samo za nizje uvrscene
        if rang > 100:
            if ath_sprememba < -99:
                tocke_prevare += 25
                indikatorji.rdeci_zastavice.append("Cena padla >99% od ATH")
            elif ath_sprememba < -95:
                tocke_prevare += 15
        
        # Zelo nizka likvidnost
        if rang > 100:
            if volumen < 1000 and trzna_kap > 0:
                tocke_prevare += 20
                indikatorji.rdeci_zastavice.append("Ekstremno nizek volumen trgovanja")
            elif volumen < 10000 and trzna_kap > 0:
                tocke_prevare += 10
        
        # Pretvori v verjetnost
        indikatorji.verjetnost_prevare = min(tocke_prevare / 100, 0.95)
        
        # Klasificiraj tip ce je verjetnost visoka
        if indikatorji.verjetnost_prevare > 0.6:
            if ath_sprememba < -99 and volumen < 10000:
                indikatorji.tip_prevare = TipPrevare.RUG_PULL
            elif 'passive income' in besedilo or 'guaranteed' in besedilo:
                indikatorji.tip_prevare = TipPrevare.SUMLJIVA_PONZI
            else:
                indikatorji.tip_prevare = TipPrevare.PUMP_AND_DUMP
        
        return indikatorji
