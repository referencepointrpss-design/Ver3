import csv
import json
import os
from datetime import datetime
from pathlib import Path

from database import load_data, get_db_path


APP_EXPORT_FOLDER = "SurveyOfficeExports"


def _timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_export_dir():
    """Return a safe writable export folder on Android and desktop."""
    try:
        from kivy.app import App
        app = App.get_running_app()
        if app and getattr(app, "user_data_dir", None):
            path = Path(app.user_data_dir) / APP_EXPORT_FOLDER
            path.mkdir(parents=True, exist_ok=True)
            return str(path)
    except Exception:
        pass

    path = Path(os.path.dirname(os.path.abspath(__file__))) / APP_EXPORT_FOLDER
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def _write_csv(filename, headers, rows):
    export_dir = get_export_dir()
    path = os.path.join(export_dir, filename)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    return path


def backup_database_json():
    data = load_data()
    export_dir = get_export_dir()
    path = os.path.join(export_dir, f"survey_equipment_backup_{_timestamp()}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def export_equipment_inventory_csv():
    data = load_data()
    rows = []
    for equip_id, info in sorted(data.get("equipments", {}).items()):
        rows.append([
            equip_id,
            info.get("type", ""),
            info.get("brand", ""),
            info.get("model", ""),
            info.get("serial", ""),
            info.get("ownership", ""),
            info.get("supplier", ""),
        ])
    return _write_csv(
        f"equipment_inventory_{_timestamp()}.csv",
        ["Equipment ID", "Type", "Brand", "Model", "Serial", "Ownership", "Supplier"],
        rows,
    )


def export_allocation_logs_csv():
    data = load_data()
    rows = []
    for log in data.get("logs", []):
        rows.append([
            log.get("equip_id", ""),
            log.get("client", ""),
            log.get("term", ""),
            log.get("start_date", log.get("date", "")),
            log.get("end_date", log.get("start_date", log.get("date", ""))),
        ])
    return _write_csv(
        f"equipment_allocation_logs_{_timestamp()}.csv",
        ["Equipment ID", "Client", "Term", "Start Date", "End Date"],
        rows,
    )


def _pdf_escape(text):
    return str(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def write_simple_pdf(filename, title, lines):
    """Create a small plain-text PDF without external dependencies."""
    export_dir = get_export_dir()
    path = os.path.join(export_dir, filename)

    page_lines = []
    current = []
    for line in lines:
        if len(current) >= 42:
            page_lines.append(current)
            current = []
        current.append(str(line))
    if current:
        page_lines.append(current)
    if not page_lines:
        page_lines = [["No data available."]]

    objects = []

    def add_obj(content):
        objects.append(content)
        return len(objects)

    pages_kids = []
    font_obj_id = 3

    # Reserve catalog/pages/font positions by adding later-compatible objects.
    add_obj("<< /Type /Catalog /Pages 2 0 R >>")
    add_obj("<< /Type /Pages /Kids [] /Count 0 >>")
    add_obj("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    for page_index, lines_chunk in enumerate(page_lines, start=1):
        content_lines = ["BT", "/F1 16 Tf", "50 790 Td", f"({_pdf_escape(title)}) Tj", "/F1 10 Tf", "0 -24 Td"]
        for line in lines_chunk:
            content_lines.append(f"({_pdf_escape(line[:105])}) Tj")
            content_lines.append("0 -15 Td")
        content_lines.append("ET")
        stream = "\n".join(content_lines)
        content_obj = add_obj(f"<< /Length {len(stream.encode('utf-8'))} >>\nstream\n{stream}\nendstream")
        page_obj = add_obj(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 {font_obj_id} 0 R >> >> /Contents {content_obj} 0 R >>"
        )
        pages_kids.append(page_obj)

    objects[1] = f"<< /Type /Pages /Kids [{' '.join(f'{kid} 0 R' for kid in pages_kids)}] /Count {len(pages_kids)} >>"

    pdf = ["%PDF-1.4\n"]
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(sum(len(part.encode('utf-8')) for part in pdf))
        pdf.append(f"{i} 0 obj\n{obj}\nendobj\n")
    xref_pos = sum(len(part.encode('utf-8')) for part in pdf)
    pdf.append(f"xref\n0 {len(objects)+1}\n")
    pdf.append("0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.append(f"{offset:010d} 00000 n \n")
    pdf.append(f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF")

    with open(path, "wb") as f:
        f.write("".join(pdf).encode("utf-8"))
    return path


def export_summary_pdf():
    data = load_data()
    lines = []
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Database path: {get_db_path()}")
    lines.append("")
    lines.append(f"Total equipment profiles: {len(data.get('equipments', {}))}")
    lines.append(f"Total allocation logs: {len(data.get('logs', []))}")
    lines.append(f"Device owners: {len(data.get('device_owners', {}))}")
    lines.append(f"Client companies: {len(data.get('rented_to_companies', {}))}")
    lines.append("")
    lines.append("Equipment Inventory:")
    for equip_id, info in sorted(data.get("equipments", {}).items()):
        lines.append(f"- {equip_id}: {info.get('brand','')} {info.get('model','')} | {info.get('type','')} | Supplier: {info.get('supplier','')}")
    lines.append("")
    lines.append("Allocation Logs:")
    for log in data.get("logs", []):
        start = log.get("start_date", log.get("date", ""))
        end = log.get("end_date", start)
        lines.append(f"- {log.get('equip_id','')} -> {log.get('client','')} | {log.get('term','')} | {start} to {end}")
    return write_simple_pdf(f"survey_equipment_summary_{_timestamp()}.pdf", "Survey Equipment Summary Report", lines)
