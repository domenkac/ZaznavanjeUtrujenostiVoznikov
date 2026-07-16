<?php
/**
 * Required invoice header/footer blocks for PsihoterapijeERP invoice PDFs/emails.
 *
 * Copy these helpers into the invoice rendering code (or include this file) and
 * echo the returned HTML inside the invoice template. The functions are written
 * without depending on any specific PDF library.
 */

if (!function_exists('psierp_required_invoice_header_html')) {
    function psierp_required_invoice_header_html($invoice_number = '') {
        $invoice_number = function_exists('esc_html')
            ? esc_html($invoice_number)
            : htmlspecialchars((string) $invoice_number, ENT_QUOTES, 'UTF-8');

        return '
            <div class="psierp-required-company-header">
                <strong>Psihoterapija in svetovanje</strong><br>
                <strong>Jasmina Čavužić, s.p.</strong><br>
                info@postavi-meje.si<br>
                041 372 076<br>
                <strong>TRR: SI56 0400 0028 2135 887</strong><br>
                <strong>ID za DDV: 90692993</strong><br>
                ' . ($invoice_number !== '' ? '<strong>Račun št.: ' . $invoice_number . '</strong>' : '') . '
            </div>
        ';
    }
}

if (!function_exists('psierp_required_invoice_footer_html')) {
    function psierp_required_invoice_footer_html() {
        return '
            <div class="psierp-required-invoice-footer">
                <p>Hvala za zaupanje.</p>
                <p>
                    DDV ni obračunan na podlagi 1. odstavka 94. člena Zakona o davku na dodano vrednost.<br>
                    Navedeni znesek nakažite na poslovni račun odprt pri OTP Banka: <strong>SI56 0400 0028 2135 887</strong>.<br>
                    Za sklic uporabite SI00 in številko računa.<br>
                    V primeru nepravočasnega plačila bomo zaračunali zakonske zamudne obresti.
                </p>
            </div>
        ';
    }
}

if (!function_exists('psierp_required_invoice_blocks_css')) {
    function psierp_required_invoice_blocks_css() {
        return '
            .psierp-required-company-header {
                text-align: right;
                font-size: 13px;
                line-height: 1.25;
                color: #1f334f;
                margin-bottom: 18px;
            }
            .psierp-required-invoice-footer {
                margin-top: 38px;
                padding-top: 14px;
                border-top: 1px solid #e2e8f0;
                font-size: 11px;
                line-height: 1.35;
                color: #111827;
            }
            .psierp-required-invoice-footer p {
                margin: 0 0 10px;
            }
        ';
    }
}
