#!/usr/bin/env python3
"""
Glavni vstopni tocka za klasifikator kriptovalut.

Primeri uporabe:
    python main.py bitcoin
    python main.py ethereum --format markdown
    python main.py btc eth sol --batch
    
Za pomoc:
    python main.py --help
"""

import argparse
import json
import sys
import os

# Dodaj parent directory v path ce poganjamo direktno
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from classifier import KriptoKlasifikator


def main():
    parser = argparse.ArgumentParser(
        description='Klasifikator kriptovalut - oceni tveganje in kvaliteto projektov',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Primeri:
  %(prog)s bitcoin                    # Analiziraj Bitcoin
  %(prog)s eth                        # Analiziraj Ethereum (po simbolu)
  %(prog)s solana --format markdown   # Izvozi kot Markdown
  %(prog)s btc eth sol --batch        # Batch analiza vec kovancev
  %(prog)s safemoon                   # Preveri znano prevaro
        """
    )
    
    parser.add_argument(
        'kovanci',
        nargs='+',
        help='ID-ji kovancev ali simboli (npr. bitcoin, eth, solana)'
    )
    
    parser.add_argument(
        '-f', '--format',
        choices=['json', 'markdown', 'text'],
        default='text',
        help='Format izpisa (privzeto: text)'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Shrani rezultat v datoteko'
    )
    
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Batch mode - primerjava vec kovancev'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Tihi nacin - samo koncni rezultat'
    )
    
    args = parser.parse_args()
    
    # Inicializiraj klasifikator
    try:
        klasifikator = KriptoKlasifikator()
    except Exception as e:
        print(f"Napaka pri inicializaciji: {e}", file=sys.stderr)
        sys.exit(1)
    
    rezultati = []
    
    # Analiziraj kovance
    for i, kovanec in enumerate(args.kovanci, 1):
        if not args.quiet:
            print(f"\n[{i}/{len(args.kovanci)}] Analiziram {kovanec}...", file=sys.stderr)
        
        try:
            rezultat = klasifikator.klasificiraj(kovanec)
            rezultati.append(rezultat)
            
            # Ce ni batch, izpisi takoj
            if not args.batch and len(args.kovanci) == 1:
                izpis = klasifikator.izvozi_porocilo(rezultat, args.format)
                
                if args.output:
                    with open(args.output, 'w', encoding='utf-8') as f:
                        f.write(izpis)
                    print(f"\nShranjeno v {args.output}", file=sys.stderr)
                else:
                    print(izpis)
                    
        except Exception as e:
            print(f"Napaka pri analizi {kovanec}: {e}", file=sys.stderr)
            rezultati.append({
                'ime': kovanec,
                'napaka': str(e)
            })
    
    # Batch mode - primerjava
    if args.batch or len(args.kovanci) > 1:
        if args.format == 'json':
            izpis = json.dumps(rezultati, indent=2, ensure_ascii=False)
        else:
            izpis = formatiraj_primerjavo(rezultati)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(izpis)
            print(f"\nShranjeno v {args.output}", file=sys.stderr)
        else:
            print(izpis)


def formatiraj_primerjavo(rezultati):
    """Formatiraj batch rezultate kot tabelo."""
    sirina = 100
    
    linije = [
        "",
        "╔" + "═" * (sirina - 2) + "╗",
        "║" + " CRYPTOCURRENCY COMPARISON REPORT ".center(sirina - 2) + "║",
        "╚" + "═" * (sirina - 2) + "╝",
        "",
        "┌" + "─" * (sirina - 2) + "┐",
        "│" + f"{'Coin':<20} {'Score':>8} {'Grade':>6} {'Risk Level':>14} {'Tech':>8} {'Econ':>8} {'Social':>8}     │",
        "├" + "─" * (sirina - 2) + "┤",
    ]
    
    for r in rezultati:
        if 'napaka' in r:
            linije.append("│" + f"  {r['ime']:<18} {'ERROR':>8}".ljust(sirina - 2) + "│")
            continue
            
        ime = r.get('ime', '???')[:18]
        ocena = r.get('koncna_ocena', 0)
        crka = r.get('ocena_crka', '?')
        tveganje = r.get('stopnja_tveganja', '?')[:12]
        teh = r.get('tehnicna_ocena', 0)
        eko = r.get('ekonomska_ocena', 0)
        soc = r.get('socialna_ocena', 0)
        
        # Oznaci prevare
        if r.get('je_potrjena_prevara'):
            ime = f"⚠️ {ime}"[:18]
            tveganje = "SCAM!"
        
        # Vizualni indikator
        if ocena >= 80:
            indikator = "🟢"
        elif ocena >= 65:
            indikator = "🟡"
        elif ocena >= 50:
            indikator = "🟠"
        else:
            indikator = "🔴"
        
        linije.append(
            "│" + f"  {indikator} {ime:<16} {ocena:>7.1f} {crka:>6} {tveganje:>14} {teh:>7.1f} {eko:>8.1f} {soc:>8.1f}     │"
        )
    
    linije.extend([
        "└" + "─" * (sirina - 2) + "┘",
        "",
        "┌" + "─" * (sirina - 2) + "┐",
        "│" + " LEGEND ".center(sirina - 2) + "│",
        "├" + "─" * (sirina - 2) + "┤",
        "│" + "  🟢 A/A+ (80-100)  🟡 B/B+ (65-79)  🟠 C/C+ (50-64)  🔴 D/F (<50)".ljust(sirina - 2) + "│",
        "│" + "  Tech = Technical Score, Econ = Economic Score, Social = Social Score".ljust(sirina - 2) + "│",
        "│" + "  All scores are on a 0-100 scale | Weighted: 40% Tech, 35% Econ, 25% Social".ljust(sirina - 2) + "│",
        "└" + "─" * (sirina - 2) + "┘",
        ""
    ])
    
    return "\n".join(linije)


if __name__ == '__main__':
    main()
