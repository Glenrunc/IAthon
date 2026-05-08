"""
Generate 10 sample French invoices for the hackathon demo.

Output: data/samples/
  - 6 clean text-layer PDFs
  - 2 scanned-style PDFs (image-based)
  - 2 phone-photo JPGs
"""

import datetime
import io
import os
import sys

# ---------------------------------------------------------------------------
# Ensure project root is importable
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.utils import luhn_valid, make_invoice_number, make_siret, make_tva_intra

# ---------------------------------------------------------------------------
# ReportLab imports
# ---------------------------------------------------------------------------
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# PIL
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

# reportlab canvas for embedding images
from reportlab.pdfgen import canvas as rl_canvas

# ---------------------------------------------------------------------------
# Supplier definitions
# ---------------------------------------------------------------------------
TODAY = datetime.date(2026, 5, 7)

SUPPLIERS = [
    {
        "name": "Orange Business",
        "address": "78 rue de la Roquette",
        "city": "75011 Paris",
        "siren": "732829320",
        "nic": "0001",
        "category": "Télécom",
        "tva_rate": 20.0,
        "ht": 49.00,
        "tva_eur": 9.80,
        "ttc": 58.80,
        "filename": "orange_business.pdf",
        "invoice_idx": 1,
        "date_offset": 5,
        "lines": [
            ("Abonnement Livebox Pro", 1, 49.00),
        ],
    },
    {
        "name": "EDF Pro",
        "address": "22 avenue de Wagram",
        "city": "75008 Paris",
        "siren": "552081317",
        "nic": "0001",
        "category": "Énergie",
        "tva_rate": 5.5,
        "ht": 118.01,
        "tva_eur": 6.49,
        "ttc": 124.50,
        "filename": "edf_pro.pdf",
        "invoice_idx": 2,
        "date_offset": 12,
        "lines": [
            ("Consommation électrique (kWh)", 1, 99.01),
            ("Abonnement mensuel Tarif Pro", 1, 19.00),
        ],
    },
    {
        "name": "La Poste Pro",
        "address": "9 rue du Louvre",
        "city": "75001 Paris",
        "siren": "356000000",
        "nic": "0002",
        "category": "Affranchissement",
        "tva_rate": 20.0,
        "ht": 36.00,
        "tva_eur": 7.20,
        "ttc": 43.20,
        "filename": "la_poste_pro.pdf",
        "invoice_idx": 3,
        "date_offset": 20,
        "lines": [
            ("Carnet 20 timbres prioritaires", 2, 16.00),
            ("Affranchissement colis standard", 1, 4.00),
        ],
    },
    {
        "name": "Manutan",
        "address": "14 avenue du Président Wilson",
        "city": "93210 La Plaine-Saint-Denis",
        "siren": "542065305",
        "nic": "0001",
        "category": "Fournitures bureau",
        "tva_rate": 20.0,
        "ht": 214.00,
        "tva_eur": 42.80,
        "ttc": 256.80,
        "filename": "manutan.pdf",
        "invoice_idx": 4,
        "date_offset": 30,
        "lines": [
            ("Armoire métallique vestiaire", 1, 149.00),
            ("Étagère stockage 5 niveaux", 1, 45.00),
            ("Chaise atelier réglable", 1, 20.00),
        ],
    },
    {
        "name": "Bureau Vallée",
        "address": "45 boulevard Haussmann",
        "city": "75009 Paris",
        "siren": "404833048",
        "nic": "0001",
        "category": "Fournitures bureau",
        "tva_rate": 20.0,
        "ht": 74.50,
        "tva_eur": 14.90,
        "ttc": 89.40,
        "filename": "bureau_vallee.pdf",
        "invoice_idx": 5,
        "date_offset": 40,
        "lines": [
            ("Ramette papier A4 80g (5x)", 3, 12.50),
            ("Cartouches encre HP 302XL (lot 2)", 1, 25.00),
            ("Classeurs à levier A4 (lot 10)", 1, 24.50),
        ],
    },
    {
        "name": "Sodexo Restauration",
        "address": "255 quai de la Bataille de Stalingrad",
        "city": "92130 Issy-les-Moulineaux",
        "siren": "301940219",
        "nic": "0001",
        "category": "Restauration",
        "tva_rate": 10.0,
        "ht": 71.00,
        "tva_eur": 7.10,
        "ttc": 78.10,
        "filename": "sodexo.pdf",
        "invoice_idx": 6,
        "date_offset": 50,
        "lines": [
            ("Titres-restaurant nominatifs (x10)", 10, 6.50),
            ("Frais de service mensuel", 1, 6.00),
        ],
    },
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

STYLES = getSampleStyleSheet()

STYLE_NORMAL = ParagraphStyle(
    "normal_fr",
    parent=STYLES["Normal"],
    fontSize=10,
    leading=14,
)
STYLE_BOLD = ParagraphStyle(
    "bold_fr",
    parent=STYLES["Normal"],
    fontSize=10,
    leading=14,
    fontName="Helvetica-Bold",
)
STYLE_H1 = ParagraphStyle(
    "h1_fr",
    parent=STYLES["Normal"],
    fontSize=18,
    leading=22,
    fontName="Helvetica-Bold",
)
STYLE_SMALL = ParagraphStyle(
    "small_fr",
    parent=STYLES["Normal"],
    fontSize=8,
    leading=12,
)


def fr_amount(value: float) -> str:
    """Format as French decimal: comma separator, 2 places."""
    return f"{value:,.2f}".replace(",", " ").replace(".", ",")


def build_invoice_story(sup: dict) -> list:
    """Return a list of ReportLab Flowables for one invoice."""
    invoice_date = TODAY - datetime.timedelta(days=sup["date_offset"])
    siret = make_siret(sup["siren"], sup["nic"])
    tva_intra = make_tva_intra(sup["siren"])
    inv_no = make_invoice_number(sup["invoice_idx"])

    story = []

    # --- Header ---
    story.append(Paragraph("Facture", STYLE_H1))
    story.append(Spacer(1, 6 * mm))

    # Supplier block + invoice meta in a 2-column table
    supplier_info = (
        f"<b>{sup['name']}</b><br/>"
        f"{sup['address']}<br/>"
        f"{sup['city']}<br/>"
        f"SIRET&nbsp;: {siret}<br/>"
        f"N° TVA&nbsp;: {tva_intra}"
    )
    invoice_meta = (
        f"<b>N° Facture</b>&nbsp;: {inv_no}<br/>"
        f"<b>Date</b>&nbsp;: {invoice_date.strftime('%d/%m/%Y')}"
    )

    header_table = Table(
        [[Paragraph(supplier_info, STYLE_NORMAL), Paragraph(invoice_meta, STYLE_NORMAL)]],
        colWidths=[100 * mm, 70 * mm],
    )
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("BACKGROUND", (0, 0), (-1, -1), colors.Color(0.97, 0.97, 0.97)),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 8 * mm))

    # --- Line items table ---
    item_data = [
        [
            Paragraph("<b>Description</b>", STYLE_BOLD),
            Paragraph("<b>Qté</b>", STYLE_BOLD),
            Paragraph("<b>Prix unitaire HT</b>", STYLE_BOLD),
            Paragraph("<b>Total HT</b>", STYLE_BOLD),
        ]
    ]
    for desc, qty, unit_price in sup["lines"]:
        total = qty * unit_price
        item_data.append(
            [
                Paragraph(desc, STYLE_NORMAL),
                Paragraph(str(qty), STYLE_NORMAL),
                Paragraph(f"{fr_amount(unit_price)} €", STYLE_NORMAL),
                Paragraph(f"{fr_amount(total)} €", STYLE_NORMAL),
            ]
        )

    items_table = Table(
        item_data,
        colWidths=[80 * mm, 20 * mm, 40 * mm, 30 * mm],
    )
    items_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.2, 0.4, 0.7)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
                ("PADDING", (0, 0), (-1, -1), 5),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ]
        )
    )
    story.append(items_table)
    story.append(Spacer(1, 6 * mm))

    # --- Totals block ---
    tva_label = f"TVA {sup['tva_rate']:g}%"
    totals_data = [
        ["Total HT", f"{fr_amount(sup['ht'])} €"],
        [tva_label, f"{fr_amount(sup['tva_eur'])} €"],
        ["Total TTC", f"{fr_amount(sup['ttc'])} €"],
    ]
    totals_table = Table(totals_data, colWidths=[80 * mm, 40 * mm], hAlign="RIGHT")
    totals_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("BACKGROUND", (0, 2), (-1, 2), colors.Color(0.2, 0.4, 0.7)),
                ("TEXTCOLOR", (0, 2), (-1, 2), colors.white),
                ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
                ("PADDING", (0, 0), (-1, -1), 5),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ]
        )
    )
    story.append(totals_table)
    story.append(Spacer(1, 10 * mm))

    # Footer note
    story.append(
        Paragraph(
            "Paiement à 30 jours. En cas de retard, des pénalités de 3× le taux légal s'appliquent.",
            STYLE_SMALL,
        )
    )

    return story


def generate_clean_pdf(sup: dict, output_path: str) -> None:
    """Generate a text-layer PDF invoice."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
    story = build_invoice_story(sup)
    doc.build(story)


# ---------------------------------------------------------------------------
# Image-based invoice (PIL)
# ---------------------------------------------------------------------------

def build_invoice_image(sup: dict, width: int = 1240, height: int = 1754) -> Image.Image:
    """Draw invoice content onto a white PIL image and return it."""
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    invoice_date = TODAY - datetime.timedelta(days=sup["date_offset"])
    siret = make_siret(sup["siren"], sup["nic"])
    tva_intra = make_tva_intra(sup["siren"])
    inv_no = make_invoice_number(sup["invoice_idx"])

    # Attempt to use a basic font; fall back to default if unavailable
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
        font_bold = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
        font_reg = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 26)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
    except OSError:
        font_title = ImageFont.load_default()
        font_bold = font_title
        font_reg = font_title
        font_small = font_title

    margin_x = 80
    y = 80

    # Title
    draw.text((margin_x, y), "Facture", font=font_title, fill=(0, 0, 0))
    y += 90

    # Horizontal rule
    draw.line([(margin_x, y), (width - margin_x, y)], fill=(50, 100, 180), width=3)
    y += 20

    # Supplier info (left) + Invoice meta (right)
    right_col = width // 2 + 40
    draw.text((margin_x, y), sup["name"], font=font_bold, fill=(0, 0, 0))
    draw.text((right_col, y), f"N° Facture : {inv_no}", font=font_bold, fill=(0, 0, 0))
    y += 40
    draw.text((margin_x, y), sup["address"], font=font_reg, fill=(60, 60, 60))
    draw.text((right_col, y), f"Date : {invoice_date.strftime('%d/%m/%Y')}", font=font_reg, fill=(60, 60, 60))
    y += 36
    draw.text((margin_x, y), sup["city"], font=font_reg, fill=(60, 60, 60))
    y += 36
    draw.text((margin_x, y), f"SIRET : {siret}", font=font_reg, fill=(60, 60, 60))
    y += 36
    draw.text((margin_x, y), f"N° TVA : {tva_intra}", font=font_reg, fill=(60, 60, 60))
    y += 60

    # Line items header
    cols = [margin_x, margin_x + 550, margin_x + 700, margin_x + 900]
    headers = ["Description", "Qté", "Prix unit. HT", "Total HT"]
    draw.rectangle([(margin_x, y), (width - margin_x, y + 44)], fill=(50, 100, 180))
    for i, h in enumerate(headers):
        draw.text((cols[i] + 6, y + 8), h, font=font_bold, fill=(255, 255, 255))
    y += 44

    # Line items rows
    row_bg = [(255, 255, 255), (242, 242, 242)]
    for row_i, (desc, qty, unit_price) in enumerate(sup["lines"]):
        total = qty * unit_price
        bg = row_bg[row_i % 2]
        draw.rectangle([(margin_x, y), (width - margin_x, y + 40)], fill=bg)
        draw.text((cols[0] + 6, y + 7), desc, font=font_reg, fill=(0, 0, 0))
        draw.text((cols[1] + 6, y + 7), str(qty), font=font_reg, fill=(0, 0, 0))
        draw.text((cols[2] + 6, y + 7), f"{fr_amount(unit_price)} EUR", font=font_reg, fill=(0, 0, 0))
        draw.text((cols[3] + 6, y + 7), f"{fr_amount(total)} EUR", font=font_reg, fill=(0, 0, 0))
        y += 40

    y += 40

    # Totals
    tva_label = f"TVA {sup['tva_rate']:g}%"
    totals = [
        ("Total HT", f"{fr_amount(sup['ht'])} EUR"),
        (tva_label, f"{fr_amount(sup['tva_eur'])} EUR"),
        ("Total TTC", f"{fr_amount(sup['ttc'])} EUR"),
    ]
    totals_x = width // 2
    for i, (label, val) in enumerate(totals):
        bg = (50, 100, 180) if i == 2 else (245, 245, 245)
        fg = (255, 255, 255) if i == 2 else (0, 0, 0)
        draw.rectangle([(totals_x, y), (width - margin_x, y + 40)], fill=bg)
        draw.text((totals_x + 10, y + 8), label, font=font_bold, fill=fg)
        draw.text((width - margin_x - 200, y + 8), val, font=font_bold, fill=fg)
        y += 40

    y += 60
    draw.line([(margin_x, y), (width - margin_x, y)], fill=(200, 200, 200), width=1)
    y += 16
    draw.text(
        (margin_x, y),
        "Paiement a 30 jours. Penalites de retard : 3x le taux legal.",
        font=font_small,
        fill=(120, 120, 120),
    )

    return img


def degrade_scan(img: Image.Image) -> Image.Image:
    """Apply scan-style degradation to a PIL image."""
    img = img.filter(ImageFilter.GaussianBlur(radius=0.8))
    img = img.rotate(2, expand=False, fillcolor=(255, 255, 255))
    # JPEG round-trip at quality=50
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=50)
    buf.seek(0)
    img = Image.open(buf).copy()
    return img


def degrade_photo(img: Image.Image) -> Image.Image:
    """Apply phone-photo degradation to a PIL image."""
    img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
    img = img.rotate(8, expand=True, fillcolor=(255, 255, 255))
    img = ImageEnhance.Brightness(img).enhance(0.92)
    return img


def image_to_pdf(img: Image.Image, output_path: str) -> None:
    """Embed a PIL image into a single-page PDF using reportlab canvas."""
    # Save image to temp bytes
    img_buf = io.BytesIO()
    # Convert to RGB if needed (JPEG requires RGB)
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.save(img_buf, format="JPEG", quality=85)
    img_buf.seek(0)

    img_width, img_height = img.size
    # Scale to A4 maintaining aspect ratio
    a4_w, a4_h = A4  # points (595 x 842)
    scale = min(a4_w / img_width, a4_h / img_height)
    draw_w = img_width * scale
    draw_h = img_height * scale
    x_offset = (a4_w - draw_w) / 2
    y_offset = (a4_h - draw_h) / 2

    pdf_buf = io.BytesIO()
    c = rl_canvas.Canvas(pdf_buf, pagesize=A4)
    from reportlab.lib.utils import ImageReader

    c.drawImage(ImageReader(img_buf), x_offset, y_offset, width=draw_w, height=draw_h)
    c.save()

    with open(output_path, "wb") as f:
        f.write(pdf_buf.getvalue())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    out_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "samples",
    )
    os.makedirs(out_dir, exist_ok=True)

    # --- Luhn self-check ---
    print("Running Luhn self-check...")
    for sup in SUPPLIERS:
        siret = make_siret(sup["siren"], sup["nic"])
        assert luhn_valid(siret), f"SIRET {siret} for {sup['name']} fails Luhn!"
        print(f"  {sup['name']:30s}  SIRET={siret}  OK")
    print()

    generated = []

    # -----------------------------------------------------------------------
    # 1. Six clean text-layer PDFs
    # -----------------------------------------------------------------------
    print("Generating 6 clean PDFs...")
    for sup in SUPPLIERS:
        path = os.path.join(out_dir, sup["filename"])
        generate_clean_pdf(sup, path)
        size = os.path.getsize(path)
        generated.append((sup["filename"], size))
        print(f"  {sup['filename']:35s}  {size:,} bytes")

    # -----------------------------------------------------------------------
    # 2. Two scanned-style PDFs (Orange + Manutan)
    # -----------------------------------------------------------------------
    print("\nGenerating 2 scanned PDFs...")
    for sup_name, out_filename in [("Orange Business", "orange_business_scan.pdf"), ("Manutan", "manutan_scan.pdf")]:
        sup = next(s for s in SUPPLIERS if s["name"] == sup_name)
        img = build_invoice_image(sup)
        img = degrade_scan(img)
        path = os.path.join(out_dir, out_filename)
        image_to_pdf(img, path)
        size = os.path.getsize(path)
        generated.append((out_filename, size))
        print(f"  {out_filename:35s}  {size:,} bytes")

    # -----------------------------------------------------------------------
    # 3. Two phone-photo JPGs (EDF + La Poste)
    # -----------------------------------------------------------------------
    print("\nGenerating 2 phone-photo JPGs...")
    for sup_name, out_filename in [("EDF Pro", "edf_pro_photo.jpg"), ("La Poste Pro", "la_poste_pro_photo.jpg")]:
        sup = next(s for s in SUPPLIERS if s["name"] == sup_name)
        img = build_invoice_image(sup)
        img = degrade_photo(img)
        if img.mode != "RGB":
            img = img.convert("RGB")
        path = os.path.join(out_dir, out_filename)
        img.save(path, format="JPEG", quality=70)
        size = os.path.getsize(path)
        generated.append((out_filename, size))
        print(f"  {out_filename:35s}  {size:,} bytes")

    # -----------------------------------------------------------------------
    # 4. Write README.md
    # -----------------------------------------------------------------------
    readme_path = os.path.join(out_dir, "README.md")
    write_readme(SUPPLIERS, readme_path)
    print(f"\n  {'README.md':35s}  {os.path.getsize(readme_path):,} bytes")

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    print("\n=== SUMMARY ===")
    total_bytes = 0
    for fname, size in generated:
        print(f"  {fname:40s}  {size:>10,} bytes")
        total_bytes += size
    print(f"  {'TOTAL':40s}  {total_bytes:>10,} bytes")
    print(f"\n  Files: {len(generated)} in {out_dir}")
    print("\nDONE.")


def write_readme(suppliers: list, path: str) -> None:
    """Write data/samples/README.md with a metadata table."""
    lines = [
        "# Sample Invoices — hackathon demo dataset",
        "",
        "| filename | supplier | type | HT | TVA% | TVA EUR | TTC | SIRET | TVA intra | invoice_no |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]

    def row(filename, supplier, file_type, sup_data):
        siret = make_siret(sup_data["siren"], sup_data["nic"])
        tva_intra = make_tva_intra(sup_data["siren"])
        inv_no = make_invoice_number(sup_data["invoice_idx"])
        return (
            f"| {filename} | {supplier} | {file_type} "
            f"| {sup_data['ht']:.2f} | {sup_data['tva_rate']} "
            f"| {sup_data['tva_eur']:.2f} | {sup_data['ttc']:.2f} "
            f"| {siret} | {tva_intra} | {inv_no} |"
        )

    # 6 clean PDFs
    for sup in suppliers:
        lines.append(row(sup["filename"], sup["name"], "PDF texte", sup))

    # 2 scanned PDFs
    for sup_name, out_filename in [("Orange Business", "orange_business_scan.pdf"), ("Manutan", "manutan_scan.pdf")]:
        sup = next(s for s in suppliers if s["name"] == sup_name)
        lines.append(row(out_filename, sup["name"], "PDF scanné", sup))

    # 2 phone JPGs
    for sup_name, out_filename in [("EDF Pro", "edf_pro_photo.jpg"), ("La Poste Pro", "la_poste_pro_photo.jpg")]:
        sup = next(s for s in suppliers if s["name"] == sup_name)
        lines.append(row(out_filename, sup["name"], "Photo JPG", sup))

    lines.append("")
    lines.append(f"*Generated {TODAY.isoformat()} by scripts/generate_invoices.py*")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
