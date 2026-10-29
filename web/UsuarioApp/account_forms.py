"""allauth forms: live password checklist and Spanish (tú) help texts (spec 018)."""

from allauth.account import forms as allauth_forms

from .password_rules import PasswordRulesMixin


class LoginForm(allauth_forms.LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The page already links «¿Olvidaste tu contraseña?» under the button.
        self.fields["password"].help_text = ""


class ChangePasswordForm(PasswordRulesMixin, allauth_forms.ChangePasswordForm):
    personal_fields = ()


class SetPasswordForm(PasswordRulesMixin, allauth_forms.SetPasswordForm):
    personal_fields = ()


class ResetPasswordKeyForm(PasswordRulesMixin, allauth_forms.ResetPasswordKeyForm):
    personal_fields = ()
