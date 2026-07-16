# Predloga računa za e-pošto

Dodana je HTML predloga `templates/invoice_email.html`, ki posnema poslani primer računa in doda podatke za plačilo:

- TRR/IBAN: `SI56 0400 0028 2135 887`
- ID za DDV: `90692993`
- besedilo o neobračunanem DDV po 94. členu ZDDV-1
- navodilo za sklic: `SI00` + številka računa
- opozorilo o zakonskih zamudnih obrestih

## Spremenljivke v predlogi

Pred pošiljanjem računa zamenjaj naslednje placeholderje:

| Placeholder | Pomen |
|---|---|
| `{{ logo_url }}` | URL ali pot do obstoječega logotipa |
| `{{ logo_alt }}` | Nadomestno besedilo za logotip |
| `{{ signature_url }}` | URL ali pot do slike podpisa |
| `{{ customer_name }}` | Ime naročnika |
| `{{ invoice_number }}` | Številka računa, npr. `2026-043` |
| `{{ service_date }}` | Datum storitve |
| `{{ issue_date }}` | Datum izdaje |
| `{{ due_date }}` | Datum zapadlosti |
| `{{ invoice_items }}` | HTML vrstice postavk računa |
| `{{ total_amount }}` | Skupni znesek |
| `{{ amount_due }}` | Znesek za plačilo |

## Primer `invoice_items`

```html
<tr>
  <td>Psihoterapija - individualna</td>
  <td>2</td>
  <td>70</td>
  <td>140</td>
</tr>
```

## Opomba

Predloga ne spreminja obstoječih nastavitev za logotip ali podpis. Uporabi obstoječi URL/sliko in jo vstavi v `{{ logo_url }}` oziroma `{{ signature_url }}`.


## Obvezni bloki za WordPress/PDF kodo

Če obstoječi PDF ali e-poštna predloga ne uporablja `templates/invoice_email.html`, uporabi helperje iz `templates/wordpress_invoice_required_blocks.php`. Ti helperji eksplicitno vrnejo obvezni tekst za glavo in nogo računa:

```php
echo '<style>' . psierp_required_invoice_blocks_css() . '</style>';
echo psierp_required_invoice_header_html($invoice_number);
// ... obstoječa vsebina računa ...
echo psierp_required_invoice_footer_html();
```

S tem se v izpisu obvezno prikažejo podatki podjetja, TRR/IBAN, ID za DDV, številka računa in celotno besedilo o plačilu oziroma DDV.
