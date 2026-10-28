"""Live password checklist (spec 018): rules mirrored from AUTH_PASSWORD_VALIDATORS.

The browser only evaluates what it can check exactly; the server still decides.
"""

from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.utils.translation import gettext

SIMILAR_MIN = 3  # shorter personal values match too much to be useful (D-078)
LATER = "se revisa al guardar"
MISMATCH = "Las contraseñas no coinciden."
ORDER = ("length", "numeric", "similar", "server")


def rules():
    """One entry per configured validator; `check` tells the browser how to evaluate it."""
    result = []
    for validator in password_validation.get_default_password_validators():
        name = type(validator).__name__
        if name == "MinimumLengthValidator":
            result.append({
                "code": "password_too_short",
                "text": f"Al menos {validator.min_length} caracteres",
                "check": "length",
                "min": validator.min_length,
            })
        elif name == "NumericPasswordValidator":
            result.append({"code": "password_entirely_numeric", "text": "No usar solo números", "check": "numeric"})
        elif name == "UserAttributeSimilarityValidator":
            result.append({
                "code": "password_too_similar",
                "text": "Que no se parezca a tu usuario ni a tu correo",
                "check": "similar",
                "note": LATER,
            })
        elif name == "CommonPasswordValidator":
            result.append({
                "code": "password_too_common",
                "text": "Que no sea una contraseña común",
                "check": "server",
                "note": LATER,
            })
        else:
            result.append({"code": "", "text": validator.get_help_text(), "check": "server", "note": LATER})
    # What the browser checks exactly first, what only the server decides last.
    return sorted(result, key=lambda rule: ORDER.index(rule["check"]))


def is_mismatch(error):
    allauth = gettext("You must type the same password each time.")
    return error.code == "password_mismatch" or allauth in error.messages


def personal_values(user):
    """Username and the e-mail local part, the values the browser compares against."""
    if user is None:
        return []
    values = [getattr(user, "username", "") or "", (getattr(user, "email", "") or "").split("@")[0]]
    return [value for value in values if len(value) >= SIMILAR_MIN]


class PasswordRulesMixin:
    """Replaces Django's static help list with `password_checklist` (RF-018-01..04)."""

    password_field = "password1"
    confirm_field = "password2"
    personal_fields = ("username", "email")  # form fields typed next to the password

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in (self.password_field, self.confirm_field):
            if name in self.fields:
                self.fields[name].help_text = ""

    def clean(self):
        cleaned_data = super().clean()
        errors = self.errors.as_data().get(self.confirm_field)
        if errors:
            # allauth's mismatch has no code; Django's says «Los dos campos…».
            kept = [e for e in errors if not is_mismatch(e)]
            if len(kept) < len(errors):
                mismatch = ValidationError(MISMATCH, code="password_mismatch")
                self.errors[self.confirm_field] = self.error_class(kept + [mismatch])
        return cleaned_data

    def password_user(self):
        return getattr(self, "user", None)

    def rejected_codes(self):
        """Validator codes rejected by the server; Django files them under the confirmation."""
        if not self.is_bound or not self.errors:
            return set()
        data = self.errors.as_data()
        errors = data.get(self.password_field, []) + data.get(self.confirm_field, [])
        return {error.code for error in errors if error.code}

    @property
    def password_checklist(self):
        rejected = self.rejected_codes()
        items = [dict(rule, state="fail" if rule["code"] in rejected else "pending") for rule in rules()]
        if self.confirm_field in self.fields:
            items.append({
                "code": "password_mismatch",
                "text": "Las contraseñas coinciden",
                "check": "match",
                "state": "fail" if "password_mismatch" in rejected else "pending",
            })
        password_id = self[self.password_field].id_for_label
        return {
            "items": items,
            "password_id": password_id,
            "json_id": f"{password_id}-personal",
            "confirm_id": self[self.confirm_field].id_for_label if self.confirm_field in self.fields else "",
            "personal_ids": [self[name].id_for_label for name in self.personal_fields if name in self.fields],
            "personal_values": personal_values(self.password_user()),
        }
