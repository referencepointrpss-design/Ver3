import json
import os

DB_FILE = "survey_equipment_db.json"


def get_db_path():
    """Return a writable database path on desktop and Android/Kivy."""
    try:
        from kivy.app import App
        app = App.get_running_app()
        if app and getattr(app, "user_data_dir", None):
            os.makedirs(app.user_data_dir, exist_ok=True)
            return os.path.join(app.user_data_dir, DB_FILE)
    except Exception:
        pass

    return os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_FILE)


def _directory_to_dict(value, default=None):
    """Normalize old list-based directories into the newer dictionary structure."""
    result = {}

    if isinstance(value, dict):
        for name, details in value.items():
            clean_name = str(name).strip()
            if not clean_name:
                continue
            if isinstance(details, dict):
                result[clean_name] = {"phone": str(details.get("phone", "No Phone")).strip() or "No Phone"}
            else:
                result[clean_name] = {"phone": str(details).strip() or "No Phone"}
    elif isinstance(value, list):
        for item in value:
            clean_name = str(item).strip()
            if clean_name:
                result[clean_name] = {"phone": "No Phone"}

    if default:
        for name, details in default.items():
            result.setdefault(name, details)

    return result


def load_data():
    db_path = get_db_path()

    if os.path.exists(db_path):
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            # Keep the app running if the JSON file becomes damaged.
            data = {}
    else:
        data = {}

    if not isinstance(data, dict):
        data = {}

    if not isinstance(data.get("equipments"), dict):
        data["equipments"] = {}

    if not isinstance(data.get("logs"), list):
        data["logs"] = []

    data["device_owners"] = _directory_to_dict(
        data.get("device_owners"),
        default={"My Office": {"phone": "Internal"}}
    )
    data["rented_to_companies"] = _directory_to_dict(data.get("rented_to_companies"))

    return data


def save_data(data):
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    temp_path = db_path + ".tmp"

    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    os.replace(temp_path, db_path)
