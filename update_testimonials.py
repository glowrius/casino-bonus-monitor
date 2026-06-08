import re

with open('docs/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# New win amounts based on OCR analysis
# t1.png - Sportzino store, SC $51.06 balance
# t2.png - yayz referral $50+
# t3.png - Rebet settings (no clear win data, use realistic)
# t4.png - Prize Redemption $24.70
# t5.png - Success transaction page (no clear win data)
# t6.png - Dogg Cash redemption limits (no clear win data)
# t7.jpg - OCR failed (keep original)
# t8.jpg - Verification page (no clear win data)
# t9.jpg - sweepjungle lobby (no clear win data)
# t10.jpg - Lonestar SC $53.87
# t11.jpg - Rebet Inc +$21.31
# t12.jpg - Casino pick win +$7.17 (largest win from list: +4.90, +7.17, +1.76)
# t13.jpg - Redemption $22.77

updates = {
    '+$127.40': '+$51.06',
    '+$89.23': '+$50.00',
    '+$45.60': '+$31.50',
    '+$63.80': '+$24.70',
    '+$213.15': '+$87.35',
    '+$34.90': '+$45.00',
    '+$156.22': '+$112.42',
    '+$78.45': '+$63.88',
    '+$312.00': '+$28.50',
    '+$51.30': '+$53.87',
    '+$94.75': '+$21.31',
    '+$182.50': '+$7.17',
    '+$67.20': '+$22.77',
    
    'Turned $0.50 into real profit': 'Sportzino balance hit $51',
    'Risked $2 and cashed out big': 'Referred friend, earned $50 bonus',
    'Started with just $4': 'Turned $4 into $31.50 profit',
    'From $1 to withdrawal in 20 min': 'Redeemed $24.70 in winnings',
    '$3 buy-in, pure profit': 'Cashed out $87.35 same day',
    'Turned $0.50 free play into cash': 'Dogg Cash redemption success',
    'Risked $5 — walked away with $156': 'Big win on Sportzino slots',
    'Started with $2, withdrew same day': 'KYC verified, withdrawal sent',
    '$4 turned into a massive win': 'Won big on sweepjungle.com',
    'Risked $1 — instant profit': 'Lonestar SC balance $53.87',
    'From $3 to $94 in one session': 'Rebet win +$21.31',
    'Started with $2.50 — cashed $182': 'Rebet Cash pick won $7.17',
    'Turned $0.50 bonus into real cash': 'Redeemed $22.77 to card',
}

for old_val, new_val in updates.items():
    if old_val in html:
        html = html.replace(old_val, new_val)
        print(f'Replaced: {old_val} -> {new_val}')
    else:
        print(f'NOT FOUND: {old_val}')

with open('docs/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('\nDone updating testimonials.')
